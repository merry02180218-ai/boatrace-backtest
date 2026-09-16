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
- まずfinal diagnostic artifactのrace-level出力を回収し、月別だけでなく、4号艇頭率、v283 Top4的中率、的中時配当、外れ方（SECOND miss / THIRD miss / 頭外れ）、高配当依存、7月と8月差を確認する。
- 必要なら既存feature列を使いApr-Jun vs Jul-Augの分布差を比較するが、候補条件・v283 policy・productionは変更しない。
- September 2026 outcome/resultsは絶対に読まない。`UNREAD`維持。

Status: `HEAD4_V283_JULAUG_ROI_DEGRADATION_ANALYSIS_STARTED`
