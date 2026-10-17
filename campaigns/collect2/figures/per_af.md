# Per-AF results

Mean over valid blocks [95% bootstrap CI]. n = blocks.

## af1 · shuttle A (sRSU)

| KPI | Direct NEF (3GPP) | PReNEF (no AI) |
|---|---|---|
| exposure / episode (s) | 0.413 [0.083, 0.825] (n=12) | 0.427 [0.092, 0.858] (n=12) |
| time in remote | 94.8% [88.8%, 99.4%] (n=12) | 94.8% [89.0%, 99.4%] (n=12) |
| timely adaptation | 0.00 [0.00, 0.00] (n=12) | 0.00 [0.00, 0.00] (n=12) |
| median lead (s) | -2.60 [-2.77, -2.43] (n=4) | -2.66 [-2.98, -2.41] (n=4) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=12) | 0.00 [0.00, 0.00] (n=12) |
| utility loss / min | 1.25 [0.13, 2.69] (n=12) | 1.25 [0.14, 2.65] (n=12) |
| alerts received | 0.0 [0.0, 0.0] (n=12) | 1.8 [1.2, 2.5] (n=12) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=12) | 100.0% [100.0%, 100.0%] (n=12) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0146 | [-0.0225, +0.0582] | 0.8750 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0002 | [-0.0009, +0.0019] | 1.0000 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 4 | -0.0617 | [-0.3878, +0.3133] | 0.8750 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | -0.0060 | [-0.0452, +0.0217] | 1.0000 |

## af2 · shuttle B (sRSU)

| KPI | Direct NEF (3GPP) | PReNEF (no AI) |
|---|---|---|
| exposure / episode (s) | 0.288 [0.122, 0.462] (n=12) | 0.273 [0.115, 0.440] (n=12) |
| time in remote | 97.5% [95.8%, 99.0%] (n=12) | 97.4% [95.8%, 98.9%] (n=12) |
| timely adaptation | 0.00 [0.00, 0.00] (n=12) | 0.00 [0.00, 0.00] (n=12) |
| median lead (s) | -2.69 [-2.85, -2.53] (n=6) | -2.51 [-2.73, -2.33] (n=6) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=12) | 0.00 [0.00, 0.00] (n=12) |
| utility loss / min | 0.61 [0.25, 1.00] (n=12) | 0.62 [0.26, 1.00] (n=12) |
| alerts received | 0.0 [0.0, 0.0] (n=12) | 1.5 [1.2, 1.8] (n=12) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=12) | 100.0% [100.0%, 100.0%] (n=12) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | -0.0155 | [-0.0498, +0.0204] | 0.5625 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | -0.0005 | [-0.0021, +0.0014] | 0.4375 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 6 | +0.1767 | [-0.1559, +0.4481] | 0.3125 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0111 | [-0.0334, +0.0500] | 0.4375 |

## af3 · drone

| KPI | Direct NEF (3GPP) | PReNEF (no AI) |
|---|---|---|
| exposure / episode (s) | 2.697 [2.557, 2.858] (n=9) | 2.690 [2.552, 2.829] (n=9) |
| time in remote | 95.0% [92.9%, 97.0%] (n=12) | 95.0% [93.0%, 97.0%] (n=12) |
| timely adaptation | 0.00 [0.00, 0.00] (n=9) | 0.00 [0.00, 0.00] (n=9) |
| median lead (s) | -2.60 [-2.74, -2.47] (n=9) | -2.65 [-2.86, -2.46] (n=9) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=12) | 0.00 [0.00, 0.00] (n=12) |
| utility loss / min | 1.21 [0.72, 1.69] (n=12) | 1.20 [0.72, 1.67] (n=12) |
| alerts received | 0.0 [0.0, 0.0] (n=12) | 1.8 [1.5, 2.2] (n=12) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=12) | 100.0% [100.0%, 100.0%] (n=12) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 9 | -0.0073 | [-0.2291, +0.2126] | 0.6523 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0005 | [-0.0016, +0.0026] | 1.0000 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 9 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 9 | -0.0503 | [-0.2735, +0.1759] | 0.9102 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | -0.0110 | [-0.0613, +0.0389] | 1.0000 |

## af4 · XR

| KPI | Direct NEF (3GPP) | PReNEF (no AI) |
|---|---|---|
| exposure / episode (s) | 2.601 [2.495, 2.806] (n=5) | 2.801 [2.600, 3.002] (n=5) |
| time in remote | 96.8% [94.1%, 99.1%] (n=12) | 96.8% [94.1%, 99.1%] (n=12) |
| timely adaptation | 0.00 [0.00, 0.00] (n=5) | 0.00 [0.00, 0.00] (n=5) |
| median lead (s) | -2.48 [-2.69, -2.29] (n=5) | -2.77 [-3.02, -2.55] (n=5) |
| unnecessary fallbacks | 0.00 [0.00, 0.00] (n=12) | 0.00 [0.00, 0.00] (n=12) |
| utility loss / min | 0.77 [0.22, 1.41] (n=12) | 0.76 [0.22, 1.41] (n=12) |
| alerts received | 0.0 [0.0, 0.0] (n=12) | 1.3 [1.0, 1.8] (n=12) |
| measurement coverage | 100.0% [100.0%, 100.0%] (n=12) | 100.0% [100.0%, 100.0%] (n=12) |

Paired comparisons for this AF (A − B, Wilcoxon, Holm within KPI):

| KPI | A vs B | n | mean diff | 95% CI | p (Holm) |
|---|---|---|---|---|---|
| exposure / episode (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 5 | +0.1997 | [-0.0020, +0.4023] | 0.4375 |
| time in remote | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0005 | [-0.0004, +0.0014] | 0.3125 |
| timely adaptation | PReNEF (no AI) vs Direct NEF (3GPP) | 5 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| median lead (s) | PReNEF (no AI) vs Direct NEF (3GPP) | 5 | -0.2938 | [-0.6877, +0.0057] | 0.6250 |
| unnecessary fallbacks | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | +0.0000 | [+0.0000, +0.0000] | 1.0000 |
| utility loss / min | PReNEF (no AI) vs Direct NEF (3GPP) | 12 | -0.0114 | [-0.0333, +0.0101] | 0.3125 |

