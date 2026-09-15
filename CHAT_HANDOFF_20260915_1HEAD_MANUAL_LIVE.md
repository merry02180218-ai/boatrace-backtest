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

## Wave5 rescue vs damage — 完了
- Run `34995646024` / Job `104471068416` / Artifact `10407751198` / success。
- Artifact SHA256 `9c8809e5c735b002b84e5c22b61f4d807b847ef4f17b58ab97081b29db75fb29`。
- threshold -0.05: 17 overrides / rescue5 / damage3 / hit24/71=33.80% / baseline比+2。
- 主力 `lap+turn+straight` は rescue3 / damage3 で差引0。`base` rescue1、`lap+turn` rescue1が純改善に寄与。
- threshold 0.05は overrides2 / rescue1 / damage0 / +1 と安全寄りだが発動が少ない。
- `SEPTEMBER_OUTCOMES_USED False` / `PRODUCTION_CHANGED False`。

## Wave6 場別効果監査 — 完了
- Run `34996525058` / Job `104474037072` / Artifact `10408615346` / success。
- Artifact SHA256 `27c075aa6aabd8dd63ff825d666bb4da53379ff8ae1df767aa651a0e3e0e7e68`。
- threshold -0.05 の場別: JCD06 浜名湖=8R baseline1→final3、rescue2/damage0、delta+2。JCD11 びわこ=4R baseline2→final0、rescue0/damage2、delta-2。JCD08 常滑=2R rescue1/damage1、delta0。JCD12 住之江=1R rescue1、delta+1。JCD18 徳山=9R rescue1、delta+1。
- JCD01 桐生はJune 5R、baseline pair 2/5、3-ticket union 3/5、Wave4 override発動0。
- 場差は有望だが小標本。production変更なし。
- `SEPTEMBER_OUTCOMES_USED False` / `PRODUCTION_CHANGED False`。

## 次作業開始 — Wave7 桐生×2号艇監査
1. ユーザー確定事項: `half`（半周ラップ）は桐生(JCD01)だけ。`half+turn+straight` は桐生専用schemaとして扱う。
2. ユーザー仮説「桐生は2号艇がよく相手に来る」を直接検証する。
3. June 5Rだけでなく、historical母集団の桐生 `half+turn+straight` 全対象を使い、実際の相手pairへの2号艇包含率を集計する。
4. 現行first pairが2号艇を含む/含まない、actual pairが2号艇を含む/含まないをクロスし、2を落としたmiss・2を残したhit・2を誤って残したmissを分解する。
5. 3-ticket unionでも2号艇を含むticketの有無とactual 2包含を確認し、「桐生だけ2を優先して残す」guardの救済数/破壊数/理論deltaを算出する。
6. 可能なら2着/3着別にも分解し、1-2-X と 1-X-2 のどちらに寄るか確認する。
7. 小標本のため、この監査だけでproduction化しない。September 2026結果・払戻は絶対に読まない。

## 現行production / LIVE
- production profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- HEAD cutoff `.78`、opponent core `SECOND G2=.45 / THIRD G3=1.00`。
- レース時刻自動controllerは停止。ユーザーが「判別して」等と依頼したときだけ直前判定。
- 03:00 JST daily preparation承認済み。
- LIVEでは結果・払戻を絶対に使用しない。`result_or_payout_used=False` / `chronology_guard=True`。

## schema production方針
正式対象: `lap+turn+straight`, `lap+turn`, `half+turn+straight`, `base`（baseは低標本フラグ）。
保留: `turn+straight`（OOF0）。
