#!/usr/bin/env python3
"""Per-run KPIs. The headline is application-mode exposure, not latency/throughput.

PRIMARY (fix before the final campaign)
  exposure_s_per_episode      seconds an AF spends in a mode whose declared conditions are
                              violated (A_i(m_i(t),t)=0), per (episode, affected AF). Eq. (25)
                              measured as a duration — the study's stated objective.
MECHANISM
  timely_adaptation_rate      eq. (26): fallback CONFIRMED before ground-truth onset
  correlated_coverage_rate    shared-service episodes where ALL affected AFs adapted in time
                              (signature of the dependency graph)
  lead_s_median, leads[]      onset - confirmation, with tau, for the lead-vs-tau figure
  *_shared / *_ue             the same KPIs stratified by episode type
COST / SAFETY
  unnecessary_transitions     fallbacks outside any real-onset episode window (false alarms)
  utility_loss_per_min        integral of (U_primary - U_current) — the J2 term, eq. (21)
  calibration_error           eq. (27) on logged predictions vs realised inadequacy
  abstention_rate             predictions blocked by eq. (19)
  coordination_overhead_ms    median PReNEF queueing delay before the POST (its own cost)
  nef_submission_rate_per_s   eq. (28)
  burst_deadline_miss_fraction, burst_completion_s, max_lateness_s
  allocated_fraction          evidence-based, eq. (17)
SANITY (not headline): mode_inadequacy_rate (tick-based eq. 25), mode_unknown_rate,
                       net_latency_ms_median
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from prenef.common import durable_json, percentile, read_json, read_jsonl  # noqa: E402
from prenef.contracts import parse_contract  # noqa: E402

LATE_TOL_S = 0.05


def load_agent_logs(run_dir):
    out = defaultdict(list)
    for p in glob.glob(os.path.join(run_dir, "agent-*.jsonl")):
        for r in read_jsonl(p):
            out[r["af_id"]].append(r)
    for v in out.values():
        v.sort(key=lambda r: r["wall_s"])
    return out


def episodes(run_dir, service_afs, contracts=None, scen=None, base_rtt_ms=3.0):
    """Episodes from the ground truth. With contracts+scenario, each affected AF gets its
    own onset = first injected state violating ITS declared requirements (eq. 4);
    otherwise the injector's 'inadequacy_onset' label is used for all affected AFs."""
    gt = os.path.join(run_dir, "ground_truth.jsonl")
    if not os.path.exists(gt):
        return []
    eps: dict[int, dict] = {}
    t2wall: dict = {}
    for r in read_jsonl(gt):
        e = eps.setdefault(r["episode"], {"episode": r["episode"], "start": r["applied_wall_s"],
                                          "end": r["applied_wall_s"], "onset": None, "false_alarm": False})
        e["start"] = min(e["start"], r["applied_wall_s"])
        e["end"] = max(e["end"], r["applied_wall_s"])
        e["kind"], e["target"] = r["kind"], r["target"]
        if "t" in r:
            t2wall[(r["episode"], round(float(r["t"]), 3))] = r["applied_wall_s"]
        if r.get("ground_truth") == "inadequacy_onset":
            e["onset"] = r["applied_wall_s"]
        if r.get("ground_truth") == "false_alarm":
            e["false_alarm"] = True
    co = {}
    if contracts and scen and scen.get("events"):
        sys.path.insert(0, ROOT)
        from lab.scenario import contract_onsets
        co = contract_onsets(scen, contracts, base_rtt_ms)
    for e in eps.values():
        e["afs"] = service_afs.get(e["target"], []) if e["kind"] == "shared" else [e["target"]]
        e["onsets"] = {}
        for af in e["afs"]:
            if co:
                t = co.get((e["episode"], af))
                e["onsets"][af] = t2wall.get((e["episode"], round(t, 3))) if t is not None else None
            else:
                e["onsets"][af] = e["onset"]
        e["onset_basis"] = "contract" if co else "injector_label"
    return sorted(eps.values(), key=lambda e: e["start"])


def mode_timeline(recs):
    return [(r["wall_s"], r["mode"], r.get("previous"), r.get("reason")) for r in recs if r["kind"] == "mode_confirmed"]


def mode_at(timeline, t):
    m = None
    for w, mode, _, _ in timeline:
        if w <= t:
            m = mode
    return m


def obs_series(recs):
    obs = [(r["wall_s"], r["adequacy"], r.get("obs", {}).get("latency_ms")) for r in recs if r["kind"] == "observation"]
    if len(obs) < 2:
        return [(w, a, 0.0, lat) for w, a, lat in obs]
    gaps = [b[0] - a[0] for a, b in zip(obs, obs[1:])]
    cap = 2 * float(np.median(gaps))
    return [(w, a, min(cap, (obs[i + 1][0] - w) if i + 1 < len(obs) else cap / 2), lat)
            for i, (w, a, lat) in enumerate(obs)]


def run_metrics(run_dir: str, cal_horizon_s: float = 5.0) -> dict:
    j = list(read_jsonl(os.path.join(run_dir, "journal.jsonl")))
    start = next(r for r in j if r["kind"] == "run_start")
    end = next((r for r in reversed(j) if r["kind"] == "run_end"), j[-1])
    planner = start.get("planner") or {}
    duration = max(1e-9, end["wall_s"] - start["wall_s"])
    scen_p = os.path.join(run_dir, "scenario.json")
    scen = read_json(scen_p) if os.path.exists(scen_p) else {}
    contracts = {}
    rt_p = os.path.join(run_dir, "runtime.json")
    if os.path.exists(rt_p):
        for cp in read_json(rt_p).get("contracts", []):
            cp = cp if os.path.isabs(cp) else os.path.join(ROOT, cp)
            c = parse_contract(read_json(cp))
            contracts[c.af_id] = c
    agents = load_agent_logs(run_dir)
    m: dict = {"run_dir": run_dir, "policy": start.get("policy"), "block": start.get("block"),
               "duration_s": duration, "ablation": {k: planner.get(k) for k in ("eta", "uncertainty_gate", "guard", "fanout")}}

    # ---------------- sanity: tick-based eq. (25), unknown share, network latency
    known = bad = unknown = 0
    lats = []
    for recs in agents.values():
        for r in recs:
            if r["kind"] != "observation":
                continue
            if r["adequacy"] is None:
                unknown += 1
            else:
                known += 1
                bad += int(r["adequacy"] == 0)
            lat = (r.get("obs") or {}).get("latency_ms")
            if lat is not None:
                lats.append(lat)
    m["mode_inadequacy_rate"] = bad / known if known else None
    m["mode_unknown_rate"] = unknown / max(1, known + unknown)
    m["net_latency_ms_median"] = percentile(lats, 0.5)
    cov = {}
    for af, recs in agents.items():
        ob = [r for r in recs if r["kind"] == "observation"]
        if ob:
            cov[af] = sum((r.get("obs") or {}).get("latency_ms") is not None for r in ob) / len(ob)
    m["meas_coverage"] = cov
    m["meas_coverage_min"] = min(cov.values()) if cov else None

    # ---------------- episodes: exposure, timeliness, correlated coverage, leads
    eps = episodes(run_dir, scen.get("service_afs", {}), contracts, scen)
    m["onset_basis"] = eps[0]["onset_basis"] if eps else None
    series = {af: obs_series(recs) for af, recs in agents.items()}
    tl = {af: mode_timeline(recs) for af, recs in agents.items()}
    primary = {af: (t[0][1] if t else None) for af, t in tl.items()}
    strata = {"all": defaultdict(list), "shared": defaultdict(list), "ue": defaultdict(list)}
    leads, corr = [], []
    fallback_windows = defaultdict(list)
    for e in eps:
        if all(v is None for v in e["onsets"].values()):
            continue
        timely_all, eligible = True, 0
        for af in e["afs"]:
            onset = e["onsets"].get(af)
            if af not in series or onset is None:
                continue
            fallback_windows[af].append((e["start"] - 1.0, e["end"] + 1.0))
            exp_s = sum(dt for w, a, dt, _ in series[af] if a == 0 and e["start"] <= w <= e["end"] + 3.0)
            in_primary = mode_at(tl[af], e["start"]) == primary[af]
            fb = [(w, mode, prev) for w, mode, prev, reason in tl[af]
                  if prev == primary[af] and mode != primary[af] and e["start"] - 1.0 <= w <= e["end"]]
            timely = bool(fb) and fb[0][0] <= onset
            for key in ("all", e["kind"]):
                strata[key]["exposure"].append(exp_s)
                if in_primary:
                    strata[key]["timely"].append(int(timely))
            if in_primary:
                eligible += 1
                timely_all &= timely
                if fb:
                    tau = contracts[af].tau(primary[af], fb[0][1]) if af in contracts else None
                    leads.append({"af": af, "kind": e["kind"], "lead_s": onset - fb[0][0], "tau_s": tau})
        if e["kind"] == "shared" and eligible >= 2:
            corr.append(int(timely_all))
    for key, d in strata.items():
        sfx = "" if key == "all" else f"_{key}"
        m[f"exposure_s_per_episode{sfx}"] = float(np.mean(d["exposure"])) if d["exposure"] else None
        m[f"timely_adaptation_rate{sfx}"] = float(np.mean(d["timely"])) if d["timely"] else None
        m[f"necessary_transitions{sfx}"] = len(d["timely"])
    m["correlated_coverage_rate"] = float(np.mean(corr)) if corr else None
    m["correlated_episodes"] = len(corr)
    m["lead_s_median"] = float(np.median([x["lead_s"] for x in leads])) if leads else None
    m["leads"] = leads

    # ---------------- cost: unnecessary transitions and utility loss (J2, eq. 21)
    unnecessary = 0
    util_loss = 0.0
    for af, t in tl.items():
        pm = primary[af]
        for w, mode, prev, reason in t:
            if prev == pm and mode != pm and not any(lo <= w <= hi for lo, hi in fallback_windows[af]):
                unnecessary += 1
        if af in contracts and pm:
            up = contracts[af].modes[pm].utility
            pts = t + [(end["wall_s"], None, None, None)]
            for (w, mode, _, _), (w2, *_rest) in zip(pts, pts[1:]):
                if mode in contracts[af].modes:
                    util_loss += max(0.0, up - contracts[af].modes[mode].utility) * max(0.0, w2 - w)
    m["unnecessary_transitions"] = unnecessary
    m["utility_loss_per_min"] = util_loss / (duration / 60.0)
    alerts = [r for r in j if r["kind"] == "alert"]
    m["alerts"] = len(alerts)

    # ---------------- AI: calibration (eq. 27) and abstention (eq. 19)
    preds = [r for r in j if r["kind"] == "prediction"]
    if preds:
        u_max = planner.get("u_max", 1.0)
        m["abstention_rate"] = float(np.mean([(not p["qualified"]) or p["u"] > u_max for p in preds]))
        bad_times = defaultdict(list)
        for af, recs in agents.items():
            bad_times[af] = [r["wall_s"] for r in recs if r["kind"] == "observation" and r["adequacy"] == 0]
        ps, ys = [], []
        for p in preds:
            if p["wall_s"] + cal_horizon_s > end["wall_s"]:
                continue
            ps.append(p["p_inad"])
            ys.append(int(any(p["wall_s"] < t <= p["wall_s"] + cal_horizon_s for t in bad_times[p["af_id"]])))
        if ps:
            ps, ys = np.array(ps), np.array(ys)
            edges = np.linspace(0, 1, 11)
            errs = []
            for lo, hi in zip(edges[:-1], edges[1:]):
                k = (ps >= lo) & ((ps < hi) if hi < 1 else (ps <= hi))
                if k.any():
                    errs.append(abs(ps[k].mean() - ys[k].mean()))
            m["calibration_error"] = float(np.mean(errs)) if errs else None
            werr = 0.0                      # sample-weighted ECE (same definition as the training gate)
            for lo, hi in zip(edges[:-1], edges[1:]):
                k = (ps >= lo) & ((ps < hi) if hi < 1 else (ps <= hi))
                if k.any():
                    werr += k.sum() * abs(ps[k].mean() - ys[k].mean())
            m["calibration_error_weighted"] = float(werr / len(ps))
            m["calibration_n"] = int(len(ps))

    # ---------------- submissions: eq. (28), deadlines, overhead
    subs = [r for r in j if r["kind"] == "submit"]
    resp = {r["correlation_id"]: r for r in j if r["kind"] == "nef_response"}
    intents = sorted((r for r in j if r["kind"] == "intent"), key=lambda r: r["arrival_mono"])
    m["nef_submission_rate_per_s"] = len(subs) / duration
    m["submissions"] = len(subs)
    m["deadline_miss_fraction"] = (sum(1 for s in subs if s.get("late_s", 0) > LATE_TOL_S) / len(subs)) if subs else None
    m["max_lateness_s"] = max((s.get("late_s", 0) for s in subs), default=None)
    m["coordination_overhead_ms"] = (percentile([s["queue_delay_s"] for s in subs if "queue_delay_s" in s], 0.5) or 0) * 1000 if subs else None
    m["median_service_s"] = percentile([r["service_s"] for r in resp.values()], 0.5)
    if intents:
        t_first = intents[0]["arrival_mono"]
        burst = {i["correlation_id"] for i in intents if i["arrival_mono"] - t_first <= 2.0}
        bs = [s for s in subs if s["correlation_id"] in burst]
        m["burst_size"] = len(burst)
        m["burst_deadline_miss_fraction"] = (sum(1 for s in bs if s.get("late_s", 0) > LATE_TOL_S) / len(bs)) if bs else None
        done = [resp[c]["mono_s"] for c in burst if c in resp]
        m["burst_completion_s"] = (max(done) - t_first) if done else None
    ev_p = os.path.join(run_dir, "evidence.json")
    if os.path.exists(ev_p):
        ev = read_json(ev_p)
        n = max(1, len(ev["subscriptions"]))
        m["allocated_fraction"] = sum(1 for s in ev["subscriptions"] if s["state"] == "allocated") / n
        m["unverified_fraction"] = sum(1 for s in ev["subscriptions"] if s["state"] == "unverified") / n
        acc = [s for s in ev["subscriptions"] if s["state"] not in ("rejected", "planned")]
        m["cp_allocated_fraction"] = (sum(1 for s in acc if s.get("cp_state") == "cp_allocated") / len(acc)) if acc else None
        rel = [s for s in ev["subscriptions"] if "release_state" in s]
        m["released_fraction"] = (sum(1 for s in rel if s["release_state"] == "released") / len(rel)) if rel else None
    aud = os.path.join(run_dir, "audit.json")
    m["audit_ok"] = read_json(aud)["ok"] if os.path.exists(aud) else None
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True, help="run dirs or globs")
    ap.add_argument("--out", default="metrics.jsonl")
    a = ap.parse_args()
    dirs = sorted({d for g in a.runs for d in glob.glob(g) if os.path.isdir(d)})
    with open(a.out, "w") as f:
        for d in dirs:
            try:
                m = run_metrics(d)
            except (StopIteration, FileNotFoundError) as e:
                print("skip:", d, e)
                continue
            f.write(json.dumps(m) + "\n")
            durable_json(os.path.join(d, "metrics.json"), m)
    print(f"{len(dirs)} runs -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
