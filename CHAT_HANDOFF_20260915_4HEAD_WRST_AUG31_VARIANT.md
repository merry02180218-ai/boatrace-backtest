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

## PREVIOUS RESULT — 全レース母集団 固定モーター条件
- Run `34906818624` / Job `104185318430` / Artifact `10371974671` / success
- Apr-Jun: 107R / 4頭27.10% / 3連単14.02% / ROI124.79%
- Jul-Aug: 89R / 4頭32.58% / 3連単7.87% / ROI72.70%

## RESULT — player4_all_win Pareto
- cut .210863: Apr-Jun 77R/29.87%; Jul-Aug 61R/42.62%
- cut .215605: Apr-Jun 75R/30.67%; Jul-Aug 61R/42.62%
- cut .230699: Apr-Jun 64R/32.81%; Jul-Aug 50R/50.00%

## RESULT — 項目別展示 頭率改善
- Run `34962290514` / Job `104358460571` / Artifact `10394097349` / success
- `straight4_adv_inside >= 0.0`: Apr-Jun 37R/37.84%; Jul-Aug 21R/52.38%。
- availability自体は加点しない。

## AFTER — モーター条件緩和 × 展示判定 Pareto
- Run `34966369280` / Job `104371677153` / Artifact `10394589438` / success
- exact: motor win `-0.0299361318939513`, motor 2ren `-7.080000000000001`, player `.215605`, ST `-0.6000000000000001`。
- Apr-Jun 111R / 36.94%; Jul-Aug 96R / 39.58%。

## AFTER — exact 111R replay × original exhibition combo
- Workflow `head4-111r-orig-combo`: Run `34970281220` / Job `104384603205` / Artifact `10397252191` / success。
- exact replay `EXACT_111R_REPLAY_OK`。
- fixed base Apr-Jun 111R/41頭/36.9369%; Jul-Aug 96R/38頭/39.5833%。
- selected `orig4_adv_inside >= -0.057777777777777706`:
  - Apr-Jun 86R / 40.6977%（same-availability 108R/37.0370%, +3.6606pt）。
  - Jul-Aug 78R / 44.8718%（same-availability 93R/40.8602%, +4.0116pt）。
- 100R前後40%は未達。86R候補を正式研究候補とする。
- Sep `UNREAD`、production unchanged。
Status: `HEAD4_111R_ORIG_COMBO_COMPLETE`

## BEFORE — 86R / 40.70% 候補 独立再現監査・月別・3連単ROI
ユーザー指定: 「この86R / 40.70%候補を独立再現監査して、月別安定性と3連単的中率・ROIまで確認」。

これからやること:
1. `analyze_4head_111r_orig_combo.py` の選択結果を読み込んで再集計するのではなく、別の監査コードで raw/source lineage から候補を独立再構築する。
2. 条件は固定: `motor_win_diff_4v3 >= -0.0299361318939513`, `motor_2ren_diff_4v3 >= -7.080000000000001`, `player4_all_win >= .215605`, `basic_complete=1`, `st4_adv_inside >= -0.6000000000000001`, `orig_avg_available=1`, `orig4_adv_inside >= -0.057777777777777706`。
3. Apr-Junで 86R / 頭率40.6977% を独立再現できることをassert。Jul-Augは条件固定のまま78R / 44.8718%を再現確認する。
4. Apr, May, Junを個別にR数・4号艇1着数・頭率で出し、特定月だけで成立していないか確認。Jul/Augも固定検証として月別表示する。
5. 3連単は研究中の4号艇系で使用している独立相手選び/チケット構成と、利用可能な締切前オッズスナップショットだけを使う。post-deadline oddsは禁止。欠損は明示し、都合のよい補完をしない。
6. 月別およびApr-Jun合計、Jul-Aug固定で、3連単的中R/的中率、stake、payout、profit、ROIを出す。賭け金ルールは監査対象の4号艇チケットルールを明記して固定する。
7. 頭率監査と3連単ROI監査を分離し、オッズ欠損で頭率母集団86R/78R自体を減らして見せない。ROI coverageを別途報告する。
8. 2026年9月結果は一切読まず `UNREAD`。production `HEAD4_V291_COMP7` は変更しない。
9. 実装→Actions→ログ/Artifact回収→独立再現・月別・ROI確認後、AFTERへ exact commit SHA / Run / Job / Artifact / 結果 / 結論 / 次の再開地点を記録してcommitする。

Status: `HEAD4_86R_INDEPENDENT_AUDIT_STARTED`

## HANDOFF UPDATE — 86R独立監査の途中経過 / 次チャット再開点

### 目的は未完了
86R候補について、独立再現 → 月別安定性 → 現行v283相手選びで3連単的中率/ROI → AFTER記録、までがゴール。現時点では **完了していない**。次チャットではここから続ける。

### BEFORE記録
- BEFORE handoff commit: `31c979a69aaa540508cda4562a982f8272593720`
- BEFORE時点 status: `HEAD4_86R_INDEPENDENT_AUDIT_STARTED`

### 最初の監査実装と失敗
- initial audit implementation: `3fbfe1da9600731f14b61d5a8d147b5b7bf97535`
- initial workflow: `478046c82f3ea5979a04e33773abae2aeeec87f5`
- initial trigger: `c03e684d7696f0a3e80b658acfc8af052b16d580`
- retrigger: `e6aa086fc81214bdc249badd66c04a8681848c08`
- dedicated Workflow: `audit-4head-86r-independent`
- failed Run `34974926857`
- failed Job `104400140027`
- exact primary traceback: `AttributeError: module 'analyze_4head_exhibition_original_trainonly' has no attribute 'build_base'`
- workflow側にも当初 `/tmp/head4_86r_audit` 作成前のtee問題があった。

### source lineage修正
`audit_4head_86r_independent.py` のhead候補再構築を正しいlineageへ修正:
- `base.settle_all()`
- merge `base.build_motor_features()`
- merge `base.build_prior_features()`
- `ex.build_ex(set(z.race_code))`
- exact fixed filters適用
- Apr-Jun `(86R,35 heads)` / Jul-Aug `(78R,35 heads)` assert

関連commit:
- source reconstruction fix: `bbaabd25e22f524932a3c508890c1e9e110de0b6`
- trigger: `1e41d3ceb6d81e50044ebf0400b5f0860e8453e2`
- extra trigger: `b612e404575d585dadd131b9ebcb04fedb9cf092`
- workflow YAML/mkdir fix: `1385b6a4895b93aa0f987e6195d772eba3da145c`
- retrigger: `a91d44c1c016d91ce45d52075020cf2430215a53`

### rerunで判明した重要事項
旧Run `34974926857` のrerun Job `104415607670` も failure。
理由: rerunは元Runの古いhead SHA `e6aa086...` をcheckoutするため、main上の修正版を実行しない。したがって旧Run rerunは今後使わない。fresh main SHAの新Runだけを正式監査に採用すること。

### v96混入を発見・排除
source reconstruction fix後の監査コードには、相手選びとして `analyze_v96_4corner_monthly_walkforward_tiebreak` が残っていた。これは現行4-head契約違反。

現行production/research opponent contract:
- production: `HEAD4_V291_COMP7`
- opponent: frozen independent `v283`
- SECOND: `PLAYER_START`
- conditional THIRD: `COND_BASE`
- pair mode: `TOP2XTOP2`
- `alpha2=.60`
- Top4 exactly 4 tickets
- v96 production signal **禁止**
- frozen inference module: `head4_v291_downstream_inference.py`
- live adapter: `build_4head_v283_live.py`
- frozen artifact: `artifacts/head4_v291_downstream_20260630.json`

監査コードはv96/post-deadline ROIを正式値として出さないfail-closed版へ修正済み:
- corrected audit commit: `85019562ccc8278099e7740cf163b4da65409acc`
- 現在の `audit_4head_86r_independent.py` はhead-rate独立再現を行い、正式ROIについてはv283 frozen feature rows + pre-deadline oddsが揃わなければ `NOT_COMPUTABLE` とする方針。
- archived/closing oddsを正式prospective ROIとして代用してはいけない。

### fresh SHA trigger調査
- fresh trigger commit: `56e3d3f5c5a1b53a34dac02aa1b462023802598e`
- このcommit自体はmain pushとしてGitHub Actionsに届いており、同SHAで4本のActions Runが生成されたことを確認。
- 例: `legacy-4head-research-trigger-only` Run `34983301866` は同SHA `56e3d3...` に反応（skipped）。
- しかし目的の `audit-4head-86r-independent` の新Runだけ生成されなかった。
- したがって Actions全体停止ではなく、専用workflowのtrigger/registration問題に絞られている。

### 注意: create_commitだけではmain pushにならない
発火調査中に以下のcommit objectも作成したが、`create_commit` はcommit object作成のみで、main refを動かさなければpushではない。これらを「mainへ反映済み」と誤認しないこと:
- `f8fc2058924e6b91bc0ea3896785f6e6a39d96f1`
- `ece2ac77f5a10f0f1a2ceb4d4404e6315bc81fd8`
- `e835c18f41d5a658c40916d6328fafe96d87601f`
- `2e0834a43d2a459cdd1c9c0d4550091b6fdd73d8`
これらはmain refへ明示的に反映した証拠がない限り、正式実装commitとして扱わない。

### 次チャットで最初にやること
1. **最新main HEADを取得**し、他チャット/他作業が進んでいるため絶対に `56e3d3...` へmainを巻き戻さない。
2. このhandoffと最新mainの `audit_4head_86r_independent.py` / `.github/workflows/audit-4head-86r-independent.yml` を読む。
3. 専用workflowがmain上でどう登録されているか確認。必要なら最新main HEADを親にしてworkflowを修正し、`update_file` などmainへ直接反映される方法でcommitする。
4. trigger fileも最新main上で更新し、**fresh main SHAの新Run**を生成する。旧Run `34974926857` のrerunは禁止。
5. 新Runでまず `HEAD4_86R_INDEPENDENT_REPLAY_OK` を通し、Apr-Jun 86/35、Jul-Aug 78/35を確認。
6. 月別 Apr/May/Jun/Jul/Aug の R / heads / head rate を回収。
7. 3連単は必ず frozen v283 を使う。Apr-Aug各raceの exact causal SECOND 25-feature / conditional THIRD 69-feature rowsを再構築できる既存builder/replayをrepoから探す。**v96で代用しない**。
8. formal ROIは official pre-deadline 120-way odds snapshotだけ。存在/coverageをrepo内で確認。なければ formal ROI=`NOT_COMPUTABLE` と明記。archived closing oddsを出す場合は別枠 retrospective diagnostic としてのみ。
9. 成功Runの exact Run / Job / Artifact ID、月別結果、ROI coverage/結果、結論をこのhandoffのAFTERへ追記してcommit。
10. Sep 2026 outcomesは最後まで `UNREAD`、production `HEAD4_V291_COMP7` unchanged。

### 最重要の禁止事項
- Sep 2026 outcomeを読まない。
- Jul/Augを再チューニングしてpristine扱いしない。
- v96を4-head opponentへ戻さない。
- post-deadline/closing oddsをformal ROIとして扱わない。
- 古いRunのrerun結果を修正版監査と誤認しない。
- mainを古いSHAへforce/resetしない。
- successful fresh Run + AFTER handoff commit前に「完了」と言わない。

Status: `HEAD4_86R_AUDIT_HANDOFF_READY_NEEDS_FRESH_MAIN_RUN`
