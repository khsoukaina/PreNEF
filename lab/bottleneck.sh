#!/usr/bin/env bash
# Create (or remove) a REAL capacity bottleneck so that QoS differentiation
# becomes observable. UERANSIM has no radio scheduler: without this, a QoS
# profile cannot change any measured outcome.
#
# Shapes egress of one interface inside a container's netns with HTB + fq_codel.
# Mutates the lab -> requires APPROVE=1. Always pair with `--remove`.
#   sudo APPROVE=1 lab/bottleneck.sh upf-qod423 eth0 30mbit        # N6/N3 side of UPF
#   sudo APPROVE=1 lab/bottleneck.sh --remove upf-qod423 eth0
#
# Also check (host, gtp5g kernel module): whether your gtp5g version enforces
# QER MBR. Look for a qos switch under /proc/gtp5g/ and in that version's README.
# If QER is not enforced, PFCP QER IEs are control-plane evidence only.
set -euo pipefail
[[ "${APPROVE:-0}" == "1" ]] || { echo "refusing: set APPROVE=1 (modifies traffic control)"; exit 2; }
remove=0; [[ "${1:-}" == "--remove" ]] && { remove=1; shift; }
ctr="${1:?container}"; ifc="${2:?interface}"; rate="${3:-30mbit}"
pid=$(docker inspect -f '{{.State.Pid}}' "$ctr")
ns() { nsenter -t "$pid" -n "$@"; }
ns tc qdisc del dev "$ifc" root 2>/dev/null || true
if [[ $remove == 1 ]]; then echo "removed shaping on $ctr/$ifc"; exit 0; fi
ns tc qdisc add dev "$ifc" root handle 1: htb default 10
ns tc class add dev "$ifc" parent 1: classid 1:10 htb rate "$rate" ceil "$rate"
ns tc qdisc add dev "$ifc" parent 1:10 fq_codel
ns tc -s qdisc show dev "$ifc"
echo "shaping $ctr/$ifc at $rate — remember --remove"
