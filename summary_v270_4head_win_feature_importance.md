# v270 4-head historical win feature importance

- Research sample: Feb-Jun 2026, 592 races, boat-4 wins=141, base head rate=23.82%.
- July/August 2026 excluded completely.
- Leakage/result/payout/ticket fields excluded from candidate inputs using v264 safe-feature rules.
- `top10/top20 lift` is descriptive; `delta OOF AUC` asks whether the feature adds information beyond PRE+POST in month walk-forward predictions.
- This is retrospective feature research/model selection, not pristine validation.

## Feature-family priority
|category|features|best AUC|mean top20 lift|best +OOF AUC|mean month consistency|
|---|---:|---:|---:|---:|---:|
|当日展示_風_環境|13|0.6270|+6.22pt|+0.0551|83.1%|
|4号艇vs1号艇_選手力差|6|0.6463|+11.65pt|+0.0329|96.7%|
|相手構成_v93|40|0.6164|+2.50pt|+0.0346|73.5%|
|4号艇vs他艇_選手力差|24|0.5952|+4.20pt|+0.0377|76.7%|
|1号艇_選手力弱さ|6|0.6221|+10.58pt|+0.0115|100.0%|
|4号艇_選手力|6|0.5966|+4.99pt|+0.0267|76.7%|
|その他|154|0.5836|+2.12pt|+0.0177|66.6%|
|PRE_POST総合|4|0.6159|+12.32pt|+0.0000|100.0%|
|4号艇_過去展示機力|32|0.5712|+2.40pt|+0.0274|67.5%|
|4号艇vs他艇_過去展示差|32|0.5573|+1.58pt|+0.0189|65.0%|
|1号艇_過去展示機力|32|0.5647|+3.44pt|+0.0085|65.0%|
|ST攻撃力_壁|64|0.5686|+2.20pt|+0.0078|64.1%|
|4号艇vs1号艇_過去展示差|8|0.5594|+4.74pt|+0.0049|72.5%|
|進入_データ確定度|1|0.5042|+0.17pt|--|80.0%|

## Most important individual features
|rank|feature|category|direction|AUC|top10 head|top20 head|month consistency|+OOF AUC vs PRE/POST|OOF months +|score|
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
|1|v91_ex|当日展示_風_環境|high|0.6270|36.72%|36.72%|100%|+0.0551|3/3|33.31|
|2|score_CORR20_v91|当日展示_風_環境|high|0.6253|36.67%|34.45%|100%|+0.0520|3/3|32.05|
|3|score_wind_v83|当日展示_風_環境|high|0.6260|43.33%|33.61%|100%|+0.0505|3/3|31.66|
|4|score_RAW20_v91|当日展示_風_環境|high|0.6207|36.67%|34.45%|100%|+0.0492|3/3|31.04|
|5|score_BASE_v91|当日展示_風_環境|high|0.6203|43.33%|33.61%|100%|+0.0469|3/3|30.36|
|6|rel_pl_all_win_4v1|4号艇vs1号艇_選手力差|high|0.6463|45.00%|37.82%|100%|+0.0275|3/3|29.93|
|7|preview_comp|当日展示_風_環境|high|0.6195|42.62%|34.45%|80%|+0.0459|3/3|29.25|
|8|rel_pl_all_p2_4v1|4号艇vs1号艇_選手力差|high|0.6411|35.00%|36.13%|100%|+0.0273|3/3|29.04|
|9|rel_pl_recent_p2_4v1|4号艇vs1号艇_選手力差|high|0.6306|40.62%|34.85%|100%|+0.0329|3/3|28.84|
|10|opp_grade_b1_v93|相手構成_v93|low|0.6108|30.37%|30.37%|100%|+0.0346|3/3|26.31|
|11|opp_score_b1_v93|相手構成_v93|low|0.6141|35.00%|34.45%|100%|+0.0283|3/3|26.21|
|12|rel_pl_recent_p2_4v3|4号艇vs他艇_選手力差|high|0.5921|29.41%|31.71%|100%|+0.0377|3/3|25.33|
|13|opp_national_b1_v93|相手構成_v93|low|0.6164|33.33%|32.77%|100%|+0.0224|3/3|24.91|
|14|b1_pl_all_win|1号艇_選手力弱さ|low|0.6197|31.67%|36.13%|100%|+0.0115|3/3|23.73|
|15|b1_pl_all_p2|1号艇_選手力弱さ|low|0.6221|35.00%|35.29%|100%|+0.0105|3/3|23.61|
|16|b4_pl_recent_p2|4号艇_選手力|high|0.5966|32.26%|31.54%|100%|+0.0267|3/3|23.54|
|17|rel_pl_frame_races_4v1|4号艇vs1号艇_選手力差|high|0.5904|32.35%|36.23%|100%|+0.0225|2/3|22.35|
|18|rel_pl_recent_p2_4v5|4号艇vs他艇_選手力差|high|0.5952|35.21%|30.53%|100%|+0.0204|3/3|21.94|
|19|b1_pl_frame_win|1号艇_選手力弱さ|low|0.6086|38.33%|36.36%|100%|+0.0071|3/3|21.80|
|20|rel_pl_frame_win_4v1|4号艇vs1号艇_選手力差|high|0.6022|36.67%|31.93%|80%|+0.0109|3/3|20.03|
|21|rel_pl_all_win_4v5|4号艇vs他艇_選手力差|high|0.5923|45.00%|33.61%|100%|+0.0092|3/3|20.03|
|22|b2_vh_p2_display|その他|high|0.5836|33.33%|27.92%|100%|+0.0177|3/3|19.72|
|23|p4_joint|PRE_POST総合|high|0.6159|40.00%|36.13%|100%|-0.0006|1/3|19.72|
|24|rel_pl_all_win_4v3|4号艇vs他艇_選手力差|high|0.5902|38.33%|31.09%|80%|+0.0157|3/3|19.62|
|25|rank_b1_v93|相手構成_v93|high|0.5770|33.87%|30.15%|100%|+0.0165|3/3|19.27|
|26|POST|PRE_POST総合|high|0.6156|36.67%|35.29%|100%|+0.0000|0/3|18.85|
|27|rel_pl_all_p2_4v3|4号艇vs他艇_選手力差|high|0.5711|36.67%|34.45%|80%|+0.0179|3/3|18.81|
|28|rel_pl_frame_p2_4v1|4号艇vs1号艇_選手力差|high|0.5930|36.67%|35.83%|100%|+0.0032|2/3|18.68|
|29|PRE|PRE_POST総合|high|0.6131|46.67%|35.29%|100%|+0.0000|0/3|18.61|
|30|opp_nst_b1_v93|相手構成_v93|low|0.5861|31.08%|30.30%|100%|+0.0109|2/3|18.42|
|31|b4_gh_delta_display|4号艇_過去展示機力|low|0.5709|32.88%|31.06%|60%|+0.0274|2/3|18.35|
|32|b1_pl_frame_p2|1号艇_選手力弱さ|low|0.5991|33.85%|32.50%|100%|+0.0013|2/3|18.24|
|33|b1_pl_frame_races|1号艇_選手力弱さ|low|0.5961|36.92%|34.96%|100%|-0.0015|2/3|18.18|
|34|relative_deg|当日展示_風_環境|high|0.5836|29.91%|29.91%|80%|+0.0118|2/3|17.37|
|35|b2_vh_delta_display|その他|low|0.5767|31.00%|29.17%|100%|+0.0113|2/3|17.33|
|36|rel_vh_p12_display_4v5|4号艇vs他艇_過去展示差|high|0.5573|31.67%|30.08%|100%|+0.0189|2/3|17.09|
|37|post_x_entry_same|PRE_POST総合|high|0.5860|38.33%|37.82%|100%|-0.0010|1/3|17.07|
|38|b4_pl_all_win|4号艇_選手力|high|0.5672|43.33%|30.25%|100%|+0.0088|3/3|16.76|
|39|b4_gh_p2_display|4号艇_過去展示機力|high|0.5712|31.91%|29.35%|80%|+0.0148|2/3|16.53|
|40|b1_pl_recent_p2|1号艇_選手力弱さ|low|0.5845|28.40%|31.15%|100%|+0.0008|2/3|16.41|
|41|b4_vh_p2_display|4号艇_過去展示機力|high|0.5630|28.74%|29.34%|100%|+0.0133|2/3|16.40|
|42|v91_straight|当日展示_風_環境|high|0.5738|25.32%|27.85%|80%|+0.0124|2/3|15.99|
|43|b1_gh_delta_overall|1号艇_過去展示機力|low|0.5570|31.67%|31.67%|100%|+0.0073|3/3|15.73|
|44|rel_pl_frame_races_4v6|4号艇vs他艇_選手力差|high|0.5483|25.40%|25.60%|100%|+0.0208|2/3|15.68|
|45|rel_pl_all_p2_4v5|4号艇vs他艇_選手力差|high|0.5660|30.00%|29.41%|100%|+0.0071|2/3|15.47|
|46|st_corr_strength_b1|ST攻撃力_壁|low|0.5686|31.03%|32.10%|80%|+0.0078|2/3|15.40|
|47|opp_direct_b5_v93|相手構成_v93|low|0.5536|31.67%|27.64%|100%|+0.0108|3/3|15.28|
|48|rel_vh_delta_display_4v3|4号艇vs他艇_過去展示差|low|0.5524|31.25%|31.71%|60%|+0.0160|3/3|15.01|
|49|rel_pl_recent_p2_4v2|4号艇vs他艇_選手力差|high|0.5659|39.68%|28.86%|80%|+0.0067|3/3|14.92|
|50|b4_gh_delta_straight|4号艇_過去展示機力|high|0.5661|27.72%|31.21%|80%|+0.0036|3/3|14.81|

## Stable add-on candidates for expanding race count
These are candidates to rescue A-rank races outside frozen v268; they are **not** new thresholds yet.
|feature|direction|AUC|top20 lift|+OOF AUC|month consistency|
|---|---|---:|---:|---:|---:|
|v91_ex|high|0.6270|+12.90pt|+0.0551|100%|
|score_CORR20_v91|high|0.6253|+10.64pt|+0.0520|100%|
|score_wind_v83|high|0.6260|+9.80pt|+0.0505|100%|
|score_RAW20_v91|high|0.6207|+10.64pt|+0.0492|100%|
|score_BASE_v91|high|0.6203|+9.80pt|+0.0469|100%|
|rel_pl_all_win_4v1|high|0.6463|+14.00pt|+0.0275|100%|
|preview_comp|high|0.6195|+10.64pt|+0.0459|80%|
|rel_pl_all_p2_4v1|high|0.6411|+12.32pt|+0.0273|100%|
|rel_pl_recent_p2_4v1|high|0.6306|+11.03pt|+0.0329|100%|
|opp_grade_b1_v93|low|0.6108|+6.55pt|+0.0346|100%|
|opp_score_b1_v93|low|0.6141|+10.64pt|+0.0283|100%|
|rel_pl_recent_p2_4v3|high|0.5921|+7.89pt|+0.0377|100%|
|opp_national_b1_v93|low|0.6164|+8.96pt|+0.0224|100%|
|b1_pl_all_win|low|0.6197|+12.32pt|+0.0115|100%|
|b1_pl_all_p2|low|0.6221|+11.48pt|+0.0105|100%|
|b4_pl_recent_p2|high|0.5966|+7.73pt|+0.0267|100%|
|rel_pl_frame_races_4v1|high|0.5904|+12.41pt|+0.0225|100%|
|rel_pl_recent_p2_4v5|high|0.5952|+6.72pt|+0.0204|100%|
|b1_pl_frame_win|low|0.6086|+12.55pt|+0.0071|100%|
|rel_pl_frame_win_4v1|high|0.6022|+8.12pt|+0.0109|80%|
|rel_pl_all_win_4v5|high|0.5923|+9.80pt|+0.0092|100%|
|b2_vh_p2_display|high|0.5836|+4.10pt|+0.0177|100%|
|rel_pl_all_win_4v3|high|0.5902|+7.27pt|+0.0157|80%|
|rank_b1_v93|high|0.5770|+6.33pt|+0.0165|100%|
|rel_pl_all_p2_4v3|high|0.5711|+10.64pt|+0.0179|80%|

## Interpretation rule
- Prioritize features that are strong in **relative 4-vs-1 terms**, stable across months, and positive after PRE/POST—not merely features with one large top-decile hit rate.
- Use these results to build a separate A-rank expansion layer; keep HEAD4_V268 unchanged as S-rank.
