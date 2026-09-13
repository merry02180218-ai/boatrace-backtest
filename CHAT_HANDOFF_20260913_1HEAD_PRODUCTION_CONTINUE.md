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

Already completed before this chat:
- `ee2ca7b155b9a2e1d4559c4e98210bc6cc5d9b55` — `run_v326_1head_ticketaware_exhibition.py`
- ticket identities remain frozen; per-boat features use result-blind tkz/stt/original snapshots and prior-only ST bias.
- chronology: Feb-Apr discovery -> May validation/freeze -> June forward; Jul/Aug unread unless June supports frozen candidate.

This chat reconciled a stale handoff that incorrectly said v325 had not started. Latest GitHub proved v325 was complete and v326 code already existed. A failed create attempt for v325 returned GitHub 422 and did not overwrite code.

Workflow created this chat:
- **64433735827c63971badaff7be2652c8a25586e2** — `.github/workflows/v326-1head-ticketaware-exhibition.yml`

## v326 first Actions run — FAILED; recorded BEFORE code fix
- Run **34766023220**
- job **103747013697**
- workflow setup/dependencies succeeded.
- research step failed in `feature_row -> margin_mean` with **`KeyError: 6`**.
- exact cause: `corrected_direct()` rank dictionaries can omit an individual boat when that boat's raw tkz/stt value is missing, even though the race-level source row exists. v326 assumed all boats 1..6 were present once `has_tkz/has_stt/has_orig` were true.
- no research output/artifact was produced.
- no Jul/Aug or September outcome was read by the failing script.

### Exact fix about to be done
1. Patch v326 to require per-boat raw metric completeness before calling ticket-aware margin functions, not just race-row presence.
2. For tkz require parseable exhibition time for boats 1..6; for stt require parseable start exhibition for boats 1..6.
3. For original exhibition require the actual per-boat turn and straight measurements used by v326 for boats 1..6; do not accept `corrected_direct` neutral 0.5 defaults as evidence.
4. Mark any race failing these requirements as `source_complete=0` and automatic SKIP; never fill missing boat ranks.
5. Re-run the same frozen search/chronology without changing candidate definitions based on this failure.
6. Inspect 345/139/290 reconciliation, source coverage, May freeze, June PASS/SKIP.
7. Jul/Aug remains unread unless the corrected June forward result supports the frozen candidate.

### Success criteria for corrected run
- no KeyError/missing-boat fabrication.
- 345/139/290 identity unchanged.
- per-boat required-source completeness explicit and fail-closed.
- ticket identities unchanged.
- Feb-Apr -> May -> June chronology unchanged.
- June PASS/SKIP exact3/head/retained R explicit.
- no Jul/Aug unless forward-supported; no September outcomes.

### Failure fallback
On another failure, record exact error and intended fix here before changing code again. If live-compatible per-boat original metrics cannot be safely established, stop v326 rather than substitute backfilled/post-race data.

---

# 5. Exact next resume point
**Patch `run_v326_1head_ticketaware_exhibition.py` for per-boat raw metric completeness, then rerun v326. Do not rebuild v325.**
