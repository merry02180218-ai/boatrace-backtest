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
- Pristine Apr-Jun: **651R / 250 hits / stake 6,510,000 / payout 8,792,530 / ROI 135.062% / profit +2,282,530 yen**.
- Monthly: Apr 232R / 130 hits / ROI 196.434% / +2,237,260; May 247R / 82 hits / ROI 131.256% / +772,030; Jun 172R / 38 hits / ROI 57.747% / -726,760.
- min month 57.747%; red months 1; max DD 1,184,940 yen.
- Jul-Aug NON-PRISTINE shadow: **296R / 80 hits / ROI 77.598% / -663,100 yen**. Jul 60.289%; Aug 93.776%.
- Baseline + pristine: **745R / ROI 139.793% / +2,964,600 yen**.
- Decision: **NO_ADOPTION**.

## Wave24 — FINAL nearest-neighbor analog
- Run `34757826506`, workflow `research-3head-wave24-neighbor`: completed successfully; artifact `3head-wave24-neighbor-analog`, ID `10317814162`.
- Distinct family: median impute -> StandardScaler -> PCA 12 -> 200-neighbor distance-weighted Euclidean KNN.
- Source **30,746R**; legacy overlap **0**; threshold **0.32**.
- Pristine Apr-Jun: **120R / 55 hits / stake 1,200,000 / payout 1,142,830 / ROI 95.236% / profit -57,170 yen**.
- Monthly: Apr 25R / 16 hits / ROI 151.992% / +129,980; May 44R / 19 hits / ROI 86.268% / -60,420; Jun 51R / 20 hits / ROI 75.151% / -126,730.
- min month **75.151%**; red months **2**; max DD **206,700 yen**.
- Jul-Aug NON-PRISTINE shadow: **77R / 22 hits / ROI 55.145% / profit -345,380 yen**. Jul 51.094%; Aug 58.521%.
- Baseline + pristine: **214R / ROI 129.201% / profit +624,900 yen**.
- Decision: **NO_ADOPTION**. Do not tune K/PCA/threshold on Jul-Aug to rescue it.

## Wave25 — FINAL latent regime cluster
- Run `34757888935`, workflow `research-3head-wave25-regime`: success; artifact `3head-wave25-regime-cluster`, ID `10317569451`.
- Distinct family: pre-deadline features -> median impute -> StandardScaler -> PCA 12 -> KMeans 24 latent regimes; smoothed prior-data 3-head rate per regime.
- Source **30,746R**; legacy overlap **0**; chosen threshold **0.12**.
- Pristine Apr-Jun: **5,427R / 962 hits / stake 54,270,000 / payout 38,369,190 / ROI 70.701% / profit -15,900,810 yen**.
- Monthly: Apr 1,887R / 309 hits / ROI 67.691% / -6,096,740; May 1,799R / 327 hits / ROI 71.962% / -5,044,030; Jun 1,741R / 326 hits / ROI 72.659% / -4,760,040.
- min month **67.691%**; red months **3**; max DD **15,890,810 yen**.
- Jul-Aug NON-PRISTINE shadow: **4,102R / 773 hits / ROI 73.452% / profit -10,890,140 yen**. Jul 74.945%; Aug 71.956%.
- Baseline + pristine: **5,521R / ROI 72.435% / profit -15,218,740 yen**.
- Decision: **NO_ADOPTION**.

## Wave26 — RUNNING conditional exact-order softmax
- Script commit `ad16968a96869ba88fe6707cfebefe84b4b8ed9b`: `research_v289_3head_wave26_exactorder_softmax.py`.
- Workflow commit `2761d402e1619abea4c4475a46e972908fd17981`: `.github/workflows/research-3head-wave26-exactorder.yml`.
- Current Run: **`34759822824`**, workflow `research-3head-wave26-exactorder`, latest launch state **queued**.
- Distinct family: 21-class multinomial softmax predicts `OTHER` vs each of the 20 exact 3-head trifecta orders using pre-deadline features only.
- Ticket ranking is model probability only. Candidate variants jointly choose p3 threshold and top-K ticket count on Apr-Jun only; closing odds are used after selection only for JPY10,000 Dutch settlement.
- Same conservative old-v243 678R exclusion guarantees legacy overlap=0.
- Apr/May/Jun prior-only walk-forward; Jul/Aug frozen NON-PRISTINE shadow; September forbidden.
- Strict decision: SHADOW_CANDIDATE only if pristine ROI >= 172.560638% and zero red pristine months; else NO_ADOPTION.

## Exact restart point
1. Inspect Run `34759822824` first.
2. If failed, inspect logs, fix, rerun automatically without weakening date/no-leakage/zero-overlap guards.
3. If success, record exact Wave26 pristine and NON-PRISTINE shadow metrics, artifact ID, overlap and combined baseline.
4. If Wave26 is `NO_ADOPTION`, continue another genuinely distinct family, not threshold loosening.
5. If `SHADOW_CANDIDATE`, do not replace v288 automatically; validate separately.
