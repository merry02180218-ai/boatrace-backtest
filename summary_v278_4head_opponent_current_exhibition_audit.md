# v278 4-head opponent current-exhibition component audit

- Code audit: v93/v96 direct = 35% current display + 20% prior-only corrected ST strength + 25% current original turn + 20% current original average.
- Therefore current start-exhibition itself and separate current original lap/straight were not explicit v96 opponent features.
- v278 decomposes current display, current start exhibition, lap, turn, straight and average.
- Jul/Aug excluded; September not read; no odds; head selectors unchanged.

## SECOND: current exhibition components

|feature|direction|AUC|Top1|Top2|month +|
|---|---|---:|---:|---:|---:|
|cur_orig_lap|high|0.6217|28.4%|54.6%|5/5|
|cur_orig_avg|high|0.6128|31.9%|53.9%|4/5|
|cur_st|high|0.5632|24.3%|48.6%|4/5|
|cur_orig_straight|high|0.5443|29.1%|46.1%|4/5|
|cur_orig_turn|high|0.5307|18.4%|44.0%|3/5|
|cur_ex|low|0.5010|23.6%|42.1%|4/5|

## THIRD: current exhibition components

|feature|direction|AUC|Top1|Top2|month +|
|---|---|---:|---:|---:|---:|
|cur_orig_turn|high|0.5334|24.8%|43.3%|4/5|
|cur_st|low|0.5331|26.4%|41.4%|3/5|
|cur_ex|high|0.5301|24.3%|42.1%|3/5|
|cur_orig_lap|high|0.5258|19.9%|44.7%|3/5|
|cur_orig_straight|low|0.5106|26.2%|44.0%|3/5|
|cur_orig_avg|high|0.5071|20.6%|39.7%|3/5|

## Apr-Jun role-model pair comparison

|scope|family|R|T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|HOLD_ALL|BASE_CURRENT_PLAYER|87|17.2%|32.2%|42.5%|49.4%|72.4%|28.7%|44.8%|55.2%|75.9%|
|HOLD_ALL|BASE_CURRENT|87|12.6%|25.3%|36.8%|50.6%|67.8%|28.7%|44.8%|55.2%|75.9%|
|HOLD_ALL|CURRENT_ONLY|87|8.0%|16.1%|33.3%|39.1%|62.1%|28.7%|44.8%|55.2%|75.9%|
|HOLD_SA|BASE_CURRENT_PLAYER|40|15.0%|27.5%|40.0%|45.0%|75.0%|35.0%|45.0%|57.5%|77.5%|
|HOLD_SA|BASE_CURRENT|40|10.0%|22.5%|37.5%|50.0%|67.5%|35.0%|45.0%|57.5%|77.5%|
|HOLD_SA|CURRENT_ONLY|40|7.5%|12.5%|32.5%|42.5%|65.0%|35.0%|45.0%|57.5%|77.5%|

## Finding
- Strongest stable decomposed current component: **cur_orig_lap** for SECOND, AUC 0.6217, month consistency 5/5.
- Do not replace v96 from this audit alone. If one or more current components are stable, the next safe test is a v96 Top4-preserving tiebreak using only those components, analogous to v277.
- This keeps the robust v96 candidate set while testing whether current exhibition can improve ordering inside that set.
