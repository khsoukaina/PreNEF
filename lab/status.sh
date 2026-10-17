#!/usr/bin/env bash
# Read-only status of a running PReNEF campaign.
#   lab/status.sh                      -> campaigns/final2
#   lab/status.sh campaigns/collect2   -> another campaign
#   watch -n 300 lab/status.sh         -> refresh every 5 min (Ctrl+C to quit)
cd "$(dirname "$0")/.." || exit 1
CAMP="${1:-campaigns/final2}"; LOG="${CAMP}.log"
[ -x .venv/bin/python3 ] && PY=.venv/bin/python3 || PY=python3
G=$'\e[32m'; R=$'\e[31m'; Y=$'\e[33m'; B=$'\e[1m'; N=$'\e[0m'
ok(){ echo "  ${G}OK${N}   $*"; }; bad(){ echo "  ${R}FAIL${N} $*"; }; warn(){ echo "  ${Y}WARN${N} $*"; }

echo "${B}== PReNEF campaign status: $CAMP   ($(date '+%a %H:%M:%S'))${N}"

# 1. progress + ETA ---------------------------------------------------------------
$PY - "$CAMP" <<'PY'
import json, glob, os, sys, time
camp = sys.argv[1]
plan = json.load(open(f"{camp}/plan.json"))
total = sum(len(b["arm_order"]) for b in plan["blocks"])
done = sorted(glob.glob(f"{camp}/b*/metrics.json"), key=os.path.getmtime)
n = len(done)
print(f"  progress  {n}/{total} runs ({100*n/total:.0f} %)")
if n >= 2:
    t = [os.path.getmtime(f) for f in done]
    per = (t[-1] - t[0]) / (n - 1)
    eta = time.strftime("%H:%M", time.localtime(t[-1] + per * (total - n)))
    print(f"  pace      {per/60:.1f} min/run  ->  ETA ~{eta}  (last run finished {(time.time()-t[-1])/60:.0f} min ago)")
cur = [d for d in glob.glob(f"{camp}/b*-*") if not os.path.exists(f"{d}/metrics.json")]
if cur:
    print(f"  running   {os.path.basename(max(cur, key=os.path.getmtime))}")
# validity so far (same rule as analyze/figures: every AF >= 90 % measurement coverage, audit OK)
rows = [json.load(open(f)) for f in done]
bad = [(os.path.basename(os.path.dirname(f)), m.get("meas_coverage_min"), m.get("audit_ok"))
       for f, m in zip(done, rows)
       if (m.get("meas_coverage_min") is not None and m["meas_coverage_min"] < 0.9) or m.get("audit_ok") is False]
print(f"  valid     {n-len(bad)}/{n} finished runs")
for name, cov, aud in bad[-5:]:
    print(f"    \x1b[31minvalid\x1b[0m {name}: coverage={cov if cov is None else f'{cov:.0%}'} audit_ok={aud}")
# per-arm progress
arms = {}
for f in done:
    a = os.path.basename(os.path.dirname(f)).split("-", 1)[1]; arms[a] = arms.get(a, 0) + 1
print("  per arm   " + "  ".join(f"{a}={c}" for a, c in sorted(arms.items())))
PY

# 2. campaign process & log ---------------------------------------------------------
if pgrep -f "bench/run_campaign.py run --plan $CAMP/plan.json" >/dev/null; then ok "campaign process running"
else
  if grep -q "TESTBED UNHEALTHY" "$LOG" 2>/dev/null; then bad "campaign STOPPED: testbed unhealthy (repair UPF->SMF->gNB->UEs, then resume)"
  elif [ "$(ls $CAMP/b*/metrics.json 2>/dev/null | wc -l)" -gt 0 ]; then warn "campaign process not running (finished, or stopped -> resume with the same nohup command)"
  else bad "campaign process not running"; fi
fi
echo "  last log  $(tail -1 "$LOG" 2>/dev/null | cut -c1-140)"
grep -i -E "Traceback|Error|UNHEALTHY|refusing|not cached" "$LOG" 2>/dev/null | tail -3 | sed "s/^/  ${R}log${N}  /"

# 3. prerequisites ------------------------------------------------------------------
TOK=~/.prenef/nef_token
if [ -f "$TOK" ]; then
  AGE=$(( ($(date +%s) - $(stat -c %Y "$TOK")) / 60 ))
  [ "$AGE" -lt 16 ] && ok "NEF token refreshed ${AGE} min ago" || bad "NEF token is ${AGE} min old -> token keeper stopped? (python3 lab/token_keeper.py ...)"
else bad "no token file $TOK"; fi
pgrep -f "lab/token_keeper.py" >/dev/null && ok "token keeper running" || warn "token keeper process not found"
pgrep -f "sudo -n true" >/dev/null && ok "sudo keep-alive loop running" || warn "no sudo keep-alive loop found (it must run in the campaign terminal)"

# 4. testbed health (same check the campaign does before each run) -------------------
for u in ueransim-ue-qod423 ueransim-ue2-qod423 ueransim-ue3-qod423 ueransim-ue4-qod423; do
  IP=$(docker exec $u sh -c 'ip -4 -o addr show uesimtun0 2>/dev/null | awk "{print \$4}"' 2>/dev/null)
  LOSS=$(docker exec $u ping -c 2 -W 1 -I uesimtun0 10.101.200.30 2>/dev/null | grep -o "[0-9]*% packet loss")
  if [ -n "$IP" ] && [ "$LOSS" = "0% packet loss" ]; then ok "$u $IP $LOSS"
  else bad "$u ip=${IP:-none} ${LOSS:-no reply}"; fi
done
docker ps --filter name=prenef-srsu --format '{{.Status}}' | grep -q Paused && warn "prenef-srsu is paused (normal only during an outage episode)"
ERR=$(docker logs --since 30m ueransim-qod423 2>&1 | grep -c -i -E "not found|fail")
[ "$ERR" -eq 0 ] && ok "gNB: no errors in the last 30 min" || warn "gNB: $ERR error lines in the last 30 min (docker logs --since 30m ueransim-qod423)"
echo "  disk      $(df -h . | awk 'NR==2{print $4" free ("$5" used)"}')"
