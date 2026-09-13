# CHAT HANDOFF — 2026-09-13 — HEAD4 A-LIVE + v283 LIVE

## Current production policy (unchanged)

- Base production model remains frozen: `HEAD4_V291_COMP7`.
- Adopted ticket overlay remains: `HEAD4_V291_COMP7_VARN_F4_N16`.
  - Entry: v291 Top4 composite odds >= 7.0.
  - Ticket count: largest N in 4..16 whose composite odds remains >= 4.0.
  - Exactly JPY 10,000/race inverse-odds Dutch with JPY 100 Hamilton rounding.
- Jul/Aug outcomes are NON-PRISTINE and MUST NOT be used to train/tune/research the LIVE builders.
- September outcomes remain outcome-blind.
- v96 production signal remains unused.
- Missing/late/incomplete pre-deadline LIVE inputs fail closed; no closing/post-deadline odds substitution.

## Prior current-day building blocks already on main

### POST seven-field builder

`build_4head_post_live.py` / `verify_4head_post_live.py` / `validate-4head-post-live.yml` remain the accepted current-day POST source adapter.

### ENV_ENTRY 25-feature assembler

Current main contains:

- `build_4head_env_entry_live.py`
- `verify_4head_env_entry_live.py`
- `.github/workflows/validate-4head-env-entry-live.yml`

The assembler emits the exact frozen 25-feature ENV_ENTRY schema and derives only:

- `p4_joint = PRE * POST`
- `post_x_entry_same = POST * entry_confirmed_same`

All other 21 primitives are required from causal/result-blind current-race sources. Missing/non-finite primitives fail closed.

Historical commits in this lineage:

- `7fad596ac8ae530307546239716aa082cad623b7` — add ENV_ENTRY live assembler
- `9f9e04a57f399ec00c07d190b497f78993d61faf` — verify ENV_ENTRY assembler
- `894b432d5ca6ca81fb7ff441f71b662316ee964c` — add ENV_ENTRY CI

## New work in this continuation: frozen A-LIVE 17-feature assembler

Added:

- `build_4head_a_live_live.py`
- `verify_4head_a_live_live.py`
- `.github/workflows/validate-4head-a-live-live.yml`

Frozen artifact/inference source:

- `artifacts/head4_v273_a_live_20260630.json`
- `head4_v273_a_live_inference.py`

Immutable A/S policy:

- S priority: PRE >= 0.28, POST >= 0.25, ENV_ENTRY >= 0.224790.
- Outside S only, A gate: PRE >= 0.18, POST >= 0.18.
- Frozen outcome-blind mapped `A_SCORE_LIVE` cut = `0.2710428764008591`.
- Mapping method: `OUTCOME_BLIND_SELECTED_FRACTION_QUANTILE`.
- Mapping explicitly records `outcomes_used_by_mapping = false`.

Exact 17 A-LIVE feature keys are artifact-defined and preserved in frozen order:

1. `v91_ex`
2. `score_CORR20_v91`
3. `score_wind_v83`
4. `score_RAW20_v91`
5. `score_BASE_v91`
6. `preview_comp`
7. `rel_pl_all_win_4v1`
8. `rel_pl_all_p2_4v1`
9. `rel_pl_recent_p2_4v1`
10. `opp_grade_b1_v93`
11. `opp_score_b1_v93`
12. `opp_national_b1_v93`
13. `b1_pl_all_win`
14. `b1_pl_all_p2`
15. `b1_pl_frame_win`
16. `rel_pl_recent_p2_4v3`
17. `b4_pl_recent_p2`

### A-LIVE CI history

Initial implementation commits:

- `12f232c1a285c0425cfaa14440685f6d6b8bf7ea` — add A-LIVE assembler
- `69777c133c65071bb199d7db6f0b5e120eccc587` — add verifier
- `99a306ccb224c9af97a57e98d2a516eb0a37782e` — add dedicated CI

Run `34749758741` FAILED in the verifier only. The test incorrectly assumed the frozen imputer medians equal scaler means, so it expected sigmoid(intercept). The actual frozen score was `0.19980456358056314` versus the incorrect expected `0.20292694696486435`. No production logic or guard was weakened.

Commit `81075a130d23fe38aa43243beeb5b61283565967` corrected the verifier to independently reproduce the exact standardized frozen logistic expression.

Run `34749789676` then FAILED on a second verifier-only negative test. Reversing artifact feature order is not itself invalid because the artifact owns that schema/order. Again, no production logic failed and no guard was weakened.

Commit `244445ac52bb461843b26091a23d9742525f9ec5` corrected that negative test to mutate immutable artifact policy metadata instead.

Final dedicated A-LIVE run:

- Run `34749862014`
- Workflow `validate-4head-a-live-live`
- Conclusion: **SUCCESS**

Decision: **ACCEPT the 17-feature A-LIVE schema/assembler + frozen scorer as a production building block.** This does not yet mean the 17 upstream causal values are all fetched/constructed automatically.

## New work in this continuation: v283 current-day SECOND/THIRD adapter

Added:

- `build_4head_v283_live.py`
- `verify_4head_v283_live.py`
- `.github/workflows/validate-4head-v283-live.yml`

Commits:

- `0aa1bd5bf96ee793c9ed7e33fd8eef979c84a575` — add v283 LIVE adapter
- `a02d5cdc568bd3298bfc1dc0bc534bdfa0f65f72` — add v283 verifier
- `a680c6f92e3264df30e006d386c6bf9e84720047` — add dedicated CI

The adapter validates the exact frozen candidate universes:

- SECOND: exactly 5 rows, boats `{1,2,3,5,6}`, exact frozen 25-feature `PLAYER_START` schema.
- Conditional THIRD: exactly 20 `(second, third)` rows over `{1,2,3,5,6}`, `second != third`, exact frozen 69-feature `COND_BASE` schema.

It then uses only frozen inference from `head4_v291_downstream_inference.py`:

- `score_second`
- `score_conditional_third`
- `v283_top4`

v283 policy remains `TOP2XTOP2`, `alpha2=0.60`, top_n=4, v96 unused.

Frozen artifact parity carried forward:

- SECOND max abs = `4.977407375150733e-13`
- Conditional THIRD max abs = `4.976713485760342e-13`
- tolerance = `2e-08`
- frozen training max date = `2026-06-29`
- Jul/Aug labels false; September labels false; v96 signal false.

Dedicated v283 run:

- Run `34749834197`
- Workflow `validate-4head-v283-live`
- Conclusion: **SUCCESS**

Decision: **ACCEPT the v283 SECOND5/conditional20 schema validator + frozen scorer as a production building block.** This still requires automatic construction of the 25/69 current-day feature values upstream.

## Exact remaining AUTO LIVE gap

The inference/scoring adapters now exist for:

`POST -> ENV_ENTRY -> A-LIVE -> v283 SECOND/THIRD -> existing pre-deadline odds/variable-N/Dutch runner`

But AUTO LIVE is **not complete yet** because automatic causal source construction is still missing for:

1. The A-LIVE player/opponent feature subset, especially feature keys 7..17 above.
2. v283 SECOND 25-feature current-day rows for boats 1,2,3,5,6.
3. v283 conditional THIRD 69-feature rows, including target-vs-4 and pair-derived terms.
4. One-click orchestration that combines PRE + POST + ENV_ENTRY + A-LIVE + v283 rows and passes the final result to `run_4head_v291_varn_live.py` before deadline.

The existing final runner already owns the downstream production behavior:

- S/A eligibility
- v283 full order / Top4 parity
- official pre-deadline 3連単 odds
- v291 Top4 composite >=7 entry
- adopted variable N=4..16 floor composite >=4
- exactly JPY10,000 Dutch
- fail closed after deadline or on incomplete odds/input

## Next implementation checkpoint

Do not re-research v291 thresholds or use Jul/Aug labels. Continue directly from this handoff:

1. Trace the historical Apr-Jun causal construction of the A-LIVE player/opponent primitives and v283 `PLAYER_START` / `COND_BASE` rows from the exact analysis source code.
2. Implement current-day builders from already proven PRE/POST/BOATCAST/official causal inputs, with no outcome/payout/closing-odds access.
3. Add Apr-Jun/result-free fixture parity for row formulas and exact feature order.
4. Build a one-click orchestrator into `run_4head_v291_varn_live.py` input format.
5. Only after full AUTO LIVE is green, resume Apr-Jun-only additional-BET / variable-ticket research without rewriting v291 baseline.

## Current verdict

- v291 base: unchanged/frozen.
- adopted variable-N ticket policy: unchanged.
- A-LIVE 17-feature assembler/scorer: **ACCEPTED, CI SUCCESS**.
- v283 SECOND5/conditional20 adapter/scorer: **ACCEPTED, CI SUCCESS**.
- Full AUTO LIVE: **IN PROGRESS / NOT YET COMPLETE** because upstream automatic feature construction and orchestration remain.
