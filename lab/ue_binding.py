#!/usr/bin/env python3
"""Establish the AF -> UE container -> PDU session IP -> flow binding.

Read-only: runs `docker inspect` and `docker exec <ue> ip -4 -o addr show`
(plus `nr-cli ... ps-list` if --imsi is configured). Nothing is configured.

The Docker address of a UE container (10.101.200.x) is NOT the UE IP the
SMF/UPF know. The UE IP is the address on uesimtunN, allocated from the UPF
pool (e.g. 10.60.0.0/16). AsSessionWithQoS must carry that address.

Input  config/binding.request.json
  {"af1": {"container": "ueransim-ue-qod423", "tun": "uesimtun0", "imsi": "imsi-208930000000001"},
   "af2": {"container": "ueransim-ue2-qod423", "tun": "uesimtun0"}, ...}
Output binding.json with ip, interface, container id, image digest, timestamps,
and a consistency report (duplicate IPs, missing tunnels, exited containers).
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prenef.common import durable_json, read_json  # noqa: E402

ADDR_RE = re.compile(r"^\d+:\s+(\S+)\s+inet\s+(\d+\.\d+\.\d+\.\d+)/(\d+)")


def run(cmd: list[str], timeout: float = 10.0) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)
    except Exception as e:  # noqa: BLE001
        return 99, str(e)


def parse_addrs(text: str) -> dict[str, tuple[str, int]]:
    out = {}
    for line in text.splitlines():
        m = ADDR_RE.match(line.strip())
        if m:
            out[m.group(1)] = (m.group(2), int(m.group(3)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--out", default="binding.json")
    ap.add_argument("--ue-pool", default="10.60.0.0/16", help="UPF UE pool (check upfcfg/smfcfg)")
    ap.add_argument("--docker", default="docker")
    a = ap.parse_args()
    req = read_json(a.request)
    pool = ipaddress.ip_network(a.ue_pool)
    result: dict = {"collected_wall_s": time.time(), "ue_pool": a.ue_pool, "afs": {}, "problems": []}
    seen_ip: dict[str, str] = {}
    for af, spec in sorted(req.items()):
        ctr, tun = spec["container"], spec.get("tun", "uesimtun0")
        entry: dict = {"container": ctr, "tun": tun}
        rc, out = run([a.docker, "inspect", ctr])
        if rc != 0:
            entry["error"] = "container not found"
            result["problems"].append(f"{af}: container {ctr} not found")
            result["afs"][af] = entry
            continue
        info = json.loads(out)[0]
        entry.update(container_id=info["Id"][:12], image=info["Config"]["Image"],
                     image_id=info["Image"], running=info["State"]["Running"])
        if not entry["running"]:
            result["problems"].append(f"{af}: container {ctr} is not running")
            result["afs"][af] = entry
            continue
        rc, out = run([a.docker, "exec", ctr, "ip", "-4", "-o", "addr", "show"])
        addrs = parse_addrs(out) if rc == 0 else {}
        entry["interfaces"] = {k: f"{v[0]}/{v[1]}" for k, v in addrs.items()}
        if tun not in addrs:
            result["problems"].append(f"{af}: {tun} absent in {ctr} (no PDU session?)")
        else:
            ip = addrs[tun][0]
            entry["ue_ipv4"] = ip
            if ipaddress.ip_address(ip) not in pool:
                result["problems"].append(f"{af}: {ip} outside UE pool {a.ue_pool}")
            if ip in seen_ip:
                result["problems"].append(f"{af}: UE IP {ip} duplicates {seen_ip[ip]}")
            seen_ip[ip] = af
        if spec.get("imsi"):
            rc, out = run([a.docker, "exec", ctr, "./nr-cli", spec["imsi"], "-e", "ps-list"])
            if rc != 0:
                rc, out = run([a.docker, "exec", ctr, "nr-cli", spec["imsi"], "-e", "ps-list"])
            entry["ps_list"] = out.strip()[:2000] if rc == 0 else None
        result["afs"][af] = entry
    images = {e.get("image_id") for e in result["afs"].values() if e.get("image_id")}
    if len(images) > 1:
        result["problems"].append(f"UE containers run {len(images)} different images: pin one digest")
    durable_json(a.out, result)
    for af, e in result["afs"].items():
        print(f"{af:6} {e.get('container',''):24} {e.get('ue_ipv4','-'):16} running={e.get('running')}")
    for p in result["problems"]:
        print("PROBLEM:", p)
    return 0 if not result["problems"] else 1


if __name__ == "__main__":
    sys.exit(main())
