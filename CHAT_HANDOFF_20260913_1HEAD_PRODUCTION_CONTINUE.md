# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## READ THIS FIRST — authoritative current 1-head state
Latest GitHub wins over old chat memory and stale handoff text.

Mandatory pattern: **handoff update -> work -> result append -> next work handoff update**.
Before every code change/restart record current position, exact next work, success criteria, and failure fallback. After every work unit record what was done, commit SHA(s), Actions Run ID/status, metrics/results, and exact next resume point.

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
- missing current exhibition inputs fail closed.
- do not modify v308/v317/v318/v320/v323.

---

# 2. Important completed work

v321 Jul/Aug reference: Run 34750719803, 55R / 45 head / 21 exact3.
v322 composite odds: Run 34753932483 success; no BUY cutoff promoted.
v323 production adapter: Run 34757079269 success; frozen 345/290/139 preserved; September unread.
v324 corrected odds audit: Run 34762939723 success; composite >=3.0 unsupported.

Exhibition source audit is complete:
- tkz `data/previews/tkz/YYYY/MM/DD.csv`
- stt `data/previews/stt/YYYY/MM/DD.csv`
- original `data/previews/original_exhibition/YYYY/MM/DD.csv`
- audited transform `backtest_v51_lane_corrected_tickets.py::corrected_direct`
- ST lane bias must use prior days only.

v108 neutral 0.5 values can stand for missing metrics. Therefore actual source/metric availability must be checked explicitly; neutral defaults cannot qualify a race to PASS.

---

# 3. Work Unit 5B — v325 boat1-only exhibition postfilter — COMPLETE

Commits/runs:
- c971d14dac4ebd1bea5f0b73535bd74b7cfe242b — initial v325 script
- d395c77dfdf2b83335b006f85046ec13f507da94 — workflow
- initial Run 34764216379 success but missing-source eligibility flaw found
- 3c4a21e184b1ec0e9e4220a412ed600a4130b810 — failure recorded before correction
- 68bf07bbd783c7082d6e21dd1917c01e1da3800e — fail-closed correction
- corrected Run **34764329333** success, job 103742497228, artifact 10319838860

Corrected metrics:
- reconcile 345R / 139 exact3 / 290 head
- all-source complete 292
- frozen candidate `one_turn >= 0.800000`
- Feb-Apr 13/33 = 39.39%
- May 17/35 = 48.57%
- Jun PASS 8/25 = 32.00%; Jun SKIP 24/67 = 35.82%; Jun baseline 32/92 = 34.78%
- FORWARD_SUPPORTED=False

Conclusion: boat1-only exhibition gating failed. Jul/Aug was not evaluated. v325 not promoted.

---

# 4. Work Unit 5C — v326 ticket-aware exhibition postfilter

Purpose: evaluate same-race exhibition quality of the actual SECOND/THIRD boats covered by the frozen three v320 tickets versus uncovered opponents.

Implementation/workflow:
- `ee2ca7b155b9a2e1d4559c4e98210bc6cc5d9b55` — initial `run_v326_1head_ticketaware_exhibition.py`
- `64433735827c63971badaff7be2652c8a25586e2` — `.github/workflows/v326-1head-ticketaware-exhibition.yml`

First run:
- Run **34766023220**, job 103747013697 — FAILED
- failure: `KeyError: 6` in ticket-aware margin calculation because a race-level source row could exist while a specific boat raw metric was missing.
- failure was recorded before fix in commit `27655a5830841815ac38bcf02723419996713d6f`.

Per-boat strict completeness correction:
- commit **`bfeba1b91f5a2b7314ad0de819c81e0c7d934df3`**
- tkz exhibition time, ST, original turn/straight were audited per boat 1..6.
- missing required all-six metric made the race fail closed rather than creating a neutral rank.

Corrected run:
- Actions Run **34766151983** — SUCCESS
- job **103747359375**
- artifact `v326-1head-ticketaware-exhibition`, ID **10321086346**
- artifact SHA256 `7593d5536cc616cea543dd279e7b869f475574efc7cbab2624f66a4310f55b65`

Corrected-run reconciliation/coverage:
- frozen baseline: **345R / 139 exact3 / 290 head wins**
- strict all-source complete: **237R**
- model-ready: **237R**
- raw all-six coverage: tkz 289 / stt 296 / original turn 299 / original straight 243 / original required(turn+straight) 243
- monthly strict-source complete: Feb 31 / Mar 10 / Apr 40 / May 89 / Jun 67

Result from strict-all-source run:
- `FROZEN_CANDIDATE NONE`
- `forward_supported=False`
- Jul/Aug and September outcomes were not read.

Useful near-misses from artifact candidate tables (diagnostic only, not promoted):
- `covered_straight_weak_margin >= 0.2`: discovery 6/12=50.0%, May 8/13=61.54% — too few discovery/validation races for fixed freeze guardrails.
- `covered_straight_weak_margin >= -0.2`: discovery 8/17=47.06%, May 11/21=52.38% — discovery too small/weak.
- logit high-score rows reached strong discovery rates but did not meet retained-R chronology; e.g. one candidate had discovery 9/12=75% and May 8/16=50%, but discovery R was below the fixed minimum.
- broader logit candidate with discovery 31/61=50.82% fell to May 21/52=40.38%.

## IMPORTANT semantic audit after successful Run 34766151983 — recorded BEFORE next code fix

The corrected run is safe but **overly strict for 1-D rules**: `rule_search()` currently requires `source_complete==1` for every one-dimensional feature. `source_complete` means tkz + ST + original turn + original straight all available for all six boats.

This is stricter than the declared rule “missing the source REQUIRED BY THAT FEATURE => fail closed.” Example: `sec_st_mean_margin` only needs ST all-six, but current code also rejects a race because original straight is missing. This unnecessarily reduces the 1-D discovery/May sample and can turn the result into `NONE` for a data-availability reason unrelated to that feature.

This is a source-semantics correction, **not performance retuning**. Do not change feature definitions, quantile grids, model C, freeze thresholds, retained-R guardrails, or chronological splits.

### Exact work about to be done
1. Add explicit feature-family readiness flags and make 1-D rules require only the actual raw source metrics they use:
   - `sec_ex_mean_margin` -> `tkz_all6`
   - `sec_st_mean_margin` -> `stt_all6`
   - turn rules (`sec_turn_mean_margin`, `third_turn_mean_margin`, `covered_turn_weak_margin`) -> `orig_turn_all6`
   - straight rules (`sec_straight_mean_margin`, `third_straight_mean_margin`, `covered_straight_weak_margin`) -> `orig_straight_all6`
   - `third_orig_mean_margin` -> strict `orig_avg_all6` where every original metric contributing to average is present for all six boats
   - `covered_balance_min` -> both original turn and straight all-six.
2. Build partial feature rows safely: compute each feature group only when its raw required source family is complete; leave unavailable features NaN. Do not let `corrected_direct` neutral defaults qualify missing metrics.
3. Keep logistic multi-feature `model_ready` strict: all MODEL_FEATURES present with their source families complete.
4. Keep existing 1-D search quantiles `.10..90 step .10`, both directions, existing primary/fallback validation criteria, logit C=.15 and threshold grid, and candidate sorting unchanged.
5. Rerun same Feb-Apr -> May freeze -> June forward chronology.
6. Report corrected per-feature coverage, frozen candidate if any, and June PASS/SKIP. Jul/Aug remains unread unless a candidate is genuinely June-forward-supported.

### Success criteria
- 345/139/290 unchanged.
- feature-specific fail-closed semantics exactly match actual required source(s).
- no missing raw metric produces a usable derived feature.
- ticket identities unchanged.
- search/freeze hyperparameters unchanged from the predeclared v326 implementation.
- June PASS/SKIP exact3/head/retained R explicit if a candidate freezes.
- no Jul/Aug unless forward-supported; no September outcome read.

### Failure fallback
On another failure, append the exact error and intended fix here before changing code. If any original-exhibition derived feature cannot be given live-compatible all-six source semantics, exclude that feature safely rather than use neutral/backfilled values.

---

# 5. Exact next resume point
**Patch v326 for feature-specific source readiness without changing search/freeze rules, then rerun v326.**
