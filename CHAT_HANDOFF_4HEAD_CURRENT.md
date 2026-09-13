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
Initial builder `build_4head_v283_current_exhibition_live.py`, commit `4f74e0bdd499ed5706917e4eb9e1f30031e422a1`.

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

Initial verifier `verify_4head_v283_current_exhibition_live.py`, commit `0008c63e78ea7e66a447074b2f79077f7b211f48`.
Workflow commit `fcdc65bd50c0f0175772c570e491b519ad6d1894`.
Initial CI Run `34753369345`: **SUCCESS**.

### Frozen v90 ST-flat extension — ACCEPTED
- builder extension commit `1b1237033ccb73dfb9f85e181ec53234826cc846`
- verifier extension commit `747fd85a8e30ce728f42aff76d1036db3c8292db`
- current exhibition schema now also emits exact v90 flat primitives for all six boats:
  - `st_raw_bN`
  - `st_raw_rank_bN`
  - `st_corr_rank_bN`
  - `st_raw_strength_bN`
  - `st_corr_strength_bN`
- CI Run `34753443662`: **SUCCESS**.

Decision: **ACCEPT automatic `current_boats` + frozen v90 `st_flat` construction.**

## v93 opponent primitives LIVE — ACCEPTED
`build_4head_v93_primitives_live.py`, commit `d9baa169d6f72f65ab80fdb9a8597863d89c1969`.
Verifier commit `9695ac3d231e90e0c56099818e307640077be09d`.
Workflow commit `e831c7f12621bb7ef900ae888a072b890c3a69b3`.

- builds exact historical v93 opponent primitives from current result-blind `race_cards.csv` + `waku10.csv` + accepted current exhibition/ST-flat object.
- outputs `opp_score_bN_v93` and exact grade/national/local/motor/waku/nst/direct parts for boats 1,2,3,5,6.
- odds/results/payouts are not read; v96 remains prohibited.
- CI Run `34753470120`: **SUCCESS**.

Decision: **ACCEPT v93 primitive live builder.**

## Verified raw/current building blocks
- `fetch_4head_v291_pre_inputs_live.py`: current result-blind `race_cards.csv` + `waku10.csv` for all active venues/races.
- `build_4head_post_live.py`: official beforeinfo tilt + BOATCAST start display + BOATCAST original exhibition, pre-race allow-list and fail-closed.
- `analyze_v93_4corner_second_third.py`: exact opponent v93 scoring primitives/formula.
- `analyze_v90_exhibition_st_10month.py`: exact prior-only ST lane-bias + raw/corrected rank/strength semantics.
- `analyze_v264_4head_feature_exhaustive.add_rel()`: exact 4-minus-opponent relative formulas.
- `analyze_v221_3head_scenario_pair.py`: defines `bN_pl_*` by freezing history before current-day results.

## Exact remaining AUTO LIVE gap
The strict source -> frozen models -> final market/Dutch runner path is green. `current_boats`, frozen v90 `st_flat`, and v93 opponent primitives are now automatic and CI-green.

Remaining upstream construction:
- frozen causal player-history values `bN_pl_*`
- ENV_ENTRY primitives not already supplied by PRE/POST
- one upstream command that merges current PRE + accepted exhibition/ST + v93 + player history + ENV_ENTRY inputs into the strict `--source-json` object
- full raw-source -> official pre-deadline odds -> VARN -> exact 10k Dutch dry/live validation.

## Exact next action
1. Implement a production-safe causal `bN_pl_*` builder preserving v221 semantics: state frozen before target race day; prior outcomes may only update causal feature history, never Sep model fitting/calibration/threshold/rescue.
2. Add explicit audit metadata proving history cutoff `< target_date`, no same-day outcome use, no odds/payout use, and no tuning path.
3. Wire accepted `st_flat` + v93 + `current_boats` + player history into one strict source-object assembler.
4. Resolve remaining ENV_ENTRY primitives from existing PRE/POST/current pre-race sources without inventing semantics.
5. Add fixture/parity + fail-closed CI, then run full chain and record all Run IDs/commits here.

## Work session started — 2026-09-13 JST
Status: **IN PROGRESS**

Before-work plan for this session:
1. Re-read latest main and latest 4-head Actions before changing production code.
2. Verify whether the v283 ST-flat extension and v93 primitive builder already landed after this handoff; if landed, verify their newest CI rather than duplicating work.
3. If CI is failed, inspect logs and fix/rerun without changing frozen production thresholds/policy.
4. Then implement the next missing causal upstream block, prioritizing `bN_pl_*` production-safe construction and wiring of generated ST/v93/current exhibition into one strict source object.
5. Add or extend fail-closed/parity CI for the new block.
6. At session end, replace this status with **COMPLETED** or **BLOCKED**, and record exact commit SHAs, Run IDs, decisions, remaining gap, and the next resume point.

### Progress checkpoint
- v283 ST-flat extension verified green: Run `34753443662`.
- v93 primitive builder verified green: Run `34753470120`.
- Next active implementation: causal `bN_pl_*` production builder.
