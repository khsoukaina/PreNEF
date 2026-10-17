# Benchmark analysis

Blocks: 10 — arms: prenef_dtip, prenef_dtip_eta0, prenef_dtip_nofanout, prenef_dtip_nogate

Primary KPI: inadequate-mode exposure per episode (s). Headline comparison: prenef_dtip vs independent_pred.

## Means per arm

| KPI | prenef_dtip | prenef_dtip_eta0 | prenef_dtip_nofanout | prenef_dtip_nogate |
|---|---|---|---|---|
| Inadequate-mode exposure per episode (s) [PRIMARY] | 0.262 (n=10) | 0.320 (n=10) | 0.277 (n=10) | 0.261 (n=10) |
| Exposure, shared-service episodes (s) | 0.000 (n=10) | 0.075 (n=10) | 0.024 (n=10) | 0.000 (n=10) |
| Exposure, single-UE episodes (s) | 0.813 (n=10) | 0.815 (n=10) | 0.815 (n=10) | 0.843 (n=10) |
| Timely adaptation rate (eq. 26) | 0.449 (n=10) | 0.523 (n=10) | 0.402 (n=10) | 0.429 (n=10) |
| Timely adaptation, shared episodes | 0.523 (n=10) | 0.662 (n=10) | 0.508 (n=10) | 0.583 (n=10) |
| Timely adaptation, single-UE episodes | 0.253 (n=10) | 0.257 (n=10) | 0.312 (n=10) | 0.170 (n=10) |
| Correlated coverage (all affected AFs in time) | 0.498 (n=10) | 0.645 (n=10) | 0.362 (n=10) | 0.560 (n=10) |
| Median lead before onset (s) | -0.063 (n=10) | 0.024 (n=10) | -0.066 (n=10) | 0.007 (n=10) |
| Unnecessary transitions (false alarms) | 3.600 (n=10) | 3.900 (n=10) | 2.300 (n=10) | 3.400 (n=10) |
| Utility loss per minute (J2, eq. 21) | 18.078 (n=10) | 18.399 (n=10) | 17.190 (n=10) | 18.156 (n=10) |
| Calibration error (eq. 27) | 0.452 (n=10) | 0.452 (n=10) | 0.463 (n=10) | 0.455 (n=10) |
| Calibration error, sample-weighted ECE | 0.043 (n=10) | 0.042 (n=10) | 0.045 (n=10) | 0.045 (n=10) |
| Abstention rate (eq. 19) | 0.000 (n=10) | 0.000 (n=10) | 0.000 (n=10) | 0.000 (n=10) |
| NEF submission rate (eq. 28) | 0.099 (n=10) | 0.101 (n=10) | 0.092 (n=10) | 0.098 (n=10) |
| PReNEF coordination overhead (ms) | 46.498 (n=10) | 48.385 (n=10) | 43.490 (n=10) | 51.823 (n=10) |
| Burst deadline miss fraction | 0.000 (n=10) | 0.000 (n=10) | 0.000 (n=10) | 0.000 (n=10) |
| Evidenced allocation fraction (eq. 17, data plane) | 0.000 (n=10) | 0.000 (n=10) | 0.000 (n=10) | 0.000 (n=10) |
| Control-plane allocation fraction (PCF->SMF->PFCP) | 0.000 (n=10) | 0.000 (n=10) | 0.000 (n=10) | 0.000 (n=10) |
| Tick-based inadequacy rate (sanity) | 0.004 (n=10) | 0.005 (n=10) | 0.004 (n=10) | 0.004 (n=10) |
| Median network latency (sanity, not headline) | 2.046 (n=10) | 2.158 (n=10) | 2.067 (n=10) | 2.104 (n=10) |

## Paired comparisons (A − B, Holm-adjusted Wilcoxon)

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) | favours |
|---|---|---|---|---|---|---|
| exposure_s_per_episode | prenef_dtip vs prenef_dtip_eta0 | 10 | -0.0580 | [-0.1381, +0.0156] | 1.0000 | none |
| exposure_s_per_episode | prenef_dtip vs prenef_dtip_nogate | 10 | +0.0006 | [-0.0472, +0.0509] | 1.0000 | none |
| exposure_s_per_episode | prenef_dtip vs prenef_dtip_nofanout | 10 | -0.0149 | [-0.0676, +0.0358] | 1.0000 | none |
| exposure_s_per_episode_shared | prenef_dtip vs prenef_dtip_eta0 | 10 | -0.0754 | [-0.1623, +0.0000] | 0.7500 | none |
| exposure_s_per_episode_shared | prenef_dtip vs prenef_dtip_nogate | 10 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| exposure_s_per_episode_shared | prenef_dtip vs prenef_dtip_nofanout | 10 | -0.0237 | [-0.0612, +0.0000] | 1.0000 | none |
| exposure_s_per_episode_ue | prenef_dtip vs prenef_dtip_eta0 | 10 | -0.0015 | [-0.1223, +0.1379] | 1.0000 | none |
| exposure_s_per_episode_ue | prenef_dtip vs prenef_dtip_nogate | 10 | -0.0295 | [-0.2041, +0.1484] | 1.0000 | none |
| exposure_s_per_episode_ue | prenef_dtip vs prenef_dtip_nofanout | 10 | -0.0015 | [-0.1567, +0.1408] | 1.0000 | none |
| timely_adaptation_rate | prenef_dtip vs prenef_dtip_eta0 | 10 | -0.0742 | [-0.2506, +0.1063] | 1.0000 | none |
| timely_adaptation_rate | prenef_dtip vs prenef_dtip_nogate | 10 | +0.0198 | [-0.2323, +0.2679] | 1.0000 | none |
| timely_adaptation_rate | prenef_dtip vs prenef_dtip_nofanout | 10 | +0.0470 | [-0.0993, +0.1951] | 1.0000 | none |
| timely_adaptation_rate_shared | prenef_dtip vs prenef_dtip_eta0 | 10 | -0.1389 | [-0.3579, +0.0992] | 1.0000 | none |
| timely_adaptation_rate_shared | prenef_dtip vs prenef_dtip_nogate | 10 | -0.0592 | [-0.4150, +0.2850] | 1.0000 | none |
| timely_adaptation_rate_shared | prenef_dtip vs prenef_dtip_nofanout | 10 | +0.0150 | [-0.2400, +0.2500] | 1.0000 | none |
| timely_adaptation_rate_ue | prenef_dtip vs prenef_dtip_eta0 | 10 | -0.0033 | [-0.1750, +0.1250] | 1.0000 | none |
| timely_adaptation_rate_ue | prenef_dtip vs prenef_dtip_nogate | 10 | +0.0833 | [-0.1500, +0.3500] | 1.0000 | none |
| timely_adaptation_rate_ue | prenef_dtip vs prenef_dtip_nofanout | 10 | -0.0583 | [-0.2083, +0.0417] | 1.0000 | none |
| correlated_coverage_rate | prenef_dtip vs prenef_dtip_eta0 | 10 | -0.1467 | [-0.3550, +0.0733] | 0.8539 | none |
| correlated_coverage_rate | prenef_dtip vs prenef_dtip_nogate | 10 | -0.0617 | [-0.4150, +0.2800] | 0.8539 | none |
| correlated_coverage_rate | prenef_dtip vs prenef_dtip_nofanout | 10 | +0.1367 | [-0.1100, +0.3733] | 0.8539 | none |
| lead_s_median | prenef_dtip vs prenef_dtip_eta0 | 10 | -0.0871 | [-0.3353, +0.1430] | 1.0000 | none |
| lead_s_median | prenef_dtip vs prenef_dtip_nogate | 10 | -0.0701 | [-0.3378, +0.1785] | 1.0000 | none |
| lead_s_median | prenef_dtip vs prenef_dtip_nofanout | 10 | +0.0037 | [-0.1780, +0.1869] | 1.0000 | none |
| unnecessary_transitions | prenef_dtip vs prenef_dtip_eta0 | 10 | -0.3000 | [-1.2000, +0.4000] | 0.8501 | none |
| unnecessary_transitions | prenef_dtip vs prenef_dtip_nogate | 10 | +0.2000 | [+0.0000, +0.5000] | 0.6916 | none |
| unnecessary_transitions | prenef_dtip vs prenef_dtip_nofanout | 10 | +1.3000 | [+0.7000, +1.9000] | 0.0356 | prenef_dtip_nofanout |
| utility_loss_per_min | prenef_dtip vs prenef_dtip_eta0 | 10 | -0.3210 | [-0.7693, +0.0668] | 0.3867 | none |
| utility_loss_per_min | prenef_dtip vs prenef_dtip_nogate | 10 | -0.0775 | [-0.6655, +0.4924] | 0.9219 | none |
| utility_loss_per_min | prenef_dtip vs prenef_dtip_nofanout | 10 | +0.8886 | [+0.3852, +1.4142] | 0.0586 | none |
| calibration_error | prenef_dtip vs prenef_dtip_eta0 | 10 | -0.0002 | [-0.0376, +0.0327] | 1.0000 | none |
| calibration_error | prenef_dtip vs prenef_dtip_nogate | 10 | -0.0030 | [-0.0182, +0.0135] | 1.0000 | none |
| calibration_error | prenef_dtip vs prenef_dtip_nofanout | 10 | -0.0117 | [-0.0424, +0.0177] | 1.0000 | none |
| calibration_error_weighted | prenef_dtip vs prenef_dtip_eta0 | 10 | +0.0009 | [-0.0041, +0.0062] | 0.9219 | none |
| calibration_error_weighted | prenef_dtip vs prenef_dtip_nogate | 10 | -0.0021 | [-0.0069, +0.0027] | 0.8262 | none |
| calibration_error_weighted | prenef_dtip vs prenef_dtip_nofanout | 10 | -0.0024 | [-0.0056, +0.0008] | 0.8262 | none |
| abstention_rate | prenef_dtip vs prenef_dtip_eta0 | 10 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| abstention_rate | prenef_dtip vs prenef_dtip_nogate | 10 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| abstention_rate | prenef_dtip vs prenef_dtip_nofanout | 10 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| nef_submission_rate_per_s | prenef_dtip vs prenef_dtip_eta0 | 10 | -0.0027 | [-0.0076, +0.0006] | 0.7500 | none |
| nef_submission_rate_per_s | prenef_dtip vs prenef_dtip_nogate | 10 | +0.0010 | [-0.0001, +0.0026] | 0.7500 | none |
| nef_submission_rate_per_s | prenef_dtip vs prenef_dtip_nofanout | 10 | +0.0065 | [+0.0038, +0.0093] | 0.0176 | prenef_dtip_nofanout |
| coordination_overhead_ms | prenef_dtip vs prenef_dtip_eta0 | 10 | -1.8871 | [-8.1020, +5.6028] | 0.6445 | none |
| coordination_overhead_ms | prenef_dtip vs prenef_dtip_nogate | 10 | -5.3247 | [-13.2979, +3.1233] | 0.4805 | none |
| coordination_overhead_ms | prenef_dtip vs prenef_dtip_nofanout | 10 | +3.0080 | [-2.0986, +10.0064] | 0.6953 | none |
| burst_deadline_miss_fraction | prenef_dtip vs prenef_dtip_eta0 | 10 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | prenef_dtip vs prenef_dtip_nogate | 10 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | prenef_dtip vs prenef_dtip_nofanout | 10 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | prenef_dtip vs prenef_dtip_eta0 | 10 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | prenef_dtip vs prenef_dtip_nogate | 10 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | prenef_dtip vs prenef_dtip_nofanout | 10 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| cp_allocated_fraction | prenef_dtip vs prenef_dtip_eta0 | 10 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| cp_allocated_fraction | prenef_dtip vs prenef_dtip_nogate | 10 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| cp_allocated_fraction | prenef_dtip vs prenef_dtip_nofanout | 10 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| mode_inadequacy_rate | prenef_dtip vs prenef_dtip_eta0 | 10 | -0.0008 | [-0.0020, +0.0003] | 0.8332 | none |
| mode_inadequacy_rate | prenef_dtip vs prenef_dtip_nogate | 10 | +0.0001 | [-0.0006, +0.0008] | 1.0000 | none |
| mode_inadequacy_rate | prenef_dtip vs prenef_dtip_nofanout | 10 | -0.0002 | [-0.0010, +0.0006] | 1.0000 | none |
| net_latency_ms_median | prenef_dtip vs prenef_dtip_eta0 | 10 | -0.1120 | [-0.1980, -0.0250] | 0.1113 | none |
| net_latency_ms_median | prenef_dtip vs prenef_dtip_nogate | 10 | -0.0585 | [-0.1390, +0.0240] | 0.4419 | none |
| net_latency_ms_median | prenef_dtip vs prenef_dtip_nofanout | 10 | -0.0215 | [-0.1145, +0.0670] | 0.8784 | none |

Notes: HTTP 201 is not counted as allocation; `allocated_fraction` uses evidence (eq. 17). Mock-mode campaigns validate the pipeline only and are not network results.
