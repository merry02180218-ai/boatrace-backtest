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

## New readiness audit finding — IMPORTANT BLOCKER

The remaining one-click chain is not production-ready yet:

`daily PRE -> current exhibition/beforeinfo -> POST -> ENV_ENTRY -> A 17 features -> v283 SECOND/conditional THIRD features -> frozen downstream inference -> market runner`

Two concrete blockers were confirmed from latest GitHub.

### Blocker 1 — frozen downstream production artifact is not persisted on main

`head4_v291_downstream_inference.py` defaults to:

`artifacts/head4_v291_downstream_20260630.json`

but that file is currently absent from the repository (`fetch_file` returns 404).

The inference module itself is production-safe/inference-only and expects this artifact for:

- POST frozen logistic state
- ENV_ENTRY frozen logistic state
- v283 SECOND frozen listwise state
- v283 conditional THIRD frozen listwise state

The successful exact A-LIVE recovery workflow `34708490537` uploaded an artifact bundle, but inspection of that bundle showed only:

- `artifacts/head4_v291_downstream_parity_20260630.json`
- A-LIVE identity/recovery audits
- all-N research curves/results

It did **not** contain `artifacts/head4_v291_downstream_20260630.json` itself.

Therefore a clean checkout cannot run the intended frozen downstream inference using its default production artifact.

Do not replace this artifact with a newly refit approximation. The previous clean rebuild path already showed small nondeterministic v283 THIRD parity drift (`9.04380706659e-05`) and correctly failed closed. Do not relax that guard merely to create a file.

### Blocker 2 — no verified generalized result-blind LIVE feature builder found

A result-blind official `beforeinfo` fetch exists historically:

- `fetch_20260910_beforeinfo_only.py`
- commit `c876904a24a5a74529f621e2aedbf12e195ba3a9`

It proves official exhibition/beforeinfo can be fetched without following result links, but it is date/target-specific and only dumps page tables.

The frozen POST recipe is identifiable from `analyze_v250_4head_rebuild_baseline.py`:

- PRE features plus exhibition ST rank / boat4 ST / 4v3 ST edge
- original exhibition straight/lap/turn
- tilt4

However, latest GitHub does not currently expose a verified generalized causal builder that converts current-day pre-result sources into the complete exact schemas required by all of:

- POST frozen feature list
- ENV_ENTRY frozen feature list
- A-LIVE 17 feature keys
- v283 SECOND five candidate rows
- v283 conditional THIRD twenty candidate-pair rows

Historical reconstruction code such as `recover_4head_v291_exact_a_live_curves.py` operates on historical prepared research frames and must not be silently repurposed as a LIVE current-day feature builder without causal/parity validation.

## Decision

Status: **MARKET RUNNER COMPLETE; ONE-CLICK LIVE ORCHESTRATION BLOCKED / NOT YET COMPLETE.**

Do not claim full automatic LIVE operation until both blockers are resolved.

The correct next work is operational plumbing/parity only, not model-rule modification:

1. Recover/persist the exact previously validated downstream artifact, or produce it through a deterministic build whose parity guard passes unchanged.
2. Build a generalized result-blind current-day feature builder using only pre-result sources.
3. Prove feature parity against frozen historical/pre-result fixtures without using Jul/Aug outcomes or any September results.
4. Generate immutable input JSON containing PRE/POST/ENV_ENTRY, A 17 features, v283 p2/conditional-third inputs plus source timestamps/hashes.
5. Feed that JSON into `run_4head_v291_varn_live.py` before deadline.
6. Add CI that fails closed on artifact absence/schema drift/source incompleteness/deadline violation.

No thresholds, v291 entry identities, A mapping, floor=4.0, maxN=16, or Dutch economics should be changed to work around these blockers.
