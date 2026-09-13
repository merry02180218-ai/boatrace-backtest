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
- Audit must persist before any result retrieval.

## Accepted downstream production chain
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
Initial verifier `verify_4head_v283_current_exhibition_live.py`, commit `0008c63e78ea7e66a447074b2f79077f7b211f48`.
Workflow commit `fcdc65bd50c0f0175772c570e491b519ad6d1894`.
Initial CI Run `34753369345`: **SUCCESS**.

Automatically constructs for all six boats:
- `cur_ex`, `cur_st`, `cur_orig_lap`, `cur_orig_turn`, `cur_orig_straight`, `cur_orig_avg`.

Result-blind sources:
- official BOAT RACE beforeinfo display time,
- BOATCAST start display,
- BOATCAST original exhibition,
- prior-only ST lane bias rebuilt strictly before target day.

### Frozen v90 ST-flat extension — ACCEPTED
- builder extension commit `1b1237033ccb73dfb9f85e181ec53234826cc846`
- verifier extension commit `747fd85a8e30ce728f42aff76d1036db3c8292db`
- emits for all six boats: `st_raw_bN`, `st_raw_rank_bN`, `st_corr_rank_bN`, `st_raw_strength_bN`, `st_corr_strength_bN`.
- CI Run `34753443662`: **SUCCESS**.

Decision: **ACCEPT automatic current exhibition + frozen v90 ST-flat.**

## v93 opponent primitives LIVE — ACCEPTED
`build_4head_v93_primitives_live.py`, commit `d9baa169d6f72f65ab80fdb9a8597863d89c1969`.
Verifier commit `9695ac3d231e90e0c56099818e307640077be09d`.
Workflow commit `e831c7f12621bb7ef900ae888a072b890c3a69b3`.

- exact historical v93 opponent primitives from current result-blind race_cards + waku10 + accepted current exhibition/ST-flat.
- outputs `opp_score_bN_v93` and grade/national/local/motor/waku/nst/direct parts for boats 1,2,3,5,6.
- odds/results/payouts not read; v96 prohibited.
- CI Run `34753470120`: **SUCCESS**.

Decision: **ACCEPT v93 primitive live builder.**

## Causal v221-style player history LIVE — ACCEPTED
Builder `build_4head_player_history_live.py`:
- initial builder commit `4b1217fdb4ea18942a586edcd85e59d79389629d`
- verifier commit `483899e0ed46bc36f4de162b7c3963d75ac52023`
- workflow commit `a2c253c3ff079aec4843ad8c662238228ddc6e22`
- initial CI Run `34762532871`: **SUCCESS**.

Exact generated fields for all six boats:
- `bN_pl_all_win`
- `bN_pl_all_p2`
- `bN_pl_frame_win`
- `bN_pl_frame_p2`
- `bN_pl_recent_p2`

Causality/audit contract:
- default history start `2025-10-01`.
- history only while date `< target_date`; `history_end = target_date - 1 day`.
- target-day outcomes never loaded.
- prior outcomes are used only to update causal pre-race player-state features, never fitting/calibration/threshold/ROI selection/rescue.
- no odds/payout use; v96 prohibited.

Metadata hardening commit `ab31a50f5aee2dacbe58ee252b145ca4de409bd3` explicitly adds `result_blind: true`.
Latest player-history CI Run `34764112242`: **SUCCESS**.

Decision: **ACCEPT causal player-history builder as production-green.**

## Strict current source-object assembler — ACCEPTED
`assemble_4head_current_source.py`, commit `0b2556cf3e4200c38f26a5aadc5e1f2c624b642d`.
Verifier `verify_4head_current_source.py`, commit `3f4ea9b868227457b56685a1a6138f322c366ea9`.
Workflow `.github/workflows/validate-4head-current-source.yml`, commit `483707ca437fad2a9aef3f23ad4621f85785dbfd`.
CI Run `34764140752`: **SUCCESS**.

It merges:
- causal base flat row,
- exact ENV_ENTRY primitive payload,
- accepted six-boat current exhibition,
- accepted frozen v90 ST-flat,
- accepted v93 opponent primitives,
- accepted causal player history,
into the exact strict `--source-json` consumed by `run_4head_v291_varn_auto_live.py`.

Guards:
- all component race codes must match.
- generated ST/v93/player values override stale/manual duplicates.
- component result-blind metadata is enforced.
- same-day outcome use rejected.
- Jul/Aug/Sep prohibited label-use flags rejected.
- existing production `build_4head_current_bundle.build()` is reused as final completeness/leakage guard.
- market/result-like flat columns fail closed.

Decision: **ACCEPT strict source-object assembler as production-green.**

## Existing ENV_ENTRY assembler — ACCEPTED, source acquisition still incomplete
`build_4head_env_entry_live.py`, commit `7fad596ac8ae530307546239716aa082cad623b7`.
Verifier commit `9f9e04a57f399ec00c07d190b497f78993d61faf`.
Workflow commit `894b432d5ca6ca81fb7ff441f71b662316ee964c`.

Exact frozen ENV_ENTRY row:
`PRE, POST, preview_comp, relative_deg, wind_speed, wind_adjust_points, entry_confirmed_same, entry_course_preview, has_orig, has_stt, has_tkz, tilt, tilt_bonus, v91_ex, v91_st_corr, v91_st_raw, v91_straight, score_BASE_v91, score_CORR20_v91, score_RAW20_v91, score_wind_v83, history_adjust_online, history_pct_online, p4_joint, post_x_entry_same`.

Derived internally:
- PRE
- POST
- `p4_joint = PRE * POST`
- `post_x_entry_same = POST * entry_confirmed_same`

Therefore the unresolved raw acquisition layer is the exact causal generation of the other 21 primitives. Missing values must fail closed; do not invent defaults/formulas.

## Verified raw/current building blocks
- `fetch_4head_v291_pre_inputs_live.py`: current result-blind race_cards + waku10 for all active venues/races.
- `build_4head_post_live.py`: official beforeinfo tilt + BOATCAST start display + BOATCAST original exhibition, pre-race allow-list and fail-closed.
- `analyze_v93_4corner_second_third.py`: exact opponent v93 scoring formula.
- `analyze_v90_exhibition_st_10month.py`: exact prior-only ST lane-bias + raw/corrected rank/strength semantics.
- `analyze_v264_4head_feature_exhaustive.add_rel()`: exact 4-minus-opponent relative formulas.
- `analyze_v221_3head_scenario_pair.py`: historical player-history semantics now reproduced by accepted live builder.

## Failures/rejections retained for audit
- Run `34753138305`: dependency-only CI failure (numpy missing); fixed without changing policy/model.
- No frozen threshold, ticket rule, or Jul/Aug/Sep outcome policy has been weakened to obtain any later PASS.

## Exact remaining AUTO LIVE gap
Automatic and CI-green now:
- current PRE raw inputs,
- current exhibition,
- frozen v90 ST-flat,
- v93 opponent primitives,
- causal v221-style player history,
- strict component merger into `--source-json`,
- strict source -> frozen models -> official-market/Dutch runner.

Still unfinished:
1. exact causal current-day acquisition/reproduction of the 21 ENV_ENTRY/base primitives, especially v91/v83/history/entry/wind primitives; copy historical semantics exactly, do not approximate.
2. one orchestration command that executes all accepted upstream builders and emits the final strict source object without manual JSON preparation.
3. full raw-source -> official pre-deadline 120-way odds -> VARN -> exact JPY10,000 Dutch dry/live validation with audit persisted before result retrieval.

## Exact next action
1. Locate historical production formulas/source lineage for each unresolved ENV_ENTRY primitive (`preview_comp`, `relative_deg`, wind/entry flags, v91/v83 scores, `history_adjust_online`, `history_pct_online`).
2. Implement a fail-closed causal primitive builder only after exact semantics are verified from repository code/data lineage.
3. Add fixture/parity/source-allow-list CI.
4. Wire it into a one-command upstream orchestrator -> `assemble_4head_current_source.py` -> `run_4head_v291_varn_auto_live.py --source-json`.
5. Run end-to-end dry/live validation and record exact Run IDs/commits here.

## Work session — 2026-09-13 JST
Status: **IN PROGRESS**

Latest completed milestones:
- player-history latest CI Run `34764112242`: SUCCESS.
- strict current source CI Run `34764140752`: SUCCESS.
- next active implementation: exact causal ENV_ENTRY/base primitive acquisition.
