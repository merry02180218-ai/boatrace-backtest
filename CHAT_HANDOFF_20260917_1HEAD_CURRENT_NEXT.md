# 1号艇 v351 現状引き継ぎ — 2026-09-17

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール
- 最新GitHubを最優先。作業開始前/完了後に引き継ぎを更新する。
- historical hard guard は通常 `race_code < 20260901`。
- ユーザーが2026-09-17に明示的に「昨日までの9月のレースバックテスト」を依頼したため、今回の retrospective に限り `20260901〜20260916` の確定結果・払戻を評価用として読むことを許可。
- `20260917` 当日結果・払戻は引き続き絶対に読まない。UNREAD維持。
- LIVE/当日判定では `result_or_payout_used=False`, `chronology_guard=True`。
- HEAD学習特徴へ展示を直接追加しない。展示は post-ranking / ticket-rescue / live final correction のみ。

## 現行production
- profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- HEAD cutoff `.78`
- opponent core SECOND G2=.45 / THIRD G3=1.00
- formal historical baseline: 276R / 1号艇1着241=87.32% / exact3 131=47.46%（3点）

## BEFORE — BoatraceCSV Sep1-16 retrospective（2026-09-17）
- 前回 Run 35185302721 は Boatcast を1Rずつ再取得して45分 timeout。
- BoatraceCSV/boatracecsv.github.io に9月実データが存在することを確認済み。
  - 2026-09-01 tkz 展示CSVあり
  - 2026-09-01 original_exhibition CSVあり
  - 2026-09-01 payouts CSVあり
- 全CSVは12桁race_codeでJOIN可能。

今回の実施方針:
1. 9/1〜9/16をBoatraceCSVの日別CSVから一括取得する。
2. race_cards / tkz / stt / original_exhibition を予測側に使用する。
3. results/realtime と results/payouts は予測を確定した後の評価にだけJOINする。
4. 9/17 CSVは一切取得しない。
5. 可能な限り現行v351 productionの特徴・cutoff・ticketロジックを再現する。完全再現できない項目があれば結果に明示する。
6. 購入R、1頭数/率、3連単的中数/率、投資、払戻、ROI、日別明細をartifact化する。
7. workflowはmanual dispatchのみ。1回発火→検証。
8. 完了後、commit / Run / Job / Artifact / 結果をAFTERへ記録する。

## 次の再開地点
- `.github/workflows/audit-1head-v351-sep1-16.yml` をBoatraceCSV一括取得方式へ置換する。
- 9/17結果はUNREAD維持。
