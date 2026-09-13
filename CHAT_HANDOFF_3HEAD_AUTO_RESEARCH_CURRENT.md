# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Current policy
- research branch: `research/3head-v289-addon-expansion`
- legacy v288 production remains unchanged.
- legacy v288 baseline is a **floor, not a fixed research count**: 94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%.
- research should not reduce total selected races below 94R; expansion above 94R is allowed.
- candidate generation may include final-NO_BET races that were formerly outside old PRE S/A.
- July/August are NON-PRISTINE.
- September outcomes are not loaded / not used for tuning.
- frozen canonical source: Run `34383567078`, artifact `v243-3head-expand-feature-audit`, artifact ID `10118044294`, max date 2026-08-31.
- all research inputs must be available before deadline; required-current missingness fails closed.
- overlap with legacy v288 must remain zero for add-on selections.

## Waves 1-13
All prior Wave1-13 proposals were rejected. The stable earlier results remain in repository result files. Because the candidate population has now changed, prior signal families may be re-tested on the expanded population, but simple global threshold relaxation remains disallowed.

## Wave14 — conformal market/field selective gating — FINAL
- Run `34741605409` completed successfully.
- artifact `v289-3head-addon-wave14-conformal-market`, artifact ID `10313288111`.
- result commit `c921aa8dc71e835d91015a83e865888d6eb33dc0`.
- best rows were still strongly negative: 99R / 4 hits / ROI 33.74% / profit -656,020 yen; other alphas were worse.
- decision: **NO_ADOPTION_WAVE14**.

## Wave15 — expanded source + prior-Wave replay — FINAL
- purpose: reopen buyable final-NO_BET races formerly excluded by old PRE S/A, while preserving the legacy 94R baseline as a floor.
- script commit `57efd2eb99d43e1f4390c6a88bd14504b05987f9`.
- workflow commit `fdc021c4a3fb729a7c7033bee7b73eb70a917592`.
- Actions Run `34745869030` completed successfully.
- artifact `3head-wave15-expanded-source-replay`, artifact ID `10314256546`.
- result commit `572104107d5a292944d2554e07e64052ba9a9fc0`.
- expanded pool: **232R = old final-NO_BET 178R + old PRE-excluded 54R**.
- best method `return_rank@0.15`: **23 add-on races / 4 hits / hit rate 17.39% / ROI 55.00% / profit -103,500 yen / minimum monthly ROI 0% / 3 red months / max DD 121,980 yen / v288 overlap 0**.
- of those 23 selected races, **12 were formerly PRE-excluded**.
- combined legacy v288 + add-on: **117R / ROI 149.45%**.
- decision: **NO_ADOPTION_WAVE15** because add-on ROI remained far below break-even despite successfully recovering formerly excluded races.

## Wave16 — hierarchical source-group x attack-style — RUNNING
- purpose: distinguish profitable vs unprofitable cases inside the expanded pool instead of applying one global ranking.
- candidate population stays expanded: `OLD_NO_BET` + `OLD_PRE_EXCLUDED`, while legacy v288 94R is retained untouched as the floor.
- hierarchy: source group (`OLD_NO_BET` vs `OLD_PRE_EXCLUDED`) x attack style (`MAKURI` vs `MAKURISASHI`), with source-group fallback for sparse cells.
- variants: hit-oriented, exhibition-oriented, return/value-oriented, and independent consensus.
- walk-forward: prior-month-only Feb-Aug; Jul/Aug NON-PRISTINE; September outcomes forbidden.
- current required features fail closed; legacy-v288 overlap must be zero.
- script commit **`8f087c21ffb31a39c4e4acdcc8baba448aaa4492`**: `research_v289_3head_wave16_hierarchical_source_style.py`.
- workflow commit **`abdf3557daced58969f25b42fc0f23d32ee213fe`**: `.github/workflows/research-3head-wave16-hierarchical-source-style.yml`.
- Actions Run **`34747021942`** started from workflow push and was queued at the latest check.
- intended artifact: **`3head-wave16-hierarchical-source-style`**.

## Research conclusion from Wave15
- the new candidate source is valid operationally: previously excluded races can be recovered without touching the legacy 94R.
- Wave16 now tests whether source-group and attack-style conditioning can separate useful recovered races from the unprofitable majority.

## Exact restart point
1. Inspect Actions Run `34747021942` first.
2. If success: read `research_v289_3head_wave16_hierarchical_source_style.md/json`, record add-on R, hits/hit rate, ROI, profit, monthly, minimum monthly ROI, red months, max DD, source-group/style splits, v288 overlap, combined R/ROI, artifact ID and result commit SHA here.
3. If failed/cancelled: inspect job/logs, fix only the technical/scientific defect without weakening the guards, rerun automatically, and record the replacement Run ID.
4. If Wave16 is NO_ADOPTION, do not globally loosen thresholds. Continue with another population-conditional family, prioritizing explicit profitable-vs-unprofitable PRE-excluded discrimination or ticket-value structure within the expanded source.
5. Preserve legacy 94R as floor, Jul/Aug NON-PRISTINE, September outcomes unused, pre-deadline inputs only, current-required missing => fail closed, and no overlap with legacy v288.
