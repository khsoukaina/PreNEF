#!/usr/bin/env bash
# usage: lab/run_qos_campaign.sh <campaign_dir> <n6_container> <bench/run_campaign.py run args...>
set -u
C=$1; N6=$2; shift 2
python3 lab/tput_logger.py --binding binding.json --server-container "$N6" --out "$C/tput.jsonl" \
  --proto udp --rate 1M --approve-live-traffic > "$C/tput.log" 2>&1 &
TP=$!
sleep 5
if ! kill -0 $TP 2>/dev/null; then echo "tput_logger failed:"; cat "$C/tput.log"; exit 1; fi
python3 bench/run_campaign.py run "$@"
RC=$?
kill $TP; wait $TP
echo "campaign finished, exit code $RC"
