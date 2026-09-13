# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Current policy
- research branch: `research/3head-v289-addon-expansion`
- legacy v288 production remains unchanged.
- legacy v288 baseline is a **floor, not a fixed research count**: 94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%.
- research should not reduce total selected races below 94R; expansion above 94R is allowed.
- candidate generation is now expanded beyond old PRE/final-NO_BET populations to the **full audited Feb-Aug race universe** wherever pre-deadline features and hypothetical settlement are scientifically usable.
- July/August are NON-PRISTINE.
- September outcomes are not loaded / not used for tuning.
- frozen canonical source: Run `34383567078`, artifact `v243-3head-expand-feature-audit`, artifact ID `10118044294`, max date 2026-08-31.
- all research inputs must be available before deadline; required-current missingness fails closed.
- overlap with legacy v288 must remain zero for add-on selections.
- 1 race stake remains JPY10,000; variable-count Dutch may be used when applicable.

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

## Wave16 — FINAL
- source-group x attack-style hierarchy.
- Run `34747021942` success; artifact `3head-wave16-hierarchical-source-style`, ID `10314003981`.
- result commit `a89e5f5f5f6c1b84875d4e72cadb9f97693bf229`.
- best `consensus@0.15`: **12 add-on / 1 hit / ROI 26.07% / profit -88,720 / combined 106R / combined ROI 155.98%**.
- PRE-excluded selected = 0.
- **NO_ADOPTION_WAVE16**.

## Wave17 — FINAL
- source-specific hurdle EV.
- Run `34747412436` completed success.
- best `frac=0.15`: **10 add-on / 1 hit / hit rate 10.00% / ROI 31.36% / profit -68,640 / min month 0% / 3 red / max DD 68,640 / combined 104R / combined ROI 158.98%**.
- PRE-excluded selected = 0 for every tested fraction.
- **NO_ADOPTION_WAVE17**.
- conclusion: treating the 54 old PRE-excluded rows as the broadened universe is still too restrictive; user explicitly requested full-population candidate generation.

## Wave18 — full-universe candidate generation — RUNNING
- user-directed scope correction: do **not** treat the 54 PRE-excluded rows as the full unexplored universe.
- scientific goal: start from all races present in the frozen Feb-Aug v243 audit source, excluding only the unchanged legacy v288 94R baseline, with **no `bet==1`, PRE grade, or old route prefilter**.
- first guard: audit whether BET=0 rows contain usable hypothetical 3-head settlement (`ret` / `trifecta_hit`). If they do, run prior-month-only full-universe ranking. If they do not, return `SOURCE_REBUILD_REQUIRED_WAVE18` and immediately rebuild an all-race settled 3-head source rather than fabricating ROI.
- ranking family if settlement is usable: full-universe hit + value + current exhibition consensus, fail-closed on required-current features.
- fractions: 1%, 2%, 3%, 5%, 8%, 10% of prior-month score distribution; this is not a global loosening of v288 because the candidate source itself is rebuilt from all audited rows.
- script commit **`bdbca654eee835ef9906d8c656fc0a29955d933c`**: `research_v289_3head_wave18_full_universe.py`.
- workflow commit **`57987f13d9a2676c7b69cd58102a1ac1ec1020f9`**: `.github/workflows/research-3head-wave18-full-universe.yml`.
- Actions Run **`34748886697`** queued at latest check.
- intended artifact: **`3head-wave18-full-universe`**.

## Exact restart point
1. Inspect Actions Run `34748886697` first.
2. If success: read `research_v289_3head_wave18_full_universe.md/json` and record source unique-race count, full universe size excluding baseline, BET=0 count, BET=0 hypothetical-settlement coverage, add-on metrics if modeled, monthly/min-month/red-month/max-DD, overlap, combined R/ROI, artifact ID, result commit SHA, decision and reason.
3. If decision is `SOURCE_REBUILD_REQUIRED_WAVE18`, immediately implement a new frozen **all-race 3-head settled source** covering Feb-Aug from pre-deadline inputs plus post-race settlement only for evaluation; do not use outcome fields as model inputs. Then rerun full-universe walk-forward research against that rebuilt source.
4. If Wave18 runs full-universe scoring but is NO_ADOPTION, proceed to a distinct full-population latent-regime / analog / ticket-rerank family rather than reverting to the old 232R pool.
5. Preserve legacy 94R floor, Jul/Aug NON-PRISTINE, September outcomes unused, pre-deadline inputs only, current-required missing => fail closed, no overlap with legacy v288, and JPY10,000 per race.
