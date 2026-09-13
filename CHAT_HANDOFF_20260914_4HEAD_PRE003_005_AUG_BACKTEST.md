# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 AUG 2026 BACKTEST

Status: **IN PROGRESS**

Period: `2026-08-01..2026-08-31`
Band: inclusive `0.03 <= PRE <= 0.05`

## Guardrails
- August 2026 is **NON-PRISTINE**. This run is exploratory only.
- Do not use August outcomes to fit/refit/calibrate/select thresholds or rescue rules.
- Frozen HEAD4 v291/VARN model coefficients and downstream rules remain unchanged.

## Two views
1. **Production-as-is**: this PRE band is below the frozen outside-S A floor `0.18`, so production bet count is zero by construction.
2. **Research shadow cohort**: select only races with `0.03 <= PRE <= 0.05` and bypass only the PRE floor for exploratory replay. Keep downstream frozen logic unchanged wherever exact historical inputs/odds can be reconstructed.

## Metrics to produce
- cohort race count
- 4-head wins and head rate
- POST / ENV_ENTRY / A_SCORE distributions and pass counts where reconstructible
- VARN N distribution where reconstructible
- bet count, hits, total stake, return, profit, ROI and max drawdown only if exact historical odds lineage is available

## Planned work
1. Locate the exact frozen v291 historical PRE/downstream replay and August data lineage.
2. Locate exact August trifecta odds snapshots/archives; do not substitute fabricated or post-hoc odds.
3. Implement a dedicated August shadow-cohort analysis only if an existing exact path cannot be reused.
4. Run CI/backtest and record exact commits, Run IDs, results, limitations and restart point here before ending.

## 2026-09-14 Work Start Record
This section is written **before** doing the continuation work, per operating rule.

Current continuation target:
- Continue the unfinished August 2026 exploratory shadow backtest for `0.03 <= PRE <= 0.05`.
- First identify the exact frozen HEAD4 v291/VARN historical replay path and the August input lineage.
- Verify whether exact historical pre-deadline 3T odds lineage exists. Do not use fabricated, post-hoc, or closing-after-deadline substitutes.
- Reuse an existing exact replay path if possible; otherwise add the smallest dedicated analysis needed for the shadow cohort.
- Run the relevant CI/backtest.
- After completion, update this handoff with exact commit(s), workflow Run ID(s), metrics, limitations, and the next restart point.

Production policy remains unchanged during this work.