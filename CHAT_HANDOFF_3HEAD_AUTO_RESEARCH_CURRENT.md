# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline: 94R / 52 hits / ROI 172.560638%.
- FINAL scope: Wave20 full six-boat population Feb 1-Aug 31 2026; exclude exact v288 operational 94R only.
- Jul/Aug NON-PRISTINE shadow only; September outcomes forbidden.
- Prediction uses pre-deadline card information only. Settlement/closing odds evaluation/staking only.
- JPY10,000 per selected race, Dutch; v288 overlap must be zero.

## Stable source
- Wave20 Run 34749917116 success: 32,111R.
- Wave21 Run 34751314113: settlement usable 31,518R.
- Wave22 Run 34752573368: full 120 closing odds 31,605R.

## Wave36 shrinkage-LDA — RESEARCH CANDIDATE
- Run 34780059085; Apr-Jun 391R / 87 hits / ROI 114.913% / +583,090 yen.
- Apr 175.280%, May 103.005%, Jun 70.290%; Jul-Aug shadow 89.756%; overlap 0.

## Wave37 opponent/order research — COMPLETE
- Run 34782216334 success; artifact 10325149135.
- March conditional conversion: logit 63.158%, position 50.000%, ExtraTrees 34.211%.
- Apr-Jun 391R / 87 hits / ROI 114.913%; conditional conversion 54.375%.

## Wave38 opponent structural features — COMPLETE
- Run 34782510443 success; artifact 10325785027.
- Expanded 198-feature opponent set lost to static63 on March; no improvement. Apr-Jun remains 114.913%.

## Wave39 candidate-pair ranker — RUNNING
- Run 34782729676 currently in progress.
- Freeze Wave36 head gate p3>=0.365448 and head chronology.
- Pair-ranker selection Feb->Mar only; Apr-Jun pristine; Jul/Aug shadow.

## Wave39V combined-odds variable ticket count — STARTED
- This is a staking/ticket-count layer, independent of head/order model training.
- Freeze Wave36/37 head gate p3>=0.365448 and current static63 conditional-logit ranking. No prediction-model retuning.
- For each selected race, rank candidate 3-a-b tickets by model score. Use historical closing trifecta odds only as a staking proxy for deadline odds; never as prediction features.
- Define combined/effective Dutch odds for a ticket set T as 1 / sum(1/odds_t). Add ranked tickets sequentially and choose the largest K within a predeclared min/max range whose combined odds remains at or above a floor.
- Compare fixed Top5 against variable-K floors using March only for staking-rule choice. Candidate floors are predeclared; no Apr-Jun tuning.
- Keep total stake JPY10,000 per selected race and Dutch allocate across chosen tickets in JPY100 units.
- Evaluate Apr-Jun untouched: races/hits/ROI/profit/monthly/min month/red months/max DD/average K/K distribution and exact v288 overlap. Jul/Aug NON-PRISTINE shadow only; September forbidden.
- Important: historical closing odds are an approximation for live deadline odds. Any favorable result remains research evidence until confirmed with true pre-deadline/live odds snapshots.

## Exact restart point
1. Let Wave39 finish and record result.
2. Implement/run Wave39V variable combined-odds ticket count on frozen Wave36/37 ranking.
3. Auto-fix technical failures without weakening guards.
4. Record whether variable K improves pristine Apr-Jun robustness versus fixed Top5 114.913%.
