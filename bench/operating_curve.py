#!/usr/bin/env python3
"""Operating curves: benefit vs false-alarm cost when the alert threshold p_alert is swept.

  python3 bench/operating_curve.py --campaign campaigns/sweep

Expects arms named <method>_p<NN> (indep_p50, dtip_p70, ...) plus optionally direct_nef.
Writes <campaign>/paper/: figC_operating_curve (.pdf/.png), operating_curve.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bench.analyze import bootstrap_ci  # noqa: E402
from bench.paper_figures import COL2, INK2, save, setup  # noqa: E402

METHODS = {"indep": ("Per-AF predictor", "#eb6834", "s"),
           "dtip": ("PReNEF + DTIP (no fan-out)", "#2a78d6", "o"),
           "dtipfo": ("PReNEF + DTIP (with fan-out)", "#6250d6", "D")}
PANELS = [("exposure_s_per_episode_shared", "(a) Shared-service failures"),
          ("exposure_s_per_episode_ue", "(b) Single-UE failures")]
ARM_RE = re.compile(r"^(indep|dtip|dtipfo)_p(\d+)$")


def load(campaign):
    runs = defaultdict(list)
    for p in glob.glob(os.path.join(campaign, "b*-*", "metrics.json")):
        arm = os.path.basename(os.path.dirname(p)).split("-", 1)[1]
        m = json.load(open(p))
        if m.get("audit_ok") is False or (m.get("meas_coverage_min") or 1) < 0.9:
            continue
        runs[arm].append(m)
    return runs


def mci(vals):
    v = np.array([x for x in vals if x is not None], float)
    if len(v) == 0:
        return None
    lo, hi = bootstrap_ci(v) if len(v) >= 3 else (v.min(), v.max())
    return float(v.mean()), float(lo), float(hi), len(v)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(a.campaign, "paper")
    os.makedirs(out, exist_ok=True)
    runs = load(a.campaign)
    if not runs:
        print("no valid runs found")
        return 1
    plt = setup()
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.35), gridspec_kw={"wspace": 0.28})
    rows = []
    for ax, (key, title) in zip(axes, PANELS):
        ax.grid(axis="both", visible=True)
        if "direct_nef" in runs:
            x = mci([m.get("unnecessary_transitions") for m in runs["direct_nef"]])
            y = mci([m.get(key) for m in runs["direct_nef"]])
            if x and y:
                ax.errorbar(x[0], y[0], yerr=[[y[0] - y[1]], [y[2] - y[0]]], fmt="^", color="#eda100", ms=6,
                            mec="white", mew=0.6, elinewidth=1.0, label="Direct NEF (3GPP, no prediction)", zorder=4)
                rows.append([key, "direct_nef", "", *x[:3], *y[:3]])
        for meth, (label, col, mk) in METHODS.items():
            pts = []
            for arm, ms in runs.items():
                mm = ARM_RE.match(arm)
                if not mm or mm.group(1) != meth:
                    continue
                x = mci([m.get("unnecessary_transitions") for m in ms])
                y = mci([m.get(key) for m in ms])
                if x and y:
                    pts.append((int(mm.group(2)) / 100, x, y))
            if not pts:
                continue
            pts.sort(key=lambda t: t[0])
            ax.plot([p[1][0] for p in pts], [p[2][0] for p in pts], "-", color=col, lw=1.2, zorder=2)
            for thr, x, y in pts:
                ax.errorbar(x[0], y[0], xerr=[[x[0] - x[1]], [x[2] - x[0]]], yerr=[[y[0] - y[1]], [y[2] - y[0]]],
                            fmt=mk, color=col, ms=5, mec="white", mew=0.6, elinewidth=0.8, alpha=0.95, zorder=3)
                ax.annotate(f"{thr:.2f}", (x[0], y[0]), xytext=(4, 4), textcoords="offset points",
                            fontsize=5.8, color=col)
                rows.append([key, meth, thr, *x[:3], *y[:3]])
            ax.plot([], [], "-" + mk, color=col, ms=5, label=label)
        ax.set_title(title, loc="left", fontsize=7.5, fontweight="bold")
        ax.set_xlabel("Unnecessary fallbacks per run (cost) $\\rightarrow$")
        ax.set_ylim(bottom=0)
        ax.set_xlim(left=-0.2)
    axes[0].set_ylabel("Exposure per episode (s)\n$\\downarrow$ better")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.07), fontsize=6.8, handlelength=1.8)
    fig.text(0.5, -0.13, "Numbers next to points: alert threshold $p_{alert}$ (higher = fewer, later alerts)",
             ha="center", fontsize=6.2, color=INK2)
    save(fig, out, "figC_operating_curve")
    plt.close(fig)
    with open(os.path.join(out, "operating_curve.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["kpi", "method", "p_alert", "fallbacks_mean", "fb_lo", "fb_hi", "exposure_mean", "ex_lo", "ex_hi"])
        w.writerows(rows)
    for r in rows:
        print(f"  {r[0]:<32} {r[1]:<10} p={r[2]!s:<5} fallbacks={r[3]:.2f}  exposure={r[6]:.2f}s")
    print("wrote", out, ": figC_operating_curve.pdf/.png, operating_curve.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
