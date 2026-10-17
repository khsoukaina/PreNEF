#!/usr/bin/env python3
"""Emulated AF agent: measures, reports to PReNEF, owns its mode decisions.

The AF — never PReNEF — decides and confirms its mode (eq. 7, 18):
  * reactive safety (ALL arms): switch to the declared fallback after
    --k-inadequate consecutive inadequate observations of the current mode;
  * anticipation (only with --act-on-alerts, i.e. prenef_* arms): on a
    'notify' alert carrying a recommended mode, start the transition at once;
  * return to the primary mode after --r-adequate consecutive observations in
    which the PRIMARY mode would be adequate.
Transitions take tau(m, m') from the contract before being confirmed.
On entering the primary mode the AF asks PReNEF for its consented QoS
profile (intent); on leaving it revokes the intent.

Measurement sources
  --source ping       persistent `docker exec <ue> ping -I <tun>` to the N6 server
                      and to each declared shared service (lab)
  --source synthetic  derived from a scenario file + its clock (offline tests only)

Example (lab):
  python3 lab/af_agent.py --af af1 --contract config/contracts/af1.json \
     --binding binding.json --prenef http://127.0.0.1:9090 --token $AF1_TOKEN \
     --services sRSU=10.101.200.40 --server 10.101.200.30 --act-on-alerts --duration-s 120
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prenef.common import read_json  # noqa: E402
from prenef.contracts import adequacy, parse_contract  # noqa: E402

PING_RE = re.compile(r"icmp_seq=(\d+).*time=([\d.]+)\s*ms")


class PingStream:
    """Persistent ping; latency of last reply, loss from sequence gaps in a window."""

    def __init__(self, container: str, tun: str, target: str, interval: float, window_s: float = 3.0,
                 max_s: float = 600.0):
        self.samples: deque = deque()          # (wall, seq, rtt or None)
        self.window_s = window_s
        self.last_seq = 0
        self.lock = threading.Lock()
        # `timeout` runs INSIDE the container: killing the docker-exec client would not stop ping there
        cmd = ["docker", "exec", container, "timeout", str(int(max_s)), "ping", "-n", "-i", str(interval),
               "-W", "1", "-I", tun, target]
        self.cmd, self.interval, self.restarts, self.last_restart = cmd, interval, 0, 0.0
        self.started = time.time()
        self._spawn()

    def _spawn(self):
        self.proc = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.last_seq = 0
        threading.Thread(target=self._read, daemon=True).start()

    def watchdog(self):
        """ping exits if the tunnel disappears; restart it (at most every 2 s) so a transient
        tunnel loss is not turned into a whole run without measurements."""
        if self.proc.poll() is not None and time.time() - self.last_restart > 2.0:
            self.last_restart = time.time()
            self.restarts += 1
            self._spawn()

    def _read(self):
        for line in self.proc.stdout:
            m = PING_RE.search(line)
            if not m:
                continue
            seq, rtt = int(m.group(1)), float(m.group(2))
            now = time.time()
            with self.lock:
                for s in range(self.last_seq + 1, seq):
                    self.samples.append((now, s, None))
                self.last_seq = max(self.last_seq, seq)
                self.samples.append((now, seq, rtt))

    def snapshot(self) -> dict:
        self.watchdog()
        now = time.time()
        with self.lock:
            while self.samples and self.samples[0][0] < now - self.window_s:
                self.samples.popleft()
            s = list(self.samples)
        got = [r for _, _, r in s if r is not None]
        last_reply = max((w for w, _, r in s if r is not None), default=None)
        if now - self.started < self.window_s:
            # warm-up: the loss window is not filled yet -> loss/availability UNKNOWN, not 100 %
            # (otherwise every AF is declared inadequate in its first second and falls back)
            return {"latency_ms": got[-1] if got else None, "loss_pct": None,
                    "up": True if got else None, "restarts": self.restarts}
        expected = max(1, int(self.window_s / self.interval))
        up = last_reply is not None and now - last_reply < 1.5
        return {"latency_ms": got[-1] if got else None,
                "loss_pct": max(0.0, 100.0 * (1 - len(got) / expected)), "up": up, "restarts": self.restarts}

    def close(self):
        self.proc.terminate()


class Synthetic:
    """Offline source: replays scenario events against the agent's own clock."""

    def __init__(self, scenario: dict, af: str, services: list[str], t0: float):
        self.ev, self.af, self.services, self.t0 = scenario["events"], af, services, t0

    def _state(self, target):
        delay, loss, down = 0.0, 0.0, False
        now = time.time() - self.t0
        for e in self.ev:
            if e["t"] > now or e["target"] != target:
                continue
            if e["action"] == "netem":
                delay, loss = e["delay_ms"], e.get("loss_pct", 0)
            elif e["action"] == "clear":
                delay, loss, down = 0.0, 0.0, False
            elif e["action"] == "outage":
                down = True
            elif e["action"] == "restore":
                down = False
        return delay, loss, down

    def snapshot(self, target):
        d, l, down = self._state(target)
        return {"latency_ms": None if down else 20.0 + d, "loss_pct": 100.0 if down else l, "up": not down}


class Agent:
    def __init__(self, a):
        self.a = a
        self.c = parse_contract(read_json(a.contract))
        self.primary = a.primary_mode or max(self.c.modes, key=lambda m: self.c.modes[m].utility)
        self.mode = self.primary
        self.bad = 0
        self.good = 0
        self.transition_until = None
        self.target_mode = None
        self.intent_seq = 0
        self.active_intent = None
        self.services = dict(kv.split("=", 1) for kv in a.services.split(",") if kv)
        self.log = open(a.log, "a") if a.log else None
        if a.source == "ping":
            b = read_json(a.binding)["afs"][a.af]
            life = a.duration_s + max(0.0, (a.start_at or time.time()) - time.time()) + 30
            self.net = PingStream(b["container"], b.get("tun", "uesimtun0"), a.server, a.interval, max_s=life)
            self.svc = {s: PingStream(b["container"], b.get("tun", "uesimtun0"), ip, a.interval, max_s=life)
                        for s, ip in self.services.items()}
        else:
            self.syn = Synthetic(read_json(a.scenario), a.af, list(self.services), a.t0 or time.time())

    # ---------------------------------------------------------------- http
    def call(self, method, path, body=None):
        req = urllib.request.Request(self.a.prenef.rstrip("/") + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": f"Bearer {self.a.token}",
                                              "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                raw = r.read()
                return r.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            return e.code, None
        except Exception:  # noqa: BLE001
            return 0, None

    def record(self, kind, **kw):
        if self.log:
            self.log.write(json.dumps({"kind": kind, "wall_s": time.time(), "af_id": self.a.af, **kw}) + "\n")
            self.log.flush()

    # ---------------------------------------------------------------- logic
    def measure(self) -> dict:
        if self.a.source == "ping":
            n = self.net.snapshot()
            svcs = {s: self.svc[s].snapshot() for s in self.svc}
        else:
            n = self.syn.snapshot(self.a.af)
            svcs = {s: self.syn.snapshot(s) for s in self.services}
        return {"obs_wall_s": time.time(), "latency_ms": n["latency_ms"], "loss_pct": n["loss_pct"],
                "services": {s: {"up": v["up"], "latency_ms": v["latency_ms"]} for s, v in svcs.items()},
                "provenance": "af_measurement"}

    def confirm(self, mode, reason):
        prev = self.mode
        self.mode = mode
        st, _ = self.call("POST", f"/v1/afs/{self.a.af}/mode-confirmations", {"mode": mode, "reason": reason})
        self.record("mode_confirmed", mode=mode, previous=prev, reason=reason, status=st)
        if mode == self.primary and prev != self.primary:
            self.request_qos()
        if prev == self.primary and mode != self.primary and self.active_intent:
            self.call("DELETE", f"/v1/afs/{self.a.af}/intents/{self.active_intent}")
            self.record("intent_revoked", intent_id=self.active_intent)
            self.active_intent = None

    def request_qos(self, deadline_s=None):
        profs = self.c.modes[self.primary].qos_profiles
        if not profs or "submit_qos" not in self.c.actions:
            return
        self.intent_seq += 1
        iid = f"{self.a.af}-i{self.intent_seq}"
        st, body = self.call("POST", f"/v1/afs/{self.a.af}/intents",
                             {"intent_id": iid, "mode": self.primary, "profile": profs[0],
                              "deadline_s": deadline_s if deadline_s is not None else self.a.deadline_s})
        if st == 202:
            self.active_intent = iid
        self.record("intent", intent_id=iid, status=st)

    def start_transition(self, target, reason):
        tau = self.c.tau(self.mode, target)
        if tau is None or self.transition_until is not None:
            return
        self.target_mode, self.transition_until = target, time.time() + tau
        self.record("transition_start", frm=self.mode, to=target, tau_s=tau, reason=reason)

    def step(self):
        o = self.measure()
        self.call("POST", f"/v1/afs/{self.a.af}/observations", o)
        svc_up = {k: v["up"] for k, v in o["services"].items()}
        a_cur, why = adequacy(self.c, self.mode, o, svc_up, time.time())
        a_pri, _ = adequacy(self.c, self.primary, o, svc_up, time.time())
        self.record("observation", mode=self.mode, adequacy=a_cur, adequacy_primary=a_pri, reasons=why, obs=o)
        if self.transition_until and time.time() >= self.transition_until:
            tgt, self.transition_until, self.target_mode = self.target_mode, None, None
            self.confirm(tgt, "transition_complete")
        if self.transition_until:
            return
        if self.mode == self.primary:
            self.bad = self.bad + 1 if a_cur == 0 else 0
            if self.bad >= self.a.k_inadequate:
                fb = self.c.fallback_modes(self.mode)
                if fb:
                    self.start_transition(fb[0], "reactive")
                self.bad = 0
        else:
            self.good = self.good + 1 if a_pri == 1 else 0
            if self.good >= self.a.r_adequate:
                self.start_transition(self.primary, "recovered")
                self.good = 0
        if self.a.act_on_alerts:
            st, alerts = self.call("GET", f"/v1/afs/{self.a.af}/alerts")
            for al in alerts or []:
                self.record("alert_received", alert=al)
                if al.get("type") in ("notify", "notify_late") and al.get("recommended_mode") \
                        and self.mode == self.primary and al["recommended_mode"] in self.c.modes:
                    self.start_transition(al["recommended_mode"], "prenef_alert")

    def run(self):
        if self.a.start_at:
            time.sleep(max(0.0, self.a.start_at - time.time()))   # align with the scenario epoch
        self.confirm(self.mode, "initial")
        if self.a.burst_deadline_s is not None:
            # concurrency test: re-request at start with an explicit deadline
            if self.active_intent:
                self.call("DELETE", f"/v1/afs/{self.a.af}/intents/{self.active_intent}")
            self.request_qos(self.a.burst_deadline_s)
        end = time.time() + self.a.duration_s
        while time.time() < end:
            t = time.time()
            self.step()
            time.sleep(max(0.0, self.a.obs_period_s - (time.time() - t)))
        if self.active_intent:
            self.call("DELETE", f"/v1/afs/{self.a.af}/intents/{self.active_intent}")
        if self.a.source == "ping":
            for st in [self.net, *self.svc.values()]:
                st.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--af", required=True)
    ap.add_argument("--contract", required=True)
    ap.add_argument("--prenef", required=True)
    ap.add_argument("--token", required=True)
    ap.add_argument("--source", choices=["ping", "synthetic"], default="ping")
    ap.add_argument("--binding")
    ap.add_argument("--server", default="10.101.200.30")
    ap.add_argument("--services", default="", help="sRSU=10.101.200.40,...")
    ap.add_argument("--scenario")
    ap.add_argument("--t0", type=float, default=None, help="scenario epoch (shared by all agents)")
    ap.add_argument("--interval", type=float, default=0.2)
    ap.add_argument("--obs-period-s", type=float, default=0.5)
    ap.add_argument("--k-inadequate", type=int, default=2)
    ap.add_argument("--r-adequate", type=int, default=6)
    ap.add_argument("--primary-mode")
    ap.add_argument("--deadline-s", type=float, default=5.0)
    ap.add_argument("--burst-deadline-s", type=float, default=None)
    ap.add_argument("--act-on-alerts", action="store_true")
    ap.add_argument("--start-at", type=float, default=None, help="wall-clock epoch to start at")
    ap.add_argument("--duration-s", type=float, default=60)
    ap.add_argument("--log")
    a = ap.parse_args()
    Agent(a).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
