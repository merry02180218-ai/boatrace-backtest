# 1号艇 v351 手動LIVE 引き継ぎ — 2026-09-15

## 最重要ルール
- 最新GitHubを最優先。
- 1号艇LIVE productionは v351。production gate/finalizerの条件は勝手に変更しない。
- LIVE判定でレース結果・払戻を使用しない。`result_or_payout_used=False` / `chronology_guard=True` を維持。
- GitHub作業は必ず、この引き継ぎへ作業前の予定を記録してから開始し、作業後に結果・commit SHA・Run/Job/Artifact ID・結論・次の再開地点を追記する。

## 現在の運用方針
- commit `59bc353faf2ca2171c18f8c18b41cf0d199735d3` で1号艇v351の自動cron/controllerを停止。
- ユーザーが「判別して」「○○R判定して」と要求した時だけ取得・判定する手動LIVE方式。
- 2026-09-15の全LIVE運用は正常な自動実運用として成功扱いにしない。

## 作業前記録 — shared cacheにも無い完全任意レース対応
- 作業前commit: `44dd1f39a65e6aeb4db18c4a9705ac9553b79dd8`
- 目的: PRE候補にもshared cacheにも無い任意race_codeについて、結果・払戻なしでcausal pre-exhibition baseをその場生成し、展示→v351判定へ接続する。

## 作業後記録 — 完全任意レース対応
### 実施内容
- `prepare_1head_v351_live_cache.py` に `--race-code` オンデマンドモードを追加。
- PRE CSVを必須から外し、指定race_codeだけを既存productionと同じ current_static → current features → head_score / opponent p2 / pc 経路で再計算可能にした。
- オンデマンドbaseには `base_source=ON_DEMAND_CAUSAL`, `result_or_payout_used=False`, `chronology_guard=True` を記録。
- 対象race_codeを同じproduction feature経路で生成できなければfail-closeする。
- manual workflowを日付固定artifact名からrace_code先頭8桁のDATE動的参照へ変更。
- shared `v351-1head-live-cache-$DATE` にbaseがあれば再利用。
- baseが無ければ同日rolling PRE artifact `v351-1head-live-pre-sab-$DATE-rolling` から `race_cards.csv` を取得し、`prepare_1head_v351_live_cache.py --race-code` でその場生成する。
- PRE候補CSVの所属は要求しない。
- その後の展示gate/finalizerは既存v351 production scriptを変更せず使用。
- 締切後は `EXPIRED` でLIVE finalを拒否。
- cron/pushは無し。workflow_dispatchのみ。

### Commits
- オンデマンドbase生成script: `bc9c7d4f1628a5c0b09a491b7ba4213dbdc5648b`
- manual workflow fallback接続: `ef18e95d6de8ff4a301e96a196c9d6e1fcae53ed`

### Run / Job / Artifact
- actual LIVE Run: 未実行（2026-09-15の対象レース終了後のため、締切後をLIVEとして偽装テストしない）。
- Run ID: 未実行
- Job ID: 未実行
- Artifact ID: 未生成
- 次の実レース指定時に初回actual LIVE smoke testを行う。

### 結論
- 事前候補外でも判定可能。
- shared cache外でも、同日のrace_cards artifactに対象レースがあればcausal baseをオンデマンド生成して判定可能。
- v351 production gate/finalizer条件は変更していない。
- 結果・払戻は使用しない。
- 自動LIVEは復活させていない。

### 次の再開地点
1. ユーザーがLIVEレースを指定したらrace_codeを確定してmanual workflowを起動。
2. shared cache hitなら即利用、missならon-demand causal base生成。
3. 締切→展示取得→v351 gate→finalizerを実行し、BUY/PASSまたはDROPと3連単3点を即返す。
4. 初回actual LIVE RunのRun/Job/Artifact IDと所要時間をこの引き継ぎへ追記する。
