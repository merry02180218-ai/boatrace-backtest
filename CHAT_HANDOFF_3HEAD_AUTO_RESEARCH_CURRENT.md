# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Current policy
- research branch: `research/3head-v289-addon-expansion`
- latest GitHub overrides older chat/memory.
- legacy v288 production remains unchanged.
- legacy v288 baseline is a **floor**: 94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%.
- candidate research universe is the **full audited Feb-Aug population** excluding only unchanged legacy v288 baseline: 678 total - 94 baseline = **584R**.
- July/August are NON-PRISTINE. September outcomes are forbidden for tuning/model selection.
- prediction inputs must be pre-deadline only; required-current missing => fail closed.
- settlement/outcome fields are evaluation-only after feature freeze.
- add-on overlap with legacy v288 must remain zero.
- stake remains JPY10,000/race.

## Waves 1-17
All rejected. Stable details remain in repository result files.

## Wave18 — FINAL
- Run `34748886697` success; artifact `3head-wave18-full-universe`, ID `10315126991`.
- source unique races 678; non-baseline research universe 584R; frozen v243 table lacked hypothetical settlement on BET=0 rows.
- decision **SOURCE_REBUILD_REQUIRED_WAVE18**.

## Wave18b — FINAL
- startup-failed Run `34749298218` fixed automatically.
- successful Run **`34749443471`**, job `103703132844` success.
- artifact **`3head-wave18b-settlement-recovery`**, ID **`10315112832`**.
- 678/678 official settlements = 100%; 678/678 exact trifecta outcomes = 100%; actual 3-head wins = 321R.
- all 678 recovered from realtime result source; max date 2026-08-31.
- decision **SETTLED_SOURCE_READY**.

## Wave19a — payout enrichment — FINAL
- Run **`34749575986`** completed success.
- job `103703497997` success.
- artifact **`3head-wave19-payout-enrichment`**, ID **`10315596555`**.
- head SHA `a30b22936169e82d14c2203759562ad332a95f88`.
- payout coverage: **678/678 = 100%**.
- payout combo exactly matched recovered actual combo: **678/678 = 100%**.
- positive trifecta payout rows: **678R**.
- max date: 2026-08-31.
- transparent benchmark: 3号艇頭20通りを各500円（計10,000円/R）で678R全買い => stake **6,780,000 yen**, payout **4,809,050 yen**, profit **-1,970,950 yen**, ROI **70.929941%**.
- decision **PAYOUT_SOURCE_READY**.
- interpretation: full-population ROI research is now scientifically settleable; do not revert to 232R/54R restricted pools.

## Wave19b — full 584R walk-forward — RUNNING
- script: `research_v289_3head_wave19b_full584_walkforward.py`.
- script commit: **`979e9647444c09452817a7e4cb59b525a16d1776`**.
- workflow update commit: **`bf8ebc78c537eb7ae3d296d890c26039a5d14150`**.
- Actions Run: **`34749707037`** (queued at launch check).
- candidate population: exactly **584R** non-baseline full universe.
- settlement benchmark: 3-head all 20 exact-order combos x JPY500 = JPY10,000/race.
- prior-month-only walk-forward; full pre-deadline features + value + current exhibition; required feature missing => fail closed.
- fractions tested: 2%, 4%, 6%, 8%, 12%, 15% of prior score distribution.
- every method must report add-on R, hits/rate, stake, payout, ROI, profit, monthly, min-month ROI, red months, max DD, overlap, combined baseline+addon R/ROI.
- adoption research guard: add-on >=20R, ROI>=100%, min-month ROI>=60%, red months<=3, overlap=0. A pass is shadow candidate only until separately validated.

## Exact restart point
1. Inspect Run `34749707037` first.
2. If failed: inspect logs, fix automatically, rerun without weakening guards.
3. If success: inspect artifact `3head-wave19b-full584-walkforward`, record artifact ID, all method metrics, best method, passers, decision, and relevant commit SHA here.
4. If **NO_ADOPTION_WAVE19B**, immediately launch a distinct Wave20 full-584R family (not simple threshold loosening; e.g. latent regime / nearest-neighbor analog / ticket-rerank using the payout-enriched source).
5. If shadow candidate appears, record it but do not replace v288 until separate validation.
6. Preserve: legacy 94R floor, Jul/Aug NON-PRISTINE, September forbidden, pre-deadline only, fail-closed current inputs, zero overlap, JPY10,000/race.
7. **AUTO-CONTINUE:** if no relevant 3-head commit/Run for >2h, a Run fails/stops/incompletely exits, or a Wave completes with no next distinct Wave launched, resume automatically from this file, fix/re-run, update this handoff, and continue.
