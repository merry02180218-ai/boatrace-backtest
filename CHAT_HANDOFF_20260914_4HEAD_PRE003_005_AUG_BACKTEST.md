# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **ROLLING FIT-CUTOFF DIAGNOSTIC IN PROGRESS**

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

## Existing safety / interpretation
July/August remain NON-PRISTINE. No rescue rule or threshold may be selected from their outcomes. September outcomes remain unavailable for tuning/model selection until predictions are frozen. Historical closing/deadline-time odds are allowed for backtests where verified lineage exists; no odds may be fabricated.
