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

## Wave26 — FINAL conditional exact-order softmax
- Run `34759822824`, workflow `research-3head-wave26-exactorder`: **success**.
- Head SHA `2761d402e1619abea4c4475a46e972908fd17981`.
- Artifact `3head-wave26-exactorder-softmax`, ID **`10318069914`**.
- Source rows **30,746R**; pre-deadline features **77**; 21 classes (`OTHER` + twenty 3-head exact orders); legacy overlap **0**.
- Frozen choice selected on pristine Apr-Jun only: **p3>=0.40, top3 tickets**.
- Pristine Apr-Jun: **1,125R / 167 hits / stake 11,250,000 / ROI 226.722% / profit +14,256,180 yen**.
- Monthly pristine: Apr **389R / 85 hits / ROI 258.811% / +6,177,760**; May **455R / 53 hits / ROI 272.062% / +7,828,830**; Jun **281R / 29 hits / ROI 108.882% / +249,590**.
- Min pristine month ROI **108.882%**; red pristine months **0**; max DD **1,361,370 yen**.
- Jul-Aug NON-PRISTINE shadow, frozen config: **487R / 56 hits / ROI 82.152% / profit -869,190 yen**.
- Shadow monthly: Jul **240R / 28 hits / ROI 80.142% / -476,600**; Aug **247R / 28 hits / ROI 84.106% / -392,590**.
- Baseline + pristine add-on: **1,219R / ROI 222.545% / profit +14,938,250 yen**.
- Decision from script: **SHADOW_CANDIDATE**. Do **not** replace v288 automatically because Jul-Aug frozen shadow is materially weak.

## Exact restart point
1. Wave26 is the first full-population family to clear the legacy ROI floor on Apr-Jun with zero red pristine months and zero overlap.
2. Before any adoption, run a separate frozen-config robustness validation of Wave26. Do not retune from Jul/Aug outcomes.
3. Validation priorities: leakage audit; venue/grade/time stability; ticket-probability calibration; contribution concentration; sensitivity around p3=0.40/top3 using only pristine history; and a frozen forward/shadow protocol.
4. Jul/Aug remain NON-PRISTINE and may be reported only as shadow evidence; September outcomes remain forbidden.
5. Keep v288 production unchanged unless an independent validation supports promotion.
