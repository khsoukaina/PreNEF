# DTIP evaluation on held-out test runs (5 runs, 7067 samples)

Model root `models/dtip-lab-v3`, dataset `data/dtip-lab-v3.jsonl`. Split chronological by run (train 60 % / calibration 20 % / test 20 %), no run shared between splits.

## Discrimination and calibration per horizon (all AFs | AFs with a shared dependency)

| h (s) | positives | base rate | AUROC A | AUROC B | AP A | AP B | Brier A | Brier B | ECE A | ECE B |
|---|---|---|---|---|---|---|---|---|---|---|
| **all AFs** |||||||||||
| 1 | 217 | 0.03 | 0.771 | 0.994 | 0.512 | 0.959 | 0.018 | 0.004 | 0.008 | 0.002 |
| 2 | 298 | 0.04 | 0.764 | 0.968 | 0.503 | 0.893 | 0.025 | 0.010 | 0.012 | 0.006 |
| 3 | 379 | 0.06 | 0.740 | 0.950 | 0.479 | 0.836 | 0.033 | 0.018 | 0.014 | 0.012 |
| 5 | 539 | 0.08 | 0.684 | 0.914 | 0.391 | 0.748 | 0.056 | 0.035 | 0.019 | 0.019 |
| 8 | 776 | 0.13 | 0.654 | 0.869 | 0.353 | 0.653 | 0.089 | 0.067 | 0.023 | 0.029 |
| 12 | 1068 | 0.18 | 0.627 | 0.819 | 0.370 | 0.606 | 0.129 | 0.107 | 0.031 | 0.034 |
| **shared-dependency AFs (af1, af2)** |||||||||||
| 1 | 180 | 0.07 | 0.717 | 0.998 | 0.463 | 0.974 | 0.043 | 0.008 | 0.020 | 0.004 |
| 2 | 247 | 0.10 | 0.717 | 0.964 | 0.456 | 0.894 | 0.059 | 0.022 | 0.028 | 0.017 |
| 3 | 312 | 0.12 | 0.687 | 0.941 | 0.455 | 0.835 | 0.079 | 0.041 | 0.037 | 0.032 |
| 5 | 437 | 0.18 | 0.647 | 0.911 | 0.408 | 0.775 | 0.119 | 0.073 | 0.061 | 0.052 |
| 8 | 609 | 0.25 | 0.630 | 0.846 | 0.429 | 0.699 | 0.168 | 0.125 | 0.084 | 0.077 |
| 12 | 804 | 0.33 | 0.612 | 0.750 | 0.492 | 0.660 | 0.213 | 0.183 | 0.109 | 0.083 |

## Operating point used at run time (h = 5 s, p_alert = 0.5)

| Metric | Model A (all) | Model A (shared) | Model B (all) | Model B (shared) |
|---|---|---|---|---|
| Accuracy | 0.941 | 0.866 | 0.957 | 0.907 |
| Balanced accuracy | 0.653 | 0.619 | 0.877 | 0.874 |
| Precision | 0.982 | 1.000 | 0.730 | 0.700 |
| Recall (failures caught) | 0.306 | 0.238 | 0.781 | 0.824 |
| F1 | 0.467 | 0.384 | 0.754 | 0.757 |
| False-alarm rate | 0.001 | 0.000 | 0.026 | 0.075 |
| Accuracy of 'always predict majority' | 0.916 | 0.824 | 0.916 | 0.824 |

Accuracy alone is misleading here: most samples are far from any failure, so always predicting 'no failure' already scores the majority-class accuracy. Use AUROC / AP / recall.

## Conservative safe time T_safe (eq. 9) and uncertainty gate (eq. 19)

| | Model A | Model B |
|---|---|---|
| target coverage α | 0.90 | 0.90 |
| coverage on test (all predictions) | 0.962 | 0.935 |
| coverage when u ≤ u_max | 0.962 | 0.935 |
| fraction kept by the gate | 1.00 | 1.00 |
| u_max | 1.00 | 1.00 |
| conformal correction q (s) | 1.50 | 0.00 |
| mean T_safe (s) | 3.46 | 9.86 |
| qualified (card) | safe-time True, uncertainty True | safe-time True, uncertainty True |

## Permutation importance, model B, h = 5 s (AUROC drop, mean ± sd of 3 shuffles)

| feature | type | AUROC drop |
|---|---|---|
| dependency latency | shared-service | 0.083 ± 0.005 |
| latency slope | per-AF | 0.065 ± 0.002 |
| latency max (window) | per-AF | 0.016 ± 0.001 |
| # AFs sharing dependency | shared-service | 0.013 ± 0.002 |
| dependency latency max | shared-service | 0.008 ± 0.003 |
| dependency down | shared-service | 0.008 ± 0.000 |
| latency (last) | per-AF | 0.007 ± 0.001 |
| dependency latency slope | shared-service | 0.006 ± 0.002 |
| # observations (window) | per-AF | 0.003 ± 0.000 |
| throughput (last) | per-AF | 0.000 ± 0.000 |
| throughput slope | per-AF | 0.000 ± 0.000 |
| observation age | per-AF | 0.000 ± 0.000 |
| loss (last) | per-AF | -0.001 ± 0.001 |
