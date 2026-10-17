#!/usr/bin/env bash
# Follow a running campaign: refresh, keep a history, alert on failure, stop when finished.
#   lab/follow.sh                       -> campaigns/final3, every 300 s
#   lab/follow.sh campaigns/final3 120  -> every 120 s
cd "$(dirname "$0")/.." || exit 1
CAMP="${1:-campaigns/final3}"; EVERY="${2:-300}"; HIST="${CAMP}.follow.log"
[ -x .venv/bin/python3 ] && PY=.venv/bin/python3 || PY=python3
alert(){ printf '\a'; command -v notify-send >/dev/null && notify-send -u critical "PReNEF $CAMP" "$1"; }
last_fail=""
while true; do
  OUT=$(lab/status.sh "$CAMP" 2>&1)
  clear; echo "$OUT"
  echo "$OUT" | sed 's/\x1b\[[0-9;]*m//g' | sed "s/^/$(date '+%d %H:%M') /" >> "$HIST"
  FAILS=$(echo "$OUT" | sed 's/\x1b\[[0-9;]*m//g' | grep -E "FAIL|invalid " | tr '\n' ' ')
  if [ -n "$FAILS" ] && [ "$FAILS" != "$last_fail" ]; then alert "$FAILS"; fi
  last_fail="$FAILS"
  read -r DONE TOTAL < <($PY -c "
import json,glob
p=json.load(open('$CAMP/plan.json')); t=sum(len(b['arm_order']) for b in p['blocks'])
print(len(glob.glob('$CAMP/b*/metrics.json')), t)")
  if [ "$DONE" -ge "$TOTAL" ] && ! pgrep -f "run_campaign.py run --plan $CAMP/plan.json" >/dev/null; then
    echo; echo "== FINISHED: $DONE/$TOTAL runs. Next:"
    echo "   python3 bench/figures.py --campaign $CAMP --out $CAMP/figures"
    echo "   python3 bench/analyze.py --campaign $CAMP --out $CAMP/analysis"
    alert "finished: $DONE/$TOTAL runs"; break
  fi
  if ! pgrep -f "run_campaign.py run --plan $CAMP/plan.json" >/dev/null; then
    alert "campaign process STOPPED at $DONE/$TOTAL (check: tail $CAMP.log; resume with the same nohup command)"
  fi
  echo; echo "next refresh in ${EVERY}s (Ctrl+C to quit; history in $HIST)"
  sleep "$EVERY"
done
