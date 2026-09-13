# CHAT HANDOFF — HEAD4 CURRENT

Updated: 2026-09-13 JST

## Source of truth
Always use latest GitHub main + latest 4-head CI over older chats/handoffs.

## Frozen production policy
- Base: `HEAD4_V291_COMP7`.
- Adopted overlay: `HEAD4_V291_COMP7_VARN_F4_N16`.
- S gate: PRE >= 0.28, POST >= 0.25, ENV_ENTRY >= 0.224790.
- Outside S only: PRE >= 0.18, POST >= 0.18, frozen `A_SCORE_LIVE >= 0.2710428764008591`.
- v283: SECOND `PLAYER_START` L2=10; conditional THIRD `COND_BASE` L2=0.3; TOP2XTOP2 alpha2=0.60.
- Base v291 entry: Top4 composite >= 7.0.
- Variable tickets: largest N in 4..16 whose composite remains >= 4.0.
- Exactly JPY10,000/race inverse-odds Dutch with JPY100 Hamilton rounding.
- Jul/Aug 2026 outcomes NON-PRISTINE; never train/tune/select/rescue on them.
- Sep 2026 remains outcome-blind for fitting/calibration/threshold/rescue.
- v96 production signal prohibited.
- Official 120-way trifecta pre-deadline odds only. Missing/incomplete/late inputs fail closed `ERROR_NO_BET`; no post-deadline fallback.

## Accepted production chain
`POST -> ENV_ENTRY -> A-LIVE -> v283 SECOND/THIRD -> official pre-deadline odds -> HEAD4_V291_COMP7_VARN_F4_N16 -> exact 10k Dutch -> audit`

- Existing bridge runner: `run_4head_v291_varn_auto_live.py`.
- Existing frozen assembler: `assemble_4head_v291_varn_live_input.py`.
- Prior downstream bridge CI Run `34752338147`: **SUCCESS**.

## Current-day causal source adapter — ACCEPTED
`build_4head_current_bundle.py`, commit `6a30e0899946ed92368c4930bc2068275bfb1637`.

- strict result-blind source object -> exact A-LIVE/v283 bundle.
- historical frozen relative player formula preserved: `b4_pl_* - opponent_pl_*`.
- v283 flat mappings use `opp_*_bN_v93`, `bN_pl_*`, `st_*_bN`, current exhibition six fields, deterministic position features.
- result/payout/odds/profit/return-like columns are rejected; missing causal primitives fail closed.

Verifier `verify_4head_current_bundle.py`, commit `3f3eaa70cb603da78009079ef82dacc18de27b8b`.

CI:
- Run `34753138305`: FAILED only because numpy was omitted from CI; no production/model rule failed.
- dependency-only fix commit `dc9c265e5ba36452be6ffd32fbddbea85de43c2c`.
- Run `34753157788`: **SUCCESS**.

Decision: **ACCEPT causal bundle adapter.**

## AUTO LIVE strict source mode — ACCEPTED
`run_4head_v291_varn_auto_live.py` source-mode commit `77e816caddea21333a2f19f56a2a75dea33ddc24`.

Accepts either:
- `--bundle-json`, or
- `--source-json` -> causal bundle builder -> frozen assembler -> existing final runner.

Verifier source-mode commit `4fd65a5ed3d95f5a753f4f7beec8ea91faebb36c`.

- Source-mode CI Run `34753243163`: **SUCCESS**.
- syntax, AUTO LIVE contract, result-blind guard and frozen-policy guard all passed.

Decision: **ACCEPT strict source mode as production-green.**

## v283 six-boat current exhibition LIVE — ACCEPTED
`build_4head_v283_current_exhibition_live.py`, commit `4f74e0bdd499ed5706917e4eb9e1f30031e422a1`.

It automatically constructs the six current v283 exhibition fields for every boat:
- `cur_ex`
- `cur_st`
- `cur_orig_lap`
- `cur_orig_turn`
- `cur_orig_straight`
- `cur_orig_avg`

Result-blind source semantics:
- official BOAT RACE `beforeinfo` for display time,
- BOATCAST start display,
- BOATCAST original exhibition,
- prior-only ST lane bias rebuilt from repository STT snapshots strictly before the target day using v90 update order,
- existing `CORR` lane/frame corrections + `corrected_direct` rank semantics reused,
- no result/payout/odds endpoint.

Verifier `verify_4head_v283_current_exhibition_live.py`, commit `0008c63e78ea7e66a447074b2f79077f7b211f48`.
Workflow commit `fcdc65bd50c0f0175772c570e491b519ad6d1894`.
CI Run `34753369345`: **SUCCESS**.

Decision: **ACCEPT automatic `current_boats` construction.**

## Verified raw/current building blocks
- `fetch_4head_v291_pre_inputs_live.py`: current result-blind `race_cards.csv` + `waku10.csv` for all active venues/races.
- `build_4head_post_live.py`: official beforeinfo tilt + BOATCAST start display + BOATCAST original exhibition, pre-race allow-list and fail-closed.
- `analyze_v93_4corner_second_third.py`: exact opponent v93 scoring primitives/formula.
- `analyze_v90_exhibition_st_10month.py`: exact prior-only ST lane-bias + raw/corrected rank/strength semantics.
- `analyze_v264_4head_feature_exhaustive.add_rel()`: exact 4-minus-opponent relative formulas.
- `analyze_v221_3head_scenario_pair.py`: defines `bN_pl_*` by freezing history before current-day results. Do not blindly ingest Sep outcomes while Sep outcome-blind constraints are in force.

## Exact remaining AUTO LIVE gap
The strict source -> frozen models -> final market/Dutch runner path is green, and `current_boats` is now automatic.

Remaining upstream construction:
- v93 opponent values `opp_{grade,national,local,motor,nst}_bN_v93`
- flat ST values `st_{raw,raw_strength,raw_rank,corr_strength,corr_rank}_bN` wired into the source object (formula is now identified)
- frozen player-history values `bN_pl_*`
- ENV_ENTRY primitives not already supplied by PRE/POST.

## Exact next action
1. Implement v90 ST flat primitive builder and v93 opponent primitive builder from current `race_cards/waku10` + current exhibition, reusing exact historical formulas.
2. Resolve `bN_pl_*` production source without violating Sep outcome-blind rules; use frozen/precomputed causal history or an allowed pre-race source, not ad-hoc Sep outcome tuning.
3. Build one upstream command emitting `--source-json` directly from current PRE + allowed pre-race exhibition/history sources.
4. Add fixture/parity + fail-closed CI.
5. Run full raw-source -> strict source -> models -> official pre-deadline odds -> VARN -> exact 10k Dutch and record all Run IDs/commits here.
