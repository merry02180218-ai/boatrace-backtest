# CHAT HANDOFF — 2026-09-16 — 4HEAD RESCUE + CLOSE-MARGIN NEXT

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール
- 4号艇productionは `HEAD4_V291_COMP7`。研究中は変更しない。
- frozen opponentはv283: SECOND `PLAYER_START` / conditional THIRD `COND_BASE` / `TOP2XTOP2` / alpha2=.60 / exactly Top4=4点。
- v96禁止。
- 2026年9月のレース結果/outcomeは絶対に読まない。`UNREAD`維持。
- Jul/Aug 2026結果は使用可。
- closing odds評価はretrospective diagnosticのみ。formal prospective ROI=`NOT_COMPUTABLE`。
- 作業前後にこの引き継ぎへBEFORE/AFTERを追記し、Run/Job/Artifact/commit SHAを正確に残す。
- Actionsの多重発火を避ける。新規研究workflowは`workflow_dispatch` onlyを基本とする。

## 確定済み母集団/成績
- fixed candidate Apr-Jun: 86R / 35頭 / 40.6977%。
- Jul-Aug: 78R / 35頭 / 44.8718%。
- Apr-Aug: 164R / 70頭。
- closing odds final audit Run `35060311090` / Job `104679045711` / Artifact `10432272637`。
- Apr-Jun ROI 167.73%、Jul-Aug 87.79%、Apr-Aug 129.71%。retrospective only。
- 4号艇頭率はJul-Augで悪化していないため、ROI低下の主因は相手capture。

## v283 miss decomposition
Run `35061928492` / Job `104683888325` / Artifact `10432044277`, success, marker `HEAD4_V283_MISS_DECOMPOSITION_OK`。
- Apr-Jun actual 4-head 35R: HIT 18, SECOND miss 14, THIRD miss 3, pair-rank miss 0。SECOND-pass conditional THIRD capture 18/21=85.71%。
- Jul-Aug actual 4-head 35R: HIT 11, SECOND miss 16, THIRD miss 8, pair-rank miss 0。SECOND-pass conditional THIRD capture 11/19=57.89%。
- July: actual head4 24、SECOND miss 11、SECOND-pass 13、HIT 6、THIRD miss 7。conditional THIRD capture 6/13=46.15%。
- August: SECOND-pass 6、HIT 5、THIRD miss 1。conditional THIRD capture 5/6=83.33%。
- pair-ranking missは0。alpha2/joint pair rankは観測上の主因ではない。

## July conditional THIRD diagnostic
- 初回 Run `35063523492` / Job `104688743645` はlist/DataFrame型ミスで失敗。
- fix commit `e2081cb81991a25c10847ee6e8ec0a2f65b98e25`。
- 修正版 Run `35065837875` / Job `104695793974` / Artifact `10434471836`: success。
- marker `HEAD4_V283_JULY_COND_THIRD_MISS_ANALYSIS_OK`。
- July THIRD miss 7Rのactual-third rank: rank3=6R、rank4=1R。大半がTop2境界型。
- Apr-Jun conditional THIRD capture 85.71%、July 46.15%、August 83.33%。July固有の崩れ。

## close-margin scan AFTER
- Run `35068090390` / Job `104702907317` / Artifact `10435526237`: success。
- Apr-Jun開発側で gap <= 0.10 を選択。base 18/21=85.71% -> expanded 19/21=90.48%、10R発火、追加20点。
- Jul-Aug holdout: base 11/19=57.89% -> expanded 16/19=84.21%、12R発火、rank3救済5R、追加24点。
- July: 6/13=46.15% -> 11/13=84.62%、9R発火、救済5R、追加18点。Augustは5/6のまま、3R発火、追加6点。
- SeptemberはUNREAD、production unchanged。

## BEFORE — strict pair-level closing-odds ROI audit
- ユーザー指示: 「厳密比較して」。
- これから gap<=0.10 を固定し、official closing oddsをpair-levelで照合して、現行v283 exactly 4点 vs close-margin expanded 6点を同一母集団・同一100円/点で比較する。
- Apr-Junは開発、Jul-Augは完全holdoutとして分離。July/Augustも補助表示する。
- 比較項目: races, tickets, stake, hits, payout, profit, ROI, incremental stake/payout/profit、追加救済レース別の的中組番とclosing odds。
- closing oddsはretrospective diagnostic。formal prospective ROIはNOT_COMPUTABLEのまま。
- September outcome/resultsは絶対に読まない。
- production HEAD4_V291_COMP7 は変更しない。

Status: `STRICT_V283_4PT_VS_MARGIN6_ROI_AUDIT_IN_PROGRESS`
