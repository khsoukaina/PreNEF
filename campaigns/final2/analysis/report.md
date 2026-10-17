# Benchmark analysis

Blocks: 20 — arms: direct_nef, independent_pred, oracle, prenef_dtip, prenef_noai

Primary KPI: inadequate-mode exposure per episode (s). Headline comparison: prenef_dtip vs independent_pred.

Oracle capture ratio (share of the achievable exposure reduction obtained by prenef_dtip): 0.72 over 19 blocks, 95% CI [0.66, 0.79]

## Means per arm

| KPI | direct_nef | independent_pred | oracle | prenef_dtip | prenef_noai |
|---|---|---|---|---|---|
| Inadequate-mode exposure per episode (s) [PRIMARY] | 0.877 (n=20) | 0.257 (n=20) | 0.019 (n=20) | 0.255 (n=20) | 0.859 (n=20) |
| Exposure, shared-service episodes (s) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) |
| Exposure, single-UE episodes (s) | 2.687 (n=19) | 0.778 (n=19) | 0.045 (n=19) | 0.786 (n=19) | 2.656 (n=19) |
| Timely adaptation rate (eq. 26) | 0.000 (n=20) | 0.120 (n=20) | 0.786 (n=20) | 0.099 (n=20) | 0.000 (n=20) |
| Timely adaptation, shared episodes | 0.000 (n=20) | 0.000 (n=20) | 0.824 (n=20) | 0.000 (n=20) | 0.000 (n=20) |
| Timely adaptation, single-UE episodes | 0.000 (n=19) | 0.370 (n=19) | 0.738 (n=19) | 0.287 (n=19) | 0.000 (n=19) |
| Correlated coverage (all affected AFs in time) | 0.000 (n=20) | 0.000 (n=20) | 0.795 (n=20) | 0.000 (n=20) | 0.000 (n=20) |
| Median lead before onset (s) | -2.628 (n=19) | -0.667 (n=19) | 0.334 (n=20) | -0.669 (n=19) | -2.578 (n=19) |
| Unnecessary transitions (false alarms) | 0.000 (n=20) | 0.250 (n=20) | 0.000 (n=20) | 1.600 (n=20) | 0.000 (n=20) |
| Utility loss per minute (J2, eq. 21) | 4.060 (n=20) | 5.000 (n=20) | 9.072 (n=20) | 5.803 (n=20) | 4.034 (n=20) |
| Calibration error (eq. 27) | — | 0.316 (n=20) | — | 0.304 (n=20) | — |
| Calibration error, sample-weighted ECE | — | 0.020 (n=20) | — | 0.018 (n=20) | — |
| Abstention rate (eq. 19) | — | 0.000 (n=20) | — | 0.000 (n=20) | — |
| NEF submission rate (eq. 28) | 0.038 (n=20) | 0.040 (n=20) | 0.073 (n=20) | 0.047 (n=20) | 0.038 (n=20) |
| PReNEF coordination overhead (ms) | 62.365 (n=20) | 67.933 (n=20) | 48.423 (n=20) | 52.873 (n=20) | 60.231 (n=20) |
| Burst deadline miss fraction | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) |
| Evidenced allocation fraction (eq. 17, data plane) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) |
| Control-plane allocation fraction (PCF->SMF->PFCP) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) | 0.000 (n=20) |
| Tick-based inadequacy rate (sanity) | 0.011 (n=20) | 0.003 (n=20) | 0.000 (n=20) | 0.003 (n=20) | 0.011 (n=20) |
| Median network latency (sanity, not headline) | 2.267 (n=20) | 2.245 (n=20) | 2.273 (n=20) | 2.204 (n=20) | 2.276 (n=20) |

## Paired comparisons (A − B, Holm-adjusted Wilcoxon)

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) | favours |
|---|---|---|---|---|---|---|
| exposure_s_per_episode | prenef_dtip vs independent_pred | 20 | -0.0020 | [-0.0295, +0.0246] | 0.9323 | none |
| exposure_s_per_episode | prenef_dtip vs direct_nef | 20 | -0.6221 | [-0.7676, -0.4845] | 0.0000 | prenef_dtip |
| exposure_s_per_episode | prenef_dtip vs prenef_noai | 20 | -0.6039 | [-0.7357, -0.4745] | 0.0000 | prenef_dtip |
| exposure_s_per_episode | prenef_noai vs direct_nef | 20 | -0.0182 | [-0.0491, +0.0095] | 0.7909 | none |
| exposure_s_per_episode | independent_pred vs direct_nef | 20 | -0.6201 | [-0.7605, -0.4864] | 0.0000 | independent_pred |
| exposure_s_per_episode | oracle vs prenef_dtip | 20 | -0.2361 | [-0.3082, -0.1659] | 0.0000 | oracle |
| exposure_s_per_episode_shared | prenef_dtip vs independent_pred | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| exposure_s_per_episode_shared | prenef_dtip vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| exposure_s_per_episode_shared | prenef_dtip vs prenef_noai | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| exposure_s_per_episode_shared | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| exposure_s_per_episode_shared | independent_pred vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| exposure_s_per_episode_shared | oracle vs prenef_dtip | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| exposure_s_per_episode_ue | prenef_dtip vs independent_pred | 19 | +0.0081 | [-0.0867, +0.0966] | 1.0000 | none |
| exposure_s_per_episode_ue | prenef_dtip vs direct_nef | 19 | -1.9017 | [-2.0534, -1.7514] | 0.0000 | prenef_dtip |
| exposure_s_per_episode_ue | prenef_dtip vs prenef_noai | 19 | -1.8708 | [-2.0343, -1.7034] | 0.0000 | prenef_dtip |
| exposure_s_per_episode_ue | prenef_noai vs direct_nef | 19 | -0.0309 | [-0.1150, +0.0501] | 1.0000 | none |
| exposure_s_per_episode_ue | independent_pred vs direct_nef | 19 | -1.9098 | [-2.0989, -1.7167] | 0.0000 | independent_pred |
| exposure_s_per_episode_ue | oracle vs prenef_dtip | 19 | -0.7409 | [-0.9182, -0.5572] | 0.0000 | oracle |
| timely_adaptation_rate | prenef_dtip vs independent_pred | 20 | -0.0210 | [-0.0406, -0.0050] | 0.2500 | none |
| timely_adaptation_rate | prenef_dtip vs direct_nef | 20 | +0.0993 | [+0.0539, +0.1497] | 0.0153 | prenef_dtip |
| timely_adaptation_rate | prenef_dtip vs prenef_noai | 20 | +0.0993 | [+0.0539, +0.1497] | 0.0153 | prenef_dtip |
| timely_adaptation_rate | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate | independent_pred vs direct_nef | 20 | +0.1202 | [+0.0789, +0.1651] | 0.0036 | independent_pred |
| timely_adaptation_rate | oracle vs prenef_dtip | 20 | +0.6872 | [+0.6178, +0.7590] | 0.0006 | oracle |
| timely_adaptation_rate_shared | prenef_dtip vs independent_pred | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate_shared | prenef_dtip vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate_shared | prenef_dtip vs prenef_noai | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate_shared | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate_shared | independent_pred vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate_shared | oracle vs prenef_dtip | 20 | +0.8242 | [+0.7412, +0.9033] | 0.0005 | oracle |
| timely_adaptation_rate_ue | prenef_dtip vs independent_pred | 19 | -0.0833 | [-0.1667, -0.0175] | 0.1950 | none |
| timely_adaptation_rate_ue | prenef_dtip vs direct_nef | 19 | +0.2868 | [+0.1667, +0.4114] | 0.0139 | prenef_dtip |
| timely_adaptation_rate_ue | prenef_dtip vs prenef_noai | 19 | +0.2868 | [+0.1667, +0.4114] | 0.0139 | prenef_dtip |
| timely_adaptation_rate_ue | prenef_noai vs direct_nef | 19 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| timely_adaptation_rate_ue | independent_pred vs direct_nef | 19 | +0.3702 | [+0.2632, +0.4711] | 0.0033 | independent_pred |
| timely_adaptation_rate_ue | oracle vs prenef_dtip | 19 | +0.4509 | [+0.2982, +0.6009] | 0.0033 | oracle |
| correlated_coverage_rate | prenef_dtip vs independent_pred | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| correlated_coverage_rate | prenef_dtip vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| correlated_coverage_rate | prenef_dtip vs prenef_noai | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| correlated_coverage_rate | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| correlated_coverage_rate | independent_pred vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| correlated_coverage_rate | oracle vs prenef_dtip | 20 | +0.7950 | [+0.7017, +0.8858] | 0.0005 | oracle |
| lead_s_median | prenef_dtip vs independent_pred | 19 | -0.0018 | [-0.1555, +0.1760] | 0.6507 | none |
| lead_s_median | prenef_dtip vs direct_nef | 19 | +1.9593 | [+1.7654, +2.1619] | 0.0000 | prenef_dtip |
| lead_s_median | prenef_dtip vs prenef_noai | 19 | +1.9094 | [+1.7064, +2.1197] | 0.0000 | prenef_dtip |
| lead_s_median | prenef_noai vs direct_nef | 19 | +0.0498 | [-0.0387, +0.1435] | 0.5507 | none |
| lead_s_median | independent_pred vs direct_nef | 19 | +1.9610 | [+1.6896, +2.2170] | 0.0000 | independent_pred |
| lead_s_median | oracle vs prenef_dtip | 19 | +1.0067 | [+0.7431, +1.2681] | 0.0000 | oracle |
| unnecessary_transitions | prenef_dtip vs independent_pred | 20 | +1.3500 | [+0.8500, +1.8500] | 0.0026 | independent_pred |
| unnecessary_transitions | prenef_dtip vs direct_nef | 20 | +1.6000 | [+1.1500, +2.0000] | 0.0016 | direct_nef |
| unnecessary_transitions | prenef_dtip vs prenef_noai | 20 | +1.6000 | [+1.1500, +2.0000] | 0.0016 | prenef_noai |
| unnecessary_transitions | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| unnecessary_transitions | independent_pred vs direct_nef | 20 | +0.2500 | [+0.0000, +0.5500] | 0.3471 | none |
| unnecessary_transitions | oracle vs prenef_dtip | 20 | -1.6000 | [-2.0000, -1.1500] | 0.0016 | oracle |
| utility_loss_per_min | prenef_dtip vs independent_pred | 20 | +0.8021 | [+0.4606, +1.1583] | 0.0004 | independent_pred |
| utility_loss_per_min | prenef_dtip vs direct_nef | 20 | +1.7426 | [+1.3547, +2.1248] | 0.0000 | direct_nef |
| utility_loss_per_min | prenef_dtip vs prenef_noai | 20 | +1.7688 | [+1.3771, +2.1446] | 0.0000 | prenef_noai |
| utility_loss_per_min | prenef_noai vs direct_nef | 20 | -0.0262 | [-0.1232, +0.0735] | 0.4900 | none |
| utility_loss_per_min | independent_pred vs direct_nef | 20 | +0.9405 | [+0.6734, +1.2398] | 0.0000 | direct_nef |
| utility_loss_per_min | oracle vs prenef_dtip | 20 | +3.2690 | [+2.6018, +3.9355] | 0.0000 | prenef_dtip |
| calibration_error | prenef_dtip vs independent_pred | 20 | -0.0113 | [-0.0345, +0.0097] | 0.5706 | none |
| calibration_error_weighted | prenef_dtip vs independent_pred | 20 | -0.0015 | [-0.0028, -0.0004] | 0.0215 | prenef_dtip |
| abstention_rate | prenef_dtip vs independent_pred | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| nef_submission_rate_per_s | prenef_dtip vs independent_pred | 20 | +0.0071 | [+0.0041, +0.0100] | 0.0014 | independent_pred |
| nef_submission_rate_per_s | prenef_dtip vs direct_nef | 20 | +0.0090 | [+0.0066, +0.0112] | 0.0000 | direct_nef |
| nef_submission_rate_per_s | prenef_dtip vs prenef_noai | 20 | +0.0090 | [+0.0066, +0.0112] | 0.0000 | prenef_noai |
| nef_submission_rate_per_s | prenef_noai vs direct_nef | 20 | -0.0000 | [-0.0000, -0.0000] | 0.0759 | none |
| nef_submission_rate_per_s | independent_pred vs direct_nef | 20 | +0.0020 | [+0.0004, +0.0042] | 0.0000 | direct_nef |
| nef_submission_rate_per_s | oracle vs prenef_dtip | 20 | +0.0264 | [+0.0202, +0.0324] | 0.0000 | prenef_dtip |
| coordination_overhead_ms | prenef_dtip vs independent_pred | 20 | -15.0596 | [-21.7368, -8.8890] | 0.0010 | prenef_dtip |
| coordination_overhead_ms | prenef_dtip vs direct_nef | 20 | -9.4921 | [-15.0665, -4.0680] | 0.0084 | prenef_dtip |
| coordination_overhead_ms | prenef_dtip vs prenef_noai | 20 | -7.3578 | [-12.7555, -2.2733] | 0.0859 | none |
| coordination_overhead_ms | prenef_noai vs direct_nef | 20 | -2.1343 | [-5.8611, +1.5563] | 0.7768 | none |
| coordination_overhead_ms | independent_pred vs direct_nef | 20 | +5.5675 | [+0.6870, +11.0799] | 0.4287 | none |
| coordination_overhead_ms | oracle vs prenef_dtip | 20 | -4.4505 | [-12.2005, +2.1616] | 0.7768 | none |
| burst_deadline_miss_fraction | prenef_dtip vs independent_pred | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | prenef_dtip vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | prenef_dtip vs prenef_noai | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | independent_pred vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| burst_deadline_miss_fraction | oracle vs prenef_dtip | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | prenef_dtip vs independent_pred | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | prenef_dtip vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | prenef_dtip vs prenef_noai | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | independent_pred vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| allocated_fraction | oracle vs prenef_dtip | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| cp_allocated_fraction | prenef_dtip vs independent_pred | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| cp_allocated_fraction | prenef_dtip vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| cp_allocated_fraction | prenef_dtip vs prenef_noai | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| cp_allocated_fraction | prenef_noai vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| cp_allocated_fraction | independent_pred vs direct_nef | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| cp_allocated_fraction | oracle vs prenef_dtip | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | none |
| mode_inadequacy_rate | prenef_dtip vs independent_pred | 20 | +0.0000 | [-0.0004, +0.0003] | 1.0000 | none |
| mode_inadequacy_rate | prenef_dtip vs direct_nef | 20 | -0.0080 | [-0.0095, -0.0064] | 0.0008 | prenef_dtip |
| mode_inadequacy_rate | prenef_dtip vs prenef_noai | 20 | -0.0078 | [-0.0092, -0.0063] | 0.0008 | prenef_dtip |
| mode_inadequacy_rate | prenef_noai vs direct_nef | 20 | -0.0002 | [-0.0005, +0.0002] | 1.0000 | none |
| mode_inadequacy_rate | independent_pred vs direct_nef | 20 | -0.0080 | [-0.0095, -0.0064] | 0.0008 | independent_pred |
| mode_inadequacy_rate | oracle vs prenef_dtip | 20 | -0.0031 | [-0.0039, -0.0022] | 0.0009 | oracle |
| net_latency_ms_median | prenef_dtip vs independent_pred | 20 | -0.0402 | [-0.0903, +0.0118] | 0.4838 | none |
| net_latency_ms_median | prenef_dtip vs direct_nef | 20 | -0.0628 | [-0.1153, -0.0105] | 0.2908 | none |
| net_latency_ms_median | prenef_dtip vs prenef_noai | 20 | -0.0715 | [-0.1435, +0.0005] | 0.3652 | none |
| net_latency_ms_median | prenef_noai vs direct_nef | 20 | +0.0087 | [-0.0548, +0.0712] | 1.0000 | none |
| net_latency_ms_median | independent_pred vs direct_nef | 20 | -0.0225 | [-0.0725, +0.0255] | 1.0000 | none |
| net_latency_ms_median | oracle vs prenef_dtip | 20 | +0.0688 | [+0.0005, +0.1358] | 0.3652 | none |

Notes: HTTP 201 is not counted as allocation; `allocated_fraction` uses evidence (eq. 17). Mock-mode campaigns validate the pipeline only and are not network results.
