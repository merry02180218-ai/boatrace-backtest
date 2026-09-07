# v187 ③頭 締切前市場人気 dynamic ticket chronological OOS

- od3結合候補: 139R。実在od3期間内を時系列で前半69R=ルール決定、後半70R=完全OOS。
- OOS開始日: 2026-08-11
- 候補母集団: strict monthly-WF v165 p3>=0.30。順位: v166 λ=1.00。
- pre_public = 全120組の1/odds合計に対する③頭20組の1/oddsシェア。
- 結果・払戻は点数決定後のsettlementのみ。

- fixed rule: share>=0.5009 → 5点, >=0.4369 → 7点, else 10点

|scope|policy|R|③頭率|hit|平均点数|ROI|
|---|---|---:|---:|---:|---:|---:|
|TUNE_FIRST_HALF|dynamic|69|44.93%|36.23%|8.38|136.1%|
|TUNE_FIRST_HALF|fixed10|69|44.93%|36.23%|10.00|114.2%|
|OOS_SECOND_HALF|dynamic|70|38.57%|22.86%|8.83|85.6%|
|OOS_SECOND_HALF|fixed10|70|38.57%|25.71%|10.00|86.3%|
|OOS_2026-08|dynamic|70|38.57%|22.86%|8.83|85.6%|
|OOS_2026-08|fixed10|70|38.57%|25.71%|10.00|86.3%|
