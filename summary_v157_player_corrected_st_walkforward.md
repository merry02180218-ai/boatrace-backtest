# v157 player-corrected exhibition ST walk-forward

- 学習開始: 2026-05-01 / untouched逐日評価: 2026-07-01〜2026-09-05
- 各日の予測を全艇freezeしてから、その日の結果で履歴更新。同日リークなし。
- GLOBAL: 展示ST + 過去日だけの全体平均(本番-展示)
- PLAYER: 展示ST + 過去日だけの選手bias（全体平均へ10走shrink）

- 評価艇: **58,045**
- GLOBAL MAE **0.0948** / RMSE **0.1223**
- PLAYER MAE **0.0935** / RMSE **0.1208**
- ΔMAE **-0.0013** / ΔRMSE **-0.0014**

- prior n>=0: 58,045艇 / GLOBAL MAE 0.0948 / PLAYER MAE 0.0935 / Δ -0.0013
- prior n>=3: 57,999艇 / GLOBAL MAE 0.0947 / PLAYER MAE 0.0935 / Δ -0.0013
- prior n>=6: 57,939艇 / GLOBAL MAE 0.0947 / PLAYER MAE 0.0935 / Δ -0.0013
- prior n>=12: 57,736艇 / GLOBAL MAE 0.0947 / PLAYER MAE 0.0935 / Δ -0.0013
- prior n>=20: 56,740艇 / GLOBAL MAE 0.0945 / PLAYER MAE 0.0933 / Δ -0.0013

## 判定
- PLAYERのMAE/RMSEがGLOBALより改善し、履歴数が増えるほど改善が安定するなら、選手固有展示→本番補正を次のv109 shadow特徴へ追加する。
- 改善しない場合はv156の相関が説明的であって予測的ではないため採用しない。
