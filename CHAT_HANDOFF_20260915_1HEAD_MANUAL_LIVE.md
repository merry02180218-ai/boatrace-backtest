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
- commit `a1c5d27cf8b2c5e42a84c99b5390287f1d261653` に対し専用workflow起動確認。
- Workflow: `chat-live-1head-v351-request`
- Run ID: `34962132626`
- Job ID: `104357944028`
- event: `push`
- workflow_id: `358664242`
- smoke無効race_codeのためfailure、Artifactなし。

## 2026-09-15 蒲郡12R actual LIVE — 失敗記録
- race_code: `202609150712`
- Run ID: `34962990778`
- Job ID: `104360757399`
- `Resolve request and causal base` でshared baseが無く、LIVE中に `run_v321_1head_julaug_nonpristine_validation.py --stage prepare` を実行。
- 約4.5万Rのhead再構築・fold処理と10万行超のTHIRD処理へ入り、10分timeoutでcancelled。展示gate/finalizer未到達、Artifactなし、BUY/DROP未判定。
- 結論: LIVE中の全量base fallbackは禁止すべき。今回をLIVE失敗として扱う。

## 03:00 JST 当日全量base + PRE候補化 — 作業前記録
- ユーザー確定方針: 毎日 `03:00 JST` に当日開催分の全場・全Rについて、展示前に確定可能なv351 causal baseを一括生成する。
- 同じ処理で当日の1号艇PRE候補を全場・全R横断で抽出し、締切時刻順に一覧化する。
- PRE候補出力には少なくとも 場/R・締切時刻・PRE S/A/B・展示前HEAD確率・事前買い目候補 を含める。
- LIVE request時は対象race JSONを既存Artifact/cacheから取得し、`deadline -> exhibition -> v351 gate -> finalizer` のみを実行する。
- LIVE時にbaseが無い場合、v321全量再構築へfallbackせず即 `BASE_NOT_READY` でfail-closeする。
- production v351 gate/finalizer条件は変更しない。LIVE/03時base生成ともSeptember結果・対象レース結果・払戻を読まない。`result_or_payout_used=False` / `chronology_guard=True` 維持。
- 03時処理はbase/PRE準備のための定期処理であり、直前自動判定controllerは復活させない。
- これから行うこと: 既存daily/PRE workflowとcache生成scriptを確認 -> 03:00 JST workflow実装 -> PRE候補Artifact出力 -> chat bridgeの重いon-demand fallback削除 -> Actions smoke/実測 -> 作業後にcommit SHA / Run / Job / Artifact / 所要時間 / 結論 / 次の再開地点を追記する。
