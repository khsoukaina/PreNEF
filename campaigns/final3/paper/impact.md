# Impact summary (20 blocks; mean [95% CI over blocks])

Distance driven blind = exposure x 30 km/h (8.3 m/s). 'Absorbed' = 0 s in an inadequate mode.

## Shared-service failures (sRSU)

| Arm | episodes | absorbed (%) | anticipated (%) | exposure / episode (s) | blind distance / episode (m) |
|---|---|---|---|---|---|
| Direct NEF (3GPP) | 135 | 0 [0, 0] | 0 [0, 0] | 2.74 [2.71, 2.77] | 22.9 [22.6, 23.1] |
| Per-AF predictor | 133 | 0 [0, 0] | 0 [0, 0] | 2.71 [2.65, 2.77] | 22.6 [22.1, 23.1] |
| PReNEF (no AI) | 137 | 0 [0, 0] | 0 [0, 0] | 2.52 [2.49, 2.55] | 21.0 [20.8, 21.3] |
| PReNEF + DTIP | 134 | 91 [79, 99] | 76 [64, 86] | 0.20 [0.02, 0.50] | 1.7 [0.1, 4.1] |

## Single-UE failures

| Arm | episodes | absorbed (%) | anticipated (%) | exposure / episode (s) | blind distance / episode (m) |
|---|---|---|---|---|---|
| Direct NEF (3GPP) | 62 | 0 [0, 0] | 0 [0, 0] | 2.69 [2.63, 2.74] | 22.4 [22.0, 22.9] |
| Per-AF predictor | 61 | 24 [13, 37] | 19 [10, 29] | 0.93 [0.74, 1.13] | 7.8 [6.1, 9.4] |
| PReNEF (no AI) | 62 | 0 [0, 0] | 0 [0, 0] | 2.70 [2.62, 2.77] | 22.5 [21.8, 23.1] |
| PReNEF + DTIP | 61 | 29 [18, 41] | 19 [11, 28] | 0.98 [0.77, 1.19] | 8.2 [6.4, 9.9] |

## Unsafe time per hour of operation (all episodes, per AF)

| Arm | inadequate-mode seconds per AF-hour |
|---|---|
| Direct NEF (3GPP) | 135 [124, 146] s per hour |
| Per-AF predictor | 105 [91, 119] s per hour |
| PReNEF (no AI) | 128 [119, 138] s per hour |
| PReNEF + DTIP | 18 [13, 24] s per hour |
