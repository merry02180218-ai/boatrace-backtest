# CHAT HANDOFF — HEAD4 CURRENT

Updated: 2026-09-13 JST

## Source of truth

Always use latest GitHub main + latest 4-head CI over older chats/handoffs.

## Frozen production policy

- Base: `HEAD4_V291_COMP7`.
- Adopted overlay: `HEAD4_V291_COMP7_VARN_F4_N16`.
- S gate: PRE >= 0.28, POST >= 0.25, ENV_ENTRY >= 0.224790.
- Outside S only, A gate: PRE >= 0.18, POST >= 0.18, frozen `A_SCORE_LIVE >= 0.2710428764008591`.
- v283: SECOND `PLAYER_START` L2=10; conditional THIRD `COND_BASE` L2=0.3; TOP2XTOP2, alpha2=0.60.
- Base v291 entry: Top4 composite odds >= 7.0.
- Variable tickets: largest N in 4..16 whose composite odds remains >= 4.0.
- Exactly JPY 10,000/race inverse-odds Dutch with JPY100 Hamilton rounding.
- Jul/Aug 2026 outcomes NON-PRISTINE; never train/tune/select/rescue on them.
- Sep 2026 remains outcome-blind for fitting/calibration/threshold/rescue.
- v96 production signal prohibited.
- Official 120-way trifecta pre-deadline odds only. Missing/incomplete/late inputs fail closed `ERROR_NO_BET`; no post-deadline fallback.

## Accepted downstream AUTO LIVE chain

`POST -> ENV_ENTRY -> A-LIVE -> v283 SECOND/THIRD -> official pre-deadline odds -> HEAD4_V291_COMP7_VARN_F4_N16 -> exact 10k Dutch -> audit`

- Existing bridge runner: `run_4head_v291_varn_auto_live.py`.
- Existing frozen assembler: `assemble_4head_v291_varn_live_input.py`.
- Dedicated prior bridge CI: Run `34752338147` SUCCESS.

## New verified current-day causal source adapter

### `build_4head_current_bundle.py`
Commit `6a30e0899946ed92368c4930bc2068275bfb1637`.

Converts a strict result-blind source object (`flat_row` + six `current_boats` exhibition rows + ENV primitives + PRE/POST) into the exact bundle consumed by the frozen assembler.

It derives the A-LIVE relative player features with the historical frozen formula used by `analyze_v264_4head_feature_exhaustive.add_rel()`:

- `rel_pl_all_win_4v1 = b4_pl_all_win - b1_pl_all_win`
- `rel_pl_all_p2_4v1 = b4_pl_all_p2 - b1_pl_all_p2`
- `rel_pl_recent_p2_4v1 = b4_pl_recent_p2 - b1_pl_recent_p2`
- `rel_pl_recent_p2_4v3 = b4_pl_recent_p2 - b3_pl_recent_p2`

It maps the frozen v283 PLAYER_START primitives for boats `{1,2,3,5,6}` from the repo's historical flat schema:

- v93: `opp_{grade,national,local,motor,nst}_bN_v93`
- player history: `bN_pl_{all_p2,all_win,frame_p2,recent_p2,frame_win}`
- prior ST: `st_{raw,raw_strength,raw_rank,corr_strength,corr_rank}_bN`
- current exhibition: `cur_ex`, `cur_st`, `cur_orig_lap`, `cur_orig_turn`, `cur_orig_straight`, `cur_orig_avg`
- deterministic position features from boat number.

Leakage guard rejects source rows containing result/payout/odds/profit/return-like columns. Missing causal primitives fail closed.

### Verifier

`verify_4head_current_bundle.py`, commit `3f3eaa70cb603da78009079ef82dacc18de27b8b`.

It verifies relative formulas, schema mapping, frozen assembler compatibility, v283 SECOND5/conditional20 output, result leakage rejection, and missing-feature rejection.

### CI

Initial workflow commit `e04f9a003c5741930117c11ca53941901133c105`.

- Run `34753138305` FAILED only because CI omitted numpy (`ModuleNotFoundError: numpy`). Production logic was not weakened.
- Dependency-only fix commit `dc9c265e5ba36452be6ffd32fbddbea85de43c2c`.
- Run `34753157788` SUCCESS.

Decision: **ACCEPT current causal bundle adapter as a production building block.**

## AUTO LIVE runner source-mode connection

Commit `77e816caddea21333a2f19f56a2a75dea33ddc24` updated `run_4head_v291_varn_auto_live.py` so it accepts either:

- `--bundle-json` (existing compatibility path), or
- `--source-json` (strict causal source -> `build_4head_current_bundle` -> frozen assembler -> existing final runner).

Commit `4fd65a5ed3d95f5a753f4f7beec8ea91faebb36c` extended `verify_4head_v291_varn_auto_live.py` to verify both legacy bundle mode and strict source mode through the exact frozen runner-input contract.

Source-mode CI Run `34753243163` is the validation run for this connection. At the time of this handoff write it was still running; latest GitHub Actions conclusion must be checked before calling source mode production-green.

## Exact current remaining gap

The model/assembler/orchestrator path is now connected from a strict causal source object through final production runner. The unresolved upstream work is **automatic acquisition/construction of that source object from current-day raw data**.

Verified existing raw/current building blocks:

- `fetch_4head_v291_pre_inputs_live.py` fetches current result-blind `race_cards.csv` + `waku10.csv` for all active venues/races.
- `build_4head_post_live.py` fetches official beforeinfo tilt + BOATCAST start display + BOATCAST original exhibition with pre-race allow-list/fail-closed behavior.
- Historical `v221` player traits freeze state before current-day results and define `bN_pl_*`; do **not** blindly read Sep outcomes while Sep outcome-blind constraints are in force.
- Historical current exhibition mapping is defined in `analyze_v278_4head_opponent_current_exhibition_audit.py` via the six fields used above.

## Exact next action

1. Check Run `34753243163`; if failed, fix source-mode bridge without changing frozen production thresholds/policy.
2. Trace and reuse the exact current-day construction for v93/player/ST flat primitives from existing PRE/history code; do not invent formulas.
3. Build an upstream fetch/transform command that emits the strict `--source-json` object directly from current PRE + allowed pre-race exhibition sources.
4. Add fail-closed CI/fixture parity and then run the full source -> model -> pre-deadline odds -> Dutch chain.
5. Record every failure/success Run ID, commit SHA, adoption/rejection reason, and next resume point here before ending a work session.
