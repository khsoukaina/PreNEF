# Pre-registered analysis plan (written before the final campaign)
- Primary KPI: inadequate-mode exposure per (episode, affected AF), contract-based onset (eq. 4).
- Headline comparison: prenef_dtip vs independent_pred (paired by block, Wilcoxon, Holm, bootstrap 95% CI).
- DTIP qualification gate: sample-weighted ECE <= 0.05 on every horizon with >= 30 test positives,
  T_safe coverage >= alpha - 0.02 (alpha = 0.9), by-run chronological split; literal eq.27 ECE also reported.
- Final campaign uses NEW scenario seeds (never used for training): plan seed 99.
- Runs failing the audit are excluded and listed; nothing else is excluded.
Wed Oct 14 12:46:01 AM CEST 2026
e847e96dc4eb774bd86c1fc6a5efd2e6146c383539aba686b1bce571cb504951  data/dtip-lab-v1.jsonl
9bbf3fb67de82cf25fbebb9618cc5e831a8ac2902974dbf9b12e85c396c758f8  models/dtip-lab-v1/model.pkl

## 2026-10-14T15:38:26+02:00 final2 frozen (PReNEF v1). Findings: anticipation -71% exposure vs direct_nef;
H1 untestable: docker-pause sRSU outages invisible (ICMP answered). v2: netem outage + attribution-gated fan-out; retrain; final3 seed 199.

## 2026-10-14T17:59:23+02:00 model frozen for final3
a32df2450ec9adb544ea9bac90be71a81acf37d4446fd6ddf3bf89c3ecb66a09  data/dtip-lab-v3.jsonl
f42c7eca821a4901711edda3201da88ba0887400b375e37dcd14c5655d68b08b  models/dtip-lab-v3/model.pkl
f42c7eca821a4901711edda3201da88ba0887400b375e37dcd14c5655d68b08b  models/dtip-lab-v3/variants/A_per_af/model.pkl

## 2026-10-14T23:43:26+02:00 variant decision for final3 (no final3 data analysed)
Automatic selection (ECE only) picked A_per_af; it ignored discrimination. Both variants qualified.
B_shared_services AUROC h1..h12 = .99/.97/.95/.91/.87/.82 vs A = .77/.76/.74/.68/.65/.63.
Decision: prenef_dtip uses B (dependency-aware DTIP, as defined in the study); independent_pred uses A.
final3 restarted from scratch; aborted partial run kept in campaigns/invalid/final3-aborted-modelA.
f8631c4bdafb56b5fd614838e97cd36e3dc6bfdb7e6abc39a79ece4b68b065eb  models/dtip-lab-v3/variants/B_shared_services/model.pkl
f42c7eca821a4901711edda3201da88ba0887400b375e37dcd14c5655d68b08b  models/dtip-lab-v3/variants/A_per_af/model.pkl

## 2026-10-15T10:53:53+02:00 analysis decision: oracle arm removed from all reported analyses and figures
Reason: not part of the deployable system; raw runs kept in campaigns/final3/b*-oracle (not reported).

## 2026-10-15T13:09:58+02:00 sweep campaign (seed 555, new scenarios)
Thresholds p_alert in {0.50,0.70,0.85} for per-AF predictor (model A) and PReNEF+DTIP (model B).
DTIP runs without fan-out (ablation result: fewer false fallbacks, exposure unchanged). Primary output: operating curves.
