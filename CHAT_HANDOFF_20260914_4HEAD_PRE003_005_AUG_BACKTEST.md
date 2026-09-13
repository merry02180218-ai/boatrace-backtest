# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 AUG 2026 BACKTEST

Status: **COMPLETE — EXPLORATORY / PARTIAL DOWNSTREAM COVERAGE**

Period: `2026-08-01..2026-08-31`
Band: inclusive `0.03 <= PRE <= 0.05`

## Guardrails
- August 2026 is **NON-PRISTINE**. This run is exploratory only.
- Do not use August outcomes to fit/refit/calibrate/select thresholds or rescue rules.
- Frozen HEAD4 v291/VARN model coefficients and downstream rules remain unchanged.
- PRE fitting labels stop at `2026-06-30`.
- Prior-day outcomes may update causal player-history feature state only; target-day outcomes never enter features.
- No v96 production signal/fallback is used.
- Exact historical pre-deadline 120-way trifecta odds were not proven for August, so ROI/VARN settlement is not reported.

## Two views
1. **Production-as-is**: this PRE band is below the frozen outside-S A floor `0.18` and S floor `0.28`, so production bet count is zero by construction.
2. **Research shadow cohort**: select only races with `0.03 <= PRE <= 0.05`; describe realized head rate and frozen downstream scores only where exact historical-safe inputs can be reconstructed. Do not tune from these August outcomes.

## 2026-09-14 Work Start Record
This section was written **before** continuation work, per operating rule.

Continuation target was:
- Continue the unfinished August 2026 exploratory shadow backtest for `0.03 <= PRE <= 0.05`.
- Identify the exact frozen HEAD4 v291/VARN historical replay path and August input lineage.
- Verify exact historical pre-deadline 3T odds lineage; never substitute fabricated/post-hoc/closing-after-deadline odds.
- Reuse exact frozen paths where possible and add only the minimum dedicated analysis needed.
- Run CI/backtest and record commits, Run IDs, results, limitations and restart point.

Production policy was not changed during this work.

---

# Completion record — 2026-09-14

## Implementation
Dedicated exploratory analysis:
- `analyze_4head_aug_pre003_005_shadow.py`
- workflow: `.github/workflows/analyze-4head-aug-pre003-005-shadow.yml`

Relevant commits:
- `1273acbea1be18c4adf3294a85a88244395b0de6` — initial dedicated Aug shadow analysis
- `929361d43088d125fe5b501f46e4d81b7f6cd420` — workflow
- `b32edfcd003905991bd24d82b5bb0c588bbe1fd2` — causal August player-history replay fix
- `81f5c21842356827ad94d3b30c6191cbb4af8e44` — allow honest partial ENV/A reconstruction coverage instead of fabricating missing historical rows

Reference production causal player-history builder:
- `build_4head_player_history_live.py`
- source commit `4b1217fdb4ea18942a586edcd85e59d79389629d`
- contract: historical outcomes update only causal pre-race player state; target-day results are not read into target features; no fitting/calibration/threshold tuning/odds/payout use.

## CI history
### Run 1 — failed as intended by fail-closed guard
- Run ID: `34770611938`
- head SHA: `929361d43088d125fe5b501f46e4d81b7f6cd420`
- failure: August A_SCORE historical player primitives were missing because old `v221.build()` was hard-limited to pre-July history.
- no result was accepted from this run.

### Run 2 — failed as intended by fail-closed guard
- Run ID: `34770892924`
- head SHA: `b32edfcd003905991bd24d82b5bb0c588bbe1fd2`
- causal player-history feature reconstruction succeeded, but many PRE-band races had no matching archived historical-safe v93/v264 row for ENV/A reconstruction.
- script failed rather than silently imputing/fabricating those rows.
- no result was accepted from this run.

### Run 3 — SUCCESS
- Run ID: `34771358780`
- head SHA: `81f5c21842356827ad94d3b30c6191cbb4af8e44`
- job ID: `103761429484`
- analysis: PASS
- guard audit: PASS
- artifact upload: PASS
- artifact ID: `10321973532`
- artifact: `head4-aug-pre003-005-shadow`

## Frozen PRE cohort result
Frozen PRE model:
- fit labels: `2025-12-01..2026-06-30`
- training rows: `32,085`
- training 4-head rate: `9.7335%`
- July/August labels used for fitting: **false**

August frozen-PRE universe:
- all rows: **4,920R**
- inclusive `0.03 <= PRE <= 0.05` cohort: **171R**
- 4号艇1着: **34/171**
- realized head rate: **19.88%**

IMPORTANT:
- This 19.88% is NON-PRISTINE August descriptive evidence only.
- It must not be used to lower production PRE thresholds, select a rescue rule, calibrate, or promote a new policy.

## PRE / POST distributions for the full 171R cohort
PRE:
- min `0.030045`
- p25 `0.033243`
- median `0.036237`
- p75 `0.041724`
- max `0.049994`
- mean `0.037702`

POST:
- min `0.021319`
- p25 `0.033439`
- median `0.037937`
- p75 `0.044176`
- max `0.092424`
- mean `0.039429`

POST >= 0.25:
- **0/171R**

Therefore even if the PRE production floor were hypothetically bypassed, **none of these 171 races passes the frozen S POST gate**.

## ENV_ENTRY / A_SCORE historical reconstruction limitation
Archived historical-safe v93/v264 lineage could reconstruct exact ENV/A input rows for only:
- **17/171R**
- missing: **154R**

Missing rows were explicitly left missing; no median/dummy/post-hoc reconstruction was used to pretend full coverage.

Among the 17 reconstructible rows:

ENV_ENTRY distribution:
- min `0.070218`
- p25 `0.123512`
- median `0.157299`
- p75 `0.201425`
- max `0.392491`
- mean `0.174436`

ENV_ENTRY >= `0.224790`:
- **3R**

But frozen S downstream combination requires POST >= 0.25 too:
- **0R**

A_SCORE_LIVE distribution:
- min `0.120062`
- p25 `0.186566`
- median `0.223120`
- p75 `0.321966`
- max `0.551006`
- mean `0.276268`

Mapped frozen A_SCORE live cut:
- `0.2710428764008591`

A downstream combination with PRE floor intentionally bypassed but keeping POST >= 0.18 and A_SCORE live cut:
- **0R**

So in the reconstructible subset, the frozen POST gate already eliminates the 0.03-0.05 PRE band before market/ticket logic.

## Odds / ROI / VARN status
Repository contains `data/official_closing_odds3t`, but the verified tree did not provide a `2026/08` archive and the direct August path was not present.

Therefore this task does **not** report:
- VARN N distribution
- BET count under exact historical market state
- hits
- stake
- return
- profit
- ROI
- max drawdown

Reason:
- exact August official **pre-deadline** 120/120 trifecta odds lineage is not proven.
- closing/final/post-hoc odds must not be substituted.

This is a data-lineage limitation, not a model result.

## Final interpretation
The exploratory August PRE `0.03..0.05` band has a surprisingly high realized 4-head rate of **19.88% (34/171)**, but the same frozen downstream model gives POST values only `0.0213..0.0924`; **0/171** reaches POST 0.25 and **0/171** reaches POST 0.18.

Therefore:
- do **not** change production thresholds from this August result.
- do **not** treat 19.88% as pristine validation.
- production remains unchanged.
- current frozen HEAD4 production does not bet this band.
- if this band is researched further, it should be treated as a separate future hypothesis and validated on a genuinely unseen future period, not optimized using August outcomes.

## Restart point
This PRE 0.03-0.05 August shadow task is complete.

Next safe choices for future work:
1. Leave production unchanged and continue prospective September/next unseen LIVE observation.
2. If researching why this low-PRE cohort has 19.88% realized head rate, formulate features/hypotheses **without tuning on August outcomes**, then freeze them before a future unseen validation period.
3. Separately improve historical source coverage/archiving so exact frozen ENV/A and pre-deadline odds can be reconstructed for future audits.

Any future work must again write the planned work into the handoff **before** implementation and update the handoff **after** completion.