# OFFICIAL 3HEAD A PRECISION HEAD GATE — ADOPTED 2026-09-19

Status: **FORMALLY ADOPTED / LIVE PARITY PENDING**

## Frozen rule

The adopted 3-head candidate/head gate is exactly:

- race number: **1 through 12**
- enhanced PRE percentile: **>= 0.925**
- boat3 prior-day motor EWMA-rank edge vs boat2: **>= +0.20**
- boat3 current exhibition-time rank: **1st**

Code source of truth:
- `threehead_head_gate_a_adopted.py`

No threshold may be rounded, relaxed, or substituted without a new research version.

## Evidence at adoption

Selection/reference:
- Nov-Dec-Jan: **157R / 65 heads = 41.40%**

Fresh one-shot frozen diagnostic:
- March: **52R / 21 heads = 40.38%**
- March H1: 30R / 12 = 40.00%
- March H2: 22R / 9 = 40.91%
- March max venue share: 11.54%
- March leave-one-venue-out: 37.50% to 43.48%

Clean combined, excluding non-pristine February:
- **209R / 86 heads = 41.15%**

## April note

Wave23 did not produce a performance result because the frozen canonical source contains zero April-2026 settlement rows. Run 35362293256 failed with `canonical April too small: 0`. This is a data-horizon limitation, not a failed A-gate result.

## Production semantics

This adoption is for the **3-head candidate/head gate**.

It does **not** redefine the frozen v288 ticket-ranking or Dutch staking rules.

The A gate's enhanced PRE percentile is not interchangeable with the older v288 PRE grade/score. A production implementation must reproduce the exact enhanced-PRE semantics, strict prior-day motor state, and current exhibition rank. Missing required data fails closed.

Until live parity verification succeeds, existing v288 production remains unchanged.

September-2026 settlement outcomes must remain unread for research/tuning.
