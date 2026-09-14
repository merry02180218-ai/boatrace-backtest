# CHAT HANDOFF — 2026-09-15 — 4HEAD WR_ST AUG31 HISTORY VARIANT

Predecessor: `CHAT_HANDOFF_20260915_4HEAD_ENV_V283_JULAUG_ENV_DONE.md`

## CURRENT RULES

- 2026年7月・8月の結果はユーザー明示承認により学習・履歴更新・検証に使用可。
- 2026年9月のレース結果は引き続き `UNREAD`。結果・払戻・結果ラベルを読まない。
- production `HEAD4_V291_COMP7` は変更しない。
- WR_STは検証専用。本番接続しない。
- frozen exact v283 と今回のvariantを混同しない。

## AFTER — 8/31履歴固定variant 入力契約完成

- policy: `HEAD4_B3_WR_ST_AUG31_HISTORY_VERIFY_V1`
- current 20項目 + 8/31固定 `pref_pl_*` 5項目 = 25項目×6艇を検証専用で構築可能。
- `exact_for_target=false`
- `usable_for_frozen_exact_v283=false`
- `production_action_authorized=false`
- `september_outcomes_used=false`
- CI: Run `34866278492`, Job `104050804419`, Artifact `10357217015`, success。
- production `HEAD4_V291_COMP7` は変更なし。

## BEFORE — 3号艇モデルのモーター差ロジックを4号艇へ移植

ユーザー方針変更: 4号艇モデルを全面再構築するのではなく、現在3号艇モデルで有効な「モーター差」を4号艇へ移植して検証する。

確認済み3号艇v288の代表モーター差ルート:

- B rescue は `c_b3_minus_b2_motor >= 0.22388571428571424`
- かつ `c_b3_inside_nst <= -0.0714285714285712`
- production-compatible PRE replay: 94R / 52 hits / ROI 172.561%
- route別 B: 18R / 9 hits / ROI 164.717%

今回やること:

1. 最新4号艇コードから、4号艇と1・2・3号艇のモーター評価入力と既存差分項目を特定する。
2. 3号艇v288の考え方をそのまま4号艇へ写すのではなく、4角攻撃に対応する比較軸を定義する。
3. 最低限 `4号艇 - 3号艇`, `4号艇 - 2号艇`, `4号艇 - 内側最強艇` のモーター差を作る。
4. 可能なら伸び/行き足寄りと出足/回り足寄りを分け、4角まくり型とまくり差し型を別比較する。
5. 7・8月結果は学習・検証に使用可。9月結果はUNREAD維持。
6. 現行production `HEAD4_V291_COMP7` は凍結比較対象とし、変更しない。
7. 最初は検証専用でバックテストし、S/A/B既存ルートとの比較、候補数、4号艇1着率、3連単的中率、ROIを回収する。
8. 作業後にcommit SHA / Run / Job / Artifact / 結論 / 次の再開地点を追記する。

Status: `HEAD4_MOTOR_DIFF_TRANSFER_STARTED`
