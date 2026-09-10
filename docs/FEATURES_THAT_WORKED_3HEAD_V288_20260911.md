# 3-head v288: features that actually worked

Purpose: record the features that materially improved the adopted 3-head model so they can be tested first when improving other head models. This is not a generic methodology memo; it is a concrete feature ledger.

Status: 3-head v288 100R version is the adopted current model. Historical figures below are model-selection evidence; 2026-07/08 are NON-PRISTINE.

## Adopted 100R structure

### S core (58R)
Applied after the canonical v249 S+A -> v243 final chain.

1. `f__c_b3_minus_b4_waku_st <= 0.4999999999999999`
   - Important Waku10-derived separator.
   - This was the strongest first overlay found when moving from the official 104R set toward higher hit rate / ROI.
   - Exact floating boundary mattered historically; literal `<= 0.5` produced different rows. Do not casually round without normalizing the feature construction first.

2. `f__c_b3_minus_b4_st >= -0.6`
   - Current 3-vs-4 ST-relative feature.
   - Worked well as a second-stage filter after the Waku10 condition.

3. `f__c_b3_meetst <= 0.861111111111111`
   - Meeting/series ST-related feature for boat 3.
   - This was the best-looking third filter among the explored train-side candidates for keeping high hit rate while removing weak races.
   - Operational boundary corresponds to keeping values through the discrete 0.861111... level and rejecting the next observed band around 0.875+.

Historical S-core result:
- 58 races
- 34 hits
- hit rate 58.62%
- payout 1,048,340 yen
- profit +468,340 yen
- ROI 180.75%

### Expansion route A (adds 24R)
Applied only to purchasable v249 S+A races outside the fixed S core.

4. `f__c_b3_minus_b4_st >= 0.6`
   - Strong positive 3-vs-4 ST-relative separation.
   - The same feature that acted as a core lower-bound filter also became useful in the opposite, stronger positive regime for recovery outside the core.

5. `f__c_wall12_weak <= 0.24875`
   - Inner-wall weakness feature for boats 1/2.
   - Useful jointly with strong boat-3 vs boat-4 ST separation.

Historical Route A result:
- +24 races
- 13 hits
- hit rate 54.17%
- payout 398,980 yen
- profit +158,980 yen
- ROI 166.24%

Core + A:
- 82 races
- 47 hits
- hit rate 57.32%
- payout 1,447,320 yen
- profit +627,320 yen
- ROI 176.50%

### Expansion route B (adds 18R)
Applied only to remaining purchasable races after S core + A.

6. `f__c_b3_minus_b2_motor >= 0.22388571428571424`
   - Boat-3 vs boat-2 motor relative-strength feature.
   - This repeatedly appeared as one of the most useful separators when searching for independent extra races while preserving ROI.
   - This is a high-priority feature to test in 4-head / 5-head analogues using target-boat-vs-key-inner-rival motor differences.

7. `f__c_b3_inside_nst <= -0.0714285714285712`
   - Boat-3 relative NST versus inside boats.
   - Worked jointly with the motor-difference feature as an independent B-route selector.

Historical Route B result:
- +18 races
- 9 hits
- hit rate 50.00%
- payout 296,490 yen
- profit +116,490 yen
- ROI 164.72%

## Adopted combined v288 historical result
- 100 races
- 56 hits
- hit rate 56.00%
- stake 1,000,000 yen
- payout 1,743,810 yen
- profit +743,810 yen
- ROI 174.381%

## Other features that showed useful signal during exploration
These were not adopted into v288, but should be placed high in the candidate list when transferring the concept to other head models.

- `f__c_b3_minus_b2_origavg >= 0.1`
  - Strong historical third-filter candidate.
  - 56R / 33 hits / profit +460,460 / ROI 182.225% in the tested 73R branch.
  - Exhibition/original-display-heavy and therefore more selection-sensitive; do not adopt blindly.

- `f__c_b3_minus_b6_meetst <= 0.575`
  - 61R / 34 hits / profit +442,180 / ROI 172.49% in the tested 73R branch.

- `f__c_b3_minus_b2_meetst <= 0.6083333`
  - Improved Feb-Jun train-side profit and retained positive Jul-Aug historical robustness in the explored scan.

- `f__c_b3_outside_straight >= -0.6` and `>= -0.8`
  - Boat-3 outside-relative straight-line/exhibition signal.
  - Useful as supporting evidence that relative straight-line performance matters.

- `f__c_b3_ex >= 0.4`
  - Boat-3 exhibition-related signal that improved the tested subset historically.

- `f__c_b3_outside_ex >= -0.6`
  - Relative exhibition signal vs outside boats.

- `f__c_b3_inside_origavg >= ~0`
  - Relative original-display average vs inside boats.

- `f__c_b3_minus_b1_origavg >= 0.0666667`
  - Boat-3 vs boat-1 original-display average difference.

- `f__c_b3_nst <= 0.785714`
  - Boat-3 NST-related feature.

- `f__b3_vh_p2_display >= 0.4`
  - Display-related feature that showed useful train-side improvement.

- `f__c_b3_straight >= 0.2`
  - Boat-3 straight-line exhibition feature.

## Feature families that should be tested first in other head models
When porting these findings to 4-head / 5-head models, do not copy the literal b3 feature names. Rebuild analogous target-boat-relative features and test these families first:

1. Target boat vs nearest attacking rival ST difference.
2. Target boat vs key inside rival motor difference.
3. Waku10 ST-relative differences.
4. Inner-wall weakness / inside obstruction weakness.
5. Target boat meeting/series ST or NST state.
6. Target vs inside/outside original-display averages.
7. Target vs inside/outside straight-line exhibition performance.

## Important warnings
- July/August 2026 are NON-PRISTINE and must never be presented as untouched validation.
- Several thresholds were selected after comparing many historical candidates; the numbers above are model-selection evidence.
- Waku10 floating-point boundaries currently matter. Before generalizing exact thresholds, normalize/round the underlying constructed feature values so model behavior is not dependent on binary float artifacts.
- The useful discovery is not only each threshold, but especially the recurring pattern: relative target-boat advantage versus specific rivals (ST, motor, Waku10, wall weakness, straight/original display) was more useful than absolute raw values.
