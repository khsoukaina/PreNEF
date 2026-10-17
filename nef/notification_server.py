#!/usr/bin/env python3
"""AF-side receiver for NEF notifications (notificationDestination).

Accepts UserPlaneNotificationData (TS 29.122):
  {"transaction": "<subscription resource URI>",
   "eventReports": [{"event": "SUCCESSFUL_RESOURCES_ALLOCATION", "flowIds": [1], ...}]}
and TestNotification (requestTestNotification / websocket test).

Every request is appended (fsync) to a JSONL file with wall and monotonic
receive time, then answered 204 No Content. Invalid bodies are still logged
(kind="invalid") and answered 400 with ProblemDetails, so nothing is lost.

Run inside the callback container's network namespace, e.g. replace the
existing qod-callback service command with:
  python3 notification_server.py --bind 0.0.0.0 --port 8080 --out /data/notifications.jsonl
Read-only for the network: it never calls the NEF.
"""
from __future__ import annotations

import argparse
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_LOCK = threading.Lock()
OUT_PATH = "notifications.jsonl"


def classify(body) -> tuple[str, list[str]]:
    errs: list[str] = []
    if not isinstance(body, dict):
        return "invalid", ["body is not a JSON object"]
    if "eventReports" in body or "transaction" in body:
        if not isinstance(body.get("transaction"), str):
            errs.append("transaction (Link) missing")
        reps = body.get("eventReports")
        if not isinstance(reps, list) or not reps:
            errs.append("eventReports must be a non-empty array")
        else:
            for r in reps:
                if not isinstance(r, dict) or "event" not in r:
                    errs.append("eventReport without event")
        return ("user_plane_notification" if not errs else "invalid"), errs
    if "subscription" in body:
        return "test_notification", []
    return "invalid", ["unknown notification type"]


def append(rec: dict) -> None:
    line = json.dumps(rec, sort_keys=True) + "\n"
    with _LOCK:
        with open(OUT_PATH, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # silence stderr access log
        pass

    def _reply(self, status: int, body: dict | None = None):
        data = json.dumps(body).encode() if body is not None else b""
        self.send_response(status)
        if body is not None:
            self.send_header("Content-Type", "application/problem+json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if data:
            self.wfile.write(data)

    def do_POST(self):
        t_wall, t_mono = time.time(), time.monotonic()
        n = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            body = None
        kind, errs = classify(body)
        append({
            "kind": kind, "errors": errs, "path": self.path,
            "recv_wall_s": t_wall, "recv_mono_s": t_mono,
            "peer": self.client_address[0],
            "content_type": self.headers.get("Content-Type"),
            "body": body if body is not None else raw.decode(errors="replace")[:4000],
        })
        if kind == "invalid":
            self._reply(400, {"status": 400, "title": "Bad Request", "detail": "; ".join(errs)})
        else:
            self._reply(204)

    do_PUT = do_POST

    def do_GET(self):  # health probe only
        self._reply(200, {"status": "ok"}) if self.path == "/healthz" else self._reply(404, {"status": 404})


def main() -> None:
    global OUT_PATH
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bind", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--out", default="notifications.jsonl")
    a = ap.parse_args()
    OUT_PATH = a.out
    os.makedirs(os.path.dirname(os.path.abspath(OUT_PATH)), exist_ok=True)
    srv = ThreadingHTTPServer((a.bind, a.port), Handler)
    print(f"listening on {a.bind}:{a.port} -> {OUT_PATH}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
