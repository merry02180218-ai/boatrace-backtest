# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Current policy
- research branch: `research/3head-v289-addon-expansion`
- legacy v288 production remains unchanged.
- legacy v288 baseline is a **floor, not a fixed research count**: 94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%.
- research should not reduce total selected races below 94R; expansion above 94R is allowed.
- candidate generation is expanded to the **full audited Feb-Aug race universe** wherever pre-deadline features and post-race settlement are scientifically usable.
- July/August are NON-PRISTINE.
- September outcomes are not loaded / not used for tuning.
- frozen canonical feature source: Run `34383567078`, artifact `v243-3head-expand-feature-audit`, artifact ID `10118044294`, max date 2026-08-31.
- all research inputs must be available before deadline; required-current missingness fails closed.
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
- full-universe settlement usable from the frozen v243 table alone: **False**.
- decision: **SOURCE_REBUILD_REQUIRED_WAVE18**.
- reason: the frozen feature audit has the broader race population but does not carry hypothetical 3-head return settlement for non-bet rows. Do not infer zero return from missing settlement.

## Wave18b — full-universe settlement recovery — RUNNING
- user indicated prior settlement data likely already exists; GitHub history confirmed a reusable pattern in `run_v297_1head_guard_trifecta5_research.py` using historical settlement sources after feature freeze.
- settlement sources: `data/results/realtime/YYYY/MM/DD.csv` -> `data/results/payouts/YYYY/MM/DD.csv` (`3連単_組番`) -> archived `actual_combo` only as fallback for official settlement rows.
- settlement is post-race evaluation only and must never enter prediction features.
- goal: attach actual exact-order outcomes to all **678** frozen races, count actual 3-head wins, and produce a full-universe settled source for subsequent ticket simulation / ROI research.
- fail-closed guards: source max date <= 2026-08-31; official settlement row share >= 98%; exact-order completeness within official rows >= 99.9%; September forbidden.
- script: `research_v289_3head_wave18b_settlement_recovery.py`.
- script commit: `1c905d2ac75827d64e8699ac54e60abe9bcb297d`.
- existing Wave18 workflow was safely reused because creating a brand-new workflow was blocked by tool safety checks.
- workflow update commit: **`3563c25614258c6b0e9137fe6e8721dbc2dfae50`**.
- Actions Run **`34749298218`** queued at latest check.
- intended artifact: **`3head-wave18b-settlement-recovery`**.

## Exact restart point
1. Inspect Actions Run `34749298218` first.
2. If success: inspect artifact `3head-wave18b-settlement-recovery` and read `research_v289_3head_wave18b_settlement_recovery.md/json`; record unique races, official settlement rows/share, exact-order rows/completeness, actual 3-head wins, source split, artifact ID, result commit SHA.
3. If failed: inspect job/log and fix automatically without weakening guards.
4. If `SETTLED_SOURCE_READY`: immediately start Wave19/full-universe model research using the recovered all-race settlement source, while preserving frozen pre-deadline features and legacy v288 94R floor. Build candidate generation from the full 584R non-baseline universe, not the old 232R pool.
5. Wave19 must report add-on R, hits/hit rate, ROI, profit, monthly, min monthly ROI, red months, max DD, overlap with v288, and baseline+add-on combined R/ROI.
6. Preserve Jul/Aug NON-PRISTINE, September outcomes unused, pre-deadline inputs only, current-required missing => fail closed, no overlap with legacy v288, JPY10,000 per race.
