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
- Artifact `3head-wave21-allrace-source-build`, ID `10316748754` (Wave21 source enriched with closing odds).
- Source: Kyotei24 Odds Bank historical 3T pages explicitly labelled `締切時オッズ`.
- odds available/full 120: **31,605/32,111 = 98.424%**.
- Monthly coverage: Feb 4021/4100 98.07%; Mar 4523/4607 98.18%; Apr 4165/4244 98.14%; May 4731/4832 97.91%; Jun 4418/4488 98.44%; Jul 4877/4920 99.13%; Aug 4870/4920 98.98%.
- Decision: `CLOSING_ODDS_SOURCE_READY`.
- Closing odds remain excluded from prediction features; use only after selection for staking/post-hoc ROI.

## Wave23 — FINAL full-population tree walk-forward
- Run `34754875342`, workflow `research-3head-wave21-allrace-source-build`, head `3d27fa6a1c215346693b92d30a07db10a5ced135`: success.
- Artifact `3head-wave21-allrace-source-build`, ID `10317157868`.
- Source after conservative old-v243 678R exclusion: **30,746R**; legacy v288 overlap **0**.
- Features **77**; HistGradientBoosting; chosen threshold **0.40**.
- Pristine Apr-Jun: **651R / 250 hits / stake 6,510,000 / payout 8,792,530 / ROI 135.062% / profit +2,282,530 yen**.
- Pristine monthly:
  - Apr: 232R / 130 hits / ROI 196.434% / profit +2,237,260 yen.
  - May: 247R / 82 hits / ROI 131.256% / profit +772,030 yen.
  - Jun: 172R / 38 hits / ROI 57.747% / profit -726,760 yen.
- min-month ROI **57.747%**; red months **1**; max DD **1,184,940 yen**.
- Jul-Aug NON-PRISTINE shadow: **296R / 80 hits / ROI 77.598% / profit -663,100 yen**.
  - Jul: 143R / 34 hits / ROI 60.289% / profit -567,870 yen.
  - Aug: 153R / 46 hits / ROI 93.776% / profit -95,230 yen.
- Baseline + pristine add-on: **745R / ROI 139.793% / profit +2,964,600 yen**.
- Decision: **NO_ADOPTION**. Do not relax threshold family to rescue it.

## Wave24 — RUNNING distinct latent nearest-neighbor analog family
- Script commit `9ae0803b30e1163d81c435076a81aaa00795f401`: `research_v289_3head_wave24_neighbor_analog.py`.
- Workflow commit `adde22ffca67eaa160c4849af41afdaa44317ee6`: `.github/workflows/research-3head-wave24-neighbor.yml`.
- Current Run: **`34757826506`**, workflow `research-3head-wave24-neighbor`, status at launch **in_progress**.
- Distinct family: same pre-deadline feature construction -> median impute -> StandardScaler -> PCA 12 latent components -> 200-neighbor distance-weighted Euclidean KNN.
- Same conservative old-v243 678R exclusion guarantees legacy v288 overlap=0.
- Apr/May/Jun use prior-month-only walk-forward predictions; threshold selected on Apr-Jun only; Jul/Aug frozen NON-PRISTINE shadow only.
- Closing odds and settlement remain post-selection only; JPY10,000/race all twenty `3-x-y` exact-order Dutch in JPY100 units.
- Decision rule remains strict: SHADOW_CANDIDATE only if pristine ROI >= legacy 172.560638% and zero red pristine months; else NO_ADOPTION.

## Exact restart point
1. Inspect Run `34757826506` first.
2. If failed, inspect logs, fix, and rerun automatically without weakening no-leakage/date/zero-overlap guards.
3. If success, report exact Wave24 pristine Apr-Jun R/hits/stake/payout/ROI/profit/monthly/min-month/red-months/max-DD/overlap/combined and Jul-Aug NON-PRISTINE shadow metrics.
4. If Wave24 is `NO_ADOPTION`, automatically launch another genuinely distinct family (opponent-ticket rerank or regime segmentation), not threshold loosening.
5. If `SHADOW_CANDIDATE`, do not replace v288 automatically; validate separately.
6. Jul/Aug NON-PRISTINE; September outcomes forbidden; legacy v288 remains immutable baseline/floor; add-on overlap zero.
