# CHAT HANDOFF — 2026-09-13 — 4号艇 LIVE orchestration blocker audit

Updated: 2026-09-13 JST
Repository: `merry02180218-ai/boatrace-backtest`
Priority: latest GitHub > older handoffs/chat memory.

## Immutable rules

- Keep current v291 race-entry logic unchanged.
- Jul/Aug 2026 are NON-PRISTINE; never use their outcomes for fitting, calibration, rule selection, rescue, or performance promotion.
- September 2026 remains outcome-blind; do not read current-month results/payouts for fitting, calibration, threshold selection, rescue, or evaluation.
- v96 is prohibited from production inference.
- LIVE requires an official pre-deadline 3連単 120-way snapshot; never substitute closing/post-deadline odds.
- Missing/late/incomplete required LIVE input must fail closed.

## Completed state confirmed in latest GitHub

The S/A market/ticket runner is implemented and CI validated:

- `run_4head_v291_varn_live.py`
- `verify_4head_v291_varn_live.py`
- `.github/workflows/validate-4head-v291-varn-live.yml`
- corrected CI run `34711859515`: SUCCESS
- adopted policy: `HEAD4_V291_COMP7_VARN_F4_N16`

Exact market path remains:

`S priority / A outside S -> frozen v283 order -> official pre-deadline 120-way odds -> original v291 Top4 composite >= 7 entry gate -> largest N<=16 with composite >=4.0 -> exact ¥10,000 Dutch`

The variable-N rule does not add races by itself and does not bypass the original v291 Top4>=7 market-entry gate.

A-LIVE frozen inference is available through:

- `head4_v273_a_live_inference.py`
- `artifacts/head4_v273_a_live_20260630.json`

A added-race rescue remains REJECTED. A may classify a layer but does not authorize bypassing v291 entry.

## Readiness audit status

The remaining one-click chain is:

`daily PRE -> current exhibition/beforeinfo -> POST -> ENV_ENTRY -> A 17 features -> v283 SECOND/conditional THIRD features -> frozen downstream inference -> market runner`

### Blocker 1 — RESOLVED: frozen downstream production artifact persisted

The original audit found that `head4_v291_downstream_inference.py` expected:

`artifacts/head4_v291_downstream_20260630.json`

but the file was not persisted on `main`.

Resolution work:

- commit `7346e9a6af26264860a08419acff5d911be7b008` added `.github/workflows/persist-4head-v291-downstream-artifact.yml`;
- the first attempt used an exact byte-hash guard, which was too strict for harmless floating-point serialization variation;
- commit `77b5a97d2ddf97def469f9d03596d4069d71c876` changed the persistence guard to the existing strict model-parity checks instead of raw byte identity;
- CI run `34714996270` completed **SUCCESS**;
- commit `672db68cf86ce91e0a30cf5ae909fa6464512a37` persisted the resulting parity-passing production artifact on `main`.

Persisted artifact state:

- policy = `HEAD4_V291_COMP7`
- frozen training cutoff = `2026-06-30`
- Jul/Aug labels used = false
- September labels used = false
- v96 production signal used = false
- POST parity max abs ~= `9.71e-17`
- ENV_ENTRY parity max abs ~= `8.33e-17`
- v283 SECOND parity max abs ~= `4.98e-13`
- v283 conditional THIRD parity max abs ~= `4.98e-13`
- parity status = `PASS`

Decision: **ACCEPT blocker-1 recovery.** This is operational plumbing only; no v291 threshold, race identity, A mapping, variable-N rule, or Dutch economics changed.

Important note: the earlier run `34707632922` failed inside exact A-LIVE curve recovery, but that path was subsequently repaired and completed in later successful recovery research. It is not the current blocker.

### Blocker 2 — ACTIVE: no verified generalized result-blind LIVE feature builder yet

A result-blind official `beforeinfo` fetch exists historically:

- `fetch_20260910_beforeinfo_only.py`
- commit `c876904a24a5a74529f621e2aedbf12e195ba3a9`

It proves official exhibition/beforeinfo can be fetched without following result links, but it is date/target-specific and only dumps page tables.

The frozen POST recipe is identifiable from `analyze_v250_4head_rebuild_baseline.py`:

- PRE features plus exhibition ST rank / boat4 ST / 4v3 ST edge
- original exhibition straight/lap/turn
- tilt4

Latest GitHub still does not expose a verified generalized causal builder that converts current-day pre-result sources into the complete exact schemas required by all of:

- POST frozen feature list
- ENV_ENTRY frozen feature list
- A-LIVE 17 feature keys
- v283 SECOND five candidate rows
- v283 conditional THIRD twenty candidate-pair rows

Historical reconstruction code such as `recover_4head_v291_exact_a_live_curves.py` operates on historical prepared research frames and must not be silently repurposed as a LIVE current-day feature builder without causal/parity validation.

Current decision: **DO NOT fabricate or refit missing LIVE features.** Keep fail-closed behavior until a generalized pre-result feature builder passes parity.

## Current status / restart point

Status: **MARKET RUNNER COMPLETE; DOWNSTREAM ARTIFACT BLOCKER RESOLVED; ONE-CLICK LIVE ORCHESTRATION STILL INCOMPLETE ONLY AT GENERALIZED RESULT-BLIND FEATURE BUILDING/PARITY.**

Next work is operational plumbing/parity only:

1. Generalize official pre-result `beforeinfo` / exhibition acquisition for arbitrary current-day race codes without following result/payout endpoints.
2. Map those sources plus frozen PRE-side inputs into the exact POST / ENV_ENTRY / A-LIVE / v283 SECOND / v283 conditional THIRD schemas without fitting.
3. Prove feature parity against frozen historical/pre-result fixtures using Apr–Jun or result-free fixtures only; Jul/Aug outcomes and September outcomes remain prohibited.
4. Generate immutable input JSON containing PRE/POST/ENV_ENTRY, A 17 features, v283 p2/conditional-third inputs plus source timestamps/hashes.
5. Feed that JSON into `run_4head_v291_varn_live.py` before deadline.
6. Add CI that fails closed on source incompleteness, schema drift, artifact absence, parity failure, odds incompleteness, or deadline violation.

No thresholds, v291 entry identities, A mapping, floor=4.0, maxN=16, or Dutch economics should be changed to work around the remaining blocker.
