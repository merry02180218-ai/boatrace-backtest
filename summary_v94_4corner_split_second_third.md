# v94 4カド 2着/3着ランキング分離検証

- 学習: 2025-11-01〜2026-05-31 の4号艇頭的中のみ (165R)
- 評価: 2026-06-01〜2026-08-31 は重み学習に未使用
- 入力特徴: v93で結果前に凍結した級別/全国/当地/モーター/枠別/ST/直前＋艇番位置。
- 2着用・3着用を別々の5択softmaxで学習。L2固定、recent3でハイパーパラメータ調整なし。
- 注意: モデル形式自体はv93の10か月診断から着想しているため、recent3は「parameter holdout」であり完全な未知prospectiveではない。

## 学習された方向

|特徴|2着weight|3着weight|
|---|---:|---:|
|grade|+0.239|-0.066|
|national|+0.333|+0.242|
|local|+0.080|+0.152|
|motor|+0.049|+0.071|
|waku|+0.000|+0.000|
|nst|+0.163|-0.240|
|direct|-0.010|+0.019|
|boat1|+0.251|+0.032|
|boat2|-0.004|-0.057|
|boat3|+0.012|-0.278|
|boat5|-0.029|+0.168|
|boat6|-0.231|+0.134|

## 順位単体カバー（4号艇頭的中時）

|期間|選別|方式|2着Top1|2着Top2|2着Top3|3着Top1|3着Top2|3着Top3|3着Top4|頭的中R|
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|prior7|BASE_A|CURRENT|38.1%|64.9%|81.4%|24.7%|44.3%|73.2%|86.6%|97|
|prior7|BASE_A|SPLIT|45.4%|63.9%|82.5%|23.7%|49.5%|71.1%|89.7%|97|
|prior7|CORR20_A|CURRENT|35.1%|64.9%|81.4%|25.8%|45.4%|74.2%|86.6%|97|
|prior7|CORR20_A|SPLIT|44.3%|61.9%|82.5%|25.8%|50.5%|72.2%|90.7%|97|
|prior7|BASE_S|CURRENT|32.1%|62.5%|76.8%|23.2%|39.3%|73.2%|83.9%|56|
|prior7|BASE_S|SPLIT|42.9%|62.5%|83.9%|25.0%|44.6%|64.3%|85.7%|56|
|prior7|CORR20_S|CURRENT|29.1%|63.6%|80.0%|27.3%|43.6%|74.5%|85.5%|55|
|prior7|CORR20_S|SPLIT|43.6%|61.8%|81.8%|27.3%|47.3%|67.3%|87.3%|55|
|recent3|BASE_A|CURRENT|33.3%|57.4%|72.2%|27.8%|57.4%|85.2%|94.4%|54|
|recent3|BASE_A|SPLIT|35.2%|57.4%|77.8%|31.5%|63.0%|85.2%|92.6%|54|
|recent3|CORR20_A|CURRENT|33.9%|58.9%|73.2%|30.4%|58.9%|87.5%|96.4%|56|
|recent3|CORR20_A|SPLIT|37.5%|60.7%|80.4%|30.4%|64.3%|85.7%|92.9%|56|
|recent3|BASE_S|CURRENT|41.4%|65.5%|79.3%|27.6%|62.1%|82.8%|93.1%|29|
|recent3|BASE_S|SPLIT|44.8%|58.6%|82.8%|24.1%|51.7%|79.3%|89.7%|29|
|recent3|CORR20_S|CURRENT|41.9%|64.5%|80.6%|25.8%|58.1%|83.9%|93.5%|31|
|recent3|CORR20_S|SPLIT|45.2%|58.1%|83.9%|25.8%|58.1%|80.6%|90.3%|31|

## 買い目形比較（全選別Rに4頭固定で購入）

|期間|選別|方式|形|平均点数|4頭時カバー|ROI|
|---|---|---|---|---:|---:|---:|
|prior7|BASE_A|CURRENT|2着Top2×3着Top3|4.00|42/97 (43.3%)|72.9%|
|prior7|BASE_A|SPLIT|2着Top2×3着Top3|4.37|42/97 (43.3%)|74.9%|
|prior7|BASE_A|CURRENT|2着Top2×3着Top4|6.00|52/97 (53.6%)|69.1%|
|prior7|BASE_A|SPLIT|2着Top2×3着Top4|6.11|54/97 (55.7%)|75.2%|
|prior7|BASE_A|CURRENT|2着Top3×3着Top3|6.00|54/97 (55.7%)|95.6%|
|prior7|BASE_A|SPLIT|2着Top3×3着Top3|6.73|55/97 (56.7%)|75.9%|
|prior7|CORR20_A|CURRENT|2着Top2×3着Top3|4.00|44/97 (45.4%)|75.2%|
|prior7|CORR20_A|SPLIT|2着Top2×3着Top3|4.36|42/97 (43.3%)|76.0%|
|prior7|CORR20_A|CURRENT|2着Top2×3着Top4|6.00|53/97 (54.6%)|67.8%|
|prior7|CORR20_A|SPLIT|2着Top2×3着Top4|6.10|53/97 (54.6%)|75.1%|
|prior7|CORR20_A|CURRENT|2着Top3×3着Top3|6.00|56/97 (57.7%)|98.6%|
|prior7|CORR20_A|SPLIT|2着Top3×3着Top3|6.74|55/97 (56.7%)|76.6%|
|prior7|BASE_S|CURRENT|2着Top2×3着Top3|4.00|23/56 (41.1%)|73.8%|
|prior7|BASE_S|SPLIT|2着Top2×3着Top3|4.33|20/56 (35.7%)|64.6%|
|prior7|BASE_S|CURRENT|2着Top2×3着Top4|6.00|28/56 (50.0%)|69.9%|
|prior7|BASE_S|SPLIT|2着Top2×3着Top4|6.09|29/56 (51.8%)|74.7%|
|prior7|BASE_S|CURRENT|2着Top3×3着Top3|6.00|29/56 (51.8%)|87.4%|
|prior7|BASE_S|SPLIT|2着Top3×3着Top3|6.74|29/56 (51.8%)|76.5%|
|prior7|CORR20_S|CURRENT|2着Top2×3着Top3|4.00|24/55 (43.6%)|75.3%|
|prior7|CORR20_S|SPLIT|2着Top2×3着Top3|4.34|20/55 (36.4%)|63.0%|
|prior7|CORR20_S|CURRENT|2着Top2×3着Top4|6.00|28/55 (50.9%)|62.1%|
|prior7|CORR20_S|SPLIT|2着Top2×3着Top4|6.10|28/55 (50.9%)|72.4%|
|prior7|CORR20_S|CURRENT|2着Top3×3着Top3|6.00|30/55 (54.5%)|109.7%|
|prior7|CORR20_S|SPLIT|2着Top3×3着Top3|6.76|29/55 (52.7%)|74.8%|
|recent3|BASE_A|CURRENT|2着Top2×3着Top3|4.00|27/54 (50.0%)|81.5%|
|recent3|BASE_A|SPLIT|2着Top2×3着Top3|4.37|25/54 (46.3%)|66.0%|
|recent3|BASE_A|CURRENT|2着Top2×3着Top4|6.00|29/54 (53.7%)|58.5%|
|recent3|BASE_A|SPLIT|2着Top2×3着Top4|6.11|28/54 (51.9%)|52.0%|
|recent3|BASE_A|CURRENT|2着Top3×3着Top3|6.00|33/54 (61.1%)|77.1%|
|recent3|BASE_A|SPLIT|2着Top3×3着Top3|6.72|34/54 (63.0%)|72.1%|
|recent3|CORR20_A|CURRENT|2着Top2×3着Top3|4.00|29/56 (51.8%)|70.8%|
|recent3|CORR20_A|SPLIT|2着Top2×3着Top3|4.37|28/56 (50.0%)|73.3%|
|recent3|CORR20_A|CURRENT|2着Top2×3着Top4|6.00|31/56 (55.4%)|51.4%|
|recent3|CORR20_A|SPLIT|2着Top2×3着Top4|6.11|31/56 (55.4%)|57.2%|
|recent3|CORR20_A|CURRENT|2着Top3×3着Top3|6.00|35/56 (62.5%)|70.3%|
|recent3|CORR20_A|SPLIT|2着Top3×3着Top3|6.72|37/56 (66.1%)|77.3%|
|recent3|BASE_S|CURRENT|2着Top2×3着Top3|4.00|17/29 (58.6%)|68.2%|
|recent3|BASE_S|SPLIT|2着Top2×3着Top3|4.39|12/29 (41.4%)|31.2%|
|recent3|BASE_S|CURRENT|2着Top2×3着Top4|6.00|17/29 (58.6%)|45.5%|
|recent3|BASE_S|SPLIT|2着Top2×3着Top4|6.13|15/29 (51.7%)|31.9%|
|recent3|BASE_S|CURRENT|2着Top3×3着Top3|6.00|19/29 (65.5%)|75.6%|
|recent3|BASE_S|SPLIT|2着Top3×3着Top3|6.72|18/29 (62.1%)|69.4%|
|recent3|CORR20_S|CURRENT|2着Top2×3着Top3|4.00|18/31 (58.1%)|75.5%|
|recent3|CORR20_S|SPLIT|2着Top2×3着Top3|4.41|13/31 (41.9%)|39.8%|
|recent3|CORR20_S|CURRENT|2着Top2×3着Top4|6.00|18/31 (58.1%)|50.4%|
|recent3|CORR20_S|SPLIT|2着Top2×3着Top4|6.13|16/31 (51.6%)|37.6%|
|recent3|CORR20_S|CURRENT|2着Top3×3着Top3|6.00|21/31 (67.7%)|83.9%|
|recent3|CORR20_S|SPLIT|2着Top3×3着Top3|6.75|20/31 (64.5%)|76.3%|

## 事前採否ルール
- recent3のCORR20_A/Sで、同程度の平均点数においてCURRENTより「4頭時カバー率」とROIがともに改善することを第一候補条件とする。
- 片方だけ改善、またはS/Aで方向不一致ならproduction採用しない。
- 採用候補になっても、次はprospectiveまたは別期間walk-forwardで再確認する。
