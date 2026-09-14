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

## BEFORE — 4号艇−3号艇 モーター勝率・2連対率 集中検証

ユーザー指定により比較軸を絞る。

これからやること:

1. 4号艇・3号艇それぞれのモーター勝率とモーター2連対率の実データ列・生成元を最新GitHubから特定する。
2. 主軸を `4号艇−3号艇` とし、少なくとも `motor_win_rate_diff_4_3` と `motor_2ren_rate_diff_4_3` を検証する。
3. 4〜6月を条件探索期間として、単独差・AND/OR・閾値帯を比較する。
4. 7〜8月は後段検証として候補数、4号艇1着率、3連単的中率、ROIを確認する。
5. 既存 `HEAD4_V291_COMP7` のS/A/Bを基準比較し、production自体は変更しない。
6. 9月結果・払戻・結果ラベルは一切読まず `UNREAD` を維持する。
7. 検証コード・workflowを追加し、CIで再現可能にする。
8. 完了後、commit SHA / Run / Job / Artifact / 結論 / 次の再開地点を追記する。

Status: `HEAD4_B4_MINUS_B3_MOTOR_WIN_2REN_STUDY_STARTED`

## INTERMEDIATE — 4号艇−3号艇 モーター勝率・2連対率 実装完了 / CI待ち

定義を確定:

- 公式race-cardにはモーター2連対率・3連対率は存在するが、独立した「モーター勝率」列はない。
- 今回の `motor_win_diff_4v3` は、同場・同モーターについて**当日より前の全レース結果だけ**から算出する1着率の `4号艇 - 3号艇` 差。
- `motor_2ren_diff_4v3` は公式race-card事前値のモーター2連対率の `4号艇 - 3号艇` 差。
- 各日の出走表でモーター番号と入力値を全レース分先に固定し、その日の結果は全固定後に履歴へ追加する。よって同日結果はその日の入力に入らない。
- 履歴開始は 2025-11-01、研究対象終端は 2026-08-31。2026-09結果はコード上も読まない。

実装:

- `analyze_4head_b4_minus_b3_motor_win_2ren.py`
  - initial commit `0107e3ecb86ffb2bd6e27373e557f9e4a77d4f7a`
  - causal history fix commit `26c0e4efd93cfc5b95fb9728cb1cf5a7c195e9cc`
- `.github/workflows/analyze-4head-b4-minus-b3-motor-win-2ren.yml`
  - initial commit `18b649a166a87059fd98a054852a0ae046c3a203`
  - frozen committed input optimization commit `08e13b0cdc64e4006ba22a4c2dabfffd49f291cd`
- BEFORE handoff commit `cee1076dbf94601e969ac85671492093ec9f3c53`

研究設計:

- candidate universe: v250 `PRE >= 0.18`
- Apr-Junだけで閾値を選択。
- 比較: `WIN_ONLY`, `2REN_ONLY`, `AND`, `OR`。
- 閾値候補はApr-Jun内の20/30/40/50/60/70/80 percentile。
- Jul-Augは選択後に条件固定してholdout評価。
- 1R 10,000円、prior-only v96相手順位、N=2..20から合成オッズ10.5最接近。
- ROIはarchived historical odds proxy。

CI状況:

- 初版 Run `34900742342`, Job `104165828652`: 旧workflowの重いPRE再構築が実行中。最終研究結果としては採用しない。
- causal fix Run `34901160996`, Job `104167181816`: 起動済み。
- 最適化済み正式検証 Run `34901233777`, Job `104167416359`: 現在queued。既存コミット済みのv250/v93凍結入力を使い、不要な再構築を省略した正式な結果回収対象。
- Artifact ID: Run完了前のため未発行。推測禁止。

現時点の結論:

- 4号艇−3号艇のモーター勝率差・2連対率差を事前情報として安全に再構築する実装は完了。
- バックテスト数値はRun完了前なので未確定。結果を推測しない。
- production `HEAD4_V291_COMP7` は変更なし。
- September outcomes remain `UNREAD`。

次の再開地点:

1. Run `34901233777` / Job `104167416359` の完了状態を取得する。
2. failureならjob logを読み、その場で修正して再実行。
3. successならArtifact IDを取得し、job log / summaryからApr-Jun選択条件、Jul-Aug holdoutのR数・4号艇1着率・3連単率・ROI、月別Jul/Augを回収する。
4. このhandoffに最終AFTERを追記し、Artifact ID・最終commit SHA・結論を固定する。
5. production昇格はしない。September結果は読まない。

Status: `HEAD4_B4_MINUS_B3_MOTOR_WIN_2REN_CI_PENDING`

## AFTER — 4号艇−3号艇 モーター勝率・2連対率 集中検証 完了

正式検証は成功。

- final implementation SHA: `08e13b0cdc64e4006ba22a4c2dabfffd49f291cd`
- causal motor-win fix SHA: `26c0e4efd93cfc5b95fb9728cb1cf5a7c195e9cc`
- Actions Run: `34901233777`
- Job: `104167416359`
- conclusion: `success`
- Artifact: `head4-b4-minus-b3-motor-win-2ren`
- Artifact ID: `10371331473`
- Artifact digest: `sha256:587c035450e4931438fcb41e2c60e9ca9515e1c857d8fb43e4ede28833c1057d`
- September blind / frozen-input guard: PASS

### Apr-Jun 条件探索

baseline:
- 189R
- 4号艇1着 55 / 29.10%
- 3連単 21 / 11.11%
- ROI 90.76%
- return 1,715,450円

選択された固定条件:

- rule: `AND`
- `motor_win_diff_4v3 >= 0.010782`
- `motor_2ren_diff_4v3 >= 0.4000pt`
- つまり、4号艇の事前モーター1着率が3号艇より約1.0782ポイント以上高く、かつ公式モーター2連対率も3号艇より0.4ポイント以上高いことを同時に要求。

chosen train:
- 65R
- 4号艇1着 20 / 30.77%
- 3連単 11 / 16.92%
- ROI 140.56%
- return 913,670円
- 月別ROI最低値 101.53%

### Jul-Aug 固定holdout

baseline holdout:
- 58R
- 4号艇1着 23 / 39.66%
- 3連単 6 / 10.34%
- ROI 94.05%
- return 545,510円

chosen holdout:
- 23R
- 4号艇1着 11 / **47.83%**
- 3連単 3 / **13.04%**
- ROI **131.46%**
- return 302,350円
- retention 23/58 = 39.7%

holdoutでbaseline比:
- 4号艇1着率: 39.66% -> 47.83% (+8.17pt)
- 3連単率: 10.34% -> 13.04% (+2.70pt)
- ROI: 94.05% -> 131.46% (+37.41pt)

### 月別 fixed rule

- 2026-04: 20R / 4頭率 25.00% / 3連単率 15.00% / ROI 141.40%
- 2026-05: 25R / 4頭率 36.00% / 3連単率 24.00% / ROI 171.12%
- 2026-06: 20R / 4頭率 30.00% / 3連単率 10.00% / ROI 101.53%
- 2026-07: 19R / 4頭率 42.11% / 3連単率 15.79% / ROI 159.13%
- 2026-08: 4R / 4頭率 75.00% / 3連単率 0.00% / ROI 0.00%

### 結論

- **4号艇−3号艇のモーター優位差は、4号艇頭判定の主要フィルタ候補として有望。**
- Apr-Junで選択した単純なAND条件が、条件を固定したJul-Augでも4号艇1着率・3連単率・proxy ROIのすべてをbaselineより改善した。
- 特にJulは19Rで4頭率42.11%、3連単率15.79%、ROI159.13%と強い。
- ただしAugは4Rしかなく、3連単0的中。Jul-Aug合算の改善だけでproductionへ昇格させない。
- ROIはarchived historical odds proxyであり、当時の不変LIVE締切前オッズではない。
- production `HEAD4_V291_COMP7` は変更なし。
- 2026年9月の結果・払戻・結果ラベルは引き続き `UNREAD`。

### 次の再開地点

1. 固定条件 `motor_win_diff_4v3 >= 0.010782 AND motor_2ren_diff_4v3 >= 0.4000pt` を変更せず、4号艇頭候補の主要モーターゲートとして比較する。
2. 現行S/A/B候補および新しい4号艇head再構築baselineにこのゲートを重ね、候補数・4号艇1着率・3連単率・ROIを比較する。
3. 特に8月4Rの小標本を補うため、許可済みの過去期間で時間分割を追加し、閾値を再最適化せず固定条件の再現性を見る。
4. その後、必要ならまくり型 / まくり差し型を分離して、このモーター優位条件の効き方を比較する。
5. production昇格はユーザー明示承認まで行わない。September outcomesは読まない。

Status: `HEAD4_B4_MINUS_B3_MOTOR_WIN_2REN_HOLDOUT_PASS_NEXT_CORE_GATE_TEST`
