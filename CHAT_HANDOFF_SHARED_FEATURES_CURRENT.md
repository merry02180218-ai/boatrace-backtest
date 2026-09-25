# CHAT_HANDOFF_SHARED_FEATURES_CURRENT

Updated: 2026-09-21

## Purpose
Canonical handoff for features/data assets reusable across head models (1HEAD/3HEAD/4HEAD/5HEAD etc.).
Model-specific production handoffs remain authoritative for each model. Nothing in this file implies production adoption.

## Global rules
- Latest GitHub/main overrides old chats/handoffs.
- September 2026 outcomes/payouts remain UNREAD unless user explicitly authorizes otherwise.
- Shared features are SHADOW/RESEARCH until explicitly adopted per model.
- No production model is changed merely because a feature is listed here.
- Before workflow fire: refetch actual main files, inspect full relevant source, check literal escaped newline, YAML/Python syntax, paths/deps, leakage guards, and September UNREAD.
- Never reconstruct historical Waku10 from future/result-derived data.

## Shared feature asset: PLAYER_HISTORY

### Definition
Causal prior-result player history, 5 features per boat x 6 boats = 30 base features:
- `b{1..6}_pl_all_win`: prior all-race win rate with smoothing.
- `b{1..6}_pl_all_p2`: prior all-race top-2 rate with smoothing.
- `b{1..6}_pl_frame_win`: prior win rate in current frame with smoothing.
- `b{1..6}_pl_frame_p2`: prior top-2 rate in current frame with smoothing.
- `b{1..6}_pl_recent_p2`: top-2 rate over latest 30 prior starts.

Current implementation reference:
- `rebuild_4head_v93_all_parent.py`
- State begins 2025-10-01.
- Target-day rows are frozen before that day's results are ingested.

### Independent leakage/parity audit
Run 35597225826 / Job 106324736532 / Artifact 10637383105
- 23,855 races checked.
- 715,650 PLAYER_HISTORY cells independently recomputed.
- mismatches = 0.
- strict_prior_date = true.
- same_day_results_used_for_features = false.
- September outcomes read = false.
Conclusion: independently verified causal/prior-only for audited Mar-Aug 2026 population.

### Predictive diagnostic
4HEAD BASE ablation Run 35593228759 / Job 106312094381 / Artifact 10635251844:
- PLAYER_HISTORY = 30 features.
- strongest standardized BASE coefficient: `b4_pl_all_p2` +0.484267.
- Removing PLAYER_HISTORY almost eliminated BASE selections at fixed .35 cut, showing BASE is highly dependent on this family.

Fixed-bin diagnostic Run 35597873022 / Job 106326785722 / Artifact 10637950770:
- `b4_pl_all_p2` shows broadly monotonic predictive signal across months.
- Signal exists before June; it is not a June-only artifact.
- Example Jul: .50-.60 => 80/342 head4 = 23.39%; .60+ => 10/24 = 41.67%.
- Example Aug: .50-.60 => 68/311 = 21.86%; .60+ => 8/25 = 32.00%.
- No retuning; production unchanged; September UNREAD.

### Intended cross-model use
Do NOT automatically add to production.
When each model is next researched, test in SHADOW:
1. head boat's own 5 PLAYER_HISTORY features;
2. important adjacent/wall/attack boats' features;
3. relative/difference features appropriate to race mechanism (e.g. 4-vs-3, 3-vs-2);
4. fixed existing model first, then compare head rate, volume, calibration and ultimately closing-odds ROI;
5. preserve chronological training/validation and leakage audit.

## Shared data asset: historical Waku10 (Boatcast)

Canonical shared path:
`data/shared_historical/waku10_boatcast/2026/MM/DD/JJ_RR.txt`

Available reconstructed historical range:
- Mar-Jul 2026 from Boatcast historical source.
- Jul-Aug also exists in BoatraceCSV; semantic parity was checked.

Key audits:
- Historical source leakage audit Run 35527070792: repeated historical fetches identical; no direct result fields; LEAK_AUDIT_OK.
- Full semantic parity Run 35558286203: 44 CSV days / 1,424,736 cells / 0 semantic mismatches; result files not read; September outcomes not read.
- Mar-Jun reconstruction Run 35547108828: 18,171/18,171 files, missing 0.
- Validation Run 35547394740: FORMAT_BAD 0; source sample mismatch 0.
- July reconstruction Run 35568270269: 4,920/4,920, missing 0.
- Six-month complete-Waku audit Run 35572435087: 23,855 parent races, missing {}; shared historical Waku used true; Waku backfill false.

Shared commits:
- Mar-Jun data: `6410b14d209eb7247cce2770693a73b6f3f7cc04`
- July data: `edcb7be33d35b1fc5a50b8635f36bd5685028cf`
- nested loader fix: `44231256976040596f30b859158073b1ae278046`

### Waku10 research note
Broad Waku10 injection into 4HEAD did not universally improve performance.
More targeted relative features (especially boat4-vs-boat3) were more promising, but are NOT production-adopted.
Treat Waku10 as shared raw feature material, not a universal proven gate.

## Shared leakage findings relevant to all model research
4HEAD forensic sequence provides reusable audit patterns:
- v7 Run 35589976860: causal ordering checks passed.
- v8 Run 35591622050 / Job 106307071457 / Artifact 10634439444:
  result/payout access blocked during exhibition feature generation; 28,011 reference vs 28,011 isolated rows; mismatch columns = 0.
- v10 PLAYER_HISTORY independent audit: 715,650 cells, mismatch 0.

These findings validate the audited shared feature-generation paths; they do not automatically prove every other model implementation leak-free. Re-run model-specific isolation/parity when integrating.

## Production status
- PLAYER_HISTORY shared asset: READY FOR SHADOW TESTING; no new cross-model production adoption.
- Historical Waku10 shared asset: AVAILABLE; no automatic production adoption.
- 1HEAD/3HEAD/4HEAD/5HEAD production definitions remain unchanged by this handoff.

## Next use
When resuming any head model, read:
1. that model's latest handoff;
2. this `CHAT_HANDOFF_SHARED_FEATURES_CURRENT.md`;
3. latest GitHub/main.
Then decide whether that model is at the right research point to Shadow-test PLAYER_HISTORY/Waku10.


## Shared GitHub Actions operation: automatic latest-Run discovery

Verified 2026-09-23 during 1HEAD PLAYER_HISTORY expansion research.

When a pushed research commit auto-triggers a workflow, do NOT ask the user to paste the Actions Run URL first. The GitHub connector generic fetch can list repository workflow runs directly through the approved REST collection endpoint, including branch filtering:

`https://api.github.com/repos/merry02180218-ai/boatrace-backtest/actions/runs?branch=<URL-encoded-branch>&per_page=10`

Verified example:
- branch: `research/1head-player-history-expansion`
- commit: `3ced5b1d5c1b2e3c7b8c63189e4b374b171db6cc`
- automatically discovered Run: `35859504662`
- event: push
- status at discovery: in_progress
- workflow: `1HEAD PLAYER_HISTORY expansion audit`

Operational sequence for all model chats:
1. After push/update, fetch `/actions/runs?branch=...&per_page=10`.
2. Match `head_sha` to the commit just pushed and confirm the expected workflow/path.
3. Use the returned Run ID with `fetch_workflow_run_jobs`.
4. On failure, use `fetch_workflow_job_logs` / step inspection.
5. On success, use `fetch_workflow_run_artifacts` and inspect/download the relevant artifact.
6. Never claim RUNNING/SUCCESS/FAILURE without checking the current Run/job state.
7. `fetch_commit_workflow_runs` is not sufficient for this purpose because that wrapper currently filters to pull-request-triggered runs; push-triggered research runs can therefore appear empty.
8. Only ask the user for a Run URL if automatic REST run discovery actually fails.

This procedure is shared operational guidance for 1HEAD/3HEAD/4HEAD/5HEAD research.


## LIVE prior-result learning rule — fixed 2026-09-24

- LIVE operation MUST use all settled prior-date results, including completed September 2026 races.
- For target date D, causal daily state ends at D-1 (`history_end = target_date - 1 day`). Example: 2026-09-24 LIVE may use settled results through 2026-09-23.
- Target-date results are never read before decisions (`target_date_results_used = false`).
- Current 4HEAD implementation is compliant: `prepare_4head_120r_daily_state.py` loops only while `d < target`, records `september_prior_results_allowed: true`, and updates PLAYERHistory, motor history and ST lane-bias from settled prior dates.
- `run_4head_120r_lastminute_fast.py` rejects contaminated state unless `target_date_results_used` is false.
- Research/holdout may keep September outcomes UNREAD for leakage-safe evaluation. This does NOT mean September prior results are excluded from LIVE causal learning.
- Never change LIVE to blanket September UNREAD. LIVE = settled prior September allowed; research holdout = outcome masking per audit.
- User explicitly confirmed this intended operational rule on 2026-09-24.


# 4HEAD opponent-selection / regime-research handoff — 2026-09-24

## Scope / authority
This section records the full current 4HEAD opponent-selection research state from the latest chat. Latest GitHub/main remains authoritative. PH5 head selection is frozen; this work concerns SECOND/THIRD/ticket composition only unless explicitly stated otherwise.

## Frozen production/research baseline
- Repo: `merry02180218-ai/boatrace-backtest`
- Frozen production population: 163 bets = June 47 / July 57 / August 59.
- Among these, actual 4-head wins used for opponent truth research: 81 races = June 24 / July-August 57.
- PH5 head model remains unchanged.
- Research development: June only.
- Holdout: July-August.
- September outcomes remain UNREAD for this research.
- LIVE is separate: settled prior September dates are allowed causally through D-1 per shared LIVE rule above.
- PLAYERHistory = causal prior-day.
- Waku10 = pre-race only.
- Production SECOND gap = .11; THIRD gap = .18.

## Adopted production opponent policy before this chat
Policy: `HEAD4_OPP_INNER_SURVIVE_ALWAYS_V1`.
Production adoption commit: `3f066c5795f24791661c93e3363a8cdd25d30a3c`.
LIVE parity fix commit: `6b481b991639adef22ee774de6687a198f61b148`.
Research metadata commit: `e6233b0...`; Run `35879285297`.

Exact SECOND concept:
- base = logit(p2)
- bonus = (z(pl_frame_p2) + z(w10_wr) - z(w10_rel4_wr))/3
- multiplier 1.0 for boats 1/2/3, -0.35 for 5/6
- final = base + 0.20*bonus
- race-local z scores over opponent boats 1,2,3,5,6.
Current production THIRD remains conditional `pc[(second,third)]` based.

Important holdout result for adopted SECOND:
- baseline Jul-Aug capture = 36/57, avg points about 6.21.
- always-on inner_survive Jul-Aug capture = 37/57, avg points about 5.89.
- July = 18/27 at 5.704 avg points.
- August = 19/30 at 6.067 avg points.
Truth-conditioned pre-close od3 proxy on 37 races with odds:
  baseline ROI 221.29%; inner_survive ROI 224.16%.
This proxy is NOT all-163 production ROI.

## Current production implementation
`run_4head_120r_lastminute_fast.py`
- `inner_survive_second_scores(...)` implements adopted SECOND formula.
- `production_tickets(...)` requires PLAYERHistory and Waku10.
- SECOND: top2, add rank3 if score gap <= .11.
- THIRD: for each SECOND, rank by frozen conditional pc, top2, add rank3 if pc gap <= .18.
- Thus PLAYERHistory/Waku10 directly adjust SECOND but not current production THIRD.

## September current-LIVE replay evidence that motivated opponent research
These completed dates used current LIVE causality (prior settled Sep allowed; target-day result joined only after decision freeze):
- 9/10 Run 35887861368: BET2, head4 0, hits0, ROI0%.
- 9/11 Run 35890535515: BET2, head4 2, hits1, ROI149.5%. 住之江7 head correct/ticket miss; 尼崎6 hit.
- 9/12 Run 35891254548: BET1, head4 1, hits0. 戸田3 head correct/opponent miss.
- 9/13 Run 35892079611: BET2, head4 1, hits0. 住之江3 head correct/opponent miss.
- 9/14 Run 35892557622: BET3, head4 2, hits1, ROI100%. びわこ2 head correct/ticket miss; 福岡4 hit.
Cumulative 9/10-9/14: BET10, head4 6/10=60%, trifecta 2/10=20%, stake100k, payout59.9k, ROI59.9%.
Do NOT fit opponent research to these September outcomes.

Production bug found during replay:
- `NameError: np not defined` in inner-survive LIVE scorer.
- fixed commit `d2bf8ff2584c99670730b72caea6882e9e29a166`.

## THIRD PLAYERHistory + Waku10 soft rerank — rejected
Research added to `research_4head_opponent_second_rerank_v2.py`.
Initial commit `0dc7d478575ed94c57cb577d595bc436577aca03`.
The first run failed because the newly inserted block contained literal escaped `\\n`, causing the block to be commented out and `third_dev` undefined.
Failure Run: `35893644340`.
Root error: `NameError: name 'third_dev' is not defined`.
Fix commit: `cb537ec1a43be792afdc7c2f4862ce475494d95a`.
Successful Run: `35897109109`.

Design:
- SECOND fixed to adopted always-on inner_survive.
- THIRD soft score used conditional pc plus PLAYERHistory/Waku10.
- alpha candidates selected on June only: 0,.10,.20,.30,.40,.60.
- selected alpha = .30.
Results:
- June: current inner_survive capture 11/24; new THIRD soft rerank 8/24.
- July: current 18/27; new 15/27.
- August: current 19/30; new 13/30.
- Jul-Aug current = 37/57 = 64.9%; new = 28/57 = 49.1%.
- New avg points ~4.61 vs current ~5.89: tickets were reduced too aggressively and capture collapsed.
Conclusion: REJECT. Do not production-adopt this THIRD soft rerank.

## Conservative THIRD rank3 rescue — not adopted
User wanted continued opponent improvement. Added a conservative rescue that does NOT reorder existing THIRD top2:
commit `9bacf7a05a34f5b8aeb8b672aff3f6eda5f0642f`.
Successful Run: `35900506220`.

Design:
- SECOND stays adopted inner_survive.
- baseline conditional pc THIRD top2 untouched.
- existing .18 rank3 rescue untouched.
- only when normal rank3 is not already included, add rank3 if pre-race support is strong.
- support = mean z(pl_frame_p2, pl_recent_p2, w10_wr, w10_sr, -w10_rel4_wr).
- threshold tuned on June only.
- selected rescue support cutoff = .75.
Results:
- June current 11/24 -> rescue 13/24.
- July current 18/27 -> rescue 19/27.
- August current 19/30 -> rescue 18/30.
- Jul-Aug total current 37/57 -> rescue 37/57, no net capture gain.
- avg points rescue Jul ~6.037, Aug ~6.033 vs current combined ~5.89.
Conclusion: no clear holdout gain; NOT production-adopted. User explicitly felt this was not changing enough and requested a different research viewpoint.

## Why research direction changed
Repeated SECOND/THIRD direct ranking work has plateaued:
- generic SECOND ML rerank selected alpha 0.0 / no gain.
- rescue/scenario variants mostly no robust gain.
- direct THIRD soft rerank was materially worse.
- conservative THIRD rescue only shifted wins between July/August with no Jul-Aug total improvement.
Older pair-ranking research also failed to show a robust direct-ranking breakthrough.

Relevant older evidence reviewed:
- `analysis_v276_4head_opponent_pair_family.csv`: direct pair models often underperformed v96 at holdout top ranks.
- `analysis_v278_4head_opponent_current_exhibition_family.csv`: current-exhibition-only family was weak; BASE_CURRENT_PLAYER gave some top2 improvement but not broad ranking dominance.
- `analysis_v280_4head_opponent_role_split.csv`: separate SECOND/THIRD role probabilities existed but did not solve production capture robustly.
- v281/v282/v284 historical THIRD branches: independent THIRD, conditional THIRD, and INNER/OUTER regime conditional THIRD all showed some signal but no stable overall production improvement.

## New research direction: development/regime first, tickets second
User approved moving away from micro-tuning THIRD.
Core idea:
Do NOT first ask “which boat is 2nd/3rd?”.
First ask: “when 4 wins, what development/formation occurs behind 4?”
Candidate regimes:
- INNER_REMAIN: inner boats 1/2/3 survive together.
- FIVE_FOLLOW: boat5 follows / appears in opponent pair.
- SIX_RISE: boat6 rises through open lane / appears in opponent pair.
- MIXED / more detailed regime to be refined after descriptive discovery.
Future classifier should use only pre-race information such as:
- 1-3 wall strength.
- 4 attack strength.
- 5 follow strength.
- 6 open-lane/rise strength.
- exhibition ST.
- corrected exhibition.
- original exhibition.
- motor type/strength.
- PLAYERHistory.
- Waku10.
Then choose ticket structure conditional on predicted regime. This is intentionally different from directly ranking all 20 pairs.

## New regime discovery v1
Created new independent research file:
`research_4head_opponent_regime_v1.py`
Commit: `60ee2275df0d55ad58d2ea21263bd7e880cafc33`.

v1 is intentionally descriptive before classifier fitting:
- builds on frozen `base.build_long()`.
- requires 81 actual head4 races.
- requires June dev 24 and Jul-Aug holdout 57.
- truth labels currently:
  - INNER_REMAIN if both second and third are among 1/2/3.
  - FIVE_FOLLOW if 5 appears.
  - SIX_RISE if 6 appears.
  - MIXED fallback.
- extracts race-level PLAYERHistory/Waku10/p2 inner-vs-outer summaries and boat-level values.
- outputs:
  - `/tmp/head4_opponent_regime_v1/race_regime_features.csv`
  - `regime_monthly.csv`
  - `pair_monthly.csv`
  - `meta.json`
- meta asserts:
  - head4_R 81
  - dev June only
  - holdout Jul-Aug
  - September outcomes read false
  - PH5 head model changed false
  - production changed false
  - stage DESCRIPTIVE_REGIME_DISCOVERY_ONLY.
This first pass is meant to determine whether stable, useful regime labels exist before fitting a classifier. Do not jump straight to production.

## Workflow wiring / operational safety
Research workflow:
`.github/workflows/audit-4head-ph5-live-walkforward.yml`

Important user policy:
- research/replay workflows must be MANUAL ONLY.
- do NOT add temporary `push:` triggers.
- do NOT use trigger-file commits.
- user previously warned that workflow triggers can cause later side effects.
- always preflight before asking user to fire.

Workflow manual-only cleanup commit:
`d55f8ca979bf2a03295a59a4087f5a8eb12795f0`.
It leaves:
`on: workflow_dispatch:`
and no push trigger.

The regime script was wired into preflight/artifact path, then a missed execution step was detected and fixed.
Final wiring commit:
`85f4dcf24e32cd11c2e9b612f9e79d868383680a`.
Current workflow:
- py_compile includes `research_4head_opponent_regime_v1.py`.
- explicit step `Opponent regime discovery v1` runs the script after SECOND research.
- artifact includes `/tmp/head4_opponent_regime_v1/`.
- remains manual-only.

## CURRENT RUN AT HANDOFF
User manually fired the workflow after commit `85f4dcf`.
Automatically discovered current Run:
- Run ID: `35903045223`
- head SHA: `85f4dcf24e32cd11c2e9b612f9e79d868383680a`
- status at handoff creation: IN_PROGRESS
- conclusion: none yet
- URL: https://github.com/merry02180218-ai/boatrace-backtest/actions/runs/35903045223

### Exact next action in new chat
1. Read this handoff + latest GitHub/main.
2. Check Run `35903045223` automatically; do not ask user for URL.
3. If failure:
   - inspect failed job logs first;
   - fix root cause;
   - preflight;
   - keep workflow manual-only;
   - then ask for one manual re-fire only if necessary.
4. If success:
   - inspect `REGIME_MONTHLY`, `PAIR_TOP`, meta and artifact CSVs.
   - first judge label stability across June/July/August descriptively.
   - inspect whether INNER_REMAIN/FIVE_FOLLOW/SIX_RISE definitions overlap conceptually. Current `classify_truth` gives FIVE precedence after INNER_REMAIN and SIX only if 5 absent; if this masks useful 5+6 combinations, refine labels before classifier fitting.
   - analyze actual pair families (e.g. inner-inner, inner-5, inner-6, 5-6/6-5) rather than forcing a poor four-class taxonomy.
   - only after stable target taxonomy is established, build leakage-safe pre-race regime classifier.
5. For classifier stage:
   - design/tune on June only.
   - validate July and August separately and combined.
   - September outcomes stay UNREAD.
   - PH5 and production opponent policy stay unchanged until explicit adoption.
   - compare regime-conditioned ticket capture, avg points, and if reconstructable pre-close od3 ROI against current `HEAD4_OPP_INNER_SURVIVE_ALWAYS_V1`.
6. Do not revert to THIRD micro-reranking unless regime research clearly indicates it.

## User preference / intent from latest exchange
User said the THIRD rescue “doesn't seem to change much” and explicitly asked to research from a different viewpoint.
User reacted positively to the regime/development idea and said it sounded good.
Therefore continue regime-first research, not another small PLAYERHistory/Waku10 THIRD threshold sweep.


## 統合LIVE自動運用の共通仕様（2026-09-24追記）

今後、1号艇・3号艇・4号艇など他の頭モデルも、4号艇で確立したLIVE運用方式に揃えて統合する予定。各モデルを統合する際は以下を共通仕様として扱う。

### 自動運用フロー
1. 朝の事前スキャンで候補レースを抽出し、result-blindなwatchlistへ登録する。
2. watchdogを定期自動起動し、候補ごとに展示後の直前データ・締切前オッズを取得する。
3. 直前判定は BET / PASS / NO_BET_DATA_NOT_READY を明示する。
4. PASSは通知しない。BETだけ通知する。
5. NO_BET_DATA_NOT_READYは「完了」にしない。診断artifactは残してよいがcanonical完了artifact名を使わず、安全時間内なら次のscheduler tickで自動再試行する。
6. BET/PASSに到達した時だけcanonical完了artifactを作り、同一レースの重複実行を防ぐ。
7. target raceの結果・払戻は判定前に絶対に読まない。target_race_result_used=false / payout_used=false を維持する。

### BET通知の共通仕様
BET通知には最低限、以下を含める。
- モデル名 / 対象場 / R / 締切
- BET判定に使った主要指標
- 3連単の買い目
- 各買い目の締切前取得オッズ
- 各買い目への購入金額振分
- 合計購入額
- 各買い目の的中時想定払戻

資金配分の現行標準は「1レース上限5,000円、100円単位」。4号艇では取得オッズの逆数比例（dutching）で、買い目間の的中時払戻ができるだけ均等になるよう自動配分する。今後ほかのモデルを統合する際も、特別な検証済みstaking policyがない限り、この方式を共通の初期仕様とする。

### 4号艇での基準実装
- watchdog: `.github/workflows/live-4head-120r-watchdog.yml`
- 直前判定: `run_4head_120r_lastminute_fast.py`
- BET通知: `notify_head4_bet_github_issue.py`
- 2026-09-24に NO_BET_DATA_NOT_READY を再試行可能に修正: commit `a21b1c2283ada5c6485658b07b57c75be44f7dcf`
- BET通知へ買い目・5,000円振分・想定払戻を追加: commit `0d7c2fd78498e0b61b691587181ad42f0c918cbf`

### 将来の統合時の注意
各頭モデル固有の「頭判定」「相手選び」「採用閾値」は勝手に共通化しない。共通化するのはLIVEの監視・再試行・通知・資金配分インターフェース。モデル固有ロジックはそれぞれの正式採用版を保持したまま、最終的に同じ統合watchdog/通知形式へ接続する。


## 1HEAD current-day LIVE wiring — 2026-09-25
Detailed handoff:
- `CHAT_HANDOFF_20260925_1HEAD_CURRENT_DAY_LIVE.md`

Validated daily audit:
- Run 36124801250 / Artifact 10859279916
- 2026-09-25 cards 144R / causal cache 144R / WATCH 11R
- D-1 history_end=2026-09-24
- target-day result=false / payout=false
- old run's overall FAILURE was only a self-matching static grep; core audit was SUCCESS.
- preflight fix: `9fc47376b06eb9c8eb452ae1985dc32e3cab391c`

1HEAD final LIVE lanes remain model-specific:
- formal: HEAD>=.790 + mass>=.375 + standard exhibition .05/.70
- PH expansion: .780<=HEAD<.790 + mass>=.375 + b1 recent_p2>=.533333333333 + standard exhibition
- relaxed volume expansion: .750<=HEAD<.780 + mass>=.375 + relaxed exhibition .10/.65 + env_pair<=-.34

Manual monitor:
- `.github/workflows/live-1head-current-day-monitor.yml`
- workflow_dispatch only; **no schedule restored**
- uses audited daily artifact directly
- BET / PASS / NO_BET_DATA_NOT_READY
- BET only notification
- 5,000 yen total Dutch allocation in 100-yen units
- target result/payout forbidden
- official odds must be verified pre-deadline both before and after fetch

Latest strengthened contract:
- Run 36127372755 SUCCESS
- verifies promoted lanes, existing v351 finalizer bridge, BET notification dry-run,
  pre-deadline odds guard, YAML/syntax and result/payout source guard.

Do not enable automatic 1HEAD watchdog/schedule until explicit user adoption after one real active-race manual validation.


## 1HEAD automatic schedule now shares HEAD4 timing — 2026-09-25
User decision: **do not create a separate 1HEAD cron.**

Shared scheduling:
- Morning PRE: `live-4head-newfeature-pre-daily.yml`
  - 05:30 JST + 06:30 JST refresh.
  - now also calls reusable `live-1head-current-day-audit.yml`.
- Intraday watchdog: `live-4head-120r-watchdog.yml`
  - existing HEAD4 every-5-minute schedule.
  - now also resolves and calls reusable `live-1head-current-day-monitor.yml`.

1HEAD-specific workflow files have no `schedule:`; manual `workflow_dispatch` remains available.

Safety:
- official racelist-only deadline enrichment.
- WATCH begins 35 minutes before deadline.
- target-day result/payout remain unread.
- BET/PASS canonical artifact prevents duplicate processing.
- NOT_READY remains retryable on the next shared watchdog tick.
- per-race 1HEAD calls are serialized.

Schedule integration commits:
- `d03b85e5` shared morning PRE.
- `ce16ae76` shared intraday watchdog.
- `ce46f5fc` checkout-free artifact download fix.

Validation:
- shared schedule contract Run `36138243239`: SUCCESS.
- first scheduled integration Run `36138298239`: HEAD4 resolve SUCCESS; 1HEAD resolver failed only on missing repo context for `gh run download`.
- fix `ce46f5fc`.
- real artifact resolver integration Run `36138471846`: SUCCESS.
- HEAD4 watchdog parallel regression Run `36138388274`: SUCCESS.
