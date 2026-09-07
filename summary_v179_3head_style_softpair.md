# v179 ③頭・racer-style soft-pair OOS比較

- v178で安定改善したracer-style特徴だけを展開分類器へ追加。
- v165 ③頭確率とv166 direct pairは固定。
- style履歴は評価レースより前だけでrolling生成。現在レース展示は不使用。
- 展開classifier targetは過去③頭のまくり vs まくり差しのみ。
- alphaはMar-Mayだけで選択し、Jun-Augは固定完全OOS。

## reconstruction coverage
- SRC matched: 44549
- prior exhibition available (not used in v179 classifier): 44299

## Mar-May alpha tuning
|alpha|coverage差|月別worst差|v179 coverage|
|---:|---:|---:|---:|
|0.00|+0.00pt|+0.00pt|81.47%|
|0.05|-0.06pt|-0.39pt|81.41%|
|0.10|-0.30pt|-0.59pt|81.18%|
|0.15|-0.30pt|-0.98pt|81.18%|
|0.20|-0.60pt|-1.38pt|80.88%|
|0.30|-0.60pt|-1.38pt|80.88%|
|0.40|-0.78pt|-1.57pt|80.70%|
|0.50|-1.20pt|-1.97pt|80.28%|
|0.75|-2.82pt|-3.67pt|78.66%|
|1.00|-3.36pt|-4.20pt|78.12%|

選択 alpha = **0.00**

## p3>=0.30 / top10 Jun-Aug OOS
|month|R|③頭R|v166 hit|v179 hit|v166 cov|v179 cov|v166 ROI|v179 ROI|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|ALL|270|104|29.26%|29.26%|75.96%|75.96%|103.2%|103.2%|
|2026-06|73|30|30.14%|30.14%|73.33%|73.33%|91.2%|91.2%|
|2026-07|87|26|26.44%|26.44%|88.46%|88.46%|116.3%|116.3%|
|2026-08|110|48|30.91%|30.91%|70.83%|70.83%|100.9%|100.9%|

## Decision rule
- v166に対して全体coverage/hit/ROIだけでなくJun/Jul/Augの月別安定性も確認する。
- Jun-Augを見てalphaや特徴定義を後付け変更しない。
- 一貫改善しなければv166を維持する。
