# Per-AF results

Mean over valid blocks [95% bootstrap CI]. n = blocks.

## af1 · shuttle A (sRSU)

| KPI | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| exposure / episode (s) | 2.705 [2.671, 2.737] (n=20) | 2.357 [2.152, 2.543] (n=20) | 2.555 [2.506, 2.609] (n=20) | 0.346 [0.161, 0.584] (n=20) |
| time in remote | 79.9% [77.1%, 82.5%] (n=20) | 78.6% [75.4%, 81.6%] (n=20) | 79.2% [76.5%, 81.8%] (n=20) | 65.4% [62.3%, 68.5%] (n=20) |
| timely adaptation | 0.00 [0.00, 0.00] (n=20) | 0.03 [0.00, 0.07] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.63 [0.51, 0.74] (n=20) |
| median lead (s) | -3.80 [-3.98, -3.60] (n=20) | -3.50 [-3.85, -3.09] (n=20) | -3.66 [-3.77, -3.54] (n=20) | 0.05 [-0.13, 0.22] (n=20) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.00 [0.00, 0.00] (n=20) | 1.90 [1.50, 2.35] (n=20) |
| utility loss / min | 4.83 [4.20, 5.49] (n=20) | 5.14 [4.42, 5.90] (n=20) | 4.99 [4.37, 5.63] (n=20) | 8.31 [7.56, 9.04] (n=20) |
| alerts received | 0.0 [0.0, 0.0] (n=20) | 7.9 [6.7, 9.3] (n=20) | 9.2 [8.2, 10.2] (n=20) | 25.1 [23.2, 26.9] (n=20) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF + DTIP vs Per-AF predictor | 20 | -2.0115 | [-2.3227, -1.6365] | 0.0000 |
| exposure / episode (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | -2.3594 | [-2.5458, -2.1240] | 0.0000 |
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | -0.1506 | [-0.2186, -0.0819] | 0.0014 |
| exposure / episode (s) | Per-AF predictor vs Direct NEF (3GPP) | 20 | -0.3480 | [-0.5458, -0.1636] | 0.0056 |
| time in remote | PReNEF + DTIP vs Per-AF predictor | 20 | -0.1323 | [-0.1485, -0.1156] | 0.0000 |
| time in remote | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | -0.1451 | [-0.1577, -0.1318] | 0.0000 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | -0.0065 | [-0.0098, -0.0029] | 0.0040 |
| time in remote | Per-AF predictor vs Direct NEF (3GPP) | 20 | -0.0128 | [-0.0207, -0.0057] | 0.0083 |
| timely adaptation | PReNEF + DTIP vs Per-AF predictor | 20 | +0.5950 | [+0.4833, +0.7017] | 0.0005 |
| timely adaptation | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.6258 | [+0.5133, +0.7358] | 0.0005 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| timely adaptation | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.0308 | [+0.0000, +0.0683] | 0.5000 |
| median lead (s) | PReNEF + DTIP vs Per-AF predictor | 20 | +3.5495 | [+3.0295, +4.0090] | 0.0000 |
| median lead (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +3.8511 | [+3.5221, +4.1577] | 0.0000 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.1354 | [+0.0408, +0.2296] | 0.0112 |
| median lead (s) | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.3015 | [+0.0664, +0.5603] | 0.0532 |
| unnecessary fallbacks | PReNEF + DTIP vs Per-AF predictor | 20 | +1.9000 | [+1.5000, +2.3500] | 0.0003 |
| unnecessary fallbacks | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +1.9000 | [+1.5000, +2.3500] | 0.0003 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| utility loss / min | PReNEF + DTIP vs Per-AF predictor | 20 | +3.1747 | [+2.7740, +3.5652] | 0.0000 |
| utility loss / min | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +3.4821 | [+3.1642, +3.7859] | 0.0000 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.1550 | [+0.0699, +0.2346] | 0.0040 |
| utility loss / min | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.3074 | [+0.1361, +0.4963] | 0.0083 |

## af2 · shuttle B (sRSU)

| KPI | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| exposure / episode (s) | 2.737 [2.692, 2.781] (n=20) | 2.435 [2.216, 2.608] (n=20) | 2.581 [2.530, 2.641] (n=20) | 0.255 [0.123, 0.397] (n=20) |
| time in remote | 81.7% [78.8%, 84.5%] (n=20) | 81.0% [78.0%, 84.0%] (n=20) | 81.3% [78.4%, 84.2%] (n=20) | 67.0% [63.8%, 70.1%] (n=20) |
| timely adaptation | 0.00 [0.00, 0.00] (n=20) | 0.07 [0.01, 0.14] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.72 [0.60, 0.82] (n=20) |
| median lead (s) | -3.86 [-4.01, -3.66] (n=20) | -3.68 [-4.03, -3.18] (n=20) | -3.74 [-3.86, -3.60] (n=20) | 0.22 [0.08, 0.35] (n=20) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.00 [0.00, 0.00] (n=20) | 2.15 [1.60, 2.70] (n=20) |
| utility loss / min | 4.39 [3.73, 5.08] (n=20) | 4.55 [3.84, 5.29] (n=20) | 4.48 [3.80, 5.19] (n=20) | 7.92 [7.17, 8.70] (n=20) |
| alerts received | 0.0 [0.0, 0.0] (n=20) | 6.8 [5.6, 8.2] (n=20) | 8.8 [7.8, 9.9] (n=20) | 24.8 [22.9, 26.6] (n=20) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF + DTIP vs Per-AF predictor | 20 | -2.1805 | [-2.4445, -1.8661] | 0.0000 |
| exposure / episode (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | -2.4822 | [-2.6187, -2.3348] | 0.0000 |
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | -0.1557 | [-0.2288, -0.0788] | 0.0024 |
| exposure / episode (s) | Per-AF predictor vs Direct NEF (3GPP) | 20 | -0.3017 | [-0.5349, -0.1102] | 0.0024 |
| time in remote | PReNEF + DTIP vs Per-AF predictor | 20 | -0.1405 | [-0.1546, -0.1255] | 0.0000 |
| time in remote | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | -0.1473 | [-0.1599, -0.1340] | 0.0000 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | -0.0039 | [-0.0074, -0.0006] | 0.0592 |
| time in remote | Per-AF predictor vs Direct NEF (3GPP) | 20 | -0.0068 | [-0.0119, -0.0023] | 0.0592 |
| timely adaptation | PReNEF + DTIP vs Per-AF predictor | 20 | +0.6520 | [+0.5179, +0.7770] | 0.0006 |
| timely adaptation | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.7175 | [+0.5983, +0.8242] | 0.0005 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| timely adaptation | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.0655 | [+0.0071, +0.1446] | 0.1950 |
| median lead (s) | PReNEF + DTIP vs Per-AF predictor | 20 | +3.9039 | [+3.4306, +4.2601] | 0.0000 |
| median lead (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +4.0770 | [+3.7840, +4.2951] | 0.0000 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.1170 | [-0.0197, +0.2298] | 0.0344 |
| median lead (s) | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.1731 | [-0.0977, +0.5903] | 0.9273 |
| unnecessary fallbacks | PReNEF + DTIP vs Per-AF predictor | 20 | +2.1500 | [+1.6000, +2.7000] | 0.0011 |
| unnecessary fallbacks | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +2.1500 | [+1.6000, +2.7000] | 0.0011 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| utility loss / min | PReNEF + DTIP vs Per-AF predictor | 20 | +3.3721 | [+3.0111, +3.7106] | 0.0000 |
| utility loss / min | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +3.5343 | [+3.2152, +3.8384] | 0.0000 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0940 | [+0.0143, +0.1772] | 0.0592 |
| utility loss / min | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.1623 | [+0.0554, +0.2852] | 0.0592 |

## af3 · drone

| KPI | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| exposure / episode (s) | 2.639 [2.542, 2.751] (n=12) | 0.959 [0.544, 1.335] (n=12) | 2.661 [2.546, 2.786] (n=12) | 0.993 [0.554, 1.411] (n=12) |
| time in remote | 94.9% [92.5%, 97.1%] (n=20) | 94.1% [91.4%, 96.4%] (n=20) | 95.0% [92.5%, 97.2%] (n=20) | 94.2% [91.5%, 96.6%] (n=20) |
| timely adaptation | 0.00 [0.00, 0.00] (n=12) | 0.17 [0.00, 0.42] (n=12) | 0.00 [0.00, 0.00] (n=12) | 0.08 [0.00, 0.25] (n=12) |
| median lead (s) | -2.65 [-2.76, -2.52] (n=12) | -0.88 [-1.36, -0.40] (n=12) | -2.67 [-2.86, -2.49] (n=12) | -0.96 [-1.38, -0.52] (n=12) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=20) | 0.05 [0.00, 0.15] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.00 [0.00, 0.00] (n=20) |
| utility loss / min | 1.22 [0.70, 1.81] (n=20) | 1.42 [0.86, 2.06] (n=20) | 1.20 [0.68, 1.79] (n=20) | 1.40 [0.81, 2.05] (n=20) |
| alerts received | 0.0 [0.0, 0.0] (n=20) | 3.7 [2.6, 4.8] (n=20) | 1.8 [1.4, 2.1] (n=20) | 3.5 [2.5, 4.7] (n=20) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF + DTIP vs Per-AF predictor | 12 | +0.0337 | [-0.1560, +0.2499] | 1.0000 |
| exposure / episode (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 12 | -1.6460 | [-2.0619, -1.2284] | 0.0020 |
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0214 | [-0.1240, +0.1685] | 1.0000 |
| exposure / episode (s) | Per-AF predictor vs Direct NEF (3GPP) | 12 | -1.6798 | [-2.0553, -1.2924] | 0.0020 |
| time in remote | PReNEF + DTIP vs Per-AF predictor | 20 | +0.0011 | [-0.0021, +0.0050] | 1.0000 |
| time in remote | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | -0.0074 | [-0.0108, -0.0042] | 0.0015 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0007 | [-0.0018, +0.0032] | 1.0000 |
| time in remote | Per-AF predictor vs Direct NEF (3GPP) | 20 | -0.0085 | [-0.0124, -0.0049] | 0.0010 |
| timely adaptation | PReNEF + DTIP vs Per-AF predictor | 12 | -0.0833 | [-0.2500, +0.0000] | 1.0000 |
| timely adaptation | PReNEF + DTIP vs Direct NEF (3GPP) | 12 | +0.0833 | [+0.0000, +0.2500] | 1.0000 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| timely adaptation | Per-AF predictor vs Direct NEF (3GPP) | 12 | +0.1667 | [+0.0000, +0.4167] | 1.0000 |
| median lead (s) | PReNEF + DTIP vs Per-AF predictor | 12 | -0.0752 | [-0.3211, +0.1689] | 1.0000 |
| median lead (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 12 | +1.6916 | [+1.2555, +2.1396] | 0.0020 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | -0.0196 | [-0.1680, +0.1266] | 1.0000 |
| median lead (s) | Per-AF predictor vs Direct NEF (3GPP) | 12 | +1.7668 | [+1.2582, +2.2594] | 0.0029 |
| unnecessary fallbacks | PReNEF + DTIP vs Per-AF predictor | 20 | -0.0500 | [-0.1500, +0.0000] | 1.0000 |
| unnecessary fallbacks | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.0500 | [+0.0000, +0.1500] | 1.0000 |
| utility loss / min | PReNEF + DTIP vs Per-AF predictor | 20 | -0.0265 | [-0.1199, +0.0501] | 1.0000 |
| utility loss / min | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.1778 | [+0.1004, +0.2583] | 0.0015 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | -0.0160 | [-0.0761, +0.0438] | 1.0000 |
| utility loss / min | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.2043 | [+0.1174, +0.2977] | 0.0010 |

## af4 · XR

| KPI | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| exposure / episode (s) | 2.786 [2.660, 2.911] (n=12) | 0.931 [0.583, 1.306] (n=12) | 2.618 [2.522, 2.734] (n=12) | 0.961 [0.626, 1.335] (n=12) |
| time in remote | 95.5% [93.5%, 97.3%] (n=20) | 94.8% [92.4%, 96.9%] (n=20) | 95.5% [93.5%, 97.3%] (n=20) | 94.7% [92.2%, 96.9%] (n=20) |
| timely adaptation | 0.00 [0.00, 0.00] (n=12) | 0.19 [0.00, 0.42] (n=12) | 0.00 [0.00, 0.00] (n=12) | 0.24 [0.04, 0.46] (n=12) |
| median lead (s) | -2.73 [-2.88, -2.57] (n=12) | -0.84 [-1.22, -0.45] (n=12) | -2.63 [-2.75, -2.51] (n=12) | -0.86 [-1.27, -0.46] (n=12) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.00 [0.00, 0.00] (n=20) | 0.00 [0.00, 0.00] (n=20) |
| utility loss / min | 1.07 [0.64, 1.56] (n=20) | 1.25 [0.74, 1.82] (n=20) | 1.08 [0.64, 1.55] (n=20) | 1.28 [0.75, 1.87] (n=20) |
| alerts received | 0.0 [0.0, 0.0] (n=20) | 3.9 [2.6, 5.3] (n=20) | 1.8 [1.4, 2.1] (n=20) | 3.6 [2.5, 4.9] (n=20) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) | 100.0% [100.0%, 100.0%] (n=20) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF + DTIP vs Per-AF predictor | 12 | +0.0299 | [-0.1102, +0.1707] | 0.2324 |
| exposure / episode (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 12 | -1.8251 | [-2.1535, -1.4989] | 0.0020 |
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | -0.1676 | [-0.2913, -0.0632] | 0.0137 |
| exposure / episode (s) | Per-AF predictor vs Direct NEF (3GPP) | 12 | -1.8550 | [-2.1875, -1.5399] | 0.0020 |
| time in remote | PReNEF + DTIP vs Per-AF predictor | 20 | -0.0011 | [-0.0034, +0.0010] | 0.5322 |
| time in remote | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | -0.0086 | [-0.0145, -0.0039] | 0.0020 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | -0.0001 | [-0.0021, +0.0018] | 1.0000 |
| time in remote | Per-AF predictor vs Direct NEF (3GPP) | 20 | -0.0075 | [-0.0116, -0.0039] | 0.0020 |
| timely adaptation | PReNEF + DTIP vs Per-AF predictor | 12 | +0.0417 | [+0.0000, +0.1250] | 1.0000 |
| timely adaptation | PReNEF + DTIP vs Direct NEF (3GPP) | 12 | +0.2361 | [+0.0417, +0.4583] | 0.3901 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| timely adaptation | Per-AF predictor vs Direct NEF (3GPP) | 12 | +0.1944 | [+0.0000, +0.4167] | 0.5207 |
| median lead (s) | PReNEF + DTIP vs Per-AF predictor | 12 | -0.0240 | [-0.1697, +0.1197] | 0.5693 |
| median lead (s) | PReNEF + DTIP vs Direct NEF (3GPP) | 12 | +1.8691 | [+1.4733, +2.2817] | 0.0020 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.1027 | [-0.0500, +0.2541] | 0.4072 |
| median lead (s) | Per-AF predictor vs Direct NEF (3GPP) | 12 | +1.8931 | [+1.5382, +2.2683] | 0.0020 |
| unnecessary fallbacks | PReNEF + DTIP vs Per-AF predictor | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| unnecessary fallbacks | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| utility loss / min | PReNEF + DTIP vs Per-AF predictor | 20 | +0.0268 | [-0.0237, +0.0808] | 0.5322 |
| utility loss / min | PReNEF + DTIP vs Direct NEF (3GPP) | 20 | +0.2071 | [+0.0936, +0.3473] | 0.0020 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 20 | +0.0033 | [-0.0434, +0.0504] | 1.0000 |
| utility loss / min | Per-AF predictor vs Direct NEF (3GPP) | 20 | +0.1803 | [+0.0935, +0.2774] | 0.0020 |

