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

## Wave25 — RUNNING latent regime cluster family
- Script commit `c6c3020121ad10f5a8e39c249742f25e8f47764e`: `research_v289_3head_wave25_regime_cluster.py`.
- Workflow commit `9067353322e0549042df80dde64b706093a6c2f8`: `.github/workflows/research-3head-wave25-regime.yml`.
- Current Run: **`34757888935`**, workflow `research-3head-wave25-regime`, latest launch state **queued**.
- Distinct family: pre-deadline features -> median impute -> StandardScaler -> PCA 12 -> KMeans 24 latent regimes; prediction is smoothed prior-data 3-head frequency of assigned regime.
- Same conservative old-v243 678R exclusion guarantees legacy overlap=0.
- Apr/May/Jun prior-only walk-forward; threshold selection Apr-Jun only; Jul/Aug frozen NON-PRISTINE shadow.
- Closing odds and settlement remain post-selection only; JPY10,000/race all-20 Dutch.
- Strict decision: SHADOW_CANDIDATE only if pristine ROI >= 172.560638% and zero red pristine months; else NO_ADOPTION.

## Exact restart point
1. Inspect Run `34757888935` first.
2. If failed, inspect logs, fix, rerun automatically without weakening date/no-leakage/zero-overlap guards.
3. If success, record exact Wave25 pristine and NON-PRISTINE shadow metrics, artifact ID, overlap and combined baseline.
4. If Wave25 is `NO_ADOPTION`, continue another genuinely distinct family (opponent-ticket rerank / conditional exact-order model), not threshold loosening.
5. If `SHADOW_CANDIDATE`, do not replace v288 automatically; validate separately.
