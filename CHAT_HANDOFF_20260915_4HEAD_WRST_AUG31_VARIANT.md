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

## AFTER — 8/31履歴固定variant 入力契約完成

### 実装

追加:

- `assemble_4head_b3_wrst_aug31_history_variant.py`
  - commit: `43ae1f6cdaa21494d1013419572750edba29a592`
  - policy: `HEAD4_B3_WR_ST_AUG31_HISTORY_VERIFY_V1`
  - frozen v283 SECOND 25項目をartifactから確認。
  - 9月結果不要のcurrent 20項目と、8/31固定の `pref_pl_*` 5項目を別入力として受け取る。
  - 6艇×25項目へ結合するが、exact-currentとは扱わない。
  - current入力は締切前・result-blind・complete provenanceを必須化。
  - history入力は `history_end=2026-08-31`、`september_outcomes_read=false`、`exact_for_target=false`、`usable_for_exact_v283=false` を必須化。
  - 9月結果使用を示す履歴、exactを偽装する履歴、締切以後のcurrent snapshotは拒否。
- `verify_4head_b3_wrst_aug31_history_variant.py`
  - commit: `02f468ddb5b3aba2a124c8d692153bf83d82e2a1`
  - 合成入力で20+5=25項目×6艇の結合を確認。
  - `pref_pl_*` 5項目が8/31履歴からのみ入ることを確認。
  - September outcome history拒否、exact-v283偽装拒否、締切後snapshot拒否を確認。
- `.github/workflows/validate-4head-b3-wrst-aug31-history-variant.yml`
  - commit: `fc2deb6d490ec89bac42a7e2fef146dedb261e8e`
  - 構文確認、variant契約検証、contract evidence生成、Artifact保存。

### 固定された出力契約

variant出力は必ず以下を持つ:

- `policy=HEAD4_B3_WR_ST_AUG31_HISTORY_VERIFY_V1`
- `history_cutoff=2026-08-31`
- `history_mode=AUG31_TRUNCATED_VERIFICATION_ONLY`
- `exact_for_target=false`
- `usable_for_frozen_exact_v283=false`
- `production_action_authorized=false`
- `september_outcomes_used=false`
- `jul_aug_outcomes_allowed=true`
- `result_blind_current_sources=true`
- current features/boat = 20
- history features/boat = 5
- assembled SECOND features/boat = 25

これにより、8/31履歴を9/14 exact履歴と誤認してproduction/frozen exact v283へ流すことを契約上禁止した。

### GitHub Actions

- Workflow: `validate-4head-b3-wrst-aug31-history-variant`
- Run ID: `34866278492`
- Job ID: `104050804419`
- Run conclusion: `success`
- validated head SHA: `fc2deb6d490ec89bac42a7e2fef146dedb261e8e`
- Artifact ID: `10357217015`
- Artifact name: `head4-b3-wrst-aug31-history-variant`
- Artifact digest: `sha256:d89380d65e67743e7d804de51d4c3daa69cebd2c0ae33749874483a1b932ea61`

### 結論

- 9月結果を読まずに、WR_ST研究用のv283 6艇×25項目入力を技術的に組み立てる経路ができた。
- ただし5つの選手履歴は8/31固定なので、これは **2026-09-14 exact v283ではない**。
- このvariantは候補生成・配線確認・挙動監査のための検証専用であり、production判断やexact frozen v283の代用には使わない。
- Jul/Aug結果の解禁はこの5履歴項目の8/31状態再現に利用可能。
- September outcomesは今回も未読のまま。
- production `HEAD4_V291_COMP7`、閾値、重みは変更なし。

### 次の再開地点

1. 既存 `HEAD4_B3_WR_ST_SHADOW_V1` の候補生成/推論runnerに、今回の `HEAD4_B3_WR_ST_AUG31_HISTORY_VERIFY_V1` 入力を **検証専用の別入口** として接続する。
2. runner側でも `usable_for_frozen_exact_v283=false` / `production_action_authorized=false` を保持し、production出力へ昇格できないようにする。
3. 合成または結果非参照の事前入力だけで、PRE → POST → ENV → variant v283 → WR_ST候補出力まで一気通しの配線テストを作る。
4. この一気通しテストでは候補が出ても「検証候補」と明示し、実投票・production候補にはしない。
5. 9月結果は引き続き読まない。
6. production `HEAD4_V291_COMP7`、閾値、重みは変更しない。

Status: `WR_ST_AUG31_HISTORY_VARIANT_INPUT_CONTRACT_PASS_RUNNER_WIRING_NEXT`
