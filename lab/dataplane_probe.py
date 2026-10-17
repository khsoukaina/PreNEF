#!/usr/bin/env python3
"""Data-plane evidence (source D of evidence_collector): does the QoS change anything?

Sends test traffic, so it requires --approve-live-traffic.
  1. Optional competing load from other UE containers (--competitors).
  2. iperf3 UDP/TCP from the target UE, bound to its uesimtun IP, towards the
     N6 server (default iperf3-n6-qod423), for --duration-s.
  3. Records goodput, loss and jitter (UDP) and a verdict:
       qos_effect_observed   measured >= min_ratio * expected_kbps
       no_effect             otherwise
       error                 tool missing / no tunnel / timeout
Run it once BEFORE the subscription (phase=pre) and once AFTER (phase=post).
Without a real bottleneck (lab/bottleneck.sh) both phases will look the same:
UERANSIM has no radio scheduler, so QoS can only show up where you shape.

Prereqs: iperf3 in the UE image (`apt-get install -y iperf3` / `apk add iperf3`)
and `iperf3 -s` running in the server container.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prenef.common import read_json  # noqa: E402


def iperf(container: str, bind_ip: str, server: str, port: int, secs: float, udp: bool, rate: str | None):
    cmd = ["docker", "exec", container, "iperf3", "-c", server, "-p", str(port), "-B", bind_ip,
           "-t", str(int(max(1, secs))), "-J"]
    if udp:
        cmd += ["-u", "-b", rate or "10M"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=secs + 20)
    if p.returncode != 0:
        return {"error": (p.stderr or p.stdout)[-400:]}
    j = json.loads(p.stdout)
    end = j.get("end", {})
    if udp:
        s = end.get("sum", {})
        return {"kbps": s.get("bits_per_second", 0) / 1e3, "loss_pct": s.get("lost_percent"),
                "jitter_ms": s.get("jitter_ms")}
    s = end.get("sum_received", {})
    return {"kbps": s.get("bits_per_second", 0) / 1e3}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binding", required=True, help="binding.json from ue_binding.py")
    ap.add_argument("--af", required=True)
    ap.add_argument("--server", default="10.101.200.30")
    ap.add_argument("--port", type=int, default=5201)
    ap.add_argument("--competitors", default="", help="comma list of AF ids generating load")
    ap.add_argument("--competitor-port", type=int, default=5202)
    ap.add_argument("--duration-s", type=float, default=10)
    ap.add_argument("--udp", action="store_true")
    ap.add_argument("--rate", default="20M")
    ap.add_argument("--expect-kbps", type=float, required=True, help="rate the QoS profile should protect")
    ap.add_argument("--min-ratio", type=float, default=0.9)
    ap.add_argument("--expect-mode", choices=["floor", "cap"], default="floor",
                    help="floor: protected rate >= min_ratio*expect (GBR-like); "
                         "cap: rate <= (2-min_ratio)*expect while offering more (MBR/QER enforced)")
    ap.add_argument("--phase", choices=["pre", "post"], required=True)
    ap.add_argument("--correlation-id", default=None)
    ap.add_argument("--out", default="probes.jsonl")
    ap.add_argument("--approve-live-traffic", action="store_true")
    a = ap.parse_args()
    if not a.approve_live_traffic:
        print("refusing: sends test traffic; pass --approve-live-traffic", file=sys.stderr)
        return 2
    b = read_json(a.binding)["afs"]
    tgt = b.get(a.af, {})
    if not tgt.get("ue_ipv4"):
        print(f"{a.af}: no UE IP in binding", file=sys.stderr)
        return 1
    procs = []
    for c in [x for x in a.competitors.split(",") if x]:
        cb = b.get(c, {})
        if cb.get("ue_ipv4"):
            procs.append(subprocess.Popen(
                ["docker", "exec", cb["container"], "iperf3", "-c", a.server, "-p", str(a.competitor_port),
                 "-B", cb["ue_ipv4"], "-t", str(int(a.duration_s + 4)), "-u", "-b", "100M"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    if procs:
        time.sleep(2)
    t0 = time.time()
    try:
        res = iperf(tgt["container"], tgt["ue_ipv4"], a.server, a.port, a.duration_s, a.udp, a.rate)
    except subprocess.TimeoutExpired:
        res = {"error": "timeout"}
    finally:
        for p in procs:
            p.terminate()
    if "error" in res:
        verdict = "error"
    elif a.expect_mode == "floor":
        verdict = "qos_effect_observed" if res["kbps"] >= a.min_ratio * a.expect_kbps else "no_effect"
    else:
        verdict = "qos_effect_observed" if res["kbps"] <= (2 - a.min_ratio) * a.expect_kbps else "no_effect"
    rec = {"af_id": a.af, "phase": a.phase, "wall_s": t0, "correlation_id": a.correlation_id,
           "ue_ipv4": tgt["ue_ipv4"], "server": a.server, "competitors": a.competitors,
           "expect_kbps": a.expect_kbps, "expect_mode": a.expect_mode, "result": res, "verdict": verdict if a.phase == "post" else "baseline"}
    with open(a.out, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
