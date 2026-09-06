# v159 ST context interaction audit

- 対象: 2026-07-01〜2026-09-05 walk-forward / 評価艇 **58,045**
- 各日の予測を全艇freeze後、その日の結果で履歴更新。同日リークなし。
- PLAYERを基準に、選手×コース / 選手×展示F正常 / 選手×隣艇文脈 / 選手の直近6走を比較。

|variant|MAE|Δ vs PLAYER|
|---|---:|---:|
|PLAYER|0.09350|+0.00000|
|PLAYERxCOURSE|0.09444|+0.00094|
|PLAYERxFSTATE|0.08205|-0.01145|
|PLAYERxNEIGHBOR|0.09014|-0.00336|
|PLAYERxRECENT6|0.09603|+0.00253|

## 履歴量別
|variant|条件|n|MAE|
|---|---|---:|---:|
|PLAYERxCOURSE|prior n>=3|56,614|0.09418|
|PLAYERxCOURSE|prior n>=6|46,847|0.09331|
|PLAYERxCOURSE|prior n>=12|13,170|0.09300|
|PLAYERxFSTATE|prior n>=3|57,465|0.08152|
|PLAYERxFSTATE|prior n>=6|55,840|0.08099|
|PLAYERxFSTATE|prior n>=12|51,440|0.08129|
|PLAYERxNEIGHBOR|prior n>=3|56,641|0.08977|
|PLAYERxNEIGHBOR|prior n>=6|52,192|0.08928|
|PLAYERxNEIGHBOR|prior n>=12|38,396|0.08750|

## 判定
- PLAYERより一貫してMAE改善し、履歴量が増えても改善方向が維持されるinteractionだけ次のv109 shadow候補にする。
- 「展示F」「隣艇が遅い」等は単純ルール化せず、予測改善が確認できた場合のみ採用する。
