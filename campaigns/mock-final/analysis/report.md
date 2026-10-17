# Benchmark analysis

Blocks: 3 — arms: direct_nef, independent_pred, oracle, prenef_dtip, prenef_noai

Primary KPI: inadequate-mode exposure per episode (s). Headline comparison: prenef_dtip vs independent_pred.

Oracle capture ratio (share of the achievable exposure reduction obtained by prenef_dtip): 0.28 over 2 blocks

## Means per arm

| KPI | direct_nef | independent_pred | oracle | prenef_dtip | prenef_noai |
|---|---|---|---|---|---|
| Inadequate-mode exposure per episode (s) [PRIMARY] | 2.739 (n=3) | 2.197 (n=3) | 1.416 (n=3) | 2.196 (n=3) | 2.753 (n=3) |
| Exposure, shared-service episodes (s) | 2.815 (n=2) | 2.630 (n=2) | 0.127 (n=2) | 2.542 (n=2) | 2.540 (n=2) |
| Exposure, single-UE episodes (s) | 2.752 (n=2) | 1.250 (n=2) | 2.997 (n=2) | 1.499 (n=2) | 3.000 (n=2) |
| Timely adaptation rate (eq. 26) | 0.444 (n=3) | 0.444 (n=3) | 0.833 (n=3) | 0.444 (n=3) | 0.444 (n=3) |
| Timely adaptation, shared episodes | 0.000 (n=2) | 0.000 (n=2) | 0.750 (n=2) | 0.000 (n=2) | 0.000 (n=2) |
| Timely adaptation, single-UE episodes | 1.000 (n=2) | 1.000 (n=2) | 1.000 (n=2) | 1.000 (n=2) | 1.000 (n=2) |
| Correlated coverage (all affected AFs in time) | 0.000 (n=2) | 0.000 (n=2) | 0.750 (n=2) | 0.000 (n=2) | 0.000 (n=2) |
| Median lead before onset (s) | -1.144 (n=3) | -0.924 (n=3) | 0.583 (n=3) | -0.866 (n=3) | -1.176 (n=3) |
| Unnecessary transitions (false alarms) | 0.667 (n=3) | 0.667 (n=3) | 0.667 (n=3) | 1.000 (n=3) | 0.667 (n=3) |
| Utility loss per minute (J2, eq. 21) | 11.262 (n=3) | 12.158 (n=3) | 13.155 (n=3) | 12.908 (n=3) | 11.255 (n=3) |
| Calibration error (eq. 27) | — | 0.217 (n=3) | — | 0.199 (n=3) | — |
| Abstention rate (eq. 19) | — | 0.000 (n=3) | — | 0.000 (n=3) | — |
| NEF submission rate (eq. 28) | 0.111 (n=3) | 0.114 (n=3) | 0.101 (n=3) | 0.108 (n=3) | 0.106 (n=3) |
| PReNEF coordination overhead (ms) | 74.749 (n=3) | 75.284 (n=3) | 73.519 (n=3) | 233.173 (n=3) | 368.649 (n=3) |
| Burst deadline miss fraction | 0.000 (n=3) | 0.000 (n=3) | 0.000 (n=3) | 0.000 (n=3) | 0.000 (n=3) |
| Evidenced allocation fraction (eq. 17) | 0.764 (n=3) | 0.884 (n=3) | 0.952 (n=3) | 0.963 (n=3) | 0.725 (n=3) |
| Tick-based inadequacy rate (sanity) | 0.039 (n=3) | 0.029 (n=3) | 0.018 (n=3) | 0.028 (n=3) | 0.037 (n=3) |
| Median network latency (sanity, not headline) | 20.000 (n=3) | 20.000 (n=3) | 20.000 (n=3) | 20.000 (n=3) | 20.000 (n=3) |

## Paired comparisons (A − B, Holm-adjusted Wilcoxon)

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) | favours |
|---|---|---|---|---|---|---|
| exposure_s_per_episode | prenef_dtip vs independent_pred | 3 | -0.0003 | [-0.1467, +0.1486] | 1.0000 | none |
| exposure_s_per_episode | prenef_dtip vs direct_nef | 3 | -0.5423 | [-0.8484, -0.2710] | 1.0000 | none |
| exposure_s_per_episode | prenef_dtip vs prenef_noai | 3 | -0.5566 | [-1.0031, -0.0103] | 1.0000 | none |
| exposure_s_per_episode | prenef_noai vs direct_nef | 3 | +0.0143 | [-0.2607, +0.4955] | 1.0000 | none |
| exposure_s_per_episode | independent_pred vs direct_nef | 3 | -0.5421 | [-0.9970, -0.1243] | 1.0000 | none |
| exposure_s_per_episode | oracle vs prenef_dtip | 3 | -0.7804 | [-2.3504, +0.9960] | 1.0000 | none |
| timely_adaptation_rate | prenef_dtip vs independent_pred | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate | prenef_dtip vs direct_nef | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate | prenef_dtip vs prenef_noai | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate | prenef_noai vs direct_nef | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate | independent_pred vs direct_nef | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate | oracle vs prenef_dtip | 3 | +0.3889 | [+0.0000, +0.6667] | 1.0000 | none |
| lead_s_median | prenef_dtip vs independent_pred | 3 | +0.0580 | [-0.0022, +0.1726] | 1.0000 | none |
| lead_s_median | prenef_dtip vs direct_nef | 3 | +0.2780 | [+0.0092, +0.4824] | 1.0000 | none |
| lead_s_median | prenef_dtip vs prenef_noai | 3 | +0.3103 | [-0.0683, +0.9986] | 1.0000 | none |
| lead_s_median | prenef_noai vs direct_nef | 3 | -0.0323 | [-0.5162, +0.4106] | 1.0000 | none |
| lead_s_median | independent_pred vs direct_nef | 3 | +0.2200 | [+0.0055, +0.4846] | 1.0000 | none |
| lead_s_median | oracle vs prenef_dtip | 3 | +1.4485 | [-0.9902, +2.9879] | 1.0000 | none |
| unnecessary_transitions | prenef_dtip vs independent_pred | 3 | +0.3333 | [+0.0000, +1.0000] | 1.0000 | none |
| unnecessary_transitions | prenef_dtip vs direct_nef | 3 | +0.3333 | [+0.0000, +1.0000] | 1.0000 | none |
| unnecessary_transitions | prenef_dtip vs prenef_noai | 3 | +0.3333 | [+0.0000, +1.0000] | 1.0000 | none |
| unnecessary_transitions | prenef_noai vs direct_nef | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| unnecessary_transitions | independent_pred vs direct_nef | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| unnecessary_transitions | oracle vs prenef_dtip | 3 | -0.3333 | [-1.0000, +0.0000] | 1.0000 | none |
| utility_loss_per_min | prenef_dtip vs independent_pred | 3 | +0.7501 | [+0.1799, +1.4712] | 1.0000 | none |
| utility_loss_per_min | prenef_dtip vs direct_nef | 3 | +1.6462 | [+0.3159, +3.2545] | 1.0000 | none |
| utility_loss_per_min | prenef_dtip vs prenef_noai | 3 | +1.6533 | [+0.6778, +2.9280] | 1.0000 | none |
| utility_loss_per_min | prenef_noai vs direct_nef | 3 | -0.0071 | [-0.3618, +0.3265] | 1.0000 | none |
| utility_loss_per_min | independent_pred vs direct_nef | 3 | +0.8961 | [+0.1360, +1.7833] | 1.0000 | none |
| utility_loss_per_min | oracle vs prenef_dtip | 3 | +0.2470 | [-1.6238, +2.8602] | 1.0000 | none |
| calibration_error | prenef_dtip vs independent_pred | 3 | -0.0185 | [-0.0834, +0.0273] | 1.0000 | none |
| abstention_rate | prenef_dtip vs independent_pred | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| nef_submission_rate_per_s | prenef_dtip vs independent_pred | 3 | -0.0052 | [-0.0309, +0.0154] | 1.0000 | none |
| nef_submission_rate_per_s | prenef_dtip vs direct_nef | 3 | -0.0024 | [-0.0275, +0.0185] | 1.0000 | none |
| nef_submission_rate_per_s | prenef_dtip vs prenef_noai | 3 | +0.0026 | [-0.0125, +0.0185] | 1.0000 | none |
| nef_submission_rate_per_s | prenef_noai vs direct_nef | 3 | -0.0050 | [-0.0150, +0.0000] | 1.0000 | none |
| nef_submission_rate_per_s | independent_pred vs direct_nef | 3 | +0.0028 | [+0.0019, +0.0034] | 1.0000 | none |
| nef_submission_rate_per_s | oracle vs prenef_dtip | 3 | -0.0076 | [-0.0184, -0.0018] | 1.0000 | none |
| coordination_overhead_ms | prenef_dtip vs independent_pred | 3 | +157.8887 | [-9.6092, +481.9976] | 1.0000 | none |
| coordination_overhead_ms | prenef_dtip vs direct_nef | 3 | +158.4241 | [-5.7839, +478.6211] | 1.0000 | none |
| coordination_overhead_ms | prenef_dtip vs prenef_noai | 3 | -135.4759 | [-234.7426, +51.8870] | 1.0000 | none |
| coordination_overhead_ms | prenef_noai vs direct_nef | 3 | +293.9000 | [+226.0073, +426.7340] | 1.0000 | none |
| coordination_overhead_ms | independent_pred vs direct_nef | 3 | +0.5354 | [-7.0616, +12.0443] | 1.0000 | none |
| coordination_overhead_ms | oracle vs prenef_dtip | 3 | -159.6538 | [-489.2541, +9.6886] | 1.0000 | none |
| burst_deadline_miss_fraction | prenef_dtip vs independent_pred | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | prenef_dtip vs direct_nef | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | prenef_dtip vs prenef_noai | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | prenef_noai vs direct_nef | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | independent_pred vs direct_nef | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | oracle vs prenef_dtip | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | prenef_dtip vs independent_pred | 3 | +0.0787 | [+0.0000, +0.2222] | 1.0000 | none |
| allocated_fraction | prenef_dtip vs direct_nef | 3 | +0.1991 | [+0.0000, +0.3333] | 1.0000 | none |
| allocated_fraction | prenef_dtip vs prenef_noai | 3 | +0.2380 | [+0.1389, +0.3750] | 1.0000 | none |
| allocated_fraction | prenef_noai vs direct_nef | 3 | -0.0389 | [-0.2000, +0.1250] | 1.0000 | none |
| allocated_fraction | independent_pred vs direct_nef | 3 | +0.1204 | [+0.0000, +0.2500] | 1.0000 | none |
| allocated_fraction | oracle vs prenef_dtip | 3 | -0.0106 | [-0.1429, +0.1111] | 1.0000 | none |
| mode_inadequacy_rate | prenef_dtip vs independent_pred | 3 | -0.0007 | [-0.0021, +0.0000] | 1.0000 | none |
| mode_inadequacy_rate | prenef_dtip vs direct_nef | 3 | -0.0104 | [-0.0187, -0.0021] | 1.0000 | none |
| mode_inadequacy_rate | prenef_dtip vs prenef_noai | 3 | -0.0090 | [-0.0167, -0.0042] | 1.0000 | none |
| mode_inadequacy_rate | prenef_noai vs direct_nef | 3 | -0.0014 | [-0.0042, +0.0021] | 1.0000 | none |
| mode_inadequacy_rate | independent_pred vs direct_nef | 3 | -0.0097 | [-0.0187, -0.0021] | 1.0000 | none |
| mode_inadequacy_rate | oracle vs prenef_dtip | 3 | -0.0104 | [-0.0333, +0.0042] | 1.0000 | none |
| net_latency_ms_median | prenef_dtip vs independent_pred | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| net_latency_ms_median | prenef_dtip vs direct_nef | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| net_latency_ms_median | prenef_dtip vs prenef_noai | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| net_latency_ms_median | prenef_noai vs direct_nef | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| net_latency_ms_median | independent_pred vs direct_nef | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| net_latency_ms_median | oracle vs prenef_dtip | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |

Notes: HTTP 201 is not counted as allocation; `allocated_fraction` uses evidence (eq. 17). Mock-mode campaigns validate the pipeline only and are not network results.
