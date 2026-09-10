# HEAD4_V273 A-RANK FROZEN — 2026-09-10

## Purpose
Freeze a separate A-rank expansion layer for the existing frozen HEAD4_V268 S-rank before any September outcome-based tuning.

The objective is to increase race count without modifying or contaminating the v268 S-rank rule.

July/August 2026 remain NON-PRISTINE and are excluded from this A-rank rule selection and robustness audit.
September outcomes were not used to select or tune this rule.

## Priority / separation
1. Evaluate HEAD4_V268 S-rank first.
2. If a race qualifies for S, classify it S only.
3. A-rank applies only to races that do NOT qualify for S.
4. Never stake both S and A on the same race.
5. Report S, A, and S+A portfolio results separately.

## Frozen S-rank reference (unchanged)
HEAD4_V268 remains exactly:

- PRE >= 0.28
- POST >= 0.25
- ENV_ENTRY >= 0.224790

No v273 setting changes v268.

## Frozen A-rank development rule
A race is an A-rank candidate only when it is outside v268 S-rank and:

- PRE >= 0.18
- POST >= 0.18
- A_SCORE >= 0.28 on the v271/v272 monthly walk-forward OOF score scale

### Frozen A_SCORE model family
Logistic model using the v264 LR pipeline (median imputation, standard scaling, LogisticRegression C=0.18) and these pre-result features:

1. `v91_ex`
2. `score_CORR20_v91`
3. `score_wind_v83`
4. `score_RAW20_v91`
5. `score_BASE_v91`
6. `preview_comp`
7. `rel_pl_all_win_4v1`
8. `rel_pl_all_p2_4v1`
9. `rel_pl_recent_p2_4v1`
10. `opp_grade_b1_v93`
11. `opp_score_b1_v93`
12. `opp_national_b1_v93`
13. `b1_pl_all_win`
14. `b1_pl_all_p2`
15. `b1_pl_frame_win`
16. `rel_pl_recent_p2_4v3`
17. `b4_pl_recent_p2`

Features are available only if they satisfy the same historical coverage/safety rules used in v271. Result, payout, ticket, actual-result, kimarite, and post-result fields are prohibited.

## Frozen ticket rule for A-rank
Same economics as v268:

- Head: boat 4 fixed.
- Opponent pair order: existing prior-only v96-lineage 4-x-y pair ranking.
- Candidate N: 2..20.
- Choose N whose combined/composite odds is closest to 10.5.
- Stake: exactly 10,000 JPY per betting race.
- Allocation: inverse-odds Dutch with 100-JPY Hamilton rounding.
- Miss: payout 0 JPY / profit -10,000 JPY.

## Development evidence
v271/v272 retrospective development audit, Apr-Jun 2026, Jul/Aug excluded:

### Frozen A cut 0.28
- S races: 53
- A-added races: 47
- S+A total races: 100
- A boat-4 head rate: 44.68%
- A trifecta hit rate: 17.02%
- A development ROI: 150.16%
- S+A boat-4 head rate: 40.00%
- S+A trifecta hit rate: 16.00%
- S+A development ROI: 131.26%
- S+A monthly minimum ROI: 104.00%

S+A monthly split:
- 2026-04: 31R, ROI 104.00%, head 35.48%, hit 9.68%
- 2026-05: 34R, ROI 170.66%, head 44.12%, hit 23.53%
- 2026-06: 35R, ROI 117.13%, head 40.00%, hit 14.29%

### Threshold-neighborhood robustness
For A_SCORE 0.27-0.30:
- combined race count: 91-101R
- combined development ROI: 123.53%-131.26%
- combined monthly floor: 104.00%-115.15%

### Rotating leave-one-month-out robustness
Threshold chosen on the other two months, then applied to held-out month:
- holdout 2026-04: combined ROI 104.00%
- holdout 2026-05: combined ROI 170.66%
- holdout 2026-06: combined ROI 110.80%

All three held-out combined portfolio ROIs were >=100%.

Important caveat: A alone was not profitable in every held-out month (2026-04 A-only ROI 67.37%). Therefore A-rank is frozen as a portfolio expansion layer paired with S, not as proof of an independently profitable standalone model.

## Evidence status
All figures above are retrospective development/model-selection evidence.
Archived historical odds are a proxy and are not equivalent to immutable contemporaneous pre-deadline LIVE odds snapshots.
This file does not claim formal OOS profitability.

## LIVE score-scale requirement before prospective use
The frozen A_SCORE threshold `0.28` belongs to the monthly walk-forward OOF probability scale.
A final LIVE model trained once on a fixed historical window can have a different probability scale.

Therefore DO NOT blindly apply raw 0.28 to a differently fitted final LIVE model.
Before any prospective scoring/result inspection:

1. Fit the final A_SCORE model only with allowed pre-result historical data through 2026-06-30.
2. Exclude Jul/Aug from tuning/calibration.
3. Build an outcome-blind distribution/quantile mapping from the final-model score scale to the frozen v271/v272 OOF selection semantics.
4. Persist the fitted coefficients, imputer/scaler parameters, feature order, and mapped LIVE threshold.
5. Freeze that LIVE artifact before using September outcomes for evaluation.

This mapping may change the numerical LIVE threshold but must not change the frozen selection semantics using outcomes.

## Prospective discipline
- A-rank freeze date: 2026-09-10.
- Do not tune using July/August.
- Do not tune using September outcomes.
- Formal prospective/OOS evaluation begins only after the LIVE model/score mapping is frozen and from races occurring after that operational freeze.
- Use immutable pre-deadline odds snapshots for formal OOS settlement.
- Report every eligible race including misses.
- Required metrics by S, A, and S+A: bets, head wins/head rate, trifecta hits/rate, stake, return, profit, ROI, max drawdown, longest losing streak, average/actual composite odds.

## Status
HEAD4_V273 is a frozen A-rank prospective candidate layered under frozen v268 S-rank.
It is not yet a production model until the LIVE score-scale mapping and operational artifact are frozen.