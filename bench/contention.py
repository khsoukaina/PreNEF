#!/usr/bin/env python3
"""Contention experiment: where request ORDERING (fifo / edf / static_priority / PReNEF
guard) matters, i.e. when the NEF->PCF path is the bottleneck.

For each number of AFs N and repetition r, one burst of N AsSessionWithQoS
requests with random deadlines (same seed for every policy -> paired) is
submitted following each policy's order with C slots (direct_nef: unbounded).
Afterwards every created subscription is DELETEd.

Measured per (N, r, policy): deadline miss fraction (POST start > t_last),
weight-weighted miss, max lateness, batch completion, NEF service time.
This is a batch (static) plan; the live runtime re-plans continuously.

Mock (emulated contention, capacity = NEF parallelism):
  python3 nef/mock_nef.py --port 18000 --capacity 1 --service-s 0.3 &
  python3 bench/contention.py --api-root http://127.0.0.1:18000 --target-is-mock \
     --n-afs 4,8,16,32 --repeats 10 --out campaigns/contention-mock
Lab (real NEF; creates N subscriptions per burst, deletes them):
  python3 bench/contention.py --api-root http://10.101.200.14:8000 --binding binding.json \
     --notif-dest http://10.101.200.1:18080/notify --n-afs 4,8,16 --repeats 10 \
     --approve-live-NEF-operation --out campaigns/contention-lab
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
import threading
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from nef.as_session_qos import NefClient, build_subscription, classify_create  # noqa: E402
from prenef.common import durable_json, percentile, read_json  # noqa: E402
from prenef.contracts import parse_contract  # noqa: E402
from prenef.graph_state import Registry  # noqa: E402
from prenef.planner import PlannerConfig, Request, plan  # noqa: E402

POLICIES = ["direct_nef", "fifo", "edf", "static_priority", "prenef_noai"]


def make_contracts(templates: list[dict], n: int) -> list[dict]:
    out = []
    for k in range(n):
        raw = copy.deepcopy(templates[k % len(templates)])
        raw["af_id"] = raw["scs_as_id"] = f"c{k:02d}"
        for fl in raw["flows"]:
            fl["remote_port"] = 6000 + k          # distinct flow per synthetic AF
        out.append(raw)
    return out


def run_burst(a, raws, ue_ips, deadlines, policy, service_est) -> dict:
    reg = Registry([parse_contract(r) for r in raws])
    for c in reg.contracts.values():
        reg.confirm_mode(c.af_id, max(c.modes, key=lambda m: c.modes[m].utility), {"source": "af"})
    raw_by = {r["af_id"]: r for r in raws}
    t0 = time.monotonic() + 0.05
    reqs = []
    for k, c in enumerate(reg.contracts.values()):
        m = reg.confirmed_mode[c.af_id]
        reqs.append(Request(f"q{k}", c.af_id, "burst", m, c.modes[m].qos_profiles[0], t0, t0 + deadlines[k], service_est))
    dec, meta = plan(PlannerConfig(policy=policy, concurrency=a.concurrency), reg, reqs, {}, t0)
    order = [d for d in dec if d.kind == "submit"]
    conc = meta["concurrency"]
    sem = threading.Semaphore(conc)
    results, locs, lock = [], [], threading.Lock()

    def worker(d):
        try:
            r = next(x for x in reqs if x.request_id == d.request_id)
            raw = raw_by[d.af_id]
            k = int(d.af_id[1:])
            body = build_subscription(raw, r.profile, ue_ips[k % len(ue_ips)],
                                      f"{a.notif_dest.rstrip('/')}/{d.af_id}", events=None)
            nef = NefClient(a.api_root, raw["scs_as_id"], token=a.token, transport=a.transport)
            post = time.monotonic()
            res = nef.create(body)
            st, info = classify_create(res)
            with lock:
                results.append({"af": d.af_id, "w": raw["weight"], "late_s": max(0.0, post - r.t_last_mono),
                                "service_s": res.t_done_mono - res.t_send_mono, "status": res.status,
                                "done_mono": res.t_done_mono})
                if info.get("location"):
                    locs.append((raw["scs_as_id"], info["location"]))
        finally:
            sem.release()

    threads = []
    time.sleep(max(0.0, t0 - time.monotonic()))
    for d in order:                       # dispatch strictly in planned order, C at a time
        sem.acquire()
        th = threading.Thread(target=worker, args=(d,))
        th.start()
        threads.append(th)
    for th in threads:
        th.join()
    for scs, loc in locs:                 # cleanup (block J): DELETE everything created
        NefClient(a.api_root, scs, token=a.token, transport=a.transport).delete(loc)
    late = [x["late_s"] > 0.05 for x in results]
    # POST-start deadlines are trivially met by direct_nef (it never waits locally, the NEF queues
    # instead). Completion deadlines (response by t_last + nominal service) are the fair comparison.
    t_last = {r.af_id: r.t_last_mono for r in reqs}
    comp_late = [x["done_mono"] > t_last[x["af"]] + service_est + 0.05 for x in results]
    wsum = sum(x["w"] for x in results) or 1
    return {"policy": policy, "n": len(raws), "miss_fraction": float(np.mean(late)) if late else None,
            "weighted_miss": sum(x["w"] for x in results if x["late_s"] > 0.05) / wsum,
            "completion_miss_fraction": float(np.mean(comp_late)) if comp_late else None,
            "max_lateness_s": max((x["late_s"] for x in results), default=None),
            "completion_s": (max(x["done_mono"] for x in results) - t0) if results else None,
            "median_service_s": percentile([x["service_s"] for x in results], 0.5),
            "http_errors": sum(1 for x in results if x["status"] != 201),
            "feasible_order_existed": meta.get("feasible")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-root", required=True)
    ap.add_argument("--contracts", nargs="+", default=[f"config/contracts/af{i}.json" for i in range(1, 5)])
    ap.add_argument("--binding", help="binding.json (lab): UE IPs are cycled over synthetic AFs")
    ap.add_argument("--notif-dest", default="http://127.0.0.1:18080/notify")
    ap.add_argument("--n-afs", default="4,8,16,32")
    ap.add_argument("--policies", default=",".join(POLICIES))
    ap.add_argument("--repeats", type=int, default=10)
    ap.add_argument("--deadline-range", default="0.5,6.0", help="uniform t_last range (s)")
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--service-s-est", type=float, default=0.4, help="planner estimate; measure it first")
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--token", default=os.environ.get("NEF_TOKEN"))
    ap.add_argument("--transport", choices=["http1", "h2c"], default="http1")
    ap.add_argument("--pause-s", type=float, default=2.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--approve-live-NEF-operation", action="store_true")
    ap.add_argument("--target-is-mock", action="store_true")
    a = ap.parse_args()
    if not (a.approve_live_NEF_operation or a.target_is_mock):
        print("refusing: creates and deletes NEF subscriptions; pass --approve-live-NEF-operation or --target-is-mock",
              file=sys.stderr)
        return 2
    templates = [read_json(os.path.join(ROOT, p) if not os.path.isabs(p) else p) for p in a.contracts]
    ue_ips = [e["ue_ipv4"] for e in read_json(a.binding)["afs"].values() if e.get("ue_ipv4")] if a.binding \
        else [f"10.60.0.{i}" for i in range(1, 5)]
    lo, hi = (float(x) for x in a.deadline_range.split(","))
    policies = [p for p in a.policies.split(",") if p]
    rng = random.Random(a.seed)
    os.makedirs(a.out, exist_ok=True)
    rows = []
    for n in [int(x) for x in a.n_afs.split(",")]:
        raws = make_contracts(templates, n)
        for rep in range(a.repeats):
            deadlines = [rng.uniform(lo, hi) for _ in range(n)]
            order = policies[:]
            rng.shuffle(order)                  # randomise policy order within each (n, rep)
            for pol in order:
                r = run_burst(a, raws, ue_ips, deadlines, pol, a.service_s_est)
                r.update(rep=rep)
                rows.append(r)
                print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}))
                time.sleep(a.pause_s)
    with open(os.path.join(a.out, "contention.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    summary = {}
    for n in sorted({r["n"] for r in rows}):
        for pol in policies:
            sel = [r for r in rows if r["n"] == n and r["policy"] == pol]
            summary[f"{pol}@{n}"] = {k: float(np.mean([r[k] for r in sel if r[k] is not None]))
                                     for k in ("miss_fraction", "completion_miss_fraction", "weighted_miss",
                                               "completion_s", "median_service_s")}
    durable_json(os.path.join(a.out, "summary.json"), {"mock": a.target_is_mock, "summary": summary})
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(1, 2, figsize=(10, 3.8))
        ns = sorted({r["n"] for r in rows})
        for pol in policies:
            axs[0].plot(ns, [summary[f"{pol}@{n}"]["completion_miss_fraction"] for n in ns], marker="o", label=pol)
            axs[1].plot(ns, [summary[f"{pol}@{n}"]["completion_s"] for n in ns], marker="o", label=pol)
        axs[0].set_ylabel("completion-deadline miss fraction")
        axs[1].set_ylabel("batch completion (s)")
        for ax in axs:
            ax.set_xlabel("number of AFs in the burst")
            ax.spines[["top", "right"]].set_visible(False)
        axs[0].legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(a.out, "contention.png"), dpi=150)
    except ImportError:
        pass
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
