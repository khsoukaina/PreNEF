#!/usr/bin/env python3
"""PReNEF runtime service — blocks A, B, C, D, E, F, G, H, I, J wired together.

AF-facing API (HTTP/1.1 JSON, per-AF bearer token, per-AF isolation, rate limit):
  POST   /v1/afs/{af}/observations          observation (block D)
  POST   /v1/afs/{af}/mode-confirmations    {"mode": m}            -> z_im (eq. 18)
  POST   /v1/afs/{af}/intents               {"intent_id","mode","profile","deadline_s"}
  GET    /v1/afs/{af}/intents/{intent_id}   state (planned/accepted/allocated/...)
  DELETE /v1/afs/{af}/intents/{intent_id}   revoke via NEF DELETE (block J)
  GET    /v1/afs/{af}/alerts                drain alerts/recommendations (block H)
NEF-facing:
  POST   /nef-notify/{af}                   notificationDestination (UserPlaneNotificationData)
  GET    /healthz

Outputs in --run-dir:
  journal.jsonl       hash-chained audit trail (block I) — verify with prenef/audit.py
  submissions.jsonl   one row per subscription (input of lab/evidence_collector.py)
  notifications.jsonl raw NEF notifications

Example
  python3 -m prenef.runtime --config config/runtime.json --policy prenef_dtip \
      --run-dir runs/b07-prenef_dtip --block 7 --approve-live-NEF-operation
"""
from __future__ import annotations

import os as _os
_os.environ.setdefault("OMP_NUM_THREADS", "1")   # single-row sklearn inference: threads only add latency

import argparse
import json
import os
import re
import signal
import sys
import threading
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nef.as_session_qos import (ALLOC_NEGATIVE, ALLOC_POSITIVE, NefClient,  # noqa: E402
                                build_subscription, classify_create)
from prenef.common import (AuditJournal, durable_json, new_correlation_id,  # noqa: E402
                           percentile, read_json)
from prenef.contracts import ContractError, adequacy, parse_contract  # noqa: E402
from prenef.graph_state import DependencyGraph, Registry, Subscription  # noqa: E402
from prenef.planner import AI_ALERT_POLICIES, POLICIES, UNBOUNDED, Decision, PlannerConfig, Request, l_adapt, plan  # noqa: E402

ROUTE = re.compile(r"^/v1/afs/([A-Za-z0-9_.-]+)/(observations|mode-confirmations|intents|alerts)(?:/([A-Za-z0-9_.-]+))?$")
NOTIF = re.compile(r"^/nef-notify/([A-Za-z0-9_.-]+)$")


class TokenBucket:
    def __init__(self, rate: float, burst: float):
        self.rate, self.burst, self.tokens, self.t = rate, burst, burst, time.monotonic()
        self.lock = threading.Lock()

    def take(self) -> bool:
        with self.lock:
            now = time.monotonic()
            self.tokens = min(self.burst, self.tokens + (now - self.t) * self.rate)
            self.t = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False


class PReNEF:
    def __init__(self, cfg: dict, policy: str, run_dir: str, block: int | None, live_ok: bool,
                 overrides: dict | None = None, oracle: tuple[str, float] | None = None):
        self.cfg = cfg
        self.run_dir = run_dir
        os.makedirs(run_dir, exist_ok=True)
        self.journal = AuditJournal(os.path.join(run_dir, "journal.jsonl"))
        contracts = []
        for p in cfg["contracts"]:
            c = parse_contract(read_json(p))
            if c.is_expired(time.time()):
                raise ContractError(f"{c.af_id}: contract expired")
            contracts.append(c)
        self.reg = Registry(contracts)
        self.graph = DependencyGraph(self.reg)
        self.binding = read_json(cfg["binding"])["afs"]
        self.tokens = cfg["af_tokens"]                      # {"af1": "secret"}
        self.buckets = {af: TokenBucket(cfg.get("rate_per_s", 50), cfg.get("burst", 100)) for af in self.tokens}
        pc = cfg.get("planner", {})
        self.pcfg = PlannerConfig(policy=policy, **{k: v for k, v in pc.items() if k != "policy"})
        for k, v in (overrides or {}).items():          # ablations: eta, uncertainty_gate, guard, fanout
            setattr(self.pcfg, k, v)
        self.nef_cfg = cfg["nef"]
        self.notif_base = cfg["notification_base_url"].rstrip("/")
        self.live_ok = live_ok
        self.lock = threading.RLock()
        self.obs: dict[str, deque] = defaultdict(lambda: deque(maxlen=2000))
        self.alerts: dict[str, list] = defaultdict(list)
        self.last_alert: dict[tuple, float] = {}
        self.intents: dict[tuple[str, str], dict] = {}     # (af, intent_id) -> intent
        self.by_location: dict[str, str] = {}               # location -> correlation_id
        self.sub_rows: dict[str, dict] = {}
        self.inflight = 0
        self.service_samples: deque = deque(maxlen=50)
        self.stop = threading.Event()
        self.predictor = None
        model_dir = cfg.get("independent_model_dir") if policy == "independent_pred" else cfg.get("model_dir")
        if policy not in AI_ALERT_POLICIES and not cfg.get("shadow_predictions", False):
            model_dir = None          # non-AI arms do not run the model (no hidden cost on their dispatch)
        self.latest_preds: dict = {}
        if model_dir:
            from dtip.predictor import OnlinePredictor
            self.predictor = OnlinePredictor(model_dir, cfg.get("p_horizon_s", 5.0))
            self.pcfg.u_max = float(self.predictor.model.u_max)
        self.oracle_plan = self._load_oracle(*oracle) if oracle else []
        self.last_pred: dict[str, tuple] = {}
        self.queue_delays: list[float] = []
        self.journal.append("run_start", run_id=os.path.basename(os.path.abspath(run_dir)), policy=policy,
                            block=block, planner=self.pcfg.__dict__,
                            contracts={c.af_id: c.version for c in contracts},
                            model_card=(self.predictor.card.get("model_sha256") if self.predictor else None),
                            model_qualified=(self.predictor.qualified if self.predictor else None),
                            model_dir=model_dir, oracle_alerts=len(self.oracle_plan))

    # ------------------------------------------------------------ block A
    def authorize(self, handler, af: str) -> str | None:
        if af not in self.reg.contracts:
            return "unknown_af"
        auth = handler.headers.get("Authorization", "")
        if auth != f"Bearer {self.tokens.get(af)}":
            return "forbidden"                 # an AF can only access its own namespace
        if not self.buckets[af].take():
            return "rate_limited"
        return None

    # ------------------------------------------------------------ block D
    def on_observation(self, af: str, o: dict) -> dict:
        o = dict(o)
        o.setdefault("obs_wall_s", time.time())
        o.setdefault("provenance", "af_measurement")
        with self.lock:
            self.obs[af].append(o)
            mode = self.reg.confirmed_mode.get(af)
        a = None
        if mode:
            a, why = adequacy(self.reg.contracts[af], mode, o,
                              {k: v.get("up") for k, v in (o.get("services") or {}).items()}, time.time())
        self.journal.append("observation", af_id=af, observation=o, confirmed_mode=mode, adequacy=a)
        if self.pcfg.policy in ("prenef_noai", "prenef_dtip") and self.pcfg.fanout and mode:
            self.shared_dependency_fanout(af, mode, o)
        return {"adequacy": a}

    def shared_dependency_fanout(self, af: str, mode: str, o: dict) -> None:
        """Non-AI semantic coordination (block C): an AF *observes* a declared
        dependency down -> warn every other AF whose confirmed mode depends on it.
        This is what prenef_noai adds over EDF; prenef_dtip adds anticipation."""
        down = [s for s, v in (o.get("services") or {}).items()
                if v.get("up") is False and s in self.reg.contracts[af].modes[mode].dependencies]
        for s in down:
            for other in sorted(self.graph.impacted_by(s) - {af}):
                c = self.reg.contracts[other]
                om = self.reg.confirmed_mode.get(other)
                if not om or not c.allows_action("alert"):
                    continue
                tg = c.fallback_modes(om)
                self.emit_alert(Decision("notify", other,
                                         recommended_mode=tg[0] if tg and c.allows_action("recommend_mode") else None,
                                         justification={"reason": "observed_shared_dependency_down",
                                                        "service": s, "shared_dependency_fanout": True}))

    def on_confirmation(self, af: str, body: dict) -> dict:
        mode = body.get("mode")
        with self.lock:
            prev = self.reg.confirmed_mode.get(af)
            self.reg.confirm_mode(af, mode, {"source": "af"})
        self.journal.append("mode_confirmed", af_id=af, mode=mode, previous=prev,
                            recommended=self.reg.recommended_mode.get(af), reason=body.get("reason"))
        return {"confirmed": mode}

    # ------------------------------------------------------------ intents
    def on_intent(self, af: str, body: dict) -> tuple[int, dict]:
        iid = str(body.get("intent_id", ""))
        mode, prof = body.get("mode"), body.get("profile")
        c = self.reg.contracts[af]
        if not iid or not c.allows_profile(mode, prof):
            return 400, {"status": 400, "cause": "profile_not_consented_for_mode"}
        now = time.monotonic()
        with self.lock:
            if (af, iid) in self.intents and self.intents[(af, iid)]["state"] not in ("rejected", "revoked", "released"):
                return 409, {"status": 409, "cause": "intent_active (eq. 16)"}
            cid = new_correlation_id()
            it = {"af_id": af, "intent_id": iid, "mode": mode, "profile": prof, "correlation_id": cid,
                  "arrival_mono": now, "t_last_mono": now + float(body.get("deadline_s", 5.0)),
                  "arrival_wall": time.time(), "state": "planned"}
            self.intents[(af, iid)] = it
            self.reg.plan_submission(Subscription(cid, af, iid, mode, prof, c.version))
        self.journal.append("intent", **{k: v for k, v in it.items()}, contract_version=c.version)
        return 202, {"correlation_id": cid, "state": "planned"}

    # ------------------------------------------------------------ block E
    def degraded_services(self) -> set:
        """Attribution for fan-out: a shared service is 'degraded' if a FRESH observation by any AF
        that depends on it reports it down, or its RTT above dep_degraded_ms (config, default 15 ms;
        the healthy sRSU RTT in the testbed is ~2 ms)."""
        thr = float(self.cfg.get("dep_degraded_ms", 15.0))
        max_age = float(self.cfg.get("dep_obs_max_age_s", 2.0))
        now = time.time()
        out = set()
        with self.lock:
            for af, dq in self.obs.items():
                if not dq:
                    continue
                o = dq[-1]
                if now - float(o.get("obs_wall_s", 0)) > max_age:
                    continue
                for svc, v in (o.get("services") or {}).items():
                    lat = v.get("latency_ms")
                    if v.get("up") is False or (lat is not None and lat >= thr):
                        out.add(svc)
        return out

    def predictions(self) -> dict:
        """Latest predictions, computed by pred_loop in its own thread so the
        dispatch tick never waits for the model. Stale ones are dropped (abstain)."""
        if not self.predictor:
            return {}
        max_age = 2.5 * self.cfg.get("pred_period_s", 0.5)
        now = time.time()
        with self.lock:
            return {af: p for af, (t, p) in self.latest_preds.items() if now - t <= max_age}

    def pred_loop(self) -> None:
        period = self.cfg.get("pred_period_s", 0.5)
        while not self.stop.is_set():
            t_start = time.time()
            try:
                with self.lock:
                    items = [(af, list(self.obs[af]), sorted(self.reg.contracts[af].modes[m].dependencies),
                              self.graph.shared_count(af))
                             for af, m in self.reg.confirmed_mode.items() if m is not None]
                    modes = dict(self.reg.confirmed_mode)
                res = self.predictor.predict_many(items, t_start)
                with self.lock:
                    for af, (p, _info) in res.items():
                        self.latest_preds[af] = (t_start, p)
                for af, (p, info) in res.items():
                    self.journal.append("prediction", af_id=af, mode=modes.get(af), p_inad=p.p_inad,
                                        t_safe_s=p.t_safe_s, u=p.u, qualified=p.qualified,
                                        l_pred_s=info["l_pred_s"], F=info["F"])
            except Exception as e:  # noqa: BLE001
                self.journal.append("prediction_error", error=str(e)[:300])
            time.sleep(max(0.0, period - (time.time() - t_start)))

    # ------------------------------------------------------------ block F + G
    def service_estimate(self) -> float:
        p = percentile(self.service_samples, 0.9)
        return p if p is not None else float(self.cfg.get("service_s_default", 0.9))

    def tick(self) -> None:
        preds = self.predictions()
        with self.lock:
            pending = [i for i in self.intents.values() if i["state"] == "planned"]
            svc = self.service_estimate()
            reqs = [Request(i["correlation_id"], i["af_id"], i["intent_id"], i["mode"], i["profile"],
                            i["arrival_mono"], i["t_last_mono"], svc) for i in pending]
        self.oracle_tick()
        if not reqs and self.pcfg.policy not in AI_ALERT_POLICIES:
            return
        decisions, meta = plan(self.pcfg, self.reg, reqs, preds, time.monotonic(),
                               degraded_services=self.degraded_services())
        conc = 10 ** 6 if self.pcfg.policy in UNBOUNDED else self.pcfg.concurrency
        launched = []
        for d in decisions:
            if d.kind == "submit":
                with self.lock:
                    if self.inflight >= conc:
                        break
                    it = next(i for i in pending if i["correlation_id"] == d.request_id)
                    it["state"] = "submitting"
                    self.inflight += 1
                launched.append(d.request_id)
                self.journal.append("plan_decision", decision=d.__dict__, meta=meta)
                threading.Thread(target=self.submit, args=(it, d.justification), daemon=True).start()
            elif d.kind in ("notify", "notify_late", "request_measurement"):
                self.emit_alert(d)
            elif d.kind == "no_action":
                self.journal.append("plan_decision", decision=d.__dict__, meta=meta)

    def submit(self, it: dict, just: dict) -> None:
        af, cid = it["af_id"], it["correlation_id"]
        c = self.reg.contracts[af]
        ue_ip = self.binding.get(af, {}).get("ue_ipv4")
        row = {"correlation_id": cid, "af_id": af, "intent_id": it["intent_id"], "profile": it["profile"],
               "ue_ipv4": ue_ip, "contract_version": c.version, "submit_wall_s": time.time(),
               "t_last_mono": it["t_last_mono"], "arrival_wall": it["arrival_wall"]}
        try:
            if not ue_ip:
                raise RuntimeError("no UE IP in binding (run lab/ue_binding.py)")
            body = build_subscription(c.raw, it["profile"], ue_ip, f"{self.notif_base}/nef-notify/{af}",
                                      events=self.nef_cfg.get("events"),
                                      supported_features=self.nef_cfg.get("supported_features"))
            nef = NefClient(self.nef_cfg["api_root"], c.scs_as_id, token=(self.nef_cfg.get("token") or os.environ.get("NEF_TOKEN")),
                            transport=self.nef_cfg.get("transport", "http1"),
                            timeout_s=self.nef_cfg.get("timeout_s", 10))
            post_mono = time.monotonic()
            self.reg.set_state(cid, "submitted")
            self.journal.append("submit", correlation_id=cid, af_id=af, intent_id=it["intent_id"],
                                profile=it["profile"], contract_version=c.version, body=body,
                                post_mono_s=post_mono, t_last_mono=it["t_last_mono"],
                                queue_delay_s=post_mono - it["arrival_mono"],
                                late_s=max(0.0, post_mono - it["t_last_mono"]), justification=just)
            res = nef.create(body)
            state, info = classify_create(res)
            dur = res.t_done_mono - res.t_send_mono
            with self.lock:
                self.service_samples.append(dur)
                it["state"] = state
                it["location"] = info.get("location")
                if info.get("location"):
                    self.by_location[info["location"].rstrip("/")] = cid
            self.reg.set_state(cid, state)
            row.update(status=res.status, location=info.get("location"), service_s=dur,
                       post_mono_s=post_mono, done_mono_s=res.t_done_mono)
            self.journal.append("nef_response", correlation_id=cid, af_id=af, status=res.status, state=state,
                                info=info, service_s=dur, headers_s=res.t_headers_mono - res.t_send_mono)
            self.alerts[af].append({"type": "intent_state", "intent_id": it["intent_id"], "state": state})
        except Exception as e:  # noqa: BLE001
            with self.lock:
                it["state"] = "rejected"
            row.update(status=0, error=str(e)[:300])
            self.journal.append("submit_error", correlation_id=cid, af_id=af, error=str(e)[:300])
        finally:
            with self.lock:
                self.inflight -= 1
                self.sub_rows[cid] = row
            self.flush_rows()

    def revoke(self, af: str, iid: str) -> tuple[int, dict]:
        with self.lock:
            it = self.intents.get((af, iid))
        if not it:
            return 404, {"status": 404}
        if not it.get("location"):
            with self.lock:
                it["state"] = "revoked"
            return 200, {"state": "revoked", "note": "never accepted by NEF"}
        c = self.reg.contracts[af]
        nef = NefClient(self.nef_cfg["api_root"], c.scs_as_id, token=(self.nef_cfg.get("token") or os.environ.get("NEF_TOKEN")),
                        transport=self.nef_cfg.get("transport", "http1"))
        t = time.time()
        self.reg.set_state(it["correlation_id"], "revoke_requested")
        r = nef.delete(it["location"])
        st = "revoked" if r.status in (200, 204) else "revoke_failed"
        with self.lock:
            it["state"] = st
            row = self.sub_rows.setdefault(it["correlation_id"], {})
            row.update(delete_wall_s=t, delete_status=r.status)
        if st == "revoked":
            self.reg.set_state(it["correlation_id"], "revoked")   # local only; NOT 'released'
        self.journal.append("revoke", correlation_id=it["correlation_id"], af_id=af, status=r.status, state=st,
                            note="DELETE success is not network release evidence (block J)")
        self.flush_rows()
        return 200, {"state": st}

    def flush_rows(self) -> None:
        with self.lock:   # serialise writers: concurrent submit threads share this file
            rows = list(self.sub_rows.values())
            tmp = os.path.join(self.run_dir, f"submissions.jsonl.tmp-{threading.get_ident()}")
            with open(tmp, "w") as f:
                for r in rows:
                    f.write(json.dumps(r, sort_keys=True) + "\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, os.path.join(self.run_dir, "submissions.jsonl"))

    # ------------------------------------------------------------ oracle arm
    def _load_oracle(self, scenario_path: str, t0_wall: float) -> list[dict]:
        """Upper-bound arm: alert each affected AF exactly L_adapt + guard before the
        ground-truth onset. Uses information PReNEF can never have; reference only."""
        scn = read_json(scenario_path)
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from lab.scenario import contract_onsets
        out = []
        for (ep, af), t in contract_onsets(scn, self.reg.contracts, self.cfg.get("base_rtt_ms", 3.0)).items():
            if t is None:
                continue
            c = self.reg.contracts[af]
            for m in c.modes:
                tg = c.fallback_modes(m)
                if tg and c.tau(m, tg[0]) is not None:
                    lead = (l_adapt(self.pcfg, c, m, tg[0]) or 0.0) + self.pcfg.guard_s
                    out.append({"af": af, "mode": m, "target": tg[0], "episode": ep,
                                "fire_wall": t0_wall + t - lead, "onset_wall": t0_wall + t})
        return sorted(out, key=lambda x: x["fire_wall"])

    def oracle_tick(self) -> None:
        if self.pcfg.policy != "oracle" or not self.oracle_plan:
            return
        now = time.time()
        while self.oracle_plan and self.oracle_plan[0]["fire_wall"] <= now:
            o = self.oracle_plan.pop(0)
            if self.reg.confirmed_mode.get(o["af"]) != o["mode"]:
                continue
            self.emit_alert(Decision("notify", o["af"], recommended_mode=o["target"],
                                     justification={"reason": "oracle_ground_truth", "episode": o["episode"],
                                                    "onset_wall": o["onset_wall"]}))

    # ------------------------------------------------------------ block H
    def emit_alert(self, d) -> None:
        key = (d.af_id, d.kind, d.recommended_mode)
        now = time.monotonic()
        if now - self.last_alert.get(key, -1e9) < self.cfg.get("alert_cooldown_s", 3.0):
            return
        self.last_alert[key] = now
        if d.recommended_mode:
            try:
                self.reg.recommend(d.af_id, d.recommended_mode)      # r_im, never z_im
            except ValueError:
                return
        just = dict(d.justification)
        if just.get("shared_dependency_fanout"):
            just.pop("trigger_af", None)          # do not leak another AF's identity (block H)
        msg = {"type": d.kind, "recommended_mode": d.recommended_mode, "issued_wall_s": time.time(),
               "issued_mono_s": now, "justification": just}
        with self.lock:
            self.alerts[d.af_id].append(msg)
        self.journal.append("alert", af_id=d.af_id, alert_kind=d.kind, recommended_mode=d.recommended_mode,
                            justification=d.justification)

    def on_nef_notification(self, af: str, body, peer: str) -> int:
        t = time.time()
        with open(os.path.join(self.run_dir, "notifications.jsonl"), "a") as f:
            f.write(json.dumps({"recv_wall_s": t, "af_path": af, "peer": peer, "body": body}) + "\n")
        if not isinstance(body, dict) or not isinstance(body.get("transaction"), str):
            self.journal.append("notification_invalid", af_path=af, peer=peer)
            return 400
        cid = self.by_location.get(body["transaction"].rstrip("/"))
        events = [r.get("event") for r in body.get("eventReports", []) if isinstance(r, dict)]
        self.journal.append("notification", correlation_id=cid, af_path=af, events=events, peer=peer)
        if cid:
            sub = self.reg.subs[cid]
            if sub.af_id != af:
                self.journal.append("notification_af_mismatch", correlation_id=cid, af_path=af)
                return 403
            ev = {"source": "nef_notification", "events": events, "recv_wall_s": t}
            if set(events) & ALLOC_POSITIVE:
                self.reg.set_state(cid, "allocated", ev)
            elif set(events) & ALLOC_NEGATIVE:
                self.reg.set_state(cid, "alloc_failed", ev)
            with self.lock:
                for it in self.intents.values():
                    if it["correlation_id"] == cid:
                        it["state"] = self.reg.subs[cid].state
                self.alerts[af].append({"type": "network_result", "intent_id": sub.intent_id,
                                        "events": events, "state": self.reg.subs[cid].state})
        return 204

    # ------------------------------------------------------------ lifecycle
    def loop(self) -> None:
        dt = self.cfg.get("tick_s", 0.05)
        while not self.stop.is_set():
            try:
                self.tick()
            except Exception as e:  # noqa: BLE001
                self.journal.append("tick_error", error=str(e)[:300])
            time.sleep(dt)

    def shutdown(self) -> None:
        self.stop.set()
        deadline = time.time() + 15
        while self.inflight and time.time() < deadline:
            time.sleep(0.1)
        for (af, iid), it in list(self.intents.items()):
            if it.get("location") and it["state"] in ("accepted", "allocated", "unverified", "alloc_failed"):
                self.revoke(af, iid)
        self.journal.append("run_end", intents=len(self.intents),
                            states={k: sum(1 for i in self.intents.values() if i["state"] == k)
                                    for k in {i["state"] for i in self.intents.values()}})
        durable_json(os.path.join(self.run_dir, "run_summary.json"),
                     {"intents": list(self.intents.values())})


def make_handler(p: PReNEF):
    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _json(self, status, body=None):
            data = json.dumps(body).encode() if body is not None else b""
            self.send_response(status)
            if body is not None:
                self.send_header("Content-Type", "application/json" if status < 400 else "application/problem+json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if data:
                self.wfile.write(data)

        def _body(self):
            n = int(self.headers.get("Content-Length", "0") or 0)
            try:
                return json.loads(self.rfile.read(n)) if n else {}
            except json.JSONDecodeError:
                return None

        def _route(self, method):
            m = NOTIF.match(self.path)
            if m and method == "POST":
                allowed = p.cfg.get("nef_peer_allowlist")
                if allowed and self.client_address[0] not in allowed:
                    return self._json(403, {"status": 403, "cause": "peer_not_allowed"})
                return self._json(p.on_nef_notification(m.group(1), self._body(), self.client_address[0]))
            if self.path == "/healthz":
                return self._json(200, {"status": "ok", "policy": p.pcfg.policy})
            m = ROUTE.match(self.path)
            if not m:
                return self._json(404, {"status": 404})
            af, res, rid = m.groups()
            err = p.authorize(self, af)
            if err:
                return self._json({"unknown_af": 404, "forbidden": 403, "rate_limited": 429}[err],
                                  {"status": 0, "cause": err})
            body = self._body() if method == "POST" else {}
            if body is None:
                return self._json(400, {"status": 400, "cause": "invalid_json"})
            try:
                if res == "observations" and method == "POST":
                    return self._json(200, p.on_observation(af, body))
                if res == "mode-confirmations" and method == "POST":
                    return self._json(200, p.on_confirmation(af, body))
                if res == "intents" and method == "POST" and rid is None:
                    return self._json(*p.on_intent(af, body))
                if res == "intents" and method == "GET" and rid:
                    it = p.intents.get((af, rid))
                    return self._json(200, {k: it[k] for k in ("intent_id", "state", "correlation_id")}) \
                        if it else self._json(404, {"status": 404})
                if res == "intents" and method == "DELETE" and rid:
                    return self._json(*p.revoke(af, rid))
                if res == "alerts" and method == "GET":
                    with p.lock:
                        out, p.alerts[af] = p.alerts[af], []
                    return self._json(200, out)
            except (ValueError, ContractError) as e:
                return self._json(400, {"status": 400, "cause": str(e)[:200]})
            return self._json(405, {"status": 405})

        def do_POST(self):
            self._route("POST")

        def do_GET(self):
            self._route("GET")

        def do_DELETE(self):
            self._route("DELETE")
    return H


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--policy", required=True, choices=list(POLICIES))
    ap.add_argument("--eta", type=float, default=None, help="ablation: 0 removes the shared-dependency term")
    ap.add_argument("--no-uncertainty-gate", action="store_true", help="ablation: ignore eq. (19)")
    ap.add_argument("--no-guard", action="store_true", help="ablation: ignore eq. (24)")
    ap.add_argument("--no-fanout", action="store_true", help="ablation: warn only the predicted AF")
    ap.add_argument("--p-alert", type=float, default=None, help="alert threshold on p_inad (sweep)")
    ap.add_argument("--oracle-scenario", default=None)
    ap.add_argument("--oracle-t0", type=float, default=None)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--block", type=int)
    ap.add_argument("--duration-s", type=float, default=0, help="0 = until SIGTERM")
    ap.add_argument("--approve-live-NEF-operation", action="store_true")
    ap.add_argument("--target-is-mock", action="store_true")
    a = ap.parse_args()
    if not (a.approve_live_NEF_operation or a.target_is_mock):
        print("refusing: PReNEF submits/deletes NEF subscriptions; pass --approve-live-NEF-operation "
              "(lab) or --target-is-mock", file=sys.stderr)
        return 2
    cfg = read_json(a.config)
    if a.policy == "prenef_dtip" and not cfg.get("model_dir"):
        print("prenef_dtip needs model_dir (a trained DTIP); use prenef_noai otherwise", file=sys.stderr)
        return 2
    if a.policy == "independent_pred" and not cfg.get("independent_model_dir"):
        print("independent_pred needs independent_model_dir (DTIP variant A_per_af)", file=sys.stderr)
        return 2
    if a.policy == "oracle" and not (a.oracle_scenario and a.oracle_t0):
        print("oracle needs --oracle-scenario and --oracle-t0", file=sys.stderr)
        return 2
    ov = {}
    if a.eta is not None:
        ov["eta"] = a.eta
    if a.no_uncertainty_gate:
        ov["uncertainty_gate"] = False
    if a.no_guard:
        ov["guard"] = False
    if a.no_fanout:
        ov["fanout"] = False
    if a.p_alert is not None:
        ov["p_alert"] = a.p_alert
    p = PReNEF(cfg, a.policy, a.run_dir, a.block, a.approve_live_NEF_operation, ov,
               (a.oracle_scenario, a.oracle_t0) if a.policy == "oracle" else None)
    srv = ThreadingHTTPServer((cfg.get("bind", "0.0.0.0"), int(cfg.get("port", 9090))), make_handler(p))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    threading.Thread(target=p.loop, daemon=True).start()
    if p.predictor:
        threading.Thread(target=p.pred_loop, daemon=True).start()
    done = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: done.set())
    signal.signal(signal.SIGINT, lambda *_: done.set())
    print(f"PReNEF [{a.policy}] on {cfg.get('bind', '0.0.0.0')}:{cfg.get('port', 9090)} -> {a.run_dir}", flush=True)
    done.wait(a.duration_s or None)
    p.shutdown()
    srv.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
