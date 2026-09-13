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

## Research conclusion from Wave15
- the new candidate source is valid operationally: previously excluded races can be recovered without touching the legacy 94R.
- the next useful question is not whether PRE-excluded races exist, but how to distinguish profitable vs unprofitable PRE-excluded/NO_BET cases under prior-month-only training.
- because the population changed, source-group-specific and attack-style-specific re-evaluation of earlier signal families is allowed.

## Current blocker / restart state
- Wave15 finished and the previous handoff had not been updated; this file now repairs that gap.
- attempted next implementation: a source-group x attack-style hierarchical Wave16 over the expanded pool, with prior-month-only training and fail-closed current features.
- repository write for the new Wave16 script was blocked by the connected GitHub write safety layer before a commit could be created. No scientific guard was weakened and no Wave16 Run exists yet.

## Exact restart point
1. First inspect whether a Wave16 implementation or newer 3-head commit has appeared since this handoff.
2. If not, resume with a genuinely population-conditional expanded-source method rather than a global threshold relaxation. Preferred next family: source-group (`OLD_NO_BET` vs `OLD_PRE_EXCLUDED`) x attack-style (makuri-like vs makuri-sashi-like) hierarchical models, with source-group fallback only for sparse cells.
3. Compare hit-oriented, exhibition-upgrade, return/value, and independent-consensus variants using prior-month-only walk-forward Feb-Aug.
4. Preserve: legacy 94R as floor, Jul/Aug NON-PRISTINE, September outcomes unused, pre-deadline inputs only, missing-current fail closed, no legacy-v288 overlap.
5. For every completed experiment record add-on races, hits/hit rate, ROI, profit, monthly metrics, minimum monthly ROI, red months, max DD, legacy-v288 overlap, combined race count and combined ROI, Run ID, artifact name/ID, result commit SHA, decision, rejection/adoption reason, and the next restart point here.
