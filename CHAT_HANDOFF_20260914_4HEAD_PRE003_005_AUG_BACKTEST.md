# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **OLDER-PERIOD BACKTEST IN PROGRESS**

## Frozen facts from completed August run
- August 2026 is NON-PRISTINE; completed descriptive shadow result was 34/171 = 19.88% for inclusive `0.03 <= PRE <= 0.05`.
- Frozen production remains unchanged: S PRE >= 0.28, A PRE >= 0.18 and all downstream gates remain frozen.
- August result must not be used to tune/select a rescue rule.

## 2026-09-14 Older-period work start record
Written **before** implementation, per operating rule.

User request:
- Test the same low-PRE phenomenon on older historical periods.
- For historical backtests, user explicitly permits use of the archived closing/deadline-time odds for ROI settlement.

Planned work:
1. Identify the oldest historical period(s) for which the frozen HEAD4 feature/model lineage can be reconstructed without target leakage.
2. Re-run the inclusive `0.03 <= PRE <= 0.05` cohort by month/period using a causal walk-forward/frozen-at-period-start contract as appropriate; do not let a race result enter its own features.
3. Report race count, 4-head wins/head rate, PRE/POST distributions and downstream pass counts.
4. Locate archived historical closing/deadline-time 3T odds. For this historical research only, closing/deadline-time odds are explicitly allowed by the user for ROI calculation. Clearly label the odds source/semantics.
5. Where odds coverage is sufficient, apply the frozen ticket/opponent/stake settlement rules and report bets, hits, stake, return, profit, ROI and drawdown. Do not fabricate missing odds.
6. Compare older periods with August descriptively, while keeping August NON-PRISTINE and avoiding threshold selection from August outcomes.
7. Run CI/backtest and update this handoff after completion with exact commits, Run IDs, results, limitations and restart point.

Production policy remains unchanged during this work.
