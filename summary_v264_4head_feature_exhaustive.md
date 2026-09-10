# v264 4-head exhaustive feature audit

- Primary evaluation: Feb-Jun 2026 only; every month trains on earlier races only.
- Jul/Aug are excluded from this v264 audit.
- v221 player/prior-exhibition traits are frozen before the current day.
- Current-race ST/entry/wind/legacy POST fields are allowed only as pre-result final-selection features.
- Result/payout/ticket/actual-combination fields are explicitly excluded.
- Research/model-selection evidence only; not pristine validation.

## Variant diagnostics
|variant|features|AUC|best >=200R head rate|R|cut|
|---|---:|---:|---:|---:|---:|
|BASE_P4|2|0.5962|--|--|--|
|ST_3HEAD_ANALOG|66|0.5569|25.00%|212|0.2475|
|PLAYER_COURSE|68|0.5831|26.50%|200|0.2325|
|PRIOR_FOOT|252|0.5411|25.36%|209|0.1825|
|OPP_CONTEXT|42|0.6159|27.60%|221|0.1850|
|ENV_ENTRY|25|0.6362|28.84%|215|0.2325|
|ALL_SAFE_LINEAR|445|0.5681|27.50%|200|0.1375|
|ALL_SAFE_HGB|445|0.6019|26.70%|221|0.1100|

## Top-N realized head rate
|variant|N|heads|head rate|
|---|---:|---:|---:|
|BASE_P4|10|3|30.00%|
|BASE_P4|20|5|25.00%|
|BASE_P4|30|8|26.67%|
|BASE_P4|50|14|28.00%|
|BASE_P4|100|23|23.00%|
|BASE_P4|126|28|22.22%|
|BASE_P4|126|28|22.22%|
|BASE_P4|126|28|22.22%|
|BASE_P4 max cumulative >=40/50/60%|7/4/3|--|--|
|ST_3HEAD_ANALOG|10|2|20.00%|
|ST_3HEAD_ANALOG|20|4|20.00%|
|ST_3HEAD_ANALOG|30|7|23.33%|
|ST_3HEAD_ANALOG|50|15|30.00%|
|ST_3HEAD_ANALOG|100|27|27.00%|
|ST_3HEAD_ANALOG|150|37|24.67%|
|ST_3HEAD_ANALOG|200|52|26.00%|
|ST_3HEAD_ANALOG|300|71|23.67%|
|ST_3HEAD_ANALOG max cumulative >=40/50/60%|0/0/0|--|--|
|PLAYER_COURSE|10|2|20.00%|
|PLAYER_COURSE|20|5|25.00%|
|PLAYER_COURSE|30|7|23.33%|
|PLAYER_COURSE|50|15|30.00%|
|PLAYER_COURSE|100|25|25.00%|
|PLAYER_COURSE|150|42|28.00%|
|PLAYER_COURSE|200|53|26.50%|
|PLAYER_COURSE|300|72|24.00%|
|PLAYER_COURSE max cumulative >=40/50/60%|0/0/0|--|--|
|PRIOR_FOOT|10|1|10.00%|
|PRIOR_FOOT|20|2|10.00%|
|PRIOR_FOOT|30|3|10.00%|
|PRIOR_FOOT|50|9|18.00%|
|PRIOR_FOOT|100|25|25.00%|
|PRIOR_FOOT|150|35|23.33%|
|PRIOR_FOOT|200|50|25.00%|
|PRIOR_FOOT|300|71|23.67%|
|PRIOR_FOOT max cumulative >=40/50/60%|0/0/0|--|--|
|OPP_CONTEXT|10|4|40.00%|
|OPP_CONTEXT|20|7|35.00%|
|OPP_CONTEXT|30|10|33.33%|
|OPP_CONTEXT|50|16|32.00%|
|OPP_CONTEXT|100|28|28.00%|
|OPP_CONTEXT|150|43|28.67%|
|OPP_CONTEXT|200|56|28.00%|
|OPP_CONTEXT|300|76|25.33%|
|OPP_CONTEXT max cumulative >=40/50/60%|10/2/0|--|--|
|ENV_ENTRY|10|3|30.00%|
|ENV_ENTRY|20|6|30.00%|
|ENV_ENTRY|30|11|36.67%|
|ENV_ENTRY|50|18|36.00%|
|ENV_ENTRY|100|33|33.00%|
|ENV_ENTRY|150|44|29.33%|
|ENV_ENTRY|200|56|28.00%|
|ENV_ENTRY|300|76|25.33%|
|ENV_ENTRY max cumulative >=40/50/60%|27/4/0|--|--|
|ALL_SAFE_LINEAR|10|3|30.00%|
|ALL_SAFE_LINEAR|20|5|25.00%|
|ALL_SAFE_LINEAR|30|6|20.00%|
|ALL_SAFE_LINEAR|50|12|24.00%|
|ALL_SAFE_LINEAR|100|25|25.00%|
|ALL_SAFE_LINEAR|150|39|26.00%|
|ALL_SAFE_LINEAR|200|55|27.50%|
|ALL_SAFE_LINEAR|300|69|23.00%|
|ALL_SAFE_LINEAR max cumulative >=40/50/60%|2/2/1|--|--|
|ALL_SAFE_HGB|10|3|30.00%|
|ALL_SAFE_HGB|20|5|25.00%|
|ALL_SAFE_HGB|30|9|30.00%|
|ALL_SAFE_HGB|50|18|36.00%|
|ALL_SAFE_HGB|100|28|28.00%|
|ALL_SAFE_HGB|150|44|29.33%|
|ALL_SAFE_HGB|200|52|26.00%|
|ALL_SAFE_HGB|300|74|24.67%|
|ALL_SAFE_HGB max cumulative >=40/50/60%|7/4/3|--|--|

## Strongest individual features (retrospective descriptive)
|feature|oriented AUC|direction|top10 head rate|lift|
|---|---:|---|---:|---:|
|rel_pl_all_win_4v1|0.6463|high|44.07%|+20.25pt|
|rel_pl_all_p2_4v1|0.6411|high|35.59%|+11.78pt|
|rel_pl_recent_p2_4v1|0.6306|high|38.98%|+15.17pt|
|v91_ex|0.6270|high|38.98%|+15.17pt|
|score_wind_v83|0.6260|high|42.37%|+18.56pt|
|score_CORR20_v91|0.6253|high|37.29%|+13.47pt|
|b1_pl_all_p2|0.6221|low|35.59%|+11.78pt|
|score_RAW20_v91|0.6207|high|37.29%|+13.47pt|
|score_BASE_v91|0.6203|high|44.07%|+20.25pt|
|b1_pl_all_win|0.6197|low|30.51%|+6.69pt|
|preview_comp|0.6195|high|42.37%|+18.56pt|
|opp_national_b1_v93|0.6164|low|33.90%|+10.08pt|
|p4_joint|0.6159|high|40.68%|+16.86pt|
|POST|0.6156|high|37.29%|+13.47pt|
|opp_score_b1_v93|0.6141|low|33.90%|+10.08pt|
|PRE|0.6131|high|47.46%|+23.64pt|
|opp_grade_b1_v93|0.6108|low|32.20%|+8.39pt|
|b1_pl_frame_win|0.6086|low|37.29%|+13.47pt|
|rel_pl_frame_win_4v1|0.6022|high|37.29%|+13.47pt|
|b1_pl_frame_p2|0.5991|low|33.90%|+10.08pt|
|b4_pl_recent_p2|0.5966|high|38.98%|+15.17pt|
|b1_pl_frame_races|0.5961|low|37.29%|+13.47pt|
|rel_pl_recent_p2_4v5|0.5952|high|33.90%|+10.08pt|
|rel_pl_frame_p2_4v1|0.5930|high|37.29%|+13.47pt|
|rel_pl_all_win_4v5|0.5923|high|44.07%|+20.25pt|
|rel_pl_recent_p2_4v3|0.5921|high|30.51%|+6.69pt|
|rel_pl_frame_races_4v1|0.5904|high|37.29%|+13.47pt|
|rel_pl_all_win_4v3|0.5902|high|38.98%|+15.17pt|
|opp_nst_b1_v93|0.5861|low|33.90%|+10.08pt|
|post_x_entry_same|0.5860|high|38.98%|+15.17pt|
|b1_pl_recent_p2|0.5845|low|25.42%|+1.61pt|
|b2_vh_p2_display|0.5836|high|30.51%|+6.69pt|
|relative_deg|0.5836|high|32.65%|+9.36pt|
|rank_b1_v93|0.5770|high|35.59%|+11.78pt|
|opp_local_b1_v93|0.5769|low|25.42%|+1.61pt|

## ALL_SAFE_LINEAR coefficient stability
|feature|mean coef|sd|
|---|---:|---:|
|st_bias3_v90|+0.4265|0.0560|
|b3_vh_has2|+0.4136|0.0749|
|b2_vh_has1|+0.4133|0.2240|
|b4_vh_p2_straight|+0.4126|0.0214|
|PRE|+0.4113|nan|
|b4_gh_p2_straight|-0.3772|0.0222|
|opp_grade_b6_v93|-0.3661|0.0773|
|opp_grade_b5_v93|-0.3609|0.0257|
|b3_vh_has1|-0.3536|0.1684|
|b6_pl_frame_win|+0.3316|0.0417|
|b4_gh_p12_straight|-0.3274|0.0291|
|b6_pl_frame_p2|-0.3267|0.0182|
|b5_vh_p2_straight|+0.3239|0.0434|
|b1_vh_has2|-0.3179|0.1212|
|attack4_stretch_x_st|-0.3124|0.0364|
|st_bias4_v90|-0.2880|0.0324|
|st_raw_b1|+0.2808|0.0820|
|b5_gh_p2_straight|-0.2677|0.0627|
|b2_vh_p2_display|+0.2634|0.1199|
|opp_grade_b2_v93|-0.2579|0.0496|
|opp_nst_b1_v93|-0.2555|0.1043|
|b1_vh_p2_turn|-0.2539|0.0743|
|b4_gh_p2_display|+0.2531|0.0769|
|b6_vh_p12_straight|+0.2480|0.0186|
|b2_gh_delta_straight|+0.2272|0.0087|
|b3_vh_p2_overall|+0.2258|0.0559|
|b5_gh_delta_straight|+0.2208|0.0429|
|tilt|+0.2164|0.0565|
|opp_motor_b2_v93|+0.2143|0.1173|
|b2_vh_p2_straight|+0.2116|0.0152|
