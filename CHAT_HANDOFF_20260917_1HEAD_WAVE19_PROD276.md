# 1号艇 v351 Wave19 本番276R救済監査 — 2026-09-17

## BEFORE
- ユーザー指示: 「本番276Rで見たい」→実行承認済み。
- 現行production: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`。
- 基準: 276R / 1号艇1着241=87.32% / 3連単3点131=47.46%。
- Wave18のcutoff未満 `[.350,.375)` 拡張帯とは分離し、今回は現行production 276Rだけを母集団にする。
- Wave17/18の事前条件（BOAT3_STRONGER、候補1-3-5、slot2 replacement）を結果を見て変更せず本番276Rへ適用し、baseline/fixed3/rescue/damage/netを監査する。
- 月別・場別・schema別・strength bucket別も確認する。
- September 2026 outcomes/payoutsはUNREAD。`race_code < 20260901` hard guard。
- HEAD学習特徴へ展示を直接追加しない。
- 結果確認前にproduction変更しない。
