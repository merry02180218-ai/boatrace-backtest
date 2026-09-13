# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## READ THIS FIRST — authoritative current 1-head state

Latest GitHub wins over old chat memory and over stale handoff text.

Mandatory operating pattern for every work unit:

**handoff update -> work -> result append -> next work handoff update**

Before every code change/restart record here:
1. current position,
2. exact work about to be done,
3. success criteria,
4. failure fallback.

After every work unit record here:
1. what was actually done,
2. commit SHA(s),
3. Actions Run ID(s)/status,
4. metrics/results,
5. exact next resume point.

If interrupted, resume from the first unfinished item in this file. Never guess from memory.

---

# 1. Frozen production stack — DO NOT ALTER

PRE / same-day result-blind stack:
1. HEAD: **v308**
2. SECOND: **v317 `OUTER_L2_1`**
3. THIRD: **v318 `DROPSTART_T0.1`**
4. 3-ticket policy: **v320 `HYBRID alpha=.70`**
5. Exactly **3 trifecta tickets per selected race**
6. Current three odds -> composite odds: `1 / (1/o1 + 1/o2 + 1/o3)`

Frozen regression:
- selected races: **345**
- boat1 wins: **290/345 = 84.06%**
- exact3 hits: **139/345 = 40.29%**

v308 frozen point:
- `q=.980`
- opponent mass >= `.375`
- head cutoff **0.8073405637**

Causality guardrails:
- Jul/Aug 2026 = **NON-PRISTINE/reference-only**. Never tune/promote on them.
- September outcomes = **UNREAD**.
- no same/later-race result, payout, future/backfill contamination.
- month M trains strictly on `< M`.
- missing current exhibition sources must fail closed.
- same-race exhibition is post-PRE only; never feed it backward into v308/v317/v318/v320.

Mandatory causal cache family remains:
- `cache_v313_1head_opponent_pre.csv.gz`
- `cache_v313_1head_opponent_p3.csv.gz`
- `cache_v313_1head_opponent_p4.csv.gz`
- `CACHE_V313_1HEAD_OPPONENT_CAUSAL.md`

---

# 2. Frozen model research summary

- v309 clean base: exact3 132/345 = 38.26%; SECOND TOP2 71.72%
- v310 causal p3/p4: SECOND TOP2 72.07%; exact3 133/345
- v311 DROP_START: SECOND TOP2 72.41%; exact3 136/345 = 39.42%
- v312 outer gate: SECOND TOP2 73.10%; exact3 136/345
- v314 role split: unstable; not promoted
- v315 pairwise SECOND: exact3 133/345
- v316 multiclass SECOND: exact3 136/345
- v317 `OUTER_L2_1`: exact3 137/345 = 39.71%
- v318 `DROPSTART_T0.1`: exact3 137/345 = 39.71%
- v319 direct ordered-pair: exact3 134/345 = 38.84%
- v320 `HYBRID alpha=.70`: exact3 **139/345 = 40.29%**

v321 Jul/Aug NON-PRISTINE reference:
- Run **34750719803**
- 55R / boat1 wins 45 / exact3 21 = 38.18%
- July 13R / exact3 3
- August 42R / exact3 18

v322 development composite-odds diagnostic:
- Run **34753932483** success
- 339 complete odds / 136 evaluable exact3 hits / ROI 91.27%
- no odds-only BUY cutoff promoted.

v323 production adapter:
- Run **34757079269** success
- frozen regression remained 345 / 290 / 139
- September results unread.

v324 Jul/Aug composite-odds audit:
- corrected Run **34762939723** success
- 55 selected / 21 exact3 / 55 complete odds
- composite >=3.0 was not supported; no BUY cutoff promoted.

---

# 3. Exhibition source audit — COMPLETE

Safe historical/current sources:
- `data/previews/tkz/YYYY/MM/DD.csv`
- `data/previews/stt/YYYY/MM/DD.csv`
- `data/previews/original_exhibition/YYYY/MM/DD.csv`
- audited historical implementation: `analyze_v108_1head_feasibility.py`
- live semantics reference: `build_4head_v283_current_exhibition_live.py`
- rank/correction helper: `backtest_v51_lane_corrected_tickets.py::corrected_direct`

v108 timing audit:
- feature freeze precedes settlement.
- ST lane-bias correction uses prior days only.
- historical overall coverage was tkz 92.8%, stt 92.8%, original 88.5%.

Important source rule discovered during v325:
- v108 neutral `0.5` feature values can represent missing sources.
- therefore the postfilter must check `has_tkz` / `has_stt` / `has_orig` explicitly and fail closed when the required actual source is absent.

---

# 4. Work Unit 5B — v325 boat1-only exhibition postfilter — COMPLETE

Initial implementation:
- `c971d14dac4ebd1bea5f0b73535bd74b7cfe242b` — v325 script
- `d395c77dfdf2b83335b006f85046ec13f507da94` — v325 workflow
- initial Run **34764216379** success, but audit found neutral-0.5 missing-source leakage into PASS eligibility.

Failure/correction was recorded before fixing:
- `3c4a21e184b1ec0e9e4220a412ed600a4130b810` — failure/worklog record
- `68bf07bbd783c7082d6e21dd1917c01e1da3800e` — fail-closed correction

Corrected Run:
- Actions Run **34764329333** — success
- job `103742497228`
- artifact `v325-1head-exhibition-postfilter`, ID `10319838860`

Corrected v325 metrics:
- v320 reconcile: **345R / 139 exact3 / 290 head wins**
- v108 joined rows 336
- tkz 292 / stt 292 / original 295 / all-source complete 292
- source-complete split: Feb-Apr 97 / May 104 / Jun 91
- frozen May candidate: **`one_turn >= 0.800000`**
- discovery Feb-Apr: **13/33 = 39.39% exact3**, head 27/33 = 81.82%
- May validation: **17/35 = 48.57% exact3**, head 33/35 = 94.29%
- June forward PASS: **8/25 = 32.00% exact3**, head 21/25 = 84.00%
- June skipped: **24/67 = 35.82% exact3**
- June baseline: **32/92 = 34.78% exact3**
- `FORWARD_SUPPORTED=False`

Conclusion:
- boat1-only same-race exhibition/original-exhibition gating did **not** produce a stable >=50% exact3 postfilter.
- Jul/Aug was correctly not evaluated for v325 because June did not support the frozen candidate.
- v325 is not promoted.

---

# 5. Work Unit 5C — v326 ticket-aware exhibition postfilter

Rationale:
The frozen exact3 tickets depend on the actual 2nd/3rd-place opponent boats. v325 only evaluated boat1 exhibition quality, so v326 adds same-race result-blind exhibition features for the boats actually covered by the three frozen tickets and compares them with uncovered opponents.

Pre-work plan had already been written in `CHAT_HANDOFF_20260913_1HEAD_WORKLOG.md` before v326 implementation.

Already completed:
- commit **`ee2ca7b155b9a2e1d4559c4e98210bc6cc5d9b55`** — `run_v326_1head_ticketaware_exhibition.py` research implementation.
- v326 reconstructs per-boat same-race exhibition ranks directly from tkz/stt/original snapshots with prior-only ST bias.
- parses the exact frozen three v320 tickets.
- derives covered SECOND, covered THIRD, covered opponent union, uncovered opponents, and ticket-aware margins/balance/dominance features.
- missing actual source is fail-closed via `source_complete` / `model_ready`.
- chronological split remains Feb-Apr discovery -> May validation/freeze -> June untouched forward.
- Jul/Aug remains unread unless a frozen v326 candidate is June-forward-supported.

## CURRENT POSITION — v326 workflow/run still must be verified

At 2026-09-14 00:29 JST the latest commit scan showed the v326 code commit above, but no later commit explicitly named a v326 workflow or v326 result.

A stale authoritative handoff had incorrectly said v325 had not started. That conflict is now corrected here using the later GitHub commits/results as source of truth.

During this chat a create attempt for `run_v325_1head_exhibition_postfilter.py` returned GitHub 422 (`sha wasn't supplied`) because the file already existed. No v325 code was overwritten. This revealed the stale-handoff/latest-GitHub conflict. The fix is to stop redoing v325 and resume from v326.

### Exact work about to be done
1. Verify whether `.github/workflows/v326-1head-ticketaware-exhibition.yml` (or equivalent) already exists despite commit-message search.
2. If absent, create a v326 workflow that runs the existing v326 script, uploads `/tmp/v326/*`, and never reads September outcomes.
3. Trigger/observe GitHub Actions.
4. Inspect actual logs/artifact and verify 345/139/290 identity, source coverage, frozen candidate, May metrics, June PASS/SKIP metrics.
5. Only if June is forward-supported may a separate one-time Jul/Aug reference step be considered; do not silently add Jul/Aug tuning.
6. Append all actual results, commit SHA, Run ID, job/artifact IDs, and the next resume point to this handoff.

### Success criteria
- frozen v320 exactly **345R / 139 exact3 / 290 head wins**.
- ticket identities unchanged.
- per-boat exhibition features come only from pre-settlement tkz/stt/original snapshots using live-compatible semantics.
- missing source cannot PASS.
- Feb-Apr -> May freeze -> June forward chronology is preserved.
- June PASS exact3/head/retained R and SKIP metrics are explicit.
- no Jul/Aug outcome use unless June supports the frozen candidate.
- no September result/payout read.
- no modification to v308/v317/v318/v320/v323.

### Failure fallback
- On any Actions/code/workflow failure, append the exact failure and intended fix here **before** changing code.
- If safe per-boat reconstruction is not live-compatible, stop and document the source mismatch instead of substituting result/backfilled data.

---

# 6. Exact next resume point

**Resume Work Unit 5C from workflow verification for the already-committed v326 code. Do not rebuild v325.**
