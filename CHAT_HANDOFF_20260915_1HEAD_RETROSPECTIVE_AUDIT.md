# 1号艇 v351 2026-09-15 retrospective audit 引き継ぎ

## 2026-09-15 作業開始記録
- ユーザーが2026-09-15結果のunblindを明示承認。以後この監査は retrospective / non-pristine として扱う。過去LIVE artifactの時刻評価は変更しない。
- 凍結条件: production v351 / HEAD cutoff 0.78 / 現行production opponent-selection・ticket logic。結果を見てthreshold/features/ticketsを変更しない。
- 先に17候補について9/15当時のPRE cache + Boatcast展示データだけから prediction/tickets を生成・artifactへ凍結する。結果・払戻はこのPhase Aでは取得しない。
- Phase A凍結後にのみ公式結果・3連単払戻を結合し、PASS頭率、DROP救済/false drop、買い目的中数、投資/払戻/ROIを集計する。
- 現行LIVE workflowの単純rerunは締切後 `EXPIRED` となり展示probeを実行しないことを Job 104292235929 のログで確認済み。そのため締切時間guardだけをretrospective用に迂回し、gate/finalizer本体はproduction scriptをそのまま呼ぶ専用workflowを作る。
- 17候補: 202609151803, 202609150710, 202609151204, 202609151804, 202609150811, 202609151801, 202609152210, 202609151812, 202609151811, 202609151805, 202609151810, 202609151806, 202609151809, 202609152201, 202609151909, 202609151910, 202609151808。

## 場別 completeness 監査開始
- ユーザー指示により、v351/v326展示バックテスト母集団を場別に分解する。
- 確認対象: 各場の候補R数、tkz/stt/original各complete数、strict source_complete/model_ready数、展示gate評価可能数、頭率。特に original straight 非公開場（江戸川/津/住之江/尼崎/徳山等）の除外偏りを確認する。
- 閾値・特徴量は変更せず、まず現行バックテストがどの場を母集団から落としていたかを監査する。

次: 既存v326/v351 dataset生成ロジックを使ったvenue auditをActionsで実行し、artifactを回収する。