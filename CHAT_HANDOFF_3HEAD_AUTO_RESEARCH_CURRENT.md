# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline: 94R / 52 hits / ROI 172.560638%.
- FINAL scope: Wave20 full six-boat population Feb 1-Aug 31 2026; exclude exact v288 operational 94R only.
- Prediction uses pre-deadline card information only. Settlement/closing odds evaluation/staking only.
- JPY10,000 per selected race, Dutch; v288 overlap must be zero.

## Wave36 current benchmark
- Run 34780059085; shrinkage-LDA head gate + conditional logistic Top5.
- Apr-Jun 391R / 87 hits / ROI 114.913% / +583,090 yen.
- Apr 175.280%, May 103.005%, Jun 70.290%.

## Wave36X extended learning — COMPLETE
- Run 34784017004 success; artifact 10326071695.
- Expanding Apr-Aug: 718R / 166 hits / ROI 103.145% / +225,820 yen.
- Monthly ROI Apr 175.280 / May 103.005 / Jun 70.290 / Jul 77.896 / Aug 99.025.
- Learning July did not improve August: expanding Aug 99.025% vs frozen-through-Jun 100.253%.
- Exact v288 overlap 0. Jul/Aug remain NON-PRISTINE for adoption.

## Wave36D temporal degradation diagnosis — COMPLETE
- Run 34784246428 success; artifact 10325977322.
- No model/staking tuning was performed; diagnostic only.
- Monthly head/order/payout decomposition:
  - Apr: 121R / head rate 44.63% / Top5 conversion 61.11% / ROI 175.28%; winning-return mean 64,269 yen, median 39,130.
  - May: 145R / head rate 40.69% / conversion 55.93% / ROI 103.00%; winning-return mean 45,260, median 32,600.
  - Jun: 125R / head rate 37.60% / conversion 44.68% / ROI 70.29%; winning-return mean 41,840, median 38,850.
  - Jul: 154R / head rate 38.31% / conversion 57.63% / ROI 77.90%; winning-return mean 35,282, median 32,935.
  - Aug: 173R / head rate 42.20% / conversion 61.64% / ROI 99.02%; winning-return mean 38,070, median 32,940.
- Main diagnosis:
  1. June weakness is primarily model-quality degradation: both head hit rate and Top5 conversion fell sharply, especially the low p3 band 0.365-0.40 (head rate 22.2%, conversion 25.0%).
  2. July head rate stayed weak, but Top5 conversion recovered to 57.6%. July monetary weakness is therefore more payout/mix driven; mean winning return fell to 35,282 yen, the lowest Apr-Aug.
  3. August model quality largely recovered (head 42.2%, conversion 61.6%) but payout level remained far below April, explaining ROI near breakeven rather than April-like profit.
  4. High p3 was not consistently safer in June/July: June p3>0.60 head rate only 16.7%; July p3>0.60 only 14.3%. This indicates notable p3 miscalibration / temporal instability rather than a simple threshold issue.
- Static 63-feature drift versus Apr-May reference was moderate and strongest in relative ST / racer strength fields:
  - June top shifts ~0.31 SD: b3-vs-b2 local 2-rate and national average ST; motor 2/3-rate gaps also ~0.24 SD.
  - July strongest shift 0.512 SD in b3-minus-mean national avg ST; b3-vs-b4 national win-rate/ST ~0.41 SD; several racer-strength gaps ~0.33-0.37 SD.
  - August shifts remained ~0.30-0.39 SD, mainly b3-vs-b2 national strength and b3 own local/national strength.
- Venue mix could not be diagnosed because no explicit venue column was present in the settled source used by this script.
- Exact v288 overlap 0.
- Interpretation: June is mainly head+order model degradation; July is mainly weak head calibration plus lower payout mix; August recovers prediction quality but not payout richness. A simple fixed higher p3 cutoff is not supported by the diagnostic.

## Exact restart point
1. Keep Wave36 fixed Top5 as benchmark.
2. Next improvement should target temporal calibration/robustness of the p3 head model, especially June/July, rather than another ticket-count rule.
3. Any new calibration method must be designed from pre-April data only for pristine validation; Jul/Aug may be used only as non-pristine robustness diagnostics unless explicitly requested otherwise.
