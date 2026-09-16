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

## BEFORE — Jul-Aug ROI degradation analysis
- ユーザー指示「調べて」。Apr-Jun ROI 167.73%に対してJul-Aug 87.79%へ低下した原因を、固定候補164R・frozen v283・公式締切時オッズのまま分解する。
- final diagnostic Artifact `10432272637` のrace-level出力を使用する。
- September 2026 outcome/resultsは絶対に読まない。`UNREAD`維持。

## AFTER — Jul-Aug ROI degradation analysis
- Artifact `10432272637` の `race_detail.csv` 164Rを直接集計。coverage 164/164。
- 4号艇頭率は Apr-Jun 35/86=40.70% → Jul-Aug 35/78=44.87% とむしろ上昇。したがってROI低下の主因はHEAD候補選別ではない。
- 4号艇が実際に頭だった35Rに限定したv283 Top4 captureは Apr-Jun 18/35=51.43% → Jul-Aug 11/35=31.43%。頭は同数35Rなのに相手Top4で拾えないレースが17R→24Rへ増えた。ここが最大の劣化点。
- 月別 capture: Apr 8/11=72.73%, May 7/15=46.67%, Jun 3/9=33.33%, Jul 6/24=25.00%, Aug 5/11=45.45%。特に7月が悪い。8月は相手capture自体は回復している。
- 的中時平均3連単オッズも Apr-Jun 32.06倍（median 30.1）→ Jul-Aug 24.90倍（median 18.7）へ低下。相手capture低下に加えて、拾えた的中の配当も低くなった。
- Apr-Jun hit odds: 10.9,11.1,16.5,17.6,19.0,19.1,20.3,21.8,29.4,30.8,30.9,31.4,34.3,37.9,47.7,53.7,67.8,76.8。
- Jul-Aug hit odds: 7.2,10.2,12.0,16.3,17.6,18.7,19.8,23.1,43.4,51.3,54.3。高配当側の拾い方も弱い。
- SECOND候補構成にもshiftあり。全ticket上の2着艇shareは boat1 43.0%→34.0%、boat5 12.2%→20.5%。実際に4頭だったレースのSECOND top2構成では (1,6) capture 5/6=83.3%→2/5=40.0%、(1,2) 7/15=46.7%→5/12=41.7%、Jul-Augで増えた(2,5)は2/7=28.6%。
- 結論: Jul-AugのROI低下は「4号艇が頭にならなくなった」ためではなく、主に frozen v283 の相手順位付け/capture劣化、特に7月の2・3着選択劣化。さらに的中時オッズ低下が重なった。
- 現artifactは実着2着/3着列を持たないため、SECOND miss と THIRD miss の厳密分離はまだ未実施。次の研究は4号艇頭35Rについて実着2/3をrace-levelへ付加し、SECOND Top2 miss / conditional THIRD miss / pair-ranking missを分離する。その上で7月に崩れた相手特徴を調べる。
- production `HEAD4_V291_COMP7` / frozen v283 はまだ変更しない。formal prospective ROI=`NOT_COMPUTABLE`。September outcome/results `UNREAD`。

Status: `HEAD4_V283_JULAUG_ROI_DEGRADATION_ANALYZED_NEXT_OPPONENT_MISS_DECOMPOSITION`
