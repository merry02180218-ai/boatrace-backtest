# 1号艇 v351 LIVE timing fix — 2026-09-15

## 作業前記録
- 最新 `CHAT_HANDOFF_20260915_1HEAD_LIVE_RECOVERY.md` と production workflow `.github/workflows/auto-live-1head-v351-exhibition-20260915.yml` を確認。
- 現行は nonblocking 化済みだが、外側起動は `*/5` schedule のままで、GitHub Actions schedule の遅延/欠落により FINAL5 を取り逃がす構造問題が残っている。
- 下関9R `202609151909` は手動push Run 34956642068 / Job 104340238153 で 19:13:10 JST に finalizer 完了、DROP、Artifact 10391526174。締切19:16には間に合ったが、自動scheduleだけでは保証できていない。
- これから、17本のpersistent matrix jobへは戻さず、**1本のcontroller/orchestrator job** が候補をdeadline順に管理して短周期で監視し、READYになった候補だけ production v351 gate/finalizerへ送る方式へ修正する。
- 目的は5分cronの発火時刻依存を直前判定のクリティカルパスから外すこと。結果・払戻は読まず `result_or_payout_used=false` / `chronology_guard=true` を維持する。
- 実装後に commit SHA / Actions Run / Job / Artifact / 次レースでの締切前完了を確認して追記する。
