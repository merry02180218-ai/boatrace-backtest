# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch: `research/3head-v289-addon-expansion`; newest GitHub state wins.
- Legacy v288 fixed baseline: 94R / 52 hits / stake 940,000 / payout 1,622,070 / profit +682,070 / ROI 172.560638%.
- Research universe: every available six-boat race 2026-02-01 through 2026-08-31 from BoatraceCSV `race_cards`.
- Add-ons exclude only the exact v288 operational 94-race baseline and must have zero overlap with it.
- Jul/Aug are NON-PRISTINE shadow only. September outcomes forbidden.
- Prediction features are pre-deadline only. Result/payout/settlement fields are evaluation-only. Closing trifecta odds are staking/post-hoc ROI only.
- Current leak-free feature family uses exactly 63 static card-only features; all `節D` / current-meet result/ST fields are forbidden.
- Missing required current input => fail closed. Stake JPY10,000/race with Dutch allocation.

## Stable source milestones
- Wave20 Run `34749917116`: success; full six-boat universe 32,111R.
- Wave21 Run `34751314113`: exact settlement usable 31,518/32,111 = 98.153%.
- Wave22 Run `34752573368`: full 120 closing trifecta odds 31,605/32,111 = 98.424%.
- Exact v288 94R baseline code list: `v288_operational_pre_replay_94_baseline_codes.csv`.

## Scope correction
- Waves27-31 used an older broad 678R exclusion and are historical only, not definitive corrected-scope tests.
- Correct scope from Wave32 onward = Wave20 full six-boat population minus exact v288 operational 94R only.

## Wave32 — FINAL corrected-scope ExtraTrees broad selection
- Run `34766794599`: success; artifact `3head-wave32-extratrees-corrected-scope` ID `10320636906`.
- March tune p3>=0.32 / top5: 3,670R / ROI 80.636%.
- Apr-Jun holdout: 10,324R / 781 hits / ROI 78.449% / profit -22,249,650 yen.
- Monthly ROI Apr 75.476% / May 76.715% / Jun 83.014%; red months 3.
- Jul-Aug shadow ROI 77.955%; combined v288 + holdout ROI 79.298%.
- Decision NO_ADOPTION.

## Wave33 — FINAL sparse high-confidence family
- Run `34767681917`: success; artifact `3head-wave33-sparse-high-confidence` ID `10320502922`.
- Family: HGB P(3-head) + ExtraTrees exact-order concentration gate; 63 static features; exact v288 overlap 0.
- March gate from Feb-only: p3>=0.259206995, concentration>=0.340699289, top5; 70R / 12 hits / ROI 102.484% / +17,390 yen.
- Apr-Jun pristine holdout: 235R / 35 hits / ROI 57.226% / profit -1,005,180 yen.
- Monthly: Apr 64R / ROI 73.838%; May 99R / ROI 51.372%; Jun 72R / ROI 50.511%.
- Min month 50.511%; red months 3; max DD 1,080,860 yen.
- Jul-Aug NON-PRISTINE shadow: 172R / 37 hits / ROI 90.738% / -159,310 yen.
- Combined baseline + holdout: 329R / 87 hits / ROI 90.179% / -323,110 yen.
- Decision NO_ADOPTION.

## Wave34 — RETRYING prototype-distance family
- Initial Run `34767979974` failed in the research script only; baseline/source guards passed.
- Failure cause: current scikit-learn removed the `multi_class` keyword from `LogisticRegression`; error was `TypeError: LogisticRegression.__init__() got an unexpected keyword argument 'multi_class'`.
- Compatibility-only fix committed as `b711725614b63a2355098e11d0d5294c0c2d3439`: removed `multi_class='auto'`; research logic/scope unchanged.
- Retry Run `34768428513` is in progress.
- Family: standardized positive-vs-negative prototype-distance head score + conditional logistic exact-order model.
- March selects head-score quantile and top3/top5/top7 with 30..300R floor; Apr-Jun untouched; Jul-Aug NON-PRISTINE shadow.
- Corrected full-population-minus-exact-94 scope; September forbidden; closing odds staking-only; JPY10k Dutch.

## Exact restart point
1. Inspect retry Run `34768428513` first.
2. If failed, inspect logs, fix automatically, rerun without weakening guards.
3. If success, record March score gate/top-K; Apr-Jun R/hits/ROI/profit/monthly/min month/red months/max DD; Jul-Aug shadow; exact v288 overlap; combined baseline.
4. Adoption status uses pristine Apr-Jun only. Jul/Aug cannot rescue a weak result.
5. If NO_ADOPTION, automatically continue with another genuinely distinct corrected-scope leak-free family.
