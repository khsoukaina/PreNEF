#!/usr/bin/env python3
"""Quick per-run summary of a campaign:  python3 bench/show.py campaigns/mock0"""
import glob
import json
import os
import sys

KEYS = ["audit_ok", "exposure_s_per_episode", "timely_adaptation_rate", "correlated_coverage_rate",
        "lead_s_median", "unnecessary_transitions", "alerts", "burst_deadline_miss_fraction",
        "coordination_overhead_ms", "allocated_fraction"]


def fmt(v):
    return f"{v:.3f}" if isinstance(v, float) else str(v)


def main() -> int:
    camp = sys.argv[1] if len(sys.argv) > 1 else "."
    for d in sorted(glob.glob(os.path.join(camp, "b*-*"))):
        print(f"== {os.path.basename(d)}")
        mp = os.path.join(d, "metrics.json")
        if os.path.exists(mp):
            m = json.load(open(mp))
            print("   " + "  ".join(f"{k}={fmt(m.get(k))}" for k in KEYS))
        else:
            print("   no metrics.json")
        ap = os.path.join(d, "audit.json")
        if os.path.exists(ap):
            v = json.load(open(ap)).get("violations")
            if v:
                print("   audit violations:", json.dumps(v)[:300])
        for log in [os.path.join(d, "runtime.log")] + glob.glob(os.path.join(d, "agent-*.err")):
            if os.path.exists(log):
                errs = [l.strip() for l in open(log) if "Error" in l or "Traceback" in l]
                if errs:
                    print(f"   {os.path.basename(log)}: {errs[-1][:200]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
