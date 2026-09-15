# 1号艇 v351 LIVE 引き継ぎ — 2026-09-15

## 最重要ルール
- 最新GitHubを最優先する。
- 2026年9月15日のレース結果・払戻は読まない。LIVE判断では `UNREAD` を維持する。
- `result_or_payout_used=False` / `chronology_guard=True` を維持する。
- 作業前にこの引き継ぎへ「これからやること」を記録し、作業後に結果・commit SHA・Actions Run/Job/Artifact ID・結論・次の再開地点を追記する。
- Actions/workflow名に `head4` 等が表示されても、名前だけで1号艇/4号艇を判定しない。必ず対象workflow・実行script・目的変数/処理内容まで確認する。

## 現在の1号艇production / LIVE
- 1号艇LIVEは v351。
- 基準として確認していたproduction HEAD: `bfc9b8ba9f72baf04434b4686e08b7f5538a8992`。
- `e9cb97b403b3508c5bd665a7fc28927868b81b54` は1号艇v351 LIVE側。

## 徳山9Rで判明した展示READY問題
- 徳山はオリジナル展示の直線タイムを公開しない。venue-aware修正commit: `376748f25079cd3a717fbb42da71fc8fcb5b4b9f`。
- 徳山(JCD18)は `avg + turn` を必須、straightは必須にしないよう変更。
- 全24場の現行2026仕様は引き続き監査対象。

## LIVE遅延問題
- 現行v351 workflowは5分cronで毎回新しいActions Runを立ち上げ、WAITならjob終了するため、展示公開後の直前判定を取り逃がす。
- 常滑11Rで、PRE=A (0.8048050886183357)、締切15:46、15:26時点WAITとなり、そのRun内では展示後判定まで進まなかったことを確認。

## 作業開始 — WAIT継続監視化
2026-09-15: ユーザー指示により今から実装する。
1. `.github/workflows/auto-live-1head-v351-exhibition-20260915.yml` のWAIT即終了を廃止する。
2. 同一watch job内で候補レースの展示READYまで短間隔pollする。
3. READYになったら即 `probe_1head_v351_boatcast_exhibition.py` → exact v351 gate/finalizer → immutable artifact uploadへ進む。
4. 締切安全窓を超えた場合だけfail-closeする。結果・払戻は読まない。
5. 実装後にActions実動を確認し、Run / Job / Artifact IDと結果をこのファイルへ追記する。

## 既知の監査ID
- 徳山9R旧失敗 Run: `34934002769`
- 徳山9R旧Job: `104267980339`
- 徳山9R旧Artifact: `10382617649`
- 旧status: `ERROR_NO_BET`

## 次の再開地点
**WAIT継続監視化を実装し、Actionsで実動監査する。**
