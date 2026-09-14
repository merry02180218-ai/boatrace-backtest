# CHAT HANDOFF — 2026-09-15 — 4HEAD ENV / V283 JUL-AUG OVERRIDE

## RULE OVERRIDE / USER APPROVAL

- 2026-09-15 JST: ユーザーから、4号艇モデルについて **2026年7月・8月は使用してよい** と明示承認あり。
- したがって、この作業単位以降は7月・8月の結果・履歴更新を、当日入力再現・履歴状態更新・検証に使用可とする。
- 旧 `CHAT_HANDOFF_20260914_4HEAD_BOAT3_WAKU10_NEXT.md` の「Jul/Aug outcome禁止」は、この作業単位では上記ユーザー承認で上書きする。
- 2026年9月の結果は引き続き **UNREAD / outcome-blind** を維持する。9月結果を入力補完・選択・閾値調整・検証に使わない。
- 4号艇production `HEAD4_V291_COMP7` はユーザーの明示承認なしに変更しない。
- 実投票・購入処理は追加しない。研究・再現・shadow入力監査に限定する。

## BEFORE — ENV 21項目 + v283 6艇×25項目 現在日取得・再現監査

- 作業開始時 latest main HEAD: `e11e75b9bcfd5f14cd586939b8a2bc91544d96b9`。
- 前作業の状態: `HEAD4_B3_WR_ST_SHADOW_V1` のcurrent-day source contractまでは完成。POST 7項目は取得系統がほぼ確定。残件はENV 21項目とv283 6艇×25項目の現在日取得・同一意味論再現。
- v283の既知系統: `v282.prep()` → `v279.build_source()` → `v270.prepare()` / `v274` / `v278`。当日展示6項目は `tkz / stt / original_exhibition` から生成。
- 重要な残件だった `pref_pl_*` 等の履歴系は、v221で日Dの特徴を凍結してから日D結果を履歴へ入れる因果的更新。今回から7月・8月結果を履歴状態更新に使えるため、9月時点までの状態再現可能性を再監査する。
- ENVは frozen 21 primitives の各生成元を `直接取得 / 決定的派生 / 過去状態 / 未解決` に分類する。
- v283は frozen SECOND 25 features を同じ分類で6艇分確認し、7・8月を含む履歴更新で9月当日まで再現できるか確認する。
- 9月 outcomeは絶対に読まない。production変更なし。閾値・重みの再調整なし。

Status: `ENV_V283_JULAUG_ALLOWED_AUDIT_STARTED`

## AFTER — v283 選手履歴5項目の7・8月解禁対応 / 因果再現監査

### 確認したv283 SECOND 25項目

25項目を生成元で分解した結果、以下まで確定した。

- 能力系5項目: `v93_grade / v93_national / v93_local / v93_motor / v93_nst`
  - 現在のrace card / waku系入力から結果非参照で生成可能。
- 枠位置4項目: `pos_boat_number / pos_inside4 / pos_outside4 / pos_distance4`
  - 艇番から決定的に生成可能。
- 当日展示6項目: `cur_ex / cur_st / cur_orig_lap / cur_orig_turn / cur_orig_straight / cur_orig_avg`
  - 既存current exhibition builderで結果非参照生成可能。
- 選手履歴5項目: `pref_pl_all_p2 / pref_pl_all_win / pref_pl_frame_p2 / pref_pl_recent_p2 / pref_pl_frame_win`
  - v221の因果更新状態から生成する項目。
- ST系5項目: `suf_st_raw / suf_st_raw_strength / suf_st_raw_rank / suf_st_corr_strength / suf_st_corr_rank`
  - 当日ST展示とtarget日より前のSTT補正から結果非参照で生成可能。

結論として、**25項目中20項目は9月結果を読まずに現在日まで同じ意味論で再現可能**。

### 選手履歴5項目の結論

- v221の意味論は、日Dの入力を日D結果反映前の状態で凍結し、その後に日D結果を履歴へ追加する。
- ユーザー承認により2026年7月・8月結果は履歴更新に使用可能になったため、**2026-09-01時点の選手履歴5項目は8月31日までの結果を使って完全再現可能**。
- 一方、2026-09-14時点の完全な選手履歴状態には2026-09-01〜09-13の結果更新が必要。
- 9月結果は引き続き `UNREAD` なので、**2026-09-14のv283選手履歴5項目を完全一致として生成することは現ルールでは不可**。
- この不足を中央値・既定値・8月31日状態で黙って補完しない。完全再現を要求された場合は条件不足として停止する。
- 監査用には8月31日までの切断状態を出せるが、`exact_for_target=false / usable_for_exact_v283=false` を明示し、exact v283推論には使わせない。

### 実装

追加:

- `build_4head_v283_player_history_julaug.py`
  - v221と同じ5項目の計算式・日次更新順序を再現。
  - 2025-10-01から履歴を更新。
  - 2026-08-31までの結果のみ許可。
  - 2026-09-01 targetまではexact。
  - 2026-09-14等、9月途中targetのexact生成は9月結果が必要なため自動停止。
  - `--allow-truncated` は監査専用で、exact v283利用不可フラグを必ず付与。
- `verify_4head_v283_player_history_julaug.py`
  - 7月・8月結果が履歴へ入ることを合成データで確認。
  - v221と同じ平滑化式・recent30更新を確認。
  - 9/1 exact PASS、9/14 exact拒否、9/14 truncated非利用可を確認。
  - 9月結果読込が発生しないことを確認。
- `.github/workflows/validate-4head-v283-player-history-julaug.yml`
  - 構文確認 + 契約検証 + 検証ログArtifact保存。

### Commit / Actions

実装系commit:

- `9d454a9ca66e3f92bc9f195ddbca5e0a31fec398` — player-history builder追加
- `882f37540d45dab519ca5523da05acb0839a76c9` — verifier追加
- `0daf6c0afdd54e25be295655738a86cbac10dffb` — 初回CI追加
- `c8db9797b2218410a16c6b4e014a403727bdd216` — 検証ログArtifact保存を追加した最終検証commit

初回CI:

- Run ID: `34864969925`
- Job ID: `104046393491`
- conclusion: `success`

Artifact付き最終CI:

- Run ID: `34865140935`
- Job ID: `104046969844`
- Job conclusion: `success`
- Artifact ID: `10356740746`
- Artifact name: `head4-v283-player-history-julaug-verify`
- Artifact digest: `sha256:6eab5e7ce0ce7a06f4c3071dc7f9d6c226c243732ecb21a01ec7ea69aa191898`

### production / データ境界

- production `HEAD4_V291_COMP7`: **変更なし**。
- WR_ST: **検証専用のまま**。
- 7月・8月結果: **今回から許可され、選手履歴再現に使用可能**。
- 9月結果: **UNREAD維持。今回も読んでいない**。

### 結論

- v283 SECOND 25項目のうち、9月結果なしでexact-current再現できるものは20項目まで確定。
- 選手履歴5項目は8月31日までの状態なら正確に再現できる。
- 2026-09-14 exact v283を成立させるには9月1〜13日の結果履歴が必要なので、現ルールでは停止が正解。
- よって、9月UNREADを維持したままWR_ST検証を続ける場合は、8月31日固定履歴を「exact v283」として偽装せず、別の検証専用仕様として扱う必要がある。

### 次の再開地点

1. `ENV_ENTRY` frozen入力21項目を同じ方式で `直接取得 / 決定的派生 / 過去状態 / 未解決` に最終分類する。
2. 9月結果を読まずに2026-09-14時点でexact再現できるENV項目を確定する。
3. v283選手履歴5項目は現状のexact fail-closedを維持する。
4. WR_ST検証を9月UNREADのまま進める必要があれば、`8/31固定履歴を使う別検証仕様` として明示的に分離し、production / frozen v283 exact経路へ混ぜない。
5. production変更・閾値変更・重み変更はしない。

Status: `V283_JULAUG_PLAYER_HISTORY_AUDIT_PASS_ENV_ENTRY_NEXT`

## BEFORE — ENV_ENTRY 21項目 最終分類 / 2026-09-14 exact可否監査

- この作業は上記v283履歴監査完了後の継続作業。
- 作業開始時の直前handoff commit: `51cf96247866725bbf052179e7ba7cbb71436f0b`。
- `ENV_ENTRY` frozen 21項目をコード上の実生成元まで再追跡し、各項目を `直接取得 / 決定的派生 / 過去状態 / 未解決` に確定する。
- 各項目について、2026-09-14時点で **9月結果を一切読まずにexact再現可能か** を判定する。
- 7月・8月結果はユーザー承認どおり使用可。
- 9月結果は `UNREAD` のまま。結果依存項目があれば黙って補完せず、exact不可として停止条件を明示する。
- production `HEAD4_V291_COMP7` とWR_STの本番接続は変更しない。今回も検証専用。

Status: `ENV_ENTRY_21_EXACT_AUDIT_STARTED`
