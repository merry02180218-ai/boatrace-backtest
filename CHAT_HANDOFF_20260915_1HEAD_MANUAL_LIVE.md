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

## 作業後記録 — 事前候補外レース対応
### 実施内容
- workflow `.github/workflows/auto-live-1head-v351-exhibition-20260915.yml` を修正。
- PRE candidate artifact / `pre_candidates_sab.csv` のダウンロードと、対象race_codeがPRE候補に1件存在することを要求するチェックを完全に撤去。
- `workflow_dispatch` で渡された任意の12桁race_codeを直接 DATE/JCD/RACE に分解して処理する方式へ変更。
- shared v351 cacheから対象race_codeの causal pre-exhibition baseを直接検索する。
- PRE候補外でも、そのbaseがshared cacheに存在すれば、締切取得 → 展示取得 → 既存v351 exhibition gate → 既存v351 finalizer → per-race immutable artifact、の経路へ進める。
- shared cacheに対象baseが無い場合は、PRE候補落ちとは区別して明示的にexit 4とする。結果・払戻からbaseを補完することは禁止。
- 自動cron / push起動は引き続き無し。手動要求のみ。
- v351 production gate/finalizerの条件は変更していない。

### Commit
- 実装commit: `ced13b2351d7262a66179bdfd1cf672560d472bd`
- 作業前引き継ぎcommit: `249c25816c317b16061d1567089ad4f3dc41ec9f`

### Run / Job / Artifact
- 本日は対象LIVEレース終了後のため、事前候補外レースを使った新しいactual LIVE Runは実行していない。
- Run ID: 未実行
- Job ID: 未実行
- Artifact ID: 未生成
- 締切後レースをactual LIVEのように再判定して動作確認することはしていない。

### 結論
- PRE候補CSVに無いこと自体は、今後の手動判定を妨げない。
- 任意race_codeを直接指定できる。
- 現時点の残る条件は「shared v351 cacheにそのレースのcausal baseが存在すること」。ここに無いレースまで完全対応するには、次に任意race_codeのcausal baseをその場で生成する経路が必要。

### 次の再開地点
1. 次回ユーザーがレースを指定したら、まず任意race_codeで手動判定を実行する。
2. shared cacheにbaseがあればそのままv351判定まで進める。
3. baseが無ければ、結果・払戻を使わず、その場でcausal pre-exhibition baseを生成する実装へ進む。
4. 作業前後に必ずこの引き継ぎを更新する。
