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

## 完了済み — PRE候補CSV依存撤去
- 実装commit: `ced13b2351d7262a66179bdfd1cf672560d472bd`
- PRE candidate CSVに対象race_codeが無くても、shared v351 cacheにcausal baseがあれば直接判定可能。
- 自動cron/pushは復活させていない。

## 作業前記録 — shared cacheにも無い完全任意レース対応
ユーザー指示: 「そうしてくれ」＝事前候補にもshared cacheにも無い任意レースについて、その場でcausal pre-exhibition baseを生成し、展示取得→v351判定まで可能にする。

これから行うこと:
1. 最新repo内でv351当日prediction/baseを生成している既存scriptと入力依存を特定する。
2. race_code単体から、結果・払戻を一切使わず、その時点で利用可能な事前情報だけでcausal baseを生成する最短経路を実装する。
3. shared cacheにbaseがあれば従来通り再利用し、無い場合だけオンデマンド生成へfallbackする。
4. 展示取得後は既存 `run_1head_v351_live_exhibition_gate.py` と `run_1head_v351_live_finalize.py` をそのまま使い、production条件は変更しない。
5. 自動cron/controllerは復活させない。手動要求のみ。
6. 締切後はLIVE finalを拒否する。
7. 結果・払戻は使用しない。`result_or_payout_used=False` / `chronology_guard=True` を維持する。
8. 実装後、この引き継ぎへcommit SHA、テスト状況、Run/Job/Artifact ID、結論、次の再開地点を追記する。
