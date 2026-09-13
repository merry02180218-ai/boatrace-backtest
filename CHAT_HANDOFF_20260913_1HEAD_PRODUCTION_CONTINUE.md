# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## Mandatory operating rule
Before every work unit, record current position and intended next action here. After work, record commit/run/result/next action. Latest GitHub wins.

## Frozen production stack
v308 PRE head -> v317 SECOND OUTER_L2_1 -> v318 THIRD DROPSTART_T0.1 -> v320 HYBRID alpha=.70 exactly 3 tickets -> three odds -> composite odds `1/(1/o1+1/o2+1/o3)`.
Development regression: 345 selected / 290 head wins / 139 exact3. Jul/Aug 2026 NON-PRISTINE/reference-only. September outcomes unread. `meet_*` forbidden.

## Production adapter status
v323 implementation was completed and a successful GitHub Actions production run was verified: run **34757079269** (`live-1head-v323-20260913`). Historical regression remained 345/290/139 and frozen hcut 0.8073405637. 2026-09-13 current scoring selected 2 races and calculated current 3-ticket composite odds. No BUY cutoff was frozen; status remained fail-safe.

## WORK UNIT 2026-09-13-4 — Jul/Aug composite-odds BUY reference audit — written BEFORE execution
User hypothesis: with roughly 40% exact-3-ticket hit probability, a composite-odds BUY condition around 3.0 may be reasonable. User explicitly requested testing this on July/August.

Do now:
1. Use the already frozen v321 Jul/Aug NON-PRISTINE selections and frozen v317/v318/v320 3-ticket outputs. Do NOT retrain, tune, or alter model components on Jul/Aug.
2. Attach historical trifecta closing odds to the exact three tickets for every Jul/Aug selected race where complete odds exist.
3. Compute composite odds exactly as `1/(1/o1+1/o2+1/o3)`.
4. Report separately July, August, and Jul+Aug for at least thresholds >=2.5, >=2.7, >=3.0, >=3.2, >=3.5: eligible races, exact3 hits, hit rate, notional composite-odds ROI, and profit/loss under 1 unit per eligible race. Misses count as -1 unit; hits return composite_odds units.
5. Also report ALL evaluable races. Missing odds must be explicit and excluded only from odds-evaluable rows, never silently treated as wins/losses.
6. This is NON-PRISTINE reference evidence only. Do not promote a threshold merely because it performs best on Jul/Aug. The immediate question is specifically whether >=3.0 behaves plausibly out of the reused development period.
7. Implement as a new audit script/workflow if no committed output already contains these exact Jul/Aug calculations. Trigger GitHub Actions, verify real Run ID/logs/artifact, then append the result here.

Success criteria: frozen Jul/Aug race/ticket identities are unchanged; exact3 counts reconcile with v321 reference (Jul+Aug 21/55 before odds-missing exclusions); threshold table is produced from historical odds with correct hit/miss accounting; no September outcome is read.

If interrupted: resume this WORK UNIT 4 from item 1. Do not change the frozen model or silently choose a BUY cutoff.
