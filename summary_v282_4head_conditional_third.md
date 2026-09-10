# v282 independent conditional THIRD model

- SECOND: independent PLAYER_START/L2=10. THIRD is P(third | candidate second, pre-result context).
- No v96 feature/order/candidate restriction/blending. v96 is benchmark only after freeze.
- THIRD family/L2 and pair alpha selected on Feb-Mar only; Apr-Jun untouched holdout-like evaluation.
- Jul/Aug excluded; September not read; no odds.

## Conditional THIRD choice (Feb-Mar)

- family: **COND_BASE**
- L2: **0.3**
- conditional THIRD Top1/Top2: **35.2% / 70.4%**

|family|L2|R|cond T1|T2|objective|features|
|---|---:|---:|---:|---:|---:|---:|
|COND_BASE|0.3|54|35.2%|70.4%|49.26|69|
|COND_DIFF|0.3|54|35.2%|70.4%|49.26|88|
|COND_COMPACT|0.3|54|33.3%|72.2%|48.89|67|
|COND_COMPACT|1|54|33.3%|72.2%|48.89|67|
|COND_COMPACT|3|54|33.3%|72.2%|48.89|67|
|COND_DIFF|1|54|33.3%|70.4%|48.15|88|
|COND_BASE|10|54|35.2%|66.7%|47.78|69|
|COND_DIFF|3|54|33.3%|68.5%|47.41|88|
|COND_DIFF|10|54|35.2%|64.8%|47.04|88|
|COND_DIFF_PROD|10|54|31.5%|70.4%|47.04|107|
|COND_DIFF_PROD|3|54|33.3%|66.7%|46.67|107|
|COND_COMPACT|10|54|31.5%|68.5%|46.30|67|
|COND_BASE|1|54|31.5%|66.7%|45.56|69|
|COND_BASE|3|54|29.6%|68.5%|45.19|69|
|COND_DIFF_PROD|1|54|29.6%|64.8%|43.70|107|
|COND_DIFF_PROD|0.3|54|27.8%|63.0%|41.85|107|

## Pair alpha frozen on Feb-Mar

- alpha2: **0.65**
- tune T2/T4/T6/T10: **27.8% / 40.7% / 55.6% / 74.1%**

## Apr-Jun holdout-like result

|scope|R|2nd T1|T2|cond 3rd T1|T2|Pair T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|ALL 4-head wins|87|41.4%|60.9%|40.2%|69.0%|21.8%|34.5%|44.8%|57.5%|67.8%|28.7%|44.8%|55.2%|75.9%|
|Frozen S+A head-wins|40|32.5%|55.0%|37.5%|67.5%|12.5%|25.0%|35.0%|50.0%|65.0%|35.0%|45.0%|57.5%|77.5%|

## S+A monthly

|month|R|T2|T4|T6|T10|v96 T2|T4|T6|T10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2026-04|11|36.4%|36.4%|45.5%|63.6%|27.3%|36.4%|36.4%|54.5%|
|2026-05|15|26.7%|33.3%|53.3%|66.7%|46.7%|53.3%|66.7%|86.7%|
|2026-06|14|14.3%|35.7%|50.0%|64.3%|28.6%|42.9%|64.3%|85.7%|

## Strongest conditional THIRD coefficients (Apr-Jun fits)

|feature|mean beta|abs mean|months|
|---|---:|---:|---:|
|t_h4_attack_x_cur_st|+1.0377|1.0377|3|
|t_h4_attack_x_cur_orig_straight|-0.8317|0.8317|3|
|t_suf_st_corr_rank|+0.7899|0.7899|3|
|t_h4_attack_x_cur_orig_lap|-0.6569|0.6569|3|
|t_v93_national|+0.6500|0.6500|3|
|t_suf_st_raw_rank|+0.6363|0.6363|3|
|t_cur_orig_straight|+0.5521|0.5521|3|
|t_cur_orig_lap|+0.4951|0.4951|3|
|t_suf_st_raw|-0.4436|0.4436|3|
|t_v93_nst|-0.4099|0.4099|3|
|t_cur_orig_straight__vs4|+0.3782|0.3782|3|
|t_pref_pl_all_p2|+0.3398|0.3398|3|
|t_cur_orig_lap__vs4|+0.3365|0.3365|3|
|pair_distance|+0.2915|0.2915|3|
|pair_adjacent|+0.2857|0.2857|3|
|t_cur_st__abs4|+0.2810|0.2810|3|
|t_v93_local|+0.2748|0.2748|3|
|t_h4_attack_x_is_outer_edge5|+0.2720|0.2720|3|
|t_pref_pl_recent_p2|-0.2679|0.2679|3|
|t_h4_attack_x_is_inner_edge3|+0.2575|0.2575|3|

## Decision
- This remains an independent opponent-model branch; v96 is not a fallback feature.
- If conditional THIRD improves Apr-Jun small-N pair coverage, promote it to the next candidate and then test exact 10,000-yen Dutch economics.
- Otherwise research should focus on regime-splitting the conditional THIRD task (inner-survival vs outer-follow) with all regime choices frozen on pre-Apr data.
