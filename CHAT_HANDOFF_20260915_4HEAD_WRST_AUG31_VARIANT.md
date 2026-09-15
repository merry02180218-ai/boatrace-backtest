# CHAT HANDOFF — 2026-09-15 — 4HEAD WR_ST AUG31 HISTORY VARIANT

## CURRENT RULES
- 2026年7月・8月結果は学習・検証に使用可。
- 2026年9月結果は `UNREAD` 維持。
- production `HEAD4_V291_COMP7` は変更しない。

## PREVIOUS RESULT — 4号艇−3号艇 モーター差
- Run `34901233777` / Job `104167416359` / Artifact `10371331473` / success
- fixed rule: `motor_win_diff_4v3 >= 0.010782 AND motor_2ren_diff_4v3 >= 0.4000pt`
- Apr-Jun v250 PRE>=0.18 universe: 65R / 4頭30.77% / 3連単16.92% / ROI140.56%
- Jul-Aug holdout: 23R / 4頭47.83% / 3連単13.04% / ROI131.46%
- implementation SHA `08e13b0cdc64e4006ba22a4c2dabfffd49f291cd`

## PREVIOUS RESULT — 全レース母集団 固定モーター条件
- successful rerun: Run `34906818624` / Job `104185318430` / Artifact `10371974671`
- commit `6802593f9824c7802ccecf5729ec2f0436f44580`
- Apr-Jun: 107R / 4頭27.10% / 3連単14.02% / ROI124.79%
- Jul-Aug: 89R / 4頭32.58% / 3連単7.87% / ROI72.70%
- Apr-Aug total: 196R / 4頭29.59% / 3連単11.22% / ROI101.14%

## RESULT — player4_all_win Pareto
- Run `34926782402` / Job `104246398587` / Artifact `10379723183` / success
- cut .210863: Apr-Jun 77R/29.87%; Jul-Aug 61R/42.62%; total 138R/35.51%
- cut .215605: Apr-Jun 75R/30.67%; Jul-Aug 61R/42.62%; total 136R/36.03%
- cut .224982: Apr-Jun 69R/31.88%; Jul-Aug 50R/50.00%; total 119R/39.50%
- cut .230699: Apr-Jun 64R/32.81%; Jul-Aug 50R/50.00%; total 114R/40.35%
- cut .242111: Apr-Jun 59R/33.90%; Jul-Aug 45R/53.33%; total 104R/42.31%

## BEFORE — オリジナル展示を項目単位availabilityへ分離
ユーザー指定: 「展示タイム／展示ST＝全場共通 → 回り足／直線／その他オリジナル展示＝それぞれ独立availability → オリジナル展示提供場そのものを加点しない」。
- `basic_complete` = 展示タイム+展示ST。
- `turn_available` / `straight_available` / `orig_avg_available` を独立判定。
- availability自体は加点しない。同一availability母集団内のベース頭率との差で評価する。
- Apr-Jun選択、Jul-Aug固定、Sep UNREAD、production frozen。
Status: `HEAD4_EXHIBITION_ITEM_AVAILABILITY_FIX_STARTED`

## RESULT — 項目別展示 頭率改善
- Run `34962290514` / Job `104358460571` / Artifact `10394097349` / success
- Apr-Jun `player4_all_win >= .210863` の直線available母集団: 64R / 4頭28.13%
- train-only selected: `straight4_adv_inside >= 0.0`: 37R / 14頭 / 37.84%（同一availability母集団比 +9.71pt）
- 緩め `straight4_adv_inside >= -0.0667`: 39R / 35.90%
- Jul-Aug fixed: selected 21R / 11頭 / 52.38%（同一availability母集団48.72%比 +3.66pt）
- availability自体は加点していない。Sep UNREAD、production frozen。

## BEFORE — モーター条件緩和 × 展示判定 Pareto
ユーザー指定: 「モーター条件緩めるとどうなる？」「やってみて」。
- 現行条件をApr-Junだけで段階緩和し、player力・基本展示・optional origを重ねる。
- availability自体は加点しない。
- Apr-Junで選択、Jul-Aug固定評価、Sep UNREAD、production frozen。
Status: `HEAD4_RELAXED_MOTOR_EXHIBITION_PARETO_STARTED`

## AFTER — モーター条件緩和 × 展示判定 Pareto
- Run `34966369280` / Job `104371677153` / Artifact `10394589438` / success
- executed head SHA `f40ad8c5c697de14e2aaef303789af9020b168ed`
- Apr-Jun最大ボリューム35%超: 111R / 4頭36.94%。
- exact: `motor_win_diff_4v3 >= -0.0299361318939513` / `motor_2ren_diff_4v3 >= -7.080000000000001` + `player4_all_win >= .215605` + `st4_adv_inside >= -0.6000000000000001`。
- ST判定前 Apr-Jun: 130R / 34.62%。展示STで +2.32pt。
- Jul-Aug fixed: 96R / 39.58%。
- orig平均は Apr-Jun 101R / 38.61%、Jul-Aug 92R / 44.57%。
- Sep `UNREAD`、production unchanged。

## BEFORE — 111R母集団 × オリジナル展示組み合わせ
- exact 111R/36.94%系を固定し、orig各項目を独立availabilityでtrain-only比較する。
- 第一目的は100R前後を維持し40%近辺。Jul-Augは固定評価。
- Sep `UNREAD`、production frozen。
Status: `HEAD4_111R_ORIG_COMBO_STARTED`

## INTERIM — 111R再現ズレ検出
- combo Run `34969019521` / Job `104380406547` / Artifact `10396239531` / success。
- 丸め値で固定したため Apr-Jun 103R/35.92%, Jul-Aug 84R/42.86%となり111Rを再現しなかった。
- 103R上の `orig4_adv_inside >= 0.044444...` は参考候補だが最終採用しない。

## BEFORE — exact 111R replay repair
- Run `34966369280` Artifact `10394589438` のexact thresholdsを再利用。
- exact 111R/41頭、Jul-Aug 96R/38頭をassertしてからorigを再評価。
- availability非加点、same-availability比較、Sep `UNREAD`、production frozen。
Status: `HEAD4_111R_EXACT_REPLAY_REPAIR_STARTED`

## AFTER — exact 111R replay × original exhibition combo
- repair BEFORE commit `34e3650b50a674b655d4d7ff760d675cc189b80f`。
- exact-threshold/assert implementation commit `268ecc58057b8ecac65928ad57534d2f2eca76eb`。
- trigger commit `77d4e30f74db65f311a86c0a21bcfbcd6d3a29fa`。
- Workflow `head4-111r-orig-combo`: Run `34970281220` / Job `104384603205` / Artifact `10397252191` / success。
- Artifact digest `sha256:dd89f32a0463f27ff223991c7b97639800b71d1ff440b3bb9eff58240f97aa96`。
- exact replay assertion passed: `EXACT_111R_REPLAY_OK`。
- fixed base Apr-Jun: 111R / 41頭 / 36.9369%。Jul-Aug fixed: 96R / 38頭 / 39.5833%。
- Apr-Jun train-only selected: `orig4_adv_inside >= -0.057777777777777706`。
  - same-availability Apr-Jun: 108R / 37.0370%。selected 86R / 40.6977%（+3.6606pt）。
  - Jul-Aug fixed same-availability: 93R / 40.8602%。selected 78R / 44.8718%（+4.0116pt）。
- volume/strength Pareto:
  - `orig4_adv_inside >= 0.046666666666666655`: Apr-Jun 75R / 41.3333%; Jul-Aug 71R / 45.0704%。
  - `straight4_adv_inside >= -0.13333333333333336`: Apr-Jun 71R / 42.2535%; Jul-Aug 49R / 48.9796%（same-availability +7.0877pt holdout）。
  - `straight4_adv_inside >= -0.0666666666666666`: Apr-Jun 62R / 40.3226%; Jul-Aug 39R / 51.2821%。
  - adaptive vote `score>=0.67`（min_n 1〜3で同じ結果）: Apr-Jun 58R / 41.3793%; Jul-Aug 60R / 45.0000%。
- 100R前後を維持するadaptive `score>=0.4`: Apr-Jun 101R / 37.6238%、Jul-Aug 87R / 42.5287%。40%には届かない。
- 結論: 100R前後の40%は未達。train-onlyで最大Rを優先して40%以上を満たす正式研究候補は `orig4_adv_inside >= -0.057777777777777706` の86R/40.70%。Jul-Augでも78R/44.87%と同方向改善。
- 2026年9月結果は `UNREAD` 維持。production `HEAD4_V291_COMP7` は変更なし。

Status: `HEAD4_111R_ORIG_COMBO_COMPLETE`
Next restart: 86R/40.70%候補を軸に、独立再現監査・月別安定性・3連単/ROIを確認してproduction昇格可否を判断する。