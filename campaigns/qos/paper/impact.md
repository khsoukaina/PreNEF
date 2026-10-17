# Impact summary (6 blocks; mean [95% CI over blocks])

Distance driven blind = exposure x 30 km/h (8.3 m/s). 'Absorbed' = 0 s in an inadequate mode.

## Shared-service failures (sRSU)

| Arm | episodes | absorbed (%) | anticipated (%) | exposure / episode (s) | blind distance / episode (m) |
|---|---|---|---|---|---|
| Direct NEF (3GPP) | 38 | 0 [0, 0] | 0 [0, 0] | 2.81 [2.64, 2.95] | 23.5 [22.0, 24.5] |
| Per-AF predictor | 38 | 3 [0, 10] | 7 [0, 13] | 2.55 [2.39, 2.69] | 21.3 [19.9, 22.4] |
| PReNEF (no AI) | 38 | 0 [0, 0] | 0 [0, 0] | 2.49 [2.47, 2.51] | 20.7 [20.6, 20.9] |
| PReNEF + DTIP | 37 | 86 [75, 97] | 59 [39, 80] | 0.26 [0.02, 0.57] | 2.2 [0.1, 4.8] |

## Single-UE failures

| Arm | episodes | absorbed (%) | anticipated (%) | exposure / episode (s) | blind distance / episode (m) |
|---|---|---|---|---|---|
| Direct NEF (3GPP) | 21 | 0 [0, 0] | 0 [0, 0] | 2.69 [2.57, 2.82] | 22.4 [21.4, 23.5] |
| Per-AF predictor | 22 | 34 [17, 51] | 32 [14, 50] | 0.79 [0.48, 1.08] | 6.6 [4.0, 9.0] |
| PReNEF (no AI) | 21 | 0 [0, 0] | 0 [0, 0] | 2.63 [2.53, 2.75] | 21.9 [21.1, 22.9] |
| PReNEF + DTIP | 20 | 46 [21, 72] | 38 [10, 67] | 0.69 [0.33, 1.01] | 5.7 [2.8, 8.4] |

## Unsafe time per hour of operation (all episodes, per AF)

| Arm | inadequate-mode seconds per AF-hour |
|---|---|
| Direct NEF (3GPP) | 136 [116, 159] s per hour |
| Per-AF predictor | 97 [65, 127] s per hour |
| PReNEF (no AI) | 126 [109, 144] s per hour |
| PReNEF + DTIP | 21 [18, 25] s per hour |
