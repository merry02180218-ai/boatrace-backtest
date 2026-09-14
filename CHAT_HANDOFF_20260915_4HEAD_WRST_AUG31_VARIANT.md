# CHAT HANDOFF — 2026-09-15 — 4HEAD WR_ST AUG31 HISTORY VARIANT

Predecessor: `CHAT_HANDOFF_20260915_4HEAD_ENV_V283_JULAUG_ENV_DONE.md`

## CURRENT RULES

- 2026年7月・8月の結果はユーザー明示承認により学習・履歴更新・検証に使用可。
- 2026年9月のレース結果は引き続き `UNREAD`。結果・払戻・結果ラベルを読まない。
- production `HEAD4_V291_COMP7` は変更しない。
- WR_STは検証専用。本番接続しない。
- frozen exact v283 と今回のvariantを混同しない。

## BEFORE — 8/31履歴固定のWR_ST検証専用variant

前段監査の確定事項:

- POST 7項目: 事前ソースがあればREADY、9月結果不要。
- ENV_ENTRY primitives 21項目: 21/21 exact-current再現可、9月結果不要。
- v283 SECOND 25項目: 20/25は9月結果不要。
- 残る `pref_pl_*` 5項目は、2026-09-14 exact-currentでは9/1〜9/13結果が必要なため、September `UNREAD`ルール下ではBLOCKED。
- READY gate final CI: Run `34865910925`, Job `104049576389`, Artifact `10356657553`, success。

今回やること:

1. 8/31までの選手履歴状態を明示的に使う検証専用policyを作る。
2. policy名・manifest・出力を exact frozen v283 / production と明確に分離する。
3. 必須フラグを固定する:
   - `exact_for_target=false`
   - `usable_for_frozen_exact_v283=false`
   - `production_action_authorized=false`
   - `september_outcomes_used=false`
4. 8/31履歴5項目を使っても、それを9/14 exact-historyとは呼ばない。
5. WR_ST候補生成まで技術的に入力を流せる契約を、レース結果を一切見ずにCIで検証する。
6. production `HEAD4_V291_COMP7`、閾値、重み、frozen exact v283は変更しない。
7. 作業完了後、commit SHA / Actions Run・Job・Artifact ID / 結論 / 次の再開地点をこのhandoffへ記録する。

Status: `WR_ST_AUG31_HISTORY_VARIANT_STARTED`
