# QoS experienced by the applications (only while they relied on the network)

Mean [95 % bootstrap CI over blocks]; percentage = relative change vs Direct NEF (3GPP).

| Metric | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| Time in remote (network-dependent) mode (%) | 88.0 [87.3, 88.8] | 87.2 [86.4, 87.9]<br>(-1 %) | 87.8 [87.0, 88.6]<br>(-0 %) | 80.3 [79.5, 81.2]<br>(-9 %) |
| Relying on an out-of-contract path (s per AF-hour) | 351.5 [317.7, 384.7] | 324.0 [284.8, 362.9]<br>(-8 %) | 344.5 [312.1, 376.3]<br>(-2 %) | 148.5 [131.9, 165.2]<br>(-58 %) |
| – N6 path: RTT > 60 ms, loss or no reply (s per AF-hour) | 42.9 [34.1, 51.7] | 15.2 [11.5, 19.1]<br>(-64 %) | 43.3 [34.3, 52.3]<br>(+1 %) | 15.3 [11.6, 19.3]<br>(-64 %) |
| – sRSU unreachable or RTT > 60 ms (s per AF-hour, af1–af2) | 659.3 [584.1, 733.7] | 632.3 [549.1, 713.9]<br>(-4 %) | 646.5 [572.5, 718.8]<br>(-2 %) | 281.2 [245.2, 317.4]<br>(-57 %) |
| p99 N6 RTT experienced in remote mode (ms, no reply = 2000) | 66 [51, 79] | 28 [19, 37]<br>(-57 %) | 65 [51, 78]<br>(-1 %) | 33 [24, 43]<br>(-50 %) |

## Per UE: seconds per AF-hour relying on an out-of-contract path

| UE | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| af1 | 665.0 [589.0, 739.5] | 634.1 [550.0, 716.5] | 653.5 [578.0, 726.0] | 285.4 [248.3, 323.5] |
| af2 | 654.1 [576.6, 730.6] | 631.0 [547.1, 713.0] | 640.0 [565.9, 714.1] | 277.0 [240.5, 313.0] |
| af3 | 42.5 [24.0, 62.4] | 17.0 [7.5, 29.0] | 42.5 [24.5, 62.5] | 17.5 [7.5, 29.5] |
| af4 | 44.5 [25.5, 65.0] | 14.0 [6.5, 23.0] | 42.0 [24.0, 62.0] | 14.0 [7.0, 22.0] |

## Per scenario phase: % of the phase spent relying on the network (remote mode)

| Phase | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| UE ramp (precursor) | 94 [83, 100] | 93 [82, 99] | 94 [83, 100] | 92 [81, 99] |
| UE degradation (contract violated) | 30 [28, 32] | 11 [10, 13] | 30 [28, 32] | 12 [10, 14] |
| sRSU ramp (precursor) | 97 [95, 99] | 97 [95, 99] | 97 [95, 99] | 82 [78, 86] |
| sRSU outage | 58 [56, 60] | 57 [55, 59] | 55 [53, 57] | 5 [3, 8] |

## Tail (figQ2): % of operating time relying on the path with RTT > 60 ms / with no reply

| Path | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| UE→N6 | 1.19 / 0.00 | 0.42 / 0.00 | 1.20 / 0.00 | 0.42 / 0.00 |
| UE→sRSU | 18.31 / 5.47 | 17.56 / 5.44 | 17.96 / 5.03 | 7.81 / 0.27 |
