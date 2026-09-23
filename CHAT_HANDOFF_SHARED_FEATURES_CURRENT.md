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
