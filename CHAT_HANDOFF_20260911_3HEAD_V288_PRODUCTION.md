# Chat handoff — 2026-09-11 3-head v288 PRODUCTION

Updated: 2026-09-11 JST
Repository: `merry02180218-ai/boatrace-backtest`

## READ THIS FIRST
This is the current primary handoff for 3-head v288 production. Always inspect latest GitHub first; if this file conflicts with newer code/commits, latest GitHub wins.

Hard rules:
- 2026-07/08 are NON-PRISTINE / contaminated model-selection periods. Never tune production from their outcomes.
- September production remains outcome-blind. Never use current-day result/payout/post-deadline data to reconstruct a pre-deadline decision.
- Deadline path is cache-first. Never rebuild heavy history/model state near a deadline.
- Missing/invalid inputs fail closed; do not invent Waku/exhibition/odds values.
- ROI definition remains payout / settled stake * 100; 10,000 JPY per settled race, misses payout=0.

## 1. Current production-compatible reference
Historical adopted v288 under corrected route semantics remains reproducible:
- 100R / 56 hits / 56.00%
- stake 1,000,000 / payout 1,743,810 / profit +743,810
- ROI 174.381%

But the 100R historical PRE used month-internal percentile and is not the primary live expectation.

Production-compatible leakage-free PRE replay is the operational reference:
- 94R / 52 hits / 55.319%
- stake 940,000 / payout 1,622,070 / profit +682,070
- ROI 172.561%

Route breakdown:
- S: 55R / 33 hits / ROI 184.062%
- A: 21R / 10 hits / ROI 149.162%
- B: 18R / 9 hits / ROI 164.717%

Proof workflow: `verify-v288-operational-pre-replay`, run `34560827602`, success, marker `V288_OPERATIONAL_PRE_REPLAY_OK`.

## 2. Correct v288 route semantics — MUST NOT REGRESS
S requires v243 final/purchasable pass plus:
- `c_b3_minus_b4_waku_st <= 0.4999999999999999`
- `c_b3_minus_b4_st >= -0.6`
- `c_b3_meetst <= 0.861111111111111`

A is an independent rescue outside S; it does NOT require v243 pass. It requires PRE S+A and v242 buyable, then:
- `c_b3_minus_b4_st >= 0.6`
- `c_wall12_weak <= 0.24875`

B is an independent rescue outside S/A; it does NOT require v243 pass. It requires PRE S+A and v242 buyable, then:
- `c_b3_minus_b2_motor >= 0.22388571428571424`
- `c_b3_inside_nst <= -0.0714285714285712`

Precedence is exactly `S -> else A -> else B -> else NO_BET`.
LIVE parity proof: run `34560454539`, success, `V288_LIVE_ROUTE_PARITY_OK cases=32`.

## 3. Production PRE semantics
Old current-month/current-day percentile bridge is prohibited.

Current live PRE:
1. fit/score from prior allowed history only;
2. S cutoff = training-score 70th percentile;
3. A cutoff = training-score 20th percentile;
4. current races are graded independently of future/current-month races.

For September 2026 the model/history state is frozen through `2026-08-31`.
Required cache flags:
- `history_cutoff == 2026-08-31`
- `operational_pre_training_quantile == True`
- `operational_pre_percentile_bridge == False`
- `target_result_or_payout_used == False`

## 4. 2026-09-11 definitive PRE state
Do not use older/intermediate values. The authoritative successful artifacts are the fixed single-pass run and the generic daily production run below; their PRE CSVs are byte-identical.

Definitive candidate:
- race code `202609111403` = 鳴門3R / JCD14 3R
- grade S
- PRE score `4.426435747478959`
- training CDF `0.7743362831858407`
- p3 `0.4630542888426509`
- `b3_minus_b2_motor = 0.46036000000000005`
- `b3_inside_nst = 0.14285714285714302`
- S threshold `3.290593` (display rounded)
- A threshold `-4.798475` (display rounded)
- v243 current head universe: 1
- PRE S+A candidates: 1

Important coverage limitation on 2026-09-11:
- Kyoteibiyori detail rows seen: 144
- complete race-card + required Waku10 rows: 132
- excluded because required Waku10 was missing: 12
- policy is strict audited v288 semantics; these 12 are excluded rather than filled with guessed/default Waku values.
- This is safe/fail-closed but can miss a candidate. Fixing these 12 requires a source/parity audit, not an unverified fallback.

## 5. Single-pass morning cache is verified
Old architecture rebuilt the heavy augmented history twice (PRE then cache). It has been replaced by one augmented build shared by PRE and cache.

Fixed 2026-09-11 proof:
- workflow run `34572656816`
- job `103177958122`
- success
- fixed artifact PRE CSV matches generic daily PRE CSV exactly.

Generic production proof:
- workflow `daily-3head-v288-production.yml`
- run `34573237107`
- job `103179794043`
- success
- artifact `daily-3head-v288-production`, artifact ID `10189256180`
- cache SHA256 `5930cd6aa3dac82af7dce69b7f7502b932d358045fd6678673cb7a49878d068c`
- `single_augmented_build = true`
- build_augmented ~1228.04 sec
- total production build ~1264.87 sec (~21m05)

Older two-pass run was about 34m; single-pass saves roughly 12-13 minutes under comparable conditions.

Production daily schedule:
- `.github/workflows/daily-3head-v288-production.yml`
- 06:00 JST primary
- 06:30 JST fallback/retry
- scope guard: September 2026 only. Outside September it does no model build.

## 6. Production deadline path
Primary scorer remains the audited `run_20260911_3head_v288_live.py`.
Production wrapper: `run_3head_v288_production_live.py`.

Wrapper adds fail-closed operational guards before delegating unchanged scoring:
- target date must be September 2026
- JCD 1..24 / race 1..12
- deadline date must equal target date
- cache date must equal target date
- history cutoff must be exactly 2026-08-31
- training-quantile PRE must be enabled
- legacy percentile bridge must be disabled
- result/payout leakage flag must be false
- required cache payload must exist

Hardening commit: `ca50d7d57dc42d281b9771bdb444d5802f1b0e7f`.
Associated LIVE validation passed.

Deadline scorer still does only:
`cache load -> BOATCAST exhibition/start/original -> official 120/120 trifecta odds -> cached model scoring -> v242/v243 -> corrected v288 S/A/B -> variable 5-10 tickets -> exact 10,000 JPY Dutch -> output/audit`.
No model fit in deadline path.

## 7. Official deadline acquisition
`fetch_boatrace_deadline.py` reads BOAT RACE official `racelist` only and persists timestamp/hash metadata.
It never requests result/payout endpoints.

For 2026-09-11 Naruto 3R it resolved:
- deadline `2026-09-11T09:36:00+09:00`
- official racelist source
- result endpoint requested: false
- payout endpoint requested: false

Because the production bundle was completed after this deadline, DO NOT reconstruct a fake pre-deadline BET using later exhibition/odds.

## 8. Auto-LIVE watcher
Primary automatic watcher:
- `.github/workflows/auto-live-3head-v288-production.yml`
- cron every 5 minutes during September (`*/5 * * 9 *`)
- also supports manual workflow_dispatch.

Flow:
1. find a successful frozen daily bundle for the target day;
2. create matrix from PRE S+A candidate race codes only;
3. skip a race if immutable `live-v288-final-<racecode>` artifact already exists;
4. resolve official deadline;
5. >30 min remaining -> WAIT, no heavy model dependencies;
6. <=30 min and before deadline -> TRY: download exact daily cache, install scorer deps, run production wrapper;
7. invalid/not-yet-published exhibition or odds -> do not finalize; later scheduled run may retry;
8. deadline already passed without valid decision -> final `ERROR_NO_BET`;
9. once final artifact exists, duplicate guard prevents another final decision.

Latest watcher optimization commit: `9888fb6555db8b2af6e502a7448a4b20c23e2ad2` (`Avoid heavy installs while v288 watcher waits`). Validation succeeded.

GitHub `schedule` events had not yet emitted a run immediately after adding the new cron, so production behavior was verified with a one-shot Actions verifier instead of waiting/claiming future completion.

One-shot production watcher proof:
- workflow `.github/workflows/verify-auto-live-v288-production.yml`
- run `34575367215`
- `verify-expired-finalization`: success
- `verify-duplicate-guard`: success
- final artifact `live-v288-final-202609111403`
- artifact ID `10189401755`
- decision `ERROR_NO_BET`
- reason: deadline passed before a valid production LIVE decision was frozen
- deadline `2026-09-11T09:36:00+09:00`
- decision time `2026-09-11T16:39:22.755830+09:00`
- `result_or_payout_used = false`
- duplicate guard log: `DUPLICATE_GUARD_OK final_artifacts=1`

This final artifact is intentionally safe: Naruto3 was not retroactively scored/bet after deadline.

## 9. Current production operating procedure
Primary route:
`06:00 daily build (06:30 fallback) -> frozen daily artifact -> 5-minute auto watcher -> PRE candidates only -> official deadline -> WAIT/TRY/EXPIRED -> if TRY, exhibition + exact 120 odds -> v242/v243 -> v288 S/A/B -> 5-10 points -> exact 10k Dutch -> immutable final artifact`.

Manual fallback:
- `.github/workflows/live-3head-v288-production.yml`
- use only with the same target-day frozen daily artifact.

Old date-specific files remain for audit/reproducibility, not as the preferred daily production entry point.

## 10. Immediate next priority
The core production automation is now verified fail-closed, but full all-race coverage is NOT solved because 12/144 races were excluded on 2026-09-11 for missing required Waku10.

Next work should prioritize current-input coverage without semantic drift:
1. identify an alternative pre-race source for the exact missing Waku10-equivalent fields;
2. compare that source against races where canonical Kyoteibiyori Waku10 exists, using feature/prediction parity only and no outcome tuning;
3. accept it only if parity is proven; otherwise continue fail-closed exclusion;
4. keep Jul/Aug NON-PRISTINE and September outcomes blind.

After coverage, the next useful operational test is the first future PRE candidate whose daily cache exists before exhibition/deadline. That race must be allowed to flow through the real TRY branch and verify exhibition + official 120 odds + v288 + Dutch before deadline.

## Important files
- `CHAT_HANDOFF_20260911_3HEAD_V288_PRODUCTION.md`
- `fetch_3head_v288_pre_inputs_live.py`
- `build_3head_v288_daily_live.py`
- `run_3head_v288_production_live.py`
- `run_20260911_3head_v288_live.py`
- `fetch_boatrace_deadline.py`
- `fetch_live_trifecta_odds.py`
- `.github/workflows/daily-3head-v288-production.yml`
- `.github/workflows/auto-live-3head-v288-production.yml`
- `.github/workflows/live-3head-v288-production.yml`
- `.github/workflows/verify-auto-live-v288-production.yml`
- `verify_v288_operational_pre_replay.py`
- `OFFICIAL_3HEAD_V288_100R_ADOPTED_20260911.md`

## Recommended next-chat opening
`boatrace-backtest の CHAT_HANDOFF_20260911_3HEAD_V288_PRODUCTION.md と最新GitHubを読んで続き。最新GitHub優先。3号艇v288のproduction自動化は daily cache -> auto watcher -> fail-closed final artifact まで確認済み。まず2026-09-11に132/144しか完全PRE入力を作れなかった12レースのWaku10欠損を、結果を使わずsource parityで安全に埋められるか調査して。未検証fallbackは使わない。7月8月NON-PRISTINE、9月outcome blindを厳守。`
