# Per-AF results

Mean over valid blocks [95% bootstrap CI]. n = blocks.

## af1 · shuttle A (sRSU)

| KPI | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP | Oracle (upper bound) |
|---|---|---|---|---|---|
| exposure / episode (s) | 0.425 [0.229, 0.630] (n=20) | 0.100 [0.032, 0.177] (n=20) | 0.429 [0.230, 0.641] (n=20) | 0.099 [0.035, 0.170] (n=20) | 0.000 [0.000, 0.000] (n=20) |
| time in remote | 95.5% [93.2%, 97.6%] (n=20) | 94.2% [91.4%, 96.7%] (n=20) | 95.4% [93.1%, 97.6%] (n=20) | 92.3% [89.6%, 94.8%] (n=20) | 85.8% [83.0%, 88.6%] (n=20) |
| timely adaptation | 0.00 [0.00, 0.00] (n=20) | 0.10 [0.04, 0.16] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.07 [0.02, 0.14] (n=20) | 0.84 [0.76, 0.91] (n=20) |
| median lead (s) | -2.65 [-2.84, -2.47] (n=10) | -0.82 [-1.89, -0.05] (n=11) | -2.65 [-2.78, -2.52] (n=10) | -0.45 [-0.81, -0.12] (n=10) | 0.34 [0.25, 0.44] (n=20) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=20) | 0.05 [0.00, 0.15] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.85 [0.50, 1.25] (n=20) | 0.00 [0.00, 0.00] (n=20) |
| utility loss / min | 1.08 [0.57, 1.63] (n=20) | 1.40 [0.78, 2.06] (n=20) | 1.10 [0.58, 1.66] (n=20) | 1.86 [1.24, 2.49] (n=20) | 3.40 [2.73, 4.08] (n=20) |
| alerts received | 0.0 [0.0, 0.0] (n=20) | 3.9 [2.6, 5.2] (n=20) | 1.8 [1.4, 2.1] (n=20) | 5.2 [4.0, 6.4] (n=20) | 9.1 [8.0, 10.1] (n=20) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF + DTIP vs Per-AF predictor | 20 | -0.0011 | [-0.0181, +0.0147] | 1.0000 |
| exposure / episode (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | -0.3267 | [-0.5048, -0.1689] | 0.0098 |
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0035 | [-0.0212, +0.0284] | 1.0000 |
| exposure / episode (s) | Per-AF predictor vs Direct NEF (3GPP) | 20 | -0.3256 | [-0.5073, -0.1678] | 0.0098 |
| exposure / episode (s) | Oracle (upper bound) vs PReNEF + DTIP | 20 | -0.0987 | [-0.1704, -0.0350] | 0.0938 |
| time in remote | PReNEF + DTIP vs Per-AF predictor | 20 | -0.0190 | [-0.0289, -0.0097] | 0.0042 |
| time in remote | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | -0.0323 | [-0.0419, -0.0230] | 0.0001 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | -0.0006 | [-0.0019, +0.0007] | 0.6953 |
| time in remote | Per-AF predictor vs Direct NEF (3GPP) | 20 | -0.0132 | [-0.0209, -0.0067] | 0.0029 |
| time in remote | Oracle (upper bound) vs PReNEF + DTIP | 20 | -0.0644 | [-0.0816, -0.0456] | 0.0001 |
| timely adaptation | PReNEF + DTIP vs Per-AF predictor | 20 | -0.0225 | [-0.0575, +0.0000] | 1.0000 |
| timely adaptation | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.0742 | [+0.0225, +0.1367] | 0.1050 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| timely adaptation | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.0967 | [+0.0425, +0.1608] | 0.0542 |
| timely adaptation | Oracle (upper bound) vs PReNEF + DTIP | 20 | +0.7633 | [+0.6783, +0.8459] | 0.0004 |
| median lead (s) | PReNEF + DTIP vs Per-AF predictor | 10 | -0.0708 | [-0.2538, +0.1132] | 1.0000 |
| median lead (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 10 | +2.1989 | [+1.8940, +2.5319] | 0.0098 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 10 | -0.0015 | [-0.1893, +0.2023] | 1.0000 |
| median lead (s) | Per-AF predictor vs Direct NEF (3GPP) | 10 | +2.2697 | [+1.8181, +2.7206] | 0.0098 |
| median lead (s) | Oracle (upper bound) vs PReNEF + DTIP | 10 | +0.7579 | [+0.3783, +1.1731] | 0.0176 |
| unnecessary fallbacks | PReNEF + DTIP vs Per-AF predictor | 20 | +0.8000 | [+0.4500, +1.1500] | 0.0076 |
| unnecessary fallbacks | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.8500 | [+0.5000, +1.2500] | 0.0076 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.0500 | [+0.0000, +0.1500] | 1.0000 |
| unnecessary fallbacks | Oracle (upper bound) vs PReNEF + DTIP | 20 | -0.8500 | [-1.2500, -0.5000] | 0.0076 |
| utility loss / min | PReNEF + DTIP vs Per-AF predictor | 20 | +0.4571 | [+0.2328, +0.6943] | 0.0042 |
| utility loss / min | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.7747 | [+0.5506, +1.0051] | 0.0001 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0132 | [-0.0169, +0.0465] | 0.6953 |
| utility loss / min | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.3175 | [+0.1601, +0.5019] | 0.0029 |
| utility loss / min | Oracle (upper bound) vs PReNEF + DTIP | 20 | +1.5458 | [+1.0954, +1.9588] | 0.0001 |

## af2 · shuttle B (sRSU)

| KPI | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP | Oracle (upper bound) |
|---|---|---|---|---|---|
| exposure / episode (s) | 0.518 [0.292, 0.773] (n=20) | 0.173 [0.066, 0.304] (n=20) | 0.505 [0.287, 0.742] (n=20) | 0.172 [0.071, 0.290] (n=20) | 0.006 [0.000, 0.019] (n=20) |
| time in remote | 95.1% [92.6%, 97.4%] (n=20) | 94.6% [91.9%, 97.0%] (n=20) | 95.3% [92.8%, 97.5%] (n=20) | 92.4% [89.7%, 94.9%] (n=20) | 85.3% [82.7%, 87.8%] (n=20) |
| timely adaptation | 0.00 [0.00, 0.00] (n=20) | 0.05 [0.00, 0.11] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.05 [0.00, 0.11] (n=20) | 0.78 [0.70, 0.85] (n=20) |
| median lead (s) | -2.70 [-2.88, -2.53] (n=12) | -0.75 [-1.17, -0.33] (n=12) | -2.55 [-2.70, -2.40] (n=12) | -0.84 [-1.22, -0.43] (n=12) | 0.31 [0.21, 0.41] (n=20) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.75 [0.40, 1.10] (n=20) | 0.00 [0.00, 0.00] (n=20) |
| utility loss / min | 1.17 [0.62, 1.78] (n=20) | 1.30 [0.72, 1.94] (n=20) | 1.14 [0.61, 1.73] (n=20) | 1.82 [1.23, 2.48] (n=20) | 3.53 [2.92, 4.16] (n=20) |
| alerts received | 0.0 [0.0, 0.0] (n=20) | 3.9 [2.6, 5.2] (n=20) | 1.9 [1.5, 2.2] (n=20) | 5.3 [4.1, 6.7] (n=20) | 9.3 [8.5, 10.1] (n=20) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF + DTIP vs Per-AF predictor | 20 | -0.0010 | [-0.0250, +0.0227] | 1.0000 |
| exposure / episode (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | -0.3457 | [-0.5343, -0.1847] | 0.0024 |
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | -0.0132 | [-0.0475, +0.0156] | 1.0000 |
| exposure / episode (s) | Per-AF predictor vs Direct NEF (3GPP) | 20 | -0.3448 | [-0.5323, -0.1850] | 0.0024 |
| exposure / episode (s) | Oracle (upper bound) vs PReNEF + DTIP | 20 | -0.1662 | [-0.2739, -0.0710] | 0.0117 |
| time in remote | PReNEF + DTIP vs Per-AF predictor | 20 | -0.0217 | [-0.0317, -0.0123] | 0.0020 |
| time in remote | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | -0.0271 | [-0.0366, -0.0182] | 0.0001 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0013 | [-0.0008, +0.0035] | 0.3013 |
| time in remote | Per-AF predictor vs Direct NEF (3GPP) | 20 | -0.0054 | [-0.0091, -0.0021] | 0.0098 |
| time in remote | Oracle (upper bound) vs PReNEF + DTIP | 20 | -0.0712 | [-0.0866, -0.0559] | 0.0000 |
| timely adaptation | PReNEF + DTIP vs Per-AF predictor | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| timely adaptation | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.0458 | [+0.0000, +0.1083] | 1.0000 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| timely adaptation | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.0458 | [+0.0000, +0.1083] | 1.0000 |
| timely adaptation | Oracle (upper bound) vs PReNEF + DTIP | 20 | +0.7308 | [+0.6275, +0.8292] | 0.0004 |
| median lead (s) | PReNEF + DTIP vs Per-AF predictor | 12 | -0.0914 | [-0.3005, +0.0908] | 0.8501 |
| median lead (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 12 | +1.8592 | [+1.4937, +2.2312] | 0.0024 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.1484 | [-0.0824, +0.4095] | 0.7607 |
| median lead (s) | Per-AF predictor vs Direct NEF (3GPP) | 12 | +1.9506 | [+1.5087, +2.3858] | 0.0024 |
| median lead (s) | Oracle (upper bound) vs PReNEF + DTIP | 12 | +1.1997 | [+0.7485, +1.6444] | 0.0029 |
| unnecessary fallbacks | PReNEF + DTIP vs Per-AF predictor | 20 | +0.7500 | [+0.4000, +1.1000] | 0.0235 |
| unnecessary fallbacks | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.7500 | [+0.4000, +1.1000] | 0.0235 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | Oracle (upper bound) vs PReNEF + DTIP | 20 | -0.7500 | [-1.1000, -0.4000] | 0.0235 |
| utility loss / min | PReNEF + DTIP vs Per-AF predictor | 20 | +0.5210 | [+0.2943, +0.7610] | 0.0020 |
| utility loss / min | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.6514 | [+0.4371, +0.8781] | 0.0001 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | -0.0302 | [-0.0837, +0.0198] | 0.3013 |
| utility loss / min | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.1305 | [+0.0503, +0.2177] | 0.0098 |
| utility loss / min | Oracle (upper bound) vs PReNEF + DTIP | 20 | +1.7088 | [+1.3425, +2.0789] | 0.0000 |

## af3 · drone

| KPI | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP | Oracle (upper bound) |
|---|---|---|---|---|---|
| exposure / episode (s) | 2.686 [2.580, 2.810] (n=12) | 0.584 [0.271, 0.958] (n=12) | 2.728 [2.603, 2.854] (n=12) | 0.559 [0.267, 0.872] (n=12) | 0.000 [0.000, 0.000] (n=12) |
| time in remote | 95.8% [94.1%, 97.5%] (n=20) | 94.5% [92.4%, 96.4%] (n=20) | 95.8% [94.1%, 97.5%] (n=20) | 94.9% [92.9%, 96.9%] (n=20) | 94.6% [92.4%, 96.7%] (n=20) |
| timely adaptation | 0.00 [0.00, 0.00] (n=12) | 0.46 [0.21, 0.71] (n=12) | 0.00 [0.00, 0.00] (n=12) | 0.38 [0.17, 0.62] (n=12) | 0.58 [0.33, 0.83] (n=12) |
| median lead (s) | -2.68 [-2.81, -2.56] (n=12) | -0.53 [-0.97, -0.15] (n=12) | -2.70 [-2.87, -2.53] (n=12) | -0.53 [-0.90, -0.18] (n=12) | 0.22 [0.07, 0.37] (n=12) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=20) | 0.15 [0.00, 0.30] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.00 [0.00, 0.00] (n=20) |
| utility loss / min | 1.00 [0.61, 1.42] (n=20) | 1.33 [0.86, 1.83] (n=20) | 1.00 [0.61, 1.40] (n=20) | 1.21 [0.74, 1.70] (n=20) | 1.30 [0.79, 1.83] (n=20) |
| alerts received | 0.0 [0.0, 0.0] (n=20) | 4.2 [3.1, 5.3] (n=20) | 1.8 [1.5, 2.1] (n=20) | 3.8 [2.6, 4.9] (n=20) | 2.6 [2.0, 3.3] (n=20) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF + DTIP vs Per-AF predictor | 12 | -0.0248 | [-0.2175, +0.1682] | 1.0000 |
| exposure / episode (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 12 | -2.1270 | [-2.4265, -1.7905] | 0.0024 |
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0416 | [-0.1243, +0.2101] | 1.0000 |
| exposure / episode (s) | Per-AF predictor vs Direct NEF (3GPP) | 12 | -2.1022 | [-2.3931, -1.7279] | 0.0024 |
| exposure / episode (s) | Oracle (upper bound) vs PReNEF + DTIP | 12 | -0.5592 | [-0.8725, -0.2670] | 0.0234 |
| time in remote | PReNEF + DTIP vs Per-AF predictor | 20 | +0.0049 | [-0.0001, +0.0102] | 0.2080 |
| time in remote | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | -0.0088 | [-0.0134, -0.0042] | 0.0044 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0003 | [-0.0027, +0.0036] | 0.9097 |
| time in remote | Per-AF predictor vs Direct NEF (3GPP) | 20 | -0.0137 | [-0.0196, -0.0078] | 0.0024 |
| time in remote | Oracle (upper bound) vs PReNEF + DTIP | 20 | -0.0035 | [-0.0059, -0.0015] | 0.0024 |
| timely adaptation | PReNEF + DTIP vs Per-AF predictor | 12 | -0.0833 | [-0.2500, +0.0000] | 1.0000 |
| timely adaptation | PReNEF + DTIP vs Direct NEF (3GPP) | 12 | +0.3750 | [+0.1667, +0.6250] | 0.1281 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| timely adaptation | Per-AF predictor vs Direct NEF (3GPP) | 12 | +0.4583 | [+0.2083, +0.7083] | 0.0961 |
| timely adaptation | Oracle (upper bound) vs PReNEF + DTIP | 12 | +0.2083 | [-0.0833, +0.5000] | 0.8510 |
| median lead (s) | PReNEF + DTIP vs Per-AF predictor | 12 | +0.0002 | [-0.2832, +0.2470] | 1.0000 |
| median lead (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 12 | +2.1493 | [+1.7976, +2.4826] | 0.0024 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | -0.0223 | [-0.2080, +0.1483] | 1.0000 |
| median lead (s) | Per-AF predictor vs Direct NEF (3GPP) | 12 | +2.1491 | [+1.7356, +2.4917] | 0.0024 |
| median lead (s) | Oracle (upper bound) vs PReNEF + DTIP | 12 | +0.7462 | [+0.3536, +1.1558] | 0.0146 |
| unnecessary fallbacks | PReNEF + DTIP vs Per-AF predictor | 20 | -0.1500 | [-0.3000, +0.0000] | 0.7446 |
| unnecessary fallbacks | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.1500 | [+0.0000, +0.3000] | 0.7446 |
| unnecessary fallbacks | Oracle (upper bound) vs PReNEF + DTIP | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| utility loss / min | PReNEF + DTIP vs Per-AF predictor | 20 | -0.1173 | [-0.2446, +0.0026] | 0.2080 |
| utility loss / min | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.2108 | [+0.1007, +0.3215] | 0.0044 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | -0.0064 | [-0.0865, +0.0639] | 0.9097 |
| utility loss / min | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.3280 | [+0.1880, +0.4695] | 0.0024 |
| utility loss / min | Oracle (upper bound) vs PReNEF + DTIP | 20 | +0.0839 | [+0.0369, +0.1413] | 0.0024 |

## af4 · XR

| KPI | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP | Oracle (upper bound) |
|---|---|---|---|---|---|
| exposure / episode (s) | 2.723 [2.585, 2.863] (n=9) | 1.056 [0.581, 1.529] (n=9) | 2.557 [2.500, 2.668] (n=9) | 1.056 [0.754, 1.386] (n=9) | 0.167 [0.000, 0.501] (n=9) |
| time in remote | 96.0% [93.7%, 98.1%] (n=20) | 95.4% [92.9%, 97.8%] (n=20) | 96.0% [93.8%, 98.1%] (n=20) | 95.6% [93.0%, 97.9%] (n=20) | 95.1% [92.3%, 97.7%] (n=20) |
| timely adaptation | 0.00 [0.00, 0.00] (n=9) | 0.17 [0.00, 0.39] (n=9) | 0.00 [0.00, 0.00] (n=9) | 0.06 [0.00, 0.17] (n=9) | 0.78 [0.56, 1.00] (n=9) |
| median lead (s) | -2.66 [-2.81, -2.51] (n=9) | -1.03 [-1.51, -0.51] (n=9) | -2.50 [-2.68, -2.36] (n=9) | -1.08 [-1.33, -0.84] (n=9) | 0.36 [0.14, 0.57] (n=9) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=20) | 0.05 [0.00, 0.15] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.00 [0.00, 0.00] (n=20) |
| utility loss / min | 0.95 [0.45, 1.51] (n=20) | 1.10 [0.53, 1.70] (n=20) | 0.95 [0.45, 1.49] (n=20) | 1.07 [0.51, 1.67] (n=20) | 1.17 [0.56, 1.84] (n=20) |
| alerts received | 0.0 [0.0, 0.0] (n=20) | 3.1 [2.0, 4.2] (n=20) | 1.6 [1.3, 1.9] (n=20) | 2.9 [1.9, 4.0] (n=20) | 2.2 [1.6, 2.9] (n=20) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF + DTIP vs Per-AF predictor | 9 | +0.0003 | [-0.3054, +0.2513] | 0.8203 |
| exposure / episode (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 9 | -1.6675 | [-2.0542, -1.2758] | 0.0195 |
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 9 | -0.1667 | [-0.3343, +0.0004] | 0.4062 |
| exposure / episode (s) | Per-AF predictor vs Direct NEF (3GPP) | 9 | -1.6679 | [-2.2250, -1.1097] | 0.0195 |
| exposure / episode (s) | Oracle (upper bound) vs PReNEF + DTIP | 9 | -0.8890 | [-1.3013, -0.4741] | 0.0234 |
| time in remote | PReNEF + DTIP vs Per-AF predictor | 20 | +0.0015 | [-0.0021, +0.0056] | 0.9922 |
| time in remote | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | -0.0047 | [-0.0087, -0.0012] | 0.1094 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0001 | [-0.0021, +0.0025] | 1.0000 |
| time in remote | Per-AF predictor vs Direct NEF (3GPP) | 20 | -0.0063 | [-0.0119, -0.0014] | 0.1094 |
| time in remote | Oracle (upper bound) vs PReNEF + DTIP | 20 | -0.0045 | [-0.0077, -0.0015] | 0.0977 |
| timely adaptation | PReNEF + DTIP vs Per-AF predictor | 9 | -0.1111 | [-0.3333, +0.0000] | 1.0000 |
| timely adaptation | PReNEF + DTIP vs Direct NEF (3GPP) | 9 | +0.0556 | [+0.0000, +0.1667] | 1.0000 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 9 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| timely adaptation | Per-AF predictor vs Direct NEF (3GPP) | 9 | +0.1667 | [+0.0000, +0.3889] | 1.0000 |
| timely adaptation | Oracle (upper bound) vs PReNEF + DTIP | 9 | +0.7222 | [+0.4444, +1.0000] | 0.0735 |
| median lead (s) | PReNEF + DTIP vs Per-AF predictor | 9 | -0.0533 | [-0.3760, +0.2657] | 0.9102 |
| median lead (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 9 | +1.5805 | [+1.1959, +1.9481] | 0.0195 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 9 | +0.1564 | [-0.0117, +0.3230] | 0.3281 |
| median lead (s) | Per-AF predictor vs Direct NEF (3GPP) | 9 | +1.6338 | [+1.0230, +2.2554] | 0.0195 |
| median lead (s) | Oracle (upper bound) vs PReNEF + DTIP | 9 | +1.4432 | [+1.1247, +1.7901] | 0.0195 |
| unnecessary fallbacks | PReNEF + DTIP vs Per-AF predictor | 20 | -0.0500 | [-0.1500, +0.0000] | 1.0000 |
| unnecessary fallbacks | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.0500 | [+0.0000, +0.1500] | 1.0000 |
| unnecessary fallbacks | Oracle (upper bound) vs PReNEF + DTIP | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| utility loss / min | PReNEF + DTIP vs Per-AF predictor | 20 | -0.0370 | [-0.1334, +0.0497] | 0.9922 |
| utility loss / min | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.1131 | [+0.0298, +0.2097] | 0.1094 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | -0.0034 | [-0.0593, +0.0500] | 1.0000 |
| utility loss / min | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.1500 | [+0.0335, +0.2865] | 0.1094 |
| utility loss / min | Oracle (upper bound) vs PReNEF + DTIP | 20 | +0.1072 | [+0.0369, +0.1841] | 0.0977 |

