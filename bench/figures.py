#!/usr/bin/env python3
"""Per-AF (per-UE) analysis + paper figures for a PReNEF campaign.

  python3 bench/figures.py --campaign campaigns/final --out campaigns/final/figures

Reads every run directory b<NN>-<arm>/ (journal, agent logs, scenario, ground truth,
runtime.json) - nothing is re-run. Writes:

  per_af.csv            one row per (block, arm, AF): every per-AF KPI
  per_af.md             means with 95% bootstrap CI per AF x arm + paired comparisons per AF
  data_quality.md       runs whose measurements are not trustworthy (excluded from the figures)
  fig1_timeline_bNN     what every AF did in one block, all arms stacked: mode, inadequacy,
                        alerts, injected episodes and contract onsets  (the mechanism figure)
  fig2_exposure_per_af  primary KPI per AF, paired by block, mean + 95% CI per arm
  fig3_tradeoff         exposure vs utility loss per arm (overall + per AF): the cost/benefit view
  fig4_time_in_remote   share of time each AF spent in its primary (remote) mode, AF x arm
  fig5_lead_time        how long before the contract onset the fallback was confirmed, per arm
  fig6_data_quality     measurement coverage per run (block x arm), invalid runs marked
Each figure is written as .png (300 dpi) and .pdf (vector, for LaTeX).

Validity rule (same as bench/analyze.py --min-coverage): a run is excluded if any AF
obtained a path measurement (RTT) in fewer than --min-coverage of its observations.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bench.analyze import bootstrap_ci, holm, wilcoxon  # noqa: E402
from bench.metrics import episodes, load_agent_logs, mode_at, mode_timeline, obs_series  # noqa: E402
from prenef.common import read_json, read_jsonl  # noqa: E402
from prenef.contracts import parse_contract  # noqa: E402

# ---------------------------------------------------------------- presentation constants
# Entity -> colour is FIXED (never by rank). Validated palette slots 1-5 (light mode):
# adjacent CVD dE >= 9.1, normal-vision dE >= 19.6; slots 3-5 are < 3:1 contrast, so every
# arm is ALSO identified by text (tick labels / direct labels) and by marker shape.
ARM_STYLE = {
    "prenef_dtip":          ("#2a78d6", "o", "PReNEF + DTIP"),
    "independent_pred":     ("#eb6834", "s", "Per-AF predictor"),
    "prenef_noai":          ("#1baf7a", "D", "PReNEF (no AI)"),
    "direct_nef":           ("#eda100", "^", "Direct NEF (3GPP)"),
    "oracle":               ("#e87ba4", "v", "Oracle (upper bound)"),
    "prenef_dtip_eta0":     ("#008300", "P", "DTIP, η = 0"),
    "prenef_dtip_nogate":   ("#6250d6", "X", "DTIP, no u-gate"),
    "prenef_dtip_nofanout": ("#e34948", "h", "DTIP, no fan-out"),
}
ARM_ORDER = ["direct_nef", "independent_pred", "prenef_noai", "prenef_dtip", "oracle",
             "prenef_dtip_eta0", "prenef_dtip_nogate", "prenef_dtip_nofanout"]
AF_LABEL = {"af1": "af1 · shuttle A (sRSU)", "af2": "af2 · shuttle B (sRSU)",
            "af3": "af3 · drone", "af4": "af4 · XR"}
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1"
MODE_PRIMARY, MODE_FALLBACK, INADEQ, EPISODE_BG = "#2a78d6", "#d9d8d4", "#e34948", "#f3f2ee"


def label(arm):
    return ARM_STYLE.get(arm, ("#8a8984", "o", arm))[2]


def color(arm):
    return ARM_STYLE.get(arm, ("#8a8984", "o", arm))[0]


def marker(arm):
    return ARM_STYLE.get(arm, ("#8a8984", "o", arm))[1]


# ---------------------------------------------------------------- per-run, per-AF extraction
def load_contracts(run_dir):
    out = {}
    rt = os.path.join(run_dir, "runtime.json")
    if os.path.exists(rt):
        for cp in read_json(rt).get("contracts", []):
            cp = cp if os.path.isabs(cp) else os.path.join(ROOT, cp)
            c = parse_contract(read_json(cp))
            out[c.af_id] = c
    return out


def run_per_af(run_dir: str) -> tuple[dict, dict]:
    """Returns ({af: kpis}, raw) for one run. raw keeps what the timeline figure needs."""
    j = list(read_jsonl(os.path.join(run_dir, "journal.jsonl")))
    start = next(r for r in j if r["kind"] == "run_start")
    scen_p = os.path.join(run_dir, "scenario.json")
    scen = read_json(scen_p) if os.path.exists(scen_p) else {}
    contracts = load_contracts(run_dir)
    agents = load_agent_logs(run_dir)
    eps = episodes(run_dir, scen.get("service_afs", {}), contracts, scen)
    gt = os.path.join(run_dir, "ground_truth.jsonl")
    t0 = None
    if os.path.exists(gt):
        t0s = [r["applied_wall_s"] - r["t"] for r in read_jsonl(gt) if "t" in r]
        t0 = min(t0s) if t0s else None
    raw = {"t0": t0, "episodes": eps, "agents": {}, "start_wall": start["wall_s"]}
    out = {}
    for af, recs in agents.items():
        obs = [r for r in recs if r["kind"] == "observation"]
        if not obs:
            continue
        tl = mode_timeline(recs)
        primary = tl[0][1] if tl else None
        series = obs_series(recs)
        t_first, t_last = obs[0]["wall_s"], obs[-1]["wall_s"]
        dur = max(1e-9, t_last - t_first)
        # time in primary mode (confirmed), and utility loss (J2 per AF)
        pts = [(w, m) for w, m, _, _ in tl] + [(t_last, None)]
        in_primary = 0.0
        uloss = 0.0
        c = contracts.get(af)
        for (w, m), (w2, _) in zip(pts, pts[1:]):
            a, b = max(w, t_first), max(w2, t_first)
            if b <= a:
                continue
            if m == primary:
                in_primary += b - a
            if c and primary and m in c.modes:
                uloss += max(0.0, c.modes[primary].utility - c.modes[m].utility) * (b - a)
        fallbacks = [(w, m, prev) for w, m, prev, _ in tl if prev == primary and m != primary]
        windows, exps, timely, leads = [], [], [], []
        for e in eps:
            onset = e["onsets"].get(af)
            if af not in e["afs"] or onset is None:
                continue
            windows.append((e["start"] - 1.0, e["end"] + 1.0))
            exps.append(sum(dt for w, a, dt, _ in series if a == 0 and e["start"] <= w <= e["end"] + 3.0))
            if mode_at(tl, e["start"]) == primary:
                fb = [x for x in fallbacks if e["start"] - 1.0 <= x[0] <= e["end"]]
                timely.append(int(bool(fb) and fb[0][0] <= onset))
                if fb:
                    tau = c.tau(primary, fb[0][1]) if c else None
                    leads.append({"lead_s": onset - fb[0][0], "tau_s": tau, "kind": e["kind"]})
        unnecessary = sum(1 for w, _, _ in fallbacks if not any(lo <= w <= hi for lo, hi in windows))
        cov = sum(r.get("obs", {}).get("latency_ms") is not None for r in obs) / len(obs)
        out[af] = {
            "coverage": cov,
            "time_in_primary": in_primary / dur,
            "episodes": len(exps),
            "exposure_s_per_episode": float(np.mean(exps)) if exps else None,
            "exposure_s_total": float(np.sum(exps)) if exps else 0.0,
            "timely_rate": float(np.mean(timely)) if timely else None,
            "lead_s_median": float(np.median([x["lead_s"] for x in leads])) if leads else None,
            "fallbacks": len(fallbacks),
            "unnecessary_fallbacks": unnecessary,
            "utility_loss_per_min": uloss / (dur / 60.0),
            "alerts_received": sum(1 for r in recs if r["kind"] == "alert_received"),
            "leads": leads,
        }
        raw["agents"][af] = {
            "modes": [(w, m) for w, m, _, _ in tl], "primary": primary, "t_last": t_last,
            "inadequate": [(w, dt) for w, a, dt, _ in series if a == 0],
            "alerts": [r["wall_s"] for r in recs if r["kind"] == "alert_received"
                       and (r.get("alert") or {}).get("type") in ("notify", "notify_late")],
        }
    return out, raw


def load_campaign(campaign: str):
    rows, raws = [], {}
    for d in sorted(glob.glob(os.path.join(campaign, "b*-*"))):
        if not os.path.exists(os.path.join(d, "journal.jsonl")):
            continue
        name = os.path.basename(d)
        block, arm = int(name[1:3]), name.split("-", 1)[1]
        if arm == "oracle":                  # oracle arm removed from the study
            continue
        try:
            per_af, raw = run_per_af(d)
        except (StopIteration, FileNotFoundError, ValueError) as e:
            print("skip", d, e)
            continue
        audit = os.path.join(d, "audit.json")
        audit_ok = read_json(audit)["ok"] if os.path.exists(audit) else None
        raws[(block, arm)] = raw
        for af, k in per_af.items():
            rows.append({"block": block, "arm": arm, "af": af, "audit_ok": audit_ok, **k})
    return rows, raws


# ---------------------------------------------------------------- matplotlib style
def setup_mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
        "axes.labelsize": 10, "axes.labelcolor": INK2, "axes.edgecolor": MUTED, "axes.linewidth": 0.8,
        "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.grid.axis": "y",
        "grid.color": GRID, "grid.linewidth": 0.8, "legend.frameon": False, "legend.fontsize": 9,
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.bbox": "tight",
        "pdf.fonttype": 42, "lines.linewidth": 2,
    })
    return plt


def save(fig, out, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(out, f"{name}.{ext}"), dpi=300)


def mean_ci(vals):
    v = np.array([x for x in vals if x is not None and not (isinstance(x, float) and math.isnan(x))], float)
    if len(v) == 0:
        return None, None, None, 0
    lo, hi = bootstrap_ci(v) if len(v) >= 3 else (v.min(), v.max())
    return float(v.mean()), lo, hi, len(v)


# ---------------------------------------------------------------- figures
def fig_timeline(plt, raws, valid_runs, arms, block, out):
    afs = sorted({af for (b, a), r in raws.items() if b == block for af in r["agents"]})
    lanes = [a for a in arms if (block, a) in raws]
    if not afs or not lanes:
        return None
    fig, axes = plt.subplots(len(afs), 1, figsize=(11, 1.0 + 0.42 * len(lanes) * len(afs)),
                             sharex=True, gridspec_kw={"hspace": 0.35})
    axes = np.atleast_1d(axes)
    tmax = 0.0
    for ax, af in zip(axes, afs):
        ax.grid(False)
        for k, arm in enumerate(lanes):
            raw = raws[(block, arm)]
            t0 = raw["t0"] or raw["start_wall"]
            ag = raw["agents"].get(af)
            y = len(lanes) - 1 - k
            if k == 0:   # injected episodes & per-AF contract onsets (same scenario in every arm)
                for e in raw["episodes"]:
                    if af in e["afs"]:
                        ax.axvspan(e["start"] - t0, e["end"] - t0, color=EPISODE_BG, zorder=0, lw=0)
            if ag is None:
                continue
            modes = ag["modes"] + [(ag["t_last"], None)]
            for (w, m), (w2, _) in zip(modes, modes[1:]):
                ax.broken_barh([(w - t0, w2 - w)], (y - 0.32, 0.64),
                               color=MODE_PRIMARY if m == ag["primary"] else MODE_FALLBACK, lw=0, zorder=2)
            if ag["inadequate"]:
                ax.broken_barh([(w - t0, dt) for w, dt in ag["inadequate"]], (y - 0.42, 0.14),
                               color=INADEQ, lw=0, zorder=3)
            if ag["alerts"]:
                ax.plot([w - t0 for w in ag["alerts"]], [y + 0.42] * len(ag["alerts"]), "v",
                        color=INK, ms=5, zorder=4, clip_on=False)
            for e in raw["episodes"]:
                on = e["onsets"].get(af)
                if on is not None and k == 0:
                    ax.axvline(on - t0, color=INK, lw=1, ls=(0, (3, 2)), zorder=5)
            tmax = max(tmax, ag["t_last"] - t0)
            if (block, arm) not in valid_runs:
                ax.text(1.002, y, "invalid", transform=ax.get_yaxis_transform(), color=INADEQ,
                        fontsize=8, va="center")
        ax.set_yticks(range(len(lanes)))
        ax.set_yticklabels([label(a) for a in reversed(lanes)], fontsize=8.5)
        ax.set_ylim(-0.6, len(lanes) - 0.4)
        ax.set_title(AF_LABEL.get(af, af), loc="left", fontsize=10)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
    axes[-1].set_xlim(0, tmax)
    axes[-1].set_xlabel("time since scenario start (s)")
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    handles = [Patch(color=MODE_PRIMARY, label="remote (primary) mode"),
               Patch(color=MODE_FALLBACK, label="local (fallback) mode"),
               Patch(color=INADEQ, label="mode inadequate (A = 0)"),
               Patch(color=EPISODE_BG, label="injected degradation episode"),
               Line2D([], [], color=INK, ls=(0, (3, 2)), lw=1, label="contract onset (eq. 4)"),
               Line2D([], [], color=INK, marker="v", ls="", ms=5, label="PReNEF alert received")]
    fig.legend(handles=handles, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.0 + 0.02))
    fig.suptitle(f"Block {block}: mode of each AF under every arm (same injected scenario)",
                 y=1.0 + 0.07, fontsize=12, fontweight="bold")
    save(fig, out, f"fig1_timeline_b{block:02d}")
    plt.close(fig)
    return f"fig1_timeline_b{block:02d}"


def fig_per_af_paired(plt, rows, arms, afs, key, ylabel, title, name, out):
    fig, axes = plt.subplots(1, len(afs), figsize=(3.2 * len(afs), 3.8), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, af in zip(axes, afs):
        by_block = defaultdict(dict)
        for r in rows:
            if r["af"] == af and r[key] is not None:
                by_block[r["block"]][r["arm"]] = r[key]
        for b, d in by_block.items():   # paired lines: one per block
            xs = [i for i, a in enumerate(arms) if a in d]
            ax.plot(xs, [d[arms[i]] for i in xs], color=GRID, lw=1, zorder=1)
        for i, arm in enumerate(arms):
            mu, lo, hi, n = mean_ci([d.get(arm) for d in by_block.values()])
            if mu is None:
                continue
            ax.errorbar(i, mu, yerr=[[mu - lo], [hi - mu]], fmt=marker(arm), color=color(arm), ms=8,
                        mec="white", mew=1.2, capsize=0, elinewidth=2, zorder=3)
        ax.set_xticks(range(len(arms)))
        ax.set_xticklabels([label(a) for a in arms], rotation=35, ha="right", fontsize=8.5)
        ax.set_title(AF_LABEL.get(af, af), loc="left", fontsize=10)
        ax.set_xlim(-0.5, len(arms) - 0.5)
    axes[0].set_ylabel(ylabel)
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, fontweight="bold", y=1.04)
    fig.text(0.01, 0.985, "dot = mean over blocks · bar = 95% bootstrap CI · grey lines pair the same block",
             fontsize=8.5, color=INK2, ha="left")
    save(fig, out, name)
    plt.close(fig)
    return name


def fig_tradeoff(plt, rows, arms, afs, out):
    def panel(ax, sel, title):
        for arm in arms:
            blocks = defaultdict(lambda: {"x": [], "y": []})
            for r in sel:
                if r["arm"] == arm:
                    blocks[r["block"]]["x"].append(r["utility_loss_per_min"])
                    if r["exposure_s_per_episode"] is not None:
                        blocks[r["block"]]["y"].append(r["exposure_s_per_episode"])
            xs = [np.mean(v["x"]) for v in blocks.values() if v["x"]]
            ys = [np.mean(v["y"]) for v in blocks.values() if v["y"]]
            mx, xlo, xhi, _ = mean_ci(xs)
            my, ylo, yhi, _ = mean_ci(ys)
            if mx is None or my is None:
                continue
            ax.errorbar(mx, my, xerr=[[mx - xlo], [xhi - mx]], yerr=[[my - ylo], [yhi - my]],
                        fmt=marker(arm), color=color(arm), ms=9, mec="white", mew=1.2, elinewidth=1.6, zorder=3)
            ax.annotate(label(arm), (mx, my), xytext=(6, 6), textcoords="offset points", fontsize=8.5, color=INK)
        ax.set_title(title, loc="left", fontsize=10)
        ax.grid(True, axis="both")
        ax.set_xlabel("utility loss (utility-s per min, J2)")
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    panel(ax, rows, "All AFs")
    ax.set_ylabel("inadequate-mode exposure per episode (s)")
    ax.annotate("better", xy=(0.04, 0.06), xytext=(0.2, 0.22), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color=INK2), color=INK2, fontsize=9)
    fig.suptitle("Benefit vs cost: less exposure should not be bought with lost utility",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    save(fig, out, "fig3_tradeoff")
    plt.close(fig)
    fig, axes = plt.subplots(1, len(afs), figsize=(3.4 * len(afs), 3.8))
    for ax, af in zip(np.atleast_1d(axes), afs):
        panel(ax, [r for r in rows if r["af"] == af], AF_LABEL.get(af, af))
    np.atleast_1d(axes)[0].set_ylabel("exposure per episode (s)")
    fig.suptitle("Benefit vs cost per AF (mean ± 95% CI over blocks)", x=0.01, ha="left",
                 fontsize=12, fontweight="bold", y=1.03)
    save(fig, out, "fig3_tradeoff_per_af")
    plt.close(fig)


def fig_heatmap(plt, rows, arms, afs, key, title, name, out, fmt="{:.0%}", cmap_name="Blues", vmax=1.0):
    M = np.full((len(afs), len(arms)), np.nan)
    for i, af in enumerate(afs):
        for j, arm in enumerate(arms):
            v = [r[key] for r in rows if r["af"] == af and r["arm"] == arm and r[key] is not None]
            if v:
                M[i, j] = float(np.mean(v))
    fig, ax = plt.subplots(figsize=(1.5 * len(arms) + 2, 0.6 * len(afs) + 1.6))
    ax.grid(False)
    im = ax.imshow(M, cmap=cmap_name, vmin=0, vmax=vmax, aspect="auto")
    for i in range(len(afs)):
        for j in range(len(arms)):
            if not np.isnan(M[i, j]):
                ax.text(j, i, fmt.format(M[i, j]), ha="center", va="center", fontsize=9,
                        color="white" if M[i, j] > 0.6 * vmax else INK)
    ax.set_xticks(range(len(arms)))
    ax.set_xticklabels([label(a) for a in arms], rotation=25, ha="right")
    ax.set_yticks(range(len(afs)))
    ax.set_yticklabels([AF_LABEL.get(a, a) for a in afs])
    for s in ax.spines.values():
        s.set_visible(False)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    ax.set_title(title, loc="left")
    save(fig, out, name)
    plt.close(fig)


def fig_leads(plt, rows, arms, out):
    fig, ax = plt.subplots(figsize=(7.5, 4))
    rng = np.random.default_rng(0)
    any_pts = False
    taus = []
    for i, arm in enumerate(arms):
        vals = [x["lead_s"] for r in rows if r["arm"] == arm for x in r["leads"]]
        taus += [x["tau_s"] for r in rows if r["arm"] == arm for x in r["leads"] if x["tau_s"]]
        if not vals:
            ax.text(i, 0, "no fallback\nin episodes", ha="center", va="center", fontsize=8, color=MUTED)
            continue
        any_pts = True
        ax.scatter(i + rng.uniform(-0.18, 0.18, len(vals)), vals, s=22, color=color(arm), marker=marker(arm),
                   edgecolor="white", linewidth=0.6, alpha=0.9, zorder=3)
        ax.plot([i - 0.3, i + 0.3], [np.median(vals)] * 2, color=INK, lw=2, zorder=4)
    ax.axhline(0, color=INK, lw=1)
    ax.axhspan(0, ax.get_ylim()[1] if any_pts else 1, color="#eaf2fc", zorder=0)
    ax.text(len(arms) - 0.45, 0.1, "confirmed BEFORE onset (anticipated)", ha="right", va="bottom",
            fontsize=8.5, color=INK2)
    ax.text(len(arms) - 0.45, -0.1, "confirmed after onset (reactive)", ha="right", va="top",
            fontsize=8.5, color=INK2)
    ax.set_xticks(range(len(arms)))
    ax.set_xticklabels([label(a) for a in arms], rotation=20, ha="right")
    ax.set_xlim(-0.6, len(arms) - 0.4)
    ax.set_ylabel("lead = onset − fallback confirmation (s)")
    t = f" (declared τ = {np.median(taus):.1f} s)" if taus else ""
    ax.set_title("Timeliness of the fallback per arm" + t, loc="left")
    save(fig, out, "fig5_lead_time")
    plt.close(fig)


def fig_quality(plt, cov_run, arms, blocks, thr, out):
    M = np.full((len(blocks), len(arms)), np.nan)
    for i, b in enumerate(blocks):
        for j, a in enumerate(arms):
            if (b, a) in cov_run:
                M[i, j] = cov_run[(b, a)]
    fig, ax = plt.subplots(figsize=(1.4 * len(arms) + 2, 0.28 * len(blocks) + 1.6))
    ax.grid(False)
    im = ax.imshow(M, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    for i in range(len(blocks)):
        for j in range(len(arms)):
            v = M[i, j]
            if np.isnan(v):
                ax.text(j, i, "missing", ha="center", va="center", fontsize=7, color=MUTED)
            elif v < thr:
                ax.text(j, i, f"✗ {v:.0%}", ha="center", va="center", fontsize=7.5, color=INADEQ,
                        fontweight="bold")
            else:
                ax.text(j, i, f"{v:.0%}", ha="center", va="center", fontsize=7, color="white")
    ax.set_xticks(range(len(arms)))
    ax.set_xticklabels([label(a) for a in arms], rotation=25, ha="right")
    ax.set_yticks(range(len(blocks)))
    ax.set_yticklabels([f"block {b}" for b in blocks], fontsize=8)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    ax.set_title(f"Measurement coverage per run (worst AF); ✗ = below {thr:.0%}, excluded", loc="left")
    save(fig, out, "fig6_data_quality")
    plt.close(fig)


# ---------------------------------------------------------------- tables
KPIS_AF = [("exposure_s_per_episode", "exposure / episode (s)", -1, "{:.3f}"),
           ("time_in_primary", "time in remote", +1, "{:.1%}"),
           ("timely_rate", "timely adaptation", +1, "{:.2f}"),
           ("lead_s_median", "median lead (s)", +1, "{:.2f}"),
           ("unnecessary_fallbacks", "unnecessary fallbacks", -1, "{:.2f}"),
           ("utility_loss_per_min", "utility loss / min", -1, "{:.2f}"),
           ("alerts_received", "alerts received", 0, "{:.1f}"),
           ("coverage", "measurement coverage", +1, "{:.1%}")]
PAIRS = [("prenef_dtip", "independent_pred"), ("prenef_dtip", "direct_nef"), ("prenef_noai", "direct_nef"),
         ("independent_pred", "direct_nef"), ("oracle", "prenef_dtip")]


def tables(rows, arms, afs, out):
    with open(os.path.join(out, "per_af.csv"), "w", newline="") as f:
        cols = ["block", "arm", "af", "audit_ok"] + [k for k, *_ in KPIS_AF] + ["episodes", "fallbacks"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r["af"], r["block"], ARM_ORDER.index(r["arm"]) if r["arm"] in ARM_ORDER else 99)):
            w.writerow(r)
    L = ["# Per-AF results", "", "Mean over valid blocks [95% bootstrap CI]. n = blocks.", ""]
    for af in afs:
        L += [f"## {AF_LABEL.get(af, af)}", "", "| KPI | " + " | ".join(label(a) for a in arms) + " |",
              "|---|" + "---|" * len(arms)]
        for k, name, _, fmt in KPIS_AF:
            cells = []
            for arm in arms:
                mu, lo, hi, n = mean_ci([r[k] for r in rows if r["af"] == af and r["arm"] == arm])
                cells.append("—" if mu is None else f"{fmt.format(mu)} [{fmt.format(lo)}, {fmt.format(hi)}] (n={n})")
            L.append(f"| {name} | " + " | ".join(cells) + " |")
        L += ["", "Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):", "",
              "| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |", "|---|---|---|---|---|---|"]
        for k, name, direction, fmt in KPIS_AF[:6]:
            res, pv = [], {}
            for A, B in PAIRS:
                if A not in arms or B not in arms:
                    continue
                d = {}
                for r in rows:
                    if r["af"] == af and r[k] is not None and r["arm"] in (A, B):
                        d.setdefault(r["block"], {})[r["arm"]] = r[k]
                diffs = np.array([v[A] - v[B] for v in d.values() if A in v and B in v], float)
                if len(diffs) < 3:
                    continue
                lo, hi = bootstrap_ci(diffs)
                p = wilcoxon(diffs)
                pv[(A, B)] = p
                res.append((A, B, len(diffs), diffs.mean(), lo, hi))
            adj = holm(pv)
            for A, B, n, mu, lo, hi in res:
                L.append(f"| {name} | {label(A)} vs {label(B)} | {n} | {mu:+.4f} | [{lo:+.4f}, {hi:+.4f}] | "
                         f"{adj[(A, B)]:.4f} |")
        L.append("")
    with open(os.path.join(out, "per_af.md"), "w") as f:
        f.write("\n".join(L) + "\n")


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-coverage", type=float, default=0.9)
    ap.add_argument("--block", type=int, default=None, help="block for the timeline figure (default: richest)")
    ap.add_argument("--include-invalid", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows, raws = load_campaign(a.campaign)
    if not rows:
        print("no runs found")
        return 1
    arms = [x for x in ARM_ORDER if any(r["arm"] == x for r in rows)] + \
        sorted({r["arm"] for r in rows} - set(ARM_ORDER))
    afs = sorted({r["af"] for r in rows})
    blocks = sorted({r["block"] for r in rows})
    cov_run = {}
    for r in rows:
        k = (r["block"], r["arm"])
        cov_run[k] = min(cov_run.get(k, 1.0), r["coverage"])
    valid = {k for k, v in cov_run.items() if v >= a.min_coverage}
    audit_bad = {(r["block"], r["arm"]) for r in rows if r["audit_ok"] is False}
    valid -= audit_bad
    invalid = sorted(set(cov_run) - valid)
    with open(os.path.join(a.out, "data_quality.md"), "w") as f:
        f.write(f"# Data quality\n\nValid runs: {len(valid)} / {len(cov_run)} "
                f"(rule: every AF measured its path in >= {a.min_coverage:.0%} of observations, audit OK)\n\n")
        for k in invalid:
            why = "audit failed" if k in audit_bad else f"coverage {cov_run[k]:.0%}"
            f.write(f"- block {k[0]:02d} {k[1]}: {why}\n")
    use = rows if a.include_invalid else [r for r in rows if (r["block"], r["arm"]) in valid]
    plt = setup_mpl()
    fig_quality(plt, cov_run, arms, blocks, a.min_coverage, a.out)
    tables(use, arms, afs, a.out)
    made = []
    if use:
        if a.block is None:
            def richness(b):
                return sum(len(raws[(b, x)]["episodes"]) for x in arms if (b, x) in raws and (b, x) in valid)
            cand = [b for b in blocks if all((b, x) in valid for x in arms if (b, x) in raws)] or blocks
            a.block = max(cand, key=richness)
        made.append(fig_timeline(plt, raws, valid, arms, a.block, a.out))
        made.append(fig_per_af_paired(plt, use, arms, afs, "exposure_s_per_episode",
                                      "inadequate-mode exposure per episode (s)",
                                      "Primary KPI per AF: time spent in an inadequate mode",
                                      "fig2_exposure_per_af", a.out))
        made.append(fig_per_af_paired(plt, use, arms, afs, "utility_loss_per_min",
                                      "utility loss (utility-s / min)",
                                      "Cost per AF: utility lost while in the fallback mode",
                                      "fig2b_utility_loss_per_af", a.out))
        fig_tradeoff(plt, use, arms, afs, a.out)
        fig_heatmap(plt, use, arms, afs, "time_in_primary",
                    "Share of time each AF spent in its primary (remote) mode", "fig4_time_in_remote", a.out)
        fig_leads(plt, use, arms, a.out)
    print(json.dumps({"runs": len(cov_run), "valid": len(valid), "invalid": len(invalid),
                      "timeline_block": a.block, "out": a.out}, indent=1))
    if len(valid) < 0.8 * len(cov_run):
        print(f"WARNING: only {len(valid)}/{len(cov_run)} runs are valid - see data_quality.md / "
              f"fig6_data_quality. Results from this campaign are NOT conclusive.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
