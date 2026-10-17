# QoS experienced by the applications (only while they relied on the network)

Mean [95 % bootstrap CI over blocks]; percentage = relative change vs Direct NEF (3GPP).

| Metric | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| Time in remote (network-dependent) mode (%) | 88.0 [86.9, 88.9] | 85.6 [84.9, 86.4]<br>(-3 %) | 87.8 [86.7, 88.7]<br>(-0 %) | 79.8 [78.8, 80.9]<br>(-9 %) |
| Relying on an out-of-contract path (s per AF-hour) | 325.1 [243.8, 382.6] | 280.0 [187.6, 349.2]<br>(-14 %) | 317.6 [240.8, 371.0]<br>(-2 %) | 148.8 [110.9, 181.1]<br>(-54 %) |
| – N6 path: RTT > 60 ms, loss or no reply (s per AF-hour) | 48.8 [34.6, 69.2] | 15.4 [7.9, 23.0]<br>(-68 %) | 48.8 [34.2, 69.2]<br>(-0 %) | 15.0 [6.3, 24.6]<br>(-69 %) |
| – sRSU unreachable or RTT > 60 ms (s per AF-hour, af1–af2) | 593.5 [411.7, 719.3] | 542.6 [359.4, 680.0]<br>(-9 %) | 582.7 [411.7, 701.9]<br>(-2 %) | 281.8 [208.1, 343.6]<br>(-53 %) |
| p99 N6 RTT experienced in remote mode (ms, no reply = 2000) | 74 [62, 88] | 35 [20, 47]<br>(-53 %) | 74 [62, 86]<br>(-0 %) | 38 [23, 55]<br>(-49 %) |
| Uplink data not delivered in remote mode (Mbit per AF-hour) | 4.1 [4.0, 4.1] | 3.9 [3.9, 4.0]<br>(-3 %) | 4.1 [4.0, 4.1]<br>(-0 %) | 3.7 [3.6, 3.8]<br>(-9 %) |
| Remote-mode seconds with goodput < 50 % (s per AF-hour) | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] |

## Per UE: seconds per AF-hour relying on an out-of-contract path

| UE | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| af1 | 615.2 [446.8, 740.1] | 563.5 [388.6, 691.8] | 616.8 [451.8, 735.4] | 288.5 [223.5, 343.6] |
| af2 | 573.5 [376.7, 708.5] | 521.7 [331.7, 676.7] | 548.5 [368.3, 672.0] | 275.1 [193.0, 345.4] |
| af3 | 30.0 [10.0, 50.0] | 6.7 [0.0, 16.7] | 28.3 [8.3, 49.9] | 6.6 [0.0, 19.9] |
| af4 | 81.7 [41.7, 120.1] | 28.3 [5.0, 51.7] | 76.7 [41.5, 116.7] | 25.1 [3.3, 51.8] |

## Per scenario phase: % of the phase spent relying on the network (remote mode)

| Phase | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| UE ramp (precursor) | 99 [96, 100] | 99 [98, 100] | 99 [96, 100] | 96 [92, 99] |
| UE degradation (contract violated) | 34 [29, 40] | 10 [7, 13] | 34 [29, 40] | 9 [5, 13] |
| sRSU ramp (precursor) | 96 [88, 100] | 96 [92, 99] | 96 [91, 100] | 80 [68, 91] |
| sRSU outage | 56 [51, 61] | 52 [44, 58] | 52 [46, 60] | 9 [7, 11] |

## Tail (figQ2): % of operating time relying on the path with RTT > 60 ms / with no reply

| Path | Direct NEF (3GPP) | Per-AF predictor | PReNEF (no AI) | PReNEF + DTIP |
|---|---|---|---|---|
| UE→N6 | 1.35 / 0.00 | 0.43 / 0.00 | 1.35 / 0.00 | 0.42 / 0.00 |
| UE→sRSU | 16.49 / 4.96 | 15.07 / 4.54 | 16.19 / 4.39 | 7.83 / 0.44 |
