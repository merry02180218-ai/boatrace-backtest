# v288 3-head: fixed 58R core + independent A/B expansion candidate

Historical exploratory audit on frozen canonical v243 artifact. July/August are NON-PRISTINE and must not be described as validation.

## Fixed S core (unchanged)
- v249 S+A and v243 final target
- `f__c_b3_minus_b4_waku_st <= 0.4999999999999999`
- `f__c_b3_minus_b4_st >= -0.6`
- `f__c_b3_meetst <= 0.861111111111111`
- 58 races / 34 hits / 58.62% / payout 1,048,340 / profit +468,340 / ROI 180.75%

## Existing expansion route A
Applied only to v249 S+A purchasable races outside fixed core:
- `f__c_b3_minus_b4_st >= 0.6`
- `f__c_wall12_weak <= 0.24875`
- 24 additional races / 13 hits / 54.17% / payout 398,980 / profit +158,980 / ROI 166.24%

Core + A:
- 82 races / 47 hits / 57.32% / payout 1,447,320 / profit +627,320 / ROI 176.50%

## New independent expansion route B candidate
Applied only to remaining v249 S+A purchasable races after core + A:
- `f__c_b3_minus_b2_motor >= 0.22388571428571424`
- `f__c_b3_inside_nst <= -0.0714285714285712`

Route B:
- 18 additional races / 9 hits / 50.00%
- payout 296,490 / profit +116,490 / ROI 164.72%

### Combined historical candidate
- **100 races / 56 hits / 56.00%**
- stake 1,000,000
- payout **1,743,810**
- profit **+743,810**
- ROI **174.381%**

Monthly combined:
- Feb: 8R / 5 hits / 62.50% / ROI 198.14% / +78,510
- Mar: 12R / 7 hits / 58.33% / ROI 175.32% / +90,380
- Apr: 13R / 9 hits / 69.23% / ROI 212.87% / +146,730
- May: 17R / 11 hits / 64.71% / ROI 198.59% / +167,610
- Jun: 16R / 9 hits / 56.25% / ROI 169.35% / +110,960
- Jul NON-PRISTINE: 14R / 3 hits / 21.43% / ROI 80.90% / -26,740
- Aug NON-PRISTINE: 20R / 12 hits / 60.00% / ROI 188.18% / +176,360

## Selection warning
Route-B candidate thresholds were generated from Feb-Jun training-side feature distributions/performance, then Jul/Aug were inspected as NON-PRISTINE robustness evidence. Because multiple candidates were compared and Jul/Aug performance was visible during model development, the combined 100R numbers are historical/model-selection evidence, not pristine validation.

A further third expansion to 110+ races was searched. No simple train-selected single/two-feature route found in this pass maintained the combined 55% hit-rate target at 110+ without relying on additional historical selection. Therefore 100R is the current preferred expansion candidate; do not force 110-116R by loosening thresholds.
