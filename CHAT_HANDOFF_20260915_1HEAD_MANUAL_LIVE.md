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

### 検証結果 — bridge trigger確認完了
- 以前「bridge専用Run未確認」としていたのは検索確認不足。commit `a1c5d27cf8b2c5e42a84c99b5390287f1d261653` に対し、専用workflowは実際に起動していた。
- Workflow: `chat-live-1head-v351-request`
- Run ID: `34962132626`
- Job ID: `104357944028`
- event: `push`
- workflow_id: `358664242`
- Runは `failure` だが、これはsmoke requestが意図的な無効race_code `999999999999` だったため `Resolve request and causal base` でfail-closeしたもの。trigger不良ではない。
- Artifact ID: なし。

### 結論
- Chatから `live_requests/1head_v351.txt` を更新することで専用LIVE workflowを起動できる。
- 1号艇の定期cron/controllerは復活させない。

### 次の再開地点
- 実在レース判別要求 → request commit → Run/Job監視 → Artifact回収 → BUY/DROP + BUY時3点返却 → 作業後handoff更新。

## 2026-09-15 蒲郡12R actual LIVE
### 作業前記録
- ユーザー要求: 「蒲郡12R判別して」
- race_code: `202609150712`
- BOAT RACE公式で締切予定 `20:35 JST` を確認。
- これから `live_requests/1head_v351.txt` を上記race_codeへ更新し、専用bridge Runを特定・監視、Artifactを回収してv351のBUY/DROP（BUYなら3連単3点）を返す。
- production gate/finalizerは変更しない。結果・払戻は使用しない。
