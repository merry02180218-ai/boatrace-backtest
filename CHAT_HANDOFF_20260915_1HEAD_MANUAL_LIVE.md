# 1号艇 v351 手動LIVE 引き継ぎ — 2026-09-15

## 最重要ルール
- 最新GitHubを最優先。
- 1号艇LIVE productionは v351。production gate/finalizerの条件は勝手に変更しない。
- LIVE判定でレース結果・払戻を使用しない。`result_or_payout_used=False` / `chronology_guard=True` を維持。
- GitHub作業は必ず、この引き継ぎへ作業前の予定を記録してから開始し、作業後に結果・commit SHA・Run/Job/Artifact ID・結論・次の再開地点を追記する。

## 現在の運用方針
- 1号艇v351の自動cron/controllerは停止済み。
- ユーザーが判別を要求した時だけ取得・判定する手動LIVE方式。

## 完了済み — 完全任意レース対応
- オンデマンドbase生成script: `bc9c7d4f1628a5c0b09a491b7ba4213dbdc5648b`
- manual workflow fallback接続: `ef18e95d6de8ff4a301e96a196c9d6e1fcae53ed`

## Chat起動用request bridge
### 作業前記録
- commit `bb8104b1ce68ee2e2b2e8a0962fd0ede51c5545a`
- Chat側GitHub接続では新規workflow_dispatchを直接開始できないため、専用request fileへのcommitを起点にする方針を明記。

### 実装
- workflow追加commit: `a5db0a6c9e90d4f365452dc904f93bbabaed301f`
- workflow: `.github/workflows/chat-live-1head-v351-request.yml`
- request path: `live_requests/1head_v351.txt`
- request初期化commit: `3d7d7c79773d3dbb878cf5caa3fa35dc77ac7209`
- smoke用request更新commit: `a1c5d27cf8b2c5e42a84c99b5390287f1d261653`
- 設計: request fileの12桁race_codeを読み、shared cache hitまたはon-demand causal base生成後、deadline→exhibition→既存v351 gate→既存v351 finalizer→artifact upload。
- 定期cron/controllerは追加していない。結果・払戻は使用しない。

### 検証状態
- request fileへのcommit自体はChatから成功。
- smoke commit `a1c5d27...` に対してrepoの既存push workflow Run `34962132886` がqueuedになったことを確認し、ChatからのcommitがGitHub Actions push eventを発生させること自体は確認済み。
- ただし新設 `chat-live-1head-v351-request` のRunは同commitではまだ確認できていないため、bridgeをactual LIVE使用可能と断定しない。
- Run ID: bridge専用は未確認。
- Job ID: 未確認。
- Artifact ID: 未生成。

### 結論 / 次の再開地点
1. 新設workflowがActionsに登録・起動されない原因を確認する。
2. 必要ならworkflow YAML/triggerを修正し、専用request変更でbridge Runが発生するまで検証する。
3. bridge RunのJob/stepsを確認し、実レースではArtifact回収まで完了させる。
4. 今後の判別要求は request commit → bridge Run確認 → Run監視 → Artifact回収 → BUY/DROPと買い目返却までを一連のLIVE作業とする。
