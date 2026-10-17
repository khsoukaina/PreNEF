# Per-AF results

Mean over valid blocks [95% bootstrap CI]. n = blocks.

## af1 · shuttle A (sRSU)

| KPI | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| exposure / episode (s) | 2.703 [2.584, 2.815] (n=6) | 2.106 [1.691, 2.424] (n=6) | 2.609 [2.551, 2.659] (n=6) | 0.499 [0.165, 0.905] (n=6) |
| time in remote | 79.1% [75.9%, 82.5%] (n=6) | 77.3% [74.4%, 80.9%] (n=6) | 78.9% [76.0%, 82.1%] (n=6) | 66.4% [63.1%, 70.0%] (n=6) |
| timely adaptation | 0.00 [0.00, 0.00] (n=6) | 0.11 [0.03, 0.22] (n=6) | 0.00 [0.00, 0.00] (n=6) | 0.48 [0.34, 0.62] (n=6) |
| median lead (s) | -3.73 [-4.14, -3.13] (n=6) | -3.39 [-3.86, -2.56] (n=6) | -3.62 [-3.93, -3.12] (n=6) | -0.12 [-0.54, 0.25] (n=6) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=6) | 0.00 [0.00, 0.00] (n=6) | 0.00 [0.00, 0.00] (n=6) | 1.67 [0.83, 2.50] (n=6) |
| utility loss / min | 5.02 [4.19, 5.77] (n=6) | 5.45 [4.59, 6.15] (n=6) | 5.07 [4.30, 5.77] (n=6) | 8.05 [7.20, 8.87] (n=6) |
| alerts received | 0.0 [0.0, 0.0] (n=6) | 9.2 [7.2, 10.8] (n=6) | 8.7 [6.3, 10.8] (n=6) | 23.2 [19.5, 26.8] (n=6) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=6) | 100.0% [100.0%, 100.0%] (n=6) | 100.0% [100.0%, 100.0%] (n=6) | 100.0% [100.0%, 100.0%] (n=6) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF + DTIP vs Per-AF predictor | 6 | -1.6063 | [-2.1598, -0.8400] | 0.1250 |
| exposure / episode (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | -2.2036 | [-2.5768, -1.7312] | 0.1250 |
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | -0.0945 | [-0.2411, +0.0563] | 0.2188 |
| exposure / episode (s) | Per-AF predictor vs Direct NEF (3GPP) | 6 | -0.5974 | [-0.9278, -0.3481] | 0.1250 |
| time in remote | PReNEF + DTIP vs Per-AF predictor | 6 | -0.1085 | [-0.1299, -0.0835] | 0.1250 |
| time in remote | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | -0.1266 | [-0.1476, -0.1039] | 0.1250 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | -0.0023 | [-0.0069, +0.0019] | 0.5625 |
| time in remote | Per-AF predictor vs Direct NEF (3GPP) | 6 | -0.0181 | [-0.0250, -0.0111] | 0.1250 |
| timely adaptation | PReNEF + DTIP vs Per-AF predictor | 6 | +0.3694 | [+0.2333, +0.5361] | 0.1250 |
| timely adaptation | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | +0.4806 | [+0.3389, +0.6167] | 0.1250 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| timely adaptation | Per-AF predictor vs Direct NEF (3GPP) | 6 | +0.1111 | [+0.0278, +0.2222] | 0.3471 |
| median lead (s) | PReNEF + DTIP vs Per-AF predictor | 6 | +3.2756 | [+2.2439, +4.0769] | 0.1250 |
| median lead (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | +3.6127 | [+2.8369, +4.2749] | 0.1250 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | +0.1093 | [-0.1659, +0.3314] | 0.5625 |
| median lead (s) | Per-AF predictor vs Direct NEF (3GPP) | 6 | +0.3371 | [+0.0665, +0.6488] | 0.1875 |
| unnecessary fallbacks | PReNEF + DTIP vs Per-AF predictor | 6 | +1.6667 | [+0.8333, +2.5000] | 0.2270 |
| unnecessary fallbacks | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | +1.6667 | [+0.8333, +2.5000] | 0.2270 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | Per-AF predictor vs Direct NEF (3GPP) | 6 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| utility loss / min | PReNEF + DTIP vs Per-AF predictor | 6 | +2.6049 | [+2.0044, +3.1173] | 0.1250 |
| utility loss / min | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | +3.0385 | [+2.4924, +3.5413] | 0.1250 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | +0.0552 | [-0.0462, +0.1667] | 0.5625 |
| utility loss / min | Per-AF predictor vs Direct NEF (3GPP) | 6 | +0.4336 | [+0.2667, +0.5998] | 0.1250 |

## af2 · shuttle B (sRSU)

| KPI | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| exposure / episode (s) | 2.763 [2.612, 2.913] (n=6) | 2.191 [1.697, 2.644] (n=6) | 2.451 [2.367, 2.534] (n=6) | 0.503 [0.066, 1.170] (n=6) |
| time in remote | 84.4% [80.7%, 88.4%] (n=6) | 81.6% [77.2%, 85.9%] (n=6) | 84.1% [80.3%, 88.3%] (n=6) | 70.4% [65.3%, 76.2%] (n=6) |
| timely adaptation | 0.00 [0.00, 0.00] (n=6) | 0.14 [0.00, 0.31] (n=6) | 0.00 [0.00, 0.00] (n=6) | 0.50 [0.24, 0.76] (n=6) |
| median lead (s) | -3.88 [-4.24, -3.23] (n=6) | -3.17 [-4.01, -2.24] (n=6) | -3.54 [-3.88, -3.02] (n=6) | -0.34 [-1.07, 0.26] (n=6) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=6) | 0.50 [0.17, 0.83] (n=6) | 0.00 [0.00, 0.00] (n=6) | 2.67 [2.17, 3.33] (n=6) |
| utility loss / min | 3.74 [2.79, 4.63] (n=6) | 4.41 [3.38, 5.48] (n=6) | 3.81 [2.81, 4.73] (n=6) | 7.10 [5.72, 8.32] (n=6) |
| alerts received | 0.0 [0.0, 0.0] (n=6) | 6.7 [6.0, 8.0] (n=6) | 7.7 [5.2, 9.8] (n=6) | 21.3 [16.8, 25.5] (n=6) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=6) | 100.0% [100.0%, 100.0%] (n=6) | 100.0% [100.0%, 100.0%] (n=6) | 100.0% [100.0%, 100.0%] (n=6) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF + DTIP vs Per-AF predictor | 6 | -1.6886 | [-2.5338, -0.6428] | 0.1250 |
| exposure / episode (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | -2.2603 | [-2.7850, -1.5007] | 0.1250 |
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | -0.3124 | [-0.4878, -0.1504] | 0.1250 |
| exposure / episode (s) | Per-AF predictor vs Direct NEF (3GPP) | 6 | -0.5717 | [-1.0626, -0.1686] | 0.1250 |
| time in remote | PReNEF + DTIP vs Per-AF predictor | 6 | -0.1119 | [-0.1351, -0.0881] | 0.1250 |
| time in remote | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | -0.1397 | [-0.1596, -0.1188] | 0.1250 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | -0.0028 | [-0.0066, +0.0014] | 0.4375 |
| time in remote | Per-AF predictor vs Direct NEF (3GPP) | 6 | -0.0278 | [-0.0501, -0.0101] | 0.1250 |
| timely adaptation | PReNEF + DTIP vs Per-AF predictor | 6 | +0.3639 | [+0.1389, +0.5889] | 0.3750 |
| timely adaptation | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | +0.5028 | [+0.2361, +0.7556] | 0.2316 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| timely adaptation | Per-AF predictor vs Direct NEF (3GPP) | 6 | +0.1389 | [+0.0000, +0.3056] | 1.0000 |
| median lead (s) | PReNEF + DTIP vs Per-AF predictor | 6 | +2.8338 | [+1.3089, +3.9250] | 0.1250 |
| median lead (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | +3.5356 | [+2.2130, +4.4591] | 0.1250 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | +0.3380 | [+0.1279, +0.5470] | 0.1250 |
| median lead (s) | Per-AF predictor vs Direct NEF (3GPP) | 6 | +0.7019 | [+0.1362, +1.4439] | 0.1250 |
| unnecessary fallbacks | PReNEF + DTIP vs Per-AF predictor | 6 | +2.1667 | [+1.6667, +2.6667] | 0.1340 |
| unnecessary fallbacks | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | +2.6667 | [+2.1667, +3.3333] | 0.1340 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | Per-AF predictor vs Direct NEF (3GPP) | 6 | +0.5000 | [+0.1667, +0.8333] | 0.2978 |
| utility loss / min | PReNEF + DTIP vs Per-AF predictor | 6 | +2.6851 | [+2.1149, +3.2434] | 0.1250 |
| utility loss / min | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | +3.3525 | [+2.8510, +3.8305] | 0.1250 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | +0.0667 | [-0.0338, +0.1582] | 0.4375 |
| utility loss / min | Per-AF predictor vs Direct NEF (3GPP) | 6 | +0.6674 | [+0.2424, +1.2033] | 0.1250 |

## af3 · drone

| KPI | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| exposure / episode (s) | 2.997 [2.989, 3.002] (n=3) | 0.667 [0.000, 1.500] (n=3) | 2.829 [2.501, 2.994] (n=3) | 0.663 [0.000, 1.990] (n=3) |
| time in remote | 97.4% [94.6%, 99.4%] (n=6) | 95.1% [91.5%, 98.7%] (n=6) | 97.5% [94.8%, 99.4%] (n=6) | 94.9% [91.6%, 97.8%] (n=6) |
| timely adaptation | 0.00 [0.00, 0.00] (n=3) | 0.33 [0.00, 1.00] (n=3) | 0.00 [0.00, 0.00] (n=3) | 0.67 [0.00, 1.00] (n=3) |
| median lead (s) | -2.99 [-3.15, -2.84] (n=3) | -0.51 [-1.49, 0.14] (n=3) | -2.85 [-3.18, -2.38] (n=3) | -0.51 [-1.98, 0.32] (n=3) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=6) | 0.67 [0.17, 1.33] (n=6) | 0.00 [0.00, 0.00] (n=6) | 0.67 [0.33, 1.00] (n=6) |
| utility loss / min | 0.64 [0.14, 1.29] (n=6) | 1.17 [0.30, 2.05] (n=6) | 0.60 [0.13, 1.24] (n=6) | 1.21 [0.53, 2.01] (n=6) |
| alerts received | 0.0 [0.0, 0.0] (n=6) | 4.2 [2.0, 6.5] (n=6) | 1.5 [1.2, 1.8] (n=6) | 4.2 [2.5, 5.8] (n=6) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=6) | 100.0% [100.0%, 100.0%] (n=6) | 100.0% [100.0%, 100.0%] (n=6) | 100.0% [100.0%, 100.0%] (n=6) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF + DTIP vs Per-AF predictor | 3 | -0.0035 | [-0.5009, +0.4904] | 1.0000 |
| exposure / episode (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 3 | -2.3338 | [-3.0016, -0.9986] | 1.0000 |
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 3 | -0.1680 | [-0.5011, +0.0041] | 1.0000 |
| exposure / episode (s) | Per-AF predictor vs Direct NEF (3GPP) | 3 | -2.3304 | [-3.0016, -1.4890] | 1.0000 |
| time in remote | PReNEF + DTIP vs Per-AF predictor | 6 | -0.0019 | [-0.0204, +0.0200] | 0.8125 |
| time in remote | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | -0.0241 | [-0.0353, -0.0125] | 0.2500 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | +0.0014 | [+0.0005, +0.0024] | 0.5000 |
| time in remote | Per-AF predictor vs Direct NEF (3GPP) | 6 | -0.0223 | [-0.0408, -0.0065] | 0.3750 |
| timely adaptation | PReNEF + DTIP vs Per-AF predictor | 3 | +0.3333 | [+0.0000, +1.0000] | 1.0000 |
| timely adaptation | PReNEF + DTIP vs Direct NEF (3GPP) | 3 | +0.6667 | [+0.0000, +1.0000] | 1.0000 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 3 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| timely adaptation | Per-AF predictor vs Direct NEF (3GPP) | 3 | +0.3333 | [+0.0000, +1.0000] | 1.0000 |
| median lead (s) | PReNEF + DTIP vs Per-AF predictor | 3 | -0.0007 | [-0.4835, +0.4924] | 1.0000 |
| median lead (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 3 | +2.4825 | [+0.9996, +3.4786] | 1.0000 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 3 | +0.1442 | [-0.0221, +0.4653] | 1.0000 |
| median lead (s) | Per-AF predictor vs Direct NEF (3GPP) | 3 | +2.4833 | [+1.4831, +2.9861] | 1.0000 |
| unnecessary fallbacks | PReNEF + DTIP vs Per-AF predictor | 6 | +0.0000 | [-0.8333, +0.6667] | 1.0000 |
| unnecessary fallbacks | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | +0.6667 | [+0.3333, +1.0000] | 0.2874 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | Per-AF predictor vs Direct NEF (3GPP) | 6 | +0.6667 | [+0.1667, +1.3333] | 0.5207 |
| utility loss / min | PReNEF + DTIP vs Per-AF predictor | 6 | +0.0450 | [-0.4800, +0.4907] | 0.8125 |
| utility loss / min | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | +0.5792 | [+0.3004, +0.8475] | 0.2500 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | -0.0338 | [-0.0568, -0.0111] | 0.5000 |
| utility loss / min | Per-AF predictor vs Direct NEF (3GPP) | 6 | +0.5342 | [+0.1560, +0.9791] | 0.3750 |

## af4 · XR

| KPI | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| exposure / episode (s) | 2.801 [2.602, 2.999] (n=5) | 0.783 [0.300, 1.383] (n=5) | 2.550 [2.497, 2.651] (n=5) | 0.667 [0.100, 1.367] (n=5) |
| time in remote | 90.9% [85.7%, 96.0%] (n=6) | 88.4% [82.0%, 94.5%] (n=6) | 90.5% [85.4%, 95.9%] (n=6) | 87.1% [81.1%, 93.4%] (n=6) |
| timely adaptation | 0.00 [0.00, 0.00] (n=5) | 0.20 [0.00, 0.60] (n=5) | 0.00 [0.00, 0.00] (n=5) | 0.40 [0.00, 0.80] (n=5) |
| median lead (s) | -2.90 [-3.22, -2.57] (n=5) | -0.60 [-1.24, -0.04] (n=5) | -2.56 [-2.68, -2.45] (n=5) | -0.32 [-1.08, 0.42] (n=5) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=6) | 0.33 [0.00, 0.67] (n=6) | 0.00 [0.00, 0.00] (n=6) | 0.67 [0.33, 1.00] (n=6) |
| utility loss / min | 2.18 [0.97, 3.44] (n=6) | 2.79 [1.33, 4.31] (n=6) | 2.27 [0.99, 3.51] (n=6) | 3.10 [1.58, 4.55] (n=6) |
| alerts received | 0.0 [0.0, 0.0] (n=6) | 7.0 [4.0, 10.3] (n=6) | 2.5 [1.8, 3.3] (n=6) | 7.5 [4.3, 10.7] (n=6) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=6) | 100.0% [100.0%, 100.0%] (n=6) | 100.0% [100.0%, 100.0%] (n=6) | 100.0% [100.0%, 100.0%] (n=6) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF + DTIP vs Per-AF predictor | 5 | -0.1160 | [-0.3637, +0.1001] | 0.6250 |
| exposure / episode (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 5 | -2.1333 | [-2.8974, -1.2333] | 0.2500 |
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 5 | -0.2505 | [-0.4493, -0.0516] | 0.2500 |
| exposure / episode (s) | Per-AF predictor vs Direct NEF (3GPP) | 5 | -2.0174 | [-2.6992, -1.2195] | 0.2500 |
| time in remote | PReNEF + DTIP vs Per-AF predictor | 6 | -0.0130 | [-0.0232, -0.0037] | 0.2500 |
| time in remote | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | -0.0381 | [-0.0548, -0.0195] | 0.2500 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | -0.0037 | [-0.0107, +0.0018] | 0.4375 |
| time in remote | Per-AF predictor vs Direct NEF (3GPP) | 6 | -0.0251 | [-0.0404, -0.0116] | 0.2500 |
| timely adaptation | PReNEF + DTIP vs Per-AF predictor | 5 | +0.2000 | [+0.0000, +0.6000] | 1.0000 |
| timely adaptation | PReNEF + DTIP vs Direct NEF (3GPP) | 5 | +0.4000 | [+0.0000, +0.8000] | 1.0000 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 5 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| timely adaptation | Per-AF predictor vs Direct NEF (3GPP) | 5 | +0.2000 | [+0.0000, +0.6000] | 1.0000 |
| median lead (s) | PReNEF + DTIP vs Per-AF predictor | 5 | +0.2801 | [+0.0756, +0.4822] | 0.3750 |
| median lead (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 5 | +2.5854 | [+1.5430, +3.5474] | 0.2500 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 5 | +0.3445 | [+0.0867, +0.5999] | 0.3750 |
| median lead (s) | Per-AF predictor vs Direct NEF (3GPP) | 5 | +2.3053 | [+1.3729, +3.1597] | 0.2500 |
| unnecessary fallbacks | PReNEF + DTIP vs Per-AF predictor | 6 | +0.3333 | [+0.0000, +0.6667] | 1.0000 |
| unnecessary fallbacks | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | +0.6667 | [+0.3333, +1.0000] | 0.2874 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | Per-AF predictor vs Direct NEF (3GPP) | 6 | +0.3333 | [+0.0000, +0.6667] | 1.0000 |
| utility loss / min | PReNEF + DTIP vs Per-AF predictor | 6 | +0.3125 | [+0.0896, +0.5572] | 0.2500 |
| utility loss / min | PReNEF + DTIP vs Direct NEF (3GPP) | 6 | +0.9144 | [+0.4674, +1.3161] | 0.2500 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | +0.0888 | [-0.0437, +0.2560] | 0.4375 |
| utility loss / min | Per-AF predictor vs Direct NEF (3GPP) | 6 | +0.6020 | [+0.2779, +0.9706] | 0.2500 |

