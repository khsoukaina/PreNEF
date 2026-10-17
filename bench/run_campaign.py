#!/usr/bin/env python3
"""Paired, randomised benchmark campaign: plan -> run -> evidence -> audit -> metrics.

Design
  * Each BLOCK fixes one scenario seed and one deadline regime; ALL arms run that
    same scenario (paired design: compare arms within a block).
  * Arm order inside a block is a rotated + shuffled Latin square (balances drift
    and order effects; the order is recorded in plan.json).
  * Main ladder (default): direct_nef -> independent_pred -> prenef_noai -> prenef_dtip, + oracle.
    Ablations: prenef_dtip_eta0 / _nogate / _noguard / _nofanout.
    Ordering baselines (fifo, edf, static_priority) belong to bench/contention.py.
  * Every run is audited; failed audits are excluded AND listed.

Modes
  --mode mock  mock NEF + synthetic AF measurements: validates the whole pipeline
               offline. NOT a network result.
  --mode lab   real NEF, ping-based agents, scenario injector (root), optional N4
               capture. Needs --approve-live-NEF-operation --approve-live-degradation.

  python3 bench/run_campaign.py plan --blocks 20 --seed 7 --out campaigns/c1/plan.json
  python3 bench/run_campaign.py run  --plan campaigns/c1/plan.json --mode lab \
      --config config/runtime.lab.json --agents config/agents.lab.json \
      --targets config/scenario_targets.json --approve-live-NEF-operation --approve-live-degradation
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import signal
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from lab.scenario import generate  # noqa: E402
from prenef.common import durable_json, read_json  # noqa: E402

# arm -> (runtime policy, AF acts on alerts, extra runtime args)
ARMS = {
    "direct_nef": ("direct_nef", False, []),                       # 3GPP status quo, reactive AF
    "fifo": ("fifo", False, []),                                   # contention experiment
    "edf": ("edf", False, []),
    "static_priority": ("static_priority", False, []),
    "independent_pred": ("independent_pred", True, []),           # per-AF predictor, no graph
    "oracle": ("oracle", True, []),                               # ground-truth upper bound
    "prenef_noai": ("prenef_noai", True, []),
    "prenef_dtip": ("prenef_dtip", True, []),
    "prenef_dtip_eta0": ("prenef_dtip", True, ["--eta", "0"]),            # ablations
    "prenef_dtip_nogate": ("prenef_dtip", True, ["--no-uncertainty-gate"]),
    "prenef_dtip_noguard": ("prenef_dtip", True, ["--no-guard"]),
    "prenef_dtip_nofanout": ("prenef_dtip", True, ["--no-fanout"]),
    # threshold sweep (operating curves): same thresholds for both predictors
    **{f"indep_p{p}": ("independent_pred", True, ["--p-alert", f"0.{p}"]) for p in (35, 50, 70, 85)},
    **{f"dtip_p{p}": ("prenef_dtip", True, ["--no-fanout", "--p-alert", f"0.{p}"]) for p in (35, 50, 70, 85)},
    **{f"dtipfo_p{p}": ("prenef_dtip", True, ["--p-alert", f"0.{p}"]) for p in (35, 50, 70, 85)},
}
DEFAULT_ARMS = ["direct_nef", "independent_pred", "prenef_noai", "prenef_dtip"]
REGIMES = {"permissive": 6.0, "tight": 1.5}   # burst deadline_s per AF at block start
PY = sys.executable


def make_plan(blocks: int, seed: int, arms: list[str], duration_s: float, episodes: int) -> dict:
    rng = random.Random(seed)
    base = list(arms)
    rng.shuffle(base)
    out = []
    for b in range(1, blocks + 1):
        rot = b % len(base)
        order = base[rot:] + base[:rot]
        if b % 2 == 0:
            order = list(reversed(order))          # Williams-style balancing of carry-over
        out.append({"block": b, "scenario_seed": rng.randrange(1, 2**31),
                    "regime": "tight" if b % 2 else "permissive", "arm_order": order})
    return {"seed": seed, "arms": arms, "duration_s": duration_s, "episodes": episodes, "blocks": out}


def wait_http(url: str, timeout: float = 15.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            urllib.request.urlopen(url, timeout=1).read()
            return True
        except Exception:  # noqa: BLE001
            time.sleep(0.2)
    return False


def lab_health_check(runtime_cfg: dict, server: str) -> None:
    """Refuse to start a run on a broken testbed: every UE must still hold the tunnel IP
    recorded in binding.json (the NEF maps IP->SUPI) and reach the N6 server through it."""
    b = read_json(runtime_cfg["binding"])["afs"]
    problems = []
    for af, e in sorted(b.items()):
        ctr, tun, ip = e["container"], e.get("tun", "uesimtun0"), e.get("ue_ipv4")
        p = subprocess.run(["docker", "exec", ctr, "sh", "-c", f"ip -4 -o addr show {tun}"],
                           capture_output=True, text=True)
        if ip is None or f" {ip}/" not in p.stdout:
            problems.append(f"{af}: {tun} does not hold {ip} ({p.stdout.strip()[:60] or p.stderr.strip()[:60]})")
            continue
        q = subprocess.run(["docker", "exec", ctr, "ping", "-c", "2", "-W", "1", "-I", tun, server],
                           capture_output=True, text=True)
        if q.returncode != 0:
            problems.append(f"{af}: no reply from {server} through {tun}")
    if problems:
        raise SystemExit("TESTBED UNHEALTHY - campaign stopped before this run:\n  " + "\n  ".join(problems) +
                         "\nRepair (README: UPF -> SMF -> gNB -> UEs one by one), then re-run the same command.")


def run_one(a, plan, blk, arm, runtime_cfg, agents_cfg, targets, out_dir) -> str:
    policy, act, extra = ARMS[arm]
    if a.mode == "lab" and subprocess.run(["sudo", "-n", "true"], stdin=subprocess.DEVNULL).returncode != 0:
        raise SystemExit("sudo credentials not cached: run `sudo -v` (and keep the sudo keep-alive loop running)")
    run_dir = os.path.join(out_dir, f"b{blk['block']:02d}-{arm}")
    if os.path.exists(os.path.join(run_dir, "metrics.json")) and not a.force:
        print("skip (done):", run_dir)
        return run_dir
    if a.mode == "lab":
        lab_health_check(runtime_cfg, a.server)
    if os.path.exists(os.path.join(run_dir, "metrics.json")) and not a.force:
        print("skip (done):", run_dir)
        return run_dir
    shutil.rmtree(run_dir, ignore_errors=True)
    os.makedirs(run_dir)
    scn = generate(blk["scenario_seed"], plan["duration_s"], targets, plan["episodes"])
    durable_json(os.path.join(run_dir, "scenario.json"), scn)
    cfg = dict(runtime_cfg)
    cfg_path = os.path.join(run_dir, "runtime.json")
    durable_json(cfg_path, cfg)
    port = cfg.get("port", 9090)
    t0 = time.time() + a.startup_s          # common scenario epoch (agents, injector, oracle)
    rt_cmd = [PY, "-m", "prenef.runtime", "--config", cfg_path, "--policy", policy, "--run-dir", run_dir,
              "--block", str(blk["block"]), *extra]
    if policy == "oracle":
        rt_cmd += ["--oracle-scenario", os.path.join(run_dir, "scenario.json"), "--oracle-t0", str(t0)]
    rt_cmd += ["--target-is-mock"] if a.mode == "mock" else ["--approve-live-NEF-operation"]
    rt = subprocess.Popen(rt_cmd, cwd=ROOT, stdout=open(os.path.join(run_dir, "runtime.log"), "w"),
                          stderr=subprocess.STDOUT)
    procs = []
    try:
        if not wait_http(f"http://127.0.0.1:{port}/healthz"):
            raise RuntimeError("runtime did not start (see runtime.log)")
        pcap = os.path.join(run_dir, "n4.pcap")
        if a.mode == "lab" and a.capture_n4:
            subprocess.run(["sudo", "-n", os.path.join(ROOT, "lab/capture_n4.sh"), a.upf, pcap], check=False,
                           stdin=subprocess.DEVNULL, timeout=20)
        if time.time() > t0 - 0.5:
            raise RuntimeError("runtime start took longer than --startup-s; increase it")
        for af, ag in sorted(agents_cfg.items()):
            cmd = [PY, os.path.join(ROOT, "lab/af_agent.py"), "--af", af, "--contract", ag["contract"],
                   "--prenef", f"http://127.0.0.1:{port}", "--token", ag["token"],
                   "--services", ag.get("services", ""), "--duration-s", str(plan["duration_s"]),
                   "--burst-deadline-s", str(REGIMES[blk["regime"]]),
                   "--log", os.path.join(run_dir, f"agent-{af}.jsonl"),
                   "--obs-period-s", str(a.obs_period_s), "--start-at", str(t0)]
            if act:
                cmd.append("--act-on-alerts")
            if a.mode == "mock":
                cmd += ["--source", "synthetic", "--scenario", os.path.join(run_dir, "scenario.json"),
                        "--t0", str(t0)]
            else:
                cmd += ["--source", "ping", "--binding", runtime_cfg["binding"], "--server", ag.get("server", a.server)]
            procs.append(subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=open(
                os.path.join(run_dir, f"agent-{af}.err"), "w")))
        gt = os.path.join(run_dir, "ground_truth.jsonl")
        if a.mode == "lab":
            time.sleep(max(0, t0 - time.time()))
            procs.append(subprocess.Popen(["sudo", "-n", PY, os.path.join(ROOT, "lab/scenario.py"), "inject",
                                           "--targets", a.targets, "--scenario", os.path.join(run_dir, "scenario.json"),
                                           "--ground-truth", gt, "--approve-live-degradation"], cwd=ROOT))
        else:   # synthetic ground truth on the shared clock
            with open(gt, "w") as f:
                for e in scn["events"]:
                    f.write(json.dumps(dict(e, applied_wall_s=t0 + e["t"])) + "\n")
        for p in procs:
            p.wait(timeout=plan["duration_s"] + 60)
    finally:
        for p in procs:
            if p.poll() is None:
                p.send_signal(signal.SIGTERM)
        rt.send_signal(signal.SIGTERM)
        try:
            rt.wait(timeout=60)
        except subprocess.TimeoutExpired:
            rt.kill()
        if a.mode == "lab" and a.capture_n4:
            subprocess.run(["sudo", "-n", os.path.join(ROOT, "lab/capture_n4.sh"), "--stop", pcap], check=False,
                           stdin=subprocess.DEVNULL, timeout=20)
    ev_cmd = [PY, os.path.join(ROOT, "lab/evidence_collector.py"),
              "--submissions", os.path.join(run_dir, "submissions.jsonl"),
              "--notifications", os.path.join(run_dir, "notifications.jsonl"),
              "--out", os.path.join(run_dir, "evidence.json")]
    if os.path.exists(os.path.join(ROOT, "config/evidence.json")):
        ev_cmd += ["--config", os.path.join(ROOT, "config/evidence.json")]
    if a.mode == "lab":
        if a.capture_n4:
            ev_cmd += ["--pcap", os.path.join(run_dir, "n4.pcap")]
        ev_cmd += ["--logs-from-docker", a.nf_logs]
    if os.path.exists(os.path.join(run_dir, "submissions.jsonl")):
        subprocess.run(ev_cmd, cwd=ROOT, stdout=subprocess.DEVNULL)
    subprocess.run([PY, "-m", "prenef.audit", "--run-dir", run_dir, "--contracts",
                    *[ag["contract"] for ag in agents_cfg.values()]], cwd=ROOT, stdout=subprocess.DEVNULL)
    subprocess.run([PY, os.path.join(ROOT, "bench/metrics.py"), "--runs", run_dir,
                    "--out", os.path.join(run_dir, "metrics.line.jsonl")], cwd=ROOT, stdout=subprocess.DEVNULL)
    print("done:", run_dir)
    return run_dir


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--blocks", type=int, default=20)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--arms", default=",".join(DEFAULT_ARMS), help=f"any of: {','.join(ARMS)}")
    p.add_argument("--duration-s", type=float, default=120)
    p.add_argument("--episodes", type=int, default=6)
    p.add_argument("--out", required=True)
    r = sub.add_parser("run")
    r.add_argument("--plan", required=True)
    r.add_argument("--mode", choices=["mock", "lab"], required=True)
    r.add_argument("--config", required=True)
    r.add_argument("--agents", required=True)
    r.add_argument("--targets", required=True)
    r.add_argument("--server", default="10.101.200.30")
    r.add_argument("--upf", default="upf-qod423")
    r.add_argument("--nf-logs", default="pcf-qod423,smf-qod423,upf-qod423")
    r.add_argument("--capture-n4", action="store_true")
    r.add_argument("--obs-period-s", type=float, default=0.5)
    r.add_argument("--startup-s", type=float, default=6.0)
    r.add_argument("--blocks", default="", help="subset, e.g. 1-4")
    r.add_argument("--force", action="store_true")
    r.add_argument("--approve-live-NEF-operation", action="store_true")
    r.add_argument("--approve-live-degradation", action="store_true")
    a = ap.parse_args()
    if a.cmd == "plan":
        arms = [x for x in a.arms.split(",") if x]
        bad = set(arms) - set(ARMS)
        if bad:
            print("unknown arms", bad, file=sys.stderr)
            return 2
        durable_json(a.out, make_plan(a.blocks, a.seed, arms, a.duration_s, a.episodes))
        print("wrote", a.out)
        return 0
    if a.mode == "lab" and not (a.approve_live_NEF_operation and a.approve_live_degradation):
        print("refusing: lab campaign needs --approve-live-NEF-operation and --approve-live-degradation",
              file=sys.stderr)
        return 2
    plan = read_json(a.plan)
    runtime_cfg, agents_cfg, targets = read_json(a.config), read_json(a.agents), read_json(a.targets)
    if any(ARMS[x][0] == "prenef_dtip" for x in plan["arms"]) and not runtime_cfg.get("model_dir"):
        print("plan contains prenef_dtip arms but runtime config has no model_dir", file=sys.stderr)
        return 2
    if "independent_pred" in plan["arms"] and not runtime_cfg.get("independent_model_dir"):
        print("plan contains independent_pred but runtime config has no independent_model_dir", file=sys.stderr)
        return 2
    sel = None
    if a.blocks:
        lo, _, hi = a.blocks.partition("-")
        sel = range(int(lo), int(hi or lo) + 1)
    out_dir = os.path.dirname(os.path.abspath(a.plan))
    for blk in plan["blocks"]:
        if sel and blk["block"] not in sel:
            continue
        for arm in blk["arm_order"]:
            run_one(a, plan, blk, arm, runtime_cfg, agents_cfg, targets, out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
