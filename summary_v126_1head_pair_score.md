# v126 v110 pair-score validation

- v109/head gate frozen at p109>=72%.
- Changes pair/order construction only; no odds and no Sep outcomes.

## STOP: development block unavailable
- Source months present: **2026-06, 2026-07, 2026-08**.
- `analysis_v110_1head_role_tickets.csv` is Jun-Aug holdout output only, so Mar-May candidate orders are not available.
- Therefore v126 must not tune on Jun-Aug and call that a holdout result.
- Next action: regenerate Mar-May v110 pair-order rows from the frozen v110b code, then tune pair scoring on Mar-May and evaluate once on Jun-Aug.
