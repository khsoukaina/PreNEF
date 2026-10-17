# Network conditions per UE and scenario phase

Pooled over arms (the scenario of a block is identical in every arm). RTT/loss from the AF probes (0.2 s ping), goodput from lab/tput_logger.py (receiver side).

| UE | phase | samples | RTT N6 p50 / p95 (ms) | loss N6 (%) | sRSU reachable (%) | RTT sRSU p50 (ms) | goodput p50 (Mb/s) |
|---|---|---|---|---|---|---|---|
| af1 | Baseline | 18300 | 2.2 / 3.1 | 0.5 | 100 | 2.3 | – |
| af1 | UE ramp (precursor) | 283 | 34.7 / 50.9 | 1.4 | 100 | 34.9 | – |
| af1 | UE degradation (contract violated) | 1501 | 241.0 / 603.0 | 8.8 | 100 | 242.0 | – |
| af1 | sRSU ramp (precursor) | 4422 | 2.2 / 3.0 | 0.4 | 100 | 67.2 | – |
| af1 | sRSU outage | 4294 | 2.3 / 3.1 | 0.3 | 39 | 82.0 | – |
| af2 | Baseline | 18827 | 2.2 / 3.0 | 0.5 | 100 | 2.3 | – |
| af2 | UE ramp (precursor) | 234 | 33.9 / 50.9 | 0.8 | 100 | 33.9 | – |
| af2 | UE degradation (contract violated) | 1020 | 242.0 / 603.0 | 8.9 | 100 | 242.0 | – |
| af2 | sRSU ramp (precursor) | 4420 | 2.2 / 3.0 | 0.4 | 100 | 67.1 | – |
| af2 | sRSU outage | 4299 | 2.2 / 3.1 | 0.4 | 39 | 82.0 | – |
| af3 | Baseline | 27339 | 2.3 / 3.1 | 0.4 | – | – | – |
| af3 | UE ramp (precursor) | 233 | 34.3 / 50.9 | 1.3 | – | – | – |
| af3 | UE degradation (contract violated) | 1228 | 202.5 / 603.0 | 8.5 | – | – | – |
| af4 | Baseline | 27460 | 2.3 / 3.1 | 0.4 | – | – | – |
| af4 | UE ramp (precursor) | 264 | 34.5 / 50.9 | 1.4 | – | – | – |
| af4 | UE degradation (contract violated) | 1076 | 123.0 / 423.2 | 6.6 | – | – | – |

Identical-conditions check: largest difference between arms of the median N6 RTT within a (UE, phase) cell = 39.0 ms.

