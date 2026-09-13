# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## READ THIS FIRST — authoritative current 1-head state
Latest GitHub wins over old chat memory and stale handoff text.

Mandatory pattern: **handoff update -> work -> result append -> next work handoff update**.
Before every work unit/code change/restart record: current position, exact next work, success criteria, failure fallback. After every work unit record: actual work, commit SHA(s), Actions Run ID/status, metrics/results, exact next resume point.

---

# 1. Frozen production stack — DO NOT ALTER
- HEAD v308
- SECOND v317 `OUTER_L2_1`
- THIRD v318 `DROPSTART_T0.1`
- 3-ticket policy v320 `HYBRID alpha=.70`
- exactly 3 trifecta tickets per selected race
- composite odds = `1 / (1/o1 + 1/o2 + 1/o3)`

Frozen regression: **345 selected / 290 boat1 wins / 139 exact3**.
v308: q=.980, opponent mass >=.375, head cutoff 0.8073405637.

Guardrails:
- Jul/Aug 2026 = NON-PRISTINE/reference-only; never tune/promote on them.
- September outcomes = UNREAD.
- no same/later-race result, payout, future/backfill contamination.
- month M trains strictly on `<M`.
- same-race exhibition is post-PRE only.
- missing current exhibition inputs fail closed for any feature that requires them.
- do not modify v308/v317/v318/v320/v323.

---

# 2. Important completed work

v321 Jul/Aug reference: Run 34750719803, 55R / 45 head / 21 exact3.
v322 composite odds: Run 34753932483 success; no BUY cutoff promoted.
v323 production adapter: Run 34757079269 success; frozen 345/290/139 preserved; September unread.
v324 corrected odds audit: Run 34762939723 success; composite >=3.0 unsupported.

Exhibition source audit:
- tkz `data/previews/tkz/YYYY/MM/DD.csv`
- stt `data/previews/stt/YYYY/MM/DD.csv`
- original `data/previews/original_exhibition/YYYY/MM/DD.csv`
- audited transform `backtest_v51_lane_corrected_tickets.py::corrected_direct`
- ST lane bias uses prior days only.
- neutral 0.5 defaults cannot be treated as proof that a raw metric existed.

---

# 3. Work Unit 5B — v325 boat1-only exhibition postfilter — COMPLETE / NOT PROMOTED

Commits/runs:
- c971d14dac4ebd1bea5f0b73535bd74b7cfe242b — initial script
- d395c77dfdf2b83335b006f85046ec13f507da94 — workflow
- Run 34764216379 exposed missing-source eligibility issue
- 3c4a21e184b1ec0e9e4220a412ed600a4130b810 — failure recorded before correction
- 68bf07bbd783c7082d6e21dd1917c01e1da3800e — fail-closed correction
- corrected Run **34764329333** success, job 103742497228, artifact 10319838860

Final v325:
- 345R / 139 exact3 / 290 head
- frozen `one_turn >= 0.800000`
- Feb-Apr 13/33=39.39%
- May 17/35=48.57%
- Jun PASS 8/25=32.00%; SKIP 24/67=35.82%; baseline 32/92=34.78%
- FORWARD_SUPPORTED=False
- Jul/Aug not opened for v325.

---

# 4. Work Unit 5C — v326 ticket-aware exhibition postfilter — COMPLETE / NOT PROMOTED

Purpose: compare exhibition quality of SECOND/THIRD boats actually covered by the frozen v320 tickets against uncovered opponents.

Implementation/workflow:
- `ee2ca7b155b9a2e1d4559c4e98210bc6cc5d9b55` — initial v326 script
- `64433735827c63971badaff7be2652c8a25586e2` — workflow

First run failure:
- Run **34766023220**, job 103747013697 — FAILED `KeyError: 6` because race-row presence did not guarantee every boat metric existed.
- failure recorded before fix: `27655a5830841815ac38bcf02723419996713d6f`.

Strict per-boat correction:
- `bfeba1b91f5a2b7314ad0de819c81e0c7d934df3`
- Run **34766151983** success, job 103747359375, artifact 10321086346
- strict all-feature source complete/model-ready 237R
- result was `FROZEN_CANDIDATE NONE`.

A second semantic audit found 1-D rules were over-requiring all source families even when a rule used only one family. This was recorded before correction in commit `7fe36555e2a7657957a67235275ead76360880b7`.

Feature-specific source-readiness correction:
- commit **`749d298354f46e2bfa5e8e8e7e19c2f9fd6211cf`**
- 1-D rules now fail closed only on the raw source family actually required by that feature.
- logistic remains full-source/model-ready.
- candidate definitions, quantile grids, C=.15, validation/fallback thresholds, sorting, and Feb-Apr -> May -> Jun chronology were unchanged.

Final v326 Actions:
- Run **34766426083** — SUCCESS
- job **103748102108**
- artifact `v326-1head-ticketaware-exhibition`, ID **10320837179**
- artifact SHA256 `b26b340c8515e557be1ae97637f59b624b8dd347dd61ba7fc133876205454d21`

Final v326 reconciliation/availability:
- **345R / 139 exact3 / 290 head wins** unchanged
- strict all-feature complete/model-ready: 237R
- tkz all6: 289
- ST all6: 296
- original turn all6: 299
- original straight all6: 243
- original avg all6: 299
- turn+straight all6: 243

Frozen candidate after correct feature-specific availability:
- **`sec_st_mean_margin <= -0.600000`**
- discovery Feb-Apr: **8/22 = 36.36% exact3**, head 21/22=95.45%
- May validation: **14/29 = 48.28% exact3**, head 24/29=82.76%
- June PASS: **8/25 = 32.00% exact3**, head 20/25=80.00%
- June SKIP: **24/67 = 35.82% exact3**, head 55/67=82.09%
- June baseline: **32/92 = 34.78% exact3**
- **FORWARD_SUPPORTED=False**

Conclusion:
- v326 ticket-aware exhibition-only postfilter also fails chronological forward validation.
- It is not promoted.
- Jul/Aug remains unread for v326 because forward support failed.
- September outcomes remain unread.

---

# 5. Work Unit 5D — v327 PRE-confidence + exhibition selective postfilter SOURCE AUDIT — COMPLETE

Audited frozen PRE confidence sources:
- v308 persists race-level `p_head` and `opp_mass`; both are computed before target-race settlement and are already reproduced in live v323.
- v317 SECOND uses a probability map `p2[boat]` from causal PRE/prior features only. Safe race-level summaries can be derived directly from that map without labels.
- v318 THIRD uses conditional probability map `pc[(second,third)]`, normalized within each SECOND branch from causal PRE/prior features only.
- v320 computes `pair_prob(p2,pc,alpha=.70)` and frozen `HYBRID` ticket order. These probabilities are pre-settlement and independent of odds/results.
- v323 reconstructs the same live sequence: head `p_head` -> base opponent mass -> frozen v317 `p2` -> frozen v318 `pc` -> v320 pair probabilities/tickets.

Audited v327 PRE feature set to freeze before implementation:
1. `p_head`
2. `opp_mass`
3. `second_top1_prob` = largest frozen v317 `p2`
4. `second_top2_mass` = sum of two largest frozen v317 `p2`
5. `second_margin12` = top1 minus top2 frozen v317 `p2`
6. `third_top1_mean_for_top2_second` = mean best conditional THIRD probability for the top-2 SECOND candidates
7. `third_top1_min_for_top2_second` = weaker of those two branch-best THIRD probabilities
8. `ticket_prob1`, `ticket_prob2`, `ticket_prob3` = pair probabilities of the exact three frozen HYBRID tickets
9. `ticket_mass3` = sum of pair probability on the three frozen tickets
10. `ticket_prob3` / weakest-ticket confidence retained explicitly
11. `ticket_gap34` = probability gap between 3rd and 4th HYBRID-ranked pair
12. `ticket_entropy20` = entropy of normalized 20 pair probabilities

Excluded from v327 PRE confidence inputs:
- odds/composite odds
- result/payout fields
- actual combo/head labels except after feature freeze for evaluation
- same-race exhibition fields inside the PRE confidence block
- Jul/Aug/September outcome-derived fields
- any `meet_*` or future/backfilled value

Historical reconstruction plan:
- use `analysis_v320_1head_exact3_ticket_policy_best_race.csv` only as the immutable 345-race/ticket identity + labels for evaluation after feature generation.
- recompute PRE confidence features fold-by-fold from v313/v308/v317/v318/v320 causal code, keyed by `race_code`.
- verify exact identity before search: **345R / 290 head / 139 exact3** and exact ticket strings unchanged.
- no Jul/Aug or September outcomes opened during feature building/search.

### Predeclared v327 research design — NEXT WORK UNIT
Chronology remains:
- Feb-Apr: discovery only
- May: validation/freeze
- Jun: one-shot forward check
- Jul/Aug may be opened once, reference-only, only if June is forward-supported
- September outcomes remain unread

Candidate families are intentionally small:
1. one-dimensional PRE confidence gates on the frozen features above;
2. one-dimensional exhibition confirmation gates from v326's already-audited feature-specific source families;
3. PRE gate AND one exhibition confirmation gate;
4. one small regularized logistic PASS model using frozen PRE-confidence + audited exhibition features, chronological only, no random CV.

Primary success target:
- June forward exact3 PASS rate >=50% with useful retained R and no obvious month-collapse.
- 345/290/139 and frozen tickets must remain unchanged before filtering.

Failure fallback:
- if PRE-confidence alone does not validate, do not retune v308/v317/v318/v320; stop that family.
- if PRE+exhibition fails June, do not inspect Jul/Aug for promotion and do not create production BUY logic.

---

# 6. Work Unit 5E — v327 IMPLEMENTATION ABOUT TO START

Exact work about to be done:
1. Create `run_v327_1head_preconf_exhibition.py`.
2. Rebuild the frozen 345 cohort's PRE-confidence table fold-by-fold using only v308/v317/v318/v320 causal paths.
3. Assert 345/290/139 and exact frozen ticket identity before any search.
4. Join the existing audited historical exhibition feature builder from v326 without changing source-readiness semantics.
5. Run the predeclared Feb-Apr -> May -> Jun chronology only.
6. Emit race-level dataset, candidate table, frozen candidate summary, monthly PASS/SKIP metrics, and clear `FORWARD_SUPPORTED` flag.
7. Add `.github/workflows/v327-1head-preconf-exhibition.yml` and run Actions.

Success criteria:
- frozen identity/tickets unchanged.
- no Jul/Aug or September outcome read during candidate search.
- every PRE feature available through the same live v323 computation path.
- exhibition features remain fail-closed per source family.
- June forward result explicit.

Failure fallback:
- on any assertion/schema/runtime failure, first append exact failure + intended fix to this handoff, then patch.
- unsafe/unreproducible feature is dropped, never approximated from settlement data.

---

# 7. Exact next resume point
**Implement `run_v327_1head_preconf_exhibition.py` from the frozen source-audited feature set above, then workflow + Actions. Do not open Jul/Aug or September outcomes unless June forward support is achieved.**
