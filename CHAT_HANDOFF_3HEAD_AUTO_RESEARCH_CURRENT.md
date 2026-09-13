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
- Wave27 Run `34763079073`: 63 static features; May-Jun holdout 195R / ROI 57.947%; Jul-Aug 124.170%; NO_ADOPTION.
- Wave28 Run `34764021442`: structural gate; May-Jun 75R / ROI 73.745%; Jul-Aug 128.013%; NO_ADOPTION.
- Wave29 Run `34764558658`: Feb train -> Mar tune p3>=0.38/top7; Apr-Jun 342R / 63 hits / ROI 93.845% / -210,510; Apr 123.769%, May 78.718%, Jun 56.762%; Jul-Aug 111.906%; combined 110.816%; NO_ADOPTION.

## Wave30 — FINAL two-stage linear family
- Run `34765791471`: success; artifact `3head-wave30-twostage-preapril` ID `10320691590`.
- March tune p3>=0.30/top7: 160R / ROI 103.285%.
- Apr-Jun: 547R / 104 hits / ROI 81.210% / -1,027,810.
- Apr 112.334% / +222,010; May 73.083% / -557,180; Jun 56.710% / -692,640.
- Min month 56.710%; red months 2; max DD 1,333,820.
- Jul-Aug shadow 386R / 89 hits / ROI 76.262% / -916,270.
- Combined baseline + holdout 641R / ROI 94.606% / -345,740. Decision NO_ADOPTION.

## Wave31 — FINAL nonlinear HGB head gate
- Latest successful Run `34765910652`; artifact `3head-wave31-nonlinear-gate` ID `10320971097`.
- Family: HistGradientBoosting 3-head gate + conditional exact-order logistic; 63 static card-only features.
- March tune from Feb only: p3>=0.18/top5; 313R / ROI 82.474%.
- Apr-Jun walk-forward holdout: 806R / 85 hits / stake 8,060,000 / payout 6,378,170 / profit -1,681,830 / ROI 79.134%.
- Monthly: Apr 296R / 32 hits / ROI about 93.126% / -203,470; May 306R / 32 hits / ROI 74.604% / -777,110; Jun 204R / 21 hits / ROI 66.237% / -688,770.
- Min month 66.237%; red months 3; max DD 2,247,630.
- Jul-Aug NON-PRISTINE shadow: 592R / 123 hits / ROI 85.673% / -848,140. Jul 73.406%; Aug 95.959%.
- Combined baseline + holdout: 900R / 137 hits / ROI 88.892% / -999,760. Decision NO_ADOPTION.

## Scope audit correction after Wave31
- Source audit found Waves27-31 excluded all 678 old v243 candidate rows via `auto_refine_execution_candidates` / Wave19 source instead of excluding only the fixed v288 94R baseline.
- Therefore Waves27-31 are historical experiments, but are NOT definitive full-population tests under the latest corrected scope.
- Exact v288 operational 94R was reconstructed from the frozen canonical v243 artifact used by `verify-v288-operational-pre-replay` Run `34560827602` and matches 94R / 52 hits / payout 1,622,070 plus route counts S55/A21/B18 and monthly counts Feb8/Mar12/Apr12/May16/Jun14/Jul13/Aug19.
- Exact code list committed as `v288_operational_pre_replay_94_baseline_codes.csv`; corrected commit `9cc1cb666f5cf66a662f8f308cec56ac357f6948`.
- This correction does NOT change the fixed v288 baseline metrics; it changes which races are eligible for new add-on research.

## Wave32 — RUNNING corrected-scope ExtraTrees
- Script: `research_v289_3head_wave32_extratrees_gate.py`, commit `e73f46772cb14f54690aa8ad36c411242c981a45`.
- Workflow: `.github/workflows/research-3head-wave32-extratrees.yml`, commit `9b95658a41fe168a809dfee6a10318e0dacee7bb`; trigger follow-up `e3c07ad480f5b3a95a23672e78ce4d23e856275e`.
- Run `34766777947` currently in progress.
- Family: fixed-hyperparameter ExtraTrees 3-head gate + conditional exact-order logistic; same 63 static card-only pre-deadline features.
- Scope: Wave20 full population, exact v288 94R exclusion only; no old 678R candidate exclusion/prefilter.
- Protocol: Feb trains March for threshold/top-K selection; Apr-Jun walk-forward holdout; Jul-Aug frozen NON-PRISTINE shadow; September forbidden; closing odds staking-only; JPY10k Dutch.
- Workflow hard-checks exact 94 baseline code count, uniqueness, S55/A21/B18 and monthly 8/12/12/16/14/13/19 before research.

## Exact restart point
1. Inspect Run `34766777947` first (and any newer Wave32 duplicate if present).
2. If failed, inspect jobs/logs, fix automatically, and rerun without weakening leak/date/overlap/baseline guards.
3. If success, record March threshold/top-K; Apr-Jun R/hits/ROI/profit/monthly/min month/red months/max DD; Jul-Aug shadow; exact v288 overlap; combined baseline.
4. Adoption status uses pristine Apr-Jun only. Jul/Aug cannot rescue a weak result.
5. If NO_ADOPTION, automatically launch another genuinely distinct corrected-scope leak-free full-population family.
