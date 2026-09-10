# Official 3-head model adoption — v288 100R

Adopted on 2026-09-11 JST by user decision.

## Status
- OFFICIALLY ADOPTED for 3-head operation.
- Historical performance is model-selection evidence, NOT pristine validation.
- July/August 2026 remain NON-PRISTINE.
- Do not change thresholds during September forward operation without creating a new version.

## Base chain
`v249 PRE S+A -> v243 final selection -> v242 variable 5-10 tickets -> JPY 10,000 Dutch`

## Route S: fixed high-precision core
Requirements:
- v249 S+A and v243 final target
- `f__c_b3_minus_b4_waku_st <= 0.4999999999999999`
- `f__c_b3_minus_b4_st >= -0.6`
- `f__c_b3_meetst <= 0.861111111111111`

Historical result:
- 58 races
- 34 hits
- hit rate 58.62%
- stake JPY 580,000
- payout JPY 1,048,340
- profit +JPY 468,340
- ROI 180.75%

## Route A: independent expansion outside S
Apply only to v249 S+A purchasable races that are NOT selected by S.

Requirements:
- `f__c_b3_minus_b4_st >= 0.6`
- `f__c_wall12_weak <= 0.24875`

Historical incremental result:
- +24 races
- 13 hits
- hit rate 54.17%
- payout JPY 398,980
- profit +JPY 158,980
- ROI 166.24%

S + A:
- 82 races
- 47 hits
- hit rate 57.32%
- payout JPY 1,447,320
- profit +JPY 627,320
- ROI 176.50%

## Route B: second independent expansion outside S+A
Apply only to remaining v249 S+A purchasable races after S and A.

Requirements:
- `f__c_b3_minus_b2_motor >= 0.22388571428571424`
- `f__c_b3_inside_nst <= -0.0714285714285712`

Historical incremental result:
- +18 races
- 9 hits
- hit rate 50.00%
- payout JPY 296,490
- profit +JPY 116,490
- ROI 164.72%

## Official combined v288 result
- 100 races
- 56 hits
- hit rate 56.00%
- stake JPY 1,000,000
- payout JPY 1,743,810
- profit +JPY 743,810
- ROI 174.381%

Monthly historical combined:
- Feb: 8R / 5 hits / 62.50% / ROI 198.14% / +78,510
- Mar: 12R / 7 hits / 58.33% / ROI 175.32% / +90,380
- Apr: 13R / 9 hits / 69.23% / ROI 212.87% / +146,730
- May: 17R / 11 hits / 64.71% / ROI 198.59% / +167,610
- Jun: 16R / 9 hits / 56.25% / ROI 169.35% / +110,960
- Jul NON-PRISTINE: 14R / 3 hits / 21.43% / ROI 80.90% / -26,740
- Aug NON-PRISTINE: 20R / 12 hits / 60.00% / ROI 188.18% / +176,360

## Operational rule
Evaluate in strict order:
1. Candidate must pass the existing v249/v243 purchasable chain.
2. If S conditions pass -> select as S.
3. Else if A conditions pass -> select as A.
4. Else if B conditions pass -> select as B.
5. Else -> NO BET.
6. For any selected race, use the existing v242 variable 5-10 ticket construction and exactly JPY 10,000 Dutch staking.

S/A/B here are route labels for selection logic. They do not authorize ad-hoc staking changes unless a new staking model is separately tested and versioned.

## Forward-use rule
Freeze this specification before evaluating new outcomes. Any threshold modification, new feature, route extension, or staking change requires a new version and must not overwrite this adopted baseline.
