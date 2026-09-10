# v281 independent THIRD scenario model

- v96 is not used in features, training, candidate restriction, blending, or ordering; benchmark only after freeze.
- SECOND fixed to PLAYER_START / L2=10 from v280. THIRD family/L2 selected on Feb-Mar only.
- Scenario features include inside/outer identity, boat-4 current attack context, opponent-vs-4 foot gaps, and interactions.
- Optional P(third|second) transition prior is learned only from races before each evaluation month.
- Jul/Aug excluded; September not read; no odds.

## Frozen THIRD choice from Feb-Mar

- THIRD: **THIRD_SCENARIO_CURRENT**, L2 **0.3**, objective **48.52**
- SECOND: **PLAYER_START**, L2 **10**

### THIRD grid

|family|L2|R|T1|T2|objective|features|
|---|---:|---:|---:|---:|---:|---:|
|THIRD_SCENARIO_CURRENT|0.3|54|38.9%|63.0%|48.52|56|
|THIRD_SCENARIO_CURRENT|1|54|37.0%|61.1%|46.67|56|
|THIRD_SCENARIO_CURRENT|3|54|37.0%|61.1%|46.67|56|
|THIRD_PLAYER_START|0.3|54|37.0%|57.4%|45.19|25|
|THIRD_PLAYER_START|1|54|35.2%|57.4%|44.07|25|
|THIRD_SCENARIO_LIGHT|0.3|54|35.2%|57.4%|44.07|41|
|THIRD_SCENARIO_LIGHT|10|54|35.2%|57.4%|44.07|41|
|THIRD_RICH_SCENARIO|1|54|37.0%|53.7%|43.70|70|
|THIRD_SCENARIO_LIGHT|1|54|35.2%|55.6%|43.33|41|
|THIRD_PLAYER_START|3|54|33.3%|57.4%|42.96|25|
|THIRD_SCENARIO_LIGHT|3|54|33.3%|57.4%|42.96|41|
|THIRD_SCENARIO_CURRENT|10|54|31.5%|59.3%|42.59|56|
|THIRD_RICH_SCENARIO|0.3|54|33.3%|53.7%|41.48|70|
|THIRD_PLAYER_START|10|54|29.6%|53.7%|39.26|25|
|THIRD_RICH_SCENARIO|3|54|31.5%|50.0%|38.89|70|
|THIRD_RICH_SCENARIO|10|54|31.5%|48.1%|38.15|70|

## Pair composition frozen on Feb-Mar

- second weight alpha: **0.55**
- transition gamma: **0.75**
- tune T2/T4/T6/T10: **31.5% / 38.9% / 50.0% / 75.9%**

## Apr-Jun holdout-like result

|scope|R|2nd T1|T2|3rd T1|T2|Pair T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|ALL 4-head wins|87|41.4%|60.9%|27.6%|44.8%|16.1%|26.4%|42.5%|55.2%|77.0%|28.7%|44.8%|55.2%|75.9%|
|Frozen S+A head-wins|40|32.5%|55.0%|27.5%|37.5%|15.0%|22.5%|37.5%|52.5%|75.0%|35.0%|45.0%|57.5%|77.5%|

## S+A monthly

|month|R|T2|T4|T6|T10|v96 T2|T4|T6|T10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2026-04|11|27.3%|27.3%|27.3%|54.5%|27.3%|36.4%|36.4%|54.5%|
|2026-05|15|26.7%|46.7%|73.3%|86.7%|46.7%|53.3%|66.7%|86.7%|
|2026-06|14|14.3%|35.7%|50.0%|78.6%|28.6%|42.9%|64.3%|85.7%|

## Strongest THIRD coefficients (Apr-Jun fits, standardized)

|feature|mean beta|abs mean|months|
|---|---:|---:|---:|
|h4_attack_x_cur_orig_straight|-0.9691|0.9691|3|
|h4_attack_x_cur_st|+0.9605|0.9605|3|
|cur_orig_straight|+0.6908|0.6908|3|
|v93_national|+0.6823|0.6823|3|
|suf_st_corr_rank|+0.5607|0.5607|3|
|suf_st_raw_rank|+0.4902|0.4902|3|
|cur_orig_straight__vs4|+0.4741|0.4741|3|
|v93_nst|-0.4459|0.4459|3|
|suf_st_raw|-0.4246|0.4246|3|
|h4_attack_x_cur_orig_lap|-0.4058|0.4058|3|
|cur_orig_lap|+0.4032|0.4032|3|
|cur_orig_avg|-0.3867|0.3867|3|
|v93_grade|-0.3848|0.3848|3|
|h4_attack_x_is_inner_edge3|+0.3623|0.3623|3|
|pref_pl_frame_win|-0.3192|0.3192|3|
|v93_local|+0.2990|0.2990|3|
|cur_orig_lap__vs4|+0.2746|0.2746|3|
|cur_orig_avg__vs4|-0.2655|0.2655|3|

## Decision
- Continue independent opponent-model development; do not use v96 as a feature.
- If scenario/transition features improve THIRD and small-N pair coverage, use v281 as the next independent baseline.
- If not, next step is a dedicated conditional THIRD model P(third | predicted-second, race context), not a return to v96.
