# Benchmark analysis

Blocks: 20 — arms: direct_nef, independent_pred, prenef_dtip, prenef_noai

Primary KPI: inadequate-mode exposure per episode (s). Headline comparison: prenef_dtip vs independent_pred.

## Means per arm

| KPI | direct_nef | independent_pred | prenef_dtip | prenef_noai |
|---|---|---|---|---|
| Inadequate-mode exposure per episode (s) [PRIMARY] | 2.721 (n=20) | 2.152 (n=20) | 0.411 (n=20) | 2.579 (n=20) |
| Exposure, shared-service episodes (s) | 2.734 (n=20) | 2.709 (n=20) | 0.226 (n=20) | 2.521 (n=20) |
| Exposure, single-UE episodes (s) | 2.677 (n=20) | 1.000 (n=20) | 1.016 (n=20) | 2.691 (n=20) |
| Timely adaptation rate (eq. 26) | 0.000 (n=20) | 0.073 (n=20) | 0.580 (n=20) | 0.000 (n=20) |
| Timely adaptation, shared episodes | 0.000 (n=20) | 0.000 (n=20) | 0.758 (n=20) | 0.000 (n=20) |
| Timely adaptation, single-UE episodes | 0.000 (n=19) | 0.190 (n=19) | 0.192 (n=19) | 0.000 (n=19) |
| Correlated coverage (all affected AFs in time) | 0.000 (n=20) | 0.000 (n=20) | 0.752 (n=20) | 0.000 (n=20) |
| Median lead before onset (s) | -3.662 (n=20) | -3.430 (n=20) | 0.069 (n=20) | -3.575 (n=20) |
| Unnecessary transitions (false alarms) | 0.000 (n=20) | 0.050 (n=20) | 4.050 (n=20) | 0.000 (n=20) |
| Utility loss per minute (J2, eq. 21) | 11.106 (n=20) | 12.035 (n=20) | 18.404 (n=20) | 11.334 (n=20) |
| Calibration error (eq. 27) | — | 0.332 (n=20) | 0.455 (n=20) | — |
| Calibration error, sample-weighted ECE | — | 0.034 (n=20) | 0.043 (n=20) | — |
| Abstention rate (eq. 19) | — | 0.000 (n=20) | 0.000 (n=20) | — |
| NEF submission rate (eq. 28) | 0.077 (n=20) | 0.078 (n=20) | 0.102 (n=20) | 0.077 (n=20) |
| PReNEF coordination overhead (ms) | 47.546 (n=20) | 48.092 (n=20) | 44.773 (n=20) | 45.967 (n=20) |
| Burst deadline miss fraction | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) |
| Evidenced allocation fraction (eq. 17, data plane) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) |
| Control-plane allocation fraction (PCF->SMF->PFCP) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) |
| Tick-based inadequacy rate (sanity) | 0.039 (n=20) | 0.031 (n=20) | 0.006 (n=20) | 0.037 (n=20) |
| Median network latency (sanity, not headline) | 2.324 (n=20) | 2.286 (n=20) | 2.276 (n=20) | 2.312 (n=20) |

## Paired comparisons (A − B, Holm-adjusted Wilcoxon)

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) | favours |
|---|---|---|---|---|---|---|
| exposure_s_per_episode | prenef_dtip vs independent_pred | 20 | -1.7407 | [-1.9926, -1.4542] | 0.0000 | prenef_dtip |
| exposure_s_per_episode | prenef_dtip vs direct_nef | 20 | -2.3103 | [-2.4445, -2.1501] | 0.0000 | prenef_dtip |
| exposure_s_per_episode | prenef_dtip vs prenef_noai | 20 | -2.1679 | [-2.2936, -2.0127] | 0.0000 | prenef_dtip |
| exposure_s_per_episode | prenef_noai vs direct_nef | 20 | -0.1424 | [-0.1911, -0.0905] | 0.0001 | prenef_noai |
| exposure_s_per_episode | independent_pred vs direct_nef | 20 | -0.5696 | [-0.7150, -0.4338] | 0.0000 | independent_pred |
| exposure_s_per_episode_shared | prenef_dtip vs independent_pred | 20 | -2.4838 | [-2.7073, -2.1616] | 0.0000 | prenef_dtip |
| exposure_s_per_episode_shared | prenef_dtip vs direct_nef | 20 | -2.5083 | [-2.6989, -2.2216] | 0.0000 | prenef_dtip |
| exposure_s_per_episode_shared | prenef_dtip vs prenef_noai | 20 | -2.2952 | [-2.4915, -1.9993] | 0.0000 | prenef_dtip |
| exposure_s_per_episode_shared | prenef_noai vs direct_nef | 20 | -0.2131 | [-0.2546, -0.1648] | 0.0000 | prenef_noai |
| exposure_s_per_episode_shared | independent_pred vs direct_nef | 20 | -0.0245 | [-0.1008, +0.0590] | 0.3884 | none |
| exposure_s_per_episode_ue | prenef_dtip vs independent_pred | 20 | +0.0154 | [-0.0731, +0.1007] | 1.0000 | none |
| exposure_s_per_episode_ue | prenef_dtip vs direct_nef | 20 | -1.6610 | [-1.8538, -1.4401] | 0.0000 | prenef_dtip |
| exposure_s_per_episode_ue | prenef_dtip vs prenef_noai | 20 | -1.6750 | [-1.8846, -1.4410] | 0.0000 | prenef_dtip |
| exposure_s_per_episode_ue | prenef_noai vs direct_nef | 20 | +0.0140 | [-0.0587, +0.0918] | 1.0000 | none |
| exposure_s_per_episode_ue | independent_pred vs direct_nef | 20 | -1.6764 | [-1.8814, -1.4484] | 0.0000 | independent_pred |
| timely_adaptation_rate | prenef_dtip vs independent_pred | 20 | +0.5071 | [+0.4145, +0.5924] | 0.0005 | prenef_dtip |
| timely_adaptation_rate | prenef_dtip vs direct_nef | 20 | +0.5802 | [+0.4977, +0.6569] | 0.0005 | prenef_dtip |
| timely_adaptation_rate | prenef_dtip vs prenef_noai | 20 | +0.5802 | [+0.4977, +0.6569] | 0.0005 | prenef_dtip |
| timely_adaptation_rate | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate | independent_pred vs direct_nef | 20 | +0.0731 | [+0.0361, +0.1138] | 0.0115 | independent_pred |
| timely_adaptation_rate_shared | prenef_dtip vs independent_pred | 20 | +0.7585 | [+0.6405, +0.8644] | 0.0006 | prenef_dtip |
| timely_adaptation_rate_shared | prenef_dtip vs direct_nef | 20 | +0.7585 | [+0.6405, +0.8644] | 0.0006 | prenef_dtip |
| timely_adaptation_rate_shared | prenef_dtip vs prenef_noai | 20 | +0.7585 | [+0.6405, +0.8644] | 0.0006 | prenef_dtip |
| timely_adaptation_rate_shared | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate_shared | independent_pred vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate_ue | prenef_dtip vs independent_pred | 19 | +0.0018 | [-0.0526, +0.0561] | 1.0000 | none |
| timely_adaptation_rate_ue | prenef_dtip vs direct_nef | 19 | +0.1921 | [+0.1096, +0.2781] | 0.0183 | prenef_dtip |
| timely_adaptation_rate_ue | prenef_dtip vs prenef_noai | 19 | +0.1921 | [+0.1096, +0.2781] | 0.0183 | prenef_dtip |
| timely_adaptation_rate_ue | prenef_noai vs direct_nef | 19 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate_ue | independent_pred vs direct_nef | 19 | +0.1904 | [+0.0982, +0.2921] | 0.0183 | independent_pred |
| correlated_coverage_rate | prenef_dtip vs independent_pred | 20 | +0.7525 | [+0.6358, +0.8583] | 0.0006 | prenef_dtip |
| correlated_coverage_rate | prenef_dtip vs direct_nef | 20 | +0.7525 | [+0.6358, +0.8583] | 0.0006 | prenef_dtip |
| correlated_coverage_rate | prenef_dtip vs prenef_noai | 20 | +0.7525 | [+0.6358, +0.8583] | 0.0006 | prenef_dtip |
| correlated_coverage_rate | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| correlated_coverage_rate | independent_pred vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| lead_s_median | prenef_dtip vs independent_pred | 20 | +3.4986 | [+2.9638, +3.9627] | 0.0000 | prenef_dtip |
| lead_s_median | prenef_dtip vs direct_nef | 20 | +3.7315 | [+3.4275, +4.0067] | 0.0000 | prenef_dtip |
| lead_s_median | prenef_dtip vs prenef_noai | 20 | +3.6441 | [+3.3696, +3.8762] | 0.0000 | prenef_dtip |
| lead_s_median | prenef_noai vs direct_nef | 20 | +0.0874 | [-0.0117, +0.1795] | 0.1946 | none |
| lead_s_median | independent_pred vs direct_nef | 20 | +0.2329 | [+0.0139, +0.4860] | 0.2305 | none |
| unnecessary_transitions | prenef_dtip vs independent_pred | 20 | +4.0000 | [+3.2000, +4.8000] | 0.0005 | independent_pred |
| unnecessary_transitions | prenef_dtip vs direct_nef | 20 | +4.0500 | [+3.2500, +4.8000] | 0.0005 | direct_nef |
| unnecessary_transitions | prenef_dtip vs prenef_noai | 20 | +4.0500 | [+3.2500, +4.8000] | 0.0005 | prenef_noai |
| unnecessary_transitions | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| unnecessary_transitions | independent_pred vs direct_nef | 20 | +0.0500 | [+0.0000, +0.1500] | 1.0000 | none |
| utility_loss_per_min | prenef_dtip vs independent_pred | 20 | +6.3687 | [+5.7862, +6.9025] | 0.0000 | independent_pred |
| utility_loss_per_min | prenef_dtip vs direct_nef | 20 | +7.2978 | [+6.8159, +7.7396] | 0.0000 | direct_nef |
| utility_loss_per_min | prenef_dtip vs prenef_noai | 20 | +7.0698 | [+6.6036, +7.4901] | 0.0000 | prenef_noai |
| utility_loss_per_min | prenef_noai vs direct_nef | 20 | +0.2279 | [+0.0881, +0.3617] | 0.0042 | direct_nef |
| utility_loss_per_min | independent_pred vs direct_nef | 20 | +0.9290 | [+0.7678, +1.0945] | 0.0000 | direct_nef |
| calibration_error | prenef_dtip vs independent_pred | 20 | +0.1237 | [+0.0903, +0.1611] | 0.0000 | independent_pred |
| calibration_error_weighted | prenef_dtip vs independent_pred | 20 | +0.0090 | [+0.0033, +0.0145] | 0.0153 | independent_pred |
| abstention_rate | prenef_dtip vs independent_pred | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| nef_submission_rate_per_s | prenef_dtip vs independent_pred | 20 | +0.0241 | [+0.0198, +0.0284] | 0.0000 | independent_pred |
| nef_submission_rate_per_s | prenef_dtip vs direct_nef | 20 | +0.0251 | [+0.0207, +0.0294] | 0.0000 | direct_nef |
| nef_submission_rate_per_s | prenef_dtip vs prenef_noai | 20 | +0.0251 | [+0.0207, +0.0294] | 0.0000 | prenef_noai |
| nef_submission_rate_per_s | prenef_noai vs direct_nef | 20 | +0.0000 | [-0.0000, +0.0000] | 0.9854 | none |
| nef_submission_rate_per_s | independent_pred vs direct_nef | 20 | +0.0010 | [+0.0006, +0.0015] | 0.0000 | direct_nef |
| coordination_overhead_ms | prenef_dtip vs independent_pred | 20 | -3.3189 | [-6.1959, -0.3778] | 0.2913 | none |
| coordination_overhead_ms | prenef_dtip vs direct_nef | 20 | -2.7734 | [-5.9796, +0.6105] | 0.4924 | none |
| coordination_overhead_ms | prenef_dtip vs prenef_noai | 20 | -1.1936 | [-4.7438, +2.3228] | 1.0000 | none |
| coordination_overhead_ms | prenef_noai vs direct_nef | 20 | -1.5799 | [-4.4999, +1.3633] | 1.0000 | none |
| coordination_overhead_ms | independent_pred vs direct_nef | 20 | +0.5455 | [-2.7791, +3.8253] | 1.0000 | none |
| burst_deadline_miss_fraction | prenef_dtip vs independent_pred | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | prenef_dtip vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | prenef_dtip vs prenef_noai | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | independent_pred vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | prenef_dtip vs independent_pred | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | prenef_dtip vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | prenef_dtip vs prenef_noai | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | independent_pred vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| cp_allocated_fraction | prenef_dtip vs independent_pred | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| cp_allocated_fraction | prenef_dtip vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| cp_allocated_fraction | prenef_dtip vs prenef_noai | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| cp_allocated_fraction | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| cp_allocated_fraction | independent_pred vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| mode_inadequacy_rate | prenef_dtip vs independent_pred | 20 | -0.0258 | [-0.0306, -0.0209] | 0.0000 | prenef_dtip |
| mode_inadequacy_rate | prenef_dtip vs direct_nef | 20 | -0.0337 | [-0.0374, -0.0299] | 0.0004 | prenef_dtip |
| mode_inadequacy_rate | prenef_dtip vs prenef_noai | 20 | -0.0317 | [-0.0352, -0.0282] | 0.0004 | prenef_dtip |
| mode_inadequacy_rate | prenef_noai vs direct_nef | 20 | -0.0019 | [-0.0027, -0.0012] | 0.0009 | prenef_noai |
| mode_inadequacy_rate | independent_pred vs direct_nef | 20 | -0.0078 | [-0.0095, -0.0062] | 0.0004 | independent_pred |
| net_latency_ms_median | prenef_dtip vs independent_pred | 20 | -0.0102 | [-0.0675, +0.0483] | 1.0000 | none |
| net_latency_ms_median | prenef_dtip vs direct_nef | 20 | -0.0485 | [-0.0865, -0.0132] | 0.0932 | none |
| net_latency_ms_median | prenef_dtip vs prenef_noai | 20 | -0.0365 | [-0.0875, +0.0118] | 0.5219 | none |
| net_latency_ms_median | prenef_noai vs direct_nef | 20 | -0.0120 | [-0.0510, +0.0273] | 1.0000 | none |
| net_latency_ms_median | independent_pred vs direct_nef | 20 | -0.0382 | [-0.0965, +0.0107] | 1.0000 | none |

Notes: HTTP 201 is not counted as allocation; `allocated_fraction` uses evidence (eq. 17). Mock-mode campaigns validate the pipeline only and are not network results.
