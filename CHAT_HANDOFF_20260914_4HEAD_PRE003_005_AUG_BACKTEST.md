# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **OUTCOME-INDEPENDENT REGIME-SHIFT AUDIT IN PROGRESS**

## Frozen production
Production remains unchanged. S PRE >= 0.28; A PRE >= 0.18; frozen downstream rules remain in force. July/August 2026 remain NON-PRISTINE; September remains outcome-blind for tuning.

## Completed common frozen-scale result
One PRE/POST model frozen at 2026-01-31 and reused unchanged for 2026-02..08, inclusive PRE 0.03..0.05:
- Feb-Jun: 3,764R / 138 wins = 3.67%
- July: 574R / 40 wins = 6.97% (NON-PRISTINE)
- August: 233R / 54 wins = 23.18% (NON-PRISTINE)
- August POST >= 0.18: 0/233; POST >= 0.25: 0/233
- Run ID `34772249054`, Job ID `103763843482`, artifact `10322571216`
- implementation `analyze_4head_common_frozen_20260131.py`
- production unchanged.

## 2026-09-14 regime-shift work-start record
Written **before** implementation.

Goal: determine whether the August low-PRE anomaly coincides with an outcome-independent shift in the frozen model inputs / race composition, without selecting explanations by looking at which August races won.

Planned work:
1. Reuse the exact Jan-31-frozen common-scale replay and its PRE 0.03..0.05 cohort for Feb-Aug.
2. Compare month-level distributions of PRE input features and field/race composition using no target outcome in feature selection: `legacy_score4`, `racer4`, `hist_st_edge_4v3`, `wall3_weak`, `inner12_resistance`, `motor4_2ren`, `motor4_hist`, `turnfoot4_prior`, `past_win4`, plus venue/field composition where available.
3. Quantify drift versus Feb-Jun baseline with fixed distribution metrics (median/mean, standardized mean difference, PSI/KS where technically valid) and report the largest shifts. The ranking criterion is distribution drift only, not win association.
4. Separately produce full frozen-PRE score-bin counts by month to determine whether August drift is broad calibration/population movement or concentrated around the 0.03..0.05 cohort. Do not use outcome rates to select bins or features during this audit.
5. July/August remain descriptive NON-PRISTINE. No rescue rule, threshold, feature selection, or production change may be derived from this audit.
6. Run CI and save machine-readable artifacts/audit. After completion update this handoff with commits, Run IDs, exact drift findings, limitations and next restart point.

Historical ROI permission remains: closing/deadline-time odds may be used for historical backtests only where verified archived lineage exists. This audit is distribution-focused and does not fabricate missing odds.
