# Chat handoff — 2026-09-11 3-head v288 PRODUCTION

Updated: 2026-09-11 JST
Repository: `merry02180218-ai/boatrace-backtest`

## READ THIS FIRST IN THE NEXT CHAT
This file is the primary handoff for the current 3-head v288 production operation. Read this plus the latest GitHub commits before doing any prediction, model change, or live-run change. If any older chat/memory/file conflicts with current GitHub, current GitHub wins.

Hard rules:
- July/August 2026 are NON-PRISTINE / contaminated model-selection periods.
- Never use result, payout, or post-deadline data to reconstruct a pre-deadline prediction.
- Do not rebuild heavy history/model state at race deadline.
- The deadline path must be cache-first and fast.

## 1. Current production interpretation of v288
Historical adopted v288 100R result is now independently reproducible under the correct route semantics:
- 100R
- 56 hits
- hit rate 56.00%
- stake 1,000,000 yen
- payout 1,743,810 yen
- profit +743,810 yen
- ROI 174.381%

However, the historical PRE used month-internal percentile, which is not strictly reproducible in true live operation because it depends on the full month universe. Therefore do NOT use 174.381% as the main production expectation.

The production-compatible, leakage-free PRE replay is now the operational reference:
- 94R
- 52 hits
- hit rate 55.319%
- stake 940,000 yen
- payout 1,622,070 yen
- profit +682,070 yen
- ROI 172.561%

Route breakdown for the production-compatible replay:
- S: 55R / 33 hits / 60.00% / payout 1,012,340 / profit +462,340 / ROI 184.062%
- A: 21R / 10 hits / 47.619% / payout 313,240 / profit +103,240 / ROI 149.162%
- B: 18R / 9 hits / 50.00% / payout 296,490 / profit +116,490 / ROI 164.717%

Monthly production-compatible replay:
- 2026-02: 8R / 5 hits / ROI 198.138%
- 2026-03: 12R / 7 hits / ROI 175.317%
- 2026-04: 12R / 8 hits / ROI 200.608%
- 2026-05: 16R / 10 hits / ROI 192.513%
- 2026-06: 14R / 7 hits / ROI 153.436%
- 2026-07: 13R / 3 hits / ROI 87.123%  <-- NON-PRISTINE
- 2026-08: 19R / 12 hits / ROI 198.084% <-- NON-PRISTINE

Workflow proving the production-compatible replay:
- run `34560827602`
- workflow `verify-v288-operational-pre-replay`
- ended `success`
- log marker: `V288_OPERATIONAL_PRE_REPLAY_OK`

## 2. Correct v288 route semantics — MUST NOT REGRESS
A previous live-run implementation incorrectly required `v243 pass` for A/B. That was too strict and did not match the adopted backtest.

Correct semantics are:

### S
S is the fixed core and requires v243 final/purchasable pass PLUS all S thresholds:
- `f__c_b3_minus_b4_waku_st <= 0.4999999999999999`
- `f__c_b3_minus_b4_st >= -0.6`
- `f__c_b3_meetst <= 0.861111111111111`

### A
A is an independent rescue outside S. It does NOT require v243 pass. It does require the race to be in the PRE S+A / v242-purchasable live universe, then:
- `f__c_b3_minus_b4_st >= 0.6`
- `f__c_wall12_weak <= 0.24875`

### B
B is an independent rescue outside S and A. It does NOT require v243 pass. It does require the race to be in the PRE S+A / v242-purchasable live universe, then:
- `f__c_b3_minus_b2_motor >= 0.22388571428571424`
- `f__c_b3_inside_nst <= -0.0714285714285712`

Precedence is exactly:
**S -> else A -> else B -> else NO BET**

Backtest replay proving historical adoption values under the corrected route semantics:
- historical 100R replay now reproduces S=58R, A=24R, B=18R and combined payout 1,743,810 exactly.

LIVE route parity test:
- workflow run `34560454539`
- success
- marker `V288_LIVE_ROUTE_PARITY_OK cases=32`
- production `select_v288_route()` matched the reference semantics on all 32 boolean combinations.

## 3. Production-compatible PRE — key change
Old historical v249 PRE grades used month-internal percentile ranking. That uses the whole test month and is therefore not a valid strictly-live procedure.

The live production PRE now uses only prior training-universe information:
1. Train/fit the PRE score using only historical data available before the current test month/day.
2. Compute fixed score cutpoints from the prior training universe only:
   - S threshold = 70th percentile of prior training-universe scores.
   - A threshold = 20th percentile of prior training-universe scores.
3. Score the current race with the same trained score function.
4. Grade independently of same-day/future races:
   - S if score >= S threshold
   - A if A threshold <= score < S threshold
   - B otherwise

For September 2026 the threshold logic must be derived strictly from data through 2026-08-31. Do not rank the current race inside the current-day candidate set.

Files changed for this:
- `scan_20260911_3head_v288_pre.py`
  - commit `9b6f2990eba7440867019db1274a4581d2787d15`
  - message: `Use leakage-free training-quantile PRE thresholds in live scan`
- `build_20260911_3head_v288_live_cache.py`
  - commit `888b4ede04ae08e957795ffaa9d0d67acf6cd994`
  - message: `Align live cache PRE grading with leakage-free replay`

The old field/idea `operational_pre_percentile_bridge=True` and target-day within-universe percentile must be considered superseded by the fixed training-quantile production approach.

## 4. FAST LIVE production operating procedure — MUST KEEP
The user explicitly requires practical speed. The old pattern of rebuilding 10-20 minutes of heavy history at deadline is unacceptable.

### Phase A — once before races / morning prebuild
Do all expensive work ahead of time and freeze a daily cache:
1. Build/load all historical prerequisite data.
2. Build current-day canonical PRE rows for all races.
3. Fit/load 3-head `head_model` and `pair_model` using only allowed historical data.
4. Compute leakage-free fixed PRE score thresholds from prior training-universe scores.
5. Score current-day races and store PRE grades/candidates.
6. Store model objects, feature lists/categories, current rows, PRE candidates, fixed thresholds, ST bias, and expensive derived prerequisites in one reusable daily `joblib` cache.
7. Build this cache once per day/model version, not once per race.

If the daily cache is unavailable near a race deadline, do NOT start a heavy rebuild and pretend the decision is LIVE-capable.

### Phase B — race deadline path
After exhibition/current data appears, the live runner should do only:
1. Load daily cache.
2. Fetch current BOATCAST exhibition/start/original data for that race.
3. Freeze requested/fetched timestamps, URLs, and hashes BEFORE deadline.
4. Update only that race's canonical current features.
5. Fetch official BOAT RACE 3連単 odds and require exact 120/120 combinations.
6. Freeze odds timestamp/hash BEFORE deadline.
7. Score using cached models; no fitting here.
8. Apply canonical v242 purchasability / v243 core logic as required.
9. Apply corrected v288 route semantics: S -> A -> B.
10. Build variable 5-10 ticket set with v242.
11. Allocate exactly 10,000 yen using canonical inverse-odds Dutch/Hamilton rounding.
12. Immediately print BET/NO BET, route, decisive feature values/thresholds, raw/purchased TopN, composite odds, each ticket/odds/stake, total stake.
13. Hard-fail to `ERROR_NO_BET` if deadline is crossed, exhibition is invalid, or odds are not exactly 120/120.
14. Never query/use result or payout endpoints.

Operational one-liner:
**Morning: heavy build/cache. Deadline: cache load -> exhibition -> official 120 odds -> v242/v243 -> corrected v288 S/A/B -> 5-10 tickets -> 10,000-yen Dutch -> print.**

## 5. Proven speed reference
Cached smoke proof from 2026-09-10:
- runner `run_20260910_3head_live_from_cache.py`
- cache load ~0.005 sec
- two races completed in ~20.265 sec total
- no historical reconstruction/model fitting in deadline path

Observed smoke output:
- Kojima 5R: FINAL=False
- Naruto 7R: FINAL=True
- Naruto7 tickets: 3-1-6 3400 / 3-1-4 1300 / 3-6-1 2200 / 3-4-6 1000 / 3-1-2 800 / 3-6-4 1300 = exactly 10,000 yen

This smoke was post-deadline and is only architecture/performance proof, not valid betting evidence.

## 6. Current-day 2026-09-11 state
Earlier old-bridge scan had only Naruto 3R as PRE candidate, but that scan used the now-superseded target-day percentile bridge. Do not use that candidate list as proof of the new production PRE behavior.

After commits `9b6f2990...` and `888b4ede...`, a new `scan-20260911-3head-v288-pre` run was triggered:
- newest run seen: `34560960164`
- at last check it was still in progress during dependency/install/input-build steps.

NEXT CHAT MUST FIRST check the latest status/artifact of this run (or the latest successful run on the same workflow/commit) before using today's PRE candidates. Do not assume Naruto3 remains the only candidate under the new leakage-free PRE.

## 7. Current important LIVE files
Inspect latest GitHub versions before changing anything:
- `run_20260911_3head_v288_live.py`
- `build_20260911_3head_v288_live_cache.py`
- `scan_20260911_3head_v288_pre.py`
- `fetch_live_trifecta_odds.py`
- `.github/workflows/live-3head-v288-from-daily-cache.yml`
- `.github/workflows/scan-20260911-3head-v288-pre.yml`
- `verify_v288_3head_100r_replay.py` and/or corrected replay verifier
- `verify_v288_operational_pre_replay.py`
- `OFFICIAL_3HEAD_V288_100R_ADOPTED_20260911.md`
- `docs/FEATURES_THAT_WORKED_3HEAD_V288_20260911.md`

## 8. User expectations for next chat
- Execute directly; minimal chatter.
- Always read actual latest GitHub before prediction or model changes.
- Latest GitHub overrides older memory and older handoff files.
- Do not claim finished until an actual GitHub Actions run/log/artifact verifies it.
- For model comparisons report race count, hits, hit rate, profit, ROI.
- Keep July/August explicitly NON-PRISTINE.
- No outcome leakage.
- Speed is part of correctness for real operation.

## 9. Immediate next actions for next chat
1. Read this handoff and latest GitHub.
2. Check latest `scan-20260911-3head-v288-pre` run after commit `888b4ede...` and download/inspect its artifact if successful.
3. Confirm current PRE candidate list under leakage-free training-quantile thresholds.
4. Inspect current `run_20260911_3head_v288_live.py` and make sure it consumes the corrected cache/PRE semantics and corrected S/A/B semantics.
5. Run an end-to-end production smoke using a race with available frozen exhibition + complete 120/120 odds, keeping it result-blind.
6. Measure deadline-path elapsed time. Target approximately <=20 sec per race if network conditions allow.
7. If anything differs between historical verifier and live runner, fix live first and add/extend CI parity tests.

## Recommended next-chat opening prompt
`boatrace-backtest の CHAT_HANDOFF_20260911_3HEAD_V288_PRODUCTION.md と最新GitHubを読んで続き。特に実運用を優先して、未来情報なしPRE（過去training scoreの70%/20%固定閾値）、朝1回daily cache、締切時はcache load -> 展示 -> 公式120オッズ -> v242/v243 -> 正しいv288 S/A/B独立救済 -> 5〜10点 -> 1万円Dutchのみを厳守。まず最新の2026-09-11 PRE scan結果とcacheを確認し、その後end-to-end LIVE smokeを実行して。7月8月はNON-PRISTINE、結果/払戻/締切後データは予測に絶対使わない。`
