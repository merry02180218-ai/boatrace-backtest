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
- Run `34749917116`: success; artifact `3head-wave20-allrace-universe`, ID `10314839371`.
- Full six-boat universe: **32,111R**. Monthly: Feb 4100 / Mar 4607 / Apr 4244 / May 4832 / Jun 4488 / Jul 4920 / Aug 4920. Missing race_cards date: 2026-06-17 only.
- Decision: `ALLRACE_UNIVERSE_READY`.

## Wave21 — FINAL source audit
- Run `34751314113`: success; artifact ID `10316605199`.
- 32,111 rows; feature columns 786; usable exact settlement **31,518/32,111 = 98.153%**; both-source agreement **99.9553%**; true mismatches 14; actual 3-head wins 4,040.
- Decision: `ALLRACE_SETTLED_SOURCE_READY`.

## Wave22 — FINAL historical closing trifecta odds
- Run `34752573368`: success; artifact ID `10316748754`.
- Kyotei24 Odds Bank `締切時オッズ`; full 120 odds **31,605/32,111 = 98.424%**.
- Monthly coverage: Feb 98.07%; Mar 98.18%; Apr 98.14%; May 97.91%; Jun 98.44%; Jul 99.13%; Aug 98.98%.
- Decision: `CLOSING_ODDS_SOURCE_READY`. Odds remain staking/post-hoc only.

## Wave23 — FINAL tree walk-forward
- Run `34754875342`: success; artifact ID `10317157868`.
- Source after conservative old-v243 678R exclusion: **30,746R**; legacy overlap **0**; features 77; HistGradientBoosting; threshold 0.40.
- Pristine Apr-Jun: **651R / 250 hits / ROI 135.062% / profit +2,282,530 yen**.
- Monthly: Apr 196.434%; May 131.256%; Jun 57.747%.
- Jul-Aug NON-PRISTINE shadow: **296R / 80 hits / ROI 77.598% / -663,100 yen**.
- Decision: **NO_ADOPTION**.

## Wave24 — FINAL nearest-neighbor analog
- Run `34757826506`: success; artifact ID `10317814162`.
- Pristine Apr-Jun: **120R / 55 hits / ROI 95.236% / profit -57,170 yen**.
- Jul-Aug NON-PRISTINE shadow: **77R / 22 hits / ROI 55.145% / -345,380 yen**.
- Decision: **NO_ADOPTION**.

## Wave25 — FINAL latent regime cluster
- Run `34757888935`: success; artifact ID `10317569451`.
- Pristine Apr-Jun: **5,427R / 962 hits / ROI 70.701% / profit -15,900,810 yen**.
- Jul-Aug NON-PRISTINE shadow: **4,102R / 773 hits / ROI 73.452% / -10,890,140 yen**.
- Decision: **NO_ADOPTION**.

## Wave26 — FINAL but INVALIDATED pending leak-free rerun
- Run `34759822824`, workflow `research-3head-wave26-exactorder`: success; artifact `3head-wave26-exactorder-softmax`, ID `10318069914`.
- Reported Apr-Jun: **1,125R / 167 hits / ROI 226.722% / +14,256,180 yen**; Jul-Aug shadow **487R / 56 hits / ROI 82.152% / -869,190 yen**; overlap 0.
- Wave26 used 77 features: 63 static card metrics plus current-meet `節D...ST/着順` aggregates.
- Leak audit found a strong target signature in historical `race_cards`: for boat 3, rows where `節D` race-number/frame matched the current race produced **15,280 matched rows**, and `節D...着順==1` agreed with actual 3-head outcome at about **97.997%**.
- Therefore Wave26 `recent_finish` and `recent_st` cannot be treated as pre-deadline-safe from this historical source. The previous `SHADOW_CANDIDATE` is **invalidated for adoption** until reproduced without all section-history fields.
- Closing odds were not prediction features in Wave26; the leakage concern is the historical section-race fields.

## Wave27 — RUNNING leak-free exact-order audit
- Script commit `894387d7835846e9437415c153a215b6f77b886e`: `research_v289_3head_wave27_leakfree_exactorder.py`.
- Workflow commit `b30fd9608f45d452271380ca50f82eafd380e041`: `.github/workflows/research-3head-wave27-leakfree.yml`.
- Current Run: **`34763079073`**, workflow `research-3head-wave27-leakfree`, status at launch **in_progress**.
- Prediction features are restricted to **63 static card metrics only**. Every `節D`, current-meet ST/finish, result, settlement and odds field is excluded from prediction and guarded fail-closed.
- Exact-order family remains 21-class softmax (`OTHER` + 20 exact 3-head combinations).
- Strict model-selection correction: threshold/top-K are chosen **only on April**; **May-Jun are untouched holdout** for the adoption decision. Jul-Aug remain frozen NON-PRISTINE shadow. September forbidden.
- Closing odds remain staking-only for JPY10,000 Dutch settlement. Legacy overlap remains 0 by conservative old-v243 exclusion.

## Exact restart point
1. Inspect Run `34763079073` first.
2. If failed, inspect logs and fix/rerun without restoring any `節D` field or weakening no-leak/date/zero-overlap guards.
3. If success, record April tuning metrics, strict May-Jun holdout R/hits/ROI/profit/monthly/min month/red months/max DD, Jul-Aug NON-PRISTINE shadow, overlap and combined baseline.
4. Treat Wave26's 226.7% ROI as contaminated unless Wave27 independently reproduces strength with static pre-deadline-safe features.
5. Keep v288 production unchanged unless independent leak-free validation supports promotion.
