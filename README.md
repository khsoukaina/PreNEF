# PReNEF finalization toolkit (v2)

Run every command from this folder with the venv active:

```bash
cd ~/prenef-experiments/prenef-next-stage/prenef-finalize && . .venv/bin/activate
```

Any script that touches the lab refuses to run without an explicit `--approve-...` flag or `APPROVE=1`. PReNEF listens on **port 19090** (9090 is taken on your machine).

## What changed in v2

- **Bug fixes:**
  - alerts crashed the runtime (`kind` argument collision);
  - the audit flagged EDF/FIFO deadline misses as violations, although eq. (24) binds only PReNEF;
  - two threads could write `submissions.jsonl` at the same time.
- **New arms:**
  - `independent_pred`: a per-AF predictor without the dependency graph (state of the art);
  - `oracle`: a ground-truth upper bound;
  - `static_priority`.
- **Ablations of `prenef_dtip`:** `_eta0`, `_nogate`, `_noguard`, `_nofanout`.
- **New KPIs:**
  - the primary KPI is now **inadequate-mode exposure (s) per episode**;
  - correlated coverage, lead time vs τ, utility loss, abstention rate, coordination overhead;
  - every KPI is stratified into shared-service vs single-UE episodes.
- **Analysis:** a ladder of paired comparisons plus the oracle capture ratio.
- **New script `bench/contention.py`:** the ordering experiment (fifo, edf, static priority, PReNEF guard) as the number of AFs grows.

## Benchmark design

| Experiment | Arms | What it shows |
|---|---|---|
| **Main** (Steps 9–10) | `direct_nef` → `independent_pred` → `prenef_noai` → `prenef_dtip`, + `oracle` | Value of the graph, of dependency-aware anticipation, and remaining headroom |
| **Ablations** (Step 9) | `prenef_dtip_eta0`, `_nogate`, `_noguard`, `_nofanout` | What each component of eq. 19, 23 and 24 contributes |
| **Contention** (Step 11) | `direct_nef`, `fifo`, `edf`, `static_priority`, `prenef_noai` vs number of AFs | Where request ordering and the deadline guard matter |

- **Primary KPI:** `exposure_s_per_episode`.
- **Headline comparison:** `prenef_dtip` vs `independent_pred`.
- **Latency and throughput:** sanity checks only. PReNEF does not deliver QoS; the PCF and UPF do.

---

## Phase A: validate the tooling offline

### Step 0: install and unit tests

```bash
python3 -m unittest tests.test_core -v          # 27 tests OK
```

### Step 1: mock campaign (about 6 min)

**Terminal 1** (leave it running):
```bash
python3 nef/mock_nef.py --port 18000 --capacity 1 --service-s 0.4 --fail-prob 0.1
```

**Terminal 2:**
```bash
rm -rf campaigns/mock0
python3 bench/run_campaign.py plan --blocks 1 --seed 3 --arms direct_nef,prenef_noai,oracle,fifo,edf \
  --duration-s 60 --episodes 3 --out campaigns/mock0/plan.json
python3 bench/run_campaign.py run --plan campaigns/mock0/plan.json --mode mock \
  --config config/runtime.mock.json --agents config/agents.mock.json --targets config/scenario_targets.json
python3 bench/show.py campaigns/mock0
```

**Exit:**
- every run shows `audit_ok: True`;
- `oracle` and `prenef_noai` have alerts greater than 0;
- `oracle` has the lowest exposure and a positive lead.

### Step 1b: full AI pipeline on mock data (about 25 min)

This checks that data collection, training, `independent_pred` and `prenef_dtip` all run. Mock models are **not** results.

```bash
python3 bench/run_campaign.py plan --blocks 6 --seed 21 --arms direct_nef,prenef_noai \
  --duration-s 90 --episodes 5 --out campaigns/mock-collect/plan.json
python3 bench/run_campaign.py run --plan campaigns/mock-collect/plan.json --mode mock \
  --config config/runtime.mock.json --agents config/agents.mock.json --targets config/scenario_targets.json
python3 dtip/dataset.py --journals "campaigns/mock-collect/b*/journal.jsonl" \
  --contracts config/contracts/*.json --out data/dtip-mock.jsonl
python3 dtip/train.py --dataset data/dtip-mock.jsonl --out-dir models/dtip-mock --min-positives 10
python3 - <<'EOF'
import json; p = "config/runtime.mock.json"; c = json.load(open(p))
c["model_dir"] = "models/dtip-mock"; c["independent_model_dir"] = "models/dtip-mock/variants/A_per_af"
json.dump(c, open(p, "w"), indent=2); print("runtime.mock.json updated")
EOF
python3 bench/run_campaign.py plan --blocks 2 --seed 4 --duration-s 60 --episodes 3 \
  --arms direct_nef,independent_pred,prenef_noai,prenef_dtip,oracle --out campaigns/mock-final/plan.json
python3 bench/run_campaign.py run --plan campaigns/mock-final/plan.json --mode mock \
  --config config/runtime.mock.json --agents config/agents.mock.json --targets config/scenario_targets.json
python3 bench/analyze.py --campaign campaigns/mock-final --out campaigns/mock-final/analysis
```

### Step 1c: contention experiment on the mock (about 5 min)

```bash
python3 bench/contention.py --api-root http://127.0.0.1:18000 --target-is-mock \
  --n-afs 4,8,16 --repeats 3 --service-s-est 0.45 --out campaigns/contention-mock
```

---

## Phase B: anchor PReNEF in the lab (read-only)

### Step 2: AF → UE → PDU-session binding

```bash
python3 lab/ue_binding.py --request config/binding.request.json --out binding.json --ue-pool 10.60.0.0/16
```

### Step 3a: find what your NEF expects (read-only)

```bash
cd .. && grep -rn --include=*.py -E "3gpp-as-session-with-qos|scsAsId|scs_as_id" app-v2 | head -20
grep -rn -E "qosReference|altQoSReferences" --include=*.json . 2>/dev/null | grep -v prenef-finalize | head -20
docker exec nef-qod423 sh -c 'cat /free5gc/config/nefcfg.yaml 2>/dev/null' | head -60
cd prenef-finalize
```

Send me this output. The contracts (`qosReference`, `scs_as_id`) and the `api_root` may need adapting.

### Step 3b: conformance of the real NEF (creates and deletes one subscription)

```bash
AF1_IP=$(python3 -c "import json;print(json.load(open('binding.json'))['afs']['af1']['ue_ipv4'])")
mkdir -p runs/conf
python3 nef/notification_server.py --bind 10.101.200.1 --port 18080 --out runs/conf/notif.jsonl &
sleep 1
python3 nef/conformance.py --api-root http://10.101.200.14:8000 --scs-as-id af1 \
  --contract config/contracts/af1.json --ue-ip "$AF1_IP" \
  --notif-dest http://10.101.200.1:18080/notify/af1 --notif-file runs/conf/notif.jsonl \
  --approve-live-NEF-operation --out runs/conf/report.json
kill %1
```

---

## Phase C: allocation evidence (eq. 17)

### Step 4

```bash
sudo lab/capture_n4.sh upf-qod423 runs/ev1/n4.pcap
sudo APPROVE=1 lab/bottleneck.sh upf-qod423 eth0 30mbit
python3 lab/dataplane_probe.py --binding binding.json --af af1 --phase pre --expect-kbps 10000 \
  --competitors af2,af3 --udp --rate 20M --out runs/ev1/probes.jsonl --approve-live-traffic
#   create a subscription (the conformance run of Step 3b, or one PReNEF run)
python3 lab/dataplane_probe.py --binding binding.json --af af1 --phase post --expect-kbps 10000 \
  --competitors af2,af3 --udp --rate 20M --out runs/ev1/probes.jsonl --approve-live-traffic
sudo lab/capture_n4.sh --stop runs/ev1/n4.pcap
sudo APPROVE=1 lab/bottleneck.sh --remove upf-qod423 eth0
tshark -G fields | grep -E "^F\s.*pfcp\.(msg_type|seid|ue_ip|qer_id|cause|seqno)" | head
```

Then run `lab/evidence_collector.py` on the run directory (see its header for the arguments).

---

## Phase D: shared service, scenarios, live smoke test

### Step 5

```bash
docker compose -f config/srsu-compose.yml up -d
docker exec ueransim-ue-qod423 ping -c 3 -I uesimtun0 10.101.200.40
python3 lab/scenario.py generate --targets config/scenario_targets.json --seed 11 --duration-s 120 --out /tmp/s.json
sudo .venv/bin/python3 lab/scenario.py inject --targets config/scenario_targets.json --scenario /tmp/s.json \
  --ground-truth /tmp/gt.jsonl --dry-run
```

### Step 6: one live block (`direct_nef` + `prenef_noai`)

```bash
python3 bench/run_campaign.py plan --blocks 1 --seed 8 --arms direct_nef,prenef_noai --duration-s 120 \
  --episodes 5 --out campaigns/lab-smoke/plan.json
python3 bench/run_campaign.py run --plan campaigns/lab-smoke/plan.json --mode lab \
  --config config/runtime.lab.json --agents config/agents.lab.json --targets config/scenario_targets.json \
  --capture-n4 --approve-live-NEF-operation --approve-live-degradation
python3 bench/show.py campaigns/lab-smoke
```

---

## Phase E: DTIP on lab data

### Steps 7–8: collect, train, qualify

```bash
python3 bench/run_campaign.py plan --blocks 12 --seed 21 --arms direct_nef,prenef_noai --duration-s 180 \
  --episodes 8 --out campaigns/collect1/plan.json
python3 bench/run_campaign.py run --plan campaigns/collect1/plan.json --mode lab \
  --config config/runtime.lab.json --agents config/agents.lab.json --targets config/scenario_targets.json \
  --capture-n4 --approve-live-NEF-operation --approve-live-degradation
python3 dtip/dataset.py --journals "campaigns/collect1/b*/journal.jsonl" \
  --contracts config/contracts/*.json --out data/dtip.jsonl
python3 dtip/train.py --dataset data/dtip.jsonl --out-dir models/dtip-v1 --alpha 0.9
```

- **Configure:** set `model_dir: models/dtip-v1` and `independent_model_dir: models/dtip-v1/variants/A_per_af` in `config/runtime.lab.json`.
- **Exit:** both model cards show `safe_time_qualified` and `uncertainty_qualified` set to true.
- **If not qualified:** collect more blocks.

---

## Phase F: final evaluation

### Step 9: main campaign + ablations (20 new blocks)

```bash
python3 bench/run_campaign.py plan --blocks 20 --seed 99 --duration-s 180 --episodes 8 \
  --arms direct_nef,independent_pred,prenef_noai,prenef_dtip,oracle,prenef_dtip_eta0,prenef_dtip_nogate,prenef_dtip_nofanout \
  --out campaigns/final/plan.json
python3 bench/run_campaign.py run --plan campaigns/final/plan.json --mode lab \
  --config config/runtime.lab.json --agents config/agents.lab.json --targets config/scenario_targets.json \
  --capture-n4 --approve-live-NEF-operation --approve-live-degradation
```

The run can be resumed: finished runs are skipped. Use `--blocks 5-8` to run a subset.

### Step 10: analysis

```bash
python3 bench/analyze.py --campaign campaigns/final --out campaigns/final/analysis
```

This writes `report.md` (means, paired CIs, Holm-adjusted p-values, oracle capture ratio), one figure per KPI, and `lead_vs_tau.png`.

### Step 11: contention on the real NEF

```bash
python3 nef/notification_server.py --bind 10.101.200.1 --port 18080 --out runs/cont/notif.jsonl &
python3 bench/contention.py --api-root http://10.101.200.14:8000 --binding binding.json \
  --notif-dest http://10.101.200.1:18080/notify --n-afs 4,8,16 --repeats 10 \
  --approve-live-NEF-operation --out campaigns/contention-lab
kill %1
```

### Step 12: paper corrections

- **Eq. (9):** use `F(h) ≥ 1−α`.
- **Eq. (23):** document the clamped urgency term.
- **Lab limits:** no radio scheduler (QoS is observable only behind the bottleneck), and only the AsSessionWithQoS NEF API is in scope.
