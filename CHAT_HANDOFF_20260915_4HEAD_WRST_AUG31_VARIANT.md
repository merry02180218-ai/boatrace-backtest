# CHAT HANDOFF — 2026-09-15 — 4HEAD WR_ST AUG31 HISTORY VARIANT

## CURRENT RULES
- 2026年7月・8月結果は学習・検証に使用可。
- 2026年9月結果は `UNREAD` 維持。
- production `HEAD4_V291_COMP7` は変更しない。

## KEY AUDITED STATE
- 4-head fixed candidate: Apr-Jun 86R / 35頭 / 40.6977%; Jul-Aug 78R / 35頭 / 44.8718%。
- frozen opponent v283: SECOND `PLAYER_START`, conditional THIRD `COND_BASE`, `TOP2XTOP2`, alpha2=.60, Top4 exactly 4 tickets。v96禁止。
- independent audit Run `34984842829` / Job `104434176443` / Artifact `10402973600`: success。
- retrospective diagnosticのみ。formal prospective ROI=`NOT_COMPUTABLE`。Sep `UNREAD`、production unchanged。

## AFTER — targeted recovery + final 164R frozen-v283 closing-odds audit
- targeted recovery Run `35041139038` / Job `104621037331`: success。uncovered 49Rを49/49回収、FAILED 0。
- final audit Run `35060311090` / Job `104679045711` / Artifact `10432272637`: success。
- Apr-Aug fixed candidate 164R coverage=164/164=100%。
- Apr: 25R, head4 11R, hits 8, profit +16,910円, ROI 269.10%。
- May: 35R, head4 15R, hits 7, profit +6,340円, ROI 145.29%。
- Jun: 26R, head4 9R, hits 3, profit +50円, ROI 100.48%。
- Jul: 47R, head4 24R, hits 6, profit -3,260円, ROI 82.66%。
- Aug: 31R, head4 11R, hits 5, profit -550円, ROI 95.56%。
- Apr-Jun ROI 167.73%、Jul-Aug ROI 87.79%、Apr-Aug ROI 129.71%。
- retrospective closing-odds diagnostic only。formal prospective ROI=`NOT_COMPUTABLE`。
- production `HEAD4_V291_COMP7` unchanged、frozen opponent v283 unchanged、v96禁止、September outcome/results `UNREAD`。

## AFTER — Jul-Aug ROI degradation analysis
- Artifact `10432272637` の `race_detail.csv` 164Rを直接集計。coverage 164/164。
- 4号艇頭率 Apr-Jun 35/86=40.70% → Jul-Aug 35/78=44.87%。ROI低下主因はHEADではない。
- 4頭時v283 Top4 capture Apr-Jun 18/35=51.43% → Jul-Aug 11/35=31.43%。特にJul 6/24=25.00%。Aug 5/11=45.45%。
- 的中時平均オッズ Apr-Jun 32.06倍 → Jul-Aug 24.90倍。
- SECOND候補構成もshift: ticket上boat1 43.0%→34.0%、boat5 12.2%→20.5%。
- production/frozen v283 unchanged。formal prospective ROI=`NOT_COMPUTABLE`。Sep `UNREAD`。

## BEFORE — v283 opponent miss decomposition
- ユーザー指示「お願いします」。4号艇が実際に頭だった70Rへ実着2着/3着をrace-level出力し、v283の失敗を厳密に分解する。
- 現auditはp2/conditional-third/pairsを内部計算しているがartifactにはactual second/thirdやSECOND Top2、actual-second条件のTHIRD Top2を保存していない。
- audit出力を診断用に拡張し、actual_second/actual_third、second_top2、second_top2_hit、actual-secondに対するconditional third top2、conditional_third_top2_hit、final_pair_hitを保存する。
- これにより `SECOND miss` / `THIRD miss` / `pair-ranking miss` をApr-Jun vs Jul-Aug、月別で分離する。
- frozen v283のスコアリング・候補条件・productionは変更しない。これはretrospective diagnostic拡張のみ。
- v96禁止。September 2026 outcome/resultsは絶対に読まない。`UNREAD`維持。

Status: `HEAD4_V283_OPPONENT_MISS_DECOMPOSITION_STARTED`
