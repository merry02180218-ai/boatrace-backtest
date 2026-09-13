# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch: `research/3head-v289-addon-expansion`; newest GitHub state wins.
- Legacy v288 fixed baseline: 94R / 52 hits / stake 940,000 / payout 1,622,070 / profit +682,070 / ROI 172.560638%.
- Research universe: every available six-boat race 2026-02-01 through 2026-08-31 from BoatraceCSV `race_cards`. Do NOT revert to old v243 678R / 584R universe and do NOT use v243/PRE/bet/route as a candidate prefilter.
- Add-ons exclude only the exact v288 operational 94-race baseline and must have zero overlap with it.
- Jul/Aug are NON-PRISTINE shadow only. September outcomes forbidden.
- Prediction features are pre-deadline only. Result/payout/settlement fields are evaluation-only. Closing trifecta odds are staking/post-hoc ROI only.
- Current leak-free feature family uses exactly 63 static card-only features; all `節D` / current-meet result/ST fields are forbidden.
- Missing required current input => fail closed. Stake JPY10,000/race with Dutch allocation.

## Stable source milestones
- Wave19b Run `34749707037` failed on missing payout column; superseded by all-race rebuild. Preserve failure but never reduce scope because of it.
- Wave20 Run `34749917116`: success; full six-boat universe 32,111R. Feb 4100 / Mar 4607 / Apr 4244 / May 4832 / Jun 4488 / Jul 4920 / Aug 4920.
- Wave21 Run `34751314113`: success; exact settlement usable 31,518/32,111 = 98.153%; both-source agreement 99.9553%; actual 3-head wins 4,040.
- Wave22 Run `34752573368`: success; full 120 closing trifecta odds 31,605/32,111 = 98.424%.

## Earlier research summary
- Wave23 Run `34754875342`: Apr-Jun 651R / ROI 135.062%; Jul-Aug 77.598%; NO_ADOPTION.
- Wave24 Run `34757826506`: Apr-Jun 120R / ROI 95.236%; Jul-Aug 55.145%; NO_ADOPTION.
- Wave25 Run `34757888935`: Apr-Jun 5,427R / ROI 70.701%; Jul-Aug 73.452%; NO_ADOPTION.
- Wave26 Run `34759822824`: INVALIDATED. Used 77 features with leaking `節D...ST/着順`; boat-3 `節D` matched current race on 15,280 rows and `節D着順==1` agreed with actual 3-head at 97.997%.
- Wave27-31 are historical leak-free experiments but used the older broad 678R exclusion and are not definitive corrected-scope tests.

## Scope audit correction
- Exact v288 operational 94R reconstructed from frozen canonical v243 artifact used by `verify-v288-operational-pre-replay` Run `34560827602`.
- Exact 94R matches baseline 94R / 52 hits / payout 1,622,070; routes S55/A21/B18; months Feb8/Mar12/Apr12/May16/Jun14/Jul13/Aug19.
- Baseline code list: `v288_operational_pre_replay_94_baseline_codes.csv`.
- Correct research scope from Wave32 onward = Wave20 full six-boat population minus exact v288 94R only.

## Wave32 — FINAL corrected-scope ExtraTrees broad selection
- Run `34766794599`: success; artifact `3head-wave32-extratrees-corrected-scope` ID `10320636906`.
- Family: ExtraTrees 3-head gate + conditional exact-order logistic; 63 static card-only features.
- Exact v288 baseline exclusion hard-check passed; selected overlap 0.
- March tune from Feb-only chose p3>=0.32 / top5: 3,670R / ROI 80.636%.
- Apr-Jun corrected-scope holdout: 10,324R / 781 hits / ROI 78.449% / profit -22,249,650 yen.
- Monthly ROI: Apr 75.476% / May 76.715% / Jun 83.014%; red months 3; minimum 75.476%.
- Jul-Aug NON-PRISTINE shadow: 7,417R / ROI 77.955%.
- Combined v288 + holdout ROI 79.298%.
- Decision: NO_ADOPTION.
- Interpretation: broad selection buys too many races. Next family must deliberately target sparse, high-confidence 3-head opportunities.

## Wave33 — NEXT sparse high-confidence corrected-scope family
- Goal: sharply reduce race count and test whether only the strongest 3-head signals can clear profitability.
- Keep corrected full-population-minus-exact-94 scope, 63 leak-free static features, pre-April model selection, Jul/Aug shadow only, September forbidden, closing odds staking-only, JPY10k Dutch.
- Use nonlinear head probability plus exact-order concentration and freeze March-derived high-confidence cutoffs before Apr-Jun evaluation.
- March selection must require a meaningful sample floor but explicitly allow a sparse candidate set; do not optimize Jul/Aug.

## Exact restart point
1. Implement and launch Wave33 sparse high-confidence family.
2. If failed, inspect logs, fix automatically, rerun without weakening guards.
3. If success, record March gates; Apr-Jun R/hits/ROI/profit/monthly/min month/red months/max DD; Jul-Aug shadow; exact v288 overlap; combined baseline.
4. Adoption status uses pristine Apr-Jun only. Jul/Aug cannot rescue a weak result.
5. If NO_ADOPTION, automatically continue with another genuinely distinct corrected-scope leak-free full-population family.
