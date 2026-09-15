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

## G2/G3 pair補正研究 Wave3 — 完了
- 実装 commit `f95e7c02d5c4a0b1011f2ff78b26e8db19af07cd`。
- workflow/trigger commit `d7031c058749c6ad7b0d5922ecb89a91d90cd277`。
- Run `34992781339` / Job `104461353200` / Artifact `10406003255` / success。
- Artifact SHA256 `171e6e1f22477a214b593ab28f1d1d2e3b7c369773ed83d1fd5a35aefdd891b5`。
- 母集団 20260201〜20260630、235R。3-ticket union pair hit=120/235=51.06%。
- 第1優先ticket pair分解: KEEP=67 / REPLACE_ONE=144 / REPLACE_BOTH=24。
- KEEP+REPLACE_ONE=211/235=89.79%。主力lap+turn+straightは KEEP48 / REPLACE_ONE115 / REPLACE_BOTH13。
- `SEPTEMBER_OUTCOMES_USED False` をログ確認。September UNREAD維持。
- 結論: pairをゼロから作り直さず、REPLACE_ONEで「片方を残し片方だけ交換」が次の本命。

## 次作業開始 — Wave4 one-replacement correction
1. Wave3の235Rを基準に、現行第1pairのどちらをKEEPするかを因果特徴だけで学習する。
2. REPLACE_ONEでは残す艇を決めた後、未選択の2〜6号艇からreplacement候補を順位付けする。
3. KEEPを誤って壊す false override を明示評価し、override閾値を設ける。
4. 同一race集合で first-pair baseline / corrected first-pair / 3-ticket union coverage / override率 / false-override damage / REPLACE_ONE rescue を比較する。
5. schemaごとの利用可能展示特徴に合わせ、存在しないstraight等を一律dropnaしない。
6. データが20260630までなので、可能なら train<20260601 / June frozen holdout を別評価する。
7. September 2026結果・払戻は絶対に読まない。production/LIVE条件は研究結果確定まで変更しない。

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
