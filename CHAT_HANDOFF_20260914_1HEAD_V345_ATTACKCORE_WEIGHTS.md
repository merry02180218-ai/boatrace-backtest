# v345 attack-core weight diagnostic

## Start state
- Formal production remains unchanged from the current 1-head production profile.
- v344 found `attack_core` to be the strongest and most directionally stable historical association among the reviewed pre-race features.
- Current formula: 0.30*one_ex + 0.30*one_st + 0.23*one_straight + 0.17*one_orig_avg.
- This task is a retrospective diagnostic of alternative component weights, not a production change.
- Primary evaluation window: Feb-Jun historical pristine set. Jul/Aug remain auxiliary only.
- September outcomes remain unread.

## Plan
- Reconstruct the same production-selected rows and v344 broad diagnostic window.
- Sweep nonnegative weights summing to 1.0 on a 0.05 grid across the four attack-core components.
- Include the current exact weight vector as the baseline.
- Measure Spearman association with exact3 top3 hit and return multiple.
- Evaluate leave-one-month-out stability and require attention to worst-fold direction, not just full-sample fit.
- Compare component-only and balanced formulas.
- Do not modify formal production during v345.
