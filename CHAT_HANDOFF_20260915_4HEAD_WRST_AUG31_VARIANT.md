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

## BEFORE — 全レース母集団で固定モーター条件を検証

ユーザー指定: 「レース数は全体でやってみて」。

これからやること:
1. これまでの `v250 PRE >= 0.18` 候補母集団を外し、対象期間の全レースを母集団にする。
2. 既に選択済みのモーター条件 `motor_win_diff_4v3 >= 0.010782 AND motor_2ren_diff_4v3 >= 0.4000pt` は再最適化せず固定する。
3. 4〜6月および7〜8月の全レースに適用し、全体R数、条件通過R数、4号艇1着率、3連単率、ROI、月別値を回収する。
4. v250 PRE>=0.18で先に絞った結果と比較し、このモーター条件単独でどこまで4号艇頭を抽出できるか確認する。
5. 9月結果は一切読まずUNREAD維持。
6. production `HEAD4_V291_COMP7` は変更しない。
7. CI完了後、commit SHA / Run / Job / Artifact / 結論 / 次の再開地点を追記する。

Status: `HEAD4_B4_MINUS_B3_MOTOR_FULL_UNIVERSE_STARTED`
