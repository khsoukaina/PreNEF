#!/usr/bin/env python3
"""Paired statistical analysis of a campaign + figures + markdown report.

For each KPI and each planned comparison (A vs B), using only blocks where
both runs exist AND passed the audit:
  * mean paired difference (A - B), 95% percentile bootstrap CI (10 000 resamples)
  * Wilcoxon signed-rank test (exact for n <= 50 without ties, normal approx otherwise)
  * Holm correction across comparisons within each KPI
  * Cliff's-delta-like effect: P(A better than B) over pairs
Excluded runs (audit failed / missing) are listed in the report.

  python3 bench/analyze.py --campaign campaigns/c1 --out campaigns/c1/analysis
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prenef.common import durable_json, read_json  # noqa: E402

# KPI -> (direction: -1 lower is better, +1 higher is better, label). First = PRIMARY.
KPIS = {
    "exposure_s_per_episode": (-1, "Inadequate-mode exposure per episode (s) [PRIMARY]"),
    "exposure_s_per_episode_shared": (-1, "Exposure, shared-service episodes (s)"),
    "exposure_s_per_episode_ue": (-1, "Exposure, single-UE episodes (s)"),
    "timely_adaptation_rate": (+1, "Timely adaptation rate (eq. 26)"),
    "timely_adaptation_rate_shared": (+1, "Timely adaptation, shared episodes"),
    "timely_adaptation_rate_ue": (+1, "Timely adaptation, single-UE episodes"),
    "correlated_coverage_rate": (+1, "Correlated coverage (all affected AFs in time)"),
    "lead_s_median": (+1, "Median lead before onset (s)"),
    "unnecessary_transitions": (-1, "Unnecessary transitions (false alarms)"),
    "utility_loss_per_min": (-1, "Utility loss per minute (J2, eq. 21)"),
    "calibration_error": (-1, "Calibration error (eq. 27)"),
    "calibration_error_weighted": (-1, "Calibration error, sample-weighted ECE"),
    "abstention_rate": (-1, "Abstention rate (eq. 19)"),
    "nef_submission_rate_per_s": (-1, "NEF submission rate (eq. 28)"),
    "coordination_overhead_ms": (-1, "PReNEF coordination overhead (ms)"),
    "burst_deadline_miss_fraction": (-1, "Burst deadline miss fraction"),
    "allocated_fraction": (+1, "Evidenced allocation fraction (eq. 17, data plane)"),
    "cp_allocated_fraction": (+1, "Control-plane allocation fraction (PCF->SMF->PFCP)"),
    "mode_inadequacy_rate": (-1, "Tick-based inadequacy rate (sanity)"),
    "net_latency_ms_median": (-1, "Median network latency (sanity, not headline)"),
}
# (A, B): A is the candidate. Headline = prenef_dtip vs independent_pred.
COMPARISONS = [
    ("prenef_dtip", "independent_pred"),      # value of dependency-aware anticipation vs per-UE prediction
    ("prenef_dtip", "direct_nef"),            # total value vs 3GPP status quo
    ("prenef_dtip", "prenef_noai"),           # value of the AI
    ("prenef_noai", "direct_nef"),            # value of the graph without AI
    ("independent_pred", "direct_nef"),       # value of per-AF prediction alone
    ("prenef_dtip", "prenef_dtip_eta0"),      # ablations: what each component contributes
    ("prenef_dtip", "prenef_dtip_nogate"),
    ("prenef_dtip", "prenef_dtip_noguard"),
    ("prenef_dtip", "prenef_dtip_nofanout"),
    # oracle comparison removed
    ("edf", "fifo"), ("prenef_noai", "edf"), ("static_priority", "edf"),
]


def wilcoxon(d: np.ndarray) -> float:
    d = d[d != 0]
    n = len(d)
    if n == 0:
        return 1.0
    ranks = _rank(np.abs(d))
    w_plus = ranks[d > 0].sum()
    ties = len(np.unique(np.abs(d))) < n
    if n <= 50 and not ties:
        # exact distribution of W+ by DP over integer ranks
        maxs = n * (n + 1) // 2
        cnt = np.zeros(maxs + 1)
        cnt[0] = 1
        for r in range(1, n + 1):
            cnt[r:] = cnt[r:] + cnt[:-r].copy()
        cdf = np.cumsum(cnt) / cnt.sum()
        w = int(round(min(w_plus, maxs - w_plus)))
        return float(min(1.0, 2 * cdf[w]))
    mu = n * (n + 1) / 4
    _, c = np.unique(np.abs(d), return_counts=True)
    sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24 - (c ** 3 - c).sum() / 48)
    z = (abs(w_plus - mu) - 0.5) / sigma if sigma > 0 else 0
    return float(math.erfc(z / math.sqrt(2)))


def _rank(x):
    order = np.argsort(x)
    r = np.empty(len(x))
    r[order] = np.arange(1, len(x) + 1)
    for v in np.unique(x):
        m = x == v
        r[m] = r[m].mean()
    return r


def bootstrap_ci(d: np.ndarray, B: int = 10000, seed: int = 0):
    rng = np.random.default_rng(seed)
    if len(d) == 0:
        return (math.nan, math.nan)
    means = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def holm(pvals: dict) -> dict:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, prev = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        adj = min(1.0, max(prev, (m - i) * p))
        out[k], prev = adj, adj
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--include-failed-audit", action="store_true")
    ap.add_argument("--min-coverage", type=float, default=0.9,
                    help="exclude runs where an AF measured its path in fewer observations (testbed failure)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    data = defaultdict(dict)       # block -> arm -> metrics
    excluded = []
    for p in sorted(glob.glob(os.path.join(a.campaign, "b*-*/metrics.json"))):
        m = read_json(p)
        arm = os.path.basename(os.path.dirname(p)).split("-", 1)[1]
        if arm == "oracle":                  # oracle arm removed from the study
            continue
        if m.get("audit_ok") is False and not a.include_failed_audit:
            excluded.append({"run": os.path.dirname(p), "reason": "audit_failed"})
            continue
        cov = m.get("meas_coverage_min")
        if cov is not None and cov < a.min_coverage:
            excluded.append({"run": os.path.dirname(p),
                             "reason": f"measurement_loss (min RTT coverage {cov:.0%} < {a.min_coverage:.0%})"})
            continue
        data[m.get("block")][arm] = m
    arms = sorted({arm for b in data.values() for arm in b})
    results = []
    for kpi, (direction, label) in KPIS.items():
        pv = {}
        rows = []
        for A, B in COMPARISONS:
            if A not in arms or B not in arms:
                continue
            pairs = [(data[b][A].get(kpi), data[b][B].get(kpi)) for b in data if A in data[b] and B in data[b]]
            pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
            if len(pairs) < 3:
                continue
            d = np.array([x - y for x, y in pairs], dtype=float)
            lo, hi = bootstrap_ci(d)
            p = wilcoxon(d)
            better = np.mean([(x - y) * direction > 0 for x, y in pairs]) - np.mean([(x - y) * direction < 0 for x, y in pairs])
            rows.append({"kpi": kpi, "A": A, "B": B, "n_pairs": len(pairs), "mean_A": float(np.mean([x for x, _ in pairs])),
                         "mean_B": float(np.mean([y for _, y in pairs])), "mean_diff": float(d.mean()),
                         "ci95": [lo, hi], "p_wilcoxon": p, "dominance": float(better),
                         "direction": "lower_better" if direction < 0 else "higher_better"})
            pv[(A, B)] = p
        adj = holm(pv)
        for r in rows:
            r["p_holm"] = adj[(r["A"], r["B"])]
            r["significant_0.05"] = r["p_holm"] < 0.05
            r["favours"] = (r["A"] if r["mean_diff"] * KPIS[kpi][0] > 0 else r["B"]) if r["significant_0.05"] else "none"
        results += rows
    capture = []
    for b in data:   # share of the oracle's improvement over direct_nef that PReNEF captures
        if all(x in data[b] for x in ("direct_nef", "prenef_dtip", "oracle")):
            d0, d1, o = (data[b][x].get("exposure_s_per_episode") for x in ("direct_nef", "prenef_dtip", "oracle"))
            if None not in (d0, d1, o) and d0 - o > 1e-9:
                capture.append((d0 - d1) / (d0 - o))
    oracle_capture = {"n_blocks": len(capture), "mean": float(np.mean(capture)) if capture else None,
                      "ci95": list(bootstrap_ci(np.array(capture))) if len(capture) >= 3 else None}
    durable_json(os.path.join(a.out, "results.json"), {"oracle_capture_ratio": oracle_capture, "arms": arms, "blocks": sorted(k for k in data if k is not None),
                                                         "excluded": excluded, "comparisons": results})
    _figures(data, arms, a.out)
    _report(data, arms, results, excluded, a.out, oracle_capture)
    if not results:
        print("note: paired tests need >= 3 blocks with both arms present")
    print(f"{len(results)} comparisons; report -> {os.path.join(a.out, 'report.md')}")
    return 0


def _figures(data, arms, out):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    for kpi, (_, label) in KPIS.items():
        vals = {arm: [data[b][arm].get(kpi) for b in data if arm in data[b] and data[b][arm].get(kpi) is not None]
                for arm in arms}
        if not any(vals.values()):
            continue
        fig, ax = plt.subplots(figsize=(7, 3.6))
        for b in data:   # paired lines
            ys = [data[b][arm].get(kpi) if arm in data[b] else None for arm in arms]
            xs = [i for i, y in enumerate(ys) if y is not None]
            ax.plot(xs, [ys[i] for i in xs], color="0.8", lw=0.7, zorder=1)
        for i, arm in enumerate(arms):
            v = vals[arm]
            if v:
                ax.scatter([i] * len(v), v, s=14, color="0.35", zorder=2)
                ax.errorbar(i + 0.18, np.mean(v), yerr=1.96 * np.std(v, ddof=1) / math.sqrt(len(v)) if len(v) > 1 else 0,
                            fmt="o", color="C0", capsize=3, zorder=3)
        ax.set_xticks(range(len(arms)), arms, rotation=15)
        ax.set_ylabel(label)
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(os.path.join(out, f"{kpi}.png"), dpi=150)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 4))
    for i, arm in enumerate(arms):
        pts = [(x["tau_s"], x["lead_s"]) for b in data if arm in data[b]
               for x in data[b][arm].get("leads", []) if x.get("tau_s") is not None]
        if pts:
            jit = (i - len(arms) / 2) * 0.03
            ax.scatter([p[0] + jit for p in pts], [p[1] for p in pts], s=12, label=arm, alpha=0.7)
    ax.axhline(0, color="0.5", lw=0.8)
    ax.set_xlabel("declared transition time tau (s)")
    ax.set_ylabel("lead before onset (s)  [>0 = anticipated]")
    ax.spines[["top", "right"]].set_visible(False)
    if ax.has_data():
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(out, "lead_vs_tau.png"), dpi=150)
    plt.close(fig)


def _report(data, arms, results, excluded, out, oracle_capture=None):
    L = ["# Benchmark analysis", "", f"Blocks: {len(data)} — arms: {', '.join(arms)}", "",
         "Primary KPI: inadequate-mode exposure per episode (s). Headline comparison: "
         "prenef_dtip vs independent_pred.", ""]
    if oracle_capture and oracle_capture["mean"] is not None:
        L += [f"Oracle capture ratio (share of the achievable exposure reduction obtained by prenef_dtip): "
              f"{oracle_capture['mean']:.2f} over {oracle_capture['n_blocks']} blocks"
              + (f", 95% CI [{oracle_capture['ci95'][0]:.2f}, {oracle_capture['ci95'][1]:.2f}]"
                 if oracle_capture["ci95"] else ""), ""]
    if excluded:
        L += ["## Excluded runs", ""] + [f"- {e['run']} ({e['reason']})" for e in excluded] + [""]
    L += ["## Means per arm", "", "| KPI | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    for kpi, (_, label) in KPIS.items():
        cells = []
        for arm in arms:
            v = [data[b][arm].get(kpi) for b in data if arm in data[b] and data[b][arm].get(kpi) is not None]
            cells.append(f"{np.mean(v):.3f} (n={len(v)})" if v else "—")
        L.append(f"| {label} | " + " | ".join(cells) + " |")
    L += ["", "## Paired comparisons (A − B, Holm-adjusted Wilcoxon)", "",
          "| KPI | A vs B | n | mean diff | 95% CI | p (Holm) | favours |", "|---|---|---|---|---|---|---|"]
    for r in results:
        L.append(f"| {r['kpi']} | {r['A']} vs {r['B']} | {r['n_pairs']} | {r['mean_diff']:+.4f} | "
                 f"[{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}] | {r['p_holm']:.4f} | {r['favours']} |")
    L += ["", "Notes: HTTP 201 is not counted as allocation; `allocated_fraction` uses evidence (eq. 17). "
          "Mock-mode campaigns validate the pipeline only and are not network results."]
    with open(os.path.join(out, "report.md"), "w") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
