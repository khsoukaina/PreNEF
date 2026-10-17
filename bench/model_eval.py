#!/usr/bin/env python3
"""Evaluation of the trained DTIP models on the held-out TEST runs (never seen in training/calibration).

  python3 bench/model_eval.py --campaign campaigns/final3
  python3 bench/model_eval.py --model-root models/dtip-v1 --dataset data/dtip.jsonl --out models/dtip-v1/eval

Model A = per-AF features only (= the 'independent_pred' baseline), model B = + shared-service
features (= PReNEF + DTIP). The test split is the one recorded in the model card (chronological,
by run), so these are honest out-of-sample numbers.

Writes to --out (default <campaign>/paper):
  figM1_discrimination  AUROC per horizon (all AFs / shared-dependency AFs) + ROC at the runtime horizon
  figM2_calibration     reliability diagrams (predicted vs observed probability), ECE in the legend
  figM3_safe_time       (a) predicted T_safe vs true time-to-inadequacy, (b) uncertainty gate trade-off
  figM4_importance      permutation importance (AUROC drop) of model B at the runtime horizon
  model_eval.md, table_model.tex, model_eval.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import math
import os
import pickle
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bench.paper_figures import COL1, COL2, INK, INK2, save, setup  # noqa: E402
from dtip.features import FEATURE_NAMES  # noqa: E402
from dtip.train import DEP_FEATURES, HORIZONS, arrays, coverage, ece_weighted, labels  # noqa: E402,F401
from prenef.common import read_json, read_jsonl  # noqa: E402

VAR = {"A_per_af": ("Model A: per-AF features (per-AF predictor)", "#eb6834", "s", "--"),
       "B_shared_services": ("Model B: + shared-service features (DTIP)", "#2a78d6", "o", "-")}
PRETTY = {"lat_last": "latency (last)", "lat_slope": "latency slope", "lat_max_w": "latency max (window)",
          "thr_last": "throughput (last)", "thr_slope": "throughput slope", "loss_last": "loss (last)",
          "obs_age_s": "observation age", "dep_down_any": "dependency down", "dep_lat_last": "dependency latency",
          "dep_lat_slope": "dependency latency slope", "dep_lat_max_w": "dependency latency max",
          "n_shared": "# AFs sharing dependency", "n_obs_w": "# observations (window)"}


def find_model_root(campaign):
    for rt in sorted(glob.glob(os.path.join(campaign, "b*-prenef_dtip", "runtime.json"))):
        md = read_json(rt).get("model_dir")
        if md:
            md = md if os.path.isabs(md) else os.path.join(ROOT, md)
            md = os.path.normpath(md)
            return os.path.dirname(os.path.dirname(md)) if os.path.basename(os.path.dirname(md)) == "variants" else md
    return None


def find_dataset(card):
    want = card.get("dataset_sha256")
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "**", "*.jsonl"), recursive=True)):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() == want:
            return p
    return None


def load_model(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def auroc(p, y):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else math.nan


def aprec(p, y):
    from sklearn.metrics import average_precision_score
    return float(average_precision_score(y, p)) if 0 < y.sum() < len(y) else math.nan


def per_horizon(F, T, C, mask=None):
    out = {}
    for j, h in enumerate(HORIZONS):
        y, known = labels(T, C, h)
        if mask is not None:
            known = known & mask
        p, yy = F[known, j], y[known]
        out[h] = {"n": int(known.sum()), "pos": int(yy.sum()), "auroc": auroc(p, yy), "ap": aprec(p, yy),
                  "brier": float(np.mean((p - yy) ** 2)) if len(p) else math.nan,
                  "ece_w": ece_weighted(p, yy) if len(p) else math.nan,
                  "base_rate": float(yy.mean()) if len(yy) else math.nan}
    return out


def operating_point(p, y, thr):
    pred = p >= thr
    tp, fp = int((pred & (y == 1)).sum()), int((pred & (y == 0)).sum())
    fn, tn = int((~pred & (y == 1)).sum()), int((~pred & (y == 0)).sum())
    prec = tp / (tp + fp) if tp + fp else math.nan
    rec = tp / (tp + fn) if tp + fn else math.nan
    return {"threshold": thr, "accuracy": (tp + tn) / max(1, len(y)), "precision": prec, "recall": rec,
            "f1": 2 * prec * rec / (prec + rec) if prec and rec and not math.isnan(prec + rec) else math.nan,
            "false_alarm_rate": fp / (fp + tn) if fp + tn else math.nan,
            "balanced_accuracy": 0.5 * ((tp / (tp + fn) if tp + fn else 0) + (tn / (tn + fp) if tn + fp else 0)),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn, "majority_class_accuracy": float(max(y.mean(), 1 - y.mean()))}


def reliability(p, y, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    xs, ys, ns = [], [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & ((p < hi) if hi < 1 else (p <= hi))
        if m.sum() >= 10:
            xs.append(p[m].mean())
            ys.append(y[m].mean())
            ns.append(int(m.sum()))
    return np.array(xs), np.array(ys), np.array(ns)


def fig_discrimination(plt, res, F, T, C, shared_mask, hj, out):
    from sklearn.metrics import roc_curve
    fig, axes = plt.subplots(1, 3, figsize=(COL2, 2.2), gridspec_kw={"wspace": 0.38})
    for ax, key, title in ((axes[0], "all", "(a) AUROC, all AFs"),
                           (axes[1], "shared", "(b) AUROC, AFs with a shared dependency")):
        for v, (lab, col, mk, ls) in VAR.items():
            if v not in res:
                continue
            hs = [h for h in HORIZONS if not math.isnan(res[v][key][h]["auroc"])]
            ax.plot(hs, [res[v][key][h]["auroc"] for h in hs], ls=ls, marker=mk, color=col, ms=4,
                    mec="white", mew=0.5, label=lab)
        ax.axhline(0.5, color=INK2, lw=0.6, ls=":")
        ax.text(HORIZONS[-1], 0.51, "chance", ha="right", va="bottom", fontsize=5.8, color=INK2)
        ax.set_xticks(HORIZONS)
        ax.set_xlabel("Horizon $h$ (s)")
        ax.set_ylim(0.45, 1.0)
        ax.grid(axis="both", visible=True)
        ax.set_title(title, loc="left", fontsize=7.3, fontweight="bold")
    ax = axes[2]
    h = HORIZONS[hj]
    y, known = labels(T, C, h)
    m = known & shared_mask
    for v, (lab, col, mk, ls) in VAR.items():
        if v not in F or not (0 < y[m].sum() < m.sum()):
            continue
        fpr, tpr, _ = roc_curve(y[m], F[v][m, hj])
        ax.plot(fpr, tpr, ls=ls, color=col, lw=1.2, label=f"{lab.split(':')[0]} (AUC {res[v]['shared'][h]['auroc']:.2f})")
    ax.plot([0, 1], [0, 1], color=INK2, lw=0.6, ls=":")
    ax.set_xlabel("False-positive rate")
    ax.set_ylabel("True-positive rate")
    ax.set_title(f"(c) ROC at $h$ = {h:g} s, shared AFs", loc="left", fontsize=7.3, fontweight="bold")
    ax.legend(loc="lower right", fontsize=6.0)
    ax.grid(axis="both", visible=True)
    axes[0].set_ylabel("AUROC (test runs)")
    h_, l_ = axes[0].get_legend_handles_labels()
    fig.legend(h_, l_, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.1), fontsize=6.6)
    save(fig, out, "figM1_discrimination")
    plt.close(fig)


def fig_calibration(plt, F, T, C, out, hs=(2.0, 5.0, 8.0)):
    fig, axes = plt.subplots(1, len(hs), figsize=(COL2, 2.35), gridspec_kw={"wspace": 0.3})
    for ax, h in zip(axes, hs):
        j = HORIZONS.index(h)
        y, known = labels(T, C, h)
        ax.plot([0, 1], [0, 1], color=INK2, lw=0.6, ls=":")
        for v, (lab, col, mk, ls) in VAR.items():
            if v not in F:
                continue
            p, yy = F[v][known, j], y[known]
            xs, ys, ns = reliability(p, yy)
            sizes = 6 + 40 * np.sqrt(ns / max(1, ns.max()))
            ax.plot(xs, ys, ls=ls, color=col, lw=1.0)
            ax.scatter(xs, ys, s=sizes, color=col, marker=mk, edgecolor="white", lw=0.4, zorder=3,
                       label=f"{lab.split(':')[0]}: ECE {ece_weighted(p, yy):.3f}")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal")
        ax.grid(axis="both", visible=True)
        ax.set_xlabel("Predicted probability")
        ax.set_title(f"$h$ = {h:g} s  (base rate {np.mean(y[known]):.2f})", loc="left", fontsize=7.3,
                     fontweight="bold")
        ax.legend(loc="upper left", fontsize=5.9, handletextpad=0.3)
    axes[0].set_ylabel("Observed frequency")
    fig.text(0.5, -0.04, "Points on the diagonal = perfectly calibrated; marker size = number of test samples "
             "in the bin (bins with < 10 samples hidden).", ha="center", fontsize=6.0, color=INK2)
    save(fig, out, "figM2_calibration")
    plt.close(fig)


def fig_safe_time(plt, models, preds, T, C, alpha, out):
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.3), gridspec_kw={"wspace": 0.32})
    ax = axes[0]
    ev = ~np.isnan(T)
    bins = [(0, 1), (1, 2), (2, 3), (3, 5), (5, 8), (8, 12)]
    w = 0.34
    for k, (v, (lab, col, mk, ls)) in enumerate(VAR.items()):
        if v not in preds:
            continue
        ts = preds[v]["t_safe_s"]
        for i, (lo, hi) in enumerate(bins):
            m = ev & (T >= lo) & (T < hi)
            if m.sum() < 5:
                continue
            bp = ax.boxplot([ts[m]], positions=[i + (k - 0.5) * w], widths=w * 0.85, whis=(5, 95),
                            showfliers=False, patch_artist=True, medianprops={"color": INK, "lw": 0.8},
                            whiskerprops={"color": INK2, "lw": 0.6}, capprops={"color": INK2, "lw": 0.6})
            bp["boxes"][0].set(facecolor=col, alpha=0.85, edgecolor=INK2, linewidth=0.4)
        cov, _ = coverage(ts, T, C)
        ax.plot([], [], "s", color=col, label=f"{lab.split(':')[0]}: coverage {cov:.2f}")
    for i, (lo, hi) in enumerate(bins):
        ax.plot([i - 0.45, i + 0.45], [lo, lo], color=INK, lw=0.7, ls="--")
    ax.plot([], [], color=INK, lw=0.7, ls="--", label="safe if $T_{safe}$ below this line")
    ax.set_xticks(range(len(bins)))
    ax.set_xticklabels([f"{lo}–{hi}" for lo, hi in bins])
    ax.set_xlabel("True time to inadequacy (s)")
    ax.set_ylabel("Predicted conservative $T_{safe}$ (s)")
    ax.set_title(f"(a) Safe-time prediction (target coverage $\\alpha$ = {alpha:g})", loc="left", fontsize=7.3,
                 fontweight="bold")
    ax.legend(loc="upper left", fontsize=5.9)
    ax = axes[1]
    for v, (lab, col, mk, ls) in VAR.items():
        if v not in preds:
            continue
        u, ts = preds[v]["u"], preds[v]["t_safe_s"]
        grid = np.unique(np.round(np.quantile(u, np.linspace(0.02, 1, 40)), 3))
        covs, kept = [], []
        for g in grid:
            keep = u <= g
            c, n = coverage(ts[keep], T[keep], C[keep])
            covs.append(c if n >= 20 else np.nan)
            kept.append(keep.mean())
        ax.plot(kept, covs, ls=ls, color=col, lw=1.1, label=lab.split(":")[0])
        um = models[v].u_max
        keep = u <= um
        c, _ = coverage(ts[keep], T[keep], C[keep]) if keep.any() else (np.nan, 0)
        ax.plot(keep.mean(), c, mk, color=col, ms=6, mec="white", mew=0.6, zorder=4)
        ax.annotate(f"$u_{{max}}$={um:.2f}", (keep.mean(), c), xytext=(4, -9), textcoords="offset points",
                    fontsize=5.8, color=col)
    ax.axhline(alpha, color=INK, lw=0.6, ls="--")
    ax.text(0.02, alpha + 0.004, f"target {alpha:g}", fontsize=5.8, color=INK, va="bottom")
    ax.set_xlabel("Fraction of predictions kept (u $\\leq$ threshold)")
    ax.set_ylabel("Coverage of $T_{safe}$")
    ax.set_title("(b) Uncertainty gate (eq. 19): trust vs. coverage", loc="left", fontsize=7.3, fontweight="bold")
    ax.grid(axis="both", visible=True)
    ax.legend(loc="lower right", fontsize=5.9)
    save(fig, out, "figM3_safe_time")
    plt.close(fig)


def permutation_importance(model, X, T, C, hj, n_rep=3, max_rows=20000, seed=0):
    rng = np.random.default_rng(seed)
    h = HORIZONS[hj]
    y, known = labels(T, C, h)
    idx = np.nonzero(known)[0]
    if len(idx) > max_rows:
        idx = rng.choice(idx, max_rows, replace=False)
    Xs, ys = X[idx], y[idx]
    base = auroc(model.F(Xs)[0][:, hj], ys)
    res = {}
    for f in sorted(set(model.feature_idx)):
        drops = []
        for _ in range(n_rep):
            Xp = Xs.copy()
            Xp[:, f] = Xp[rng.permutation(len(Xp)), f]
            drops.append(base - auroc(model.F(Xp)[0][:, hj], ys))
        res[FEATURE_NAMES[f]] = (float(np.mean(drops)), float(np.std(drops)))
    return base, res


def fig_importance(plt, imp, out, h):
    items = sorted(imp.items(), key=lambda kv: kv[1][0])
    fig, ax = plt.subplots(figsize=(COL1, 0.22 * len(items) + 0.6))
    for i, (name, (m, s)) in enumerate(items):
        col = "#2a78d6" if name in DEP_FEATURES else "#9aa3ad"
        ax.barh(i, m, 0.7, color=col, xerr=s, error_kw={"elinewidth": 0.6, "ecolor": INK})
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels([PRETTY.get(n, n) for n, _ in items], fontsize=6.5)
    ax.axvline(0, color=INK, lw=0.6)
    ax.grid(axis="x", visible=True)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel(f"AUROC drop when the feature is shuffled ($h$ = {h:g} s)")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color="#2a78d6", label="shared-service (dependency) feature"),
                       Patch(color="#9aa3ad", label="per-AF feature")], loc="lower right", fontsize=6.0)
    save(fig, out, "figM4_importance")
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", help="campaign whose prenef_dtip runs name the model (runtime.json model_dir)")
    ap.add_argument("--model-root", help="training --out-dir (contains variants/A_per_af, variants/B_shared_services)")
    ap.add_argument("--dataset", help="training dataset JSONL (default: found by the sha256 in the model card)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--p-alert", type=float, default=0.5, help="operating threshold for accuracy/precision/recall")
    ap.add_argument("--horizon", type=float, default=5.0, help="runtime horizon p_horizon_s")
    ap.add_argument("--no-importance", action="store_true")
    a = ap.parse_args()
    root = a.model_root or (find_model_root(a.campaign) if a.campaign else None)
    if not root or not os.path.isdir(os.path.join(root, "variants")):
        print(f"model root not found ({root}); pass --model-root models/<name>", file=sys.stderr)
        return 1
    out = a.out or (os.path.join(a.campaign, "paper") if a.campaign else os.path.join(root, "eval"))
    os.makedirs(out, exist_ok=True)
    models, cards = {}, {}
    for v in VAR:
        d = os.path.join(root, "variants", v)
        if os.path.exists(os.path.join(d, "model.pkl")):
            models[v] = load_model(os.path.join(d, "model.pkl"))
            cards[v] = read_json(os.path.join(d, "model_card.json"))
    if not models:
        print("no variant models under", os.path.join(root, "variants"), file=sys.stderr)
        return 1
    card = next(iter(cards.values()))
    ds = a.dataset or find_dataset(card)
    if not ds:
        print("training dataset not found by sha256 under data/; pass --dataset data/<file>.jsonl", file=sys.stderr)
        return 1
    print("model root:", root, "\ndataset   :", ds)
    test_runs = set(card["split_by_run_chronological"]["test"])
    rows = [r for r in read_jsonl(ds) if r["run_id"] in test_runs]
    if not rows:
        print("no test rows: dataset and model card do not match", file=sys.stderr)
        return 1
    X, T, C = arrays(rows)
    shared = X[:, FEATURE_NAMES.index("n_shared")] > 0
    print(f"test split: {len(test_runs)} runs, {len(rows)} samples ({shared.mean():.0%} from AFs with a shared dependency)")
    hj = min(range(len(HORIZONS)), key=lambda k: abs(HORIZONS[k] - a.horizon))
    F, preds, res = {}, {}, {}
    for v, m in models.items():
        p = m.predict(X, p_horizon_s=HORIZONS[hj])
        preds[v], F[v] = p, p["F"]
        res[v] = {"all": per_horizon(F[v], T, C), "shared": per_horizon(F[v], T, C, shared),
                  "indep": per_horizon(F[v], T, C, ~shared)}
        y, known = labels(T, C, HORIZONS[hj])
        res[v]["op_all"] = operating_point(F[v][known, hj], y[known], a.p_alert)
        res[v]["op_shared"] = operating_point(F[v][known & shared, hj], y[known & shared], a.p_alert)
        cov, n = coverage(p["t_safe_s"], T, C)
        keep = p["u"] <= m.u_max
        cov_k, _ = coverage(p["t_safe_s"][keep], T[keep], C[keep]) if keep.any() else (math.nan, 0)
        res[v]["safe"] = {"coverage": cov, "coverage_gated": cov_k, "retained": float(keep.mean()),
                          "conformal_q_s": m.conformal_q, "u_max": m.u_max,
                          "mean_t_safe_s": float(np.mean(p["t_safe_s"])), "alpha": m.alpha,
                          "qualified": cards[v].get("safe_time_qualified"),
                          "unc_qualified": cards[v].get("uncertainty_qualified")}
    plt = setup()
    fig_discrimination(plt, res, F, T, C, shared, hj, out)
    fig_calibration(plt, F, T, C, out)
    alpha = next(iter(models.values())).alpha
    fig_safe_time(plt, models, preds, T, C, alpha, out)
    imp = None
    if not a.no_importance and "B_shared_services" in models:
        print("permutation importance (about 1-3 min)...")
        base, imp = permutation_importance(models["B_shared_services"], X, T, C, hj)
        fig_importance(plt, imp, out, HORIZONS[hj])

    rowsout = [["variant", "subset", "horizon_s", "n", "positives", "base_rate", "auroc", "avg_precision", "brier", "ece_weighted"]]
    md = [f"# DTIP evaluation on held-out test runs ({len(test_runs)} runs, {len(rows)} samples)", "",
          f"Model root `{os.path.relpath(root, ROOT)}`, dataset `{os.path.relpath(ds, ROOT)}`. "
          "Split chronological by run (train 60 % / calibration 20 % / test 20 %), no run shared between splits.", "",
          "## Discrimination and calibration per horizon (all AFs | AFs with a shared dependency)", "",
          "| h (s) | positives | base rate | AUROC A | AUROC B | AP A | AP B | Brier A | Brier B | ECE A | ECE B |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    f = lambda x, d=3: "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"  # noqa: E731
    A, B = res.get("A_per_af"), res.get("B_shared_services")
    for sub in ("all", "shared", "indep"):
        for v in res:
            for h in HORIZONS:
                r = res[v][sub][h]
                rowsout.append([v, sub, h, r["n"], r["pos"], r["base_rate"], r["auroc"], r["ap"], r["brier"], r["ece_w"]])
    for sub, nm in (("all", "all AFs"), ("shared", "shared-dependency AFs (af1, af2)")):
        md.append(f"| **{nm}** |||||||||||")
        for h in HORIZONS:
            ra, rb = (A or B)[sub][h], (B or A)[sub][h]
            md.append(f"| {h:g} | {rb['pos']} | {f(rb['base_rate'], 2)} | {f(A[sub][h]['auroc']) if A else '–'} | "
                      f"{f(B[sub][h]['auroc']) if B else '–'} | {f(A[sub][h]['ap']) if A else '–'} | "
                      f"{f(B[sub][h]['ap']) if B else '–'} | {f(ra['brier'])} | {f(rb['brier'])} | "
                      f"{f(ra['ece_w'])} | {f(rb['ece_w'])} |")
    md += ["", f"## Operating point used at run time (h = {HORIZONS[hj]:g} s, p_alert = {a.p_alert:g})", "",
           "| Metric | " + " | ".join(f"{VAR[v][0].split(':')[0]} ({s})" for v in res for s in ("all", "shared")) + " |",
           "|---|" + "---|" * (2 * len(res))]
    for k, nm in (("accuracy", "Accuracy"), ("balanced_accuracy", "Balanced accuracy"), ("precision", "Precision"),
                  ("recall", "Recall (failures caught)"), ("f1", "F1"), ("false_alarm_rate", "False-alarm rate"),
                  ("majority_class_accuracy", "Accuracy of 'always predict majority'")):
        md.append(f"| {nm} | " + " | ".join(f(res[v][f'op_{s}'][k]) for v in res for s in ("all", "shared")) + " |")
    md += ["", "Accuracy alone is misleading here: most samples are far from any failure, so always predicting "
           "'no failure' already scores the majority-class accuracy. Use AUROC / AP / recall.", "",
           "## Conservative safe time T_safe (eq. 9) and uncertainty gate (eq. 19)", "",
           "| | " + " | ".join(VAR[v][0].split(":")[0] for v in res) + " |", "|---|" + "---|" * len(res)]
    for k, nm, d in (("alpha", "target coverage α", 2), ("coverage", "coverage on test (all predictions)", 3),
                     ("coverage_gated", "coverage when u ≤ u_max", 3), ("retained", "fraction kept by the gate", 2),
                     ("u_max", "u_max", 2), ("conformal_q_s", "conformal correction q (s)", 2),
                     ("mean_t_safe_s", "mean T_safe (s)", 2)):
        md.append(f"| {nm} | " + " | ".join(f(res[v]['safe'][k], d) for v in res) + " |")
    md.append("| qualified (card) | " + " | ".join(f"safe-time {res[v]['safe']['qualified']}, "
                                                 f"uncertainty {res[v]['safe']['unc_qualified']}" for v in res) + " |")
    if imp:
        md += ["", f"## Permutation importance, model B, h = {HORIZONS[hj]:g} s (AUROC drop, mean ± sd of 3 shuffles)", "",
               "| feature | type | AUROC drop |", "|---|---|---|"]
        for n, (m_, s_) in sorted(imp.items(), key=lambda kv: -kv[1][0]):
            md.append(f"| {PRETTY.get(n, n)} | {'shared-service' if n in DEP_FEATURES else 'per-AF'} | {m_:.3f} ± {s_:.3f} |")
    with open(os.path.join(out, "model_eval.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    with open(os.path.join(out, "model_eval.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows(rowsout)
    with open(os.path.join(out, "model_eval.json"), "w") as fh:
        json.dump({v: {k: (vv if k not in ("all", "shared", "indep") else {str(h): x for h, x in vv.items()})
                       for k, vv in r.items()} for v, r in res.items()}, fh, indent=1, default=float)
    tex = ["% requires \\usepackage{booktabs}", "\\begin{table}[t]", "\\centering", "\\footnotesize",
           f"\\caption{{DTIP on held-out test runs ({len(test_runs)} runs): AUROC and sample-weighted ECE per horizon "
           "for model A (per-AF features) and model B (+ shared-service features), all AFs / AFs with a shared dependency.}",
           "\\label{tab:dtip}", "\\setlength{\\tabcolsep}{3pt}", "\\begin{tabular}{rcccccc}", "\\toprule",
           " & \\multicolumn{2}{c}{AUROC (all)} & \\multicolumn{2}{c}{AUROC (shared)} & \\multicolumn{2}{c}{ECE (all)} \\\\",
           "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}",
           "$h$ (s) & A & B & A & B & A & B \\\\", "\\midrule"]
    if A and B:
        for h in HORIZONS:
            tex.append(f"{h:g} & {f(A['all'][h]['auroc'], 2)} & {f(B['all'][h]['auroc'], 2)} & "
                       f"{f(A['shared'][h]['auroc'], 2)} & {f(B['shared'][h]['auroc'], 2)} & "
                       f"{f(A['all'][h]['ece_w'], 3)} & {f(B['all'][h]['ece_w'], 3)} \\\\")
    tex += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    with open(os.path.join(out, "table_model.tex"), "w") as fh:
        fh.write("\n".join(tex) + "\n")
    print("\n".join(md))
    print("\nwrote", out, ": figM1_discrimination, figM2_calibration, figM3_safe_time" +
          (", figM4_importance" if imp else "") + " (.pdf/.png), model_eval.md/.csv/.json, table_model.tex")
    return 0


if __name__ == "__main__":
    sys.exit(main())
