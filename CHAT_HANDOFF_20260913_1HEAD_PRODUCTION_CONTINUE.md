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

# 5. Work Unit 5D — v327 PRE-confidence + exhibition selective postfilter SOURCE AUDIT STARTING

Reason for next direction:
- v325 boat1-only exhibition and v326 ticket-aware exhibition both failed June forward validation.
- Exhibition-only thresholds are therefore not enough.
- The next safe post-PRE direction is to test whether **already-frozen PRE/ticket confidence** can identify intrinsically easier exact3 races, then use exhibition only as an incremental same-race confirmation signal.
- This remains a PASS/SKIP layer after v320; it must not alter frozen selection or ticket identities.

### Exact work about to be done
1. Audit frozen v308/v317/v318/v320 outputs/scripts for result-blind confidence values available before exhibition/settlement, especially:
   - v308/head confidence,
   - v317 SECOND probability/margin/confidence,
   - v318 THIRD probability/margin/confidence,
   - v320 pair/ticket probability or ticket-mass/spread signals.
2. Identify a single race-level historical table keyed by `race_code` that can reproduce the frozen 345 cohort without recomputing from settlement-aware fields.
3. Causality-audit each candidate confidence feature: it must be generated from the already-frozen PRE path and available live in v323 or reproducible with the same live fit.
4. Do **not** inspect Jul/Aug/September outcomes.
5. Before any v327 model implementation, append the exact audited feature set and predeclared chronological research design here.

### Success criteria for source audit
- exact 345/139/290 identity maintained.
- every proposed confidence feature is demonstrably PRE/result-blind.
- no feature relies on odds, result, payout, same-race exhibition, or future/backfilled values.
- identify how the same feature can be computed in live v323 flow.
- no model/threshold search starts until the audited feature set is frozen in this handoff.

### Failure fallback
- If no stable frozen PRE-confidence outputs are persisted, reconstruct only from v308/v317/v318/v320 causal caches/scripts and verify against the frozen 345 race/ticket identity.
- If a proposed signal cannot be reproduced live/result-blind, exclude it rather than approximate from settlement data.

---

# 6. Exact next resume point
**Audit v308/v317/v318/v320 confidence outputs for v327. Do not reopen Jul/Aug or September outcomes.**
