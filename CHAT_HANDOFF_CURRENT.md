# Chat handoff — canonical current state

Updated: 2026-09-09 17:24 JST
Repository: `merry02180218-ai/boatrace-backtest`
Default branch: `main`

## Mandatory next-chat startup
1. Read this file first.
2. Then inspect actual latest repo files/commits/results through GitHub before any prediction, judgment, backtest conclusion, audit, or model change.
3. Latest GitHub file/commit supersedes older chat/memory when they conflict.
4. Never calculate a LIVE prediction from memory alone. Run the actual current program with current inputs.
5. Freeze prediction/tickets before result/payout/post-deadline information.

## CRITICAL — JULY/AUGUST ARE NON-PRISTINE
2026-07 and 2026-08 have been repeatedly inspected and MUST NOT be used as pristine validation/model-selection evidence. They may be used only as descriptive/shadow/sanity-check periods. Do not adopt thresholds, PRE rules, opponent rules, point-count rules, odds filters, or model changes because they work on Jul/Aug.

## ROI / staking definition — mandatory
- Exactly 10,000 yen total stake per selected race.
- Dutch allocation inverse to odds.
- 100-yen units with Hamilton/largest-remainder rounding; total exactly 10,000 yen.
- Zero-stake tickets are not purchased.
- Composite odds: `O_combined = 1 / sum(1/o_i)`.
- Composite odds is a value feature, NOT ROI itself.
- Realized ROI = total payout / (settled selected races * 10,000).
- Losing race payout=0 and profit=-10,000 yen.
- Canonical implementation: `analyze_v205_3head_operational_replay.py::round_dutch`.

## Current production/model context
### 1-head
Canonical chain: Legacy PRE -> v109 S-only -> v162 Top7. Re-fetch latest files before live use.

### 3-head
Main current research line is v165/v166 -> v219+ redesign work. v165 uses current exhibition/direct margins and prior-safe features; target boat 3 must exhibit course 3. v166 direct ordered-pair model ranks opponents. Production history used p3head>=.30 and Top10, but newer research has NOT established a replacement production rule.

### 4-corner / 5-head
Models exist. Re-fetch exact latest repo rules before use; do not infer from old chat.

## Strict contamination protocol
- Jul/Aug 2026 are NON-PRISTINE.
- Dec2025-Jun2026 has also been used extensively for feature/rule discovery. Any threshold discovered on it is selection-contaminated and must not be called pristine.
- Use monthly prior-only where specified.
- Historical odds used for settlement must not be represented as pre-deadline live odds unless actually captured pre-deadline.

## v219-v225 research progression
v219 showed v166 pair ranking/calibration was relatively strong while head/race selection was weak.
v220 added player/prior history; player traits improved head discrimination and PRIOR12 improved ROI.
v221 scenario-aware pair ranking improved conditional opponent coverage/ROI direction.
v222 broad current+relative feature audit raised research ROI to 87.34%.
v223 national recent 5-meet form raised it to 89.88%.
v224 FULL_DECOMP/RECENCY_CONTEXT reached 90.77% on the then-existing Dec-Jun data, but only 2/7 profitable months.
v225 weight/entry combinations did not beat v224; v224 remained research baseline.

## v226-v228 odds exploration — IMPORTANT CAVEAT
User allowed closing-odds selection for one exploratory experiment only. Fixed Top10 plus value skipping looked strong in Dec-Jun: e.g. comp>=3.0 ROI 115.37%; comp[3.0,3.25) v227/v228 was R23, hit52.2%, ROI163.2%. Dynamic BEST_N maxEV failed.
These results are exploratory/selection-contaminated and MUST NOT be production rules.

Later audit found a critical odds-source definition issue: `v205.load_odds()` loads official closing plus BoatraceCSV `previews/od3`, then duplicate handling can prefer od3. Upstream od3 is a realtime preview snapshot typically around 5 minutes before deadline, NOT guaranteed final closing odds. In v229 selected rows, July used a mixture of od3/official while August used od3 for 103/103 settled selected races and zero official closing. Therefore v226-v229 odds-zone conclusions are not true uniform closing-odds experiments and must be treated cautiously.

## v229 Jul/Aug NON-PRISTINE shadow
After fixing a period-boundary builder bug, final v229 results were poor:
- ALL Top10 Jul+Aug: R189, hit30.69%, ROI69.04%.
- comp>=2.5: ROI58.15%.
- comp>=2.75: ROI67.82%.
- comp>=3.0: ROI45.94%.
- comp[3.0,3.25): R5, 0 hits, ROI0%.
- EV>=1.20: ROI71.09%.
Thus the Dec-Jun odds-zone signal did not reproduce even as a NON-PRISTINE sanity check.

## v230 data-integrity / failure decomposition
v230 decomposed Jul/Aug Top10 hit collapse:
- Jul R86: actual 3-head34.88%, Top10 hit26.74%, pair coverage given 3-head76.67%, mean p3 .5104.
- Aug R103: actual 3-head45.63%, Top10 hit33.98%, pair coverage74.47%, mean p3 .5950.
- Combined R189: actual 3-head40.74%, pair coverage75.32%, final hit30.69%.
Main failure was head/p3 overprediction; pair ranker degradation was secondary.

## July half-year boundary hypothesis
Official BOAT RACE information confirms:
- 2026 first-half grade applies 2026-01-01 through 2026-06-30.
- 2026 second-half grade applies 2026-07-01 through 2026-12-31.
Thus July 1 is a genuine racer-grade/period boundary. This is a hypothesis for regime shift, not yet a proven causal explanation.

## v232 July regime-shift audit
Frozen v224-like selected-race head calibration before Waku10 restoration:
- May: avg p3 52.06%, actual 3-head57.14%, gap -5.09pp.
- Jun: 53.31% vs47.95%, gap +5.36pp.
- Jul: 51.08% vs35.63%, gap +15.45pp.
- Aug: 59.71% vs44.55%, gap +15.16pp.
Largest Jun->Jul feature shifts were current/player-stat-like fields, especially `waku_wr`, `waku_sr`, `pastwin` and relative versions. Suspiciously, many Waku-related June means were exact defaults/zeros and became populated in July.

## Waku10 root cause
`backtest.py::race_features` uses `data/programs/waku10/YYYY/MM/DD.csv`.
- missing `waku_wr` -> default 0.
- missing `waku_sr` -> default 3.5, transformed by current builder to 0.5.
- no past 10-race placements -> `past_win=0`.
This exactly explained suspicious pre-July feature defaults.

Waku10 source is Boatcast `bc_j_waku10`; BoatraceCSV path is `data/programs/waku10/YYYY/MM/DD.csv`.

## v233 Waku10 coverage/backfill audit
Original slow v233 was replaced by a parallel/short-timeout version.
Successful run: `34324515336`, artifact `10093518025`.
Coverage audit showed BoatraceCSV Waku10 availability:
- 2025/12: 0/31 published; Boatcast recoverable 31/31.
- 2026/01: 0/31; recoverable31/31.
- 2026/02: 0/28; recoverable28/28.
- 2026/03: 0/31; recoverable31/31.
- 2026/04: 0/30; recoverable30/30.
- 2026/05: 0/31; recoverable31/31.
- 2026/06: 0/30; initial audit recoverable29/30; 6/17 needed deeper recovery.
- 2026/07: 13/31 published; remaining18/18 recoverable.
- 2026/08:31/31 published.
Total 8,883 original Boatcast Waku10 files recovered in v233 audit. No arbitrary imputation permitted.

## v234 — CURRENT CRITICAL RESULT: restored Waku10 replay
Implementation/workflow commits:
- script commit `09edebd3727bdf75f2ce4fef9ce24585530af355`
- workflow commit `f00b4afb44de818e9966425df99bfe1d01ec3e25`
Successful workflow run: **34326743303**.
Artifact: **10094762062**, `v234-3head-waku10-restored-replay`.

v234 procedure:
1. Reconstruct missing Waku10 into BoatraceCSV-compatible 208-column daily CSV from original Boatcast files.
2. Deep-search remaining missing dates/venues (including 2026-06-17) rather than impute.
3. Validate parser against already-published August Waku10.
4. Only after validation, rerun frozen v224 FULL_DECOMP-like head/pair replay across Dec2025-Aug2026.
5. Jul/Aug remain NON-PRISTINE.

### Reconstruction validation
Published August comparison: **156 races checked, 0 cell mismatches**. This strongly validates the reconstruction/parser method.
Historical Waku10 coverage was restored across the replay period; do not revert to default-zero Waku handling when genuine source data is available.

### v234 corrected v224-like results
Dec2025-Jun2026 aggregate after Waku10 restoration:
- R482
- Top10 hit **39.63%**
- conditional opponent Top10 coverage **81.97%**
- ROI **91.85%**
This is modestly better than old v224 ROI 90.77%, but still below 100% and is not pristine validation.

Key recent monthly calibration/results after restoration:
|month|avg p3|actual 3-head|p3 gap|Top10 hit|ROI|
|---|---:|---:|---:|---:|---:|
|2026-06|53.30%|45.21%|+8.10pp|34.25%|74.45%|
|2026-07|50.49%|39.08%|+11.41pp|27.59%|60.28%|
|2026-08|51.86%|47.71%|+4.16pp|35.78%|82.01%|

### v234 interpretation
Waku10 missing/default-imputation was a real material data bug, but NOT the entire July failure.
- Before restoration, July p3 overprediction gap was about +15.45pp; after restoration it is still +11.41pp.
- August improved dramatically from about +15.16pp pre-restoration to +4.16pp post-restoration.
Therefore:
1. Much of August's apparent calibration anomaly was caused by inconsistent/missing Waku10 handling.
2. July still has a genuine residual regime/calibration problem after Waku10 normalization.
3. Do NOT claim Waku10 fully explains July.
4. The user's July-1 second-half-season hypothesis remains plausible and is now the next audit target.

## NEXT TASK — v235 recommended
Audit the residual July-specific regime shift after Waku10 restoration. Do NOT tune a new rule yet.
Primary questions:
1. Which frozen v224 input families still change materially across Jun30 -> Jul1 after Waku10 normalization?
2. Audit grade/class fields and their source definitions at the official 2026 second-half switch.
3. Audit racer national/local stats and whether source/reference periods reset or change meaning on Jul1.
4. Audit race-card fields/fallbacks for schema/population changes at July boundary.
5. Separate genuine racer/regime changes from source-data definition changes.
6. Compare May/June/July/Aug calibration using corrected Waku10.
7. Do not derive/adopt thresholds from Jul/Aug; they remain NON-PRISTINE.
8. If another historical source is missing, search public/original sources and save exact values with provenance. Never fabricate/impute arbitrary values.

Only after v235 establishes the cause should model recalibration/redesign be considered. Any proposed new model must use an appropriate no-leak validation protocol and must not call Jul/Aug pristine.

## LIVE odds path status
A live odds-aware SHADOW infrastructure exists from v218 (`boatrace_live_odds3t.py` and shadow runner). It freezes live snapshots. However, current research focus moved to correcting the 3-head model/data before production adoption. Re-fetch latest live files before any live prediction.

## Recommended next-chat opening
`boatrace-backtest の CHAT_HANDOFF_CURRENT.md と最新GitHubを読んで続き。v234でWaku10を復元した結果を確認し、次はv235として7/1後期切替後も残る3号艇p3のキャリブレーション崩れを、級別・全国/当地成績・race-card統計期間・データ定義の変化に分解して監査して。7月8月はNON-PRISTINE厳守。`
