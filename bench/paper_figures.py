#!/usr/bin/env python3
"""Publication figures + LaTeX table for a PReNEF campaign (IEEE two-column format).

  python3 bench/paper_figures.py --campaign campaigns/final3 --out campaigns/final3/paper

Inputs
  <campaign>/figures/per_af.csv   (written by bench/figures.py; run that first)
  <campaign>/b*-*/                (run directories; needed for Fig. 4 per-episode leads and Fig. 5)
Outputs (PDF = vector for LaTeX, PNG = preview), no titles inside figures (captions go in LaTeX):
  fig1_exposure_groups    primary KPI, shared-service AFs vs independent AFs (single column)
  fig2_forest             paired differences with 95% CI and Holm-adjusted p (single column)
  fig3_benefit_cost       exposure / time in primary mode / unnecessary fallbacks (double column)
  fig4_lead_ecdf          ECDF of the fallback lead time per arm (single column)
  fig5_timeline           zoom on one shared-service episode, af1+af2, key arms (double column)
  table_main.tex          booktabs table, mean [95% CI], best non-oracle value in bold
  summary.csv             the numbers behind every figure
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bench.analyze import bootstrap_ci, holm, wilcoxon  # noqa: E402

# ------------------------------------------------------------------ fixed encoding
# arm -> (label, colour, hatch, marker). Colour fixed per arm in every figure; hatch +
# marker keep the arms distinguishable in grayscale print and for colour-blind readers.
ARMS = [
    ("direct_nef",       "Direct NEF (3GPP)",   "#eda100", "",     "^"),
    ("independent_pred", "Per-AF predictor",    "#eb6834", "////", "s"),
    ("prenef_noai",      "PReNEF (no AI)",      "#1baf7a", "....", "D"),
    ("prenef_dtip",      "PReNEF + DTIP",       "#2a78d6", "",     "o"),
    # oracle arm removed
]
LBL = {a: l for a, l, *_ in ARMS}
COL = {a: c for a, _, c, *_ in ARMS}
HAT = {a: h for a, _, _, h, _ in ARMS}
MRK = {a: m for a, *_, m in ARMS}
GROUPS = [("shared", "Shared-service AFs (af1, af2)", ("af1", "af2")),
          ("indep", "Independent AFs (af3, af4)", ("af3", "af4"))]
INK, INK2, GRID = "#1a1a1a", "#555555", "#e4e4e4"
COL1, COL2 = 3.5, 7.16           # IEEE column / double-column widths (inches)


def setup():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "stix", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "legend.frameon": False,
        "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5, "lines.linewidth": 1.0,
        "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": INK2,
        "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.5,
        "hatch.linewidth": 0.5, "hatch.color": "white",
        "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "pdf.fonttype": 42, "ps.fonttype": 42,
    })
    return plt


def save(fig, out, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(out, f"{name}.{ext}"), dpi=400)


# ------------------------------------------------------------------ data
def fnum(x):
    try:
        v = float(x)
        return None if math.isnan(v) else v
    except (TypeError, ValueError):
        return None


def load_rows(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            if r.get("audit_ok") == "False":
                continue
            rows.append({"block": int(r["block"]), "arm": r["arm"], "af": r["af"],
                         **{k: fnum(r.get(k)) for k in ("exposure_s_per_episode", "time_in_primary",
                                                         "timely_rate", "lead_s_median",
                                                         "unnecessary_fallbacks", "utility_loss_per_min",
                                                         "alerts_received", "episodes")}})
    return rows


def group_by_block(rows, afs, key):
    """block -> arm -> mean over the group's AFs (AFs without a value in that block are skipped)."""
    acc = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["af"] in afs and r[key] is not None:
            acc[r["block"]][r["arm"]].append(r[key])
    return {b: {a: float(np.mean(v)) for a, v in d.items()} for b, d in acc.items()}


def mean_ci(vals):
    v = np.array([x for x in vals if x is not None], float)
    if len(v) == 0:
        return (None, None, None, 0)
    lo, hi = bootstrap_ci(v) if len(v) >= 3 else (v.min(), v.max())
    return float(v.mean()), float(lo), float(hi), len(v)


def arm_stats(byb, arm):
    return mean_ci([d[arm] for d in byb.values() if arm in d])


def paired(byb, a, b):
    d = np.array([v[a] - v[b] for v in byb.values() if a in v and b in v], float)
    if len(d) < 3:
        return None
    lo, hi = bootstrap_ci(d)
    return {"n": len(d), "mean": float(d.mean()), "lo": float(lo), "hi": float(hi), "p": wilcoxon(d)}


# ------------------------------------------------------------------ Fig. 1
def fig1(plt, rows, out, summary):
    arms = [a for a, *_ in ARMS]
    fig, ax = plt.subplots(figsize=(COL1, 2.15))
    w = 0.19
    for gi, (gk, gl, afs) in enumerate(GROUPS):
        byb = group_by_block(rows, afs, "exposure_s_per_episode")
        base = arm_stats(byb, "direct_nef")[0]
        for k, arm in enumerate(arms):
            mu, lo, hi, n = arm_stats(byb, arm)
            if mu is None:
                continue
            x = gi + (k - (len(arms) - 1) / 2) * w
            ax.bar(x, mu, w * 0.92, color=COL[arm], hatch=HAT[arm], edgecolor="white", linewidth=0.3,
                   label=LBL[arm] if gi == 0 else None, zorder=2)
            ax.errorbar(x, mu, yerr=[[mu - lo], [hi - mu]], fmt="none", ecolor=INK, elinewidth=0.6,
                        capsize=1.6, capthick=0.6, zorder=3)
            summary.append(["fig1", gk, arm, "exposure_s_per_episode", mu, lo, hi, n])
            if arm == "prenef_dtip" and base:
                ax.text(x, hi + 0.08, f"$-${100 * (1 - mu / base):.0f}%", ha="center", va="bottom",
                        fontsize=6.5, color=COL[arm])
    ax.set_xticks([0, 1])
    ax.set_xticklabels([g[1].replace(" (", "\n(") for g in GROUPS])
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("Inadequate-mode exposure\nper episode (s)")
    ax.set_ylim(0, 3.3)
    ax.set_xlim(-0.5, 1.5)
    ax.legend(ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.24), handlelength=1.4, columnspacing=0.9)
    save(fig, out, "fig1_exposure_groups")
    plt.close(fig)


# ------------------------------------------------------------------ Fig. 2
COMPARE = [("prenef_dtip", "independent_pred"), ("prenef_dtip", "direct_nef"),
           ("independent_pred", "direct_nef"), ("prenef_noai", "direct_nef")]  # oracle removed


def fig2(plt, rows, out, summary):
    items = []
    for gk, gl, afs in GROUPS:
        byb = group_by_block(rows, afs, "exposure_s_per_episode")
        res = {(a, b): paired(byb, a, b) for a, b in COMPARE}
        res = {k: v for k, v in res.items() if v}
        adj = holm({k: v["p"] for k, v in res.items()})
        for (a, b), v in res.items():
            v["p_holm"] = adj[(a, b)]
            items.append((gk, gl, a, b, v))
            summary.append(["fig2", gk, f"{a}-{b}", "paired_diff_exposure", v["mean"], v["lo"], v["hi"],
                            v["n"], v["p_holm"]])
    fig, ax = plt.subplots(figsize=(COL1, 2.9))
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    y, yt, yl, gy = 0, [], [], []
    for gk, gl, _ in GROUPS:
        gy.append((y, gl))
        y -= 1
        for g2, _, a, b, v in items:
            if g2 != gk:
                continue
            sig = v["p_holm"] < 0.05
            ax.plot([v["lo"], v["hi"]], [y, y], color=COL[a], lw=1.4, solid_capstyle="butt")
            ax.plot(v["mean"], y, MRK[a], color=COL[a], ms=4.2, mfc=COL[a] if sig else "white",
                    mec=COL[a], mew=1.0, zorder=3)
            ptxt = "$p<$0.001" if v["p_holm"] < 0.001 else f"$p=${v['p_holm']:.2f}"
            ax.text(1.02, y, ptxt, transform=ax.get_yaxis_transform(), fontsize=6.5, va="center",
                    color=INK if sig else INK2)
            yt.append(y)
            yl.append(f"{LBL[a].replace(' (3GPP)', '')} $-$ {LBL[b].replace(' (3GPP)', '')}")
            y -= 1
        y -= 0.4
    for yy, gl in gy:
        ax.text(0.0, yy, gl, transform=ax.get_yaxis_transform(), fontsize=7.5, fontweight="bold",
                va="center", ha="left")
    ax.axvline(0, color=INK, lw=0.7)
    ax.set_yticks(yt)
    ax.set_yticklabels(yl, fontsize=6.8)
    ax.tick_params(axis="y", length=0)
    ax.set_ylim(y + 0.6, 0.6)
    ax.set_xlabel("Paired difference in exposure per episode (s)\n$\\leftarrow$ first arm better")
    ax.spines["left"].set_visible(False)
    save(fig, out, "fig2_forest")
    plt.close(fig)


# ------------------------------------------------------------------ Fig. 3
PANELS = [("exposure_s_per_episode", "(a) Exposure / episode (s)", "lower is better", 1.0),
          ("time_in_primary", "(b) Time in primary mode (%)", "higher is better", 100.0),
          ("unnecessary_fallbacks", "(c) Unnecessary fallbacks / run", "lower is better", 1.0),
          ("utility_loss_per_min", "(d) Utility loss (utility$\\cdot$s / min)", "lower is better", 1.0)]


def fig3(plt, rows, out, summary):
    arms = [a for a, *_ in ARMS]
    afs = GROUPS[0][2]
    fig, axes = plt.subplots(1, len(PANELS), figsize=(COL2, 1.75), sharey=True,
                             gridspec_kw={"wspace": 0.12})
    for ax, (key, title, hint, scale) in zip(axes, PANELS):
        byb = group_by_block(rows, afs, key)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", visible=True)
        for k, arm in enumerate(arms):
            mu, lo, hi, n = arm_stats(byb, arm)
            if mu is None:
                continue
            yk = len(arms) - 1 - k
            ax.plot([lo * scale, hi * scale], [yk, yk], color=COL[arm], lw=1.6, solid_capstyle="butt")
            ax.plot(mu * scale, yk, MRK[arm], color=COL[arm], ms=4.5, mec="white", mew=0.5, zorder=3)
            summary.append(["fig3", "shared", arm, key, mu * scale, lo * scale, hi * scale, n])
        ax.set_title(title, loc="left", fontsize=7.2, pad=9)
        ax.text(0.0, 1.015, hint, transform=ax.transAxes, fontsize=6, color=INK2, va="bottom")
        ax.margins(x=0.12)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
    axes[0].set_yticks(range(len(arms)))
    axes[0].set_yticklabels([LBL[a] for a in reversed(arms)])
    save(fig, out, "fig3_benefit_cost")
    plt.close(fig)


# ------------------------------------------------------------------ Fig. 4
def load_leads(campaign):
    """Per-episode leads from the run directories; None if unavailable."""
    try:
        from bench.figures import load_campaign
        rows, raws = load_campaign(campaign)
    except Exception as e:  # noqa: BLE001
        print("  (per-episode leads unavailable:", str(e)[:80], ")")
        return None, None
    out = defaultdict(lambda: defaultdict(list))
    for r in rows:
        for g, _, afs in GROUPS:
            if r["af"] in afs:
                out[g][r["arm"]] += [x["lead_s"] for x in r.get("leads", [])]
    return out, raws


def fig4(plt, rows, leads, out, summary):
    arms = [a for a, *_ in ARMS]
    basis = "episode" if leads else "run median"
    fig, axes = plt.subplots(2, 1, figsize=(COL1, 3.0), sharex=True, gridspec_kw={"hspace": 0.32})
    for ax, (gk, gl, afs) in zip(axes, GROUPS):
        ax.grid(axis="x", visible=True)
        ax.axvspan(0, 10, color="#eaf1fb", zorder=0, lw=0)
        ax.axvline(0, color=INK, lw=0.7)
        for arm in arms:
            if leads:
                v = np.sort(np.array(leads[gk].get(arm, []), float))
            else:
                v = np.sort(np.array([r["lead_s_median"] for r in rows
                                      if r["af"] in afs and r["arm"] == arm and r["lead_s_median"] is not None]))
            if len(v) == 0:
                continue
            yv = np.arange(1, len(v) + 1) / len(v)
            ax.step(v, yv, where="post", color=COL[arm], lw=1.2,
                    ls="--" if arm == "oracle" else "-", label=LBL[arm])
            summary.append(["fig4", gk, arm, f"share_anticipated({basis})", float(np.mean(v > 0)), None, None,
                            len(v)])
        ax.set_ylim(0, 1.02)
        ax.set_ylabel("ECDF")
        ax.set_title(gl, loc="left", fontsize=7.5, fontweight="bold", pad=3)
        ax.text(0.15, 0.06, "anticipated", fontsize=6.5, color=INK2, va="bottom")
    axes[-1].set_xlim(-5, 2)
    axes[-1].set_xlabel(f"Lead = onset $-$ fallback confirmation (s), per {basis}")
    axes[0].legend(ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.12), handlelength=1.6, columnspacing=0.8)
    save(fig, out, "fig4_lead_ecdf")
    plt.close(fig)


# ------------------------------------------------------------------ Fig. 5
def pick_episode(raws, block):
    """First shared episode in `block` where DTIP confirmed af1's fallback before the onset."""
    raw = raws.get((block, "prenef_dtip"))
    if not raw:
        return None
    for e in raw["episodes"]:
        if e["kind"] != "shared" or e["onsets"].get("af1") is None:
            continue
        ag = raw["agents"].get("af1")
        if not ag:
            continue
        prim = ag["primary"]
        on = e["onsets"]["af1"]
        if any(m != prim and on - 6 <= w <= on for w, m in ag["modes"]):
            return e
    return None


def fig5(plt, raws, out, block=None):
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    lanes = ["direct_nef", "independent_pred", "prenef_noai", "prenef_dtip"]
    blocks = sorted({b for b, _ in raws})
    cand = [block] if block else blocks
    ep = blk = None
    for b in cand:
        ep = pick_episode(raws, b)
        if ep:
            blk = b
            break
    if not ep:
        print("  fig5 skipped: no shared episode with an anticipated DTIP fallback found")
        return None
    fig, axes = plt.subplots(2, 1, figsize=(COL2, 2.35), sharex=True, gridspec_kw={"hspace": 0.45})
    for ax, af in zip(axes, ("af1", "af2")):
        ax.grid(False)
        for k, arm in enumerate(lanes):
            raw = raws.get((blk, arm))
            if not raw or af not in raw["agents"]:
                continue
            t0 = raw["episodes"][[e["episode"] for e in raw["episodes"]].index(ep["episode"])]["onsets"].get(af) \
                if ep["episode"] in [e["episode"] for e in raw["episodes"]] else None
            if t0 is None:
                continue
            e_arm = next(e for e in raw["episodes"] if e["episode"] == ep["episode"])
            ag = raw["agents"][af]
            yk = len(lanes) - 1 - k
            if k == 0:
                ax.axvspan(e_arm["start"] - t0, e_arm["end"] - t0, color="#f1f0ec", lw=0, zorder=0)
            pts = ag["modes"] + [(ag["t_last"], None)]
            for (w, m), (w2, _) in zip(pts, pts[1:]):
                ax.broken_barh([(w - t0, w2 - w)], (yk - 0.3, 0.6), lw=0, zorder=2,
                               color=COL[arm] if m == ag["primary"] else "#d4d3cf")
            if ag["inadequate"]:
                ax.broken_barh([(w - t0, dt) for w, dt in ag["inadequate"]], (yk - 0.42, 0.12),
                               color="#c62828", lw=0, zorder=3)
            al = [w - t0 for w in ag["alerts"] if -12 <= w - t0 <= 10]
            if al:
                ax.plot(al, [yk + 0.42] * len(al), "v", color=INK, ms=2.8, zorder=4, clip_on=False)
        ax.axvline(0, color=INK, lw=0.8, ls=(0, (3, 2)), zorder=5)
        ax.set_yticks(range(len(lanes)))
        ax.set_yticklabels([LBL[a] for a in reversed(lanes)], fontsize=6.8)
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        ax.set_ylim(-0.6, len(lanes) - 0.35)
        ax.set_title("af1 (shuttle A)" if af == "af1" else "af2 (shuttle B)", loc="left", fontsize=7.5)
    axes[-1].set_xlim(-12, 10)
    axes[-1].set_xlabel("Time relative to the contract onset of the shared-service failure (s)")
    handles = [Patch(color=COL["prenef_dtip"], label="primary (remote) mode, arm colour"),
               Patch(color="#d4d3cf", label="fallback (local) mode"),
               Patch(color="#c62828", label="mode inadequate"),
               Patch(color="#f1f0ec", label="injected episode"),
               Line2D([], [], color=INK, ls=(0, (3, 2)), lw=0.8, label="contract onset"),
               Line2D([], [], color=INK, marker="v", ls="", ms=3, label="alert received")]
    fig.legend(handles=handles, ncol=6, loc="upper center", bbox_to_anchor=(0.5, 1.06), handlelength=1.3,
               columnspacing=0.8, fontsize=6.5)
    save(fig, out, "fig5_timeline")
    plt.close(fig)
    return blk, ep["episode"]


# ------------------------------------------------------------------ table
TABLE_KPIS = [("exposure_s_per_episode", "Exposure / episode (s)", -1, 1.0, "{:.2f}"),
              ("timely_rate", "Timely adaptation (eq.~26)", +1, 1.0, "{:.2f}"),
              ("lead_s_median", "Median lead (s)", +1, 1.0, "{:+.2f}"),
              ("time_in_primary", "Time in primary mode (\\%)", +1, 100.0, "{:.1f}"),
              ("unnecessary_fallbacks", "Unnecessary fallbacks / run", -1, 1.0, "{:.2f}"),
              ("utility_loss_per_min", "Utility loss (utility$\\cdot$s/min)", -1, 1.0, "{:.2f}")]


def table(rows, out, summary):
    arms = [a for a, *_ in ARMS]
    L = ["% requires \\usepackage{booktabs}",
         "\\begin{table*}[t]", "\\centering", "\\small",
         "\\caption{Per-group results over 20 paired blocks: mean [95\\% bootstrap CI]. "
         "Best non-oracle value in bold.}",
         "\\label{tab:main}", "\\setlength{\\tabcolsep}{4pt}",
         "\\begin{tabular}{l" + "c" * len(arms) + "}", "\\toprule",
         " & " + " & ".join(LBL[a].replace("&", "\\&") for a in arms) + " \\\\", "\\midrule"]
    for gk, gl, afs in GROUPS:
        L.append(f"\\multicolumn{{{len(arms) + 1}}}{{l}}{{\\textit{{{gl}}}}} \\\\")
        for key, name, direction, scale, fmt in TABLE_KPIS:
            byb = group_by_block(rows, afs, key)
            st = {a: arm_stats(byb, a) for a in arms}
            cand = {a: s[0] for a, s in st.items() if s[0] is not None and a != "oracle"}
            best = (min if direction < 0 else max)(cand, key=cand.get) if cand else None
            cells = []
            for a in arms:
                mu, lo, hi, n = st[a]
                if mu is None:
                    cells.append("--")
                    continue
                v = fmt.format(mu * scale)
                v = f"\\textbf{{{v}}}" if a == best else v
                cells.append(f"{v} {{\\scriptsize[{fmt.format(lo * scale)}, {fmt.format(hi * scale)}]}}")
                summary.append(["table", gk, a, key, mu * scale, lo * scale, hi * scale, n])
            L.append(f"\\quad {name} & " + " & ".join(cells) + " \\\\")
        L.append("\\midrule" if gk == "shared" else "\\bottomrule")
    L += ["\\end{tabular}", "\\end{table*}"]
    with open(os.path.join(out, "table_main.tex"), "w") as f:
        f.write("\n".join(L) + "\n")


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--per-af", default=None, help="default: <campaign>/figures/per_af.csv")
    ap.add_argument("--out", default=None, help="default: <campaign>/paper")
    ap.add_argument("--block", type=int, default=None, help="block for Fig. 5 (default: first suitable)")
    a = ap.parse_args()
    csv_path = a.per_af or os.path.join(a.campaign, "figures", "per_af.csv")
    out = a.out or os.path.join(a.campaign, "paper")
    if not os.path.exists(csv_path):
        print(f"missing {csv_path}: run  python3 bench/figures.py --campaign {a.campaign} "
              f"--out {a.campaign}/figures  first")
        return 1
    os.makedirs(out, exist_ok=True)
    plt = setup()
    rows = load_rows(csv_path)
    summary = []
    fig1(plt, rows, out, summary)
    fig2(plt, rows, out, summary)
    fig3(plt, rows, out, summary)
    leads, raws = None, None
    if any(n.startswith("b") and os.path.isdir(os.path.join(a.campaign, n)) for n in os.listdir(a.campaign)):
        print("  reading run folders (about 1 min)...")
        leads, raws = load_leads(a.campaign)
    fig4(plt, rows, leads, out, summary)
    if raws:
        r = fig5(plt, raws, out, a.block)
        if r:
            print(f"  fig5: block {r[0]}, episode {r[1]}")
    table(rows, out, summary)
    with open(os.path.join(out, "summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["figure", "group", "arm_or_pair", "kpi", "mean", "ci_lo", "ci_hi", "n", "p_holm"])
        w.writerows(summary)
    print("wrote", out, ":", ", ".join(sorted(x for x in os.listdir(out) if x.endswith((".pdf", ".tex")))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
