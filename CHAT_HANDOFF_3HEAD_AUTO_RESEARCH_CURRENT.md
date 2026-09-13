# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch: `research/3head-v289-addon-expansion`; newest GitHub state wins.
- Legacy v288 fixed: 94R / 52 hits / stake 940,000 / payout 1,622,070 / profit +682,070 / ROI 172.560638%.
- Research universe: all available six-boat races 2026-02-01 through 2026-08-31 from BoatraceCSV race_cards. Do not revert to old v243 678R/584R universe.
- Jul/Aug are NON-PRISTINE shadow only. September outcomes forbidden.
- Prediction features are pre-deadline only. Results/payouts evaluation-only. Closing trifecta odds staking/post-hoc ROI only.
- Current leak-free family uses exactly 63 static card-only features; every `節D` / current-meet result/ST field is forbidden.
- Missing required current input => fail closed. Add-on overlap with v288 must be zero. Stake JPY10,000/race, Dutch allocation.

## Stable source milestones
- Wave19b Run `34749707037` failed on payout column; superseded by all-race rebuild. Do not reduce scope because of this failure.
- Wave20 Run `34749917116`: success; full six-boat universe 32,111R. Feb 4100 / Mar 4607 / Apr 4244 / May 4832 / Jun 4488 / Jul 4920 / Aug 4920.
- Wave21 Run `34751314113`: success; exact settlement usable 31,518/32,111 = 98.153%; both-source agreement 99.9553%; actual 3-head wins 4,040.
- Wave22 Run `34752573368`: success; full 120 closing trifecta odds 31,605/32,111 = 98.424%.

## Research summary
- Wave23 Run `34754875342`: Apr-Jun 651R / ROI 135.062%; Jul-Aug 77.598%; NO_ADOPTION.
- Wave24 Run `34757826506`: Apr-Jun 120R / ROI 95.236%; Jul-Aug 55.145%; NO_ADOPTION.
- Wave25 Run `34757888935`: Apr-Jun 5,427R / ROI 70.701%; Jul-Aug 73.452%; NO_ADOPTION.
- Wave26 Run `34759822824`: INVALIDATED. Used 77 features with leaking `節D...ST/着順`; boat-3 `節D` matched current race on 15,280 rows and `節D着順==1` agreed with actual 3-head at 97.997%.
- Wave27 Run `34763079073`: 63 static features; May-Jun holdout 195R / ROI 57.947%; Jul-Aug 124.170%; NO_ADOPTION.
- Wave28 Run `34764021442`: structural gate; May-Jun 75R / ROI 73.745%; Jul-Aug 128.013%; NO_ADOPTION.
- Wave29 Run `34764558658`: Feb train -> Mar tune p3>=0.38/top7; untouched Apr-Jun 342R / 63 hits / ROI 93.845% / -210,510; Apr 123.769%, May 78.718%, Jun 56.762%; Jul-Aug 111.906%; combined 110.816%; NO_ADOPTION.

## Wave30 — FINAL two-stage linear family
- Run `34765791471`: success; artifact `3head-wave30-twostage-preapril` ID `10320691590`.
- March tune: p3>=0.30/top7; 160R / ROI 103.285%.
- Apr-Jun untouched holdout: 547R / 104 hits / ROI 81.210% / -1,027,810.
- Monthly: Apr 112.334% / +222,010; May 73.083% / -557,180; Jun 56.710% / -692,640.
- Min month 56.710%; red months 2; max DD 1,333,820.
- Jul-Aug shadow: 386R / 89 hits / ROI 76.262% / -916,270.
- Combined baseline + holdout: 641R / ROI 94.606% / -345,740. Overlap 0. Decision NO_ADOPTION.

## Wave31 — FINAL nonlinear HGB head gate
- Run `34765896176`: success; artifact `3head-wave31-nonlinear-gate` ID `10320018221`.
- Family: HistGradientBoosting 3-head gate + conditional exact-order logistic; 63 static card-only features.
- March tune from Feb only: p3>=0.26/top3; 284R / 27 hits / ROI 100.556% / +15,790.
- Apr-Jun untouched holdout: 806R / 85 hits / ROI 79.134% / -1,681,830.
- Monthly: Apr 290R / 31 hits / ROI 95.041% / -143,800; May 244R / 27 hits / ROI 74.604% / -619,670; Jun 272R / 27 hits / ROI 66.237% / -918,360.
- Min month 66.237%; red months 3; max DD 2,166,770.
- Jul-Aug NON-PRISTINE shadow: 582R / 77 hits / ROI 83.921% / -935,820. Jul 90.256%; Aug 77.498%.
- Baseline + holdout: 900R / ROI 88.892% / -999,760. Overlap 0. Decision NO_ADOPTION.
- Interpretation: nonlinear head gate also degrades from April to June; do not tune around Jul/Aug.

## Wave32 — NEXT
- Launch a genuinely distinct leak-free family using tree-ensemble ranking for both 3-head probability and exact-order selection (ExtraTrees), not the prior HGB+logistic split.
- Same 63 static card-only features and same v288 exclusion.
- Feb-only training predicts March for threshold/top-K selection. Apr-Jun remain pristine rolling holdout. Jul-Aug frozen shadow only.
- Preserve JPY10,000 Dutch staking, closing odds staking-only, zero v288 overlap, September forbidden.

## Exact restart point
1. Implement and run Wave32 tree-ensemble family.
2. If run fails, inspect logs and fix automatically without weakening leak/date/overlap guards.
3. If success, record March chosen threshold/top-K, Apr-Jun R/hits/ROI/profit/monthly/min month/red months/max DD, Jul-Aug shadow, overlap, combined baseline.
4. Adoption status is based on pristine Apr-Jun only. Jul/Aug cannot rescue a weak result.
5. If NO_ADOPTION, continue another distinct leak-free full-population family automatically.
