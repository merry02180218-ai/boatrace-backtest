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

## v283 miss decomposition
Run `35061928492` / Job `104683888325` / Artifact `10432044277`, success。
- Apr-Jun actual 4-head 35R: HIT 18, SECOND miss 14, THIRD miss 3, pair-rank miss 0。
- Jul-Aug actual 4-head 35R: HIT 11, SECOND miss 16, THIRD miss 8, pair-rank miss 0。
- July: actual head4 24、SECOND miss 11、SECOND-pass 13、HIT 6、THIRD miss 7。
- August: actual head4 11、SECOND miss 5、SECOND-pass 6、HIT 5、THIRD miss 1。

## THIRD close-margin strict audit AFTER
- gap<=0.10 fixed from Apr-Jun development.
- Run `35074469211` / Job `104723453680` / Artifact `10437831280`, success, marker `HEAD4_V283_MARGIN6_STRICT_CLOSING_ROI_OK`。
- Apr-Jun: base ROI 167.73% -> expanded 153.11%, hits 18->19。
- Jul-Aug holdout: base 87.79% -> expanded 115.35%, hits 11->16。incremental stake 7,700円 / payout 17,480円 / profit +9,780円 / incremental ROI 227.01%。
- July: base 82.66% -> expanded 141.72%, hits 6->11。incremental ROI 388.44%。
- August: base 95.56% -> expanded 75.96%, hits 5->5。THIRD追加では救済0。
- Apr-Aug: base 129.71% -> expanded 135.13%, hits 29->35。
- September UNREAD / production unchanged。

## BEFORE — SECOND-margin rescue validation
- ユーザー指示: 8月がより荒れている可能性を検証する。
- 観測上、August actual head4 11Rのmiss 6R中5RがSECOND miss、THIRD missは1R。JulyはTHIRD境界missが中心だったため構造が異なる。
- これから actual SECOND の PLAYER_START rank分布と rank2-rank3 gapをApr-Jun development / Jul-Aug holdout / July / Augustで監査する。
- SECOND Top2→Top3拡張をgap threshold scanし、thresholdはApr-Junだけで選ぶ。Jul-Aug/July/Augustには固定適用する。
- THIRD側は既確定gap<=0.10も併記し、base4 / SECOND6 / THIRD-margin / combined のcapture・ticketsを比較する。
- 可能な範囲でofficial closing oddsを同じpair-levelでsettleし、stake/payout/profit/ROIも出す。
- 月別結果を見てthresholdを選ばない。September outcome/resultsは絶対に読まない。
- production `HEAD4_V291_COMP7` unchanged。formal prospective ROI=`NOT_COMPUTABLE`。

Status: `SECOND_MARGIN_RESCUE_VALIDATION_IN_PROGRESS`
