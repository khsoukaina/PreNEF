# DTIP base-learner benchmark (test runs: 5; production backend: sklearn_hgb)

Same dataset, split, ensemble size, isotonic calibration and conformal T_safe for every learner; default-like configurations, no per-learner tuning (post-hoc sensitivity analysis).

| Learner | AUROC h=5s [95% CI] | AUROC shared AFs | AP | weighted ECE [95% CI] | Brier | mean AUROC (all h) | T_safe coverage | train (s) | latency p50 / p95 (ms) | native NaN |
|---|---|---|---|---|---|---|---|---|---|---|
| CatBoost | 0.919 [0.914, 0.923] | 0.906 | 0.724 | 0.0196 [0.0120, 0.0287] | 0.0357 | 0.923 | 0.937 | 32 | 15.2 / 18.7 | yes |
| Random forest | 0.914 [0.901, 0.927] | 0.906 | 0.771 | 0.0195 [0.0129, 0.0280] | 0.0351 | 0.922 | 0.948 | 42 | 1740.4 / 2131.3 | no (imputed) |
| XGBoost | 0.914 [0.902, 0.923] | 0.910 | 0.754 | 0.0208 [0.0143, 0.0288] | 0.0350 | 0.922 | 0.934 | 18 | 27.6 / 29.4 | yes |
| **HistGB (sklearn)** (used) | 0.914 [0.898, 0.926] | 0.911 | 0.748 | 0.0192 [0.0132, 0.0270] | 0.0348 | 0.919 | 0.935 | 60 | 419.2 / 479.5 | yes |
| LightGBM | 0.914 [0.899, 0.924] | 0.911 | 0.757 | 0.0190 [0.0126, 0.0267] | 0.0344 | 0.922 | 0.934 | 30 | 40.8 / 45.1 | yes |
| MLP | 0.910 [0.903, 0.917] | 0.887 | 0.710 | 0.0186 [0.0116, 0.0268] | 0.0353 | 0.920 | 0.935 | 91 | 24.6 / 26.5 | no (imputed) |
| Logistic regression | 0.883 [0.859, 0.905] | 0.874 | 0.540 | 0.0162 [0.0137, 0.0212] | 0.0509 | 0.889 | 0.948 | 5 | 24.7 / 26.4 | no (imputed) |

Highest AUROC at h = 5 s: **CatBoost**. Learners whose 95 % CI overlaps the best one (not distinguishable on this test set): CatBoost, Random forest, XGBoost, HistGB (sklearn), LightGBM, MLP.
