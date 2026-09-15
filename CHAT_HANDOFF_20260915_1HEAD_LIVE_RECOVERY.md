# 1号艇 v351 LIVE 引き継ぎ — 2026-09-15

## 最重要ルール
- 最新GitHubを最優先する。
- 2026年9月15日のレース結果・払戻は読まない。LIVE判断では `UNREAD` を維持する。
- `result_or_payout_used=False` / `chronology_guard=True` を維持する。
- 作業前後に結果・commit SHA・Actions Run/Job/Artifact ID・結論・次の再開地点を記録する。
- workflow名だけで1号艇/4号艇を判定しない。

## 現在の1号艇production / LIVE
- 1号艇LIVEは v351。
- venue-aware修正: `376748f25079cd3a717fbb42da71fc8fcb5b4b9f`。
- WAIT継続job化（後に不採用）: `480c57a4da7d1b3f6f78b787beefc87790a08195`。
- nonblocking polling修正: `b953b27d45831a5a139466bb57ea0ca0a2ffcab6`。

## Runner占有問題
- Run `34938438610` は1号艇 `auto-live-1head-v351-exhibition-20260915`。
- 常滑11R `202609150811` PRE=A / 0.8048050886183357 はjob `104281420706` だったが queued。
- 各候補jobがWAIT中15秒sleepを継続してRunnerを占有したのが原因。

## 作業完了 — nonblocking polling化
- 実装commit: `b953b27d45831a5a139466bb57ea0ca0a2ffcab6`
- workflow: `.github/workflows/auto-live-1head-v351-exhibition-20260915.yml`
- WAIT中のwhile/sleep継続を撤去。
- 各5分cron Runで候補を1回だけ評価し、WAITなら即job終了してRunnerを解放。
- TRY/FINAL5のみ展示probe。READYならcache→exact v351 gate→finalizer→immutable artifact。
- FINAL5未READYのみfail-close。
- watch timeoutを45分から10分へ短縮。
- `result_or_payout_used=False` / `chronology_guard=True` 維持。9月15日結果・払戻はUNREAD。
- 実装直後に head_sha=`b953b27d...` のActions Runを検索した時点では0件で、Run/Job/Artifact IDはまだ未発行。したがって実動完了とはまだ判定しない。

## 既知の監査ID
- 徳山9R旧失敗 Run: `34934002769`
- 徳山9R旧Job: `104267980339`
- 徳山9R旧Artifact: `10382617649`
- Runner占有確認 Run: `34938438610`
- 常滑11R queued Job: `104281420706`

## 結論
persistent WAIT job方式は廃止。5分cronのnonblocking polling方式へ戻し、展示取得可能な時間帯だけ処理する設計へ修正済み。ただし新commitのActions実動監査は未完了。

## 次の再開地点
**`b953b27d` を使った最新v351 Runを確認し、常滑11Rを含むJob/Artifactとexact finalizerの実動を監査する。**
