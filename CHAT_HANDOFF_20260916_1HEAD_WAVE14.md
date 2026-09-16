# 1号艇 v351 Wave14 引き継ぎ — 2026-09-16

## BEFORE
- 最新productionは変更しない。HEAD cutoff=.78 / opponent mass=.375 / G2=.45 / G3=1.00 / HYBRID 3点。
- September 2026の結果・払戻は絶対に読まず `UNREAD` 維持。研究入力は `race_code < 20260901` のhistoricalだけ。
- Wave13ではone-replace救済可能例の特徴取得50Rで SECOND保持25 / THIRD保持25。位置だけではKEEP艇を決められない。
- ユーザー仮説: 比較的強い艇が2号艇/3号艇のどちらにいるかで、1号艇が2号艇を締める展開と3号艇のまくりを警戒する展開が変わり、相手艇の残り方も変わる可能性がある。
- Wave14ではまずこの仮説を探索監査する。2号艇vs3号艇の相対強度を、展示補正・ST・turn・straight・orig_avgの差で分類し、現行相手ペアのKEEP/DROP、実際の相手構造との関連を確認する。
- 特に現行first pairが2-3のケースを独立集計し、2KEEP/3KEEPの件数と相対特徴差を比較する。さらにfirst pairに2または3を含む全例も集計する。
- 小標本なのでこの1回の探索結果だけでproductionへ昇格しない。シグナルがあれば次に時系列freeze/OOFで再検証する。
- HEAD学習へ展示を直接追加しない。post-ranking / ticket-rescue研究のみ。
