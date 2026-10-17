"""Feature extraction shared by offline training and online inference (no train/serve skew).

Observation record (as posted by an AF to PReNEF, block D):
  {"obs_wall_s": 1791879389.66, "latency_ms": 41.2, "throughput_kbps": 2310,
   "loss_pct": 0.0, "services": {"sRSU": {"up": true, "latency_ms": 12.0}},
   "provenance": "af_measurement"}
Only provenances in ALLOWED_PROVENANCE are used; injected ground truth is
never a feature.
"""
from __future__ import annotations

import math
from typing import Sequence

ALLOWED_PROVENANCE = {"af_measurement", "af_service_probe", "nef_notification", "operator_analytics"}
WINDOW_S = 3.0

FEATURE_NAMES = [
    "lat_last", "lat_slope", "lat_max_w", "thr_last", "thr_slope", "loss_last", "obs_age_s",
    "dep_down_any", "dep_lat_last", "dep_lat_slope", "dep_lat_max_w", "n_shared", "n_obs_w",
]


def _slope(ts: Sequence[float], ys: Sequence[float]) -> float:
    n = len(ts)
    if n < 2:
        return 0.0
    mt, my = sum(ts) / n, sum(ys) / n
    den = sum((t - mt) ** 2 for t in ts)
    return 0.0 if den == 0 else sum((t - mt) * (y - my) for t, y in zip(ts, ys)) / den


def _num(v, default=math.nan) -> float:
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def extract(history: Sequence[dict], now_wall_s: float, dependencies: Sequence[str],
            n_shared: int) -> list[float]:
    """history: observations of ONE AF, any order; only those <= now are used."""
    hist = sorted((h for h in history
                   if _num(h.get("obs_wall_s"), math.inf) <= now_wall_s
                   and h.get("provenance", "af_measurement") in ALLOWED_PROVENANCE),
                  key=lambda h: h["obs_wall_s"])
    if not hist:
        return [math.nan] * (len(FEATURE_NAMES) - 2) + [float(n_shared), 0.0]
    w = [h for h in hist if h["obs_wall_s"] >= now_wall_s - WINDOW_S] or hist[-1:]
    ts = [h["obs_wall_s"] - now_wall_s for h in w]
    lat = [_num(h.get("latency_ms")) for h in w]
    thr = [_num(h.get("throughput_kbps")) for h in w]
    lat_ok = [(t, y) for t, y in zip(ts, lat) if not math.isnan(y)]
    thr_ok = [(t, y) for t, y in zip(ts, thr) if not math.isnan(y)]
    last = hist[-1]
    dep_lat, dep_ts, down = [], [], 0.0
    for h, t in zip(w, ts):
        svc = h.get("services") or {}
        vals = [svc[d] for d in dependencies if d in svc]
        if any(v.get("up") is False for v in vals):
            down = 1.0
        ls = [_num(v.get("latency_ms")) for v in vals if v.get("latency_ms") is not None]
        if ls:
            dep_lat.append(max(ls))
            dep_ts.append(t)
    return [
        lat_ok[-1][1] if lat_ok else math.nan,
        _slope(*zip(*lat_ok)) if len(lat_ok) > 1 else 0.0,
        max(y for _, y in lat_ok) if lat_ok else math.nan,
        thr_ok[-1][1] if thr_ok else math.nan,
        _slope(*zip(*thr_ok)) if len(thr_ok) > 1 else 0.0,
        _num(last.get("loss_pct")),
        now_wall_s - last["obs_wall_s"],
        down,
        dep_lat[-1] if dep_lat else math.nan,
        _slope(dep_ts, dep_lat) if len(dep_lat) > 1 else 0.0,
        max(dep_lat) if dep_lat else math.nan,
        float(n_shared),
        float(len(w)),
    ]
