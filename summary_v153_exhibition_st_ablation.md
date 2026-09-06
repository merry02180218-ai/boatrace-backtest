# v153 展示STの寄与アブレーション

- 対象: v108で既にfreeze済みのno-leak feature table。Jun/Jul/Augを月次walk-forward。
- CURRENTはv109と同じ全特徴。
- NO_EXHIBITION_STは当該レースの展示ST明示特徴 one_st / st_margin2 / st_margin3 / st_margin23 を除外して再学習。
- NO_ALL_STはさらに過去/今節ST系 one_nst_strength / one_waku_sr_strength / one_meet_st_strength も除外。
- one_direct / one_score / threat系には現行設計上STが一部内包されるため、NO_EXHIBITION_STは「展示STの明示的な追加価値」を測る保守的アブレーション。
- S閾値72%は固定。結果・払戻は特徴に不使用。

## Jun-Aug aggregate
|variant|R|AUC|Brier|S件数|S頭率|S平均p|
|---|---:|---:|---:|---:|---:|---:|
|CURRENT|13,936|0.7095|0.21505|3,308|76.72%|78.96%|
|NO_EXHIBITION_ST|13,936|0.7092|0.21514|3,309|76.88%|78.92%|
|NO_ALL_ST|13,936|0.7114|0.21425|3,138|76.77%|78.53%|

## 月別S比較
|月|variant|S件数|S頭率|
|---|---|---:|---:|
|2026-06|CURRENT|1,043|75.65%|
|2026-06|NO_EXHIBITION_ST|1,043|75.74%|
|2026-06|NO_ALL_ST|977|76.87%|
|2026-07|CURRENT|1,156|77.34%|
|2026-07|NO_EXHIBITION_ST|1,152|77.69%|
|2026-07|NO_ALL_ST|1,122|76.29%|
|2026-08|CURRENT|1,109|77.10%|
|2026-08|NO_EXHIBITION_ST|1,114|77.11%|
|2026-08|NO_ALL_ST|1,039|77.19%|

## 差分

- 展示ST明示特徴を外したとき: AUC **-0.0003** / Brier **+0.00008** / S頭率 **+0.16pt** / S件数 **+1R**
- 全ST系を外したとき: AUC **+0.0019** / Brier **-0.00081** / S頭率 **+0.05pt** / S件数 **-170R**

## 判定ルール
- NO_EXHIBITION_STがCURRENTと同等以上なら、展示STの明示ウェイトは下げる余地あり。
- CURRENTがBrier/AUC/S頭率で一貫して優位なら、展示STは現状程度の情報価値あり。
- 差が小さい場合は「展示STは補助情報」で、直前判定で単独強調しない。
