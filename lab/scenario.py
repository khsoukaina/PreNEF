#!/usr/bin/env python3
"""Correlated degradation scenarios: generation (offline) and injection (lab).

Why: in the exploratory campaigns the inadequacy rate was exactly 1/92 for every
policy, i.e. the scenario, not PReNEF, drove the outcome. A useful scenario must
  (a) be identical across arms of the same block (paired design, fixed seed),
  (b) contain SHARED-service degradations hitting several AFs (eq. 3),
  (c) contain precursors (ramps) so that prediction *can* give lead time,
  (d) contain ramps that recover (false alarms) so calibration is testable,
  (e) be logged as ground truth that PReNEF never reads at run time.

generate  -> scenario JSON (pure, deterministic from --seed)
inject    -> applies it with tc netem via nsenter (outage = 100 % egress loss, NOT docker pause),
             writes ground-truth JSONL, and always restores state on exit.
             Requires --approve-live-degradation and root.

Targets (config/scenario_targets.json):
{"services": {"sRSU": {"container": "prenef-srsu", "ifc": "eth0", "afs": ["af1","af2"]}},
 "ues": {"af1": {"container": "ueransim-ue-qod423", "ifc": "eth0"}, ...}}
"""
from __future__ import annotations

import argparse
import json
import os
import random
import signal
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prenef.common import durable_json, read_json  # noqa: E402


# ------------------------------------------------------------------ generate
def generate(seed: int, duration_s: float, targets: dict, n_episodes: int,
             ramp_steps: int = 5, step_s: float = 1.0, p_false_alarm: float = 0.3) -> dict:
    rng = random.Random(seed)
    services = list(targets.get("services", {}))
    ues = list(targets.get("ues", {}))
    events = []
    t = 5.0
    gap = max(14.0, (duration_s - 10) / max(1, n_episodes))
    for k in range(n_episodes):
        start = t + rng.uniform(0, gap * 0.4)
        # keep every episode (ramp + hold + clear, worst case) inside the run
        if start + ramp_steps * step_s + 8.5 > duration_s - 1.0:
            break
        kind = rng.choices(["shared", "ue"], weights=[0.6, 0.4])[0] if services and ues else (
            "shared" if services else "ue")
        target = rng.choice(services) if kind == "shared" else rng.choice(ues)
        recovers = rng.random() < p_false_alarm
        peak_delay = rng.choice([80, 120, 200])
        loss = rng.choice([0, 1, 3])
        # ramp: delay grows step by step -> learnable precursor
        for s in range(ramp_steps):
            events.append({"t": round(start + s * step_s, 3), "episode": k, "kind": kind, "target": target,
                           "action": "netem", "delay_ms": int(peak_delay * (s + 1) / ramp_steps),
                           "loss_pct": loss if s == ramp_steps - 1 else 0})
        t_peak = start + ramp_steps * step_s
        if recovers:
            events.append({"t": round(t_peak + 2.0, 3), "episode": k, "kind": kind, "target": target,
                           "action": "clear", "ground_truth": "false_alarm"})
        else:
            hold = rng.uniform(4.0, 8.0)
            if kind == "shared":
                events.append({"t": round(t_peak, 3), "episode": k, "kind": kind, "target": target,
                               "action": "outage", "ground_truth": "inadequacy_onset"})
                events.append({"t": round(t_peak + hold, 3), "episode": k, "kind": kind, "target": target,
                               "action": "restore"})
            else:
                events.append({"t": round(t_peak, 3), "episode": k, "kind": kind, "target": target,
                               "action": "netem", "delay_ms": peak_delay * 3, "loss_pct": 10,
                               "ground_truth": "inadequacy_onset"})
            events.append({"t": round(t_peak + hold + 0.5, 3), "episode": k, "kind": kind,
                           "target": target, "action": "clear"})
        t += gap
    events.sort(key=lambda e: (e["t"], e["episode"]))
    impacted = {s: targets["services"][s].get("afs", []) for s in services}
    return {"seed": seed, "duration_s": duration_s, "events": events, "service_afs": impacted,
            "note": "ground truth for evaluation only; never an input to PReNEF"}


# ------------------------------------------------------------------ contract onsets
def contract_onsets(scn: dict, contracts: dict, base_rtt_ms: float = 3.0) -> dict:
    """Per (episode, AF): offset t (s, scenario clock) of the FIRST injected state that
    violates that AF's declared requirements Q_i(primary) — the study's own definition of
    inadequacy (eq. 4) — instead of the injector's 'outage' label. None if never violated.
    contracts: {af_id: Contract}. Latency is RTT-based: base_rtt + injected netem delay."""
    by_ep: dict = {}
    for e in sorted(scn["events"], key=lambda e: (e["episode"], e["t"])):
        by_ep.setdefault(e["episode"], []).append(e)
    out = {}
    for ep, evs in by_ep.items():
        kind, target = evs[0]["kind"], evs[0]["target"]
        afs = scn.get("service_afs", {}).get(target, []) if kind == "shared" else [target]
        for af in afs:
            c = contracts.get(af)
            if c is None:
                continue
            prim = max(c.modes, key=lambda m: c.modes[m].utility)
            req = c.modes[prim].requirements
            delay = loss = 0.0
            down = False
            onset = None
            for e in evs:
                a = e["action"]
                if a == "netem":
                    delay, loss = float(e.get("delay_ms", 0)), float(e.get("loss_pct", 0))
                elif a == "clear":
                    delay = loss = 0.0
                    down = False
                elif a == "outage":
                    down = True
                elif a == "restore":
                    down = False
                if kind == "ue":
                    bad = (base_rtt_ms + delay > req.get("max_latency_ms", float("inf"))
                           or loss > req.get("max_loss_pct", float("inf")))
                else:   # shared service: only its declared availability is a requirement
                    bad = down and target in c.modes[prim].dependencies
                if bad:
                    onset = e["t"]
                    break
            out[(ep, af)] = onset
    return out


# ------------------------------------------------------------------ inject
class Injector:
    def __init__(self, targets: dict, gt_path: str, dry: bool):
        self.t = targets
        self.gt = gt_path
        self.dry = dry
        self.touched_netem: set[tuple[str, str]] = set()
        self.paused: set[str] = set()

    def _pid(self, ctr: str) -> str:
        return subprocess.check_output(["docker", "inspect", "-f", "{{.State.Pid}}", ctr], text=True).strip()

    def _run(self, cmd: list[str]) -> int:
        if self.dry:
            print("DRY", " ".join(cmd))
            return 0
        return subprocess.run(cmd, capture_output=True).returncode

    def _resolve(self, ev):
        if ev["kind"] == "shared":
            s = self.t["services"][ev["target"]]
            return s["container"], s.get("ifc", "eth0")
        u = self.t["ues"][ev["target"]]
        return u["container"], u.get("ifc", "eth0")

    def apply(self, ev: dict) -> None:
        ctr, ifc = self._resolve(ev)
        a = ev["action"]
        if a == "netem":
            pid = self._pid(ctr) if not self.dry else "PID"
            spec = ["delay", f"{ev['delay_ms']}ms"] + (["loss", f"{ev['loss_pct']}%"] if ev.get("loss_pct") else [])
            self._run(["nsenter", "-t", pid, "-n", "tc", "qdisc", "replace", "dev", ifc, "root", "netem", *spec])
            self.touched_netem.add((ctr, ifc))
        elif a == "clear":
            pid = self._pid(ctr) if not self.dry else "PID"
            self._run(["nsenter", "-t", pid, "-n", "tc", "qdisc", "del", "dev", ifc, "root"])
            self.touched_netem.discard((ctr, ifc))
            if ctr in self.paused:
                self._run(["docker", "unpause", ctr])
                self.paused.discard(ctr)
        elif a == "outage":
            # NOT `docker pause`: a frozen container's kernel still answers ICMP, so the outage was
            # invisible to the AFs. 100 % egress loss makes the service really unreachable.
            pid = self._pid(ctr) if not self.dry else "PID"
            self._run(["nsenter", "-t", pid, "-n", "tc", "qdisc", "replace", "dev", ifc, "root", "netem", "loss", "100%"])
            self.touched_netem.add((ctr, ifc))
        elif a == "restore":
            pid = self._pid(ctr) if not self.dry else "PID"
            self._run(["nsenter", "-t", pid, "-n", "tc", "qdisc", "del", "dev", ifc, "root"])
            self.touched_netem.discard((ctr, ifc))
            if ctr in self.paused:
                self._run(["docker", "unpause", ctr])
                self.paused.discard(ctr)
        rec = dict(ev, applied_wall_s=time.time(), applied_mono_s=time.monotonic(), container=ctr)
        with open(self.gt, "a") as f:
            f.write(json.dumps(rec) + "\n")

    def restore_all(self) -> None:
        for ctr in list(self.paused):
            self._run(["docker", "unpause", ctr])
        for ctr, ifc in list(self.touched_netem):
            try:
                pid = self._pid(ctr) if not self.dry else "PID"
                self._run(["nsenter", "-t", pid, "-n", "tc", "qdisc", "del", "dev", ifc, "root"])
            except Exception:  # noqa: BLE001
                pass
        self.paused.clear()
        self.touched_netem.clear()


def inject(scn: dict, targets: dict, gt_path: str, dry: bool, t0_mono: float | None = None) -> None:
    inj = Injector(targets, gt_path, dry)

    def stop(*_):
        inj.restore_all()
        sys.exit(130)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    start = t0_mono or time.monotonic()
    try:
        for ev in scn["events"]:
            delay = start + ev["t"] - time.monotonic()
            if delay > 0 and not dry:
                time.sleep(delay)
            inj.apply(ev)
    finally:
        inj.restore_all()


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--targets", required=True)
    g.add_argument("--seed", type=int, required=True)
    g.add_argument("--duration-s", type=float, default=120)
    g.add_argument("--episodes", type=int, default=6)
    g.add_argument("--false-alarm-prob", type=float, default=0.3)
    g.add_argument("--out", required=True)
    i = sub.add_parser("inject")
    i.add_argument("--targets", required=True)
    i.add_argument("--scenario", required=True)
    i.add_argument("--ground-truth", required=True)
    i.add_argument("--dry-run", action="store_true")
    i.add_argument("--approve-live-degradation", action="store_true")
    a = ap.parse_args()
    targets = read_json(a.targets)
    if a.cmd == "generate":
        durable_json(a.out, generate(a.seed, a.duration_s, targets, a.episodes, p_false_alarm=a.false_alarm_prob))
        print("wrote", a.out)
        return 0
    if not (a.dry_run or a.approve_live_degradation):
        print("refusing: pauses containers and applies netem; pass --approve-live-degradation", file=sys.stderr)
        return 2
    inject(read_json(a.scenario), targets, a.ground_truth, a.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
