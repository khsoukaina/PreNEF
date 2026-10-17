#!/usr/bin/env python3
"""DTIP — Dependency-aware Time-to-Inadequacy Predictor: training + qualification.

Discrete-horizon formulation of eq. (8):
  F(h) = Pr(T_inad - t <= h)   for h in HORIZONS, one calibrated classifier per h,
  made monotone in h (cumulative max).
Conservative safe time (eq. 9, corrected direction):
  T_safe(t; alpha) = inf{ h : F(h) >= 1 - alpha }
  NOTE: as written in the study, inf{h : F(h) >= alpha} becomes LESS conservative
  when alpha grows. With 1 - alpha, a larger alpha gives a smaller (safer) T_safe,
  matching the stated intent. Fix eq. (9) in the paper accordingly.
Split-conformal correction on a calibration split so that, on held-out runs,
  Pr(T_true >= T_safe_conf) >= alpha  (coverage target).
Uncertainty u in [0,1] (eq. 10) = max(ensemble disagreement, missing-feature
fraction, staleness); u_max chosen on the calibration split (eq. 19).

Splits are BY RUN, chronological: train / calib / test never share a run
(no leakage between correlated samples of the same run).

Ablation (study §0.2.6): model A = per-AF features only, model B = + shared-
service features. Model B is kept only if it improves test calibration/decision
metrics; the card records both.

Outputs: model.pkl, model_card.json (with safe_time_qualified,
uncertainty_qualified, split run ids, data hash, metrics).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dtip.features import FEATURE_NAMES  # noqa: E402
from prenef.common import durable_json, read_jsonl  # noqa: E402

HORIZONS = [1.0, 2.0, 3.0, 5.0, 8.0, 12.0]
DEP_FEATURES = {"dep_down_any", "dep_lat_last", "dep_lat_slope", "dep_lat_max_w", "n_shared"}


def make_classifier(seed: int):
    try:
        from catboost import CatBoostClassifier  # type: ignore
        return CatBoostClassifier(iterations=300, depth=4, learning_rate=0.08, verbose=False,
                                  random_seed=seed, allow_writing_files=False), "catboost"
    except ImportError:
        from sklearn.ensemble import HistGradientBoostingClassifier
        return HistGradientBoostingClassifier(max_iter=300, max_depth=4, learning_rate=0.08,
                                              random_state=seed), "sklearn_hgb"


class _Const:
    """Fallback when a horizon has a single class in training."""
    def __init__(self, p):
        self.p = p

    def predict_proba(self, X):
        return np.column_stack([1 - np.full(len(X), self.p), np.full(len(X), self.p)])


def labels(T: np.ndarray, C: np.ndarray, h: float) -> tuple[np.ndarray, np.ndarray]:
    """y=1 if event within h; known if event observed or censor >= h."""
    event = ~np.isnan(T)
    y = (event & (T <= h)).astype(int)
    known = (event & (T <= h)) | (C >= h)
    return y, known


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10, min_count: int = 1) -> float:
    """Eq. (27): (1/B) sum_b |mean p_b - empirical rate_b| over bins with >= min_count samples.
    min_count=1 is the literal eq. (27); with min_count=30 a bin holding a handful of
    samples cannot dominate the average (its empirical rate is pure noise)."""
    edges = np.linspace(0, 1, bins + 1)
    errs = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & ((p < hi) if hi < 1 else (p <= hi))
        if m.sum() >= min_count:
            errs.append(abs(p[m].mean() - y[m].mean()))
    return float(np.mean(errs)) if errs else float("nan")


def ece_weighted(p, y, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    tot = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & ((p < hi) if hi < 1 else (p <= hi))
        if m.any():
            tot += m.sum() * abs(p[m].mean() - y[m].mean())
    return float(tot / max(1, len(p)))


def auroc(p, y):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else float("nan")


class DTIP:
    def __init__(self, feature_idx: list[int], n_ens: int = 5, seed: int = 0):
        self.feature_idx = feature_idx
        self.n_ens = n_ens
        self.seed = seed
        self.models: dict[float, list] = {}
        self.calibrators: dict[float, object] = {}
        self.backend = None
        self.conformal_q = 0.0
        self.alpha = 0.9
        self.u_max = 1.0
        self.max_obs_age_s = 2.0

    def _X(self, X):
        return X[:, self.feature_idx]

    def fit(self, X, T, C):
        rng = np.random.default_rng(self.seed)
        Xs = self._X(X)
        for h in HORIZONS:
            y, known = labels(T, C, h)
            Xk, yk = Xs[known], y[known]
            ens = []
            for k in range(self.n_ens):
                idx = rng.integers(0, len(Xk), len(Xk))
                Xb, yb = Xk[idx], yk[idx]
                # keep only columns with >= 2 distinct non-NaN values in THIS bootstrap
                # (constant / all-NaN columns crash sklearn's histogram binning)
                cols = [j for j in range(Xb.shape[1])
                        if len(np.unique(Xb[~np.isnan(Xb[:, j]), j])) >= 2]
                if len(np.unique(yb)) < 2 or not cols:
                    ens.append((None, _Const(float(yk.mean()) if len(yk) else 0.0)))
                    continue
                clf, self.backend = make_classifier(self.seed + k)
                clf.fit(Xb[:, cols], yb)
                ens.append((cols, clf))
            self.models[h] = ens
        return self

    def raw_F(self, X):
        Xs = self._X(X)
        means, stds = [], []
        for h in HORIZONS:
            ps = np.column_stack([(m.predict_proba(Xs) if cols is None else m.predict_proba(Xs[:, cols]))[:, 1]
                                  for cols, m in self.models[h]])
            means.append(ps.mean(1))
            stds.append(ps.std(1))
        return np.column_stack(means), np.column_stack(stds)

    def calibrate(self, X, T, C):
        from sklearn.isotonic import IsotonicRegression
        F, _ = self.raw_F(X)
        for j, h in enumerate(HORIZONS):
            y, known = labels(T, C, h)
            if known.sum() >= 20 and 0 < y[known].sum() < known.sum():
                iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
                iso.fit(F[known, j], y[known])
                self.calibrators[h] = iso

    def F(self, X):
        Fr, S = self.raw_F(X)
        out = np.empty_like(Fr)
        for j, h in enumerate(HORIZONS):
            cal = self.calibrators.get(h)
            out[:, j] = cal.predict(Fr[:, j]) if cal is not None else Fr[:, j]
        return np.maximum.accumulate(out, axis=1), S          # monotone in h

    def t_safe_raw(self, F):
        thr = 1.0 - self.alpha
        res = np.full(len(F), HORIZONS[-1])
        for i in range(len(F)):
            hit = np.nonzero(F[i] >= thr)[0]
            if len(hit):
                j = hit[0]
                res[i] = 0.0 if j == 0 else HORIZONS[j - 1]   # last horizon still below threshold
        return res

    def uncertainty(self, X, S):
        Xs = self._X(X)
        disagreement = np.minimum(1.0, S.max(1) / 0.15)
        missing = np.isnan(Xs).mean(1)
        age_col = FEATURE_NAMES.index("obs_age_s")
        age = np.nan_to_num(X[:, age_col], nan=self.max_obs_age_s * 10)
        stale = np.minimum(1.0, age / max(1e-6, self.max_obs_age_s * 2))
        return np.maximum.reduce([disagreement, missing, stale])

    def predict(self, X, p_horizon_s: float = 5.0):
        F, S = self.F(X)
        ts = np.maximum(0.0, self.t_safe_raw(F) - self.conformal_q)
        j = min(range(len(HORIZONS)), key=lambda k: abs(HORIZONS[k] - p_horizon_s))
        return {"p_inad": F[:, j], "t_safe_s": ts, "u": self.uncertainty(X, S), "F": F}


def coverage(ts, T, C):
    event = ~np.isnan(T)
    known = event | (C >= ts)
    covered = np.where(event, T >= ts, True)
    return float(covered[known].mean()) if known.any() else float("nan"), int(known.sum())


def split_runs(rows, fr=(0.6, 0.2, 0.2)):
    starts = {}
    for r in rows:
        starts.setdefault(r["run_id"], r.get("run_start_wall_s") or r["t_wall"])
    runs = sorted(starts, key=lambda k: starts[k])
    n = len(runs)
    a, b = int(round(n * fr[0])), int(round(n * (fr[0] + fr[1])))
    return set(runs[:a]), set(runs[a:b]), set(runs[b:])


def arrays(rows):
    X = np.array([[np.nan if v is None else v for v in r["features"]] for r in rows], dtype=float)
    T = np.array([np.nan if r["t_to_inad_s"] is None else r["t_to_inad_s"] for r in rows], dtype=float)
    C = np.array([r["censor_s"] for r in rows], dtype=float)
    return X, T, C


def evaluate(model: DTIP, X, T, C) -> dict:
    out = model.predict(X)
    F = out["F"]
    per_h = {}
    for j, h in enumerate(HORIZONS):
        y, known = labels(T, C, h)
        p, yy = F[known, j], y[known]
        per_h[str(h)] = {"n": int(known.sum()), "positives": int(yy.sum()),
                         "ece_eq27": ece(p, yy), "ece_eq27_min30": ece(p, yy, min_count=30),
                         "ece_weighted": ece_weighted(p, yy),
                         "bin_counts": np.histogram(p, bins=10, range=(0, 1))[0].tolist(),
                         "brier": float(np.mean((p - yy) ** 2)) if len(p) else float("nan"),
                         "auroc": auroc(p, yy)}
    cov, n_cov = coverage(out["t_safe_s"], T, C)
    keep = out["u"] <= model.u_max
    cov_k, n_k = coverage(out["t_safe_s"][keep], T[keep], C[keep]) if keep.any() else (float("nan"), 0)
    return {"per_horizon": per_h, "t_safe_coverage": cov, "coverage_n": n_cov,
            "coverage_when_u_le_umax": cov_k, "retained_fraction": float(keep.mean()),
            "mean_t_safe_s": float(np.mean(out["t_safe_s"]))}


def fit_pipeline(feature_idx, Xtr, Ttr, Ctr, Xca, Tca, Cca, alpha, seed, max_age):
    m = DTIP(feature_idx, seed=seed)
    m.alpha, m.max_obs_age_s = alpha, max_age
    m.fit(Xtr, Ttr, Ctr)
    m.calibrate(Xca, Tca, Cca)
    # split-conformal on calibration: s = T_safe_raw - T_true for observed events
    F, S = m.F(Xca)
    ts = m.t_safe_raw(F)
    ev = ~np.isnan(Tca)
    scores = np.sort(ts[ev] - Tca[ev])
    if len(scores):
        k = min(len(scores) - 1, int(math.ceil((len(scores) + 1) * alpha)) - 1)
        m.conformal_q = max(0.0, float(scores[max(0, k)]))
    # u_max: largest threshold keeping calibration coverage >= alpha
    u = m.uncertainty(Xca, S)
    tsc = np.maximum(0.0, ts - m.conformal_q)
    best = 0.0
    for thr in np.unique(np.round(u, 3)):
        keep = u <= thr
        cov, n = coverage(tsc[keep], Tca[keep], Cca[keep])
        if n >= 20 and cov >= alpha:
            best = float(thr)
    m.u_max = best
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--alpha", type=float, default=0.9, help="target coverage of T_safe")
    ap.add_argument("--ece-max", type=float, default=0.05)
    ap.add_argument("--ece-metric", choices=["ece_eq27", "ece_eq27_min30", "ece_weighted"], default="ece_eq27",
                    help="calibration gate: literal eq.27, eq.27 over bins with >=30 samples, or "
                         "sample-weighted ECE (Guo et al. 2017). Fix it BEFORE the final campaign.")
    ap.add_argument("--min-positives", type=int, default=30)
    ap.add_argument("--coverage-tol", type=float, default=0.02)
    ap.add_argument("--min-retained", type=float, default=0.5)
    ap.add_argument("--max-obs-age-s", type=float, default=2.0)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rows = list(read_jsonl(a.dataset, strict=True))
    if not rows:
        print("empty dataset", file=sys.stderr)
        return 1
    if rows[0]["feature_names"] != FEATURE_NAMES:
        print("feature schema mismatch: rebuild dataset with the current features.py", file=sys.stderr)
        return 1
    tr, ca, te = split_runs(rows)
    if not (tr and ca and te):
        print(f"need >= 3 runs for a by-run split (got {len({r['run_id'] for r in rows})})", file=sys.stderr)
        return 1
    part = lambda S: arrays([r for r in rows if r["run_id"] in S])  # noqa: E731
    (Xtr, Ttr, Ctr), (Xca, Tca, Cca), (Xte, Tte, Cte) = part(tr), part(ca), part(te)
    idx_all = list(range(len(FEATURE_NAMES)))
    idx_a = [i for i, n in enumerate(FEATURE_NAMES) if n not in DEP_FEATURES]
    results, models = {}, {}
    for name, idx in (("A_per_af", idx_a), ("B_shared_services", idx_all)):
        m = fit_pipeline(idx, Xtr, Ttr, Ctr, Xca, Tca, Cca, a.alpha, a.seed, a.max_obs_age_s)
        models[name] = m
        results[name] = {"backend": m.backend, "conformal_q_s": m.conformal_q, "u_max": m.u_max,
                         "test": evaluate(m, Xte, Tte, Cte), "calib": evaluate(m, Xca, Tca, Cca)}

    def score(r):  # lower is better: worst qualified ECE, then coverage gap
        eces = [v[a.ece_metric] for v in r["test"]["per_horizon"].values()
                if v["positives"] >= a.min_positives and not math.isnan(v[a.ece_metric])]
        return (max(eces) if eces else 1.0, max(0.0, a.alpha - r["test"]["coverage_when_u_le_umax"]
                                                if not math.isnan(r["test"]["coverage_when_u_le_umax"]) else 1.0))

    chosen = "B_shared_services" if score(results["B_shared_services"]) < score(results["A_per_af"]) else "A_per_af"
    with open(a.dataset, "rb") as f:
        dhash = hashlib.sha256(f.read()).hexdigest()

    def write(directory: str, name: str) -> dict:
        """Write one model + card. Each variant gets its OWN qualification:
        A_per_af is the 'independent_pred' baseline, the chosen one serves prenef_dtip."""
        r = results[name]["test"]
        qualified_h = [h for h, v in r["per_horizon"].items() if v["positives"] >= a.min_positives]
        ece_ok = bool(qualified_h) and all(r["per_horizon"][h][a.ece_metric] <= a.ece_max for h in qualified_h)
        cov_ok = (not math.isnan(r["t_safe_coverage"])) and r["t_safe_coverage"] >= a.alpha - a.coverage_tol
        unc_ok = (not math.isnan(r["coverage_when_u_le_umax"])) and \
            r["coverage_when_u_le_umax"] >= a.alpha - a.coverage_tol and r["retained_fraction"] >= a.min_retained
        os.makedirs(directory, exist_ok=True)
        mp = os.path.join(directory, "model.pkl")
        with open(mp, "wb") as f:
            pickle.dump(models[name], f)
        card = {
            "model": "DTIP", "variant": name, "chosen_variant": chosen, "feature_names": FEATURE_NAMES,
            "horizons_s": HORIZONS, "alpha": a.alpha,
            "eq9_direction": "T_safe = inf{h : F(h) >= 1 - alpha} (conservative for large alpha)",
            "dataset_sha256": dhash, "model_sha256": hashlib.sha256(open(mp, "rb").read()).hexdigest(),
            "split_by_run_chronological": {"train": sorted(tr), "calib": sorted(ca), "test": sorted(te)},
            "split_disjoint": not (tr & ca or tr & te or ca & te),
            "gates": {"ece_metric": a.ece_metric, "ece_max": a.ece_max, "min_positives": a.min_positives, "coverage_tol": a.coverage_tol,
                      "min_retained": a.min_retained, "horizons_with_enough_positives": qualified_h},
            "safe_time_qualified": bool(ece_ok and cov_ok),
            "uncertainty_qualified": bool(unc_ok),
            "results": results,
        }
        durable_json(os.path.join(directory, "model_card.json"), card)
        return {"dir": directory, "safe_time_qualified": card["safe_time_qualified"],
                "uncertainty_qualified": card["uncertainty_qualified"], "test_coverage": r["t_safe_coverage"],
                "u_max": results[name]["u_max"], "horizons_qualified": qualified_h}

    summary = {"chosen_for_prenef_dtip": chosen, "prenef_dtip": write(a.out_dir, chosen)}
    for name in models:
        summary[name] = write(os.path.join(a.out_dir, "variants", name), name)
    print(json.dumps(summary, indent=1))
    print(f"\nconfig: model_dir = {a.out_dir}   independent_model_dir = "
          f"{os.path.join(a.out_dir, 'variants', 'A_per_af')}")
    return 0


if __name__ == "__main__":
    # Run through the importable module so pickled classes are 'dtip.train.DTIP',
    # not '__main__.DTIP' (otherwise the runtime cannot unpickle the model).
    from dtip import train as _train
    sys.exit(_train.main())
