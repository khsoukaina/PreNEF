#!/usr/bin/env python3
"""Allocation / release evidence chain per subscription — eq. (17) and block J.

Read-only. Sources, from strongest to weakest:
  N  NEF notification   UserPlaneNotificationData whose `transaction` equals the
                        subscription URI (Location). Positive: SUCCESSFUL_RESOURCES_ALLOCATION,
                        QOS_GUARANTEED. Negative: FAILED_RESOURCES_ALLOCATION, QOS_NOT_GUARANTEED.
  P  PFCP               Session Modification Request (type 52) carrying QER IEs for the SEID
                        of this UE's session, answered by type 53 with Cause = 1 (accepted),
                        inside [submit, submit + window]. Needs a pcap of N4 (port 8805).
  D  Data plane         dataplane_probe.py result for this AF showing the QoS effect.
  L  NF logs            PCF/SMF/UPF log lines matching configurable patterns in the window.
                        Temporal hint only — never sufficient on its own.

Default decision rule (configurable in config/evidence.json):
  allocated     <- N+   or  (P and D)
  alloc_failed  <- N-
  unverified    <- otherwise (accepted but unproven)
  released      <- DELETE 2xx and (release notification or PFCP QER removal / session
                   modification for that SEID after the DELETE)
  revoked       <- DELETE 2xx without release evidence (local only)

Inputs
  --submissions  JSONL: {"correlation_id","af_id","location","ue_ipv4",
                          "submit_wall_s","status","delete_wall_s","delete_status"}
                 (written by prenef/runtime.py; map your old journals with --map)
  --notifications JSONL from nef/notification_server.py
  --pcap          optional N4 capture
  --probes        optional JSONL from lab/dataplane_probe.py
  --logs-from-docker pcf-qod423,smf-qod423,upf-qod423   (docker logs -t, read-only)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nef.as_session_qos import ALLOC_NEGATIVE, ALLOC_POSITIVE, RELEASE_EVENTS  # noqa: E402
from prenef.common import durable_json, read_json, read_jsonl  # noqa: E402

DEFAULT_CFG = {
    "alloc_window_s": 15.0,
    "release_window_s": 15.0,
    "allocated_if_any_of": [["notification"], ["pfcp", "dataplane"]],
    "released_if_any_of": [["delete_ok", "release_notification"], ["delete_ok", "pfcp_after_delete"]],
    "log_patterns": {
        "pcf": [r"PolAuth\] Session Binding Success", r"PolAuth\] App Session Id\[.*\] (Create|Delete)", r"Send SM Policy Update Notification", "(?i)policyauthorization"],
        "smf": [r"Install PCCRule", r"Remove PCCRule", r"Sending PFCP Session Modification Request", r"Received PFCP Session Modification Response"],
        "upf": ["(?i)qer", "(?i)session modif"],
    },
    "tshark_fields": ["frame.time_epoch", "pfcp.msg_type", "pfcp.seid", "pfcp.ue_ip_addr_ipv4",
                      "pfcp.qer_id", "pfcp.cause", "pfcp.seqno"],
    "dataplane_min_ratio": 0.9,
}


# ------------------------------------------------------------------ sources
def load_notifications(path: str | None) -> dict[str, list[dict]]:
    by_tx: dict[str, list[dict]] = defaultdict(list)
    if not path or not os.path.exists(path):
        return by_tx
    for rec in read_jsonl(path):
        b = rec.get("body")
        if isinstance(b, dict) and isinstance(b.get("transaction"), str):
            by_tx[b["transaction"].rstrip("/")].append(rec)
    return by_tx


def parse_pfcp(pcap: str | None, fields: list[str]) -> tuple[list[dict], str | None]:
    if not pcap:
        return [], None
    if not shutil.which("tshark"):
        return [], "tshark not installed"
    cmd = ["tshark", "-r", pcap, "-Y", "pfcp", "-T", "fields", "-E", "separator=\t", "-E", "occurrence=a"]
    for f in fields:
        cmd += ["-e", f]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        return [], f"tshark failed (check field names with `tshark -G fields | grep pfcp`): {p.stderr[:300]}"
    msgs = []
    for line in p.stdout.splitlines():
        cols = line.split("\t")
        row = dict(zip(fields, cols))
        try:
            msgs.append({
                "t": float(row.get("frame.time_epoch") or 0),
                "type": int((row.get("pfcp.msg_type") or "0").split(",")[0]),
                "seid": (row.get("pfcp.seid") or "").split(",")[0],
                "ue_ip": (row.get("pfcp.ue_ip_addr_ipv4") or "").split(",")[0],
                "has_qer": bool(row.get("pfcp.qer_id")),
                "cause": (row.get("pfcp.cause") or "").split(",")[0],
                "seq": (row.get("pfcp.seqno") or "").split(",")[0],
            })
        except ValueError:
            continue
    return sorted(msgs, key=lambda m: m["t"]), None


def seid_for_ue(msgs: list[dict]) -> dict[str, set[str]]:
    """UE IP -> SEIDs, learned from Session Establishment Requests (type 50) and responses (51)."""
    out: dict[str, set[str]] = defaultdict(set)
    pending: dict[str, str] = {}
    for m in msgs:
        if m["type"] == 50 and m["ue_ip"]:
            pending[m["seq"]] = m["ue_ip"]
            if m["seid"]:
                out[m["ue_ip"]].add(m["seid"])
        elif m["type"] == 51 and m["seq"] in pending and m["seid"]:
            out[pending[m["seq"]]].add(m["seid"])
    return out


def pfcp_modifications(msgs, seids: set[str], ue_ip: str, t0: float, t1: float, require_qer: bool):
    reqs = [m for m in msgs if m["type"] == 52 and t0 <= m["t"] <= t1
            and ((m["seid"] in seids) or (ue_ip and m["ue_ip"] == ue_ip))
            and (m["has_qer"] or not require_qer)]
    ok = []
    for r in reqs:
        resp = next((m for m in msgs if m["type"] == 53 and m["seq"] == r["seq"] and m["t"] >= r["t"]), None)
        if resp and resp["cause"] in ("1", "Request accepted (success)"):
            ok.append({"req_t": r["t"], "resp_t": resp["t"], "seid": r["seid"], "has_qer": r["has_qer"]})
    return ok


def docker_logs(container: str, since: float, until: float, tail: int = 60000) -> list[tuple[float, str]]:
    """Last `tail` log lines, filtered to [since, until] in Python. `docker logs --since`
    scans the whole json log file from its start (minutes on long-running NFs);
    `--tail` reads from the end of the file and returns in seconds."""
    try:
        p = subprocess.run(["docker", "logs", "-t", "--tail", str(tail), container],
                           capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return []
    out = []
    for line in (p.stdout + p.stderr).splitlines():
        ts, _, msg = line.partition(" ")
        try:
            t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00")[:26] + "+00:00").timestamp()
        except ValueError:
            continue
        if since <= t <= until:
            out.append((t, msg))
    return out


def load_probes(path: str | None) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    if path and os.path.exists(path):
        for r in read_jsonl(path):
            out[r.get("af_id", "?")].append(r)
    return out


# ------------------------------------------------------------------ decision
def satisfied(rules: list[list[str]], have: set[str]) -> list[str] | None:
    for rule in rules:
        if set(rule) <= have:
            return rule
    return None


def evaluate(sub: dict, cfg: dict, notifs, msgs, ue_seids, probes, logs) -> dict:
    loc = (sub.get("location") or "").rstrip("/")
    t_sub = float(sub.get("submit_wall_s") or 0)
    t_del = sub.get("delete_wall_s")
    ev: dict = {"correlation_id": sub.get("correlation_id"), "af_id": sub.get("af_id"),
                "location": loc or None, "ue_ipv4": sub.get("ue_ipv4"), "sources": {}}
    have: set[str] = set()
    if not loc or int(sub.get("status") or 0) != 201:
        ev["state"] = "rejected" if sub.get("status") else "planned"
        return ev
    events = []
    for n in notifs.get(loc, []):
        for r in (n.get("body") or {}).get("eventReports", []):
            events.append({"event": r.get("event"), "recv_wall_s": n.get("recv_wall_s")})
    ev["sources"]["notifications"] = events
    names = {e["event"] for e in events}
    neg = names & ALLOC_NEGATIVE
    if names & ALLOC_POSITIVE:
        have.add("notification")
    seids = ue_seids.get(sub.get("ue_ipv4") or "", set())
    mods = pfcp_modifications(msgs, seids, sub.get("ue_ipv4") or "", t_sub, t_sub + cfg["alloc_window_s"], True)
    ev["sources"]["pfcp_modifications"] = mods
    if mods:
        have.add("pfcp")
    pr = [p for p in probes.get(sub.get("af_id"), []) if t_sub <= p.get("wall_s", 0) <= t_sub + 10 * cfg["alloc_window_s"]]
    ev["sources"]["dataplane"] = pr
    if any(p.get("verdict") == "qos_effect_observed" for p in pr):
        have.add("dataplane")
    ev["sources"]["log_hints"] = logs
    # control-plane chain (TS 23.502 4.15.6.6): PCF bound the app session to THIS UE's IP, the SMF
    # installed a PCC rule and the PFCP Session Modification was answered - all inside the window.
    # Reported separately as cp_state: it proves the policy reached the UPF, not a data-plane effect.
    ue = sub.get("ue_ipv4") or ""
    flat = [h for lines in (logs or {}).values() for h in lines]
    pcf_bind = any(f"UeIpv4[{ue}]" in h["line"] for h in flat) if ue else False
    smf_inst = any("Install PCCRule" in h["line"] for h in flat)
    pfcp_ok = bool(mods) or any("Received PFCP Session Modification Response" in h["line"] for h in flat)
    ev["cp_state"] = "cp_allocated" if (pcf_bind and smf_inst and pfcp_ok) else "cp_unverified"
    ev["cp_basis"] = {"pcf_session_binding_for_ue": pcf_bind, "smf_install_pccrule": smf_inst,
                      "pfcp_modification_ok": pfcp_ok}
    rule = satisfied(cfg["allocated_if_any_of"], have)
    if neg and not (names & ALLOC_POSITIVE):
        ev["state"], ev["basis"] = "alloc_failed", sorted(neg)
    elif rule:
        ev["state"], ev["basis"] = "allocated", rule
    else:
        ev["state"], ev["basis"] = "unverified", sorted(have) or ["http_201_only"]
    # ---- release
    if t_del:
        rel = set()
        if int(sub.get("delete_status") or 0) in (200, 204):
            rel.add("delete_ok")
        if any(e["event"] in RELEASE_EVENTS and (e["recv_wall_s"] or 0) >= float(t_del) for e in events):
            rel.add("release_notification")
        after = pfcp_modifications(msgs, seids, sub.get("ue_ipv4") or "", float(t_del),
                                   float(t_del) + cfg["release_window_s"], False)
        if after:
            rel.add("pfcp_after_delete")
        ev["sources"]["release"] = {"have": sorted(rel), "pfcp_after_delete": after}
        rrule = satisfied(cfg["released_if_any_of"], rel)
        if rrule:
            ev["release_state"], ev["release_basis"] = "released", rrule
        elif "delete_ok" in rel:
            ev["release_state"], ev["release_basis"] = "revoked", ["delete_ok_only (local, not network release)"]
        else:
            ev["release_state"] = "revoke_failed"
    return ev


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--submissions", required=True)
    ap.add_argument("--notifications")
    ap.add_argument("--pcap")
    ap.add_argument("--probes")
    ap.add_argument("--logs-from-docker", default="", help="comma list, e.g. pcf-qod423,smf-qod423,upf-qod423")
    ap.add_argument("--config")
    ap.add_argument("--out", default="evidence.json")
    a = ap.parse_args()
    cfg = dict(DEFAULT_CFG)
    if a.config:
        cfg.update(read_json(a.config))
    subs = list(read_jsonl(a.submissions))
    notifs = load_notifications(a.notifications)
    msgs, pfcp_err = parse_pfcp(a.pcap, cfg["tshark_fields"])
    ue_seids = seid_for_ue(msgs)
    probes = load_probes(a.probes)
    containers = [c for c in a.logs_from_docker.split(",") if c]
    results = []
    # read each NF log ONCE for the whole run window (docker logs scans the full log file
    # on every call, so per-submission calls get slow on long-running containers)
    times = [float(s["submit_wall_s"]) for s in subs if s.get("submit_wall_s")]
    logs = {}
    if times:
        for c in containers:
            role = next((r for r in cfg["log_patterns"] if r in c), None)
            pats = [re.compile(p) for p in cfg["log_patterns"].get(role, [])]
            logs[c] = [(t, l) for t, l in docker_logs(c, min(times) - 1.0, max(times) + cfg["alloc_window_s"])
                       if any(p.search(l) for p in pats)]
    for s in subs:
        t0 = float(s.get("submit_wall_s") or 0)
        hints = {c: [{"t": t, "line": l[:300]} for t, l in logs.get(c, [])
                     if t0 and t0 - 0.5 <= t <= t0 + cfg["alloc_window_s"]][:50] for c in containers}
        results.append(evaluate(s, cfg, notifs, msgs, ue_seids, probes, hints))
    summary = defaultdict(int)
    for r in results:
        summary[r["state"]] += 1
        if r.get("cp_state"):
            summary[r["cp_state"]] += 1
        if "release_state" in r:
            summary["release:" + r["release_state"]] += 1
    out = {"config": cfg, "pfcp_error": pfcp_err, "pfcp_messages": len(msgs),
           "summary": dict(summary), "subscriptions": results}
    durable_json(a.out, out)
    print(json.dumps(out["summary"], indent=1))
    if pfcp_err:
        print("PFCP:", pfcp_err)
    return 0


if __name__ == "__main__":
    sys.exit(main())
