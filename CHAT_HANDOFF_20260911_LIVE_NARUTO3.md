# Chat handoff — 2026-09-11 LIVE Naruto 3R / v288

Updated: 2026-09-11 JST
Repository: `merry02180218-ai/boatrace-backtest`

## Next-chat startup
Read this file plus `OFFICIAL_3HEAD_V288_100R_ADOPTED_20260911.md`, `docs/FEATURES_THAT_WORKED_3HEAD_V288_20260911.md`, and latest GitHub commits. Latest GitHub wins. Do not use result/payout/post-deadline information to reconstruct a pre-deadline prediction.

## Official 3-head model now adopted
The user formally adopted the 100-race v288 expansion on 2026-09-11. This supersedes the older 58R-only/core-only operational description where conflicting.

Chain:
**v249 PRE S+A -> v243 final/purchasable universe -> v288 route S/A/B -> v242 variable 5-10 tickets -> exactly 10,000 yen Dutch**.

### Route S fixed core
- `f__c_b3_minus_b4_waku_st <= 0.4999999999999999`
- `f__c_b3_minus_b4_st >= -0.6`
- `f__c_b3_meetst <= 0.861111111111111`
Historical: 58R / 34 hits / 58.62% / payout 1,048,340 / profit +468,340 / ROI 180.75%.

### Route A outside S
- `f__c_b3_minus_b4_st >= 0.6`
- `f__c_wall12_weak <= 0.24875`
Incremental: +24R / 13 hits / 54.17% / ROI 166.24%.

### Route B outside S+A
- `f__c_b3_minus_b2_motor >= 0.22388571428571424`
- `f__c_b3_inside_nst <= -0.0714285714285712`
Incremental: +18R / 9 hits / 50.00% / ROI 164.72%.

Combined v288 historical/model-selection evidence:
100R / 56 hits / 56.00% / stake 1,000,000 / payout 1,743,810 / profit +743,810 / ROI 174.381%.
July/August remain NON-PRISTINE; all historical figures are model-selection evidence, not pristine validation.

Official adoption file: `OFFICIAL_3HEAD_V288_100R_ADOPTED_20260911.md` commit `81534f88ee2acf9ba0a28241f0ddf4be3fad3966`.
Effective feature ledger: `docs/FEATURES_THAT_WORKED_3HEAD_V288_20260911.md` commit `174f95c35722d103d5598de8f7e1b659380731b9`.
Expansion playbook: `MODEL_EXPANSION_PLAYBOOK_CORE_PLUS_INDEPENDENT_ROUTES.md` commit `baa552917053c27b6aaeff451bffb2379f75d66c`.

## 2026-09-11 PRE scan
Current-day inputs were successfully sourced from Kyoteibiyori, including `player_kako10` for Waku10-like past-10 data. Scripts:
- `fetch_kyoteibiyori_v288_pre_inputs.py`
- `scan_20260911_3head_v288_pre.py`
- `.github/workflows/scan-20260911-3head-v288-pre.yml`

Successful run `34543376351`, job `103090677351`, artifact `10178694689`.
132/144 races had complete Waku10 inputs.
Only PRE candidate for 2026-09-11 was **鳴門3R (JCD14 R3)**:
- PRE grade S
- operational percentile 1.000
- p3 0.463
- b3-b2 motor +0.460
- b3 inside NST +0.143

Caveat: historical v249 grades use within-month percentile. Live 9/11 scanner used target-day v243 candidate-universe ranking as an operational bridge. Do not call it exact historical percentile replication.

## Naruto 3R exhibition captured before deadline
BOATCAST/current exhibition data were obtained before the 09:36 deadline. Values reported in chat:
- 1: ST .09 / exhibition 6.83 / lap 37.11 / turn 5.83 / straight 7.03
- 2: ST .26 / exhibition 6.84 / lap 37.63 / turn 5.73 / straight 7.26
- 3 今井美亜: ST .02 / exhibition 6.73 / lap 37.80 / turn 5.77 / straight 7.13
- 4: ST .15 / exhibition 6.88 / lap 38.13 / turn 6.13 / straight 7.23
- 5: F.05 / exhibition 6.80 / lap 37.13 / turn 6.10 / straight 7.17
- 6: F.11 / exhibition 6.86 / lap 37.43 / turn 5.80 / straight 7.13

Boat 3 had top exhibition ST (.02) and top exhibition time (6.73), but the formal v243/v288 end-to-end final decision was NOT completed before deadline. Do not retroactively label this a valid live BET after seeing results.

Official BOAT RACE schedule confirms 2026-09-11 Naruto 3R deadline 09:36 and entrants: 1藤原早菜, 2新田芳美, 3今井美亜, 4森下愛梨, 5出口舞有子, 6浜田亜理沙.

## Odds fetch debugging / status
Existing official odds parser: `fetch_live_trifecta_odds.py`.
It requires CLI args:
`python fetch_live_trifecta_odds.py --date YYYYMMDD --jcd JJ --race R --out OUTPUT_DIR`

Initial workflow `.github/workflows/probe-20260911-naruto3-odds.yml` incorrectly used `--stadium 14`, causing failure. Fixed commit:
`f04b6d988cfe333fb3a0c95cf318daa71305689f` (`Fix Naruto 3R live odds CLI args`).

Re-run `34548432395`, job `103105998123` successfully fetched official BOAT RACE 3連単 odds **120/120 complete** at 09:54:21 JST, after the 09:36 deadline. Metadata:
- source: BOAT RACE official odds3t only
- resolved URL params rno=3, jcd=14, hd=20260911
- parsed_count=120, expected_count=120, complete=true
- result_endpoint_requested=false
- payout_endpoint_requested=false
- usable_for_betting=true at parser level

IMPORTANT: because snapshot time 09:54 is after deadline, it is NOT a valid pre-deadline live betting snapshot for Naruto3R and must not be used to claim what would have been bought before 09:36.

The workflow still ended failure only because it then ran `head -20 naruto3_odds.csv` even though `--out naruto3_odds.csv` is treated as a directory. The actual generated CSV path was under that directory, e.g. `naruto3_odds.csv/odds3t_20260911_jcd14_r03_...csv`. Fix the workflow to treat `--out` as a directory, or use `find` to locate generated CSV. The odds fetch itself succeeded.

## Immediate next implementation task
User requested that the operational flow be made fast and end-to-end. Build/repair a single LIVE runner that performs:
1. Fetch current exhibition/BOATCAST data for the selected PRE candidate.
2. Freeze it before deadline.
3. Fetch official 120/120 trifecta odds before deadline and freeze timestamp/hash.
4. Build current canonical features with existing repo code; do not infer feature scaling from names.
5. Apply v243 final/purchasable logic exactly.
6. Apply v288 route S -> else A -> else B -> else NO BET.
7. If selected, run v242 variable 5-10 ticket construction.
8. Allocate exactly 10,000 yen via canonical inverse-odds Dutch/Hamilton rounding.
9. Print immediately: `BET/NO BET`, route, decisive feature values/thresholds, raw/purchased TopN, composite odds, tickets, odds, stakes, total 10,000.
10. Hard-fail if deadline passed before the snapshot or if 120 odds are incomplete. Never fall back to result/payout/post-deadline data.

Performance requirement: user complained that 15 minutes is unacceptable. Cached LIVE proof previously ran ~20.265 sec. Keep deadline path fast: prebuild/cache expensive historical/current-row prerequisites before exhibition; deadline step should only fetch current exhibition + odds and execute downstream scoring/ticket logic.

Relevant existing files to inspect/reuse:
- `build_20260910_3head_live_cache.py`
- `run_20260910_3head_live_from_cache.py`
- `fetch_live_trifecta_odds.py`
- `analyze_v243_3head_expand_feature_audit.py`
- `analyze_v242_3head_target_comp3_min5_max10.py`
- `fetch_kyoteibiyori_v288_pre_inputs.py`
- `scan_20260911_3head_v288_pre.py`

## User operating preferences
- Execute directly; minimal chatter.
- Always inspect actual latest GitHub before prediction/model change.
- Do not reread all history every turn; read this handoff + latest relevant files/commits.
- When user says `お願いします`, perform the stated next step.
- Do not claim completion until code/run/results actually verify it.
- For model comparisons always report race count, hits, hit rate, profit, ROI.
- Keep July/August explicitly NON-PRISTINE.

## Recommended next-chat opening
`boatrace-backtest の CHAT_HANDOFF_20260911_LIVE_NARUTO3.md と OFFICIAL_3HEAD_V288_100R_ADOPTED_20260911.md と最新GitHubを読んで続き。鳴門3Rで判明したオッズ取得バグを直し、展示→公式120オッズ→v243→v288 S/A/B→v242 5〜10点→1万円Dutchを締切前に高速で1本実行できるLIVE runnerを完成させて。結果/払戻/締切後データは予測に絶対使わない。`