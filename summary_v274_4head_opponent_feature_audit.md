# v274 4-head opponent feature audit

- discovered safe opponent features: **60**
- conditional boat-4-win races in long data: **207**
- Evaluation months: Feb-Jun 2026; every month trains only on earlier boat-4-win races.
- Jul/Aug excluded completely; September not read.
- 2nd and 3rd have separate models; pair score combines role probabilities only after role scoring.
- No odds in feature training/ranking. v96 is the current opponent-order baseline.
- Retrospective feature research/model selection only; not pristine OOS.

## SECOND: strongest individual pre-result features

|rank|feature|category|direction|AUC|Top1|Top2|month +|
|---:|---|---|---|---:|---:|---:|---:|
|1|pref_pl_all_p2|PLAYER_HISTORY|high|0.6676|33.3%|61.7%|5/5|
|2|v93_national|V93_BASE_CONTEXT|high|0.6663|36.2%|62.4%|5/5|
|3|pref_pl_all_win|PLAYER_HISTORY|high|0.6658|32.6%|60.3%|5/5|
|4|pref_pl_frame_p2|PLAYER_HISTORY|high|0.6645|36.9%|56.7%|5/5|
|5|v93_score|V93_BASE_CONTEXT|high|0.6604|32.6%|58.2%|5/5|
|6|pref_pl_recent_p2|PLAYER_HISTORY|high|0.6597|31.2%|62.4%|5/5|
|7|v93_local|V93_BASE_CONTEXT|high|0.6517|34.8%|58.2%|5/5|
|8|pref_pl_frame_win|PLAYER_HISTORY|high|0.6458|35.5%|53.2%|5/5|
|9|v93_rank|V93_BASE_CONTEXT|low|0.6436|32.6%|58.2%|5/5|
|10|v93_grade|V93_BASE_CONTEXT|high|0.6407|39.7%|58.9%|5/5|
|11|pos_boat_number|POSITION|low|0.6170|35.5%|57.4%|5/5|
|12|pos_distance4|POSITION|high|0.6161|35.5%|57.4%|5/5|
|13|v93_nst|V93_BASE_CONTEXT|high|0.5815|26.2%|53.2%|4/5|
|14|pref_pl_frame_races|PLAYER_HISTORY|high|0.5705|31.2%|51.1%|5/5|
|15|suf_st_raw_strength|START|high|0.5632|24.1%|48.9%|3/5|
|16|v93_direct|V93_BASE_CONTEXT|high|0.5581|22.7%|48.9%|4/5|
|17|suf_st_raw_rank|START|low|0.5523|24.1%|48.2%|4/5|
|18|pref_gh_delta_display|PRIOR_EXHIBITION|low|0.5503|24.8%|47.5%|4/5|
|19|suf_st_corr_strength|START|high|0.5503|22.7%|46.1%|3/5|
|20|pref_vh_delta_display|PRIOR_EXHIBITION|low|0.5456|26.2%|52.5%|3/5|
|21|suf_st_corr_rank|START|low|0.5405|22.7%|45.4%|3/5|
|22|suf_st_raw|START|low|0.5399|23.6%|48.8%|3/5|
|23|pref_gh_p2_turn|PRIOR_EXHIBITION|high|0.5396|24.8%|46.1%|4/5|
|24|pref_vh_p2_turn|PRIOR_EXHIBITION|high|0.5395|25.5%|47.5%|3/5|
|25|pref_gh_p2_overall|PRIOR_EXHIBITION|high|0.5390|22.0%|46.8%|4/5|

## THIRD: strongest individual pre-result features

|rank|feature|category|direction|AUC|Top1|Top2|month +|
|---:|---|---|---|---:|---:|---:|---:|
|1|v93_rank|V93_BASE_CONTEXT|low|0.6241|31.2%|51.1%|5/5|
|2|v93_national|V93_BASE_CONTEXT|high|0.6132|30.5%|51.8%|5/5|
|3|v93_score|V93_BASE_CONTEXT|high|0.6122|31.2%|51.1%|5/5|
|4|pref_pl_all_p2|PLAYER_HISTORY|high|0.5996|29.1%|53.9%|5/5|
|5|pref_pl_all_win|PLAYER_HISTORY|high|0.5985|27.7%|51.8%|5/5|
|6|v93_local|V93_BASE_CONTEXT|high|0.5928|26.2%|52.5%|5/5|
|7|pref_pl_recent_p2|PLAYER_HISTORY|high|0.5879|28.4%|46.1%|5/5|
|8|v93_grade|V93_BASE_CONTEXT|high|0.5830|22.0%|51.1%|4/5|
|9|pref_vh_delta_overall|PRIOR_EXHIBITION|low|0.5524|28.4%|48.2%|3/5|
|10|v93_nst|V93_BASE_CONTEXT|high|0.5518|23.4%|41.8%|3/5|
|11|pos_distance4|POSITION|high|0.5452|21.3%|41.8%|4/5|
|12|pref_gh_p2_turn|PRIOR_EXHIBITION|high|0.5403|22.0%|45.4%|3/5|
|13|pref_gh_p2_overall|PRIOR_EXHIBITION|high|0.5392|24.8%|48.2%|3/5|
|14|pref_vh_delta_turn|PRIOR_EXHIBITION|low|0.5383|29.8%|44.7%|3/5|
|15|pos_boat_number|POSITION|high|0.5372|26.2%|51.8%|4/5|
|16|pref_gh_delta_turn|PRIOR_EXHIBITION|low|0.5349|29.1%|40.4%|4/5|
|17|pref_gh_delta_overall|PRIOR_EXHIBITION|low|0.5348|29.1%|43.3%|3/5|
|18|pref_pl_frame_races|PLAYER_HISTORY|high|0.5340|22.7%|44.0%|4/5|
|19|suf_st_raw_strength|START|low|0.5331|26.2%|41.1%|3/5|
|20|pref_vh_p1_straight|PRIOR_EXHIBITION|low|0.5327|22.0%|47.5%|4/5|
|21|pref_vh_p2_overall|PRIOR_EXHIBITION|high|0.5313|23.4%|48.2%|3/5|
|22|pref_vh_p12_straight|PRIOR_EXHIBITION|low|0.5299|21.3%|44.7%|4/5|
|23|pref_vh_p12_display|PRIOR_EXHIBITION|high|0.5296|17.7%|44.0%|3/5|
|24|pref_gh_p12_display|PRIOR_EXHIBITION|high|0.5293|17.0%|47.5%|3/5|
|25|pref_vh_delta_straight|PRIOR_EXHIBITION|low|0.5292|22.7%|44.7%|4/5|

## Walk-forward family comparison: all boat-4 wins

|family|R|2nd T1|2nd T2|3rd T1|3rd T2|pair T2|T4|T6|T10|v96 T10|ΔT10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|BASE7_PRIOR|141|34.8%|61.7%|27.7%|48.9%|23.4%|37.6%|53.9%|73.8%|77.3%|-3.5pt|
|BASE7_PLAYER|141|39.0%|60.3%|29.1%|49.6%|26.2%|42.6%|51.8%|73.8%|77.3%|-3.5pt|
|BASE7|141|35.5%|60.3%|30.5%|51.1%|25.5%|39.0%|55.3%|73.0%|77.3%|-4.3pt|
|BASE7_CONTEXT|141|38.3%|61.0%|29.8%|49.6%|23.4%|41.1%|54.6%|73.0%|77.3%|-4.3pt|
|BASE7_ST|141|38.3%|61.0%|30.5%|51.1%|24.8%|35.5%|53.9%|73.0%|77.3%|-4.3pt|
|BASE7_PLAYER_PRIOR|141|36.9%|58.9%|25.5%|48.9%|26.2%|39.0%|55.3%|71.6%|77.3%|-5.7pt|
|ALL_RICH|141|39.0%|60.3%|27.0%|46.8%|23.4%|37.6%|53.9%|70.9%|77.3%|-6.4pt|

## Frozen v268+v273 S+A selected head-wins (Apr-Jun)

This scope changes only opponent ordering; the frozen head selectors are not retuned.

|family|4-head hit R|pair T2|T4|T6|T10|v96 T2|T4|T6|T10|ΔT10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|BASE7_PLAYER|40|27.5%|35.0%|42.5%|80.0%|35.0%|45.0%|57.5%|77.5%|+2.5pt|
|BASE7_PLAYER_PRIOR|40|27.5%|32.5%|52.5%|75.0%|35.0%|45.0%|57.5%|77.5%|-2.5pt|
|BASE7_CONTEXT|40|27.5%|37.5%|55.0%|70.0%|35.0%|45.0%|57.5%|77.5%|-7.5pt|
|BASE7|40|25.0%|35.0%|52.5%|70.0%|35.0%|45.0%|57.5%|77.5%|-7.5pt|
|ALL_RICH|40|25.0%|30.0%|47.5%|70.0%|35.0%|45.0%|57.5%|77.5%|-7.5pt|
|BASE7_PRIOR|40|22.5%|35.0%|55.0%|67.5%|35.0%|45.0%|57.5%|77.5%|-10.0pt|
|BASE7_ST|40|25.0%|30.0%|52.5%|67.5%|35.0%|45.0%|57.5%|77.5%|-10.0pt|

## Research decision
- Best S+A expansion family by pre-declared coverage score: **BASE7_PLAYER_PRIOR**.
- On selected boat-4 wins: Top4 32.5% vs v96 45.0%, Top6 52.5% vs 57.5%, Top10 75.0% vs 77.5%.
- Do not adopt from v274 alone. Next stage should freeze the best feature family and test exact current 10,000-yen Dutch/composite-odds economics against v96 on the same frozen S+A races.
- Any opponent model intended for prospective use must be frozen before September outcomes are inspected.
