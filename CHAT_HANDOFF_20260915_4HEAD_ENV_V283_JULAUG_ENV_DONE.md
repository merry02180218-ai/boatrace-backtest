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
