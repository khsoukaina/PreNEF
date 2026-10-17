"""Block B (state registry) and block C (dependency graph G_t), eqs. (2)-(3), (5)-(7), (17)-(18).

Three distinct state families are kept separately and never inferred from
one another:
  z_im : mode CONFIRMED by AF i            (only via confirm_mode)
  r_im : mode RECOMMENDED by PReNEF        (only via recommend)
  x_ik : QoS profile SUBMITTED to the NEF  (only via mark_submitted)
and the network-side allocation state, which only advances on evidence.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

from .contracts import Contract

# Network-side lifecycle of one AsSessionWithQoS subscription.
# Only the evidence collector / notification handler may move it past ACCEPTED.
ALLOC_STATES = (
    "planned",          # chosen by planner, not yet sent
    "submitted",        # POST sent (x_ik = 1)                      eq. (5)
    "accepted",         # 201 + Location  — NOT an allocation        eq. (5)-(6)
    "rejected",         # 4xx/5xx ProblemDetails
    "allocated",        # evidence_alloc = 1                         eq. (17)
    "alloc_failed",     # FAILED_RESOURCES_ALLOCATION / QOS_NOT_GUARANTEED
    "revoke_requested", # DELETE sent
    "revoked",          # DELETE 204 — local, NOT a network release
    "released",         # release evidence observed
    "unverified",       # accepted but no evidence within window
)


@dataclass
class Subscription:
    correlation_id: str
    af_id: str
    intent_id: str
    mode: str
    profile: str
    contract_version: str
    state: str = "planned"
    location: str | None = None
    evidence: list[dict] = field(default_factory=list)


class Registry:
    def __init__(self, contracts: Iterable[Contract]):
        self.contracts: dict[str, Contract] = {c.af_id: c for c in contracts}
        self.confirmed_mode: dict[str, str | None] = {a: None for a in self.contracts}
        self.recommended_mode: dict[str, str | None] = {a: None for a in self.contracts}
        self.subs: dict[str, Subscription] = {}

    # z_im — eq. (18)
    def confirm_mode(self, af: str, mode: str, confirmation: dict) -> None:
        c = self.contracts[af]
        if not c.allows_mode(mode):
            raise ValueError(f"{af}: confirmation for undeclared mode {mode}")
        if not confirmation or confirmation.get("source") != "af":
            raise ValueError("mode can only be confirmed by the AF itself (eq. 18)")
        self.confirmed_mode[af] = mode

    # r_im — eq. (7), (13)
    def recommend(self, af: str, mode: str) -> None:
        c = self.contracts[af]
        if not c.allows_mode(mode):
            raise ValueError(f"{af}: cannot recommend undeclared mode {mode} (eq. 13)")
        if not c.allows_action("recommend_mode"):
            raise ValueError(f"{af}: recommend_mode not consented (eq. 14)")
        self.recommended_mode[af] = mode  # does NOT touch confirmed_mode

    # x_ik — eq. (15)-(16)
    def plan_submission(self, sub: Subscription) -> None:
        c = self.contracts[sub.af_id]
        if not c.allows_action("submit_qos"):
            raise ValueError(f"{sub.af_id}: submit_qos not consented (eq. 14)")
        if not c.allows_profile(sub.mode, sub.profile):
            raise ValueError(f"{sub.af_id}: profile {sub.profile} not in K_i({sub.mode}) (eq. 15)")
        for s in self.subs.values():
            if (s.af_id, s.intent_id) == (sub.af_id, sub.intent_id) and s.state in (
                "planned", "submitted", "accepted", "allocated", "unverified"
            ):
                raise ValueError(f"{sub.af_id}/{sub.intent_id}: already has an active submission (eq. 16)")
        self.subs[sub.correlation_id] = sub

    def set_state(self, cid: str, state: str, evidence: dict | None = None) -> None:
        if state not in ALLOC_STATES:
            raise ValueError(state)
        sub = self.subs[cid]
        if state in ("allocated", "released", "alloc_failed") and not evidence:
            raise ValueError(f"{state} requires evidence (eq. 17)")
        if evidence:
            sub.evidence.append(evidence)
        sub.state = state


class DependencyGraph:
    """G_t = (V_t, S_t, E_t): edge (i, s) iff the CONFIRMED mode of i depends on s."""

    def __init__(self, registry: Registry):
        self.reg = registry

    def edges(self) -> set[tuple[str, str]]:
        e = set()
        for af, mode in self.reg.confirmed_mode.items():
            if mode is None:
                continue
            for s in self.reg.contracts[af].modes[mode].dependencies:
                e.add((af, s))
        return e

    def afs_by_service(self) -> dict[str, set[str]]:
        out: dict[str, set[str]] = defaultdict(set)
        for af, s in self.edges():
            out[s].add(af)
        return dict(out)

    def shared_count(self, af: str) -> int:
        """Number of OTHER AFs whose confirmed-mode dependencies intersect af's (eq. 23)."""
        mode = self.reg.confirmed_mode.get(af)
        if mode is None:
            return 0
        mine = self.reg.contracts[af].modes[mode].dependencies
        n = 0
        for other, om in self.reg.confirmed_mode.items():
            if other == af or om is None:
                continue
            if mine & self.reg.contracts[other].modes[om].dependencies:
                n += 1
        return n

    def impacted_by(self, service: str) -> set[str]:
        return self.afs_by_service().get(service, set())
