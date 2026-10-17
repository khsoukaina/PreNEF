# Network conditions per UE and scenario phase

Pooled over arms (the scenario of a block is identical in every arm). RTT/loss from the AF probes (0.2 s ping), goodput from lab/tput_logger.py (receiver side).

| UE | phase | samples | RTT N6 p50 / p95 (ms) | loss N6 (%) | sRSU reachable (%) | RTT sRSU p50 (ms) | goodput p50 (Mb/s) |
|---|---|---|---|---|---|---|---|
| af1 | Baseline | 5554 | 1.0 / 2.0 | 1.6 | 100 | 1.0 | 1.00 |
| af1 | UE ramp (precursor) | 138 | 32.8 / 49.3 | 2.3 | 100 | 32.9 | 1.00 |
| af1 | UE degradation (contract violated) | 544 | 122.0 / 601.0 | 8.1 | 100 | 124.5 | 1.00 |
| af1 | sRSU ramp (precursor) | 1211 | 1.0 / 2.2 | 1.8 | 100 | 65.4 | 1.00 |
| af1 | sRSU outage | 1192 | 1.0 / 2.1 | 1.7 | 36 | 80.9 | 1.00 |
| af2 | Baseline | 6031 | 1.0 / 1.9 | 1.7 | 100 | 1.0 | 1.00 |
| af2 | UE ramp (precursor) | 32 | 37.6 / 50.1 | 1.9 | 100 | 37.8 | 1.00 |
| af2 | UE degradation (contract violated) | 168 | 241.0 / 601.0 | 11.1 | 100 | 241.0 | 1.00 |
| af2 | sRSU ramp (precursor) | 1214 | 1.0 / 2.2 | 1.5 | 100 | 65.4 | 1.00 |
| af2 | sRSU outage | 1194 | 1.0 / 2.1 | 1.7 | 37 | 80.8 | 1.00 |
| af3 | Baseline | 8399 | 1.0 / 2.0 | 1.6 | – | – | 1.00 |
| af3 | UE ramp (precursor) | 56 | 33.0 / 49.8 | 2.5 | – | – | 1.00 |
| af3 | UE degradation (contract violated) | 184 | 82.5 / 601.0 | 7.0 | – | – | 1.00 |
| af4 | Baseline | 7839 | 1.0 / 2.1 | 1.7 | – | – | 1.00 |
| af4 | UE ramp (precursor) | 144 | 33.0 / 49.4 | 2.2 | – | – | 1.00 |
| af4 | UE degradation (contract violated) | 656 | 201.0 / 601.0 | 8.5 | – | – | 1.00 |

Identical-conditions check: largest difference between arms of the median N6 RTT within a (UE, phase) cell = 20.0 ms.

