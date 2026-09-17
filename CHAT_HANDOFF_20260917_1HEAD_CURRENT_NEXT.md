# 1号艇 v351 現状引き継ぎ — 2026-09-17

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール
- 最新GitHubを最優先。作業開始前/完了後に引き継ぎを更新する。
- historical hard guard は通常 `race_code < 20260901`。
- ただしユーザーが2026-09-17に明示的に「昨日までの9月のレースバックテスト」を依頼したため、今回の retrospective に限り `20260901〜20260916` の確定結果・払戻を評価用として読むことを許可。
- `20260917` 当日結果・払戻は引き続き絶対に読まない。UNREAD維持。
- LIVE/当日判定では `result_or_payout_used=False`, `chronology_guard=True`。
- 自動LIVE運用は廃止済み。ユーザーが依頼した時だけ取得/判定する。
- HEAD学習特徴へ展示を直接追加しない。展示は post-ranking / ticket-rescue / live final correction のみ。

## 現行production
- profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- HEAD cutoff `.78`
- opponent core SECOND G2=.45 / THIRD G3=1.00
- formal historical baseline: 276R / 1号艇1着241=87.32% / exact3 131=47.46%（3点）

## BEFORE — Sep1-16 retrospective backtest（2026-09-17）
ユーザー指示: 現行1号艇v351を、2026-09-01〜2026-09-16のレースでバックテストする。

実施方針:
1. 対象期間は9/1〜9/16のみ。9/17は除外しUNREAD維持。
2. 現行production profileを固定し、未来情報混入を避ける。
3. 各日の事前判定/展示後finalを可能な範囲で再現し、その後に確定結果を照合する。
4. 購入R、1号艇1着率、3連単的中数/率、可能なら払戻・回収率を集計する。
5. 既存workflow triggerを確認してから最小の専用retrospective経路を作る。
6. 1回発火→Run確認→結果確認。不要なworkflowやnoop commitは作らない。
7. 完了後、commit SHA / Run / Job / Artifact / 集計結果 / 次の再開地点をAFTERへ記録する。

## 既存LIVE / replay
- manual LIVE: `.github/workflows/manual-1head-v351-live.yml`
- postrace safe replay: `.github/workflows/test-replay-1head-v351.yml`
- 9/15単日 retrospective: `.github/workflows/audit-1head-v351-retrospective-20260915.yml`
- `.github/workflows/backtest.yml` は workflow_dispatch のみ（manual-only）であることを再確認済み。

## 次の再開地点
- Sep1-16専用retrospectiveを、既存の9/15 replay構造を流用して最小実装する。
- 9/17結果は読まない。
