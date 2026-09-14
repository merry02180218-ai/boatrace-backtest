# 1号艇 v350 実運用テスト 2026-09-15

## 作業開始
- 正式productionは `1HEAD_PRODUCTION_20260914_HEAD078_V349_OPPONENT_ATTACKCORE` のまま維持する。
- production SECONDは `g2=.50`、THIRDは `g3=1.00`。
- 研究候補として SECOND `g2=.45` / THIRD `g3=1.00` を同一レースへ並列適用し、買い目差分と実運用性を確認する。
- production profileはこのテストでは変更しない。

## 2026-09-15 prospective LIVEルール
- 9月15日の結果・確定着順・払戻は一切読まない。
- `SEPTEMBER_OUTCOMES_READ=false` を維持する。
- 予想時点で利用可能なPRE情報と、公開後の展示/ST/original exhibitionのみを使用する。
- まず全場PREを作成して1号艇候補を抽出する。
- 展示公開後、同じ候補に対して g2=.50 production と g2=.45 research を並列表示する。
- 結果を見て候補レースを後から除外しない。
- Jul-Augは引き続き `NON_PRISTINE_SUPPORT_ONLY`。

## 命名
- 新規コード・Workflow・Artifactは `opponentCore` 表記を使う。
- 既存v349の名称は再現性維持のため変更しない。

## 実施予定
1. 2026-09-15のresult-blind PRE入力を取得する。
2. 学習用結果はSeptember outcome guardを優先し、2026-09-01より前だけを使用する。
3. 今日の全場をPREスコアし、実運用候補を固定して記録する。
4. 展示データが取得可能な候補は production g2=.50 と research g2=.45 の3連単3点を比較する。
5. Run/Job/Artifact、候補、買い目差分、未取得項目をこのhandoffへ追記する。

## LIVE PRE 実行
- workflow=`.github/workflows/v350-1head-live-operation-20260915.yml`
- workflow commit=`7e011cbcd3e9ac53f18bbb20f6f2f2141c6d21f2`
- Actions Run ID=`34900103279` success
- Job `pre-scan`=`104163744302` success
- Artifact=`v350-1head-live-pre-20260915`
- Artifact ID=`10370741174`
- Artifact digest=`sha256:46dc7fa6d3e05a2a634970a4f26be8a5d1b46f6209dd8e87cf90cfa78e1ca11f`
- PRE cards=153 / waku10=153 / scored=153
- training max date=`2026-08-31`
- `SEPTEMBER_OUTCOMES_READ=false`
- `PRODUCTION_CHANGED=false`

## 2026-09-15 固定PRE候補
Top5は以下。候補はこの時点で固定し、結果を見て差し替えない。
1. `202609151811` 徳山11R 山口剛 PRE=0.8600252281
2. `202609151808` 徳山8R 西村拓也 PRE=0.8502034460
3. `202609151810` 徳山10R 磯部誠 PRE=0.8491149529
4. `202609151804` 徳山4R 坪井康晴 PRE=0.8365496612
5. `202609151801` 徳山1R 高橋竜矢 PRE=0.8276768490

Frozen Top15追加候補:
6. 徳山6R 川原祐明 0.8184384410
7. 福岡1R 石倉洋行 0.8061393310
8. 常滑11R 三浦永理 0.8048050886
9. 福岡10R 吉田裕平 0.8034152526
10. 徳山5R 末永和也 0.7907800225
11. 徳山9R 土屋智則 0.7901627687
12. 徳山3R 金子拓矢 0.7850749775
13. 住之江4R 中村日向 0.7847288257
14. 下関10R 平田忠則 0.7832464065
15. 徳山12R 石野貴之 0.7824352970

## 現在の結論 / 次の実運用地点
- PRE prospective stageは完了し、Top5を結果blindで固定した。
- 最初の比較対象は徳山1R。展示公開後にHEAD側production条件を適用し、PASSなら同一入力で `g2=.50/g3=1.00` と `g2=.45/g3=1.00` の3連単3点を並列比較する。
- その後も固定Top5（徳山4R/8R/10R/11R）について同じ手順で記録する。
- September outcomeは明示解禁まで読まない。

## 正式採用＋実運用バックテスト 作業開始
- ユーザー指示により、研究候補 `SECOND g2=.45 / THIRD g3=1.00` を正式productionへ昇格させる。
- 既存HEAD条件、SECOND/THIRDモデル、3点HYBRID、v345 HEAD-side weightsは変更しない。
- 新productionの名称・新規コードでは `opponentCore` 表記を使う。既存v349の歴史的名称は変更しない。
- v350探索artifactから g2=.45 のticket identityを独立計算し、候補sentinelは `PASS=276 / HEAD=241 / EXACT3=131 / race SHA=08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd / ticket SHA=21631473d2a8b82f4fe93d18f8292d777837c26a47c408917fd8b722d1898cd7` と確認済み。
- まずproduction profileを g2=.45 へ反映し、その後に独立production regressionを新規に走らせる。
- regressionはSeptember outcomeを読まず、Feb-Jun pristine=選定証拠、Jul-Aug=`NON_PRISTINE_SUPPORT_ONLY`を維持する。
- そのうえで2026-09-15固定PRE候補を新production設定で実運用バックテストする。今日の結果・払戻は一切読まない。
- 実運用バックテストでは展示公開後データが取得可能な固定候補について、HEAD PASS判定→正式g2=.45/g3=1.00→3連単3点生成までを測定し、処理時間と出力を記録する。
