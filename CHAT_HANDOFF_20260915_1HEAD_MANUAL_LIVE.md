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
- OOF結果: TOTAL 151R / PAIR_HIT 41 / PAIR_RATE 27.15%。
- 結論: 展示系だけの単純logistic top2はproduction候補にしない。

## pair研究 Wave2 — 完了
- commit `0ba82c666b88d05442d22d5b152be4ee21a3051b`。
- Run `34989886719` / Job `104451495547` / Artifact `10404069913` / success。
- 母集団は 20260201〜20260630 の235R。7〜8月データはこの監査母集団に存在せず、独立holdoutは未成立。
- 同一OOF 205Rで現行ticket pair baseline=110/205=53.66%、Wave2=54/205=26.34%、差=-27.32pt。
- schema: base 55.56→33.33、half+turn+straight 46.15→15.38、lap+turn 55.17→27.59、lap+turn+straight 53.90→26.62。
- 結論: Wave2は不採用。現行G2/G3 pairを維持する。

## 次作業開始 — G2/G3 pair補正研究 Wave3
1. 現行G2/G3/ticket生成の実装箇所を最新mainから特定する。
2. 同一235Rを KEEP（現行pair正解）/ REPLACE_ONE（現行pairと実pairが1艇共通）/ REPLACE_BOTH（共通0艇）へ分解する。
3. ゼロからtop2を作り直さず、現行pairをbaselineとして「変更すべき時だけ補正」する。
4. まずREPLACE_ONEの救済を優先し、現行正解KEEPを壊さない条件を探索する。
5. OOF評価は baseline 53.66% を必ず同一race集合で比較し、改善しない案は不採用。
6. September 2026結果・払戻は絶対に読まない。HEAD以外のproduction gate/finalizerも変更しない。

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
