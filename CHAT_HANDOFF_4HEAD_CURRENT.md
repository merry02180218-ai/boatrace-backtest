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
### Implementation
`build_4head_current_bundle.py`
- commit `6a30e0899946ed92368c4930bc2068275bfb1637`
- strict result-blind source object -> exact A-LIVE/v283 bundle.
- historical frozen A relative formula is preserved: `b4_pl_* - opponent_pl_*`.
- v283 flat mappings use `opp_*_bN_v93`, `bN_pl_*`, `st_*_bN`, current exhibition six fields, and deterministic position features.
- result/payout/odds/profit/return-like source columns are rejected.
- missing causal primitives fail closed.

Verifier `verify_4head_current_bundle.py`:
- commit `3f3eaa70cb603da78009079ef82dacc18de27b8b`
- validates relative formulas, feature mapping, frozen assembler compatibility, SECOND5/conditional20, leakage rejection, and missing-feature rejection.

CI:
- initial workflow commit `e04f9a003c5741930117c11ca53941901133c105`.
- Run `34753138305`: FAILED only because numpy was omitted from CI; no production/model rule failed.
- dependency-only fix commit `dc9c265e5ba36452be6ffd32fbddbea85de43c2c`.
- Run `34753157788`: **SUCCESS**.

Decision: **ACCEPT causal bundle adapter as production building block.**

## AUTO LIVE strict source mode — ACCEPTED
`run_4head_v291_varn_auto_live.py` updated by commit `77e816caddea21333a2f19f56a2a75dea33ddc24`.
It accepts either:
- `--bundle-json` (backward-compatible existing path), or
- `--source-json` (strict causal source -> `build_4head_current_bundle` -> frozen assembler -> existing final runner).

`verify_4head_v291_varn_auto_live.py` updated by commit `4fd65a5ed3d95f5a753f4f7beec8ea91faebb36c` to verify both paths.

Source-mode CI Run `34753243163`: **SUCCESS**.
All CI stages passed:
- syntax check
- AUTO LIVE bridge contract
- result-blind / frozen-policy guard

Decision: **ACCEPT strict source mode as production-green.**

## Verified raw/current building blocks
- `fetch_4head_v291_pre_inputs_live.py`: current result-blind `race_cards.csv` + `waku10.csv`, all active venues/races.
- `build_4head_post_live.py`: official beforeinfo tilt + BOATCAST start display + BOATCAST original exhibition, pre-race allow-list and fail-closed.
- historical `analyze_v278_4head_opponent_current_exhibition_audit.py`: exact six current exhibition fields used by v283.
- historical `analyze_v264_4head_feature_exhaustive.add_rel()`: exact 4-minus-opponent relative formulas.
- historical `analyze_v221_3head_scenario_pair.py`: defines `bN_pl_*` by freezing history before current-day results. Do not blindly ingest Sep outcomes while Sep outcome-blind constraints are in force.

## Exact remaining AUTO LIVE gap
The chain from a strict causal source object through the frozen models and existing final market/Dutch runner is now green.

The remaining upstream gap is automatic construction/acquisition of the strict source object from raw current-day inputs, specifically the flat primitives:
- v93 opponent values `opp_{grade,national,local,motor,nst}_bN_v93`
- frozen player-history values `bN_pl_*`
- prior ST values `st_{raw,raw_strength,raw_rank,corr_strength,corr_rank}_bN`
- six-boat current exhibition values
- ENV_ENTRY primitives not already supplied by PRE/POST.

## Exact next action
1. Trace the exact existing v93 + ST primitive construction from the historical/live code; reuse, do not invent formulas.
2. Resolve player-history production input without violating Sep outcome-blind rules; prefer already-frozen/precomputed causal history or an allowed current pre-race source rather than reading Sep results ad hoc.
3. Build one upstream fetch/transform command that emits `--source-json` directly from current PRE + allowed pre-race exhibition/history sources.
4. Add fixture/parity + fail-closed CI.
5. Run full raw-source -> strict source -> models -> official pre-deadline odds -> VARN -> exact 10k Dutch path and record Run IDs/commits here.
