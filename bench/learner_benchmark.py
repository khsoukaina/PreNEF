#!/usr/bin/env python3
"""Base-learner benchmark for DTIP: is the gradient-boosted-tree choice justified?

  python3 bench/learner_benchmark.py --campaign campaigns/final3
  python3 bench/learner_benchmark.py --model-root models/dtip-v1 --dataset data/dtip.jsonl --out models/dtip-v1/eval

Everything except the base learner is held fixed: the SAME dataset, the SAME chronological by-run
train/calibration/test split as the production model card, the SAME DTIP pipeline (one classifier
per horizon, bootstrap ensemble, isotonic calibration, monotone F(h), split-conformal T_safe),
model-B feature set. Configurations are default-like with a comparable budget (no per-learner
tuning) -> a post-hoc sensitivity analysis, to be reported as such.
Writes to --out (default <campaign>/paper): figS1_learners (.pdf/.png), learners.md, table_learners.tex, learners.csv
"""
from __future__ import annotations

import argparse
import csv
import functools
import math
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bench.model_eval import find_dataset, find_model_root  # noqa: E402
from bench.paper_figures import COL2, INK, INK2, save, setup  # noqa: E402
from dtip import train as T  # noqa: E402
from dtip.features import FEATURE_NAMES  # noqa: E402
from prenef.common import read_json, read_jsonl  # noqa: E402


def _imputed(est, scale):
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    steps = [SimpleImputer(strategy="median", add_indicator=True)] + ([StandardScaler()] if scale else []) + [est]
    return make_pipeline(*steps)


def learners():
    """name -> (factory(seed), colour, marker, handles NaN natively)"""
    from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.neural_network import MLPClassifier
    L = {
        "Logistic regression": (lambda s: _imputed(LogisticRegression(max_iter=2000, C=1.0), True), "#9aa3ad", "v", False),
        "Random forest": (lambda s: _imputed(RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_leaf=20,
                                                                    n_jobs=-1, random_state=s), False), "#1baf7a", "^", False),
        "MLP": (lambda s: _imputed(MLPClassifier(hidden_layer_sizes=(64, 32), early_stopping=True, max_iter=300,
                                                 random_state=s), True), "#6250d6", "P", False),
        "HistGB (sklearn)": (lambda s: HistGradientBoostingClassifier(max_iter=300, max_depth=4, learning_rate=0.08,
                                                                      random_state=s), "#eda100", "s", True),
    }
    try:
        from xgboost import XGBClassifier
        L["XGBoost"] = (lambda s: XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.08, tree_method="hist",
                                                verbosity=0, random_state=s, n_jobs=4), "#e34948", "D", True)
    except ImportError:
        pass
    try:
        from lightgbm import LGBMClassifier
        L["LightGBM"] = (lambda s: LGBMClassifier(n_estimators=300, max_depth=4, learning_rate=0.08, verbose=-1,
                                                  random_state=s), "#eb6834", "X", True)
    except ImportError:
        pass
    try:
        from catboost import CatBoostClassifier
        L["CatBoost"] = (lambda s: CatBoostClassifier(iterations=300, depth=4, learning_rate=0.08, verbose=False,
                                                      random_seed=s, allow_writing_files=False, thread_count=4),
                         "#2a78d6", "o", True)
    except ImportError:
        pass
    return L


def auroc(p, y):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else math.nan


def aprec(p, y):
    from sklearn.metrics import average_precision_score
    return float(average_precision_score(y, p)) if 0 < y.sum() < len(y) else math.nan


def metrics_at(F, Tt, Ct, j):
    y, known = T.labels(Tt, Ct, T.HORIZONS[j])
    p, yy = F[known, j], y[known]
    return {"auroc": auroc(p, yy), "ap": aprec(p, yy), "ece": T.ece_weighted(p, yy) if len(p) else math.nan,
            "brier": float(np.mean((p - yy) ** 2)) if len(p) else math.nan, "pos": int(yy.sum())}


def run_bootstrap(F, Tt, Ct, run_ids, j, B=300, seed=0):
    rng = np.random.default_rng(seed)
    runs = np.unique(run_ids)
    idx_by = {r: np.nonzero(run_ids == r)[0] for r in runs}
    au, ec = [], []
    for _ in range(B):
        pick = np.concatenate([idx_by[r] for r in rng.choice(runs, len(runs), replace=True)])
        m = metrics_at(F[pick], Tt[pick], Ct[pick], j)
        au.append(m["auroc"])
        ec.append(m["ece"])
    q = lambda v: (float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5)))  # noqa: E731
    return q(au), q(ec)


def latency_ms(model, X, n=200, seed=0):
    rng = np.random.default_rng(seed)
    rows = X[rng.integers(0, len(X), n)]
    model.predict(rows[:1])
    ts = []
    for r in rows:
        t0 = time.perf_counter()
        model.predict(r[None, :])
        ts.append((time.perf_counter() - t0) * 1e3)
    return float(np.median(ts)), float(np.percentile(ts, 95))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign")
    ap.add_argument("--model-root")
    ap.add_argument("--dataset")
    ap.add_argument("--out", default=None)
    ap.add_argument("--learners", default="", help="comma subset of names (default: all available)")
    ap.add_argument("--n-ens", type=int, default=5, help="bootstrap ensemble size (production: 5)")
    ap.add_argument("--max-train-rows", type=int, default=80000, help="subsample train rows (same for all learners)")
    ap.add_argument("--horizon", type=float, default=5.0)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    root = a.model_root or (find_model_root(a.campaign) if a.campaign else None)
    card_p = os.path.join(root or "", "variants", "B_shared_services", "model_card.json")
    if not root or not os.path.exists(card_p):
        print(f"model card not found under {root}; pass --model-root", file=sys.stderr)
        return 1
    card = read_json(card_p)
    ds = a.dataset or find_dataset(card)
    if not ds:
        print("dataset not found by sha256; pass --dataset", file=sys.stderr)
        return 1
    out = a.out or (os.path.join(a.campaign, "paper") if a.campaign else os.path.join(root, "eval"))
    os.makedirs(out, exist_ok=True)
    prod_backend = card.get("results", {}).get("B_shared_services", {}).get("backend", "?")
    prod_name = {"catboost": "CatBoost", "sklearn_hgb": "HistGB (sklearn)"}.get(prod_backend, prod_backend)
    print(f"production model backend (from model card): {prod_backend}")
    sp = card["split_by_run_chronological"]
    rows = list(read_jsonl(ds))
    part = {k: [r for r in rows if r["run_id"] in set(sp[k])] for k in ("train", "calib", "test")}
    rng = np.random.default_rng(a.seed)
    if len(part["train"]) > a.max_train_rows:
        keep = rng.choice(len(part["train"]), a.max_train_rows, replace=False)
        part["train"] = [part["train"][i] for i in sorted(keep)]
    (Xtr, Ttr, Ctr), (Xca, Tca, Cca), (Xte, Tte, Cte) = (T.arrays(part[k]) for k in ("train", "calib", "test"))
    run_te = np.array([r["run_id"] for r in part["test"]])
    shared = Xte[:, FEATURE_NAMES.index("n_shared")] > 0
    print(f"train {len(Xtr)} / calib {len(Xca)} / test {len(Xte)} samples ({len(set(sp['test']))} test runs)")
    idx = list(range(len(FEATURE_NAMES)))
    hj = min(range(len(T.HORIZONS)), key=lambda k: abs(T.HORIZONS[k] - a.horizon))
    L = learners()
    if a.learners:
        L = {k: v for k, v in L.items() if k in a.learners.split(",")}
    missing = [n for n in ("XGBoost", "LightGBM", "CatBoost") if n not in L]
    if missing:
        print("not installed (skipped):", ", ".join(missing), " -> pip install catboost xgboost lightgbm")
    res = {}
    orig_make, orig_dtip = T.make_classifier, T.DTIP
    alpha = card.get("alpha", 0.9)
    for name, (factory, *_rest) in L.items():
        print(f"--- {name}: training {len(T.HORIZONS)} horizons x {a.n_ens} ensemble members ...", flush=True)
        T.make_classifier = lambda seed, f=factory, n=name: (f(seed), n)
        T.DTIP = functools.partial(orig_dtip, n_ens=a.n_ens)
        t0 = time.perf_counter()
        try:
            m = T.fit_pipeline(idx, Xtr, Ttr, Ctr, Xca, Tca, Cca, alpha, a.seed, 2.0)
        finally:
            T.make_classifier, T.DTIP = orig_make, orig_dtip
        t_train = time.perf_counter() - t0
        pred = m.predict(Xte, p_horizon_s=T.HORIZONS[hj])
        F = pred["F"]
        per_h = [metrics_at(F, Tte, Cte, j) for j in range(len(T.HORIZONS))]
        per_h_sh = [metrics_at(F[shared], Tte[shared], Cte[shared], j) for j in range(len(T.HORIZONS))]
        (au_lo, au_hi), (ec_lo, ec_hi) = run_bootstrap(F, Tte, Cte, run_te, hj)
        cov, _ = T.coverage(pred["t_safe_s"], Tte, Cte)
        lat50, lat95 = latency_ms(m, Xte)
        ok = [p for p in per_h if p["pos"] >= 30 and not math.isnan(p["auroc"])] or per_h
        res[name] = {"per_h": per_h, "per_h_shared": per_h_sh, "h": per_h[hj], "h_shared": per_h_sh[hj],
                     "auroc_ci": (au_lo, au_hi), "ece_ci": (ec_lo, ec_hi),
                     "mean_auroc": float(np.nanmean([p["auroc"] for p in ok])),
                     "mean_ece": float(np.nanmean([p["ece"] for p in ok])), "coverage": cov,
                     "train_s": t_train, "lat_ms": lat50, "lat95_ms": lat95}
        r = res[name]
        print(f"    AUROC@{T.HORIZONS[hj]:g}s {r['h']['auroc']:.3f} [{au_lo:.3f},{au_hi:.3f}]  shared {r['h_shared']['auroc']:.3f}  "
              f"ECE {r['h']['ece']:.4f}  Brier {r['h']['brier']:.4f}  T_safe cov {cov:.3f}  "
              f"train {t_train:.0f}s  latency {lat50:.1f} ms", flush=True)
    if not res:
        print("no learner ran")
        return 1

    plt = setup()
    fig, axes = plt.subplots(1, 3, figsize=(COL2, 2.4), gridspec_kw={"wspace": 0.42})
    ax = axes[0]
    for name, r in res.items():
        _, col, mk, _ = L[name]
        big = name == prod_name
        ax.errorbar(r["h"]["ece"], r["h"]["auroc"], xerr=[[r["h"]["ece"] - r["ece_ci"][0]], [r["ece_ci"][1] - r["h"]["ece"]]],
                    yerr=[[r["h"]["auroc"] - r["auroc_ci"][0]], [r["auroc_ci"][1] - r["h"]["auroc"]]], fmt=mk, color=col,
                    ms=7 if big else 5, mec=INK if big else "white", mew=0.9 if big else 0.5, elinewidth=0.7, zorder=4 if big else 3)
    ax.set_xlabel("Calibration error, weighted ECE ($\\leftarrow$ better)")
    ax.set_ylabel(f"AUROC at $h$ = {T.HORIZONS[hj]:g} s ($\\uparrow$ better)")
    ax.set_title("(a) Discrimination vs. calibration", loc="left", fontsize=7.3, fontweight="bold")
    ax.grid(axis="both", visible=True)
    ax.text(0.03, 0.97, "best corner", transform=ax.transAxes, ha="left", va="top", fontsize=5.8, color=INK2)
    ax = axes[1]
    for name, r in res.items():
        _, col, mk, _ = L[name]
        hs = [h for h, p in zip(T.HORIZONS, r["per_h_shared"]) if not math.isnan(p["auroc"])]
        ax.plot(hs, [p["auroc"] for p in r["per_h_shared"] if not math.isnan(p["auroc"])], marker=mk, color=col, ms=3.5,
                lw=1.5 if name == prod_name else 0.9, mec="white", mew=0.4, label=name + (" (used)" if name == prod_name else ""))
    ax.axhline(0.5, color=INK2, lw=0.6, ls=":")
    ax.set_xticks(T.HORIZONS)
    ax.set_xlabel("Horizon $h$ (s)")
    ax.set_ylabel("AUROC, shared-dependency AFs")
    ax.set_title("(b) Across horizons", loc="left", fontsize=7.3, fontweight="bold")
    ax.grid(axis="both", visible=True)
    ax = axes[2]
    for name, r in res.items():
        _, col, mk, _ = L[name]
        big = name == prod_name
        ax.plot(r["lat_ms"], r["mean_auroc"], mk, color=col, ms=7 if big else 5, mec=INK if big else "white",
                mew=0.9 if big else 0.5, zorder=4 if big else 3)
    ax.set_xscale("log")
    ax.axvline(500, color="#e34948", lw=0.7, ls="--")
    ax.text(500 * 0.9, 0.97, "budget: one\nbatched call\nper 0.5 s tick", transform=ax.get_xaxis_transform(), fontsize=5.6,
            color="#e34948", va="top", ha="right")
    ax.set_xlabel("Latency of one prediction (ms, log)")
    ax.set_ylabel("Mean AUROC over horizons")
    ax.set_title("(c) Accuracy vs. run-time cost", loc="left", fontsize=7.3, fontweight="bold")
    ax.grid(axis="both", visible=True)
    h_, l_ = axes[1].get_legend_handles_labels()
    fig.legend(h_, l_, ncol=min(4, len(l_)), loc="lower center", bbox_to_anchor=(0.5, 0.98), fontsize=6.4, handlelength=1.6)
    fig.text(0.5, -0.11, "Same data, split, calibration and conformal pipeline for every learner; only the base classifier "
             "changes. Error bars: 95 % CI, bootstrap over test runs. Outlined marker = learner used in PReNEF.",
             ha="center", fontsize=6.0, color=INK2)
    save(fig, out, "figS1_learners")
    plt.close(fig)

    f = lambda x, d=3: "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"  # noqa: E731
    hs = f"{T.HORIZONS[hj]:g}"
    order = sorted(res, key=lambda n: -res[n]["h"]["auroc"] if not math.isnan(res[n]["h"]["auroc"]) else 0)
    md = [f"# DTIP base-learner benchmark (test runs: {len(set(sp['test']))}; production backend: {prod_backend})", "",
          "Same dataset, split, ensemble size, isotonic calibration and conformal T_safe for every learner; "
          "default-like configurations, no per-learner tuning (post-hoc sensitivity analysis).", "",
          f"| Learner | AUROC h={hs}s [95% CI] | AUROC shared AFs | AP | weighted ECE [95% CI] | Brier | mean AUROC (all h) "
          f"| T_safe coverage | train (s) | latency p50 / p95 (ms) | native NaN |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    rows_csv = [["learner", "horizon_s", "auroc", "auroc_lo", "auroc_hi", "auroc_shared", "ap", "ece", "ece_lo", "ece_hi",
                 "brier", "mean_auroc", "coverage", "train_s", "lat_p50_ms", "lat_p95_ms"]]
    for n in order:
        r = res[n]
        md.append(f"| {'**' + n + '** (used)' if n == prod_name else n} | {f(r['h']['auroc'])} [{f(r['auroc_ci'][0])}, "
                  f"{f(r['auroc_ci'][1])}] | {f(r['h_shared']['auroc'])} | {f(r['h']['ap'])} | {f(r['h']['ece'], 4)} "
                  f"[{f(r['ece_ci'][0], 4)}, {f(r['ece_ci'][1], 4)}] | {f(r['h']['brier'], 4)} | {f(r['mean_auroc'])} | "
                  f"{f(r['coverage'])} | {r['train_s']:.0f} | {r['lat_ms']:.1f} / {r['lat95_ms']:.1f} | "
                  f"{'yes' if L[n][3] else 'no (imputed)'} |")
        rows_csv.append([n, T.HORIZONS[hj], r["h"]["auroc"], *r["auroc_ci"], r["h_shared"]["auroc"], r["h"]["ap"],
                         r["h"]["ece"], *r["ece_ci"], r["h"]["brier"], r["mean_auroc"], r["coverage"], r["train_s"],
                         r["lat_ms"], r["lat95_ms"]])
    best = order[0]
    within = [n for n in order if res[n]["auroc_ci"][1] >= res[best]["auroc_ci"][0]]
    md += ["", f"Highest AUROC at h = {hs} s: **{best}**. Learners whose 95 % CI overlaps the best one "
           f"(not distinguishable on this test set): {', '.join(within)}."]
    with open(os.path.join(out, "learners.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    with open(os.path.join(out, "learners.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows(rows_csv)
    tex = ["% requires \\usepackage{booktabs}", "\\begin{table}[t]", "\\centering", "\\footnotesize",
           f"\\caption{{DTIP base learners on held-out test runs, identical pipeline (calibration, ensemble, conformal "
           f"$T_{{safe}}$). AUROC and weighted ECE at $h={hs}$\\,s with 95\\% run-bootstrap CI; latency of one prediction.}}",
           "\\label{tab:learners}", "\\setlength{\\tabcolsep}{3pt}", "\\begin{tabular}{lcccr}", "\\toprule",
           "Learner & AUROC & ECE & $T_{safe}$ cov. & Lat. (ms) \\\\", "\\midrule"]
    for n in order:
        r = res[n]
        nm = f"\\textbf{{{n}}}" if n == prod_name else n
        tex.append(f"{nm} & {f(r['h']['auroc'])} {{\\scriptsize[{f(r['auroc_ci'][0])}, {f(r['auroc_ci'][1])}]}} & "
                   f"{f(r['h']['ece'], 4)} & {f(r['coverage'], 2)} & {r['lat_ms']:.1f} \\\\")
    tex += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    with open(os.path.join(out, "table_learners.tex"), "w") as fh:
        fh.write("\n".join(tex) + "\n")
    print("\n" + "\n".join(md))
    print("\nwrote", out, ": figS1_learners (.pdf/.png), learners.md, learners.csv, table_learners.tex")
    return 0


if __name__ == "__main__":
    sys.exit(main())
