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
All prior Wave1-13 proposals were rejected. Stable earlier results remain in repository result files. Because the candidate population changed, prior signal families may be re-tested on the expanded population, but simple global threshold relaxation remains disallowed.

## Wave14 — FINAL
- Run `34741605409` success.
- artifact `v289-3head-addon-wave14-conformal-market`, ID `10313288111`.
- result commit `c921aa8dc71e835d91015a83e865888d6eb33dc0`.
- best: 99R / 4 hits / ROI 33.74% / profit -656,020 yen.
- **NO_ADOPTION_WAVE14**.

## Wave15 — FINAL
- expanded pool: **232R = old final-NO_BET 178R + old PRE-excluded 54R**.
- Run `34745869030` success; artifact `3head-wave15-expanded-source-replay`, ID `10314256546`.
- result commit `572104107d5a292944d2554e07e64052ba9a9fc0`.
- best `return_rank@0.15`: **23 add-on / 4 hits / ROI 55.00% / profit -103,500 / min month 0% / 3 red / max DD 121,980 / overlap 0**; 12 selected races were PRE-excluded.
- combined: **117R / ROI 149.45%**.
- **NO_ADOPTION_WAVE15**.

## Wave16 — hierarchical source-group x attack-style — FINAL
- purpose: source group (`OLD_NO_BET` vs `OLD_PRE_EXCLUDED`) x attack style (`MAKURI` vs `MAKURISASHI`) hierarchical modeling.
- script commit `8f087c21ffb31a39c4e4acdcc8baba448aaa4492`.
- workflow commit `abdf3557daced58969f25b42fc0f23d32ee213fe`.
- Actions Run **`34747021942` completed success**.
- artifact **`3head-wave16-hierarchical-source-style`**, artifact ID **`10314003981`**.
- result commit **`a89e5f5f5f6c1b84875d4e72cadb9f97693bf229`**.
- best `consensus@0.15`: **12 add-on / 1 hit / hit rate 8.33% / ROI 26.07% / profit -88,720 / min month 0% / 3 red / max DD 88,720 / combined 106R / combined ROI 155.98%**.
- critical result: **all Wave16 selected rows had PRE-excluded selected = 0**. The hierarchy failed to recover the new source population.
- **NO_ADOPTION_WAVE16**.
- rejection reason: severe negative add-on EV and no PRE-excluded recovery despite explicit source/style conditioning.

## Wave17 — source-specific hurdle EV — RUNNING
- restart reason: Wave16 completed NO_ADOPTION and no next research had started; automation resumed immediately from the exact handoff point.
- scientific goal: explicitly discriminate profitable vs unprofitable races separately inside `OLD_NO_BET` and `OLD_PRE_EXCLUDED`, rather than letting the old source dominate rankings.
- model family: source-specific independent hit probability + positive-profit hurdle probability + settled-value regression + pre-deadline market/composite-odds consensus.
- current required selected features fail closed.
- prior-month-only walk-forward Feb-Aug; Jul/Aug NON-PRISTINE; September outcomes forbidden.
- legacy 94R is a floor and remains untouched; overlap with legacy v288 must be 0.
- script commit **`f9bb2d7e2e17cab922a216b8e20577526916000b`**: `research_v289_3head_wave17_source_hurdle_ev.py`.
- workflow commit **`1883d39c46fc229b05e0648d34561d8221df838f`**: `.github/workflows/research-3head-wave17-source-hurdle-ev.yml`.
- Actions Run **`34747412436`** queued at the latest check.
- intended artifact: **`3head-wave17-source-hurdle-ev`**.

## Exact restart point
1. Inspect Actions Run `34747412436` first.
2. If success: read `research_v289_3head_wave17_source_hurdle_ev.md/json`; record add-on R, hits/hit rate, ROI, profit, monthly, min monthly ROI, red months, max DD, source-group metrics including PRE-excluded selected count, v288 overlap, combined R/ROI, artifact ID, result commit SHA, decision and rejection/adoption reason here.
3. If failed/cancelled: inspect failed job/log, fix the technical/scientific defect without weakening guards, rerun automatically, and record replacement Run ID.
4. If Wave17 is NO_ADOPTION, continue to another expanded-population family without global threshold loosening. Prefer a distinct ticket-value / latent-regime / analog-family approach that forces evaluation of PRE-excluded rows rather than allowing them to disappear from selection.
5. Preserve legacy 94R floor, Jul/Aug NON-PRISTINE, September outcomes unused, pre-deadline inputs only, current-required missing => fail closed, no overlap with legacy v288, and JPY10,000 per race.
