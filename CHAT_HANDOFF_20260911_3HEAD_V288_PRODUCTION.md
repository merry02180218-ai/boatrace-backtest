# Chat handoff — 2026-09-11 3-head v288 PRODUCTION

Updated: 2026-09-12 JST
Repository: `merry02180218-ai/boatrace-backtest`

## READ THIS FIRST
This is the current primary handoff for 3-head v288 production. Always inspect latest GitHub first; if this file conflicts with newer code/commits, latest GitHub wins.

Hard rules:
- 2026-07/08 are NON-PRISTINE / contaminated model-selection periods. Never tune production from their outcomes.
- September production remains outcome-blind. Never use current-day result/payout/post-deadline data to reconstruct a pre-deadline decision.
- Deadline path is cache-first. Never rebuild heavy history/model state near a deadline.
- Waku10 production policy is now formally adopted: Kyoteibiyori primary; if the exact required Waku10-equivalent row is missing, use only the previously overlap-validated direct BOATCAST Waku10 parser; if both fail, fail closed.
- Never invent/default Waku, exhibition, or odds values.
- ROI definition remains payout / settled stake * 100; 10,000 JPY per settled race, misses payout=0.

## 1. Current production-compatible reference
Historical adopted v288 under corrected route semantics remains reproducible:
- 100R / 56 hits / 56.00%
- stake 1,000,000 / payout 1,743,810 / profit +743,810
- ROI 174.381%

The 100R historical PRE used month-internal percentile and is not the primary live expectation.

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

## 4. Waku10 fallback — FORMALLY ADOPTED
The earlier Waku10 repair was already validated historically. The 2026-09-11 132/144 regression happened because the new LIVE PRE fetcher used Kyoteibiyori only and did not reuse that validated BOATCAST path.

Production fix:
- `historical_waku10_fetcher.py` exposes direct per-race BOATCAST `fetch_race()` using the previously validated parser/source.
- `fetch_3head_v288_pre_inputs_live.py` uses Kyoteibiyori first.
- Only when Kyoteibiyori cannot build the exact required Waku10-equivalent row does it call the validated BOATCAST direct fallback.
- If the fallback also fails, the race remains fail-closed.
- No result/payout/current exhibition data are used by this fallback.

Formal verification:
- workflow: `verify-waku10-live-fallback`
- run: `34583558321`
- result: success
- the 12 formerly excluded race codes: 12/12 direct BOATCAST Waku10 success
- full 2026-09-11 PRE input coverage: 144/144
- Kyoteibiyori source rows: 132
- validated BOATCAST fallback rows: 12
- excluded rows: 0
- marker: `WAKU10_LIVE_FALLBACK_144_OF_144_OK`

This is now the production Waku10 policy. Do NOT regress to “Kyoteibiyori-only” and do NOT describe these 12 races as unresolved.

## 5. 2026-09-11 definitive PRE state after 144/144 rebuild
The authoritative latest production run rebuilt PRE + LIVE cache using all 144 complete races.

Definitive candidate remains unchanged:
- race code `202609111403` = 鳴門3R / JCD14 3R
- grade S
- PRE score `4.426435747478959`
- training CDF `0.7743362831858407`
- p3 `0.4630542888426509`
- `b3_minus_b2_motor = 0.46036000000000005`
- `b3_inside_nst = 0.14285714285714302`
- S threshold `3.290592837278`
- A threshold `-4.79847489663985`
- v243 current head universe: 1
- PRE S+A candidates: 1

So restoring the validated Waku10 fallback did not create extra 2026-09-11 PRE candidates or alter the existing Naruto 3R candidate.

Latest full production proof:
- workflow: `daily-3head-v288-production.yml`
- run: `34583497482`
- job: `103212249604`
- conclusion: success
- complete PRE rows: 144
- live cache rows: 144
- artifact: `daily-3head-v288-production`
- artifact ID: `10193393328`
- cache SHA256: `dcccae132c1a026b0862ab99fa6030e7f839a3c217de9fd03af1fc443a2c9727`
- `single_augmented_build = true`
- `result_or_payout_used = false`
- artifact digest: `sha256:94189f705c543aa5e90fbdccc458f592aae81aee1692074cee3f92cc1b5f9fbc`

## 6. Single-pass morning cache
The heavy augmented history is built once and shared by PRE and cache.

Production daily schedule:
- `.github/workflows/daily-3head-v288-production.yml`
- 06:00 JST primary
- 06:30 JST fallback/retry
- September 2026 scope guard only; next month requires a newly frozen prior-month audit.

## 7. Production deadline path
Primary scorer remains the audited `run_20260911_3head_v288_live.py`.
Production wrapper: `run_3head_v288_production_live.py`.

Wrapper fail-closed guards include:
- target date must be September 2026
- JCD 1..24 / race 1..12
- deadline date == target date
- cache date == target date
- history cutoff exactly 2026-08-31
- training-quantile PRE enabled
- legacy percentile bridge disabled
- result/payout leakage flag false
- required cache payload exists

Deadline scorer path:
`cache load -> BOATCAST exhibition/start/original -> official 120/120 trifecta odds -> cached model scoring -> v242/v243 -> corrected v288 S/A/B -> variable 5-10 tickets -> exact 10,000 JPY Dutch -> output/audit`.
No model fit occurs in the deadline path.

## 8. Official deadline acquisition and auto-LIVE watcher
`fetch_boatrace_deadline.py` reads BOAT RACE official `racelist` only and does not request result/payout endpoints.

Auto watcher:
- `.github/workflows/auto-live-3head-v288-production.yml`
- cron every 5 minutes during September
- matrix contains PRE S+A candidates only
- immutable `live-v288-final-<racecode>` artifact prevents duplicate finalization
- >30 min remaining: WAIT
- <=30 min and before deadline: TRY
- invalid/unpublished exhibition or odds: retry later, do not finalize prematurely
- deadline passed without valid frozen decision: `ERROR_NO_BET`

2026-09-11 Naruto 3R was intentionally not retroactively scored after deadline. The earlier immutable final artifact remains safe/audit-only for that expired case.

## 9. Current production operating procedure
Primary route:
`06:00 daily build (06:30 fallback) -> 144/144 capable current-input fetch with adopted Waku10 fallback -> frozen daily artifact -> 5-minute auto watcher -> PRE candidates only -> official deadline -> WAIT/TRY/EXPIRED -> if TRY, exhibition + exact 120 odds -> v242/v243 -> v288 S/A/B -> 5-10 points -> exact 10k Dutch -> immutable final artifact`.

Manual fallback:
- `.github/workflows/live-3head-v288-production.yml`
- use only with the same target-day frozen daily artifact.

## 10. Immediate next priority
Waku10 all-race coverage is solved for the audited 2026-09-11 case and the fallback is formally adopted.

Next operational priority is the first future PRE candidate whose daily cache exists before exhibition/deadline. Allow that race to flow through the real TRY branch and verify end-to-end:
- current exhibition/start/original exhibition
- official exact 120 trifecta odds
- v242/v243
- corrected v288 S/A/B
- variable 5-10 tickets
- exact 10,000 JPY Dutch
- immutable final artifact before deadline

Do not tune from July/August outcomes and keep September outcome-blind.

## Important files
- `CHAT_HANDOFF_20260911_3HEAD_V288_PRODUCTION.md`
- `historical_waku10_fetcher.py`
- `fetch_3head_v288_pre_inputs_live.py`
- `build_3head_v288_daily_live.py`
- `run_3head_v288_production_live.py`
- `run_20260911_3head_v288_live.py`
- `fetch_boatrace_deadline.py`
- `fetch_live_trifecta_odds.py`
- `.github/workflows/verify-waku10-live-fallback.yml`
- `.github/workflows/daily-3head-v288-production.yml`
- `.github/workflows/auto-live-3head-v288-production.yml`
- `.github/workflows/live-3head-v288-production.yml`
- `verify_v288_operational_pre_replay.py`
- `OFFICIAL_3HEAD_V288_100R_ADOPTED_20260911.md`

## Recommended next-chat opening
`boatrace-backtest の CHAT_HANDOFF_20260911_3HEAD_V288_PRODUCTION.md と最新GitHubを読んで続き。最新GitHub優先。3号艇v288のWaku10は Kyoteibiyori primary + 検証済みBOATCAST direct fallback を正式採用済みで、2026-09-11は144/144 PRE入力・候補は鳴門3Rの1件のまま確認済み。daily cache -> auto watcher -> fail-closed final artifact のproduction運用を続けて。7月8月NON-PRISTINE、9月outcome blindを厳守。`
