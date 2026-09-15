# 1号艇 v351 LIVE 引き継ぎ — 2026-09-15

## 最重要ルール
- 最新GitHubを最優先する。
- 2026年9月15日のレース結果・払戻は読まない。LIVE判断では `UNREAD` を維持する。
- `result_or_payout_used=False` / `chronology_guard=True` を維持する。
- 作業前にこの引き継ぎへ「これからやること」を記録し、作業後に結果・commit SHA・Actions Run/Job/Artifact ID・結論・次の再開地点を追記する。
- Actions/workflow名だけで1号艇/4号艇を判定しない。必ず対象workflow・script・処理内容まで確認する。

## 現在の1号艇production / LIVE
- 1号艇LIVEは v351。
- venue-aware修正: `376748f25079cd3a717fbb42da71fc8fcb5b4b9f`。
- WAIT継続job化: `480c57a4da7d1b3f6f78b787beefc87790a08195`。

## 2026-09-15 15:46 JST前後に判明したRunner占有問題
- Run `34938438610` は正真正銘の `auto-live-1head-v351-exhibition-20260915`。
- 常滑11R `202609150811` PRE=A / 0.8048050886183357 はjob `104281420706` として作成されたが queued。
- 原因: 各候補jobがWAIT中も15秒sleepでRunnerを長時間占有し、後続候補がqueuedになった。
- 徳山6R/10R等が `Wait for exhibition and probe` でin_progressのままRunnerを保持していた。
- したがって `480c57a4` の「候補ごとにpersistent job」は実運用上不適切。

## 作業開始 — nonblocking polling化
2026-09-15: ユーザー指示「直せよ」により今から修正する。
1. WAIT中にjob内sleepを続ける設計を廃止する。
2. 5分cronの各Runでは各候補を1回だけ評価し、WAITなら即終了してRunnerを解放する。
3. TRY/FINAL5に入った候補だけ展示probeを行い、READYならexact gate/finalizer/artifactまで同Runで完了する。
4. FINAL5で展示未READYのみfail-closeする。
5. matrixはdeadlineが近い候補を優先できるよう、prepare段階で候補順を締切時刻ベースにする方向で実装する。
6. 結果・払戻は一切読まない。`result_or_payout_used=False` / `chronology_guard=True` を維持する。
7. 実装後、Actions Run/Job/Artifactを監査してこのhandoffへ追記する。

## 既知の監査ID
- 徳山9R旧失敗 Run: `34934002769`
- 徳山9R旧Job: `104267980339`
- 徳山9R旧Artifact: `10382617649`
- Runner占有確認 Run: `34938438610`
- 常滑11R queued Job: `104281420706`

## 次の再開地点
**v351 workflowをnonblocking pollingへ修正し、Actions実動を監査する。**
