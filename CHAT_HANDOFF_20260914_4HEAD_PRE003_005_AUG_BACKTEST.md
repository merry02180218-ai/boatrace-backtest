# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **COMMON-FROZEN-SCALE COMPARISON IN PROGRESS**

## Frozen production
Production remains unchanged. S PRE >= 0.28; A PRE >= 0.18; frozen downstream rules remain in force. July/August 2026 remain NON-PRISTINE; September remains outcome-blind for tuning.

## Completed older-period check
Monthly walk-forward 2026-02..06 for inclusive `0.03 <= PRE <= 0.05`:
- 3,818R
- 143 wins
- 3.75% head rate
- POST >= 0.18: 0R
- POST >= 0.25: 0R
Run ID `34771874589`, artifact `10321614933`.

August frozen-at-2026-06-30 shadow:
- 171R
- 34 wins
- 19.88%
- POST >= 0.18: 0R
- POST >= 0.25: 0R

The direct numeric-band comparison has a score-scale mismatch because older months were monthly walk-forward while August used a 6/30-frozen model.

## 2026-09-14 common-scale work-start record
Written **before** implementation.

User approved continuing with a same-frozen-model comparison.

Important methodology decision:
- Do **not** train a 2026-06-30 model and then call Feb-Jun a causal backtest, because that model contains future labels relative to those historical races.
- Instead freeze one PRE/POST model at **2026-01-31** and use that exact model unchanged for every comparison month from **2026-02 through 2026-08**. This gives a genuinely common score scale while keeping all target months later than the fit cutoff.
- July/August outcomes remain descriptive/NON-PRISTINE; they are not used in fitting or model selection.

Planned work:
1. Build causal training features/labels only through 2026-01-31 using the v250 PRE/POST recipe.
2. Fit exactly one PRE model and one POST model once; never refit for Feb-Aug.
3. Replay causal feature state day-by-day through 2026-08-31 and score every race with those same frozen models.
4. For each month Feb-Aug, report all-row count, inclusive `PRE 0.03..0.05` cohort size, 4-head wins/rate, PRE and POST distribution, POST>=0.18 and POST>=0.25 counts.
5. Compare Feb-Jun, July, and August on the same numerical score scale. Treat July/August as NON-PRISTINE and do not tune thresholds from them.
6. Historical ROI may use closing/deadline-time odds per user permission only where an archived, clearly identified odds source exists; otherwise no ROI fabrication.
7. Run CI, save artifact, then update this handoff with exact commits, Run IDs, results, limitations and restart point.

Production policy remains unchanged during this work.
