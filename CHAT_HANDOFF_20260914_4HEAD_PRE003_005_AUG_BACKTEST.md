# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **COMMON-FROZEN-SCALE COMPARISON COMPLETE**

## Frozen production
Production remains unchanged. S PRE >= 0.28; A PRE >= 0.18; frozen downstream rules remain in force. July/August 2026 remain NON-PRISTINE; September remains outcome-blind for tuning.

## Previously completed checks
### Monthly walk-forward 2026-02..06
Inclusive `0.03 <= PRE <= 0.05`:
- 3,818R
- 143 wins
- 3.75% head rate
- POST >= 0.18: 0R
- POST >= 0.25: 0R
- Run ID `34771874589`
- artifact ID `10321614933`

### August frozen-at-2026-06-30 shadow
- 171R
- 34 wins
- 19.88%
- POST >= 0.18: 0R
- POST >= 0.25: 0R
- August is NON-PRISTINE and descriptive only.

## 2026-09-14 common-scale work-start record
This plan was written before implementation.

Methodology:
- A 2026-06-30 model cannot honestly be used as a causal Feb-Jun backtest because it contains future labels relative to those races.
- Therefore one PRE model and one POST model were frozen at **2026-01-31** and reused unchanged for every target race from **2026-02-01 through 2026-08-31**.
- Target months are all later than the fit cutoff, so the numerical PRE/POST scale is common across the entire comparison.
- July/August remain NON-PRISTINE and cannot be used for production threshold/model selection.

## Implementation
- `analyze_4head_common_frozen_20260131.py`
- `.github/workflows/analyze-4head-common-frozen-20260131.yml`
- analysis commit: `9c77f7f9fcd207f48ca79d5db738635ff957f686`
- workflow commit: `11d3e687a453d57c2fd4740621804a583e5f3d6e`

Frozen fit:
- fit cutoff: `2026-01-31`
- train rows: `9,814`
- train 4-head rate: `9.9246%`
- exactly one PRE model + one POST model; no target-month refit.
- production modified: false.

## CI
- workflow: `analyze-4head-common-frozen-20260131`
- Run ID: `34772249054`
- Job ID: `103763843482`
- head SHA: `11d3e687a453d57c2fd4740621804a583e5f3d6e`
- syntax: PASS
- common-frozen backtest: PASS
- guard audit: PASS
- artifact upload: PASS
- artifact ID: `10322571216`
- artifact: `head4-common-frozen-20260131`

## Common frozen-scale results
Inclusive `0.03 <= PRE <= 0.05` using the **same Jan-31 frozen PRE/POST models** in every month:

|month|all R|band R|4-head wins|head rate|POST >= 0.18|POST >= 0.25|PRE mean|POST mean|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|2026-02|4,100|693|33|4.76%|0|0|0.04080|0.04051|
|2026-03|4,607|784|26|3.32%|2|0|0.04025|0.04123|
|2026-04|4,244|769|24|3.12%|2|0|0.04059|0.04099|
|2026-05|4,832|803|25|3.11%|0|0|0.04050|0.04139|
|2026-06|4,488|715|30|4.20%|0|0|0.04041|0.04142|
|2026-07|4,920|574|40|6.97%|0|0|0.04032|0.04155|
|2026-08|4,920|233|54|23.18%|0|0|0.03840|0.04207|

Feb-Jun aggregate on the common scale:
- band rows: `3,764R`
- wins: `138`
- head rate: `3.67%`

July descriptive NON-PRISTINE:
- 574R / 40 wins = `6.97%`

August descriptive NON-PRISTINE:
- 233R / 54 wins = `23.18%`

## Main finding
The August anomaly **does not disappear when score-scale mismatch is removed**.

Using one identical model frozen on 2026-01-31:
- Feb-Jun common-scale baseline = **3.67%**
- July = **6.97%**
- August = **23.18%**

So August is still dramatically different even under a truly common frozen score scale. The previous 19.88% was therefore not explained merely by comparing monthly-walk-forward scores with a 6/30-frozen score.

However:
- August is NON-PRISTINE and has already been inspected repeatedly.
- This result must **not** be converted into a rescue threshold or production promotion based on August outcomes.
- The next research question is why the distribution/regime shifted, but any candidate rule must be defined without selecting it to fit the 54 August winners, then frozen before unseen future validation.

## Downstream POST observation
Despite the August 23.18% head rate in the low-PRE band:
- August POST >= 0.18 = `0/233`
- August POST >= 0.25 = `0/233`
- July also has `0/574` at both gates.
- Across Feb-Jun, only 4 rows reached POST >= 0.18 and none reached POST >= 0.25.

Therefore frozen production POST logic still overwhelmingly rejects this low-PRE cohort. Production remains unchanged.

## Odds / ROI
User explicitly permits closing/deadline-time odds for historical backtests.

This common-scale run did not compute ROI because no verified archived closing/deadline-time 3T odds lineage for 2026-02..08 was available in the confirmed repository archive used by this work. No odds were fabricated or substituted.

## Restart point
Common-scale comparison is complete.

Safest next research directions:
1. Investigate a **calendar/regime/data-distribution shift** between June/July/August using outcome-independent feature distributions first (PRE inputs, field composition, venue mix, racer/motor/history distributions), rather than selecting features by which explain the August winners.
2. Compare the entire frozen PRE calibration curve / score bins by month, not only 0.03..0.05, to determine whether August represents broad model calibration drift or a localized low-score inversion.
3. Freeze any hypothesis derived from domain/model architecture before checking future unseen September-or-later outcomes; do not use September outcomes for selection before predictions are frozen.
4. If historical closing/deadline odds are sourced and archived with clear lineage, add the user-approved ROI settlement as a separate historical audit.

Before any next implementation, write the exact work plan here first. After completion, append exact results, commits, Run IDs, limitations and restart point.
