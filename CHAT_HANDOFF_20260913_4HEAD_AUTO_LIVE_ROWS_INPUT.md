# CHAT HANDOFF — 2026-09-13 — HEAD4 v291 AUTO LIVE rows/input

## Production policy — DO NOT CHANGE

- Base: `HEAD4_V291_COMP7`.
- Adopted overlay: `HEAD4_V291_COMP7_VARN_F4_N16`.
- Entry remains frozen v291 Top4 composite odds >= **7.0**.
- Ticket count remains largest `N=4..16` with selected composite odds >= **4.0**.
- Stake remains exactly **JPY10,000/race**, inverse-odds Dutch, JPY100 Hamilton rounding.
- Jul/Aug outcomes remain **NON-PRISTINE** and are prohibited from LIVE builder training/tuning.
- September outcomes remain **outcome-blind**.
- v96 remains excluded from production signal.
- Official odds must be frozen pre-deadline; missing/late/incomplete data fail closed.

## Why this continuation ran

The previous handoff `CHAT_HANDOFF_20260913_4HEAD_A_LIVE_V283_LIVE.md` was recent, but the requested next stage was still unfinished. Under the monitor rule, an unfinished/unstarted next stage counts as stopped, so implementation resumed rather than merely checking status.

## Prior accepted blocks

- ENV_ENTRY exact 25-feature assembler: accepted.
- A-LIVE exact frozen 17-feature assembler/scorer: accepted; CI Run `34749862014` SUCCESS.
- v283 SECOND5/conditional20 schema adapter/scorer: accepted; CI Run `34749834197` SUCCESS.

## Historical formula trace completed

The exact current-day formulas were traced from:

- `analyze_v279_4head_opponent_listwise_rebuild.py`
- `analyze_v281_4head_opponent_third_scenario.py`
- `analyze_v282_4head_conditional_third.py`
- `analyze_v278_4head_opponent_current_exhibition_audit.py`
- `analyze_v274_4head_opponent_feature_audit.py`

### Frozen SECOND base

`PLAYER_START` has 25 features. It uses pre-result symmetric boat ability/player/current exhibition/start-history/position values only.

### Frozen conditional THIRD formula

The frozen `COND_BASE` conditional THIRD row is built from:

1. the candidate third boat's `PLAYER_START`-derived/base/scenario values with `t_` prefix,
2. boat-4 current attack/turning context,
3. candidate-vs-boat4 current exhibition gaps and absolute gaps,
4. position/identity scenario terms,
5. pair-position terms from `(second, third)`.

Pair terms are deterministic pre-result functions only:

- `pair_same_side4`
- `pair_second_inner`, `pair_second_outer`
- `pair_third_inner`, `pair_third_outer`
- `pair_adjacent`
- `pair_distance`
- `pair_third_minus_second`
- `pair_second_is1/2/3/5/6`

Boat-4 context formulas were reproduced exactly from v281:

- `h4_attack = mean(cur_ex, cur_st, cur_orig_straight, cur_orig_avg)`
- `h4_turning = mean(cur_orig_lap, cur_orig_turn)`
- `cur_*__vs4 = candidate - boat4`
- `cur_*__abs4 = abs(candidate - boat4)`
- frozen interaction terms use `h4_attack` exactly as historical code.

## New accepted implementation — v283 row derivation

Added:

- `build_4head_v283_rows_live.py`
- `verify_4head_v283_rows_live.py`
- `.github/workflows/validate-4head-v283-rows-live.yml`

Commits:

- `61a762877e0c17509336a9931108af5158f5a1a2` — current-day SECOND/THIRD row derivation
- `09572187c9b9fbc2d0b07dad5d665ab5833915ed` — formula/schema verifier
- `985a7798ee96979bcfd8974971c8557b42506ac9` — dedicated CI

CI:

- Run `34750076354`
- workflow `validate-4head-v283-rows-live`
- conclusion: **SUCCESS**

Decision: **ACCEPT**.

Reason: the builder now derives the frozen SECOND5 and conditional THIRD20 rows from six current-day boat rows using the historical v279/v281/v282 formulas, enforces exact frozen schemas/universes, uses only frozen inference, and retains result-blind/Jul-Aug/Sep/v96 guards.

This closes the previous gap where 25/69 rows had to be supplied already assembled.

## New accepted implementation — final VARN runner input assembly

Added:

- `assemble_4head_v291_varn_live_input.py`
- `verify_4head_v291_varn_live_input.py`
- `.github/workflows/validate-4head-v291-varn-live-input.yml`

Commits:

- `bfcc2b0e1c70f2a34bc2f293e2d34f5a3c15447a` — assemble ENV_ENTRY + A-LIVE + v283 into final runner input
- `77f6bd8fd6dcdf8f093fa16aebea7a32746e77c4` — end-to-end frozen input verifier
- `4d14be7a7d8dccace68d03d8ec858d04915b849c` — initial CI

Initial CI:

- Run `34750136526`
- conclusion: **FAILURE**
- cause: CI environment installed only numpy, while importing the real production runner transitively required pandas.
- This was a CI dependency failure, not a model/policy/formula failure.

Fix:

- commit `1960f479055307cc2a45c0acf11b1b3e97237b6e`
- CI now installs the real runner dependency set needed for contract import.

Final CI:

- Run `34750179787`
- conclusion: **SUCCESS**

Decision: **ACCEPT** the frozen final-input composition layer.

It takes one result-blind causal bundle containing:

- `race_code`
- frozen/current PRE
- frozen/current POST
- ENV_ENTRY causal primitives
- A-LIVE causal 17 features
- six boat rows for v283 primitives/current exhibition

and emits the exact JSON accepted by `run_4head_v291_varn_live.py`. The existing final runner remains unchanged and remains sole owner of official pre-deadline odds, v291 composite>=7 entry, adopted variable N, and exact JPY10,000 Dutch.

## One-command bridge status

Added:

- `run_4head_v291_varn_auto_live.py`
- commit `3b4cb4a9ae4931cf490cbdbb8c6032871d48580d`

The bridge assembles a causal bundle and then delegates to the existing `run_4head_v291_varn_live.py`; it does not duplicate or alter ticket/odds policy. A `--prepare-only` path is included for non-market contract testing.

**Status: IMPLEMENTED BUT NOT YET CI-ACCEPTED.**

The attempted verifier-file write was blocked by the execution environment's safety classifier before it reached GitHub. Therefore no claim of CI acceptance is made for this bridge yet. Do not treat the bridge as production-green until a verifier/workflow is successfully committed and CI passes.

## What is now connected

The frozen mathematical/inference chain is now green through final runner input:

`PRE + POST + ENV causal primitives + A causal features + six v283 boat rows`

`-> ENV_ENTRY frozen score`

`-> S/A frozen classification`

`-> v283 SECOND5 + conditional THIRD20 derived rows`

`-> frozen p2/cond probabilities`

`-> exact input for run_4head_v291_varn_live.py`

`-> existing official pre-deadline odds -> v291 composite >=7 -> variable N=4..16 floor 4 -> JPY10,000 Dutch`

No v291 threshold, variable-N rule, or staking rule was changed.

## Exact remaining AUTO LIVE gap

The remaining substantive source-acquisition gap is **before** the accepted assembly layer:

1. Automatically acquire/construct all A-LIVE current-day causal values, especially player/opponent keys 7..17.
2. Automatically acquire/construct the 25 v283 base boat primitives for all opponent boats, while current exhibition components can be sourced from already proven BOATCAST/official pre-race paths.
3. Supply PRE/POST/current ENV_ENTRY primitive bundle automatically from the accepted current-day builders rather than manually composing the causal bundle.
4. CI-verify `run_4head_v291_varn_auto_live.py` once the environment permits the verifier/workflow write.
5. Then run a result-blind dry/live pre-deadline capture to prove source acquisition -> assembled input -> official odds -> BET/PASS audit end-to-end without any outcome access.

## Additional BET / variable-ticket research

Not started in this continuation because full source acquisition AUTO LIVE is not yet green. Do not use Jul/Aug outcomes to tune it. Resume this only after the above AUTO LIVE source path is completed.

## Current verdict

- `HEAD4_V291_COMP7`: **UNCHANGED / FROZEN**.
- `HEAD4_V291_COMP7_VARN_F4_N16`: **UNCHANGED / ADOPTED**.
- JPY10,000 Dutch: **UNCHANGED**.
- A-LIVE frozen scorer/assembler: **ACCEPTED**.
- v283 frozen scorer/schema adapter: **ACCEPTED**.
- v283 exact current-day row derivation: **NEWLY ACCEPTED**, Run `34750076354` SUCCESS.
- final VARN runner-input composition: **NEWLY ACCEPTED**, Run `34750179787` SUCCESS after dependency-only failure Run `34750136526`.
- one-command bridge: **IMPLEMENTED, NOT YET CI-ACCEPTED**.
- complete source-fetch AUTO LIVE: **IN PROGRESS**.

## Exact next resume point

Start from commit `3b4cb4a9ae4931cf490cbdbb8c6032871d48580d` or newer main.

1. Add/CI the verifier for `run_4head_v291_varn_auto_live.py` without changing production policy.
2. Trace and implement result-blind current-day acquisition of the remaining A-LIVE/player-history/v93 and v283 25-base primitives.
3. Produce a single causal bundle automatically, feed the accepted assembler, then the existing final runner before deadline.
4. Record the first full source-to-audit result-blind LIVE dry run.
5. Only then proceed to additional-BET / variable-ticket operational research.
