# CHAT HANDOFF — 2026-09-15 — 4HEAD WR_ST AUG31 HISTORY VARIANT

## CURRENT RULES
- 2026年7月・8月結果は学習・検証に使用可。
- 2026年9月結果は `UNREAD` 維持。
- production `HEAD4_V291_COMP7` は変更しない。
- frozen opponent v283: SECOND `PLAYER_START`, conditional THIRD `COND_BASE`, `TOP2XTOP2`, alpha2=.60, Top4 exactly 4 tickets。v96禁止。
- closing oddsを使う評価はretrospective diagnosticのみ。formal prospective ROI=`NOT_COMPUTABLE`。

## KEY AUDITED STATE
- fixed candidate: Apr-Jun 86R / 35頭 / 40.6977%; Jul-Aug 78R / 35頭 / 44.8718%。
- final closing-odds audit Run `35060311090` / Job `104679045711` / Artifact `10432272637`: success, coverage 164/164, Apr-Aug ROI 129.71%。
- Apr-Jun ROI 167.73%、Jul-Aug ROI 87.79%。4頭時capture 51.43%→31.43%。
- v283 miss decomposition Run `35061928492` / Job `104683888325` / Artifact `10432044277`: success。
- Apr-Jun actual 4-head 35R: capture 18, SECOND miss 14, THIRD miss 3, pair-rank miss 0。SECOND-pass conditional THIRD capture 18/21=85.71%。
- Jul-Aug actual 4-head 35R: capture 11, SECOND miss 16, THIRD miss 8, pair-rank miss 0。SECOND-pass conditional THIRD capture 11/19=57.89%。
- July: SECOND-pass 13R, conditional THIRD capture 6/13=46.15%, THIRD miss 7。
- August: SECOND-pass 6R, conditional THIRD capture 5/6=83.33%, THIRD miss 1。

## AFTER — July conditional THIRD diagnostic
- 初回 Run `35063523492` / Job `104688743645` は `AttributeError: 'list' object has no attribute 'second_boat'` で失敗。
- `conditional_rows()` がlistを返すことへ型処理を修正。fix commit `e2081cb81991a25c10847ee6e8ec0a2f65b98e25`。
- 修正版 Run `35065837875` / Job `104695793974` / Artifact `10434471836`: success。marker `HEAD4_V283_JULY_COND_THIRD_MISS_ANALYSIS_OK`。
- July THIRD miss 7Rのactual-third conditional rankは、rank3が6R、rank4が1R。大半がTop2境界型。
- July SECOND-pass 13R中THIRD capture 6R=46.15%。Apr-Jun 18/21=85.71%、August 5/6=83.33%。Julyだけ明確に崩れた。
- rank3 missにはTop2境界probability差が小さい例があり、単純な大外しではなく「僅差3位の取り逃し」が主対象。
- production/frozen v283 unchanged。Sep `UNREAD`。v96禁止。

## BEFORE — rescue条件 + 僅差時の買い目追加研究
- ユーザー提案: 「救済条件調べると同時に僅差なら買い目増やすってのはどう？」→ 両方を同時比較する。
- 研究A: conditional THIRDのactual rank3を特徴量条件でTop2へ救済し、4点維持できる条件を探索する。
- 研究B: 2位と3位が僅差の場合だけTHIRD候補を3艇へ広げ、現行4点から原則6点へ増やす。元Top2は捨てない。
- 研究C: A+B併用も比較する。
- 比較対象: 現行4点 / 条件付き救済4点 / 僅差時6点 / 救済+僅差追加。
- 閾値はJulyだけへ後付け最適化しない。Apr-Junを開発側、Jul-Augを独立確認側として扱い、過学習を避ける。September outcomes/resultsは絶対に読まない。
- 評価項目: 発火R数、追加点数、追加投資、追加的中、払戻増、profit、retrospective closing-odds ROI、期間別capture。closing odds評価はretrospective diagnosticラベルを維持し、formal prospective ROIは`NOT_COMPUTABLE`。
- 特にJuly rank3 miss 6Rについて、rank2-rank3 probability gapとCOND_BASE feature contributionを使い、救済/追加条件がどれだけ拾えるか確認する。同時にApr-Jun/Jul-Augの既存的中を壊さないか確認する。
- production `HEAD4_V291_COMP7` / frozen v283は研究中変更しない。v96禁止。

Status: `HEAD4_V283_RESCUE_AND_CLOSE_MARGIN_TICKET_EXPANSION_RESEARCH_START`
