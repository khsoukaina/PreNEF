"""Intent contracts C_i = (M_i, K_i, Q_i, D_i, tau_i, A_i, w_i)  — eq. (1).

Blocks A/B of the study: validation, versioning, expiry, and the
adequacy test A_i(m, t) of eq. (4). Stdlib only.

Contract JSON (one file per AF, see config/contracts.example.json):
{
  "af_id": "af1", "scs_as_id": "af1", "version": "3", "weight": 1.0,
  "valid_until_epoch_s": 1893456000,
  "consent": {"attested": true, "attested_by": "lab-operator", "scope": "emulated-AF"},
  "ue":   {"container": "ueransim-ue-qod423", "dnn": "internet",
           "snssai": {"sst": 1, "sd": "010203"}},
  "flows": [{"flow_id": 1, "proto": "udp", "remote_ipv4": "10.101.200.30",
             "remote_port": 5201, "direction": "downlink"}],
  "qos_profiles": {"qos-remote": {"qosReference": "qos-remote",
                                  "altQoSReferences": ["qos-remote-alt"]}},
  "modes": {
    "remote": {"utility": 1.0, "qos_profiles": ["qos-remote"],
               "requirements": {"max_latency_ms": 60, "min_throughput_kbps": 2000,
                                "max_loss_pct": 1.0, "max_obs_age_s": 2.0},
               "dependencies": ["sRSU"]},
    "local":  {"utility": 0.6, "qos_profiles": [],
               "requirements": {"max_obs_age_s": 5.0}, "dependencies": []}
  },
  "transitions_s": {"remote->local": 1.5, "local->remote": 2.0},
  "actions": ["alert", "submit_qos", "recommend_mode", "request_measurement"]
}
"""
from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from typing import Any

ALLOWED_ACTIONS = {"alert", "submit_qos", "recommend_mode", "request_measurement"}
REQUIREMENT_KEYS = {
    "max_latency_ms": ("latency_ms", "le"),
    "min_throughput_kbps": ("throughput_kbps", "ge"),
    "max_loss_pct": ("loss_pct", "le"),
    "max_jitter_ms": ("jitter_ms", "le"),
}


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class Mode:
    name: str
    utility: float
    qos_profiles: tuple[str, ...]
    requirements: dict[str, float]
    dependencies: frozenset[str]


@dataclass(frozen=True)
class Contract:
    af_id: str
    scs_as_id: str
    version: str
    weight: float
    valid_until_epoch_s: float
    consent: dict[str, Any]
    ue: dict[str, Any]
    flows: tuple[dict[str, Any], ...]
    qos_profiles: dict[str, dict[str, Any]]
    modes: dict[str, Mode]
    transitions_s: dict[tuple[str, str], float]
    actions: frozenset[str]
    raw: dict[str, Any] = field(repr=False, compare=False, default_factory=dict)

    # ---- eq. (13)-(15) helpers -------------------------------------------
    def allows_mode(self, m: str) -> bool:
        return m in self.modes

    def allows_action(self, a: str) -> bool:
        return a in self.actions

    def allows_profile(self, m: str, k: str) -> bool:
        return m in self.modes and k in self.modes[m].qos_profiles

    def tau(self, m: str, m2: str) -> float | None:
        return self.transitions_s.get((m, m2))

    def is_expired(self, now_epoch_s: float) -> bool:
        return now_epoch_s > self.valid_until_epoch_s

    def fallback_modes(self, m: str) -> list[str]:
        """Declared transitions out of m, ordered by transition time.
        Never inferred from names such as 'fallback' (Table 1, block B)."""
        outs = [(t, b) for (a, b), t in self.transitions_s.items() if a == m]
        return [b for _, b in sorted(outs)]


def _req(d: dict, key: str, typ, ctx: str):
    if key not in d:
        raise ContractError(f"{ctx}: missing '{key}'")
    if not isinstance(d[key], typ):
        raise ContractError(f"{ctx}: '{key}' must be {typ}")
    return d[key]


def parse_contract(raw: dict[str, Any]) -> Contract:
    ctx = f"contract[{raw.get('af_id', '?')}]"
    af_id = _req(raw, "af_id", str, ctx)
    version = str(_req(raw, "version", (str, int), ctx))
    weight = float(_req(raw, "weight", (int, float), ctx))
    if weight <= 0:
        raise ContractError(f"{ctx}: weight must be > 0 (it is NOT an ARP/5QI priority)")
    consent = _req(raw, "consent", dict, ctx)
    if consent.get("attested") is not True:
        raise ContractError(f"{ctx}: consent not attested; PReNEF may not act for this AF")
    ue = _req(raw, "ue", dict, ctx)
    flows = _req(raw, "flows", list, ctx)
    if not flows:
        raise ContractError(f"{ctx}: at least one flow is required to build flowInfo")
    for fl in flows:
        _req(fl, "flow_id", int, f"{ctx}.flow")
        ipaddress.ip_address(_req(fl, "remote_ipv4", str, f"{ctx}.flow"))
        if fl.get("direction", "bidirectional") not in ("downlink", "uplink", "bidirectional"):
            raise ContractError(f"{ctx}.flow: bad direction")
    profiles = _req(raw, "qos_profiles", dict, ctx)
    for name, prof in profiles.items():
        if not ("qosReference" in prof or "qosParams" in prof):
            raise ContractError(f"{ctx}.qos_profiles.{name}: needs qosReference or qosParams")
    modes_raw = _req(raw, "modes", dict, ctx)
    if not modes_raw:
        raise ContractError(f"{ctx}: no modes declared")
    modes: dict[str, Mode] = {}
    for mname, m in modes_raw.items():
        mctx = f"{ctx}.modes.{mname}"
        profs = tuple(m.get("qos_profiles", []))
        for k in profs:
            if k not in profiles:
                raise ContractError(f"{mctx}: references undeclared QoS profile '{k}'")
        reqs = dict(m.get("requirements", {}))
        for rk in reqs:
            if rk not in REQUIREMENT_KEYS and rk != "max_obs_age_s":
                raise ContractError(f"{mctx}: unknown requirement '{rk}'")
        modes[mname] = Mode(
            name=mname,
            utility=float(m.get("utility", 0.0)),
            qos_profiles=profs,
            requirements={k: float(v) for k, v in reqs.items()},
            dependencies=frozenset(m.get("dependencies", [])),
        )
    trans: dict[tuple[str, str], float] = {}
    for key, val in raw.get("transitions_s", {}).items():
        try:
            a, b = key.split("->")
        except ValueError:
            raise ContractError(f"{ctx}: transition key '{key}' must be 'from->to'")
        if a not in modes or b not in modes:
            raise ContractError(f"{ctx}: transition {key} references undeclared mode")
        if float(val) < 0:
            raise ContractError(f"{ctx}: negative transition time {key}")
        trans[(a, b)] = float(val)
    actions = frozenset(_req(raw, "actions", list, ctx))
    bad = actions - ALLOWED_ACTIONS
    if bad:
        raise ContractError(f"{ctx}: unknown actions {sorted(bad)}")
    return Contract(
        af_id=af_id,
        scs_as_id=str(raw.get("scs_as_id", af_id)),
        version=version,
        weight=weight,
        valid_until_epoch_s=float(raw.get("valid_until_epoch_s", float("inf"))),
        consent=consent,
        ue=ue,
        flows=tuple(flows),
        qos_profiles=profiles,
        modes=modes,
        transitions_s=trans,
        actions=actions,
        raw=raw,
    )


# ---- eq. (4): adequacy -----------------------------------------------------
def adequacy(contract: Contract, mode: str, q_hat: dict[str, Any],
             d_hat: dict[str, bool], now_wall_s: float) -> tuple[int | None, list[str]]:
    """Return (A_i(m,t), reasons).

    A = 1 only if every declared requirement is satisfied by a *fresh*
    observation and every declared dependency is observed available.
    A = None ("unknown") when a requirement has no fresh observation:
    unknown is never silently mapped to adequate (Table 1, block D).
    q_hat: {"latency_ms": .., "throughput_kbps": .., "loss_pct": .., "obs_wall_s": ..}
    d_hat: {"sRSU": True/False}
    """
    m = contract.modes[mode]
    reasons: list[str] = []
    unknown = False
    max_age = m.requirements.get("max_obs_age_s")
    obs_t = q_hat.get("obs_wall_s")
    if max_age is not None and (obs_t is None or now_wall_s - float(obs_t) > max_age):
        unknown = True
        reasons.append("stale_or_missing_observation")
    for rk, thr in m.requirements.items():
        if rk == "max_obs_age_s":
            continue
        okey, op = REQUIREMENT_KEYS[rk]
        val = q_hat.get(okey)
        if val is None:
            unknown = True
            reasons.append(f"missing:{okey}")
            continue
        ok = float(val) <= thr if op == "le" else float(val) >= thr
        if not ok:
            reasons.append(f"violated:{rk}")
    for s in m.dependencies:
        st = d_hat.get(s)
        if st is None:
            unknown = True
            reasons.append(f"dependency_unknown:{s}")
        elif not st:
            reasons.append(f"dependency_down:{s}")
    if any(r.startswith(("violated", "dependency_down")) for r in reasons):
        return 0, reasons
    if unknown:
        return None, reasons
    return 1, reasons
