# CHAT HANDOFF — HEAD4 CURRENT

Updated: 2026-09-14 JST

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
Workflow commit `e831c7f12621bb7ff441f71b662316ee964c`.

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

## Existing ENV_ENTRY assembler — ACCEPTED
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

## Exact causal ENV_ENTRY primitive semantics — ACCEPTED
Builder `build_4head_env_v91_primitives_live.py` now reproduces the 21 primitive semantics from frozen v74/v83/v91 lineage.

Initial exact v74/v91 primitive builder commit:
- `f5fa00d0e1181e2aab4ad68cf2a4194f6d3f7e66`
Tilt parity correction:
- `be28071e00a99aedb95ba65fe944ff930a22336e`
Verifier:
- `ed3c1e62374d9e398f183a811535dec340562e63`
CI workflow:
- `df8a4e2a48e073655aac725c1b51f1b9573c7d4f`
Prior parity CI:
- Run `34767423066`: **SUCCESS**.

### Frozen v83 HEAD4 wind mapping — ACCEPTED
Historical source was recovered from v83 commits `1cf29fddd2b5db088d810e5c32e412fa688713f9` and result commit `7c9a85ba492b07e4b5cd4d9c3623551a8ef52d4f`.

The mapping was learned only on old period `2025-11-01..2026-05-31` with v83's frozen rule:
- per model x relative-wind x speed cell;
- favorable if `n>=40` and head-rate lift >= +3pt vs old model baseline;
- unfavorable if `n>=40` and lift <= -3pt;
- otherwise neutral;
- Jul/Aug/recent results are not used to classify the cells.

For HEAD4 the only non-neutral frozen cells are:
- `追い_0-2m` => `-2`
- `向かい_0-2m` => `-2`
- `左横_3-4m` => `+2`
- every other valid HEAD4 wind cell => `0`

Production builder now derives relative wind, speed bin and `wind_adjust_points` internally; no manual learned wind label is required.
- implementation commit `d7109c1eea6ffb9a28855b185888b6350373a0e9`
- verifier commit `8e86a9e1bbcf03295cdab83db85b2a3ff0ee1164`
- CI Run `34767924924`: **SUCCESS**.

Decision: **ACCEPT frozen v83 wind replay. The prior 21-primitive semantic blocker is closed.**

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
- exact v74/v83/v91 ENV primitive semantics including frozen old-period wind mapping,
- strict component merger into `--source-json`,
- strict source -> frozen models -> official-market/Dutch runner.

Still unfinished:
1. exact automatic acquisition/assembly of the primitive builder context (`history_prior1`, `history_prior2`, prior-only history population, tilt/entry/wind flags) from accepted raw sources so no manual context JSON is required.
2. one orchestration command that executes all accepted upstream builders and emits the final strict source object without manual JSON preparation.
3. full raw-source -> official pre-deadline 120-way odds -> VARN -> exact JPY10,000 Dutch dry/live validation with audit persisted before result retrieval.

## Exact next action
1. Build a causal current-race ENV context adapter from accepted pre-race sources and prior-only v74 history replay; target-day results must never be read.
2. Feed that context + accepted current exhibition into `build_4head_env_v91_primitives_live.py`, then into `build_4head_env_entry_live.py`.
3. Wire all accepted components into one upstream orchestration command -> `assemble_4head_current_source.py` -> `run_4head_v291_varn_auto_live.py --source-json`.
4. Run end-to-end dry/live validation and record exact Run IDs/commits here.

## Work session — 2026-09-13 JST
Status: **IN PROGRESS**

Latest completed milestones:
- player-history latest CI Run `34764112242`: SUCCESS.
- strict current source CI Run `34764140752`: SUCCESS.
- next active implementation: exact causal ENV_ENTRY/base primitive acquisition.

## Work session — 2026-09-14 JST — START RECORD
Status: **IN PROGRESS**

User-mandated workflow: record intended work here before implementation, and record implementation/results/restart point here again before ending the work session.

Planned work unit:
1. Re-read latest main/4-head CI state and treat this handoff plus latest GitHub as source of truth.
2. Trace exact historical formulas and source lineage for all unresolved ENV_ENTRY/base primitives, with special focus on `preview_comp`, `relative_deg`, wind/entry fields, v91/v83 scores, `history_adjust_online`, and `history_pct_online`.
3. Implement only semantics that can be verified exactly from existing repository code/data; missing or unverifiable inputs must fail closed rather than use guessed defaults.
4. Add parity/fixture/source-allow-list verification and CI where the repository lineage supports implementation.
5. If the primitive layer becomes production-green, wire the next safe upstream orchestration step; otherwise stop at the exact verified boundary.
6. Before ending this session, append files changed, commits, CI/run outcomes, any rejection/blocker, and the exact restart point to this handoff.

## Work session — 2026-09-14 JST — PROGRESS / HANDOFF UPDATE
Status: **PRIMITIVE SEMANTICS COMPLETE; AUTO CONTEXT WIRING NEXT**

Completed in this work unit:
- recovered the exact v83 old-period-only wind classification source and verified it did not use Jul/Aug recent outcomes for cell classification;
- restored the frozen HEAD4 wind +/-2 mapping inside `build_4head_env_v91_primitives_live.py`;
- removed the need to manually inject `wind_adjust_points`;
- added exact relative-wind boundary, wind-speed bin and frozen-cell parity checks;
- CI Run `34767924924` completed **SUCCESS** on verifier commit `8e86a9e1bbcf03295cdab83db85b2a3ff0ee1164`.

No frozen threshold/model/ticket rule changed. Jul/Aug remain NON-PRISTINE and were not used for reclassification/tuning.

Exact restart point:
- implement automatic causal ENV context acquisition (especially prior-only v74 history state + current tilt/entry/wind extraction), then wire the one-command upstream orchestrator and run end-to-end dry/live validation.

## Work session — 2026-09-14 JST — AUTO CONTEXT + FULL ORCHESTRATION COMPLETE
Status: **PRODUCTION WIRING CI-GREEN; LIVE MARKET VALIDATION AWAITS AN ACTIVE PRE-RACE TARGET**

Completed after the prior progress record:

### 1. Automatic current ENV context — COMPLETE
Added `build_4head_env_context_live.py`.
- commit: `8589c52110c87f5874412619a4d4f929f607a2e6`
- exact pinned BOATCAST parser lineage: BoatraceCSV commit `563c69ccd28853b8b4953489c673877a9dfeb4e8`.
- `bc_j_stt`: `[0]=entry course`, `[1]=boat number`; current boat4 exhibition course is obtained directly.
- `bc_sui`: current pre-race weather only; `[3]=wind direction`, `[4]=wind speed`.
- LIVE weather explicitly does not use post-race `bc_rs1_2`.
- current tilt comes from `bc_j_tkz`.
- prior-only v74 history context is replayed in exact historical update order strictly while `day < target_date`.
- target-day results are never loaded by the v74 history replay.
- missing/malformed current source fails closed.

Verifier `verify_4head_env_context_live.py`:
- initial commit `f0955f675c13ee95a7c2b3c1891a83883486e55b`.
- initial CI Run `34768312668`: **FAILED only because the verifier matched the literal string `bc_rs1_2` inside an explanatory comment**; syntax and implementation checks passed up to that assertion.
- verifier-only correction commit `bde38f2da9b58c152b5386aaada0faad0dc48e78`; no production/model rule changed.

### 2. Automatic 25-field ENV_ENTRY — COMPLETE
Added `build_4head_env_entry_auto_live.py`.
- commit `fdcc89cbfaa3f74ea082b9bfc24013320c8a0515`.
- inputs are target date/JCD/R, current race-card CSV, frozen PRE and POST.
- automatically executes accepted current exhibition -> ENV context -> exact 21 v74/v83/v91 primitives -> frozen 25-field ENV_ENTRY inference.
- no manual context/primitive JSON is required.

Verifier:
- `verify_4head_env_entry_auto_live.py`, commit `72a76aa358632af67e0759cec71fcd4c781f689b`.

CI extension commit:
- `8a37b615b7cef71ca9a3caaabd0a680985ab4c88`.
- CI Run `34768398670`: **SUCCESS**.

Decision: **ACCEPT automatic ENV context + automatic ENV_ENTRY as CI-green.**

### 3. Full one-command upstream LIVE orchestrator — COMPLETE
Added `run_4head_full_auto_live.py`.
- implementation commit `3bc28f573b44aaf7cdbf6f3f6f687b1d8acd87ae`.
- verifier `verify_4head_full_auto_live.py`, commit `9488bb013b45d9221629c79229603cc31f7697f0`.
- CI workflow extension commit `5442c69ef3f3e17ceedabe359bf379fea70ed9a0`.
- CI Run `34768557091`: **SUCCESS**; syntax + ENV context + automatic ENV_ENTRY + full one-command LIVE wiring all passed.

Required prepared same-day inputs are only the already-accepted PRE outputs:
- `current_input/v291/YYYYMMDD/race_cards.csv`
- `current_input/v291/YYYYMMDD/waku10.csv`
- `live_outputs/v291/YYYYMMDD/pre_scan.csv`

For a selected race the new orchestrator now automatically performs:
1. read frozen PRE probability and PRE causal feature row;
2. fetch current POST exhibition sources and calculate frozen POST probability;
3. build accepted six-boat exhibition + v90 ST-flat;
4. build exact current ENV context and frozen v83 wind mapping;
5. build exact 21 ENV primitives and frozen ENV_ENTRY;
6. build v93 opponent primitives;
7. build causal v221-style player-history primitives;
8. assemble strict `--source-json` with existing leakage/completeness guards;
9. invoke `run_4head_v291_varn_auto_live.py --source-json`;
10. in non-prepare-only mode, the already-accepted final runner owns official pre-deadline 120-way odds, VARN N=4..16, exact JPY10,000 inverse-odds Dutch/Hamilton rounding and audit.

No HEAD4 threshold, model coefficient, ticket rule, wind rule, A/S rule, or ROI rule was changed in this wiring work.

### Current exact status
The previous two source-acquisition/orchestration gaps are now closed in code and CI:
- automatic ENV context: **DONE**;
- automatic ENV_ENTRY: **DONE**;
- one-command upstream source orchestration: **DONE**;
- handoff/manual JSON preparation between these layers: **removed**.

The only remaining validation item is an actual active-race market run using same-day PRE artifacts plus published exhibition data and a real future deadline, so the final runner can fetch the official pre-deadline 120-way odds and persist the real audit. Do not simulate or substitute post-deadline odds for that validation.

### Exact next restart point
1. After the same-day PRE workflow has produced `race_cards.csv`, `waku10.csv`, and `pre_scan.csv`, choose an eligible/current target race whose exhibition is published and deadline is still in the future.
2. First run `run_4head_full_auto_live.py ... --prepare-only` and confirm strict source/A-LIVE/v283 preparation succeeds.
3. Then, while still before the real deadline, run the same command without `--prepare-only` and with the exact `--deadline-jst`.
4. Confirm official 120-way odds completeness, VARN variable ticket selection, exact JPY10,000 Dutch allocation, and audit persistence before any result retrieval.
5. Record the actual live Run/command/audit outcome here. If no valid current target exists, fail closed and wait for the next pre-race window; never backfill with post-deadline market data.
