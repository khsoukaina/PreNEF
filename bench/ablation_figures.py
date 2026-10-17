#!/usr/bin/env python3
"""Paper figures + LaTeX table for the PReNEF ablation campaign (same style as paper_figures.py).

  python3 bench/ablation_figures.py --campaign campaigns/ablation

Reads <campaign>/b<NN>-<arm>/metrics.json (bench/metrics.py output). Writes to <campaign>/paper/:
  figA_ablation_delta     effect of removing each component: (ablated - full), paired by block,
                          mean + 95% bootstrap CI, filled marker = Holm-adjusted p < 0.05  (double column)
  figB_ablation_tradeoff  benefit (exposure) vs cost (unnecessary fallbacks), one point per variant
                          with 95% CI in both directions                                  (single column)
  table_ablation.tex      booktabs: mean [CI] per variant + paired difference vs full and Holm p
  ablation_summary.csv    the numbers behind the figures
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bench.analyze import bootstrap_ci, holm, wilcoxon  # noqa: E402
from bench.paper_figures import COL1, COL2, GRID, INK, INK2, save, setup  # noqa: E402

FULL = "prenef_dtip"
# variant -> (label, what was removed, colour, marker). Validated palette slots 6-8 + slot 1 for FULL.
VARIANTS = [
    (FULL,                   "Full PReNEF + DTIP",       "nothing",                         "#2a78d6", "o"),
    ("prenef_dtip_eta0",     "w/o dependency priority",  "$\\eta = 0$ in eq. (23)",          "#008300", "P"),
    ("prenef_dtip_nogate",   "w/o uncertainty gate",     "eq. (19) disabled",               "#6250d6", "X"),
    ("prenef_dtip_nofanout", "w/o alert fan-out",        "shared-dependency fan-out off",   "#e34948", "h"),
]
LBL = {v: l for v, l, *_ in VARIANTS}
WHY = {v: w for v, _, w, *_ in VARIANTS}
COL = {v: c for v, _, _, c, _ in VARIANTS}
MRK = {v: m for v, *_, m in VARIANTS}
# (metric key, panel title, direction: +1 higher is better / -1 lower is better)
KPIS = [("exposure_s_per_episode", "(a) Exposure / episode (s)", -1),
        ("exposure_s_per_episode_shared", "(b) Exposure, shared episodes (s)", -1),
        ("unnecessary_transitions", "(c) Unnecessary fallbacks / run", -1),
        ("utility_loss_per_min", "(d) Utility loss (utility$\\cdot$s / min)", -1)]


def load(campaign):
    data = {}                                        # block -> variant -> metrics
    for p in sorted(glob.glob(os.path.join(campaign, "b*-*", "metrics.json"))):
        name = os.path.basename(os.path.dirname(p))
        arm = name.split("-", 1)[1]
        m = json.load(open(p))
        if m.get("audit_ok") is False or (m.get("meas_coverage_min") is not None and m["meas_coverage_min"] < 0.9):
            continue
        data.setdefault(int(name[1:3]), {})[arm] = m
    return data


def stats(data, key):
    out = {}
    for v, *_ in VARIANTS:
        vals = np.array([d[v][key] for d in data.values() if v in d and d[v].get(key) is not None], float)
        if len(vals):
            lo, hi = bootstrap_ci(vals) if len(vals) >= 3 else (vals.min(), vals.max())
            out[v] = (float(vals.mean()), float(lo), float(hi), len(vals))
    diffs, pv = {}, {}
    for v, *_ in VARIANTS[1:]:
        d = np.array([b[v][key] - b[FULL][key] for b in data.values()
                      if v in b and FULL in b and b[v].get(key) is not None and b[FULL].get(key) is not None], float)
        if len(d) >= 3:
            lo, hi = bootstrap_ci(d)
            diffs[v] = {"mean": float(d.mean()), "lo": float(lo), "hi": float(hi), "n": len(d)}
            pv[v] = wilcoxon(d)
    adj = holm(pv)
    for v in diffs:
        diffs[v]["p"] = adj[v]
    return out, diffs


def fig_delta(plt, data, out, rows):
    abl = [v for v, *_ in VARIANTS[1:]]
    fig, axes = plt.subplots(1, len(KPIS), figsize=(COL2, 1.7), sharey=True, gridspec_kw={"wspace": 0.14})
    for ax, (key, title, direction) in zip(axes, KPIS):
        _, diffs = stats(data, key)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", visible=True)
        span = max([abs(d[k]) for d in diffs.values() for k in ("lo", "hi")] + [1e-3]) * 1.25
        # shade the side where removing the component makes things WORSE
        worse = (0, span) if direction < 0 else (-span, 0)
        ax.axvspan(*worse, color="#fbeaea", lw=0, zorder=0)
        ax.axvline(0, color=INK, lw=0.7, zorder=1)
        for k, v in enumerate(abl):
            if v not in diffs:
                continue
            d, y = diffs[v], len(abl) - 1 - k
            sig = d["p"] < 0.05
            ax.plot([d["lo"], d["hi"]], [y, y], color=COL[v], lw=1.6, solid_capstyle="butt", zorder=2)
            ax.plot(d["mean"], y, MRK[v], color=COL[v], ms=5, mfc=COL[v] if sig else "white", mec=COL[v],
                    mew=1.0, zorder=3)
            ax.text(d["mean"], y + 0.28, ("$p<$0.001" if d["p"] < 0.001 else f"$p$={d['p']:.2f}"),
                    ha="center", va="bottom", fontsize=5.8, color=INK if sig else INK2)
            rows.append(["delta", key, v, d["mean"], d["lo"], d["hi"], d["n"], d["p"]])
        ax.set_xlim(-span, span)
        ax.set_title(title, loc="left", fontsize=7.2, pad=9)
        ax.text(0.0, 1.015, "shaded: removal makes it worse", transform=ax.transAxes, fontsize=5.8,
                color=INK2, va="bottom")
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.set_ylim(-0.6, len(abl) - 0.2)
    axes[0].set_yticks(range(len(abl)))
    axes[0].set_yticklabels([LBL[v] for v in reversed(abl)])
    fig.supxlabel("Paired difference: ablated variant $-$ full PReNEF + DTIP (mean, 95% CI; filled = Holm $p<0.05$)",
                  fontsize=7, y=-0.1)
    save(fig, out, "figA_ablation_delta")
    plt.close(fig)


def fig_tradeoff(plt, data, out, rows):
    sx, _ = stats(data, "unnecessary_transitions")
    sy, _ = stats(data, "exposure_s_per_episode")
    fig, ax = plt.subplots(figsize=(COL1, 2.3))
    ax.grid(axis="both", visible=True)
    for v, *_ in VARIANTS:
        if v not in sx or v not in sy:
            continue
        (mx, xlo, xhi, _), (my, ylo, yhi, _) = sx[v], sy[v]
        ax.errorbar(mx, my, xerr=[[mx - xlo], [xhi - mx]], yerr=[[my - ylo], [yhi - my]], fmt=MRK[v],
                    color=COL[v], ms=7 if v == FULL else 5.5, mec="white", mew=0.6, elinewidth=1.0,
                    capsize=0, zorder=4 if v == FULL else 3, alpha=1.0 if v == FULL else 0.9, label=LBL[v])
        rows.append(["tradeoff", "x=unnecessary_transitions", v, mx, xlo, xhi, None, None])
        rows.append(["tradeoff", "y=exposure_s_per_episode", v, my, ylo, yhi, None, None])
    ax.set_xlabel("Unnecessary fallbacks per run (cost) $\\rightarrow$")
    ax.set_ylabel("Exposure per episode (s)\n(benefit: lower is better)")
    ax.margins(x=0.15, y=0.2)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.28), ncol=2, handlelength=1.2, columnspacing=1.0)
    save(fig, out, "figB_ablation_tradeoff")
    plt.close(fig)


TABLE = [("exposure_s_per_episode", "Exposure / episode (s)", "{:.2f}"),
         ("exposure_s_per_episode_shared", "Exposure, shared episodes (s)", "{:.2f}"),
         ("timely_adaptation_rate_shared", "Timely adaptation, shared", "{:.2f}"),
         ("correlated_coverage_rate", "Correlated coverage", "{:.2f}"),
         ("unnecessary_transitions", "Unnecessary fallbacks / run", "{:.1f}"),
         ("utility_loss_per_min", "Utility loss (utility$\\cdot$s/min)", "{:.1f}"),
         ("calibration_error_weighted", "Online calibration (weighted ECE)", "{:.3f}"),
         ("abstention_rate", "Abstention rate (eq.~19)", "{:.2f}")]


def table(data, out, rows):
    vs = [v for v, *_ in VARIANTS]
    n = len(data)
    L = ["% requires \\usepackage{booktabs}", "\\begin{table*}[t]", "\\centering", "\\small",
         f"\\caption{{Ablation over {n} paired blocks: mean [95\\% bootstrap CI]; $\\Delta$ = ablated $-$ full, "
         "with Holm-adjusted Wilcoxon $p$ in parentheses.}", "\\label{tab:ablation}",
         "\\setlength{\\tabcolsep}{3.5pt}", "\\begin{tabular}{l" + "c" * len(vs) + "}", "\\toprule",
         " & " + " & ".join(f"{LBL[v]}" for v in vs) + " \\\\",
         " & " + " & ".join(f"{{\\scriptsize {WHY[v]}}}" for v in vs) + " \\\\", "\\midrule"]
    for key, name, fmt in TABLE:
        st, diffs = stats(data, key)
        cells = []
        for v in vs:
            if v not in st:
                cells.append("--")
                continue
            mu, lo, hi, _ = st[v]
            c = f"{fmt.format(mu)} {{\\scriptsize[{fmt.format(lo)}, {fmt.format(hi)}]}}"
            if v in diffs:
                d = diffs[v]
                ptxt = "$<$0.001" if d["p"] < 0.001 else f"{d['p']:.2f}"
                dtxt = f"$\\Delta${'+' if d['mean'] >= 0 else ''}{fmt.format(d['mean'])} ({ptxt})"
                dshow = ("\\textbf{" + dtxt + "}") if d["p"] < 0.05 else dtxt
                c += "\\\\[-1pt]{\\scriptsize " + dshow + "}"
            cells.append(f"\\makecell{{{c}}}")
            rows.append(["table", key, v, mu, lo, hi, st[v][3], diffs.get(v, {}).get("p")])
        L.append(f"{name} & " + " & ".join(cells) + " \\\\")
    L += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    L.insert(0, "% also requires \\usepackage{makecell}")
    with open(os.path.join(out, "table_ablation.tex"), "w") as f:
        f.write("\n".join(L) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", default=None, help="default: <campaign>/paper")
    a = ap.parse_args()
    out = a.out or os.path.join(a.campaign, "paper")
    os.makedirs(out, exist_ok=True)
    data = load(a.campaign)
    if not data:
        print("no valid metrics.json found under", a.campaign)
        return 1
    plt = setup()
    rows = []
    fig_delta(plt, data, out, rows)
    fig_tradeoff(plt, data, out, rows)
    table(data, out, rows)
    with open(os.path.join(out, "ablation_summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["what", "kpi", "variant", "mean", "ci_lo", "ci_hi", "n", "p_holm"])
        w.writerows(rows)
    print(f"{len(data)} blocks ->", out, ":", ", ".join(sorted(x for x in os.listdir(out)
                                                               if x.startswith(("figA", "figB", "table_abl")))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
