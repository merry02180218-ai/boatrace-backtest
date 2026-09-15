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

### BEFORE記録
- BEFORE handoff commit: `31c979a69aaa540508cda4562a982f8272593720`
- corrected audit commit: `85019562ccc8278099e7740cf163b4da65409acc`
- handoff restart commit: `eecc2500098ca26ad001903267805be032be5f27`
- 旧Run `34974926857` のrerunは禁止。fresh main SHAの新Runだけを正式監査に採用する。

### 現行production/research opponent contract
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

### 最重要の禁止事項
- Sep 2026 outcomeを読まない。
- Jul/Augを再チューニングしてpristine扱いしない。
- v96を4-head opponentへ戻さない。
- post-deadline/closing oddsをformal prospective ROIとして扱わない。
- 古いRunのrerun結果を修正版監査と誤認しない。
- mainを古いSHAへforce/resetしない。

## AFTER — 86R独立再現監査 完了
- fresh audit head SHA: `c732387d1bbf01afb4ffdb266d08eb1f74a2399b`
- Workflow: `audit-4head-86r-independent`
- Run `34984842829`: success
- Job `104434176443`: success
- Artifact `10402973600`
- marker: `HEAD4_86R_INDEPENDENT_REPLAY_OK`

### 頭率独立再現
- Apr-Jun: 86R / 35頭 / 40.6977%
- Apr: 25R / 11頭 / 44.00%
- May: 35R / 15頭 / 42.86%
- Jun: 26R / 9頭 / 34.62%
- Jul: 47R / 24頭 / 51.06%
- Aug: 31R / 11頭 / 35.48%
- Jul-Aug fixed: 78R / 35頭 / 44.8718%
- 4月・5月・6月の全月で30%台後半以上を維持し、Apr-Jun 40.70%は単一月だけの突出ではない。Jul-Aug固定でも44.87%を維持した。

### v283 3連単監査
- frozen v283 contractは `TOP2XTOP2`, `alpha2=.60`, Top4 exactly 4 tickets。
- 現行の独立監査では、86R/78Rに対して検証可能な exact causal v283 feature replay rows と、formal prospective用途として認められた pre-deadline 120-way odds snapshot の組を確認できなかった。
- formal ROI coverage: 0%。したがって正式な3連単的中率 / stake / payout / ROIは `NOT_COMPUTABLE`。
- v96による代用はしていない。
- post-deadline/archived closing oddsを正式prospective ROIへ代用していない。
- 締切時オッズを retrospective diagnostic として別枠利用する研究は可能だが、今回の formal prospective audit 値には混ぜない。

### workflow発火修正
- fresh trigger: `96ab5744cdcd321c07ece62cba1284e3faf8ebf6`
- workflow registration/all-push修正: `13ff51aa80e2b67ff314a6a464788b04632e3ffb`
- registered trigger: `5e34ca175ab8840d8cdbe1294604fa89a229455e`
- fresh v2 workflow追加: `c732387d1bbf01afb4ffdb266d08eb1f74a2399b`
- このfresh main SHAで正式成功Run `34984842829` を取得した。

### 結論
- 86R候補の頭率は独立再現監査を通過。Apr-Jun 40.70%、Jul-Aug 44.87%。
- 月別にも極端な単月依存は確認されない。
- v283 formal 3連単ROIは、必要なcausal replay + prospective odds coverage不足のため捏造せず `NOT_COMPUTABLE` と確定。
- September 2026 outcomes: `UNREAD`。
- production `HEAD4_V291_COMP7`: unchanged。

### 次の再開地点
1. 86R候補は頭率監査済み研究候補として扱う。
2. 3連単を追加研究する場合は、frozen v283のApr-Aug exact causal SECOND/THIRD feature replayを構築し、締切時オッズは formal prospective と分離した retrospective diagnostic として評価する。
3. audit用に一時的に広げたworkflow triggerと重複v2 workflowは、他作業への影響を確認してから整理する。productionロジックには触れない。
4. September 2026 outcomesは引き続き `UNREAD`。

Status: `HEAD4_86R_INDEPENDENT_AUDIT_COMPLETE`

## BEFORE — v283 締切時オッズ retrospective diagnostic
ユーザー明示許可: 「締切時オッズでいいよ、検証なんだから」。したがって、従来の formal prospective ROI 監査とは明確に分離し、Apr-Aug の **retrospective diagnostic** として締切時3連単オッズを使用してよい。

これからやること:
1. 86R/78R候補の母集団・固定条件は一切変更しない。
2. frozen v283 (`PLAYER_START` SECOND + `COND_BASE` conditional THIRD, `TOP2XTOP2`, alpha2=.60, Top4=4点) を正規ロジックで過去レースへ再現する。v96代用は禁止。
3. 利用可能な `official_closing` / 締切時3連単オッズを各v283買い目へ結合し、coverageを明示する。
4. Apr, May, Jun, Jul, Aug および Apr-Jun / Jul-Aug / Apr-Aug 合計について、対象R、coverage、的中R、stake、payout、profit、ROIを計算する。
5. この値は retrospective diagnostic と明記し、formal prospective ROIとは混同しない。
6. September 2026 outcomesは引き続き `UNREAD`。production `HEAD4_V291_COMP7` は変更しない。
7. 実装→fresh Actions Run→Job/Artifact/ログ確認→AFTER追記まで行う。

Status: `HEAD4_V283_CLOSING_ODDS_DIAGNOSTIC_STARTED`
