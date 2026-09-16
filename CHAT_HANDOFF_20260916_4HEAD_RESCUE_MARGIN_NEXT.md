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
- Run `35074469211` / Job `104723453680` / Artifact `10437831280`, success。
- Apr-Jun ROI 167.73% -> 153.11%, hits 18->19。
- Jul-Aug 87.79% -> 115.35%, hits 11->16。
- July 82.66% -> 141.72%, hits 6->11。August 95.56% -> 75.96%, hits 5->5。
- Apr-Aug 129.71% -> 135.13%, hits 29->35。

## SECOND-margin rescue validation AFTER
- Run `35089336519` / Job `104771656556` / Artifact `10443723290`, success。
- Apr-JunだけでSECOND gap=`0.20`選択。
- SECOND-margin: Apr-Jun ROI 140.46%, hits22。Jul-Aug 103.33%, hits18。July 120.99%, hits12。August 75.67%, hits6。
- SECOND+THIRD: Apr-Jun 129.37%, hits24。Jul-Aug 122.63%, hits24。July 146.18%, hits17。August 85.18%, hits7。Apr-Aug 126.14%, hits48。
- August SECOND miss 5R actual SECOND rank = rank4/rank3/rank4/rank3/rank3。

## AFTER — adaptive SECOND depth / staged ticket audit
- Run `35111649299` / Job `104846602672` / Artifact `10453260665`, success。run head SHA `b494a0553af41491b473a216319d38afed5e2639`。
- Apr-Junだけで `g3=0.20`, `g4=0.20` 選択。Jul/Aug tuningなし。
- Apr-Jun: base 167.73%; adaptive SECOND 146.17%; adaptive+THIRD 129.43%。
- Jul-Aug: base 87.79%; adaptive SECOND 90.25%; adaptive+THIRD 103.04%; THIRD-margin 115.35%; SECOND3+THIRD 121.15%。
- July adaptive SECOND 90.74%; adaptive+THIRD 111.45%。August adaptive SECOND 89.45% (hits7); adaptive+THIRD 89.80% (hits8)。
- August rank4 missのrank2-4 cumulative gapは約0.0585, 0.0469と小さい。常時深掘りは投資効率不足。
- 結論: adaptive SECOND depthはproduction昇格せず。次は極小gap時だけrank4追加。
- formal prospective ROI=`NOT_COMPUTABLE`。September `UNREAD`。production unchanged。

## BEFORE — 僅差時のみ4番手を追加する救済監査
- ユーザー了承を受け、2着候補の4番手を常時買わず「2番手から4番手までの評価差が極小のときだけ」追加する方式を検証する。
- 判定には結果を使わず、PLAYER_STARTの事前スコア `2番手-4番手累積差` のみを使う。
- 閾値候補はApr-Junだけで選択し、Jul-Augには固定適用する。7月/8月個別結果で閾値調整しない。
- 比較は base4、3着僅差補正、2着Top3+3着僅差補正、および「極小gap時だけ2着4番手追加」の各方式。
- 追加買い目数、追加的中、投資、払戻、利益、回収率をofficial closing oddsで監査する。
- 特にAugustのrank4 miss 2件を拾えるかと、そのためにJul-Aug全体で何点余計に買うかを分離して評価する。
- 2026年9月 outcome/resultsは絶対に読まない。production `HEAD4_V291_COMP7` unchanged。formal prospective ROI=`NOT_COMPUTABLE`。

## AFTER — sparse rank4 rescue
- Run `35117061755` / Job `104865691490` / Artifact `10456830494`, success。run head SHA `79c9d69927c7a28216603ceb1800c29bc722a578`。
- Apr-Jun development選択ではgap24<=0.20が採用されたが、投資増が大きい。
- 追加検討として0.05/0.06固定値を全月（月別4〜8月）で比較する。
- September `UNREAD`、production unchanged。

## BEFORE — gap24 0.05 / 0.06 固定・全月比較
- ユーザー要望により、閾値選択ではなく `gap24<=0.05` と `gap24<=0.06` を固定して4月・5月・6月・7月・8月を各月別に監査する。
- 各月で発火レース数、総買い目、追加買い目、的中数、base比追加的中、投資、払戻、利益、closing-odds ROIを比較する。
- actual SECOND rank4 missについて、0.05/0.06で何件救済対象になるかも月別に出す。
- base4および必要に応じTHIRD-margin併用も同じ月別表で比較する。
- 2026年9月 outcome/resultsは読まない。対象は2026-04-01〜2026-08-31のみ。production `HEAD4_V291_COMP7` unchanged。formal prospective ROI=`NOT_COMPUTABLE`。

Status: `FIXED_GAP_005_006_MONTHLY_AUDIT_IN_PROGRESS`
