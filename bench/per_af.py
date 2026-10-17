#!/usr/bin/env python3
"""Per-AF (per-UE) breakdown + data-quality check of a campaign.

For every run (block x arm) and every AF it computes, from the AF agent logs:
  lat_cov            share of observations that carried an RTT measurement (data quality)
  pct_primary        % of the run spent in the primary (remote) mode
  fallbacks          remote->local transitions, split by trigger (reactive / prenef_alert / oracle)
  exposure_s         inadequate-mode exposure per eligible episode of THIS AF (contract onset)
  eligible / timely  episodes that hit the AF while in remote / adapted before onset
  alerts             alerts received by the AF
and a run validity flag:
  valid = every AF has lat_cov >= --min-coverage   (a run where an AF could not measure
          its own network path says nothing about PReNEF)

  python3 bench/per_af.py --campaign campaigns/final --out campaigns/final/analysis
Outputs: per_af.csv, per_af.md (arm x AF tables), data_quality.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bench.metrics import episodes, load_agent_logs, mode_at, mode_timeline, obs_series  # noqa: E402
from prenef.common import read_json, read_jsonl  # noqa: E402
from prenef.contracts import parse_contract  # noqa: E402

ARM_ORDER = ["direct_nef", "independent_pred", "prenef_noai", "prenef_dtip", "oracle",
             "prenef_dtip_eta0", "prenef_dtip_nogate", "prenef_dtip_noguard", "prenef_dtip_nofanout",
             "fifo", "edf", "static_priority"]


def load_contracts(run_dir):
    out = {}
    rt = os.path.join(run_dir, "runtime.json")
    if os.path.exists(rt):
        for cp in read_json(rt).get("contracts", []):
            cp = cp if os.path.isabs(cp) else os.path.join(ROOT, cp)
            c = parse_contract(read_json(cp))
            out[c.af_id] = c
    return out


def run_per_af(run_dir: str) -> list[dict]:
    j = list(read_jsonl(os.path.join(run_dir, "journal.jsonl")))
    start = next(r for r in j if r["kind"] == "run_start")
    end = next((r for r in reversed(j) if r["kind"] == "run_end"), j[-1])
    scen_p = os.path.join(run_dir, "scenario.json")
    scen = read_json(scen_p) if os.path.exists(scen_p) else {}
    contracts = load_contracts(run_dir)
    agents = load_agent_logs(run_dir)
    eps = episodes(run_dir, scen.get("service_afs", {}), contracts, scen)
    arm = os.path.basename(run_dir).split("-", 1)[1]
    rows = []
    for af, recs in sorted(agents.items()):
        obs = [r for r in recs if r["kind"] == "observation"]
        tl = mode_timeline(recs)
        primary = tl[0][1] if tl else None
        t0 = tl[0][0] if tl else start["wall_s"]
        t_end = max([r["wall_s"] for r in recs] + [t0])
        # time in primary
        pts = tl + [(t_end, None, None, None)]
        in_primary = sum(max(0.0, w2 - w) for (w, m, _, _), (w2, *_r) in zip(pts, pts[1:]) if m == primary)
        dur = max(1e-9, t_end - t0)
        starts = [r for r in recs if r["kind"] == "transition_start" and r.get("frm") == primary]
        by_reason = defaultdict(int)
        for r in starts:
            by_reason[r.get("reason", "?")] += 1
        lat = [(r.get("obs") or {}).get("latency_ms") for r in obs]
        loss = [(r.get("obs") or {}).get("loss_pct") for r in obs]
        svc_up = [v.get("up") for r in obs for v in ((r.get("obs") or {}).get("services") or {}).values()]
        # per-AF episode exposure / timeliness
        series = obs_series(recs)
        exp, eligible, timely, leads = [], 0, 0, []
        for e in eps:
            onset = e["onsets"].get(af)
            if af not in e["afs"] or onset is None:
                continue
            exp.append(sum(dt for w, a, dt, _ in series if a == 0 and e["start"] <= w <= e["end"] + 3.0))
            if mode_at(tl, e["start"]) == primary:
                eligible += 1
                fb = [w for w, m, prev, _ in tl if prev == primary and m != primary and e["start"] - 1.0 <= w <= e["end"]]
                if fb:
                    leads.append(onset - fb[0])
                    timely += int(fb[0] <= onset)
        rows.append({
            "run": os.path.basename(run_dir), "block": start.get("block"), "arm": arm, "af": af,
            "obs_n": len(obs),
            "lat_cov": (sum(x is not None for x in lat) / len(lat)) if lat else 0.0,
            "rtt_med_ms": float(np.median([x for x in lat if x is not None])) if any(x is not None for x in lat) else None,
            "loss_med_pct": float(np.median([x for x in loss if x is not None])) if loss else None,
            "svc_up_frac": (sum(bool(x) for x in svc_up) / len(svc_up)) if svc_up else None,
            "pct_primary": 100.0 * in_primary / dur,
            "fallbacks": len(starts),
            "fallbacks_reactive": by_reason.get("reactive", 0),
            "fallbacks_alert": by_reason.get("prenef_alert", 0),
            "returns": sum(1 for r in recs if r["kind"] == "transition_start" and r.get("to") == primary),
            "alerts": sum(1 for r in recs if r["kind"] == "alert_received"),
            "episodes": len(exp), "eligible": eligible, "timely": timely,
            "exposure_s": float(np.mean(exp)) if exp else None,
            "lead_s_med": float(np.median(leads)) if leads else None,
            "first_gap_s": next((r["wall_s"] - t0 for r in obs if (r.get("obs") or {}).get("latency_ms") is None), None),
        })
    return rows


def fmt(v, nd=2):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v:.{nd}f}" if isinstance(v, float) else str(v)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-coverage", type=float, default=0.9)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows = []
    for d in sorted(glob.glob(os.path.join(a.campaign, "b*-*"))):
        if os.path.exists(os.path.join(d, "journal.jsonl")):
            try:
                rows += run_per_af(d)
            except StopIteration:
                pass
    if not rows:
        print("no runs found")
        return 1
    # run validity
    valid = {}
    for run in sorted({r["run"] for r in rows}):
        rr = [r for r in rows if r["run"] == run]
        valid[run] = all(r["lat_cov"] >= a.min_coverage for r in rr)
    for r in rows:
        r["run_valid"] = valid[r["run"]]
    keys = list(rows[0].keys())
    with open(os.path.join(a.out, "per_af.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    arms = [x for x in ARM_ORDER if x in {r["arm"] for r in rows}] + \
        sorted({r["arm"] for r in rows} - set(ARM_ORDER))
    afs = sorted({r["af"] for r in rows})

    def table(metric, title, nd=2, only_valid=False, agg=np.mean):
        L = [f"### {title}", "", "| arm | " + " | ".join(afs) + " | all |", "|---|" + "---|" * (len(afs) + 1)]
        for arm in arms:
            cells = []
            for af in afs + [None]:
                v = [r[metric] for r in rows if r["arm"] == arm and (af is None or r["af"] == af)
                     and r[metric] is not None and (r["run_valid"] or not only_valid)]
                cells.append(fmt(float(agg(v)), nd) + f" (n={len(v)})" if v else "—")
            L.append(f"| {arm} | " + " | ".join(cells) + " |")
        return L + [""]

    n_runs = len(valid)
    n_ok = sum(valid.values())
    L = ["# Per-AF (per-UE) breakdown", "",
         f"Runs: {n_runs} — valid (every AF measured its path in >= {a.min_coverage:.0%} of observations): "
         f"**{n_ok}** — invalid: **{n_runs - n_ok}**", ""]
    L += table("lat_cov", "Data quality — share of observations with an RTT measurement", 2)
    L += table("pct_primary", "Time in primary mode `remote` (%)", 1)
    L += table("fallbacks", "Fallbacks remote→local per run", 2)
    L += table("fallbacks_alert", "…of which triggered by an alert (anticipation)", 2)
    L += table("fallbacks_reactive", "…of which reactive (after observed inadequacy)", 2)
    L += table("returns", "Returns local→remote per run", 2)
    L += table("exposure_s", "Inadequate-mode exposure per episode (s) — valid runs only", 3, only_valid=True)
    L += table("eligible", "Eligible episodes (AF in remote at episode start) per run", 2)
    L += table("timely", "Timely adaptations per run", 2)
    L += table("alerts", "Alerts received per run", 2)
    inval = sorted(r for r, ok in valid.items() if not ok)
    if inval:
        L += ["### Invalid runs (an AF lost its measurements)", ""]
        for run in inval:
            bad = [f"{r['af']} cov={r['lat_cov']:.2f} first_gap={fmt(r['first_gap_s'], 0)}s"
                   for r in rows if r["run"] == run and r["lat_cov"] < a.min_coverage]
            L.append(f"- {run}: " + ", ".join(bad))
    with open(os.path.join(a.out, "per_af.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    with open(os.path.join(a.out, "data_quality.csv"), "w") as f:
        f.write("run,valid,min_lat_cov\n")
        for run, ok in sorted(valid.items()):
            f.write(f"{run},{ok},{min(r['lat_cov'] for r in rows if r['run'] == run):.3f}\n")
    print("\n".join(L[:4]))
    print(f"-> {os.path.join(a.out, 'per_af.md')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
