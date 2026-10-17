"""Unit tests: contracts, state separation, planner guard (eq. 24), payload, journal chain, stats."""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from nef.as_session_qos import PayloadError, build_subscription, flow_descriptions  # noqa: E402
from prenef.common import AuditJournal, verify_chain  # noqa: E402
from prenef.contracts import ContractError, adequacy, parse_contract  # noqa: E402
from prenef.graph_state import DependencyGraph, Registry, Subscription  # noqa: E402
from prenef.planner import (PlannerConfig, Prediction, Request, feasible, guarded_order,  # noqa: E402
                            plan, simulate)


def load(af):
    with open(os.path.join(ROOT, "config", "contracts", f"{af}.json")) as f:
        return json.load(f)


def reg():
    return Registry([parse_contract(load(a)) for a in ("af1", "af2", "af3", "af4")])


class ContractTests(unittest.TestCase):
    def test_parse_examples(self):
        c = parse_contract(load("af1"))
        self.assertEqual(c.fallback_modes("remote"), ["local"])
        self.assertTrue(c.allows_profile("remote", "qos-remote"))
        self.assertFalse(c.allows_profile("local", "qos-remote"))

    def test_unattested_consent_rejected(self):
        raw = load("af1")
        raw["consent"]["attested"] = False
        with self.assertRaises(ContractError):
            parse_contract(raw)

    def test_undeclared_profile_rejected(self):
        raw = load("af1")
        raw["modes"]["remote"]["qos_profiles"] = ["nope"]
        with self.assertRaises(ContractError):
            parse_contract(raw)

    def test_adequacy_unknown_is_not_adequate(self):
        c = parse_contract(load("af1"))
        a, why = adequacy(c, "remote", {"obs_wall_s": 100.0}, {}, 100.5)
        self.assertIsNone(a)
        a, _ = adequacy(c, "remote", {"obs_wall_s": 100.0, "latency_ms": 20, "loss_pct": 0}, {"sRSU": True}, 100.5)
        self.assertEqual(a, 1)
        a, why = adequacy(c, "remote", {"obs_wall_s": 100.0, "latency_ms": 20, "loss_pct": 0}, {"sRSU": False}, 100.5)
        self.assertEqual(a, 0)
        self.assertIn("dependency_down:sRSU", why)


class StateTests(unittest.TestCase):
    def test_recommend_does_not_confirm(self):           # eq. (7)
        r = reg()
        r.confirm_mode("af1", "remote", {"source": "af"})
        r.recommend("af1", "local")
        self.assertEqual(r.confirmed_mode["af1"], "remote")

    def test_only_af_confirms(self):                     # eq. (18)
        r = reg()
        with self.assertRaises(ValueError):
            r.confirm_mode("af1", "local", {"source": "prenef"})

    def test_allocation_needs_evidence(self):            # eq. (17)
        r = reg()
        r.plan_submission(Subscription("c1", "af1", "i1", "remote", "qos-remote", "1"))
        r.set_state("c1", "accepted")
        with self.assertRaises(ValueError):
            r.set_state("c1", "allocated")
        r.set_state("c1", "allocated", {"source": "nef_notification"})

    def test_one_active_submission_per_intent(self):     # eq. (16)
        r = reg()
        r.plan_submission(Subscription("c1", "af1", "i1", "remote", "qos-remote", "1"))
        with self.assertRaises(ValueError):
            r.plan_submission(Subscription("c2", "af1", "i1", "remote", "qos-remote", "1"))

    def test_graph_shared(self):
        r = reg()
        for a in ("af1", "af2", "af3"):
            r.confirm_mode(a, "remote", {"source": "af"})
        g = DependencyGraph(r)
        self.assertEqual(g.shared_count("af1"), 1)
        self.assertEqual(g.shared_count("af3"), 0)
        self.assertEqual(g.impacted_by("sRSU"), {"af1", "af2"})
        r.confirm_mode("af2", "local", {"source": "af"})
        self.assertEqual(g.impacted_by("sRSU"), {"af1"})


def req(i, af, t_last, svc=0.8, arrival=0.0):
    return Request(f"r{i}", af, f"i{i}", "remote", "qos-remote", arrival, t_last, svc)


class PlannerTests(unittest.TestCase):
    def test_guard_protects_urgent(self):
        # preference puts the urgent request last; guard must move it forward
        rs = [req(1, "af1", 10), req(2, "af2", 10), req(3, "af3", 10), req(4, "af4", 1.0)]
        order, ok = guarded_order(rs, 0.0, 1)
        self.assertTrue(ok)
        self.assertTrue(feasible(order, 0.0, 1))
        starts = {r.request_id: s for r, s, _ in simulate(order, 0.0, 1)}
        self.assertLessEqual(starts["r4"], 1.0)
        self.assertEqual(order[0].request_id, "r1")       # preference kept where possible

    def test_guard_declares_infeasible(self):
        rs = [req(1, "af1", 0.1), req(2, "af2", 0.1), req(3, "af3", 0.1)]
        _, ok = guarded_order(rs, 0.0, 1)
        self.assertFalse(ok)

    def test_overdue_first(self):                        # eq. (24)
        rs = [req(1, "af1", 50.0), req(2, "af2", 4.0)]
        order, _ = guarded_order(rs, 5.0, 1)
        self.assertEqual(order[0].request_id, "r2")

    def test_matches_exploratory_failure_case(self):
        # 4 serial requests of ~0.8 s, one with t_last = 1.0 s: EDF/guard meet it, FIFO may not
        rs = [req(1, "af1", 6), req(2, "af2", 6), req(3, "af3", 6), req(4, "af4", 1.0)]
        r = reg()
        for a in ("af1", "af2", "af3", "af4"):
            r.confirm_mode(a, "remote", {"source": "af"})
        dec, meta = plan(PlannerConfig(policy="prenef_noai"), r, rs, {}, 0.0)
        sub = [d for d in dec if d.kind == "submit"]
        self.assertTrue(all(d.justification["meets_t_last"] for d in sub))
        dec, _ = plan(PlannerConfig(policy="fifo"), r, rs, {}, 0.0)
        self.assertFalse(all(d.justification["meets_t_last"] for d in dec if d.kind == "submit"))

    def test_unqualified_prediction_abstains(self):     # eq. (19)
        r = reg()
        r.confirm_mode("af1", "remote", {"source": "af"})
        preds = {"af1": Prediction(0.9, 1.0, 0.1, qualified=False)}
        dec, _ = plan(PlannerConfig(policy="prenef_dtip"), r, [req(1, "af1", 9)], preds, 0.0)
        sub = [d for d in dec if d.kind == "submit"][0]
        self.assertFalse(sub.justification["score_terms"]["ai_used"])
        self.assertTrue(any(d.kind == "request_measurement" for d in dec))

    def test_alert_fanout_on_shared_dependency(self):
        r = reg()
        for a in ("af1", "af2", "af3"):
            r.confirm_mode(a, "remote", {"source": "af"})
        preds = {"af1": Prediction(0.9, 6.0, 0.1, qualified=True)}
        dec, _ = plan(PlannerConfig(policy="prenef_dtip"), r, [], preds, 0.0)
        notified = {d.af_id for d in dec if d.kind == "notify"}
        self.assertEqual(notified, {"af1", "af2"})          # af3 does not share sRSU
        self.assertTrue(all(d.recommended_mode == "local" for d in dec if d.kind == "notify"))

    def test_fanout_requires_degraded_service(self):
        r = reg()
        for a in ("af1", "af2"):
            r.confirm_mode(a, "remote", {"source": "af"})
        preds = {"af1": Prediction(0.9, 6.0, 0.1, qualified=True)}
        # af1's own path degrades, sRSU healthy -> only af1 is warned
        dec, _ = plan(PlannerConfig(policy="prenef_dtip"), r, [], preds, 0.0, degraded_services=set())
        self.assertEqual({d.af_id for d in dec if d.kind == "notify"}, {"af1"})
        # sRSU observed degraded -> fan-out to af2
        dec, _ = plan(PlannerConfig(policy="prenef_dtip"), r, [], preds, 0.0, degraded_services={"sRSU"})
        self.assertEqual({d.af_id for d in dec if d.kind == "notify"}, {"af1", "af2"})

    def test_late_alert_flagged(self):                   # eq. (12)
        r = reg()
        r.confirm_mode("af1", "remote", {"source": "af"})
        preds = {"af1": Prediction(0.9, 0.5, 0.1, qualified=True)}
        dec, _ = plan(PlannerConfig(policy="prenef_dtip"), r, [], preds, 0.0)
        self.assertTrue(any(d.kind == "notify_late" for d in dec))

    def test_independent_pred_has_no_fanout(self):
        r = reg()
        for a in ("af1", "af2"):
            r.confirm_mode(a, "remote", {"source": "af"})
        preds = {"af1": Prediction(0.9, 6.0, 0.1, qualified=True)}
        dec, meta = plan(PlannerConfig(policy="independent_pred"), r, [], preds, 0.0)
        self.assertEqual({d.af_id for d in dec if d.kind == "notify"}, {"af1"})
        self.assertEqual(meta["eta"], 0.0)

    def test_nofanout_ablation(self):
        r = reg()
        for a in ("af1", "af2"):
            r.confirm_mode(a, "remote", {"source": "af"})
        preds = {"af1": Prediction(0.9, 6.0, 0.1, qualified=True)}
        dec, _ = plan(PlannerConfig(policy="prenef_dtip", fanout=False), r, [], preds, 0.0)
        self.assertEqual({d.af_id for d in dec if d.kind == "notify"}, {"af1"})

    def test_nogate_ablation_uses_unqualified(self):
        r = reg()
        r.confirm_mode("af1", "remote", {"source": "af"})
        preds = {"af1": Prediction(0.9, 6.0, 0.9, qualified=False)}
        dec, _ = plan(PlannerConfig(policy="prenef_dtip", uncertainty_gate=False), r, [req(1, "af1", 9)], preds, 0.0)
        self.assertTrue(any(d.kind == "notify" for d in dec))

    def test_noguard_ablation_can_miss(self):
        r = reg()
        for a in ("af1", "af2", "af3", "af4"):
            r.confirm_mode(a, "remote", {"source": "af"})
        # af1/af2 share sRSU -> higher score; af4 urgent but low score
        rs = [req(1, "af1", 6), req(2, "af2", 6), req(3, "af3", 6), req(4, "af4", 1.0)]
        dec, meta = plan(PlannerConfig(policy="prenef_noai", guard=False), r, rs, {}, 0.0)
        self.assertFalse(all(d.justification["meets_t_last"] for d in dec if d.kind == "submit"))
        self.assertTrue(meta["feasible"])            # a feasible order existed: guard would have met it

    def test_static_priority_and_unbounded(self):
        r = reg()
        rs = [req(1, "af3", 9, arrival=0.0), req(2, "af1", 9, arrival=0.1)]
        dec, _ = plan(PlannerConfig(policy="static_priority"), r, rs, {}, 0.0)
        self.assertEqual([d.af_id for d in dec if d.kind == "submit"], ["af1", "af3"])
        dec, meta = plan(PlannerConfig(policy="oracle"), r, rs, {}, 0.0)
        self.assertEqual(meta["concurrency"], 2)

    def test_local_reject_unconsented(self):
        r = reg()
        bad = Request("x", "af1", "i", "local", "qos-remote", 0, 5, 0.5)
        dec, _ = plan(PlannerConfig(policy="edf"), r, [bad], {}, 0.0)
        self.assertEqual(dec[0].kind, "no_action")


class PayloadTests(unittest.TestCase):
    def test_build(self):
        b = build_subscription(load("af1"), "qos-remote", "10.60.0.1", "http://cb/notify",
                               events=["SUCCESSFUL_RESOURCES_ALLOCATION"])
        self.assertEqual(b["ueIpv4Addr"], "10.60.0.1")
        self.assertEqual(b["qosReference"], load("af1")["qos_profiles"]["qos-remote"]["qosReference"])
        self.assertEqual(len(b["flowInfo"][0]["flowDescriptions"]), 2)
        self.assertNotIn("ueIpv6Addr", b)

    def test_flow_desc_direction(self):
        dl = flow_descriptions("10.60.0.1", {"remote_ipv4": "10.1.1.1", "proto": "udp", "remote_port": 5201,
                                             "direction": "downlink"})
        self.assertEqual(dl, ["permit out 17 from 10.1.1.1 5201 to 10.60.0.1"])

    def test_bad_event(self):
        with self.assertRaises(PayloadError):
            build_subscription(load("af1"), "qos-remote", "10.60.0.1", "http://cb", events=["NOPE"])


class JournalTests(unittest.TestCase):
    def test_chain_detects_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "j.jsonl")
            j = AuditJournal(p)
            for k in range(5):
                j.append("x", n=k)
            self.assertTrue(verify_chain(p)[0])
            with open(p) as fh:
                lines = fh.read().splitlines()
            rec = json.loads(lines[2])
            rec["n"] = 99
            lines[2] = json.dumps(rec, sort_keys=True)
            with open(p, "w") as fh:
                fh.write("\n".join(lines) + "\n")
            self.assertFalse(verify_chain(p)[0])


class StatsTests(unittest.TestCase):
    def test_wilcoxon_and_holm(self):
        import numpy as np
        from bench.analyze import holm, wilcoxon
        self.assertLess(wilcoxon(np.arange(1, 13, dtype=float)), 0.001)
        self.assertGreater(wilcoxon(np.array([1, -1, 2, -2, 3, -3.0])), 0.5)
        h = holm({"a": 0.01, "b": 0.04, "c": 0.03})
        self.assertAlmostEqual(h["a"], 0.03)


if __name__ == "__main__":
    unittest.main()
