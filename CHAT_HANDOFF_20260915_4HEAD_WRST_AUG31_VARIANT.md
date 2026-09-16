# CHAT HANDOFF — 2026-09-15 — 4HEAD WR_ST AUG31 HISTORY VARIANT

## CURRENT RULES
- 2026年7月・8月結果は学習・検証に使用可。
- 2026年9月結果は `UNREAD` 維持。
- production `HEAD4_V291_COMP7` は変更しない。

## KEY AUDITED STATE
- 4-head fixed candidate: Apr-Jun 86R / 35頭 / 40.6977%; Jul-Aug 78R / 35頭 / 44.8718%。
- frozen opponent v283: SECOND `PLAYER_START`, conditional THIRD `COND_BASE`, `TOP2XTOP2`, alpha2=.60, Top4 exactly 4 tickets。v96禁止。
- independent audit Run `34984842829` / Job `104434176443` / Artifact `10402973600`: success。
- closing-odds diagnostic Run `34991765053` / Job `104457918590` / Artifact `10406490587`: success。
- current diagnostic: Apr-Aug 164R中115R coverage=70.12%, hits=17, stake=46,000円, payout=63,070円, profit=+17,070円, ROI=137.11%。Aug 31Rはcoverage 0。
- retrospective diagnosticのみ。formal prospective ROI=`NOT_COMPUTABLE`。Sep `UNREAD`、production unchanged。

## BEFORE — 締切時オッズ coverage 100% 回収監査
- main `data/official_closing_odds3t/2026` は01〜07を確認、08 pathは現時点で404。
- official closing odds取得コード `tools/fetch_official_closing_odds3t.py` と既存archive workflowあり。
- coverage回収BEFORE commit `4b9b63c0a7889e93a1b4a26015431aed45211c2e`。
- Aug専用回収workflow追加 commit `3ac4f10dd3e9a5c79d7ba741387a4b9253b150f7`。

## BEFORE — Actions多重発火の整理を最優先
ユーザー指示: 「発火が複数しちゃうからそれを先にどうにかしよう」。coverage回収より先にActions trigger整理を行う。

## AFTER / PROGRESS — duplicate trigger cleanup
- BEFORE handoff commit: `39e82819fb12be777a7cd100f160fa9f7f81ef91`。
- `audit-4head-86r-independent.yml`: bare `push:` を削除し `workflow_dispatch` only。commit `5a9fbb122c631b33830f62df98a7cf84cf655691`。
- `audit-4head-v283-closing-odds.yml`: script/workflow path pushを削除し `workflow_dispatch` only。commit `29045dea2a5258d5c3ca8f28612dec30bc9791f1`。
- `recover-official-closing-odds3t-aug2026.yml`: self-path pushを削除し `workflow_dispatch` only。commit `512dce21d23bf64577e4856639c2961319985dfb`。
- `analyze-4head-b4-minus-b3-motor-full-universe.yml`: research script/workflow path pushを削除し manual only。commit `51564e7ce4fb15e913c59dd45d2b6668f1db2f8c`。
- `analyze-4head-b4-minus-b3-motor-win-2ren.yml`: research script/workflow path pushを削除し manual only。commit `20f51ac5b82b46bca854ed05d56a9c1dd6079120`。
- latest cleanup commit `20f51ac...` のActions runsを確認: `total_count=0`。少なくとも整理済み研究workflowによるcommit連鎖の多重発火は止まっている。
- `audit-4head-86r-independent-v2.yml` は元から `workflow_dispatch` only。
- `analyze-4head-111r-orig-combo.yml` は専用sentinel `start_4head_111r_orig_combo.txt` pathだけのpushで、通常commitでは発火しないため現状維持。
- production/live workflowは変更していない。`HEAD4_V291_COMP7` unchanged。
- September outcome `UNREAD`、v96禁止。

## BEFORE — targeted Aug 31R closing-odds recovery
- Full-Aug recovery Run `34995369072` / Job `104470152985` は長時間取得後 `cancelled`。Fetch step cancelled、commit step skippedで08 archiveは保存されなかった。
- 全31日×24場×12Rの総当たり再実行はやめる。
- 4号艇固定候補164RのうちAug 31Rだけを抽出し、その(date,jcd,rno)だけ公式 `odds3t` 締切時オッズを取得する targeted recovery に切替。
- 取得行は `source_type=official_closing`, `snapshot_type=closing_displayed`, `odds_mapping_version=official_table_v2` を明示し、既存archive互換形式で保存する。
- September 2026 outcome/resultsは絶対に読まない。`UNREAD`維持。
- production `HEAD4_V291_COMP7` unchanged、opponent frozen v283のみ、v96禁止。
- targeted recovery後にv283 retrospective closing-odds diagnosticを再実行し、Apr-Aug 164R coverageを再監査する。

Status: `HEAD4_TARGETED_AUG_CLOSING_ODDS_RECOVERY_STARTED`

## BEFORE — targeted recovery import-path fix
- 手動発火 Run `35040972097` / Job `104620526879` を確認。
- step `Recover only uncovered HEAD4 Apr-Aug candidate odds` は `ModuleNotFoundError: No module named 'audit_4head_86r_independent'` でfailure。公式サイト取得前のimport-path実装ミス。
- 原因: `tools/fetch_head4_targeted_closing_odds3t.py` を `python tools/...py` で起動すると `sys.path[0]` が `tools/` となり、repo root の `audit_4head_86r_independent.py` をimportできない。
- 修正方針: repo rootを明示的に `sys.path` へ追加してからcandidate auditをimportする。候補条件・v283・productionは変更しない。
- 修正後はworkflowを再発火して exact Run/Job と回収件数を確認する。September outcome/resultsは `UNREAD` 維持。

## AFTER — targeted recovery success
- Run `35041139038` / Job `104621037331`: success。
- uncovered candidate odds 49Rを49/49回収、FAILED 0。mainへ保存済み。
- September outcome/resultsは `UNREAD` 維持。

## BEFORE — final 164R frozen-v283 closing-odds audit
- targeted回収後のApr-Aug固定候補164Rを公式締切時3連単オッズで再監査する。
- diagnosticからv96 importを完全除去し、`analysis_v93_4corner_second_third.csv` を直接readする。
- frozen artifactが要求するfeature欠落はfail-closedにする。v283 `PLAYER_START + COND_BASE / TOP2XTOP2 / alpha2=.60 / Top4=4` は変更しない。
- retrospective diagnosticのみ。formal prospective ROI=`NOT_COMPUTABLE`。
- September 2026 outcome/resultsは絶対に読まない。`UNREAD`維持。production `HEAD4_V291_COMP7` unchanged。

Status: `HEAD4_FINAL_164R_V283_CLOSING_ODDS_AUDIT_STARTED`

## BEFORE — v283 conditional scenario feature repair
- Final audit Run `35059044185` / Job `104675270738` は `FROZEN_COND_FEATURE_MISSING:['t_is_boat1','t_is_boat2','t_is_boat3','t_is_boat5','t_is_boat6']` でfailure。
- frozen v282/v283実装を確認。`t_is_boat*` は展示進入ではなく、`analyze_v281_4head_opponent_third_scenario.add_scenario()` が作る「候補艇の艇番one-hot」scenario feature。v282 `make_pairs()` がそれを `t_` prefixでconditional THIRDへ渡している。
- 監査側 `build_long_all()` が `v281.add_scenario()` を飛ばしていたのが原因。v96とは無関係。
- 修正方針: v281をimportし、`v278.add_current()` 後に frozen研究と同じ `v281.add_scenario()` を適用してからrelative featuresを生成する。v283 policy・候補条件・odds・productionは変更しない。
- September outcome/resultsは `UNREAD` 維持。

Status: `HEAD4_V283_SCENARIO_FEATURE_REPAIR_STARTED`
