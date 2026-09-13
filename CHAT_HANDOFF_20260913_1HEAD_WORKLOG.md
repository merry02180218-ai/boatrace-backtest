# 1HEAD WORKLOG 2026-09-13

## Work unit 1 - written before execution
Current position: v322 is complete. Frozen regression target is v308 -> v317 -> v318 -> v320, with 345 selected races / 290 head wins / 139 exact3.

Now doing:
1. Inspect the latest repository for the exact v308, v317, v318, v320, v321, v322 implementation files and the current result-blind input path.
2. Identify the minimum reusable functions for a production adapter without changing frozen model logic.
3. Confirm forbidden inputs are excluded: meet_* and same-race result/payout/future data.
4. Before implementation, append the exact files/functions to change and the success criteria here.

If interrupted: resume from the first unfinished item above. Do not retune on July/August and do not read September outcomes.

## Work unit 5B - v325 initial result + fail-closed correction — COMPLETED
Initial v325 implementation commits:
- `c971d14dac4ebd1bea5f0b73535bd74b7cfe242b` — `run_v325_1head_exhibition_postfilter.py`
- `d395c77dfdf2b83335b006f85046ec13f507da94` — workflow

Initial Actions run **34764216379** completed successfully, job `103742199763`, artifact `10319987816`.
Reconciliation and first result from logs:
- v320 unchanged: 345R / 139 exact3 / 290 head wins.
- v108 join: 336 rows; tkz=292, stt=292, orig=295, all three actual-source flags complete=292.
- baseline exact3 139/345 = 40.29%.
- initial May-selected candidate: `one_turn >= 0.5`.
- discovery Feb-Apr: 43/87 = 49.43% exact3.
- May validation: 30/60 = 50.00% exact3, head 55/60 = 91.67%.
- Jun forward PASS: 15/42 = 35.71% exact3; SKIP: 17/50 = 34.00%; forward support = FALSE.

Audit finding: v108 fills missing exhibition ranks with neutral 0.5, so v325 was patched to require the actual source flag for every tested feature and to fail closed on missing sources.

Correction commits/runs:
- worklog-before-fix commit `3c4a21e184b1ec0e9e4220a412ed600a4130b810`.
- fail-closed code commit `68bf07bbd783c7082d6e21dd1917c01e1da3800e`.
- corrected Actions run **34764329333**: completed / success.
- job `103742497228`.
- artifact `v325-1head-exhibition-postfilter`, ID `10319838860`.

Corrected v325 result:
- v320 reconcile: 345R / 139 exact3 / 290 head wins.
- joined v108 rows 336; tkz=292; stt=292; orig=295; all source complete=292.
- source-complete by chronological split: Feb-Apr 97, May 104, Jun 91.
- frozen fail-closed candidate selected on May: `one_turn >= 0.800000`.
- discovery Feb-Apr: 13/33 = 39.39% exact3, head 27/33 = 81.82%.
- May validation: 17/35 = 48.57% exact3, head 33/35 = 94.29%.
- Jun forward PASS: 8/25 = 32.00% exact3, head 21/25 = 84.00%.
- Jun skipped: 24/67 = 35.82% exact3.
- Jun baseline: 32/92 = 34.78% exact3.
- `FORWARD_SUPPORTED=False`.
Conclusion: boat1-only exhibition/original-exhibition gate does not lift the frozen 3-ticket exact3 rate to >=50%. Jul/Aug was correctly NOT read/evaluated.

## Work unit 5C / v326 — ticket-aware post-exhibition features — written BEFORE execution
Reason: the frozen 3 tickets depend on the 2nd/3rd-place boats. A boat1-only exhibition gate cannot distinguish whether the specific opponents covered by v320 are actually showing superior same-race exhibition performance. Next research must evaluate the exact boats appearing in the frozen 3 tickets versus uncovered opponents.

Do now:
1. Inspect existing historical exhibition parsers/rank builders (`corrected_direct`, tkz/stt/original_exhibition snapshot formats, and current live v283 builder) and identify the safest reusable way to reconstruct per-boat exhibition ranks for each frozen v320 race without using results/payouts.
2. Build a new v326 dataset for the 345 frozen v320 races only. Parse each race's three tickets and derive:
   - unique covered SECOND boats;
   - unique covered THIRD boats;
   - covered opponent union;
   - uncovered opponents among boats 2..6.
3. For each boat 1..6 attach result-blind same-race rank-normalized exhibition features from actual source snapshots only: exhibition time, exhibition ST, original one-lap, turn, straight, original average, and exhibition course/entry where safely available.
4. Derive predeclared ticket-aware relative features, for example:
   - best/mean covered SECOND exhibition rank and margin versus best uncovered opponent;
   - best/mean covered THIRD turn/straight/original rank and margin versus uncovered opponents;
   - weakest covered ticket leg rank;
   - boat1 + covered-opponent joint quality / balance;
   - whether any uncovered opponent dominates all covered opponents in straight/turn metrics.
   Do not use result labels to invent feature definitions after seeing performance.
5. Missing required live source must fail closed. Do not let v108 neutral 0.5 defaults stand in for absent actual same-race data.
6. Chronological research remains Feb-Apr discovery -> May validation/freeze -> Jun untouched forward check. Jul/Aug remains unread until one candidate is frozen and Jun-forward-supported.
7. Compare a compact interpretable rule set and a small regularized logistic model. Optimize for retained coverage subject to a target of >=50% exact3, but do not claim success unless Jun forward evidence supports it.
8. If safe per-boat reconstruction cannot be made from committed snapshots with the same semantics available live, stop and document the missing source rather than using post-race/backfilled data.

Success criteria:
- frozen v320 remains exactly 345R/139 exact3/290 head wins;
- per-boat features are built only from pre-settlement same-race exhibition snapshots;
- ticket identities are unchanged;
- actual-source coverage and missingness explicit;
- Jun forward PASS exact3/head/coverage plus skipped metrics reported;
- no Jul/Aug evaluation unless candidate is forward-supported;
- no September outcome/payout read.

If interrupted: resume Work Unit 5C by auditing `corrected_direct` and the exact snapshot schemas, then create the v326 per-boat/ticket-aware dataset. Do not alter v308/v317/v318/v320/v323.
