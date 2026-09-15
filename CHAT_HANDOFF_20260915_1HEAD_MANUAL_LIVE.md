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
- 結論: Wave2は不採用。現行G2/G3 pairを維持する。

## G2/G3 pair補正研究 Wave3 — 完了
- 実装 commit `f95e7c02d5c4a0b1011f2ff78b26e8db19af07cd`。
- workflow/trigger commit `d7031c058749c6ad7b0d5922ecb89a91d90cd277`。
- Run `34992781339` / Job `104461353200` / Artifact `10406003255` / success。
- 母集団 20260201〜20260630、235R。3-ticket union pair hit=120/235=51.06%。
- 第1優先ticket pair分解: KEEP=67 / REPLACE_ONE=144 / REPLACE_BOTH=24。
- KEEP+REPLACE_ONE=211/235=89.79%。
- `SEPTEMBER_OUTCOMES_USED False`。September UNREAD維持。

## Wave4 one-replacement frozen June — 完了
- 実装 commit `3be754d21d727d3626924a2d159b2c25bb6c8efe`。
- workflow commit `d4c9d28f8973f31a93f93432fc6b0390bf4c3d47`。
- Run `34994619514` / Job `104467623981` / Artifact `10407745078` / success。
- Artifact SHA256 `4a64a1a6b5a16999ddf1dd1a89187c10dbfcfe51b626c586e5fd7824eaa4868d`。
- frozen June: TRAIN_R=164 / TEST_R=71 (20260601〜20260630)。
- June kind: KEEP22 / REPLACE_ONE39 / REPLACE_BOTH10。
- first-pair baseline=22/71=30.99%、3-ticket union=35/71=49.30%、always-replace=9/71=12.68%。
- threshold -0.05: overrides17 / hits24=33.80% / baseline22 / delta +2 / false-override damage3 / REPLACE_ONE rescue5。
- threshold 0.00: overrides10 / hits23=32.39% / delta +1 / damage1 / rescue2。
- threshold 0.05: overrides2 / hits23=32.39% / delta +1 / damage0 / rescue1。
- 結論: one-replacement方向は小幅改善するが、そのままproduction採用は不可。KEEP破壊を抑えながら救済を選別する必要あり。
- `SEPTEMBER_OUTCOMES_USED False` / `PRODUCTION_CHANGED False` を確認。

## 次作業開始 — Wave5 rescue vs damage 分解
1. frozen June 71Rを維持し、threshold -0.05で救えたREPLACE_ONE 5Rと壊したKEEP 3Rを明示抽出する。
2. marginだけでなく、keep/drop/replacement各艇の predicted probability、ex/st/rank、turn/straight/orig_avg rank、schema、現行pair構成の差を比較する。
3. June結果でルールを直接最適化してproduction化しない。まず診断として「damageを避けられる因果特徴」があるか確認する。
4. candidate guardを複数提示する場合は、同じJune 71Rで override数 / hit / delta / false damage / REPLACE_ONE rescue を併記する。
5. September 2026結果・払戻は絶対に読まない。production/LIVEは変更しない。

## 現行production / LIVE
- production profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- HEAD cutoff `.78`、opponent core `SECOND G2=.45 / THIRD G3=1.00`。
- レース時刻自動controllerは停止。ユーザーが「判別して」等と依頼したときだけ直前判定。
- 03:00 JST daily preparation承認済み。
- LIVEでは結果・払戻を絶対に使用しない。`result_or_payout_used=False` / `chronology_guard=True`。

## schema production方針
正式対象: `lap+turn+straight`, `lap+turn`, `half+turn+straight`, `base`（baseは低標本フラグ）。
保留: `turn+straight`（OOF0）。
