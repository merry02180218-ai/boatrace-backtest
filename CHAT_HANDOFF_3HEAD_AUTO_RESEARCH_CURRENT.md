# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## 2026-09-24 latest restart point

### Accepted CORE: 107R exact set
- Fast implementation: `research-3head-newcore-fast-v20`
- SUCCESS Run: `35892602362`
- Commit / head SHA: `e682880ac0624a675ec4c16615c6e49ea56d6c6a`
- v18 parity: **EXACT / accepted**
- Total: **107R / 64 heads = 59.81%**
- 3連単 payout ROI: **152.26%** (10,000 yen/race denominator used by audit)
- July: **8R / 3 heads = 37.50%**, ROI 72.89%
- August: **18R / 12 heads = 66.67%**, ROI 153.34%
- September: **UNREAD**. Do not use September outcomes in research.
- Production model/workflow: **unchanged** unless explicitly promoted later.

### Why v20 exists
The earlier heavy rebuild path was too slow because it rebuilt/retrained across many months. v20 instead reuses frozen pre-settlement audit sources and computes the accepted CORE membership by deterministic joins/filters only. It therefore reproduces the 107R CORE quickly without rerunning heavy training.

### v20 exact CORE logic
Source: frozen `v243-3head-expand-feature-audit` from Run `34383567078`.
The exact-threshold parity fix is important; do not round these constants:
- base = bet==1, p3>=.45, raw_top_n 7..18, comp_odds 3.05..4.0
- target = [base and f__c_b3_minus_b5_st >= -0.1999999999999999] OR [bet==1 and not base and f__c_attack3_stretch <= 0.5672342857142857]
- CORE additionally:
  - f__c_b3_minus_b4_waku_st <= 0.4999999999999999
  - f__c_b3_minus_b4_st >= -0.6
  - f__c_b3_meetst <= 0.861111111111111

v20 artifact:
- `accepted_core_fast_v20.csv`
- `accepted_core_fast_monthly_v20.csv`
- Artifact ID `10765058639`

### Full v20 monthly CORE
- 2025-12: 25R / 14 heads = 56.00%, ROI 160.90%
- 2026-01: 14R / 4 = 28.57%, ROI 42.54%
- 2026-02: 7R / 6 = 85.71%, ROI 226.44%
- 2026-03: 10R / 6 = 60.00%, ROI 156.65%
- 2026-04: 10R / 9 = 90.00%, ROI 242.10%
- 2026-05: 10R / 7 = 70.00%, ROI 216.11%
- 2026-06: 5R / 3 = 60.00%, ROI 119.42%
- 2026-07: 8R / 3 = 37.50%, ROI 72.89%
- 2026-08: 18R / 12 = 66.67%, ROI 153.34%

## Three-layer context immediately before CORE parity
Layer order under study:
1. **CORE** — now fixed to the exact 107R set above and must be the highest-priority layer.
2. **A+.60**
3. **FULL_3V2**

Old layered audit Run `35853810850` / artifact `research-3head-three-layer-monthly-bets-v8` was created before exact CORE membership was restored, so its CORE overlap numbers must not be treated as final.

Known A+.60/FULL relationship from that audit:
- July A+.60: 39R / 17 heads = 43.59%
- July FULL_3V2 at saturated target: 47R / 20 heads = 42.55%
- July A+.60 ∩ FULL: 39R; FULL-only increment: 8R / 3 heads = 37.50%
- Earlier August audit: A+.60 39R; FULL-only increment 12R / 4 heads = 33.33%
These are context only until recomputed against the exact 107R CORE.

## Required next calculation — START HERE
Use the fast/frozen sources. Do **not** rerun heavy model training.

Priority order must be:
`CORE 107R -> A+.60 -> FULL_3V2`

Compute exact race-code set differences and report, at minimum, by month and total:
1. CORE count / heads / head rate.
2. A+.60 raw count, overlap with CORE, **A+.60 pure increment after CORE exclusion**, its heads/head rate.
3. FULL_3V2 raw count, overlap with CORE and A+.60, **FULL pure increment after CORE then A+.60 exclusion**, its heads/head rate.
4. Final union count and heads/head rate after deduplication.
5. Explicit July and August breakdown.
6. Keep September outcomes UNREAD.
7. Preserve production unchanged; this is research/audit only.
8. Before firing any new workflow, inspect syntax/paths/source artifact names to avoid repeated Actions errors.

## Historical note
The previous contents of this handoff described `v289-addon-wave1` and NO_ADOPTION_WAVE1. That research remains historical context, but the active restart point is now the exact 107R CORE + layered deduplication above.
