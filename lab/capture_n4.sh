#!/usr/bin/env bash
# Passive N4 (PFCP, UDP 8805) capture in the UPF container's network namespace.
# Does not modify anything. Needs root (nsenter) and tcpdump on the host.
#   sudo lab/capture_n4.sh upf-qod423 runs/<run>/n4.pcap          # start (background)
#   sudo lab/capture_n4.sh --stop runs/<run>/n4.pcap               # stop
set -euo pipefail
if [[ "${1:-}" == "--stop" ]]; then
  pidf="${2:?pcap path}.pid"; [[ -f "$pidf" ]] && kill "$(cat "$pidf")" && rm -f "$pidf"; exit 0
fi
ctr="${1:?container}"; out="${2:?pcap path}"
mkdir -p "$(dirname "$out")"
pid=$(docker inspect -f '{{.State.Pid}}' "$ctr")
[[ "$pid" != "0" ]] || { echo "$ctr not running" >&2; exit 1; }
setsid nsenter -t "$pid" -n tcpdump -i any -U -w "$out" 'udp port 8805' </dev/null >/dev/null 2>&1 &
echo $! > "$out.pid"
echo "capturing PFCP of $ctr (pid $pid) -> $out"
