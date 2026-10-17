#!/usr/bin/env python3
"""NEF AsSessionWithQoS conformance suite (TS 29.122 resource model + notifications).

Runs against the real lab NEF or the mock. It CREATES and DELETES one
subscription, so against the lab it requires --approve-live-NEF-operation.
A `finally` block always attempts the DELETE of anything it created.

Each check is reported as pass / fail / warn with the clause it tests.
A 'fail' on C1, C2, C6 or C9 means the NEF image is not usable for the
benchmark as is; C8 'fail' means allocation can never be evidenced by
notification and you must rely on PFCP + data-plane evidence instead.

Example
  python3 nef/conformance.py --api-root http://10.101.200.14:8000 --scs-as-id af1 \
     --contract config/contracts/af1.json --ue-ip 10.60.0.1 \
     --notif-dest http://10.101.200.2:8080/notify/af1 \
     --notif-file /path/to/notifications.jsonl --approve-live-NEF-operation
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nef.as_session_qos import (ALLOC_NEGATIVE, ALLOC_POSITIVE, NefClient,  # noqa: E402
                                build_subscription)
from prenef.common import durable_json, read_json, read_jsonl  # noqa: E402


def wait_notification(path: str, transaction: str, since_wall: float, timeout_s: float) -> dict | None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if os.path.exists(path):
            for rec in read_jsonl(path):
                b = rec.get("body") or {}
                if rec.get("recv_wall_s", 0) >= since_wall and isinstance(b, dict) \
                        and b.get("transaction", "").rstrip("/") == transaction.rstrip("/"):
                    return rec
        time.sleep(0.2)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="NEF AsSessionWithQoS conformance")
    ap.add_argument("--api-root", required=True)
    ap.add_argument("--scs-as-id", required=True)
    ap.add_argument("--contract", required=True)
    ap.add_argument("--profile", default=None)
    ap.add_argument("--ue-ip", required=True, help="UE PDU-session IP (uesimtun0), NOT the container IP")
    ap.add_argument("--notif-dest", required=True)
    ap.add_argument("--notif-file", default=None, help="JSONL written by notification_server.py")
    ap.add_argument("--notif-timeout-s", type=float, default=10.0)
    ap.add_argument("--token", default=os.environ.get("NEF_TOKEN"))
    ap.add_argument("--transport", choices=["http1", "h2c"], default="http1")
    ap.add_argument("--events", default="SUCCESSFUL_RESOURCES_ALLOCATION,FAILED_RESOURCES_ALLOCATION,QOS_GUARANTEED,QOS_NOT_GUARANTEED,SESSION_TERMINATION")
    ap.add_argument("--no-events-field", action="store_true", help="omit 'events' if your NEF rejects it")
    ap.add_argument("--out", default="conformance-report.json")
    ap.add_argument("--approve-live-NEF-operation", action="store_true")
    ap.add_argument("--target-is-mock", action="store_true")
    a = ap.parse_args()
    if not (a.approve_live_NEF_operation or a.target_is_mock):
        print("refusing: this creates and deletes a NEF subscription. Pass "
              "--approve-live-NEF-operation (lab) or --target-is-mock.", file=sys.stderr)
        return 2

    raw = read_json(a.contract)
    profile = a.profile or next(iter(raw["qos_profiles"]))
    events = None if a.no_events_field else [e for e in a.events.split(",") if e]
    nef = NefClient(a.api_root, a.scs_as_id, token=a.token, transport=a.transport)
    body = build_subscription(raw, profile, a.ue_ip, a.notif_dest, events=events)
    checks: list[dict] = []

    def check(cid, ref, ok, detail, warn_only=False):
        checks.append({"id": cid, "ref": ref, "result": "pass" if ok else ("warn" if warn_only else "fail"),
                       "detail": detail})

    created: str | None = None
    try:
        t_wall = time.time()
        r = nef.create(body)
        loc = r.location
        ok =r.status == 201 and bool(loc) and "/3gpp-as-session-with-qos/v1/" in loc and "/subscriptions/" in loc
        check("C1", "TS 29.122 AsSessionWithQoS POST -> 201 Created + Location", ok,
              {"status": r.status, "location": loc, "latency_s": round(r.t_done_mono - r.t_send_mono, 4),
               "body": r.body if r.status >= 400 else None})
        if r.status == 201 and loc:
            created = loc
        if created:
            g = nef.get(created)
            check("C2", "GET individual subscription -> 200 with stored content",
                  g.status == 200 and isinstance(g.body, dict) and g.body.get("ueIpv4Addr") == a.ue_ip,
                  {"status": g.status})
            lst = nef.list()
            check("C3", "GET subscriptions collection -> 200 array", lst.status == 200 and isinstance(lst.body, list),
                  {"status": lst.status}, warn_only=True)
            alt = raw["qos_profiles"][profile].get("altQoSReferences")
            patch = {"altQoSReferences": alt} if alt else {"qosReference": body.get("qosReference")}
            p = nef.patch(created, patch)
            check("C4", "PATCH merge-patch+json -> 200/204", p.status in (200, 204), {"status": p.status})
            p2 = nef._req("PATCH", nef.resource(created), patch, "application/json")
            check("C5", "PATCH with wrong media type -> 415", p2.status == 415, {"status": p2.status}, warn_only=True)
            if a.notif_file:
                n = wait_notification(a.notif_file, created, t_wall - 1, a.notif_timeout_s)
                events_seen = [e.get("event") for e in ((n or {}).get("body") or {}).get("eventReports", [])]
                check("C8", "UserPlaneNotificationData correlated by 'transaction' == subscription URI",
                      n is not None, {"events": events_seen,
                                      "positive": bool(set(events_seen) & ALLOC_POSITIVE),
                                      "negative": bool(set(events_seen) & ALLOC_NEGATIVE),
                                      "delay_s": round(n["recv_wall_s"] - t_wall, 3) if n else None})
            else:
                check("C8", "notification check", False, "skipped: --notif-file not given", warn_only=True)
        bad = {k: v for k, v in body.items() if k != "ueIpv4Addr"}
        e = nef._req("POST", nef.collection, bad)
        is_pd = e.headers.get("content-type", "").startswith("application/problem+json")
        check("C6", "POST without UE address -> 400 ProblemDetails", e.status == 400,
              {"status": e.status, "problem+json": is_pd})
        if e.status == 201 and e.location:   # NEF accepted an invalid request: clean it up
            nef.delete(e.location)
        u = nef.get("does-not-exist-0000")
        check("C7", "GET unknown subscription -> 404", u.status == 404, {"status": u.status})
    finally:
        if created:
            d = nef.delete(created)
            check("C9", "DELETE -> 204 (or 200)", d.status in (200, 204), {"status": d.status})
            g2 = nef.get(created)
            check("C10", "GET after DELETE -> 404", g2.status == 404, {"status": g2.status})
    summary = {s: sum(c["result"] == s for c in checks) for s in ("pass", "fail", "warn")}
    report = {"target": a.api_root, "mock": a.target_is_mock, "scs_as_id": a.scs_as_id,
              "request_body": body, "checks": checks, "summary": summary,
              "note": "HTTP success here is NOT allocation evidence (eq. 5-6)."}
    durable_json(a.out, report)
    for c in checks:
        print(f"[{c['result'].upper():4}] {c['id']:3} {c['ref']}")
    print(json.dumps(summary))
    return 0 if summary["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
