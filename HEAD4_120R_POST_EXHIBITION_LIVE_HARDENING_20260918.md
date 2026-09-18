# HEAD4 120R post-exhibition LIVE hardening — 2026-09-18

## User concern
展示後判定で毎回エラーになったり、処理が遅く締切に間に合わない問題を解消する。

## September operational rule
User explicitly approved completed prior September results for live learning/history.
Causality:
- target_date-1までの完了結果: 使用可
- 対象レース結果/払戻: 判定前は使用禁止
- future data: 使用禁止

## Architecture change
The 120R last-minute rule does NOT run the full legacy POST/ENV/A chain.

Fast path:
1. daily causal state prepared once
2. pre-arm before exhibition
3. fetch exhibition sources in parallel
4. frozen v283 opponent inference
5. THIRD .10 ticket expansion + opponent_mass
6. pre-deadline trifecta odds
7. 120R BET/PASS rule
8. fail closed if data are not ready before safety margin

## Once-daily state
`prepare_4head_120r_daily_state.py`
- history through 2026-09-17
- 47,520 settled prior races
- 1,641 players
- Sep prior dates included
- target-date results not read
- local sparse checkout, no serial 350-day raw HTTP loop

Measured state build:
- 3.52 sec in Run 35322680749
- 4.16 sec in Run 35323003067
This is a once-per-day cost, not a race-time cost.

## Errors found and fixed during live trial
1. heavy legacy market-module import pulled pandas-heavy unrelated path
   - decoupled from legacy module
   - commit `ff20145878430e930634814bed3f6571893dd864`
2. stale `live.require_before_deadline` / `live.ALPHA2` references after decoupling
   - commit `5f669defbc6ab8fba608719a07e274845490bc13`
3. v283 TOP4 tuple vs added string ticket type mismatch
   - commit `d51f0d7c6fa0cb813ac1da4e43e188f1ab569a3d`
4. BOATCAST original-exhibition wrapped record handling
   - fix `02af3c2c09933d6612ef823b7b76f9d289ca4908`
   - test `ff0d529f1bea39868bf7083766c6661e368a7af4`
5. BOATCAST od3 text was decoded by requests' guessed encoding.
   Mojibake inserted a Unicode line separator inside Japanese racer names,
   splitting the sixth row and producing false "od3 row incomplete".
   - force UTF-8-sig decoding
   - commit `5b2a504f58964999c39c6a03565375ae908a04bc`
6. odds sources were attempted serially, stacking timeout latency.
   - official odds3t and BOATCAST are now polled in parallel
   - first complete 120-combo snapshot wins
   - commit `e131abfd14a38d78abd65834f1219c407a439832`

## BOATCAST od3 format verification
Observed live format:
- 8 lines
- line0 `data=`
- line1 `1`
- lines2..7 = racer name + 20 trifecta odds + 5 trailing zero fields

Diagnostic Run:
- Run `35323673970` SUCCESS

Hardened parser verification:
- Run `35324173389`
- Job `105533279813`
- conclusion **SUCCESS**
- fixture 120/120
- current 大村6R live 120/120
- combo ordering fixture checked, including:
  - 1-2-3
  - 1-2-4
  - 1-2-5
  - 1-2-6
  - 4-1-2 etc.

## Live full-path benchmark — 丸亀6R
Run:
- `35324180062`
- Job: `105533301948`
- conclusion: **SUCCESS**
- Artifact: `10538226164`
- digest: `sha256:00acc48a7671f800f88adc6bf18910d8646e77aa0801d3cdc1ec555f1500e64d`

This race was NOT in the monitoring parent, so output is correctly labeled
`BENCHMARK_ONLY`; it validates infrastructure/timing, not a live recommended bet.

Timing:
- workflow fast-run start: ~17:24:25 JST
- final decision frozen: 17:25:03.355 JST
- race deadline configured: 17:34 JST
- total runner: **36.884 sec**
- of which exhibition wait/fetch/build: **33.621 sec**
  - runner was deliberately started before exhibition became available
- v283 input build: **0.00034 sec**
- v283 inference: **0.00164 sec**
- live odds fetch: **3.174 sec**
- once data are available, post-exhibition model+market path is therefore about **3.2 sec** in this trial.

Benchmark scores:
- head_prob .07504
- opponent_mass .41208
- composite_odds 76.98
- linear score .69316
- selected false
- correct label: `BENCHMARK_ONLY`
- odds source: BOATCAST live od3 fallback
- target-race result/payout not used.

## Operational conclusion
The model computation is NOT the current latency bottleneck.

Recommended operation:
- pre-arm the runner before exhibition, rather than launching after exhibition;
- use daily-state cache;
- poll exhibition with bounded retries;
- once exhibition is ready, v283 is effectively instantaneous;
- fetch official odds3t + BOATCAST in parallel;
- fail closed by safety margin rather than hanging until deadline.

Current tested safety defaults:
- exhibition safety: T-60 to T-75 sec
- odds safety: T-30 to T-45 sec

The successful Marugame benchmark finished nearly 9 minutes before its deadline.

## Remaining validation
Before calling the 120R path production-proven:
- execute at least one true monitored-parent race end-to-end (not `--allow-unmonitored-benchmark`);
- preserve the exact same fail-closed timing behavior;
- update the PRE/head-prob operational training policy if September labels are incorporated into those models, because changing head_prob calibration changes the historical 120R threshold semantics.

Production remains unchanged.

Status:
`HEAD4_120R_LASTMINUTE_FAST_PATH_INFRA_SUCCESS__MONITORED_LIVE_CONFIRMATION_NEXT`
