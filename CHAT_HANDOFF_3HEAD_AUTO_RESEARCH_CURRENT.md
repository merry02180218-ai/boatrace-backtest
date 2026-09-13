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

## Wave39V combined-odds variable ticket count — COMPLETE
- Run 34782837106 success; artifact 10325389748.
- March chose combined-odds floor 3.5.
- Apr-Jun variable K: 391R / 92 hits / ROI 103.009% / +117,670 yen; avg K 6.069; min month 67.066%; red months 2; overlap 0.
- Monthly: Apr 147.838%, May 96.587%, Jun 67.066%. Fixed Top5 remained better at 114.913%.

## Wave39C confidence-aware variable ticket count — COMPLETE / NO_ADOPTION
- Run 34783195043 success; artifact 10325494927.
- March selected rule p45_k4_f35: if p3>=0.45 use fixed Top4; otherwise variable K under combined-odds floor 3.5.
- March: 90R / 25 hits / ROI 138.104%; early 168.931%, late 107.278%; avg K 5.978.
- Apr-Jun pristine: 391R / 84 hits / ROI 98.103% / -74,190 yen; avg K 5.529; min month 65.757%; red months 2; max DD 689,670 yen; overlap 0.
- Monthly: Apr 121R / 31 hits / ROI 131.230% / +377,880; May 145R / 32 hits / ROI 98.343% / -24,030; Jun 125R / 21 hits / ROI 65.757% / -428,040.
- Jul-Aug NON-PRISTINE shadow: 328R / 68 hits / ROI 85.825% / -464,940; avg K 4.957.
- Fixed Top5 Apr-Jun remains superior: 391R / 87 hits / ROI 114.913% / +583,090.
- Conclusion: p3 confidence + combined-odds variable K did not generalize; it lost 3 hits and 16.81 ROI points versus fixed Top5. NO_ADOPTION.

## Exact restart point
1. Keep fixed Top5 as current staking benchmark for Wave36/37.
2. Do not tune further on Apr-Jun outcomes. Any next staking idea must be predeclared and selected using March only.
3. Wave39 candidate-pair ranker, if still active/completed, inspect and record separately.
4. Prefer model/order robustness research over further broad ticket expansion unless a genuinely distinct pre-April rule is proposed.
