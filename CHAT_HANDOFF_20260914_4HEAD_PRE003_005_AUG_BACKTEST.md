# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **OLDER-PERIOD BACKTEST COMPLETE**

## Frozen production
Production remains unchanged. S PRE >= 0.28; A PRE >= 0.18; frozen downstream rules remain in force. August 2026 remains NON-PRISTINE.

## Work-start record
Before implementation, this file recorded the user request to test the same inclusive `0.03 <= PRE <= 0.05` phenomenon farther back in history and the explicit permission to use archived closing/deadline-time odds for historical ROI settlement.

## Implementation
- `analyze_4head_old_pre003_005.py`
- `.github/workflows/analyze-4head-old-pre003-005.yml`
- analysis commit: `58c0f0b81a3e60ed5bfd48caf9c5d6a5e72cf0f6`
- workflow commit: `adad3b8fb4351086c0c20c6d18dbca22fe1b18b3`

Contract:
- v250 feature recipe.
- monthly walk-forward: each test month is fit only on previous months.
- feature state is built causally day by day.
- target race result is joined only after that race's PRE/POST features are frozen.
- period tested: `2026-02..2026-06`.
- band: inclusive `0.03 <= PRE <= 0.05`.

## CI
- workflow: `analyze-4head-old-pre003-005`
- Run ID: `34771874589`
- Job ID: `103762823871`
- head SHA: `adad3b8fb4351086c0c20c6d18dbca22fe1b18b3`
- syntax: PASS
- backtest: PASS
- guard audit: PASS
- artifact upload: PASS
- artifact ID: `10321614933`
- artifact: `head4-old-pre003-005`

## Results
|month|R|4-head wins|head rate|POST >= 0.18|POST >= 0.25|
|---|---:|---:|---:|---:|---:|
|2026-02|693|33|4.76%|0|0|
|2026-03|758|22|2.90%|0|0|
|2026-04|783|23|2.94%|0|0|
|2026-05|824|31|3.76%|0|0|
|2026-06|760|34|4.47%|0|0|
|TOTAL|3,818|143|3.75%|0|0|

## Comparison with August shadow
Completed August frozen-at-6/30 shadow had:
- 171R
- 34 wins
- 19.88% head rate
- POST >= 0.18: 0R
- POST >= 0.25: 0R

The older monthly-walk-forward evidence is very different: the same numerical PRE band produced only 2.90%..4.76% monthly head rates and 3.75% overall. Therefore the August 19.88% phenomenon does **not** reproduce in this older 2026-02..06 walk-forward check.

Important scale caveat:
- Older test uses monthly walk-forward score scales.
- August shadow used a 2026-06-30 frozen model score scale.
- Therefore identical numeric PRE `0.03..0.05` is not guaranteed to represent an identical percentile/risk cohort across the two contracts. Do not interpret this comparison as a threshold promotion/rejection by itself.

## Odds / ROI
User explicitly permits closing/deadline-time odds for historical backtests.

Verified repository path `data/official_closing_odds3t/2026` currently contains only `09`; no archived `2026/02..06` files were present there. Therefore ROI, Dutch settlement, VARN N and drawdown were **not fabricated** for this run.

If closing/deadline-time odds for these months are later sourced and archived with clear lineage, historical ROI may be computed under the user's permission.

## Interpretation
- Older data does not support the idea that PRE 0.03..0.05 is generally a high-win 4-head band.
- In 3,818 older races it won 143 times = 3.75%.
- All five months also had zero races reaching POST 0.18, so the frozen downstream POST logic rejects the band consistently.
- August's 19.88% should therefore be treated as an unusual NON-PRISTINE period/scale effect until a genuinely future unseen frozen-score cohort says otherwise.
- Production policy stays unchanged.

## Restart point
This older-period check is complete.

Next safe research options:
1. Compare **PRE percentile bands** rather than absolute 0.03..0.05 across historical monthly models, which removes much of the score-scale mismatch.
2. Re-score older months with one common frozen model where causally valid, then compare the exact same frozen score scale to August.
3. Acquire/archive historical closing/deadline-time odds for older months and add the user-approved ROI settlement.

Before any next implementation, append the planned work here first; after completion, append exact results/commits/Run IDs/restart point.
