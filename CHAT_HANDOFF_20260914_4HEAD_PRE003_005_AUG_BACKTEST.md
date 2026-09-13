# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **ROLLING FIT-CUTOFF DIAGNOSTIC COMPLETE**

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

## Completed outcome-independent regime-shift audit
- Run ID `34772988796`, Job ID `103765871313`, artifact ID `10322318642`.
- Under the Jan-31 frozen model, July PRE <0.01 = 28.48%; August = 68.90%, versus essentially zero in Feb-Jun.
- Largest August PRE-band shifts versus Feb-Jun: inner12_resistance SMD +4.143, wall3_weak -2.431, racer4 +2.100, past_win4 +2.046, hist_st_edge_4v3 +1.017.
- This proves broad outcome-independent covariate/population drift, not its cause.

## 2026-09-14 rolling fit-cutoff diagnostic work-start record
Written BEFORE implementation at the user's request to test whether not learning July/August is driving the observed score-distribution shift.

Exact plan:
1. Keep production completely unchanged.
2. Reuse the v250 PRE/POST feature recipe and causal day-by-day state generation.
3. Fit separate diagnostic model pairs with progressively later fit cutoffs: 2026-01-31, 02-28, 03-31, 04-30, 05-31, 06-30, and a July-trained diagnostic ending 07-31.
4. For each cutoff, score only dates strictly AFTER its fit cutoff; never score a month with future labels in that model.
5. Compare the same fixed PRE bins, especially PRE <0.01, PRE 0.03..0.05, PRE >=0.28, and POST distribution, so we can see whether later causal training restores the July/August score distribution.
6. Primary causal question: does the 2026-06-30 model still show the August collapse? If yes, lack of Feb-Jun updating is not sufficient to explain it. If no, model staleness is a plausible contributor.
7. July-trained -> August scoring is DIAGNOSTIC/NON-PRISTINE only because July has already been inspected. It cannot select production rules, thresholds, features, or rescue logic.
8. Do not use target-month wins/losses to choose or rank explanations in this diagnostic. Distribution/feature behavior first.
9. Historical result labels may be used only to fit models up through each stated cutoff. No future-month result leakage into that model.
10. Run CI and archive the diagnostic outputs.
11. After completion, update this handoff with implementation commits, CI Run/Job/Artifact IDs, exact distribution findings, limitations, production status, and restart point.

## Rolling fit-cutoff implementation
- analysis: `analyze_4head_rolling_fit_cutoffs_20260914.py`
- workflow: `.github/workflows/analyze-4head-rolling-fit-cutoffs.yml`
- analysis commit: `419314b1344c4c21a87b3a8e6601c95f6585235d`
- workflow commit: `c75744236b446d62c7cda5b908f35fdd43f0cac5`
- later no-op/comment trigger commit used only to force a second verification run: `cae7f2c4963f7c3c7a1f841cb00588bcd5953687`

Method:
- causal feature replay from 2025-12-01 through 2026-08-31
- same v250 PRE/POST feature recipe
- separate PRE/POST model pairs ending 2026-01-31, 02-28, 03-31, 04-30, 05-31, 06-30, 07-31
- each model scores only dates strictly after its own cutoff
- comparison uses fixed PRE-bin / PRE-POST distribution summaries
- August outcomes are NOT used to rank the distribution explanation
- production is not modified.

## CI — completed primary run
- workflow: `analyze-4head-rolling-fit-cutoffs`
- Run ID `34773603328`
- Job ID `103767543705`
- head SHA `c75744236b446d62c7cda5b908f35fdd43f0cac5`
- conclusion: SUCCESS
- syntax PASS
- analysis PASS
- guard audit PASS
- artifact upload PASS
- artifact name `head4-rolling-fit-cutoffs`
- artifact ID `10322079757`
- artifact zip SHA256 `075c9307713fc291c6646054c850c6f13871bad6f2767eaedd820efedd27a1ab`

A second verification run was explicitly generated after an earlier run-discovery mistake:
- forced trigger commit `cae7f2c4963f7c3c7a1f841cb00588bcd5953687`
- verification Run ID `34774400549`
- status at creation/check: queued
- this duplicate run is not required for the findings below because primary Run `34773603328` already completed successfully.

## Exact August distribution by fit cutoff
All rows below score August 2026's 4,920 races. July/August are NON-PRISTINE.

| fit cutoff | train R | Aug R | PRE<.01 | PRE .03-.05 | PRE>=.28 | PRE mean | POST mean | POST>=.18 | POST>=.25 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2026-01-31|9,814|4,920|68.90%|4.74%|0.18%|0.01297|0.01417|26|13|
|2026-02-28|13,914|4,920|74.80%|3.78%|0.18%|0.01118|0.01193|24|11|
|2026-03-31|18,521|4,920|72.20%|4.04%|0.24%|0.01220|0.01299|26|13|
|2026-04-30|22,765|4,920|73.11%|3.98%|0.24%|0.01201|0.01289|26|13|
|2026-05-31|27,597|4,920|76.16%|3.58%|0.18%|0.01063|0.01133|22|11|
|2026-06-30|32,085|4,920|77.83%|3.48%|0.16%|0.00972|0.01039|16|9|
|2026-07-31|37,005|4,920|7.40%|16.91%|5.28%|0.08487|0.08489|591|321|

## Main finding
The hypothesis "August collapses because the model was not updated through Feb-Jun" is NOT supported. The 2026-06-30 model includes all Feb-Jun labels and still shows an even stronger August low-score collapse:
- PRE <0.01 = 77.83%
- PRE 0.03..0.05 = 3.48%
- PRE >=0.28 = 0.16%
- mean PRE = 0.00972

Therefore lack of Feb-Jun updating is not sufficient to explain the August shift.

However, the diagnostic model trained through 2026-07-31 dramatically recenters the August score scale:
- PRE <0.01 falls from 77.83% (Jun-30 fit) to 7.40%
- PRE 0.03..0.05 rises from 3.48% to 16.91%
- PRE >=0.28 rises from 0.16% to 5.28%
- mean PRE rises from 0.00972 to 0.08487

This is strong diagnostic evidence that **July contains structural information needed to adapt to the August feature population**. It does NOT yet tell us whether that structure is a genuine racing-regime change or a July-boundary data/feature-pipeline change.

## Safety / interpretation
- July/August remain NON-PRISTINE.
- The 2026-07-31 -> August comparison is DIAGNOSTIC ONLY. It must not be used to select production thresholds, rescue rules, features, model family, or retraining policy.
- No August win/loss outcome was used to rank the distribution explanation.
- The POST>=0.18 / .25 counts above are over all 4,920 August races, so they do not conflict with the earlier 0/233 result inside the Jan-31-model PRE 0.03..0.05 band.
- Production remains unchanged.

## Limitations
This test establishes that adding July training data changes the August score scale dramatically, but it does not distinguish:
1. genuine racing/population regime change,
2. source-data/schema/coverage change,
3. feature default/fallback/missingness change,
4. causal history-state/reset/coverage boundary around July.

No ROI was computed in this distribution diagnostic.

## Restart point
Next safest step is an outcome-blind July-boundary feature/data lineage audit:
1. Trace source primitives, missingness, default/fallback behavior, and history coverage behind `inner12_resistance`, `wall3_weak`, `racer4`, `past_win4`, `hist_st_edge_4v3`.
2. Compare Feb-Jun vs July vs August primitive availability and month-level distributions.
3. Inspect for any code/data-source/schema/date-gated boundary around 2026-07-01.
4. Specifically determine why a model fit through July recenters August while every model ending June or earlier collapses.
5. Optionally compare 2026-06-30 vs 2026-07-31 fitted coefficients/feature importance without using August outcomes, to identify which learned relationships changed most; treat this as diagnostic only.
6. If a pipeline bug/boundary is found, construct a corrected causal historical replay and compare score distributions first. Do not immediately change production.
7. If no pipeline issue is found, treat July/August as genuine covariate drift and define only a fixed future-facing hypothesis for unseen validation.
8. September outcomes remain unavailable for tuning/model selection until predictions are frozen.

Before next implementation, append the exact work plan here. After completion append commits, CI IDs, findings, limitations, and next restart point.
