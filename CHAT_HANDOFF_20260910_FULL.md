# Chat handoff — 2026-09-10 FULL STATE

This file is the detailed handoff for the long ChatGPT session ending 2026-09-10 JST. Read `CHAT_HANDOFF_CURRENT.md` first, then this file, then inspect the actual latest GitHub files/commits/runs before any prediction, judgment, audit, backtest, or model change.

## Mandatory behavior
- Repository: `merry02180218-ai/boatrace-backtest`, default branch `main`.
- GitHub latest code/data/results supersede chat memory whenever they conflict.
- Never calculate LIVE predictions from memory alone. Run actual current code with current inputs.
- Freeze prediction/tickets/odds snapshots before result, payout, or post-deadline information.
- 2026-07 and 2026-08 are NON-PRISTINE/overfit. Dec2025-Jun2026 is also selection-contaminated. Historical optimization may include Jul/Aug only when clearly described as retrospective/in-sample evidence, never pristine future validation.

# CURRENT OFFICIALLY ADOPTED 3-HEAD MODEL
User formally adopted on 2026-09-10:
`v249 PRE S+A -> v243 exhibition/final selection -> v242 variable 5-10 tickets -> exactly 10,000 yen Dutch`.

## ROI / staking
- Exactly 10,000 yen total stake per selected/settled race.
- Inverse-odds Dutch.
- 100-yen units with Hamilton/largest-remainder rounding; total exactly 10,000.
- Zero-stake tickets are not purchased.
- Composite odds = `1 / sum(1/o_i)` and is a value feature, NOT ROI.
- Realized ROI = total payout / total settled stake.
- Losing race: payout=0, profit=-10,000.
- Canonical Dutch: `analyze_v205_3head_operational_replay.py::round_dutch`.

## v249 PRE
Script: `analyze_v249_3head_pre_rolling_sab_optimize.py`, SHA previously recorded `64c11edfbafaa78ce7d85d9dd6b7a5be9d9f1dd3`.
- Strict PRE excludes current-race exhibition-derived features.
- Historical grade boundaries: S percentile >=0.70, A >=0.20, B <0.20.
- Operational candidate set = S+A together. Do NOT stake S more strongly than A. B is not official candidate.
- Historical optimization: S+A candidates 388/480=80.83%, captured 104/119=87.39%.
- Historical S ROI 101.41%; A ROI 124.18%; therefore use combined S+A.

### LIVE-safety caveat discovered in v249
Historical v249 code ranks score percentile against all races in the same test month (`groupby('month').rank(pct=True...)`), so exact retrospective percentile is not directly LIVE-safe because future races in the current month are unknown.
User proposed using previous month + current month races available so far. Operational decision:
- Reference universe for LIVE percentile = all prior-month races + current-month races available through current time/day, using strict PRE/static info only.
- Never include future current-month races, current-race exhibition, result, or odds.
- Treat this as LIVE-safe operational implementation/bridge of v249 intent, not silently byte-identical historical v249 if feature/calibration differs.

## v243 canonical final rule
Canonical cached artifact/run: run `34383567078`, artifact `10118044294`.
Exact target reconstruction:
- base = `bet==1 & p3>=0.45 & raw_top_n 7..18 & comp_odds 3.05..4.0`
- keep base when `f__c_b3_minus_b5_st >= -0.1999999999999999`
- rescue outside base when `f__c_attack3_stretch <= 0.5672342857142857`
DO NOT round keep threshold to literal `-0.2`; that historically selects four extra races.
After exhibition, if v243 fails => official NO BET even if PRE S/A.

## v242 ticket stage
- Evaluate unconstrained TopN N=2..20.
- Pick N whose composite odds is closest to 3.00.
- raw N<5 => NO BET.
- raw N=5..10 => buy raw N.
- raw N>10 => cap purchase at Top10.
- Allocate exactly 10,000 yen with canonical Dutch.

## Adopted historical performance reference
Rolling Feb-Aug portion:
- PRE S+A + final purchase: 104 settled races, 39 hits, hit 37.50%.
- stake 1,040,000; payout 1,200,350; profit +160,350; realized ROI 115.42%.
- Without v249 PRE gate: 119 races, 44 hits, hit36.97%, ROI113.32%.
- Dropped B: 15 races, 5 hits, hit33.33%, ROI98.74%.
Monthly adopted-pipeline ROI: Feb226.44, Mar102.38, Apr216.80, May146.02, Jun67.52, Jul32.09, Aug117.39%. These are retrospective/model-selection evidence, NOT pristine future estimates.

# 2026-09-10 OFFICIAL DATA / PRE SCAN
Created earlier:
- `predict_v107_20260910_official_fullscan.py`
- `.github/workflows/v107-20260910-official-fullscan.yml`
Successful run `34433290521`, job `102733104859`, commit output `100b98d`.
Official racelist fetched directly; no result/payout/actual entry/current exhibition/current odds.
- 11 venues, 132/132 races, errors 0.
- venues: 桐生, 江戸川, 平和島, 多摩川, 尼崎, 鳴門, 児島, 宮島, 若松, 芦屋, 大村.
- prior same-frame waku history through 9/9: 787/792=99.4%.
- old v107 structural candidates 12 total; v107 is old structural PRE, NOT v249.

## 2026-09-10 v249 LIVE-safe operational bridge
Created `predict_v249_20260910_live_safe_operational.py` and workflow.
First run graded all 132 directly and was rejected as too broad (111 S+A).
Corrected design: frozen daily 3-head structural gate first, then percentile grading only candidate universe; reference = historical gated 2026-08-01..09-09 + current 9/10 gated races; no future Sep/current exhibition/result/odds.
Corrected successful run `34436927711`, job `102743843428`.
Frozen 9/10 PRE candidates:
1. 児島5R 3号艇 平田さやか A2 — route 3まくり, score 0.7118, pct 0.4286, grade A.
2. 鳴門7R 3号艇 今井美亜 A1 — route 3まくり, score 0.7097, pct 0.4184, grade A.
Caveat: LIVE-safe operational bridge, not exact full historical-v249 f__ feature reconstruction.

# PENDING TARGET-RACE TASK
User said both 児島5R and 鳴門7R had exhibition and races were already finished, but requested judgment WITHOUT looking at results. User noted ボートレース日和 is fast for exhibition information.
Required next work:
- Judge the two frozen PRE candidates using exhibition info and canonical v243, while avoiding result/payout data entirely.
- Target races: 児島5R 平田さやか; 鳴門7R 今井美亜.
- Need actual current exhibition/entry/course and v243 required fields.
- Because races are already over, contamination risk is high: use only pre-race exhibition/odds sources/fields; do not inspect result tabs/pages.
- Freeze extracted inputs before any result lookup.
- If exact pre-deadline odds snapshot is unavailable, do NOT falsely call post-race/closing mixture live pre-deadline odds. Can report partial exhibition-side evaluation but exact v243 requires its odds-dependent base variables.

# LIVE REAL-TIME TRIFECTA ODDS FETCHER — WORK JUST STARTED
User then said: if no archived realtime odds, devise realtime-odds acquisition code.
Implemented new file:
- `fetch_live_trifecta_odds.py`
Commit: `7fc870147268b574f450e662859f220a880841a6`.
Design intent:
- Access BOAT RACE official `odds3t` only, never result/payout endpoint.
- Fetch current 3連単 odds and save immutable timestamped snapshot.
- Require all 120 trifecta combinations before marking snapshot usable.
- Save acquisition timestamp, resolved URL/params, raw HTML SHA256, raw HTML, parsed CSV/metadata.
- Result/payout endpoints explicitly not requested.

Created smoke-test workflow:
- `.github/workflows/live-trifecta-odds-smoketest.yml`
Commit: `b32c16ccf261f0cd6ed34d7f2bc2442a7d6cccc0`.
Triggered push run:
- run `34442037812`
- job `102758918458`
- artifact `10138281552` named `live-odds3t-snapshot`.
The official HTTP request succeeded with status 200, resolved URL like `https://www.boatrace.jp/owpc/pc/race/odds3t?rno=1&jcd=01&hd=20260910`, but parser only extracted 9/120 combinations, so snapshot correctly failed validation and was marked `usable_for_betting=false` with exit code 2. This is a PARSER FAILURE, not an HTTP acquisition failure.
Raw HTML was preserved in artifact. Artifact ZIP was downloaded in the ending chat to `/mnt/data/live-odds3t-snapshot.zip`, but that local path is chat-runtime only and should not be relied upon next chat. Use GitHub artifact `10138281552` if needed.

## Immediate next task for odds fetcher
1. Download/read artifact `10138281552` raw HTML.
2. Inspect actual BOAT RACE odds3t DOM/table structure.
3. Fix `fetch_live_trifecta_odds.py` parser to extract exactly all 120 ordered trifecta combinations and odds.
4. Re-run smoke test on a currently available non-target race; do not use target race result pages.
5. Require exact 120/120 before `usable_for_betting=true`.
6. Once stable, integrate snapshot into v242 ticket stage so odds are frozen before TopN/composite-odds/Dutch calculation.
7. Prefer capturing multiple snapshots near purchase time if operationally useful, but the specific snapshot used for the official ticket must be frozen and identified.

# v245 FIRST-DAY / NEW-MOTOR AUDIT
Successful run `34399551492`, artifact `10124251615`.
Canonical v243 policy reproduced 182 races.
- day metadata coverage 98.90%; meeting-start 98.90%; official-web fallback 108 rows; new-motor classification coverage 0%.
Overall:
- ALL_182: 182R, hit38.46%, ROI119.73%.
- EXCLUDE_FIRST_DAY: 161R, hit39.13%, ROI122.20%.
- EXCLUDE_NEW_MOTOR_MEETING: same as ALL due 0% classification.
- EXCLUDE_BOTH: same as first-day exclusion.
First-day exclusion historically improves 119.73 -> 122.20, but before formal production adoption apply to full adopted `v249 -> v243 -> v242` pipeline and recompute exact monthly/new ROI. Do not silently alter official model yet.

# NEW 4-HEAD MODEL REBUILD
User requested rebuilding 4-head model using successful 3-head architecture conceptually, not blindly copying thresholds/ticket settings.
Desired architecture:
1. predict boat4 win (`p4head`)
2. strict PRE candidate layer
3. POST/exhibition final gate
4. ordered-pair ranking for 4-?-?
5. 4-head-specific ticket strategy
6. exactly 10,000-yen Dutch.
Do NOT automatically reuse 3-head target composite odds 3.0 or 5-10 ticket bounds.

## v250 baseline
Successful run `34401238001`, fix commit `1229e3...`.
Monthly PRE/POST AUC and rows/head rate:
- Feb .7130/.7170 R4100 head10.71
- Mar .7029/.7079 R4607 9.42
- Apr .7287/.7296 R4244 9.45
- May .7199/.7256 R4832 9.42
- Jun .6925/.7004 R4488 9.36
- Jul .6317/.6367 R4920 9.84
- Aug .6770/.6890 R4920 9.76
Simple threshold diagnostics: PRE .40 => 214R/87 heads/40.65%; POST .40 =>275R/113 heads/41.09%.

## v251-v260 research summary
- v252 best small gate PRE.30 POST.30 N2: 80R ROI141.57, Feb-Jun61R ROI122.07, but user said too few.
- v253: FIXED2 better than copied 3-head variable strategy.
- v254 PRE.28 POST.25:123R hit13.01 avg comp9.573 profit154490 ROI112.56; Feb-Jun96R ROI103.81.
- v256 target10 variable: same gate 123R avgN2.40 ROI110.64, Feb-Jun101.34.
- v257 target10.5/11 same gate:123R avgN~2.3 ROI114.74, Feb-Jun96R ROI106.60. PRE.25 POST.25:156R ROI112.70, Feb-Jun104.45.
- v258 scenario-aware direct pair rejected.
- v259 conservative v96 reranker no material improvement.
- v260 adaptive composite target no improvement.
Benchmark remained PRE>=.28 / POST>=.25 / target comp10.5-11 / avg~2.3 tickets / 10k Dutch. Retrospective only; Jul/Aug non-pristine.

## 4-head actual-head-rate goal
User primary research objective: actual realized boat4 first-place rate >=40% while retaining >=200 historical races. Not average predicted probability.

## v262 search
Run `34429919539`, job `102723051801`.
PRE>=0.300 / POST>=0.385 => 305R, actual boat4 head rate40.66%; Feb-Jun154R, head40.26%.
Aggregate goal possible by thresholding, but monthly stability/floor weak. Do not claim every month >=40%.

## Feature research direction mandated by user
User instructed: investigate other features, prioritize features that worked for 3-head, include individual racer past performance, and exhaustively research features.
3-head successful exact features to prioritize analogues:
- `f__c_b3_minus_b5_st >= -0.1999999999999999`
- rescue `f__c_attack3_stretch <= 0.5672342857142857`
Potential 4-head analogues/families:
- 4-vs6 and 4-vs5 relative ST, 4-vs3 ST edge.
- attack4 stretch/original exhibition straight; exhibition ST4; original lap/turn; tilt.
- boat3 wall weakness; inner1/2 resistance; boat5/6 external pressure.
- motor/prior-foot, meeting form, prior exhibition reproducibility, entry/course movement, weather/water, venue interactions.
- player4 individual prior-only 4-course first-place/2-ren/3-ren, avg ST/ST rank, makuri/makuri-sashi success, recent form, course attack rate, racer x venue x course history.
- interactions such as 4 attack x 3 wall weakness, 4 ST x 3 ST, 4 stretch x inner resistance, racer strength x exhibition.
- direct matchup only with shrinkage/minimum sample.
- odds/market separate value/ticket stage only.

## v263
Run `34430331147`, job `102724318303`, artifact `10134247190`.
Walk-forward Feb-Jun, prior-only training.
Results:
- BASE_P4 AUC .5939; best >=200R 212R head27.36 cut.2100
- PLUS_PLAYER4 .6081;206R 27.18 cut.1975
- PLUS_PLAYER4_WALL3 .6023;226R26.55 cut.1850
- PLUS_PRIOR4 .6095;256R26.95 cut.1900
- PLUS_PLAYER_PRIOR .6186;257R27.24 cut.1650 (best AUC)
- PLUS_ALL_3HEAD_STYLE .5936;260R27.31 cut.1600
No >=200R and >=40% in v263. PLUS_PLAYER_PRIOR top10=40%, top20=40%, top30=40%, top50=36%, top100=29%, top200=26.5%.

## v264 exhaustive feature audit
Files created:
- `analyze_v264_4head_feature_exhaustive.py`
- `.github/workflows/v264-4head-feature-exhaustive.yml`
Commits recorded `11c3d1bc7b373de185ebe5a9bd68ba6c90e248fa` and workflow `229ddbbade69decc3e36a31c0fa09b0575f92615`.
Run ID `34432013915`, job `102729306215` was last known `in_progress` in prior handoff state. NEXT CHAT MUST RE-FETCH CURRENT STATUS before discussing result.

# 1-head / other models
- 1-head canonical chain remains Legacy PRE -> v109 S-only -> v162 Top7 unless newer repo commit supersedes.
- 4-corner and 5-head models exist; always re-fetch exact latest rules before use.

# Communication / execution style
- Japanese, concise, concrete.
- User expects action, not repeated promises.
- For status questions, actually fetch GitHub and state exact status/result.
- Never say completed unless verified.
- When user provides target, execute research/code rather than only theorize.
- Always use realized payout/settled stake definition when saying ROI.

# Recommended next-chat prompt
`boatrace-backtest の CHAT_HANDOFF_CURRENT.md と CHAT_HANDOFF_20260910_FULL.md と最新GitHubを読んで続き。まず live odds parser の artifact 10138281552 の raw HTML を確認して120/120取得に直し、その後9/10の児島5R・鳴門7Rを結果を見ずに展示後v243判定できる状態にして。正式3頭モデルは v249 PRE S+A -> v243 -> v242可変5〜10点 -> 1万円Dutch。`
