#!/usr/bin/env python3
"""Post-run audit of a PReNEF journal: integrity + decision constraints (13)-(19), (24).

  python3 -m prenef.audit --run-dir runs/b07-prenef_dtip --contracts config/contracts/*.json

Exit 0 only if the chain is intact and no constraint is violated. Benchmark
blocks whose audit fails must be excluded (and reported as excluded).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nef.as_session_qos import ALLOC_POSITIVE  # noqa: E402
from prenef.common import durable_json, read_json, read_jsonl, verify_chain  # noqa: E402
from prenef.contracts import parse_contract  # noqa: E402


def audit(run_dir: str, contracts: dict) -> dict:
    jp = os.path.join(run_dir, "journal.jsonl")
    ok, msg = verify_chain(jp)
    v: dict[str, list] = defaultdict(list)
    if not ok:
        v["integrity"].append(msg)
    recs = list(read_jsonl(jp))
    start = next((r for r in recs if r["kind"] == "run_start"), {})
    policy = start.get("policy")
    planner = start.get("planner") or {}
    u_max = planner.get("u_max")
    intents = {r["correlation_id"]: r for r in recs if r["kind"] == "intent"}
    submits = defaultdict(int)
    positive = set()
    for r in recs:
        k = r["kind"]
        if k == "alert" and r.get("recommended_mode"):
            c = contracts.get(r["af_id"])
            if c and r["recommended_mode"] not in c.modes:
                v["eq13_undeclared_mode"].append(r["seq"])
            if c and "alert" not in c.actions:
                v["eq14_action_not_consented"].append(r["seq"])
        elif k == "submit":
            it = intents.get(r["correlation_id"])
            c = contracts.get(r["af_id"])
            if not it or not c or not c.allows_profile(it["mode"], r["profile"]):
                v["eq15_profile_not_consented"].append(r["seq"])
            submits[(r["af_id"], r["intent_id"], r["correlation_id"])] += 1
            just = r.get("justification") or {}
            # eq. (24) binds PReNEF only: baselines (fifo/edf/...) may be late, that is a RESULT,
            # not a violation. A late PReNEF submission is a violation only if a feasible order
            # existed and the guard was enabled (ablation runs disable it on purpose).
            if policy in ("prenef_noai", "prenef_dtip") and planner.get("guard", True) \
                    and r.get("late_s", 0) > 0.05 and just.get("feasible_order_existed", True):
                v["eq24_avoidable_late_submission"].append({"seq": r["seq"], "late_s": r["late_s"]})
            terms = just.get("score_terms") or {}
            if planner.get("uncertainty_gate", True) and terms.get("ai_used") and u_max is not None \
                    and terms.get("confidence", 1) < 1 - u_max - 1e-9:
                v["eq19_ai_used_above_umax"].append(r["seq"])
        elif k == "notification" and set(r.get("events") or []) & ALLOC_POSITIVE and r.get("correlation_id"):
            positive.add(r["correlation_id"])
    per_intent = defaultdict(int)
    for (af, iid, cid), n in submits.items():
        per_intent[(af, iid, cid)] += n
        if n > 1:
            v["eq16_multiple_submissions"].append([af, iid, cid])
    summ_path = os.path.join(run_dir, "run_summary.json")
    if os.path.exists(summ_path):
        for it in read_json(summ_path)["intents"]:
            if it["state"] == "allocated" and it["correlation_id"] not in positive:
                v["eq17_allocated_without_evidence"].append(it["correlation_id"])
    report = {"run_dir": run_dir, "policy": policy, "integrity": msg, "records": len(recs),
              "violations": {k: vv for k, vv in v.items() if vv}, "ok": ok and not any(v.values())}
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--contracts", nargs="+", required=True)
    a = ap.parse_args()
    cs = {}
    for p in a.contracts:
        c = parse_contract(read_json(p))
        cs[c.af_id] = c
    rep = audit(a.run_dir, cs)
    durable_json(os.path.join(a.run_dir, "audit.json"), rep)
    print(json.dumps({k: rep[k] for k in ("policy", "integrity", "ok")}), json.dumps(rep["violations"])[:2000])
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
