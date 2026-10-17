"""Block F — protected planner for concurrent QoS requests.

Implements eq. (11)-(12) (adaptation feasibility), eq. (19) (uncertainty
gate), eq. (23) (semantic priority) and eq. (24) (hard submission deadline),
plus the baselines and ablations used in the benchmark.

The deadline guard is enforced *inside* the live ordering: a request is never
placed behind others if that would push its POST start past t_last, as long
as a feasible order exists. When no feasible order exists the planner says so.

Policies (submission behaviour / alert behaviour)
  direct_nef        all at once, unbounded concurrency      / no alerts
  fifo              arrival order, C slots                   / no alerts
  edf               earliest t_last first, C slots           / no alerts
  static_priority   contract weight w_i first, C slots       / no alerts
  independent_pred  all at once                              / per-AF predictor, each AF warned
                                                               only about itself (state of the art:
                                                               per-UE predictive QoS, no graph)
  oracle            all at once                              / alerts from ground truth (runtime)
  prenef_noai       eq.(23) w/o AI + guard, C slots          / observed-shared-failure fan-out (runtime)
  prenef_dtip       full eq.(23) + guard, C slots            / qualified DTIP + dependency fan-out
Ablation flags (PlannerConfig): eta (0 removes the shared-dependency term),
uncertainty_gate (False ignores u_max and qualification), guard (False drops eq. 24
enforcement), fanout (False warns only the predicted AF).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .contracts import Contract
from .graph_state import DependencyGraph, Registry

POLICIES = ("direct_nef", "fifo", "edf", "static_priority", "independent_pred", "oracle",
            "prenef_noai", "prenef_dtip")
UNBOUNDED = ("direct_nef", "independent_pred", "oracle")
AI_ALERT_POLICIES = ("prenef_dtip", "independent_pred")


@dataclass(frozen=True)
class Request:
    request_id: str
    af_id: str
    intent_id: str
    mode: str
    profile: str
    arrival_mono: float
    t_last_mono: float        # last useful POST start time (eq. 24)
    service_s: float          # conservative estimate of NEF service occupancy (e.g. p90)


@dataclass(frozen=True)
class Prediction:
    p_inad: float             # \hat p^{inad}_{ij}(t, H)
    t_safe_s: float           # \hat T^{safe}_i(t; alpha)
    u: float                  # uncertainty in [0, 1]
    qualified: bool           # model card says safe_time & uncertainty qualified
    horizon_s: float = 10.0


@dataclass
class PlannerConfig:
    policy: str = "prenef_dtip"
    concurrency: int = 1
    eta: float = 0.5
    epsilon_s: float = 0.25
    u_max: float = 0.35
    p_alert: float = 0.5
    guard_s: float = 0.5           # Delta^guard
    l_pred_s: float = 0.05         # L^pred
    l_notif_s: float = 0.10        # L^notif
    uncertainty_gate: bool = True  # ablation: False ignores eq. (19)
    guard: bool = True             # ablation: False ignores eq. (24)
    fanout: bool = True            # ablation: False warns only the predicted AF

    def effective(self) -> "PlannerConfig":
        """independent_pred = per-AF predictor without graph knowledge."""
        if self.policy == "independent_pred":
            return PlannerConfig(**{**self.__dict__, "eta": 0.0, "fanout": False})
        return self


@dataclass
class Decision:
    kind: str                       # submit | notify | notify_late | request_measurement | no_action
    af_id: str
    request_id: str | None = None
    order: int | None = None
    planned_start_mono: float | None = None
    recommended_mode: str | None = None
    justification: dict = field(default_factory=dict)


# ---------------------------------------------------------------- scheduling
def simulate(order: Sequence[Request], now: float, concurrency: int) -> list[tuple[Request, float, float]]:
    """List scheduling on `concurrency` slots. Returns (req, start, finish)."""
    slots = [now] * max(1, concurrency)
    out = []
    for r in order:
        i = min(range(len(slots)), key=lambda k: slots[k])
        start = max(slots[i], now, r.arrival_mono)
        finish = start + r.service_s
        slots[i] = finish
        out.append((r, start, finish))
    return out


def feasible(order: Sequence[Request], now: float, concurrency: int, tol: float = 1e-9) -> bool:
    return all(start <= r.t_last_mono + tol for r, start, _ in simulate(order, now, concurrency))


def edf_sort(reqs: Sequence[Request]) -> list[Request]:
    return sorted(reqs, key=lambda r: (r.t_last_mono, r.arrival_mono, r.request_id))


def guarded_order(preference: Sequence[Request], now: float, concurrency: int) -> tuple[list[Request], bool]:
    """Follow `preference` as closely as possible while keeping every t_last.

    Greedy: at each position choose the most-preferred remaining request r such
    that prefix + [r] + EDF(rest) is still feasible. EDF is optimal for
    feasibility on one slot with common release time, so with C=1 this never
    declares infeasible when a feasible order exists. With C>1 it is a sound
    heuristic (it only outputs orders it has simulated as feasible).
    """
    remaining = list(preference)
    overdue = edf_sort([r for r in remaining if now >= r.t_last_mono])    # eq. (24)
    order = list(overdue)
    remaining = [r for r in remaining if r not in overdue]
    if not feasible(order + edf_sort(remaining), now, concurrency):
        return order + edf_sort(remaining), False
    while remaining:
        for r in remaining:
            rest = [x for x in remaining if x is not r]
            if feasible(order + [r] + edf_sort(rest), now, concurrency):
                order.append(r)
                remaining = rest
                break
        else:  # pragma: no cover
            return order + edf_sort(remaining), False
    return order, True


# ---------------------------------------------------------------- priority
def l_adapt(cfg: PlannerConfig, contract: Contract, mode: str, target: str) -> float | None:
    tau = contract.tau(mode, target)
    if tau is None:
        return None
    return cfg.l_pred_s + cfg.l_notif_s + tau   # eq. (11)


def _gate_blocks(cfg: PlannerConfig, pred: Prediction | None) -> str | None:
    if pred is None:
        return "no_prediction"
    if not cfg.uncertainty_gate:
        return None
    if not pred.qualified:
        return "model_not_qualified"
    if pred.u > cfg.u_max:
        return "u>u_max"
    return None


def priority(cfg: PlannerConfig, contract: Contract, shared: int, pred: Prediction | None,
             mode: str, use_ai: bool) -> tuple[float, dict]:
    """Eq. (23). Without AI (or unqualified / too uncertain AI) the risk and time
    terms are neutral and the confidence term is 1: the planner abstains from
    AI-based ranking instead of using an unqualified score (eq. 19).
    Deviation from the paper, documented: the urgency term is clamped,
    1/(eps + max(0, T_safe - L_adapt)), so negative slack gives maximal urgency."""
    dep = 1.0 + cfg.eta * shared
    just = {"w": contract.weight, "shared": shared, "dep_factor": dep}
    blocked = _gate_blocks(cfg, pred) if use_ai else "ai_disabled"
    if blocked:
        just["ai_used"] = False
        if use_ai:
            just["abstain_reason"] = blocked
        return contract.weight * dep, just
    targets = contract.fallback_modes(mode)
    la = l_adapt(cfg, contract, mode, targets[0]) if targets else 0.0
    slack = pred.t_safe_s - (la or 0.0)
    urgency = 1.0 / (cfg.epsilon_s + max(0.0, slack))
    conf = 1.0 - min(max(pred.u, 0.0), 1.0)
    p = contract.weight * pred.p_inad * dep * urgency * conf
    just.update(ai_used=True, p_inad=pred.p_inad, t_safe_s=pred.t_safe_s, l_adapt_s=la,
                slack_s=slack, urgency=urgency, confidence=conf)
    return p, just


# ---------------------------------------------------------------- main entry
def plan(cfg: PlannerConfig, registry: Registry, requests: Sequence[Request],
         predictions: dict[str, Prediction], now: float,
         degraded_services: set | None = None) -> tuple[list[Decision], dict]:
    """degraded_services: shared services currently observed degraded (attribution). If given,
    a risk predicted for AF i is fanned out to the other users of service s ONLY if s is degraded:
    a degradation of i's own access path must not trigger alerts for AFs that merely share s."""
    if cfg.policy not in POLICIES:
        raise ValueError(f"unknown policy {cfg.policy}")
    cfg = cfg.effective()
    graph = DependencyGraph(registry)
    decisions: list[Decision] = []
    meta: dict = {"policy": cfg.policy, "feasible": True, "guard": cfg.guard,
                  "uncertainty_gate": cfg.uncertainty_gate, "eta": cfg.eta, "fanout": cfg.fanout}

    admitted: list[Request] = []
    for r in requests:                       # admission, eq. (13)-(16): local reject with cause
        c = registry.contracts.get(r.af_id)
        cause = None
        if c is None:
            cause = "unknown_af"
        elif not c.allows_action("submit_qos"):
            cause = "submit_qos_not_consented"
        elif not c.allows_profile(r.mode, r.profile):
            cause = "profile_not_in_K_i(m)"
        if cause:
            decisions.append(Decision("no_action", r.af_id, r.request_id, justification={"local_reject": cause}))
        else:
            admitted.append(r)

    scores: dict[str, tuple[float, dict]] = {}
    conc = cfg.concurrency
    by_arrival = sorted(admitted, key=lambda r: (r.arrival_mono, r.request_id))
    if cfg.policy in UNBOUNDED:
        order, conc = by_arrival, max(1, len(admitted))
    elif cfg.policy == "fifo":
        order = by_arrival
    elif cfg.policy == "edf":
        order = edf_sort(admitted)
    elif cfg.policy == "static_priority":
        order = sorted(admitted, key=lambda r: (-registry.contracts[r.af_id].weight, r.arrival_mono, r.request_id))
    else:  # prenef_noai / prenef_dtip
        use_ai = cfg.policy == "prenef_dtip"
        for r in admitted:
            c = registry.contracts[r.af_id]
            scores[r.request_id] = priority(cfg, c, graph.shared_count(r.af_id),
                                            predictions.get(r.af_id), r.mode, use_ai)
        pref = sorted(admitted, key=lambda r: (-scores[r.request_id][0], r.t_last_mono, r.request_id))
        if cfg.guard:
            order, ok = guarded_order(pref, now, conc)
            meta["feasible"] = ok
        else:
            order = pref
    if cfg.policy not in ("prenef_noai", "prenef_dtip") or not cfg.guard:
        meta["feasible"] = feasible(edf_sort(admitted), now, conc)   # did ANY feasible order exist?
    meta["concurrency"] = conc

    for idx, (r, start, finish) in enumerate(simulate(order, now, conc)):
        just = {"t_last_mono": r.t_last_mono, "planned_finish_mono": finish,
                "meets_t_last": start <= r.t_last_mono + 1e-9, "feasible_order_existed": meta["feasible"]}
        if r.request_id in scores:
            just["score"], just["score_terms"] = scores[r.request_id]
        decisions.append(Decision("submit", r.af_id, r.request_id, order=idx,
                                  planned_start_mono=start, justification=just))

    if cfg.policy in AI_ALERT_POLICIES:
        decisions += _alerts(cfg, registry, graph, predictions, degraded_services)
    return decisions, meta


def _alerts(cfg: PlannerConfig, registry: Registry, graph: DependencyGraph,
            predictions: dict[str, Prediction], degraded_services: set | None = None) -> list[Decision]:
    out: list[Decision] = []
    alerted: set[str] = set()
    for af, pred in sorted(predictions.items()):
        c = registry.contracts.get(af)
        mode = registry.confirmed_mode.get(af)
        if c is None or mode is None:
            continue
        blocked = _gate_blocks(cfg, pred)
        if blocked:
            if c.allows_action("request_measurement"):
                out.append(Decision("request_measurement", af, justification={
                    "reason": f"eq.19: {blocked}", "u": pred.u, "qualified": pred.qualified}))
            continue
        if pred.p_inad < cfg.p_alert:
            continue
        targets = c.fallback_modes(mode)
        if not targets or not c.allows_action("alert"):
            continue
        la = l_adapt(cfg, c, mode, targets[0])
        timely = la is not None and pred.t_safe_s >= la + cfg.guard_s   # eq. (12)
        kind = "notify" if timely else "notify_late"
        group = {af}
        fanned = []
        if cfg.fanout:
            for s in c.modes[mode].dependencies:
                if degraded_services is None or s in degraded_services:
                    group |= graph.impacted_by(s)
                    fanned.append(s)
        for g in sorted(group):
            if g in alerted:
                continue
            gc = registry.contracts[g]
            gm = registry.confirmed_mode.get(g)
            if gm is None or not gc.allows_action("alert"):
                continue
            gt = gc.fallback_modes(gm)
            alerted.add(g)
            out.append(Decision(kind, g, recommended_mode=(gt[0] if gt and gc.allows_action("recommend_mode") else None),
                                justification={"trigger_af": af, "p_inad": pred.p_inad, "t_safe_s": pred.t_safe_s,
                                               "l_adapt_s": la, "guard_s": cfg.guard_s, "timely": timely,
                                               "shared_dependency_fanout": g != af,
                                               "fanout_services": fanned}))
    return out


def describe(decisions: list[Decision]) -> list[dict]:
    return [d.__dict__ for d in decisions]


__all__ = ["Request", "Prediction", "PlannerConfig", "Decision", "plan", "guarded_order",
           "simulate", "feasible", "edf_sort", "priority", "l_adapt", "POLICIES", "UNBOUNDED"]
