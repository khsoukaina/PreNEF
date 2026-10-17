#!/usr/bin/env python3
"""Offline mock of the NEF AsSessionWithQoS northbound API (TS 29.122 resource model).

SIMULATION ONLY — use it to test PReNEF, the conformance suite and the
evidence chain without touching the lab. Results obtained against this mock
must never be reported as network results.

Behaviour:
  * POST/GET/PATCH/PUT/DELETE with the 29.122 paths, Location header, ProblemDetails.
  * Mandatory IE validation (UE address, flowInfo, qos).
  * A semaphore of size --capacity and a service time --service-s emulate a
    contended NEF/PCF path (so serialisation vs. direct submission matters).
  * After --alloc-delay-s sends UserPlaneNotificationData to
    notificationDestination: SUCCESSFUL_RESOURCES_ALLOCATION, or
    FAILED_RESOURCES_ALLOCATION with probability --fail-prob.
  * On DELETE sends nothing and returns 204.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import threading
import time
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PATH = re.compile(r"^/3gpp-as-session-with-qos/v1/([^/]+)/subscriptions(?:/([^/]+))?/?$")
STORE: dict[tuple[str, str], dict] = {}
LOCK = threading.Lock()
CFG = argparse.Namespace(capacity=2, service_s=0.4, alloc_delay_s=0.3, fail_prob=0.0, seed=1, base="")
SEM = threading.Semaphore(2)
RNG = random.Random(1)


def problem(status: int, title: str, detail: str, cause: str | None = None) -> dict:
    p = {"status": status, "title": title, "detail": detail}
    if cause:
        p["cause"] = cause
    return p


def validate(body) -> str | None:
    if not isinstance(body, dict):
        return "body must be a JSON object"
    if "notificationDestination" not in body:
        return "notificationDestination missing"
    if sum(k in body for k in ("ueIpv4Addr", "ueIpv6Addr", "macAddr")) != 1:
        return "exactly one UE address required"
    if not any(k in body for k in ("flowInfo", "ethFlowInfo", "exterAppId")):
        return "flowInfo missing"
    if "qosReference" not in body and not any(k in body for k in ("maxbrDl", "gbrDl", "altQosReqs")):
        return "qosReference or QoS parameters missing"
    return None


def notify(dest: str, transaction: str, event: str, flow_ids: list[int]) -> None:
    data = json.dumps({"transaction": transaction,
                       "eventReports": [{"event": event, "flowIds": flow_ids}]}).encode()
    req = urllib.request.Request(dest, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=3).read()
    except Exception:
        pass


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, status: int, body=None, headers=None, ctype="application/json"):
        data = json.dumps(body).encode() if body is not None else b""
        self.send_response(status)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        if body is not None:
            self.send_header("Content-Type", "application/problem+json" if status >= 400 else ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if data:
            self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            return json.loads(raw) if raw else None
        except json.JSONDecodeError:
            return "__invalid__"

    def _route(self):
        m = PATH.match(self.path.split("?")[0])
        return (m.group(1), m.group(2)) if m else (None, None)

    def do_POST(self):
        scs, sub = self._route()
        if scs is None or sub is not None:
            return self._send(404, problem(404, "Not Found", "unknown resource"))
        body = self._body()
        err = validate(body) if body != "__invalid__" else "invalid JSON"
        if err:
            return self._send(400, problem(400, "Bad Request", err, "MANDATORY_IE_INCORRECT"))
        with SEM:                     # emulated NEF->PCF contention
            time.sleep(CFG.service_s)
            sid = uuid.uuid4().hex[:12]
            loc = f"{CFG.base}/3gpp-as-session-with-qos/v1/{scs}/subscriptions/{sid}"
            stored = dict(body, self=loc)
            with LOCK:
                STORE[(scs, sid)] = stored
        ev = "FAILED_RESOURCES_ALLOCATION" if RNG.random() < CFG.fail_prob else "SUCCESSFUL_RESOURCES_ALLOCATION"
        flow_ids = [f["flowId"] for f in body.get("flowInfo", [])]
        threading.Timer(CFG.alloc_delay_s, notify, (body["notificationDestination"], loc, ev, flow_ids)).start()
        self._send(201, stored, {"Location": loc})

    def do_GET(self):
        scs, sub = self._route()
        if scs is None:
            return self._send(404, problem(404, "Not Found", "unknown resource"))
        with LOCK:
            if sub is None:
                return self._send(200, [v for (s, _), v in STORE.items() if s == scs])
            v = STORE.get((scs, sub))
        return self._send(200, v) if v else self._send(404, problem(404, "Not Found", "no such subscription"))

    def do_PATCH(self):
        scs, sub = self._route()
        if self.headers.get("Content-Type", "").split(";")[0] != "application/merge-patch+json":
            return self._send(415, problem(415, "Unsupported Media Type", "use application/merge-patch+json"))
        body = self._body()
        with LOCK:
            v = STORE.get((scs, sub))
            if not v:
                return self._send(404, problem(404, "Not Found", "no such subscription"))
            if not isinstance(body, dict):
                return self._send(400, problem(400, "Bad Request", "patch must be an object"))
            for k, val in body.items():
                if val is None:
                    v.pop(k, None)
                else:
                    v[k] = val
        self._send(200, v)

    def do_PUT(self):
        scs, sub = self._route()
        body = self._body()
        err = validate(body) if body != "__invalid__" else "invalid JSON"
        with LOCK:
            if (scs, sub) not in STORE:
                return self._send(404, problem(404, "Not Found", "no such subscription"))
            if err:
                return self._send(400, problem(400, "Bad Request", err))
            STORE[(scs, sub)] = dict(body, self=STORE[(scs, sub)]["self"])
            v = STORE[(scs, sub)]
        self._send(200, v)

    def do_DELETE(self):
        scs, sub = self._route()
        with LOCK:
            v = STORE.pop((scs, sub), None)
        if not v:
            return self._send(404, problem(404, "Not Found", "no such subscription"))
        self._send(204)


def serve(host: str, port: int) -> ThreadingHTTPServer:
    CFG.base = f"http://{host}:{port}"
    srv = ThreadingHTTPServer((host, port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main():
    global SEM, RNG
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=18000)
    ap.add_argument("--capacity", type=int, default=2)
    ap.add_argument("--service-s", type=float, default=0.4)
    ap.add_argument("--alloc-delay-s", type=float, default=0.3)
    ap.add_argument("--fail-prob", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    for k in ("capacity", "service_s", "alloc_delay_s", "fail_prob", "seed"):
        setattr(CFG, k, getattr(a, k))
    SEM, RNG = threading.Semaphore(a.capacity), random.Random(a.seed)
    serve(a.host, a.port)
    print(f"MOCK NEF (simulation only) on http://{a.host}:{a.port}", flush=True)
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
