# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Current policy
- research branch: `research/3head-v289-addon-expansion`
- legacy v288 production remains unchanged.
- legacy v288 baseline is a **floor, not a fixed research count**: 94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%.
- research must not reduce total selected races below 94R; expansion above 94R is allowed and preferred when scientifically justified.
- candidate generation is expanded to the **full audited Feb-Aug race universe** using frozen pre-deadline features plus post-race settlement only for evaluation.
- July/August are NON-PRISTINE.
- September outcomes are forbidden for tuning/model selection.
- frozen canonical feature source: Run `34383567078`, artifact `v243-3head-expand-feature-audit`, artifact ID `10118044294`, max date 2026-08-31.
- all model inputs must be available before deadline; required-current missingness fails closed.
- overlap with legacy v288 must remain zero for add-on selections.
- 1 race stake remains JPY10,000; variable-count Dutch may be used when applicable.

## Waves 1-17
All prior Wave1-17 proposals were rejected. Stable results remain in repository result files. Wave17 best: 10 add-on / 1 hit / ROI 31.36% / profit -68,640 / combined 104R / combined ROI 158.98%; PRE-excluded selected 0. **NO_ADOPTION_WAVE17**.

## Wave18 — full-universe candidate generation — FINAL
- Run `34748886697` completed success.
- artifact `3head-wave18-full-universe`, ID `10315126991`.
- source unique races: **678**.
- research universe excluding unchanged legacy 94R: **584R**.
- BET=0 rows: **156R**.
- BET=0 rows with positive hypothetical settlement in frozen v243 table: **0R**.
- full-universe settlement usable from frozen v243 table alone: **False**.
- decision: **SOURCE_REBUILD_REQUIRED_WAVE18**.
- reason: the frozen feature audit contains the broader race population but not hypothetical 3-head settlement for non-bet rows. Missing settlement must never be treated as zero return.

## Wave18b — full-universe settlement recovery — FINAL
- first attempt Run `34749298218` failed at Actions startup (`startup_failure`, no job created); this was a workflow-start issue, not a Python/model failure.
- workflow fix commit: `731e6853ca314acff442db81c6878d2256935f49`.
- successful Run: **`34749443471`**.
- job: `103703132844` (`wave18b-settlement-recovery`) completed **success**.
- artifact: **`3head-wave18b-settlement-recovery`**, artifact ID **`10315112832`**.
- script: `research_v289_3head_wave18b_settlement_recovery.py`.
- script commit: `1c905d2ac75827d64e8699ac54e60abe9bcb297d`.
- recovered source file in artifact: `analysis_v289_3head_wave18b_full_universe_settled.csv`.
- unique races: **678/678**.
- official settlement rows: **678/678 = 100%**.
- exact-order trifecta recovery: **678/678 = 100%**.
- actual 3-head wins: **321R**.
- settlement source split: **all 678R recovered from realtime result source**; payout/archive fallback was not needed for these 678 races.
- source max date: **2026-08-31**.
- decision: **SETTLED_SOURCE_READY**.
- scientific interpretation: the prior Wave18 settlement gap is resolved. The full 678R frozen population now has exact observed outcomes, so the 584R non-baseline universe can be used for full-population research without reverting to the old 232R/54R pools.

## Wave19 — NEXT / AUTO-CONTINUE
- start from the **full 584R non-baseline universe**, not the old 232R pool and not only the 54 PRE-excluded rows.
- use the Wave18b recovered exact outcomes strictly as post-race evaluation labels/settlement; never as prediction features.
- first implementation task: enrich the recovered source with the actual trifecta payout amount (settlement-only) from historical payout data, then define a scientifically reproducible JPY10,000-per-race ticket settlement for candidate models. Do not fabricate ROI from winner-only labels.
- after payout enrichment, run a distinct full-population family (latent regime / analog / ticket rerank or equivalent) using prior-month-only walk-forward selection.
- required report for every Wave19 method: add-on R, hits/hit rate, stake, payout, ROI, profit, monthly metrics, min monthly ROI, red months, max DD, overlap with v288, and baseline+add-on combined R/ROI.
- if no Wave19 method passes, automatically proceed to a genuinely distinct Wave20 family rather than stopping or reverting to the old restricted pool.

## Exact restart point
1. Confirm successful Wave18b Run `34749443471` and artifact ID `10315112832`.
2. Download `3head-wave18b-settlement-recovery` and use `analysis_v289_3head_wave18b_full_universe_settled.csv` as the full-population settled base.
3. Add settlement-only actual trifecta payout amount from historical payout CSV for all official rows; audit coverage and fail closed if payout completeness is insufficient for ROI research.
4. Preserve frozen pre-deadline features. Outcome/settlement columns may be used only after feature freeze for scoring/backtest evaluation.
5. Launch Wave19 full-584R research with prior-month-only walk-forward selection and JPY10,000/race ticket accounting.
6. Preserve legacy 94R floor, Jul/Aug NON-PRISTINE, September outcomes unused, current-required missing => fail closed, zero overlap with legacy v288.
7. **AUTO-CONTINUE RULE:** if the related 3-head research has no new relevant commit/Actions Run for >2 hours, any Run fails/stops/incompletely exits, or a Wave finishes without the next Wave being launched, resume automatically from this exact restart point, fix technical failures, rerun CI, record the result here, and continue to the next distinct research family.
8. Only notify the user for: automatic restart after a stop/failure, a technical blocker needing attention, an adoption/shadow candidate, or completion of a meaningful research wave. Normal healthy continuation needs no notification.
