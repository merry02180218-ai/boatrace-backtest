# v177 ③頭・historical web enrichment OOS

- 公開historical race-cardから選手登録番号を復元。
- ①1コース防御率・③3コース攻撃率は、そのレースより前の完了レースだけでrolling生成。
- ③前走展示/オリ展は直前の過去走だけを使用し、レース内相対rankに変換。
- 現在レースの展示は使用しない。実決まり手はtargetのみ。
- BOATBoyの現在値を過去へ貼ることはしない（future leakage防止）。

## reconstruction coverage
- SRC matched: 44549
- matched rows with prior exhibition: 44299
- historical card rows with boat1 id: 49780
- historical card rows with boat3 id: 49780

## Jun-Aug OOS base vs enriched
|month|variant|N|AUC|logloss|accuracy|train N|
|---|---|---:|---:|---:|---:|---:|
|2026-06|base|425|0.640|0.664|61.2%|2858|
|2026-06|enriched|425|0.660|0.654|63.1%|2858|
|2026-07|base|470|0.643|0.662|59.6%|3283|
|2026-07|enriched|470|0.661|0.652|60.4%|3283|
|2026-08|base|496|0.633|0.666|59.1%|3753|
|2026-08|enriched|496|0.652|0.663|61.1%|3753|

## 判定
- enrichedが3か月でAUC/loglossを安定改善するなら、事前展開確率の正式候補。
- 一部月だけ改善なら採用せず、特徴別ablationを次に行う。
