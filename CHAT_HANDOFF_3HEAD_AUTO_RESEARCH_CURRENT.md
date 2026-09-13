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

## Wave32 — FINAL
- Run `34766794599`: Apr-Jun 10,324R / 781 hits / ROI 78.449% / profit -22,249,650 yen. NO_ADOPTION.

## Wave33 — FINAL
- Run `34767681917`: Apr-Jun 235R / 35 hits / ROI 57.226% / profit -1,005,180 yen. NO_ADOPTION.

## Wave34 — FINAL prototype-distance family
- Retry Run `34768428513`: success; artifact `3head-wave34-prototype-distance` ID `10320144189`.
- Family: standardized positive-vs-negative prototype-distance head score + conditional logistic exact-order model; 63 static features; overlap 0.
- March gate from Feb-only: score>=0.234255, top3; 45R / 13 hits / ROI 177.860% / +350,370 yen.
- Apr-Jun pristine holdout: 386R / 53 hits / ROI 84.243% / profit -608,230 yen.
- Monthly: Apr 116R / 16 hits / ROI 96.157%; May 131R / 17 hits / ROI 66.650%; Jun 139R / 20 hits / ROI 90.880%.
- Min month 66.650%; red months 3; max DD 886,340 yen.
- Jul-Aug NON-PRISTINE shadow: 464R / 67 hits / ROI 75.100% / -1,155,370 yen.
- Combined baseline + holdout: 480R / 105 hits / ROI 101.538% / +73,840 yen.
- Decision NO_ADOPTION, but user explicitly wants additional research because this family looks materially more promising than Waves32/33.

## Wave35 — PARALLEL comparison only
- Local-neighbor family completed on newer duplicate Run `34769064788` with success; metrics not yet promoted into the main decision path because user explicitly redirected research toward Wave34 extension.

## Wave34b — RUNNING targeted prototype-distance extension
- User explicitly requested additional research on Wave34 rather than abandoning the family.
- Script: `research_v289_3head_wave34b_prototype_stability.py`, commit `cca77dcb68a781a4f138109cb6c91f1cf4a55105`.
- Workflow: `.github/workflows/research-3head-wave34b-prototype-stability.yml`, registration commit `74ea81ca0ac4926c27758e360e2792b731923e4d`, trigger follow-up `9c5201c0a8bad01c488722a1f8130e0fc4dba740`.
- Run `34769342335` is in progress.
- Core idea preserved: prototype-distance head scoring.
- Extension: 9 bootstrap positive/negative prototype views; use prototype mean, score SD, and cross-view agreement. March can choose either mean-score or stability-adjusted score plus agreement cutoff and top3/top5/top7.
- Only Feb trains March selection. Apr-Jun untouched pristine evaluation. Jul/Aug frozen NON-PRISTINE shadow only.
- Corrected full-population-minus-exact-94 scope; same 63 static features; closing odds staking-only; JPY10k Dutch; zero overlap required.
- Must compare directly against Wave34, especially Apr/May/Jun ROI and May improvement, plus race count, profit, DD and combined v288 ROI.

## Exact restart point
1. Inspect Wave34b Run `34769342335` first (and any newer duplicate if present).
2. If failed, inspect logs and fix automatically without weakening guards.
3. If success, record March fixed gates; Apr-Jun R/hits/ROI/profit/monthly/min month/red months/max DD; Jul-Aug shadow; overlap; combined baseline; delta vs Wave34.
4. Adoption uses pristine Apr-Jun only. Jul/Aug cannot rescue a weak result.
5. Continue prototype-distance-specific follow-up if Wave34b improves stability even if it still misses full adoption.
