#!/usr/bin/env bash
# Full data-plane repair: UEs get exactly the IPs in binding.json (NEF maps only those to SUPIs).
# usage: lab/repair_dataplane.sh [max_attempts]
set -u
MAX=${1:-3}; GNB=ueransim-qod423; N6=iperf3-n6-qod423
mapfile -t ROWS < <(python3 -c "
import json; b=json.load(open('binding.json'))['afs']
for a in sorted(b): print(a, b[a]['container'], b[a].get('tun','uesimtun0'), b[a]['ue_ipv4'])")
UES=$(for r in "${ROWS[@]}"; do set -- $r; echo -n "$2 "; done)
ip_of() { docker exec "$1" ip -4 -o addr show "$2" 2>/dev/null | awk '{print $4}' | cut -d/ -f1; }
echo "current IPs:"; for r in "${ROWS[@]}"; do set -- $r; echo "  $1 $2 expected $4 has '$(ip_of $2 $3)'"; done
for attempt in $(seq 1 $MAX); do
  echo "=== attempt $attempt/$MAX"
  docker stop $UES >/dev/null
  docker restart upf-qod423 >/dev/null; sleep 5
  docker restart smf-qod423 >/dev/null; sleep 8
  T=$(date +%s); docker restart $GNB >/dev/null
  for i in $(seq 1 40); do
    docker logs --since "$T" $GNB 2>&1 | grep -q "NG Setup procedure is successful" && break; sleep 1; done
  docker logs --since "$T" $GNB 2>&1 | grep -q "NG Setup procedure is successful" \
    && echo "gNB ready" || { echo "gNB did not finish NG Setup in 40 s"; continue; }
  sleep 3; ok=1
  for r in "${ROWS[@]}"; do
    set -- $r; af=$1; ctr=$2; tun=$3; want=$4
    docker start $ctr >/dev/null
    got=""; for i in $(seq 1 40); do got=$(ip_of $ctr $tun); [ -n "$got" ] && break; sleep 1; done
    if [ "$got" = "$want" ]; then echo "  $af $ctr -> $got OK"; sleep 5
    else echo "  $af $ctr -> '$got' but expected $want: restarting the sequence"; ok=0; break; fi
  done
  [ $ok = 1 ] || continue
  sudo nsenter -t $(docker inspect -f '{{.State.Pid}}' $N6) -n ip route replace 10.70.0.0/16 via 10.101.200.11
  sleep 2; allok=1
  for r in "${ROWS[@]}"; do
    set -- $r
    l=$(docker exec $2 ping -c 5 -W 1 -I $3 10.101.200.30 | grep -o '[0-9]*% packet loss')
    echo "  ping $1: $l"; [ "$l" = "0% packet loss" ] || allok=0
  done
  [ $allok = 1 ] && { echo "DATA PLANE OK (all IPs match, 0% loss)"; exit 0; }
done
echo "FAILED after $MAX attempts - send the output"; exit 1
