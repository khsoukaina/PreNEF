#!/usr/bin/env python3
"""Build the DTIP dataset from PReNEF run journals (runtime.py output).

Label = time until the CONFIRMED mode at t becomes inadequate according to
eq. (4) evaluated on the AF's own LATER observations. This is computable for
every arm (it does not depend on PReNEF decisions) and contains no injected
ground truth. Right-censoring is explicit: if no inadequacy is seen before the
end of the run (or before the AF changes mode), t_to_inad_s = null and
censor_s = remaining observed time.

Output JSONL rows:
 {"run_id","block","arm","af_id","t_wall","mode","features":[...],
  "feature_names":[...],"t_to_inad_s":float|null,"censor_s":float}
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dtip.features import FEATURE_NAMES, extract  # noqa: E402
from prenef.common import read_json, read_jsonl, verify_chain  # noqa: E402
from prenef.contracts import adequacy, parse_contract  # noqa: E402


def build_run(journal: str, contracts: dict, stride_s: float) -> list[dict]:
    ok, msg = verify_chain(journal)
    if not ok:
        raise SystemExit(f"{journal}: journal integrity check failed: {msg}")
    meta, obs, modes = {}, defaultdict(list), defaultdict(list)
    for r in read_jsonl(journal):
        if r["kind"] == "run_start":
            meta = r
        elif r["kind"] == "observation":
            obs[r["af_id"]].append(r["observation"])
        elif r["kind"] == "mode_confirmed":
            modes[r["af_id"]].append((r["wall_s"], r["mode"]))
    rows = []
    for af, hist in obs.items():
        c = contracts.get(af)
        if c is None:
            continue
        hist.sort(key=lambda h: h["obs_wall_s"])
        mchanges = sorted(modes.get(af, []))

        def mode_at(t):
            m = None
            for tw, mm in mchanges:
                if tw <= t:
                    m = mm
            return m

        def next_change(t):
            return next((tw for tw, _ in mchanges if tw > t), None)

        # adequacy series under each observation's own confirmed mode
        t_end = hist[-1]["obs_wall_s"]
        last_t = -1e18
        for idx, h in enumerate(hist):
            t = h["obs_wall_s"]
            if t - last_t < stride_s:
                continue
            last_t = t
            m = mode_at(t)
            if m is None:
                continue
            horizon_end = min(t_end, next_change(t) or t_end)
            t_inad = None
            for h2 in hist[idx + 1:]:
                if h2["obs_wall_s"] > horizon_end:
                    break
                a, _ = adequacy(c, m, h2, {k: v.get("up") for k, v in (h2.get("services") or {}).items()},
                                h2["obs_wall_s"])
                if a == 0:
                    t_inad = h2["obs_wall_s"] - t
                    break
            others = 0
            for af2 in obs:
                m2 = mode_at_af(modes, af2, t) if af2 != af and af2 in contracts else None
                if m2 and m2 in contracts[af2].modes and \
                        c.modes[m].dependencies & contracts[af2].modes[m2].dependencies:
                    others += 1
            rows.append({
                "run_id": meta.get("run_id", os.path.basename(os.path.dirname(journal))),
                "run_start_wall_s": meta.get("wall_s"),
                "block": meta.get("block"), "arm": meta.get("policy"), "af_id": af, "t_wall": t, "mode": m,
                "features": extract(hist, t, sorted(c.modes[m].dependencies), others),
                "feature_names": FEATURE_NAMES,
                "t_to_inad_s": t_inad, "censor_s": horizon_end - t,
            })
    return rows


def mode_at_af(modes, af, t):
    m = None
    for tw, mm in sorted(modes.get(af, [])):
        if tw <= t:
            m = mm
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journals", nargs="+", required=True, help="glob(s) of runs/*/journal.jsonl")
    ap.add_argument("--contracts", nargs="+", required=True)
    ap.add_argument("--stride-s", type=float, default=0.5)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    contracts = {}
    for p in a.contracts:
        c = parse_contract(read_json(p))
        contracts[c.af_id] = c
    paths = sorted({p for g in a.journals for p in glob.glob(g)})
    n = 0
    with open(a.out, "w") as f:
        for p in paths:
            for row in build_run(p, contracts, a.stride_s):
                f.write(json.dumps(row) + "\n")
                n += 1
    print(f"{n} samples from {len(paths)} runs -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
