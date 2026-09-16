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

## AFTER — sparse rank4 rescue
- Run `35117061755` / Job `104865691490` / Artifact `10456830494`, success。run head SHA `79c9d69927c7a28216603ceb1800c29bc722a578`。
- Apr-Jun development選択ではgap24<=0.20が採用されたが、投資増が大きい。
- 追加検討として0.05/0.06固定値を全月（月別4〜8月）で比較する。
- September `UNREAD`、production unchanged。

## AFTER — gap24 0.05 / 0.06 fixed monthly audit
- Run `35119432005` / Job `104873127479` / Artifact `10456963422`, success。run head SHA `8c67e71ca4b74d76b9407151185f4b20daa6a0bd`。
- Artifact meta: fixed gap24=[0.05,0.06], THIRD gap=0.10, months=2026-04..08, September=`UNREAD`, production=`HEAD4_V291_COMP7 unchanged`。
- base4 monthly ROI: Apr 269.10%, May 145.29%, Jun 100.48%, Jul 82.66%, Aug 95.56%。Apr-Aug aggregate 129.71% / 656 tickets / 29 hits。
- gap24<=0.05 only: Apr 231.98% (fire4,+16 tickets,+0 hit), May 137.43% (fire2,+8,+0), Jun 90.09% (fire3,+12,+0), Jul 71.06% (fire12,+48,+1), Aug 123.97% (fire8,+32,+1)。aggregate 121.52% / 772 tickets / 31 hits。
- gap24<=0.06 only: Apr 231.98% (fire4,+16,+0), May 130.38% (fire4,+16,+0), Jun 90.09% (fire3,+12,+0), Jul 69.84% (fire16,+64,+2), Aug 122.73% (fire12,+48,+2)。aggregate 118.73% / 812 tickets / 33 hits。
- THIRD-margin alone: Apr 211.89%, May 120.36%, Jun 138.48%, Jul 141.72%, Aug 75.96%。aggregate 135.13% / 817 tickets / 35 hits。
- gap0.05+THIRD: Apr 181.82%, May 113.63%, Jun 124.35%, Jul 114.93%, Aug 125.03%。aggregate 128.39% / 969 tickets / 38 hits。
- gap0.06+THIRD: Apr 181.82%, May 108.19%, Jun 124.35%, Jul 110.66%, Aug 121.10%。aggregate 124.76% / 1018 tickets / 40 hits。
- actual SECOND rank4 miss rescue count: Apr 0/2, May 0/2, Jun 0/2 for both thresholds; Jul 2/4 at 0.05 and 4/4 at 0.06; Aug 1/2 at 0.05 and 2/2 at 0.06。
- 重要: Apr-Jun development期間では0.05/0.06ともrank4 missを1件も救済せず、追加投資だけ増える。Jul/Augでのみ救済が出るため、この結果を使って0.05/0.06をproduction採用すると後知恵になる。
- 結論: fixed 0.05/0.06 rank4 rescueはproduction昇格しない。特にTHIRD-margin単独がApr-Aug aggregate ROIで両併用案を上回る。August改善は確認できるが、Julyとdevelopment期間の投資効率悪化を相殺できない。
- formal prospective ROI=`NOT_COMPUTABLE`。September outcome/results=`UNREAD`。production `HEAD4_V291_COMP7` unchanged。

## AFTER — strict existing variant compare
- 新規Actionsは発火せず、既存の漏洩なし監査 Artifact `10443723290`（Run `35089336519` / Job `104771656556`）を再取得し、同一164R・同一closing-odds条件の `summary.csv` / `race_mode_detail.csv` を厳密再確認した。冗長な再計算workflowは作らない。
- Apr-Jun: base 344 tickets / 18 hits / ROI 167.73%; SECOND0.20 500 / 22 / 140.46%; THIRD0.10 428 / 19 / 153.11%; COMBINED 623 / 24 / 129.37%。
- Jul-Aug validation: base 312 / 11 / 87.79%; SECOND0.20 462 / 18 / 103.33%; THIRD0.10 389 / 16 / 115.35%; COMBINED 575 / 24 / 122.63%。
- July: base 82.66%; SECOND 120.99%; THIRD 141.72%; COMBINED 146.18%。August: base 95.56%; SECOND 75.67%; THIRD 75.96%; COMBINED 85.18%。
- Apr-Aug aggregate: base 656 / 29 / stake 65,600 / payout 85,090 / profit 19,490 / ROI 129.71%; SECOND 962 / 40 / 96,200 / 117,970 / 21,770 / 122.63%; THIRD 817 / 35 / 81,700 / 110,400 / 28,700 / 135.13%; COMBINED 1198 / 48 / 119,800 / 151,110 / 31,310 / 126.14%。
- 月別補足: Apr THIRD 211.89%, May 120.36%, Jun 138.48%; SECOND Apr 181.82%, May 164.35%, Jun 68.75%; COMBINED Apr 143.14%, May 146.32%, Jun 94.72%。THIRD0.10だけがApr-Jun各月すべて100%超だったが、Augustは75.96%であり月別安定性が保証されたわけではない。
- 研究判断: rank4 rescueは打ち切り。既存候補の中では `THIRD gap0.10` を次の独立prospective/shadow候補として保持する。理由は、Jul-Aug validationが115.35%で100%超、Apr-Aug aggregate ROIが4方式中最高135.13%、追加投資がSECOND/COMBINEDより小さいため。これはproduction昇格判断ではない。
- `SECOND gap0.20` と `COMBINED` はhit数を増やすが投資膨張が大きく、Augustも100%未満。研究候補として記録は残すが、次の主候補にはしない。
- closing oddsはretrospective diagnosticのみなのでformal prospective ROI=`NOT_COMPUTABLE`。September outcome/results=`UNREAD`。production `HEAD4_V291_COMP7` unchanged。

## BEFORE — next: THIRD0.10 prospective-shadow準備
- 次の作業は `THIRD gap0.10` をproductionへ入れず、4号艇production候補が出た時にbase4とTHIRD0.10の買い目差分を保存できるshadow出力を準備する。
- shadowは予測時点情報だけで作り、結果・払戻・closing oddsを参照しない。2026年9月 outcome/resultsは引き続き読まない。
- 既存production `HEAD4_V291_COMP7` の買い目や判定を変更しない。shadow追加により本番ロジックへ副作用を出さない。
- 実装する場合はworkflow_dispatch onlyまたは既存live出力への非侵襲なsidecarとし、発火前にコード差分を監査する。

Status: `RANK4_RESCUE_REJECTED_THIRD010_HELD_FOR_PROSPECTIVE_SHADOW`
