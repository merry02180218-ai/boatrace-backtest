# CHAT_HANDOFF_INNER12_LAG_CURRENT

Updated: 2026-09-24

## Purpose
New independent research model requested by user.

Target mechanism:
- boat 1 and boat 2 both have causal pre-race reasons to start late;
- downstream outcome of interest is either:
  1. boat 3 wins by まくり, or
  2. boat 4 wins by まくり差し.

User constraint:
- do NOT make boat3/boat4 raw strength the main driver.
- model should be driven primarily by the simultaneous weakness/start-lag structure of boats 1 and 2.

## Model ID
`INNER12_LAG_3M_4MS_V1`

Research script:
`research/research_inner12_lag_3m4ms_v1.py`

Manual-only workflow:
`.github/workflows/research-inner12-lag-3m4ms-v1.yml`

Production is unchanged.

## V1 architecture

### PRE
For boats 1 and 2 independently, build a start-lag score from:
- Waku10 frame average ST;
- national average ST;
- current-meeting ST;
- Waku10 frame average start order;
- causal prior actual-ST mean;
- causal prior late-start rate (>0.20).

The core pair score is:
`dual_late_pre = min(late1_pre, late2_pre)`

Using min rather than mean is intentional: both boat1 and boat2 must carry lag evidence.

No boat3/boat4 player power or motor power is used in this primary score.

### POST
Current exhibition ST is converted to a predicted actual ST using each player's strictly prior exhibition->actual ST bias.
Then:
- `late1_post = .55 * late1_pre + .45 * current_predicted_slow1`
- `late2_post = .55 * late2_pre + .45 * current_predicted_slow2`
- `dual_late_post = min(late1_post, late2_post)`

Boat3/boat4 current predicted ST is recorded only as structural context, not the primary score.

## Exact target labels
- `target3_makuri = winner == 3 AND kimarite == まくり`
- `target4_makurisashi = winner == 4 AND kimarite == まくり差し`
- `target_any = target3_makuri OR target4_makurisashi`

3号艇のまくり差し is NOT included in v1 target.
4号艇のまくり is NOT included in v1 target.

## Leakage / evaluation contract
- history starts 2025-10-01 only to warm causal prior state;
- research rows start 2026-03-01;
- development/tuning: 2026-04-01 through 2026-06-30;
- fixed holdout: 2026-07-01 through 2026-08-31;
- September outcomes are not read;
- all target-day features are frozen before target-day results are opened;
- prior actual-ST and exhibition-bias histories are updated only after that date's feature freeze;
- production models are not modified.

V1 sweeps PRE and POST dual-late thresholds from .45 to .90.
Any candidate cutoff is selected using development months only, with minimum sample/target-count guards.
July-August is report-only holdout.

## Outputs
Artifact directory:
`/tmp/inner12_lag_3m4ms_v1/`

Expected:
- `race_features.csv`
- `threshold_grid.csv`
- `monthly_selected.csv`
- `meta.json`
- `run.log`

## Next action
Manually fire workflow `research-inner12-lag-3m4ms-v1`.
After SUCCESS:
1. inspect PRE vs POST combined-target lift;
2. inspect July and August separately;
3. inspect whether 3まくり and 4まくり差し respond to the same dual-lag cutoff;
4. if combined mechanism is real, build V2 as two-stage:
   - stage A: INNER12_LAG occurrence probability;
   - stage B: route split 3_MAKURI vs 4_MAKURI_SASHI;
5. keep boat3/4 strength features low-weight/minimum-viability only unless data proves they are necessary;
6. only after head/development signal is stable, add opponent/ticket and odds/ROI work.

## Commits
- script: `762d9ee1355bb9b30107d0f76701ea43ca2a3559`
- manual workflow: `7724ad1e6a569ab913b4ac36c4a45256c53898fd`
