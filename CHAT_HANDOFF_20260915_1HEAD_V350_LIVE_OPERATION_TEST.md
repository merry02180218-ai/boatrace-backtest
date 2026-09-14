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
2. 過去データは2026-09-15より前だけで学習し、今日の全場をPREスコアする。
3. 実運用候補を固定して記録する。
4. 展示データが取得可能な候補は production g2=.50 と research g2=.45 の3連単3点を比較する。
5. Run/Job/Artifact、候補、買い目差分、未取得項目をこのhandoffへ追記する。
