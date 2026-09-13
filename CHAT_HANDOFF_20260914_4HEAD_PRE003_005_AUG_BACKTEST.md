# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **JULY 18->19 RAW PRIMITIVE LINEAGE AUDIT IN PROGRESS**

## Frozen production
Production remains unchanged (`HEAD4_V291_COMP7`). July/August 2026 remain NON-PRISTINE; September remains outcome-blind for tuning/model selection.

## Established findings
- Seasonal YoY: 2025 does not reproduce the 2026 July shift.
- Motor-history source starts 2026-07-01 and becomes causally usable 2026-07-02.
- The dominant PRE break is later, 2026-07-19: `inner12_resistance` 0.245328->0.699611, `wall3_weak` 0.715926->0.195410, `past_win4` 0->0.0938657, `legacy_score4` 46.209->36.2835, PRE<.01 share 0->80.7292%.
- Therefore motor-history onset alone does not explain the break.
- Prior audit CI Run `34775332112`, Job `103772292898`, Artifact `10323142377`, SHA256 `9a1c36bc45255fc9b90297712db5884c0cfdcdedba8ccbd51e7c4f515380bf62`.

## Formula lineage confirmed before implementation
`inner12_resistance = resistance12(x)` depends on boat 1/2 `waku_wr`, national `wr`, and `waku_st`.
`wall3_weak = features4(x)['3壁弱さ']` depends on boat 3 `waku_wr` plus the 3-vs-4 `waku_st` edge.
`past_win4` is the fraction of numeric first-place finishes among boat 4's `艇4_過去1走_着順` ... `艇4_過去10走_着順` in Waku10.
Thus the key raw sources are `data/programs/race_cards/YYYY/MM/DD.csv` (national win rate/ST) and `data/programs/waku10/YYYY/MM/DD.csv` (frame-specific win rate/ST/start-order and past 10 finishes).

## 2026-09-14 work-start record — written BEFORE implementation
Exact plan:
1. Keep production unchanged and keep the diagnostic outcome-blind. Do not load 7/18 or 7/19 results.
2. Compare 2026-07-18 vs 2026-07-19 raw race-card and Waku10 schemas, row/race-code coverage, and field availability.
3. For boats 1-4, summarize raw primitives feeding the shifted features: national win rate/ST, frame-specific win rate/ST/start-order, and past-10 finish availability/values.
4. Measure missing/default shares separately. In particular detect whether `waku_wr` is absent/zero, whether `waku_st` falls back to national ST, and whether past-10 fields suddenly become populated.
5. Rebuild `inner12_resistance`, `wall3_weak`, `past_win4`, and `legacy_score4` from the same causal feature code for both dates and reconcile the observed aggregate jump.
6. Perform counterfactual score-distribution diagnostics where technically valid: hold the suspicious primitive/default policy at its 7/18 behavior while scoring 7/19, without using outcomes. Do not invent cross-race values when racer/race identity differs.
7. Identify whether the 7/19 break is caused by source schema/coverage/default behavior, a history reset/population boundary, or ordinary race-population composition.
8. Run CI and archive raw-field coverage tables, per-day summaries, and audit JSON.
9. AFTER completion update this handoff with commits, Run/Job/Artifact/hash, exact root-cause evidence, limitations, production status, and next restart point.

## Restart protection
If interrupted, resume from this work-start record. Do not change production.
