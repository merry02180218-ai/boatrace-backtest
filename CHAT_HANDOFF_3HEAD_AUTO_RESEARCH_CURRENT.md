# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch: `research/3head-v289-addon-expansion`; newest GitHub state wins.
- Legacy v288 stays unchanged: 94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%.
- Current research source is no longer limited to v243 678R or 584R. Use all available six-boat races from 2026-02-01 through 2026-08-31 from BoatraceCSV race_cards.
- Jul/Aug NON-PRISTINE. September outcomes forbidden.
- Features must be pre-deadline. Results/payouts are evaluation-only. Historical closing trifecta odds are staking/post-hoc ROI only and must not be prediction features.
- Missing required current inputs fail closed. Add-on overlap with v288 must be zero. Stake JPY10,000/race.

## Prior state
- Wave18b Run `34749443471`: 678/678 official settlements and exact-order results recovered.
- Wave19a Run `34749575986`: 678/678 payouts recovered; 3-head all-20 equal stake benchmark ROI 70.929941%.
- Wave19b Run `34749707037` failed with `RuntimeError: missing payout`; superseded by Wave20.

## Wave20 — FINAL
- Run `34749917116`: success.
- Artifact `3head-wave20-allrace-universe`, ID `10314839371`.
- Full available six-boat universe: **32,111R**.
- Monthly: Feb 4100 / Mar 4607 / Apr 4244 / May 4832 / Jun 4488 / Jul 4920 / Aug 4920.
- Missing race_cards date: 2026-06-17 only.
- Decision: `ALLRACE_UNIVERSE_READY`.

## Wave21 — FINAL source audit
- Successful recovery Run `34751314113`, head `10fabebaa444fdb6730b16287fe95051a6f3942b`.
- Artifact `3head-wave21-allrace-source-build`, ID `10316605199`.
- rows 32,111; feature columns 786; retry days 13.
- result coverage 31,472/32,111 = 98.010%.
- payout coverage 31,553/32,111 = 98.262%.
- usable exact settlement 31,518/32,111 = 98.153%.
- agreement when both exact sources exist 31,300/31,314 = 99.9553%; true mismatches 14.
- actual 3-head wins in usable rows 4,040.
- Decision: `ALLRACE_SETTLED_SOURCE_READY`.

## Wave22 — FINAL historical closing trifecta odds
- Run `34752573368`, workflow `research-3head-wave21-allrace-source-build`, head `195e14da883d291b633dbe4deaf0bd5a57298cd5`: success.
- Artifact `3head-wave21-allrace-source-build`, ID `10316748754` (Wave21 source now enriched with closing odds).
- Source: Kyotei24 Odds Bank historical 3T pages explicitly labelled `締切時オッズ`.
- odds available: **31,605/32,111 = 98.424%**.
- full 120 trifecta odds: **31,605/32,111 = 98.424%**.
- Monthly coverage:
  - 2026-02: 4021/4100 = 98.07%
  - 2026-03: 4523/4607 = 98.18%
  - 2026-04: 4165/4244 = 98.14%
  - 2026-05: 4731/4832 = 97.91%
  - 2026-06: 4418/4488 = 98.44%
  - 2026-07: 4877/4920 = 99.13%
  - 2026-08: 4870/4920 = 98.98%
- Decision: `CLOSING_ODDS_SOURCE_READY`.
- Closing odds remain excluded from prediction features; use only after selection for staking/post-hoc ROI.

## Wave23 — RUNNING full-population temporal walk-forward
- Script commit `aabf34f626dc2c66af7be78b47ba6557eef43e9b`: `research_v289_3head_wave23_fullpop_walkforward.py`.
- Self-contained conservative old-v243 exclusion runner commit `cfee48015a7791f1138f5919c97ad8004707678d`.
- Auto-chain commit `3d27fa6a1c215346693b92d30a07db10a5ced135` runs Wave23 after Wave21+22 and folds Wave23 metrics into the persisted Wave21 artifact JSON/MD.
- Current Run: **`34754875342`**, workflow `research-3head-wave21-allrace-source-build`, head `3d27fa6a1c215346693b92d30a07db10a5ced135`.
- Latest state at launch: **queued**.
- Wave23 design:
  - model uses only pre-deadline card/program features;
  - all old v243 678 race codes are conservatively excluded, which is a superset of legacy v288 94R and therefore guarantees legacy overlap = 0;
  - exact closing 120 odds are used only after race selection;
  - JPY10,000/race allocated across all twenty `3-x-y` exact orders in JPY100 Dutch units;
  - realized return uses official exact trifecta payout;
  - temporal tests Apr/May/Jun use prior-month-only training;
  - threshold selection is Apr-Jun only;
  - Jul/Aug are one frozen-model NON-PRISTINE shadow evaluation and may not alter threshold;
  - decision can only become SHADOW_CANDIDATE if pristine ROI reaches/exceeds legacy baseline and has zero red pristine months; otherwise NO_ADOPTION.

## Exact restart point
1. Inspect Run `34754875342` first.
2. If failed, inspect job logs and fix/rerun automatically without weakening date/no-leakage/zero-overlap guards.
3. If success, read the Wave23 section from the artifact JSON/MD and report exact pristine Apr-Jun R/hits/stake/payout/ROI/profit/monthly/min-month/red-months/max-DD/overlap/combined plus Jul-Aug NON-PRISTINE shadow metrics.
4. If Wave23 is `NO_ADOPTION`, automatically launch a genuinely distinct next family (latent regime / nearest-neighbor analog / opponent-ticket rerank) rather than simple threshold loosening.
5. If `SHADOW_CANDIDATE`, do not replace v288 automatically; validate separately.
6. Jul/Aug remain NON-PRISTINE; September outcomes forbidden; legacy v288 94R remains the baseline/floor; add-on overlap zero.
