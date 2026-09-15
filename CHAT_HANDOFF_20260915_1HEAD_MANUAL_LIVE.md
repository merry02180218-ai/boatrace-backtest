# 1号艇 v351 手動LIVE 引き継ぎ — 2026-09-15

## 最重要ルール
- 最新GitHubを最優先。
- 1号艇LIVE productionは v351。production gate/finalizerの条件は勝手に変更しない。
- LIVE判定でレース結果・払戻を使用しない。`result_or_payout_used=False` / `chronology_guard=True` を維持。
- GitHub作業は必ず、この引き継ぎへ作業前の予定を記録してから開始し、作業後に結果・commit SHA・Run/Job/Artifact ID・結論・次の再開地点を追記する。

## 現在の運用方針
- commit `59bc353faf2ca2171c18f8c18b41cf0d199735d3` で1号艇v351の自動cron/controllerを停止。
- 今後はユーザーが「判別して」「○○R判定して」と要求した時だけ取得・判定する手動LIVE方式。
- 2026-09-15の全LIVE運用は締切前の正常な自動実運用として成功扱いにしない。

## 作業前記録 — 事前候補外レース対応
ユーザー指示: 「事前候補にないレースも判別出来るようにして」

これから行うこと:
1. 現行manual v351 workflowがPRE candidate CSVに対象race_codeの存在を必須としている制約を撤去する。
2. PRE候補外でも対象race_codeの当日prediction/baseを取得または生成できる経路を確認・実装する。
3. v351 production gate/finalizerの条件そのものは変更しない。
4. 手動要求された任意レースについて、締切・展示を取得し、締切前ならv351相当の判定を実行できるようにする。
5. 結果・払戻は使用しない。
6. 自動cron/controllerは復活させない。
7. 作業後、このファイルへ実装内容・commit SHA・テスト状況・Run/Job/Artifact ID（実Runがなければ未実行と明記）・結論・次の再開地点を追記する。
