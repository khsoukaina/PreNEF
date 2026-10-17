#!/usr/bin/env python3
"""Per-second uplink goodput of every UE towards the N6 server, logged for a whole campaign.
Runs next to bench/run_campaign.py; bench/qos_metrics.py --tput cuts it per run by time.
  python3 lab/tput_logger.py --binding binding.json --out campaigns/qos/tput.jsonl --approve-live-traffic
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prenef.common import read_json  # noqa: E402

STOP = threading.Event()
LOCK = threading.Lock()


def kbps(rate):
    r = rate.strip().upper()
    mult = {"K": 1.0, "M": 1e3, "G": 1e6}.get(r[-1], 1e-3)
    return float(r[:-1] if r[-1] in "KMG" else r) * mult


def has_iperf(ctr):
    return subprocess.run(["docker", "exec", ctr, "sh", "-c", "command -v iperf3"], capture_output=True).returncode == 0


def write(fh, rec):
    with LOCK:
        fh.write(json.dumps(rec) + "\n")
        fh.flush()


def worker(a, af, e, port, fh):
    cmd = ["docker", "exec", e["container"], "iperf3", "-c", a.server_ip, "-p", str(port), "-B", e["ue_ipv4"],
           "-t", str(a.segment_s), "-i", "1", "-J", "--get-server-output", "-b", a.rate]
    if a.proto == "udp":
        cmd += ["-u", "-l", "1200"]
    offered = kbps(a.rate)
    while not STOP.is_set():
        t_launch = time.time()
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=a.segment_s + 25)
            j = json.loads(p.stdout) if p.stdout.strip().startswith("{") else {"error": (p.stderr or "no output")[-300:]}
        except subprocess.TimeoutExpired:
            j = {"error": "timeout"}
        except json.JSONDecodeError as ex:
            j = {"error": f"bad json: {ex}"}
        if j.get("error"):
            write(fh, {"kind": "error", "af": af, "wall_s": t_launch, "error": str(j["error"])[:300]})
            STOP.wait(2.0)
            continue
        srv = j.get("server_output_json") or {}
        ivs, side = srv.get("intervals"), "receiver"
        t0 = (srv.get("start", {}).get("timestamp", {}) or {}).get("timesecs")
        if not ivs or t0 is None:
            ivs, side = j.get("intervals", []), "sender"
            t0 = j.get("start", {}).get("timestamp", {}).get("timesecs", t_launch)
        for iv in ivs:
            s = iv.get("sum", {})
            if s.get("seconds", 0) < 0.5:
                continue
            write(fh, {"kind": "tput", "af": af, "wall_s": float(t0) + float(s.get("start", 0)),
                       "dur_s": s.get("seconds"), "rx_kbps": s.get("bits_per_second", 0) / 1e3,
                       "offered_kbps": offered, "lost_pct": s.get("lost_percent"), "jitter_ms": s.get("jitter_ms"),
                       "proto": a.proto, "side": side})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--binding", required=True)
    ap.add_argument("--server-ip", default="10.101.200.30")
    ap.add_argument("--server-container", default="iperf3-n6-qod423")
    ap.add_argument("--base-port", type=int, default=5211)
    ap.add_argument("--afs", default="")
    ap.add_argument("--proto", choices=["tcp", "udp"], default="tcp")
    ap.add_argument("--rate", default="5M")
    ap.add_argument("--segment-s", type=int, default=30)
    ap.add_argument("--duration-s", type=float, default=0, help="0 = until stopped")
    ap.add_argument("--out", required=True)
    ap.add_argument("--approve-live-traffic", action="store_true")
    a = ap.parse_args()
    if not a.approve_live_traffic:
        print("refusing: sends test traffic; pass --approve-live-traffic", file=sys.stderr)
        return 2
    b = read_json(a.binding)["afs"]
    afs = [x for x in (a.afs.split(",") if a.afs else sorted(b)) if x]
    if not has_iperf(a.server_container):
        print(f"iperf3 not found in {a.server_container}", file=sys.stderr)
        return 1
    missing = [af for af in afs if not has_iperf(b[af]["container"])]
    if missing:
        print("iperf3 missing in: " + ", ".join(f"{af} ({b[af]['container']})" for af in missing), file=sys.stderr)
        return 1
    ports = {af: a.base_port + k for k, af in enumerate(afs)}
    for af in afs:
        subprocess.run(["docker", "exec", "-d", a.server_container, "iperf3", "-s", "-p", str(ports[af])])
    time.sleep(1.0)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    fh = open(a.out, "a")
    write(fh, {"kind": "start", "wall_s": time.time(), "afs": afs, "ports": ports, "proto": a.proto, "rate": a.rate})
    signal.signal(signal.SIGTERM, lambda *_: STOP.set())
    signal.signal(signal.SIGINT, lambda *_: STOP.set())
    ths = [threading.Thread(target=worker, args=(a, af, b[af], ports[af], fh), daemon=True) for af in afs]
    for t in ths:
        t.start()
    print(f"logging {a.proto} {a.rate} per UE for {', '.join(afs)} -> {a.out}", flush=True)
    end = time.time() + a.duration_s if a.duration_s > 0 else None
    while not STOP.is_set() and (end is None or time.time() < end):
        STOP.wait(1.0)
    STOP.set()
    for t in ths:
        t.join(timeout=a.segment_s + 30)
    write(fh, {"kind": "stop", "wall_s": time.time()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
