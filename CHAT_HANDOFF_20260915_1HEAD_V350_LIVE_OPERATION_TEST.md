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

## 正式採用＋実運用バックテスト 作業開始
- ユーザー指示により、研究候補 `SECOND g2=.45 / THIRD g3=1.00` を正式productionへ昇格させる。
- 既存HEAD条件、SECOND/THIRDモデル、3点HYBRID、v345 HEAD-side weightsは変更しない。
- 新productionの名称・新規コードでは `opponentCore` 表記を使う。既存v349の歴史的名称は変更しない。
- v350探索artifactから g2=.45 のticket identityを独立計算し、候補sentinelは `PASS=276 / HEAD=241 / EXACT3=131 / race SHA=08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd / ticket SHA=21631473d2a8b82f4fe93d18f8292d777837c26a47c408917fd8b722d1898cd7` と確認済み。
- まずproduction profileを g2=.45 へ反映し、その後に独立production regressionを新規に走らせる。
- regressionはSeptember outcomeを読まず、Feb-Jun pristine=選定証拠、Jul-Aug=`NON_PRISTINE_SUPPORT_ONLY`を維持する。
- そのうえで2026-09-15固定PRE候補を新production設定で実運用バックテストする。今日の結果・払戻は一切読まない。
- 実運用バックテストでは展示公開後データが取得可能な固定候補について、HEAD PASS判定→正式g2=.45/g3=1.00→3連単3点生成までを測定し、処理時間と出力を記録する。

## 正式採用 完了
- 正式production profile=`1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- SECOND `g2=.45` / THIRD `g3=1.00`
- production reflection commit=`8f2950c4fbc576117793db31f8db8cfd6a1c75c6`
- independent regression code commit=`95acd70dbf5d22c9141eeb86e6926ebf237d518a`
- regression workflow commit=`60ec84a160801f0907cb412cda9f2f77b7875692`

### 独立production監査
- Run=`34900768805` success
- prepare Job=`104165916351` success
- base-third Job=`104167455887` success
- second Job=`104167456001` success
- third Job=`104167456049` success
- production-regression Job=`104170501348` success
- Artifact=`v351-1head-production-regression`
- Artifact ID=`10371394695`
- Artifact digest=`sha256:023f0592ede29601183984193d6790fe8e2d496bb7fbc73526f9a9ea8069f4af`
- `AUDIT_OK=true`
- `PASS=276`
- `HEAD=241`
- `EXACT3=131`
- exact3 rate=`47.46376811594203%`
- Feb-Jun pristine=`107/220` = `48.63636363636364%`
- Jul-Aug support-only=`24/56` = `42.857142857142855%`
- race identity SHA256=`08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd`
- ticket identity SHA256=`21631473d2a8b82f4fe93d18f8292d777837c26a47c408917fd8b722d1898cd7`
- `SEPTEMBER_OUTCOMES_READ=false`

## 実運用バックテスト 完了
- workflow=`.github/workflows/v351-1head-operational-backtest.yml`
- Run=`34900892661` success
- prepare Job=`104166323778` success
- base-third Job=`104168079611` success
- third Job=`104168079628` success
- second Job=`104168079673` success
- operational-backtest Job=`104170469924` success
- Artifact=`v351-1head-operational-backtest`
- Artifact ID=`10371468748`
- Artifact digest=`sha256:0fde92545aca309ad0b063eabb9f42aedf324b1ac3a4325a360f02dc2fa9b676`

### 実運用バックテスト結果
- overall: `276R / HEAD 241 / EXACT3 131 / 47.46376811594203%`
- Feb-Jun pristine: `220R / HEAD 193 / EXACT3 107 / 48.63636363636364%`
- Jul-Aug support-only: `56R / HEAD 48 / EXACT3 24 / 42.857142857142855%`
- 3点均等100円想定 stake=`82,800円`
- 出力上の `return_yen=0 / roi=0` は払戻データが未結合のためで、実ROI=0%を意味しない。ROIは現時点で評価不能。

### 展示後ローカル計算速度
- shared prepare=`678111.370339ms`（学習/共有前処理。レースごとの直前判定時間とは別）
- mean=`0.170026ms/race`
- median=`0.080386ms/race`
- p95=`0.398716ms/race`
- max=`0.577104ms/race`
- 結論: 展示入力が揃った後の判定・買い目生成ローカル計算は十分高速。実運用遅延の主因候補はネットワーク経由の展示データ取得側。

## 現在の結論 / 次の再開地点
- v351 `g2=.45 / g3=1.00` は正式production採用・独立再現監査とも完了。
- 的中再現性と展示後ローカル計算速度は実運用可能。
- September outcomesは一切未読のまま維持。
- 次は2本立て:
  1. 払戻/締切時オッズを安全な過去期間だけ結合し、実ROIを正しく算出する。
  2. 2026-09-15の固定PRE候補について、結果を読まずに展示公開後の正式HEAD判定と買い目生成をprospective LIVEで継続する。

## PRE S/A/B 閾値監査 作業開始
- ユーザー指示により、固定Top15方式から閾値方式への移行を検証する。
- 暫定PREランクは `S >= .82 / A >= .80 and < .82 / B >= .78 and < .80 / < .78 対象外`。
- まず過去の安全な期間で、PRE S/A/B別に `候補R / 展示後v351 PASS / PASS率 / 1号艇1着 / 3連単3点EXACT3` を集計する。
- Feb-Jun pristineを主証拠、Jul-Augは `NON_PRISTINE_SUPPORT_ONLY` として別表示し、閾値選定には使わない。
- September outcomesは一切読まず `SEPTEMBER_OUTCOMES_READ=false` を維持する。
- 特に `PRE S/A/B → 展示後v351で何R落ちるか` と、B帯が展示後にどの程度残り・改善するかを確認する。
- 既存production v351の選定・買い目は変更せず、まず監査として実施する。
