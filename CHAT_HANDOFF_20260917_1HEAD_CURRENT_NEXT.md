# 1号艇 v351 現状引き継ぎ — 2026-09-17

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール
- 最新GitHubを最優先。作業開始前/完了後に引き継ぎを更新する。
- September 2026 の結果・払戻は絶対に読まない。`UNREAD`維持。
- historical hard guard: `race_code < 20260901`。
- LIVE/当日判定では `result_or_payout_used=False`, `chronology_guard=True`。
- 自動LIVE運用は廃止済み。ユーザーが「判別して」「候補出して」等と依頼した時だけ取得/判定する。
- HEAD学習特徴へ展示を直接追加しない。展示は post-ranking / ticket-rescue / live final correction のみ。

## 現行production
- profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- HEAD cutoff `.78`
- opponent core SECOND G2=.45 / THIRD G3=1.00
- formal baseline: 276R / 1号艇1着241=87.32% / exact3 131=47.46%（3点）

## 2026-09-17 今日の正式事前候補
- `202609171306` 尼崎6R: final_head_p=0.8301538300238417 / opp_mass=0.38674739724923224 / base tickets `1-2-4;1-2-3;1-4-2`
- `202609170412` 平和島12R: final_head_p=0.7901582366125368 / opp_mass=0.42123448085672327 / base tickets `1-4-2;1-4-5;1-2-4`
- `202609171904` 下関4R: final_head_p=0.8105814572971805 / opp_mass=0.4090498291303686 / base tickets `1-2-5;1-2-3;1-3-2`
- formal cache Run `35170926144`, Artifact `10477251012`, result/payout unused.

## 既存LIVE / postrace replay
- manual LIVE: `.github/workflows/manual-1head-v351-live.yml`
- 終了後の安全な検証経路は昨日すでに作成済み:
  - `probe_1head_v351_boatcast_exhibition_test_replay.py`
  - `run_1head_v351_postrace_test.py`
  - `.github/workflows/test-replay-1head-v351.yml`
- 既存test replayはPRE cache + Boatcast展示だけを使い、結果/払戻/oddsを使わず `run_1head_v351_live_exhibition_gate.py` → `run_1head_v351_live_finalize.py` を再現する。

## BEFORE — 尼崎6R safe replay（2026-09-17）
ユーザー指示: 終了済み尼崎6Rを、昨日作成済みの安全なpostrace replay経路で直前判定として再現して出す。

実施方針:
1. September結果・払戻は絶対に読まない。UNREAD維持。
2. 9/17 formal cache `v351-1head-live-cache-20260917` を使う。
3. 対象は `202609171306` のみ。
4. deadline-free test probeでBoatcast展示だけ取得する。
5. venue-aware exhibition gate → v351 finalizeを通す。
6. `status / head_exhibition_pass / corrected exhibition / tickets` を確認する。
7. Run/Job/Artifact/commitと結果をAFTERへ追記する。
8. 1回発火→確認。不要なworkflowやnoop commitは作らない。

## 次の再開地点
- `.github/workflows/test-replay-1head-v351.yml` を9/17 request-driven単一race replayへ最小修正し、`test_requests/1head_v351.json` の尼崎6R requestで一度だけ発火する。
- 結果確認後AFTER追記。
