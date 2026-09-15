# 1号艇 v351 手動LIVE 引き継ぎ — 2026-09-15

## 今回の作業開始記録 — 2026-09-16
- September 2026結果・払戻は `UNREAD` 維持。
- exact3原因分解は Run `34986471815` / Job `104439734630` / Artifact `10402739636` で成功済み。
- schema別合計は EXACT3_HIT=106 / OPPONENT_PAIR_MISS=115 / ORDER_MISS=14。主因は順序ではなく相手2艇選択。
- 既存v351のHEAD以外のgate/finalizer条件は勝手に変更しない。`turn+straight`は保留。

## 相手pair 第1回temporal OOF — 完了
- 実装 commit `9da1ce7b5b8971f57c7ef8cd4125f8cc1434b574`。
- workflow commit `576b30f5bfba16755bcb8133807121348763a967`。
- Run `34988080328` / Job `104445260878` / Artifact `10404333709` / success。
- historical hard guard: `race_code < 20260901`。September 2026結果はUNREAD維持。
- 艇単位feature: boat / exhibition / ST / turn / straight / original avg。
- walk-forwardで同一raceより前だけを学習。
- OOF結果: TOTAL 151R / PAIR_HIT 41 / PAIR_RATE 27.15%。
- `lap+turn`: 5R / 2 hit / 40.00%。
- `lap+turn+straight`: 146R / 39 hit / 26.71%。
- `half+turn+straight` と `base` は学習量不足でOOF pair評価なし。
- 重要: `HOLDOUT_START=20260701` を設定したが、出力summaryに holdout=1 が1行も無い。よって7-8月独立holdout評価は未成立。これを成功と誤認しない。
- 結論: 展示系だけの単純logistic top2はPAIR_HIT 27.15%で、現時点ではproduction候補にしない。

## 次作業開始 — pair研究 Wave2
1. なぜ2026-07-01以降のholdout行が0なのか、母集団の日付分布とOOF対象期間を監査する。
2. 現行G2/G3 pairのPAIR_HIT baselineを同一151R上で必ず算出し、新モデル27.15%と同条件比較する。
3. 展示/STだけでなく、既存データからcausalに取得可能な選手力・コース/攻撃力・モーター/展示相対差・艇番/場/schema特徴を追加できるか調査する。
4. pairを艇ごとの独立binaryだけでなく、10通りの2艇pairを直接rankingする方式も比較する。
5. 時系列OOFで改善した案のみ、未使用の後半期間を独立holdoutに固定して最終確認する。
6. September 2026結果・払戻は絶対に読まない。

## 現行production / LIVE
- production profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- HEAD cutoff `.78`、opponent core `SECOND G2=.45 / THIRD G3=1.00`。
- core scripts: `run_1head_v351_live_window.py`, `probe_1head_v351_boatcast_exhibition.py`, `run_1head_v351_live_exhibition_gate.py`, `run_1head_v351_live_finalize.py`。
- レース時刻自動controllerは停止。ユーザーが「判別して」等と依頼したときだけ直前判定。
- 03:00 JST daily preparation承認済み。
- LIVEでは結果・払戻を絶対に使用しない。`result_or_payout_used=False` / `chronology_guard=True`。

## schema production方針
正式対象: `lap+turn+straight`, `lap+turn`, `half+turn+straight`, `base`（baseは低標本フラグ）。
保留: `turn+straight`（OOF0）。
