# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **OUTCOME-INDEPENDENT REGIME-SHIFT AUDIT COMPLETE**

## Frozen production
Production remains unchanged. S PRE >= 0.28; A PRE >= 0.18; frozen downstream rules remain in force. July/August 2026 remain NON-PRISTINE; September remains outcome-blind for tuning.

## Completed common frozen-scale result
One PRE/POST model frozen at 2026-01-31 and reused unchanged for 2026-02..08, inclusive PRE 0.03..0.05:
- Feb-Jun: 3,764R / 138 wins = 3.67%
- July: 574R / 40 wins = 6.97% (NON-PRISTINE)
- August: 233R / 54 wins = 23.18% (NON-PRISTINE)
- August POST >= 0.18: 0/233; POST >= 0.25: 0/233
- Run ID `34772249054`, Job ID `103763843482`, artifact `10322571216`
- production unchanged.

## 2026-09-14 regime-shift work-start record
Written before implementation. Goal was to investigate August using feature/population distributions only, without target-period win/loss outcomes in drift ranking.

## Implementation
- `analyze_4head_regime_drift_20260914.py`
- `.github/workflows/analyze-4head-regime-drift.yml`
- analysis commit `9a85ee2cc4539e0979ab7c7387f4c304c1badf16`
- workflow commit `d9b3b8aa32e1c4f319e3ee4d61755bb753b9eb10`
- CI trigger/final script commit `9c22108745fe26bba91248acdc3e48e71d78f4b4`

Methodology:
- exact Jan-31 frozen PRE/POST model recipe
- Feb-Jun PRE 0.03..0.05 is fixed baseline
- July/August compared by feature distributions only
- target-period results are not loaded for drift ranking
- metrics: standardized mean difference (SMD) and KS statistic
- full PRE-bin population shares also reported
- no production modification.

## CI
- workflow `head4-regime-drift`
- Run ID `34772988796`
- Job ID `103765871313`
- head SHA `9c22108745fe26bba91248acdc3e48e71d78f4b4`
- syntax PASS
- regime audit PASS
- artifact upload PASS
- artifact ID `10322318642`
- artifact `head4-regime-drift`
- artifact zip SHA256 `6d3860609f7018a7cc80365736017a92c55aaac04bd7a4cbfa8604d4723b97e7`

## Main outcome-independent August drift findings
Largest August shifts versus Feb-Jun baseline inside PRE 0.03..0.05, ranked by absolute SMD:

|feature|SMD|KS|
|---|---:|---:|
|inner12_resistance|+4.143|0.973|
|wall3_weak|-2.431|0.931|
|racer4|+2.100|0.697|
|past_win4|+2.046|0.876|
|hist_st_edge_4v3|+1.017|0.536|
|legacy_score4|+0.958|0.431|
|motor4_2ren|+0.421|0.228|
|turnfoot4_prior|+0.419|0.185|

These are very large population shifts. Because ranking did not use August wins/losses, this establishes that August's PRE 0.03..0.05 cohort is compositionally very different from Feb-Jun even before examining outcome association.

## Broad PRE population shift
The change is not limited to the 0.03..0.05 band. Under the same Jan-31 frozen model:

- Feb-Jun PRE <0.01 was essentially 0% of races (0-3 races/month).
- July PRE <0.01: `1,401 / 4,920 = 28.48%`.
- August PRE <0.01: `3,390 / 4,920 = 68.90%`.
- August PRE 0.03..0.05: `233 / 4,920 = 4.74%`, versus roughly 15.9-18.1% in Feb-Jun.
- August PRE >=0.28: only `9 / 4,920 = 0.18%`, versus roughly 2.1-2.5% in Feb-Jun.

Therefore August is a **broad frozen-model population/feature regime shift**, not merely a localized low-score-bin oddity. July already shows the shift beginning, and August becomes extreme.

## Interpretation / safety
This audit does NOT prove that any one shifted feature causes the 23.18% August head rate. It only establishes a strong outcome-independent covariate/population shift.

Do not create a rescue rule from August values, do not retune PRE/POST thresholds from July/August, and do not promote production based on these NON-PRISTINE months.

Production remains unchanged.

## Historical ROI
User permits closing/deadline-time odds for historical backtests where verified archived lineage exists. No ROI was calculated in this distribution audit and no odds were fabricated.

## Restart point
Next safest research step:
1. Audit whether the dramatic July/August drift is a **real racing-population change or a feature/data-pipeline regime change**. In particular inspect the raw/source lineage and month-by-month distributions behind `inner12_resistance`, `wall3_weak`, `racer4`, `past_win4`, and `hist_st_edge_4v3`, because SMD magnitudes +4.14 / -2.43 / +2.10 are large enough to warrant a data-generation audit before interpreting them as racing behavior.
2. Compare raw primitive availability/missingness/default/fallback rates Feb-Jun vs July/August, and inspect whether a code/data-source boundary around July 1 changed feature semantics.
3. This next audit should remain outcome-blind. Only after confirming feature lineage should any fixed domain hypothesis be defined for future unseen validation.
4. September outcomes remain unavailable for tuning/model selection until predictions are frozen.

Before next implementation, append the exact work plan here. After completion append commits, CI IDs, findings, limitations, and next restart point.
