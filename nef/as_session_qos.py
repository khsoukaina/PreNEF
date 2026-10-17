"""Block G — NEF adapter for the AsSessionWithQoS API.

3GPP basis
  TS 23.502 §4.15.6.6 / §4.15.6.6a  AF session with required QoS procedure
  TS 29.122 §4.4.13 / §5.14          AsSessionWithQoS API (T8)  — resource model,
                                     AsSessionWithQoSSubscription, UserPlaneNotificationData
  TS 29.522                          N33 NEF northbound APIs (reuse 29.122 definitions)
  TS 29.514                          Npcf_PolicyAuthorization (what the NEF calls next)
  TS 29.214 §5.3.8                   Flow-Description (IPFilterRule, "permit out" only)

Resources
  POST   {apiRoot}/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions            -> 201 + Location
  GET    {apiRoot}/3gpp-as-session-with-qos/v1/{scsAsId}/subscriptions/{subId}    -> 200
  PATCH  .../{subId}   Content-Type: application/merge-patch+json                 -> 200 / 204
  PUT    .../{subId}                                                               -> 200 / 204
  DELETE .../{subId}                                                               -> 204 (or 200 + UserPlaneNotificationData)
Errors use application/problem+json (ProblemDetails).

IMPORTANT (eq. 5-6): a 201 means "subscription resource created". It is
neither an authorisation nor an allocation. The returned state is "accepted";
only evidence (evidence/collector.py) can move it to "allocated".

Transport: stdlib HTTP/1.1 by default. If your NEF northbound only speaks
h2c (prior knowledge), set transport="h2c" (needs `pip install httpx[http2]`).
"""
from __future__ import annotations

import ipaddress
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

API_NAME = "3gpp-as-session-with-qos"
API_VERSION = "v1"

USER_PLANE_EVENTS = {
    "SESSION_TERMINATION", "LOSS_OF_BEARER", "RECOVERY_OF_BEARER", "RELEASE_OF_BEARER",
    "USAGE_REPORT", "FAILED_RESOURCES_ALLOCATION", "QOS_GUARANTEED", "QOS_NOT_GUARANTEED",
    "QOS_MONITORING", "SUCCESSFUL_RESOURCES_ALLOCATION", "ACCESS_TYPE_CHANGE", "PLMN_CHG",
}
# Events that, correlated to a subscription, count as allocation evidence (eq. 17).
ALLOC_POSITIVE = {"SUCCESSFUL_RESOURCES_ALLOCATION", "QOS_GUARANTEED"}
ALLOC_NEGATIVE = {"FAILED_RESOURCES_ALLOCATION", "QOS_NOT_GUARANTEED"}
RELEASE_EVENTS = {"SESSION_TERMINATION", "RELEASE_OF_BEARER", "LOSS_OF_BEARER"}


class PayloadError(ValueError):
    pass


# --------------------------------------------------------------- flow descriptions
def flow_descriptions(ue_ip: str, flow: dict[str, Any]) -> list[str]:
    """IPFilterRule strings per TS 29.214 Flow-Description: action 'permit',
    direction always 'out'; downlink = from remote to UE, uplink = from UE to remote.
    Verify against what your PCF parses (free5gc PCF uses its own flowdesc parser)."""
    ipaddress.ip_address(ue_ip)
    remote = flow["remote_ipv4"]
    proto = {"udp": "17", "tcp": "6", "ip": "ip", None: "ip"}.get(flow.get("proto"), str(flow.get("proto")))
    rport = flow.get("remote_port")
    rp = f" {rport}" if rport and proto != "ip" else ""
    dl = f"permit out {proto} from {remote}{rp} to {ue_ip}"
    ul = f"permit out {proto} from {ue_ip} to {remote}{rp}"
    d = flow.get("direction", "bidirectional")
    return {"downlink": [dl], "uplink": [ul]}.get(d, [ul, dl])


def build_subscription(contract_raw: dict, profile_name: str, ue_ipv4: str,
                       notification_destination: str, *, events: list[str] | None = None,
                       supported_features: str | None = None,
                       request_test_notification: bool = False,
                       include_dnn_snssai: bool = True) -> dict:
    """AsSessionWithQoSSubscription (TS 29.122). Only consented content is used."""
    if not notification_destination.startswith(("http://", "https://")):
        raise PayloadError("notificationDestination must be an absolute URI")
    prof = contract_raw["qos_profiles"].get(profile_name)
    if prof is None:
        raise PayloadError(f"profile {profile_name} not declared in contract")
    body: dict[str, Any] = {
        "notificationDestination": notification_destination,
        "ueIpv4Addr": ue_ipv4,
        "flowInfo": [
            {"flowId": int(fl["flow_id"]), "flowDescriptions": flow_descriptions(ue_ipv4, fl)}
            for fl in contract_raw["flows"]
        ],
    }
    if "qosReference" in prof:
        body["qosReference"] = prof["qosReference"]
        if prof.get("altQoSReferences"):
            body["altQoSReferences"] = list(prof["altQoSReferences"])
    else:
        # Individual QoS parameters (Rel-17+). Keep only what the NEF supports.
        body.update(prof["qosParams"])
    ue = contract_raw.get("ue", {})
    if include_dnn_snssai:
        if ue.get("dnn"):
            body["dnn"] = ue["dnn"]
        if ue.get("snssai"):
            body["snssai"] = ue["snssai"]
    if events:
        bad = set(events) - USER_PLANE_EVENTS
        if bad:
            raise PayloadError(f"unknown UserPlaneEvent {sorted(bad)}")
        body["events"] = list(events)
    if supported_features:
        body["supportedFeatures"] = supported_features
    if request_test_notification:
        body["requestTestNotification"] = True
    validate_subscription(body)
    return body


def validate_subscription(body: dict) -> None:
    """Client-side check of the mandatory IEs before any network attempt."""
    if "notificationDestination" not in body:
        raise PayloadError("missing notificationDestination")
    if not any(k in body for k in ("ueIpv4Addr", "ueIpv6Addr", "macAddr")):
        raise PayloadError("exactly one of ueIpv4Addr/ueIpv6Addr/macAddr is required")
    if sum(k in body for k in ("ueIpv4Addr", "ueIpv6Addr", "macAddr")) != 1:
        raise PayloadError("only one UE address type may be present")
    if not any(k in body for k in ("flowInfo", "ethFlowInfo", "exterAppId")):
        raise PayloadError("flowInfo (or ethFlowInfo/exterAppId) is required")
    for fi in body.get("flowInfo", []):
        if not isinstance(fi.get("flowId"), int) or not fi.get("flowDescriptions"):
            raise PayloadError("flowInfo entries need integer flowId and flowDescriptions")
    if "qosReference" not in body and not any(k in body for k in ("altQosReqs", "maxbrUl", "gbrUl", "maxbrDl", "gbrDl")):
        raise PayloadError("qosReference or individual QoS parameters required")


# --------------------------------------------------------------- HTTP client
@dataclass
class HttpResult:
    status: int
    headers: dict[str, str]
    body: Any
    t_send_mono: float
    t_headers_mono: float
    t_done_mono: float

    @property
    def location(self) -> str | None:
        return self.headers.get("location")


class NefClient:
    def __init__(self, api_root: str, scs_as_id: str, *, token: str | None = None,
                 timeout_s: float = 10.0, transport: str = "http1"):
        self.api_root = api_root.rstrip("/")
        self.scs_as_id = scs_as_id
        self.token = token
        self.timeout_s = timeout_s
        self.transport = transport
        self._h2 = None
        if transport == "h2c":
            import httpx  # type: ignore
            self._h2 = httpx.Client(http1=False, http2=True, timeout=timeout_s)

    @property
    def collection(self) -> str:
        return f"{self.api_root}/{API_NAME}/{API_VERSION}/{self.scs_as_id}/subscriptions"

    def resource(self, sub_id_or_url: str) -> str:
        """Absolute Location URIs may carry the NEF's internal hostname (e.g.
        nef.free5gc.org) that the PReNEF host cannot resolve: keep the path,
        use our api_root. The original URI is still used for notification matching."""
        if sub_id_or_url.startswith(("http://", "https://")):
            u, base = urllib.parse.urlsplit(sub_id_or_url), urllib.parse.urlsplit(self.api_root)
            if u.netloc != base.netloc:
                return self.api_root + u.path + (f"?{u.query}" if u.query else "")
            return sub_id_or_url
        return f"{self.collection}/{sub_id_or_url}"

    def _req(self, method: str, url: str, body: Any = None,
             ctype: str = "application/json") -> HttpResult:
        headers = {"Accept": "application/json, application/problem+json"}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = ctype
        token = self.token
        tf = os.environ.get("NEF_TOKEN_FILE")       # refreshed by lab/token_keeper.py (short-lived tokens)
        if tf:
            try:
                with open(tf) as fh:
                    token = fh.read().strip() or token
            except OSError:
                pass
        if token:
            headers["Authorization"] = f"Bearer {token}"
        t0 = time.monotonic()
        if self._h2 is not None:
            r = self._h2.request(method, url, content=data, headers=headers)
            t1 = time.monotonic()
            raw = r.content
            status, hdrs = r.status_code, {k.lower(): v for k, v in r.headers.items()}
        else:
            req = urllib.request.Request(url, data=data, method=method, headers=headers)
            try:
                resp = urllib.request.urlopen(req, timeout=self.timeout_s)
            except urllib.error.HTTPError as e:
                resp = e
            t1 = time.monotonic()
            raw = resp.read()
            status = resp.status if hasattr(resp, "status") else resp.code
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
        t2 = time.monotonic()
        parsed: Any = None
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = raw.decode(errors="replace")[:2000]
        return HttpResult(status, hdrs, parsed, t0, t1, t2)

    # ---- operations
    def create(self, body: dict) -> HttpResult:
        validate_subscription(body)
        return self._req("POST", self.collection, body)

    def get(self, sub: str) -> HttpResult:
        return self._req("GET", self.resource(sub))

    def list(self) -> HttpResult:
        return self._req("GET", self.collection)

    def patch(self, sub: str, patch: dict) -> HttpResult:
        return self._req("PATCH", self.resource(sub), patch, "application/merge-patch+json")

    def put(self, sub: str, body: dict) -> HttpResult:
        validate_subscription(body)
        return self._req("PUT", self.resource(sub), body)

    def delete(self, sub: str) -> HttpResult:
        return self._req("DELETE", self.resource(sub))


def classify_create(res: HttpResult) -> tuple[str, dict]:
    """Map a create response to the registry state. Never returns 'allocated'."""
    if res.status == 201 and res.location:
        return "accepted", {"location": res.location}
    if res.status == 201:
        return "accepted", {"warning": "201 without Location header (TS 29.122 requires it)"}
    problem = res.body if isinstance(res.body, dict) else {"raw": res.body}
    return "rejected", {"status": res.status, "problem": problem}


def subscription_id_from_location(location: str) -> str:
    return location.rstrip("/").rsplit("/", 1)[-1]
