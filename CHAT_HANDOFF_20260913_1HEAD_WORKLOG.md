# 1HEAD WORKLOG 2026-09-13

## Work unit 1 - written before execution
Current position: v322 is complete. Frozen regression target is v308 -> v317 -> v318 -> v320, with 345 selected races / 290 head wins / 139 exact3.

Now doing:
1. Inspect the latest repository for the exact v308, v317, v318, v320, v321, v322 implementation files and the current result-blind input path.
2. Identify the minimum reusable functions for a production adapter without changing frozen model logic.
3. Confirm forbidden inputs are excluded: meet_* and same-race result/payout/future data.
4. Before implementation, append the exact files/functions to change and the success criteria here.

If interrupted: resume from the first unfinished item above. Do not retune on July/August and do not read September outcomes.

## Work unit 5B - v325 initial result + fail-closed correction — written BEFORE fix
Initial v325 implementation commits:
- `c971d14dac4ebd1bea5f0b73535bd74b7cfe242b` — `run_v325_1head_exhibition_postfilter.py`
- `d395c77dfdf2b83335b006f85046ec13f507da94` — workflow

Actions run **34764216379** completed successfully, job `103742199763`, artifact `10319987816`.
Reconciliation and first result from logs:
- v320 unchanged: 345R / 139 exact3 / 290 head wins.
- v108 join: 336 rows; tkz=292, stt=292, orig=295, all three actual-source flags complete=292.
- baseline exact3 139/345 = 40.29%.
- frozen May-selected first candidate: `one_turn >= 0.5`.
- discovery Feb-Apr: 43/87 = 49.43% exact3.
- May validation: 30/60 = 50.00% exact3, head 55/60 = 91.67%.
- Jun forward PASS: 15/42 = 35.71% exact3; SKIP: 17/50 = 34.00%; forward support = FALSE.

Important audit finding after run:
`analyze_v108_1head_feasibility.py` deliberately fills missing same-race exhibition/original-exhibition ranks with neutral 0.5 values before writing features. Therefore a rule such as `one_turn >= 0.5` can accidentally PASS a race with `has_orig=0`. This violates the intended live fail-closed rule even though the historical feature remains causal.

Now doing BEFORE any rerun:
1. Patch v325 so every candidate is evaluated only on rows where the actual source required by that feature exists. For original-exhibition features (`one_lap`, `one_turn`, `one_straight`, `one_orig_avg`, `turn_margin23`, `straight_margin23`) require `has_orig==1`; for official exhibition time (`one_ex`, `ex_margin23`) require `has_tkz==1`; for exhibition ST (`one_st`) require `has_stt==1`. Logistic multi-feature candidate must require all `has_tkz==has_stt==has_orig==1`.
2. Treat rows missing the required source as automatic SKIP, never as neutral 0.5 PASS.
3. Re-run the same chronological Feb-Apr discovery / May freeze / Jun forward check without changing frozen v320 or reading Jul/Aug.
4. Only if Jun forward support survives this corrected fail-closed audit may Jul/Aug reference be evaluated once.

Success criteria: missing-source rows cannot PASS; 345/139/290 frozen identity still reconciles; actual-source coverage is explicit; Jun forward metrics are recomputed; no Jul/Aug or September outcome is read during this correction.

If interrupted: patch `run_v325_1head_exhibition_postfilter.py` exactly as above, then push and inspect the new Actions run. Do not reuse run 34764216379 as a production-valid filter result.
