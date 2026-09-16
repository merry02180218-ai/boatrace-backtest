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

## SECOND-margin rescue validation AFTER
- Run `35089336519` / Job `104771656556` / Artifact `10443723290`, success, marker `HEAD4_V283_SECOND_MARGIN_VALIDATION_OK`。
- Apr-Jun developmentのみで選択したSECOND gap threshold=`0.20`。Jul/Augでthreshold tuningなし。
- SECOND-margin: Apr-Jun ROI 167.73% -> 140.46%, hits 18->22。Jul-Aug 87.79% -> 103.33%, hits 11->18。July 82.66% -> 120.99%, hits 6->12。August 95.56% -> 75.67%, hits 5->6。
- SECOND+THIRD combined: Apr-Jun ROI 129.37%, hits 24。Jul-Aug ROI 122.63%, hits 24。July ROI 146.18%, hits 17。August ROI 85.18%, hits 7。Apr-Aug ROI 126.14%, hits 48。
- August SECOND miss 5Rのactual SECOND rankは rank4, rank3, rank4, rank3, rank3。THIRD-only拡張では届かない構造が中心。
- ただしAugust全体のbase capture自体はJulyより悪いとは限らないため、「8月が単純により荒い」とは断定しない。miss depthと追加投資効率を分離して監査する。
- closing oddsはretrospective diagnosticのみ。formal prospective ROI=`NOT_COMPUTABLE`。September `UNREAD`。production unchanged。

## BEFORE — adaptive SECOND depth / staged ticket audit
- 次は一律Top3拡張ではなく、SECONDの境界強度に応じて4点→6点→必要時のみ深い拡張へ段階化できるかを調べる。
- actual SECOND rank3/rank4 missのscore gap構造をApr-Jun developmentとJul-Aug holdoutで比較する。
- PLAYER_STARTのrank2-3 gapに加えrank3-4 gap、rank2-4 cumulative gapを出し、rank4まで広げるべき事前シグナルがあるか確認する。
- 比較対象: frozen base4 / SECOND Top3 / SECOND Top4 / THIRD-margin / SECOND3+THIRD-margin / adaptive SECOND depth。
- adaptive ruleの閾値選択はApr-Junのみ。July/August個別結果で閾値を選ばない。
- official closing oddsでexact tickets/stake/payout/profit/ROIをsettleし、追加1点あたりの救済効率も比較する。
- 2026-09 outcome/resultsは絶対に読まない。production `HEAD4_V291_COMP7` unchanged。formal prospective ROI=`NOT_COMPUTABLE`。

## AFTER — adaptive SECOND depth / staged ticket audit
- Run `35111649299` / Job `104846602672` / Artifact `10453260665`, success。run head SHA `b494a0553af41491b473a216319d38afed5e2639`。
- Artifact `head4-v283-adaptive-second-depth` を回収して exact official closing odds で監査完了。
- Apr-Jun developmentだけで adaptive threshold を選択: `g3=0.20`, `g4=0.20`。selection=`Apr-Jun max profit, then ROI, fewer tickets, tighter thresholds`。Jul/Augでthreshold tuningなし。
- Apr-Jun: base4 344 tickets / 18 hits / ROI 167.73%。SECOND Top3 516 / 22 / 136.10%。SECOND Top4 688 / 27 / 139.38%。adaptive SECOND 656 / 27 / 146.17%。THIRD-margin 428 / 19 / 153.11%。SECOND3+THIRD 640 / 25 / 134.03%。adaptive+THIRD 821 / 29 / 129.43%。
- Jul-Aug holdout: base4 312 / 11 / 87.79%。SECOND Top3 468 / 18 / 102.01%。SECOND Top4 624 / 19 / 88.51%。adaptive SECOND 612 / 19 / 90.25%。THIRD-margin 389 / 16 / 115.35%。SECOND3+THIRD 582 / 24 / 121.15%。adaptive+THIRD 757 / 25 / 103.04%。
- July: base 82.66%。SECOND Top3 120.99%。THIRD-margin 141.72%。SECOND3+THIRD 146.18%。adaptive SECOND 90.74%。adaptive+THIRD 111.45%。
- August: base 95.56%。SECOND Top3 73.23% (hits 5->6)。SECOND Top4 85.12% (hits 5->7)。THIRD-margin 75.96% (hits 5)。SECOND3+THIRD 82.58% (hits 7)。adaptive SECOND 89.45% (hits 7)。adaptive+THIRD 89.80% (hits 8)。
- Apr-Aug: base 129.71%。SECOND Top3 119.89%。SECOND Top4 115.18%。THIRD-margin 135.13%。SECOND3+THIRD 127.90%。adaptive SECOND 119.18%。adaptive+THIRD 116.77%。
- August SECOND miss 5Rは rank4/rank3/rank4/rank3/rank3。rank4 missでも rank2-4 cumulative gap は約0.0585, 0.0469と小さく、深いSECOND候補自体は事前score上の僅差として検出可能だった。一方、adaptiveを広く使うとticket増加が重く、Jul-Aug holdout ROIは90.25%に留まる。
- 結論: `adaptive SECOND depth` 単独をproductionへ昇格する根拠は不足。現時点では `THIRD-margin` がApr-Aug ROI 135.13%で最も安定し、Jul-Augでは `SECOND Top3 + THIRD-margin` が121.15%まで改善するがApr-Jun/Apr-AugではROIを削るためproduction変更はまだしない。August救済のためのrank4拡張は命中数を増やすが、常時適用では投資効率が不足。
- 次の再開地点: SECOND深掘りを常時Top4にせず、`rank2-4 cumulative gap` が極小のときだけrank4を追加する sparse rescue をApr-Jun developmentで設計し、Jul-Aug holdoutで固定監査する。既存THIRD-marginとの組合せも比較する。
- closing oddsはretrospective diagnosticのみ。formal prospective ROI=`NOT_COMPUTABLE`。September `UNREAD`。production `HEAD4_V291_COMP7` unchanged。

Status: `ADAPTIVE_SECOND_DEPTH_AUDIT_COMPLETE_NEXT_SPARSE_RANK4_RESCUE`
