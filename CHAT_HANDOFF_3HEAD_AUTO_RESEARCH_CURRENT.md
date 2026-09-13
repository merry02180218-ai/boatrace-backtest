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
- Correct scope from Wave32 onward = Wave20 full six-boat population minus exact v288 operational 94R only.

## Wave34 — FINAL prototype-distance
- Run `34768428513`: Apr-Jun 386R / 53 hits / ROI 84.243% / profit -608,230 yen.
- Apr 96.157% / May 66.650% / Jun 90.880%; combined v288 + holdout ROI 101.538% / +73,840 yen.
- NO_ADOPTION but retained as promising research family.

## Wave34b — FINAL prototype-stability extension
- Run `34769342335`: success; artifact `3head-wave34b-prototype-stability` ID `10321421797`.
- March fixed gate from Feb-only: prototype_mean>=0.233221, agreement>=0.55, top3; 45R / 14 hits / ROI 189.300%.
- Apr-Jun pristine holdout: 387R / 54 hits / ROI 85.449% / profit -563,130 yen.
- Monthly: Apr 107R / 15 hits / ROI 94.839% / -55,220; May 118R / 17 hits / ROI 73.993% / -306,880; Jun 162R / 22 hits / ROI 87.591% / -201,030.
- Min month 73.993%; red months 3; max DD 964,000 yen.
- Jul-Aug NON-PRISTINE shadow: 458R / 66 hits / ROI 75.338% / -1,129,530 yen.
- Combined baseline + holdout: 481R / ROI 102.473% / profit +118,940 yen.
- Delta vs Wave34: +1.206 ROI pt / +45,100 yen / May +7.343 ROI pt.
- Exact v288 overlap 0. Decision NO_ADOPTION.
- Interpretation: stability ensemble improves Wave34 modestly and improves May materially, so continue this family.

## Wave34c — NEXT loss-risk filter on Wave34b
- User requested continued research on Wave34 family.
- Preserve Wave34b prototype mean/agreement score and exact-order top-K logic.
- Add a separate loss-risk / false-positive filter trained only on information available before the pristine period. Do not use Apr-Jun labels or ROI for tuning.
- Feb is model training; March is the only gate/filter selection month. Freeze all thresholds before Apr-Jun.
- Candidate filter should learn which high prototype-score races fail to become 3-head, using only the same 63 static pre-deadline features plus Wave34b score/agreement diagnostics derived from historical training.
- Keep selection sparse; compare removing the highest predicted-loss tail from the fixed Wave34b March-qualified population while preserving a minimum March sample floor.
- Primary comparison: Apr-Jun ROI/profit, especially May ROI vs Wave34b 73.993%, while not materially damaging Apr/Jun. Report max DD and combined v288 ROI.
- Jul/Aug NON-PRISTINE shadow only; September forbidden; closing odds staking-only; exact v288 overlap must be 0.

## Exact restart point
1. Implement and launch Wave34c loss-risk filter extension.
2. If failed, inspect logs, fix automatically, rerun without weakening guards.
3. If success, compare directly with Wave34 and Wave34b: March gate/filter, Apr-Jun R/hits/ROI/profit/monthly/min month/red months/max DD, Jul-Aug shadow, overlap, combined baseline.
4. Adoption uses pristine Apr-Jun only; Jul/Aug cannot rescue weak results.
5. If Wave34c improves, continue targeted prototype-distance refinement rather than switching away immediately.
