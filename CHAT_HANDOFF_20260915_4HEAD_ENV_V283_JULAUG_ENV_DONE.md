# CHAT HANDOFF — 2026-09-15 — 4HEAD ENV / V283 JUL-AUG — ENV DONE

Predecessor: `CHAT_HANDOFF_20260915_4HEAD_ENV_V283_JULAUG.md`

## RULES / CURRENT BOUNDARY

- ユーザー明示承認により、2026年7月・8月の結果は学習・履歴更新・検証に使用可。
- 2026年9月のレース結果は引き続き `UNREAD`。結果・払戻・結果ラベルを入力補完や検証に使わない。
- production `HEAD4_V291_COMP7` は変更しない。
- WR_STは検証専用のまま。本番接続しない。
- 入力不足時は推測・中央値補完せず、条件不足として出力しない。

## AFTER — ENV_ENTRY 21項目 exact監査

### 結果

`ENV_ENTRY` の21 primitive/current-race入力をコード上の実生成元まで再監査した。

分類:

- `直接取得`: 9項目
- `決定的派生`: 9項目
- `過去状態`: 3項目
- `未解決`: 0項目

結論:

- **21/21項目すべて、2026-09-14時点で9月レース結果を一切読まずにexact再現可能**。
- ただし必要な当日事前ソース・過去事前ソースが欠損している場合は条件不足として停止する。
- ENVの「過去状態」3項目は着順結果履歴ではなく、過去の事前展示・STT補正・モーター/preview状態をtarget日より前まで因果更新したもの。
- したがって2026-09-01〜09-13の**事前情報**は使えるが、9月の**レース結果**を読む必要はない。
- 7月・8月結果は今回ユーザー承認で使用可能になったが、ENV 21項目のexact再現自体には結果ラベルは不要。

### 21項目の分類

直接取得:

- `wind_speed`
- `entry_course_preview`
- `has_orig`
- `has_stt`
- `has_tkz`
- `tilt`
- `v91_ex`
- `v91_st_raw`
- `v91_straight`

決定的派生:

- `preview_comp`
- `relative_deg`
- `wind_adjust_points`
- `entry_confirmed_same`
- `tilt_bonus`
- `score_BASE_v91`
- `score_CORR20_v91`
- `score_RAW20_v91`
- `score_wind_v83`

過去状態:

- `v91_st_corr`
- `history_adjust_online`
- `history_pct_online`

未解決: 0

### 重要な生成元

- current tilt: BOATCAST `bc_j_tkz`
- current exhibition entry: BOATCAST `bc_j_stt`
- current weather: BOATCAST `bc_sui` の事前天候のみ
- original exhibition / current exhibition: 既存current exhibition builder
- v74 history: `while d < target` で当日前までのpreview/motor状態を更新
- `build_history_before()` は `data/results` / payout / odds を読まない
- `wind_adjust_points` はcurrent結果から再学習せず、v83 old-period `2025-11-01..2026-05-31` の凍結マッピングを決定的に再生する

凍結v83 HEAD4風補正:

- `追い_0-2m`: -2.0
- `向かい_0-2m`: -2.0
- `左横_3-4m`: +2.0
- その他: 0.0

### PRE / POSTについて

- 今回の21項目監査は `ENV_ENTRY` のprimitive/current-race 21項目が対象。
- frozen `ENV_ENTRY` 全体は25項目。
- 21 primitivesに加え、上流から渡される `PRE` と `POST` が2項目。
- 残る2項目は決定的派生:
  - `p4_joint = PRE * POST`
  - `post_x_entry_same = POST * entry_confirmed_same`
- よってENV側の次の問題は21 primitivesではなく、上流PRE/POSTおよびWR_ST全体のREADY判定との接続。

### 実装 / CI

追加:

- `audit_4head_env_entry_21_exact.py`
  - commit: `54ea442b871200234597e0236128a61c037398cd`
  - 21項目のschema一致、分類、結果非参照履歴、事前ソース、凍結v83風補正を監査。
- `.github/workflows/validate-4head-env-entry-21-exact.yml`
  - commit: `4fde1a38fb21d6f0b64a3d61c182667ead07ef23`
  - 構文確認 + 21項目監査 + Artifact保存。

GitHub Actions:

- Run ID: `34865503994`
- Job ID: `104048199712`
- conclusion: `success`
- Artifact ID: `10356661895`
- Artifact name: `head4-env-entry-21-exact-audit`
- Artifact digest: `sha256:5629da5d9891e859410ee308f42086633f9be4c8eae864236756f6d88b4213f0`

### v283との対比

- ENV 21: **21/21 exact-current再現可能、9月結果不要**。
- v283 SECOND 25: **20/25は9月結果不要**。
- v283の残る5項目 `pref_pl_*` は選手の過去着順結果状態なので、2026-09-14 exactには9/1〜9/13結果が必要。
- 9月結果`UNREAD`を守る限り、2026-09-14 frozen exact v283はその5項目で停止する。
- 8/31固定履歴をexact v283として偽装しない。

### production / データ境界

- production `HEAD4_V291_COMP7`: **変更なし**。
- WR_ST: **検証専用**。
- 7月・8月結果: **使用可**。
- 9月結果: **UNREAD維持、今回も読んでいない**。

Status: `ENV_ENTRY_21_EXACT_AUDIT_PASS`

## BEFORE — WR_ST current-day READY判定の一本化

次は、現在までに確定した入力契約を1つの検証専用READY判定へまとめる。

やること:

1. ENV 21/21 exact可を明示する。
2. v283 20/25 exact可を明示する。
3. v283 `pref_pl_*` 5項目は2026-09-14 exactでは9月結果が必要なためBLOCKEDとする。
4. September outcome `UNREAD` のままなら、frozen exact v283経路の最終推論を出さない。
5. 必要なら8/31履歴を使う検証専用variantは、frozen exact v283 / productionから明確に分離する。
6. production、閾値、重みは変更しない。
7. CIでREADY/BLOCKED契約を固定し、Run/Job/Artifactまで回収する。

Status: `WR_ST_CURRENT_DAY_READINESS_GATE_STARTED`

## AFTER — WR_ST current-day READY判定の一本化

### 実装

追加:

- `audit_4head_b3_wrst_current_readiness.py`
  - 初回commit: `065cb9841da70b0bfdaaf8a50515d2adc303a356`
  - POST / ENV / v283 の現在日再現可否を1つの検証専用レポートへ統合。
  - 2026-09-14 exact-currentを例に、ENV 21/21、v283 20/25、v283履歴5項目BLOCKEDを明示。
  - `production_action_authorized=false`、`september_outcomes_read=false` を固定。
- `.github/workflows/validate-4head-b3-wrst-current-readiness.yml`
  - commit: `8997e1b754f68bd0ba5c7fc7fe8e4c95d99db795`
  - レポート生成、期待契約assert、Artifact保存。

### 初回CI failure と修正

初回:

- Run ID: `34865796033`
- Job ID: `104049206417`
- conclusion: `failure`
- 原因: readiness監査スクリプトがmodel runtimeをimportし、その依存先で `numpy` が必要だったが、この軽量CIにはnumpyを入れていなかったため `ModuleNotFoundError: No module named 'numpy'`。
- モデル契約・READY/BLOCKED判定の矛盾による失敗ではなく、監査スクリプトの不要な依存関係が原因。
- 初回RunではArtifactは保存されていない。

修正:

- `audit_4head_b3_wrst_current_readiness.py` をPython標準ライブラリのみで動くよう変更。
- frozen ENV 21 schemaを監査側に明示し、v283 SECOND 25 schemaは `artifacts/head4_v291_downstream_20260630.json` を直接JSON読込して確認する方式へ変更。
- 修正commit: `a2f02ee146215fba0477f333b0553f2cd2f6b4ec`

### 最終CI

- Workflow: `validate-4head-b3-wrst-current-readiness`
- Run ID: `34865910925`
- Job ID: `104049576389`
- Run conclusion: `success`
- Job steps: レポート生成 `success` / September outcome-blind契約assert `success` / Artifact保存 `success`
- validated head SHA: `a2f02ee146215fba0477f333b0553f2cd2f6b4ec`
- Artifact ID: `10356657553`
- Artifact name: `head4-b3-wrst-current-readiness`
- Artifact digest: `sha256:e90af83628d6a2d727cb4e0dc038c3d053db4bb59712e6790ab5dad6dc8ba596`

### READY/BLOCKED確定結果

POST 7項目:

- `READY_IF_PREDEADLINE_SOURCES_AVAILABLE`
- 9月結果不要。

ENV_ENTRY primitives 21項目:

- `READY_IF_PREDEADLINE_SOURCES_AVAILABLE`
- exact: **21/21**
- 9月結果不要。

v283 SECOND 25項目:

- 9月結果なしでexact-current再現可能: **20/25**
- 2026-09-14 exactでBLOCKEDになる5項目:
  - `pref_pl_all_p2`
  - `pref_pl_all_win`
  - `pref_pl_frame_p2`
  - `pref_pl_recent_p2`
  - `pref_pl_frame_win`
- 理由: 9/14時点のexactな選手履歴状態には9/1〜9/13のレース結果更新が必要。

WR_ST overall:

- `BLOCKED_EXACT_V283_SEPTEMBER_UNREAD`
- `may_emit_frozen_exact_wrst_decision=false`
- つまり、**9月結果UNREADを維持する現在ルールでは、2026-09-14のfrozen exact v283を使った完全なWR_ST判定は出さない**。
- これは不具合ではなく、結果漏洩を避けるための正しい停止条件。

### production / データ境界

- production `HEAD4_V291_COMP7`: **変更なし**。
- WR_ST: **検証専用のまま**。
- 閾値・重み・production policy: **変更なし**。
- 7月・8月結果: **使用可**。
- 9月結果: **UNREAD維持。今回も読んでいない**。
- 8/31履歴状態を9/14 exactと偽装する経路は作っていない。

### 結論

- current-day入力再現の未解決点はかなり絞れた。
- POSTは事前ソースがあればREADY。
- ENVは21/21 exact-current READY。
- v283は20/25 READY、残る5つの選手履歴だけがSeptember `UNREAD`ルールと衝突する。
- よって、今後も9月結果を読まないなら、WR_ST研究を続けるには **8/31までの履歴で明示的に打ち切った検証専用variant** をexact frozen v283とは別物として作るのが安全な次手。

### 次の再開地点

1. `HEAD4_B3_WR_ST` 用に、8/31時点の選手履歴を使う **明示的な検証専用variant** を設計する。
2. variantには必ず `exact_for_target=false` / `usable_for_frozen_exact_v283=false` / `production_action_authorized=false` / `september_outcomes_used=false` を持たせる。
3. exact v283 / production経路とファイル名・policy名・出力manifestを分離する。
4. 8/31履歴variantを使った場合にWR_ST候補生成まで技術的に通せるか、結果を見ずに入力契約だけをCI検証する。
5. production `HEAD4_V291_COMP7`、閾値、重みは触らない。
6. もし将来ユーザーが9月結果の使用も明示的に解禁した場合のみ、9/14 exact v283の5履歴項目を再構築する。

Status: `WR_ST_CURRENT_DAY_READINESS_GATE_PASS_BLOCKED_BY_V283_SEP_HISTORY`
