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
- successful rerun: Run `34906818624` / Job `104185318430` / Artifact `10371974671`
- commit `6802593f9824c7802ccecf5729ec2f0436f44580`
- Apr-Jun: 107R / 4頭27.10% / 3連単14.02% / ROI124.79%
- Jul-Aug: 89R / 4頭32.58% / 3連単7.87% / ROI72.70%
- Apr-Aug total: 196R / 4頭29.59% / 3連単11.22% / ROI101.14%
- monthly ROI: Apr 91.23 / May 149.00 / Jun 124.78 / Jul 133.02 / Aug 16.30

## BEFORE — 4号艇の頭確率を優先して引き上げる追加研究

ユーザー指定: 「まず頭確率を上げよう。3連帯率や他の要素も他のモデルの最新情報から参考にしてやってみて」。

これからやること:
1. 現在の全レース母集団・固定モーター差条件をベースに、まず4号艇1着率の改善を最優先する。3連単ROIの最適化は後段に回す。
2. 4号艇と3号艇のモーター3連対率差を新しい中心候補として追加する。3連対率は prior-only の1着+2着+3着 / 出走数で因果的に再構築し、同日結果を当日入力へ混ぜない。
3. 他モデルの最新確定ロジックから、頭判定に効いている相対要素を候補化する。特に3号艇v288の最新確定要素（相手艇とのST差、内艇ST環境、モーター差）を4号艇向けに置き換えて比較する。
4. 候補入力は、4−3 motor win差 / 2連対率差 / 3連対率差に加え、4号艇自身の選手力、4コース/ST攻撃力、3号艇とのST差、1〜3号艇の壁・ST環境など、既存データで結果前に確定する項目だけを使う。
5. 4〜6月で条件探索し、7〜8月を固定条件の検証期間にする。単月だけの過適合を避けるため、月別頭率とR数も必ず確認する。
6. 目標はまず全体196R前後の母集団から、R数を極端に減らさず4号艇頭率を現状29.59%から35%近辺以上へ引き上げられる条件を探す。R数・頭率のPareto候補も残す。
7. 9月結果は一切読まず `UNREAD` 維持。production `HEAD4_V291_COMP7` は凍結。
8. 実装→CI→結果回収後、commit SHA / Run / Job / Artifact / 採用候補 / 月別頭率 / 次の再開地点を追記する。

Status: `HEAD4_HEADRATE_3REN_ST_ENV_RESEARCH_STARTED`

## RESULT — initial head-rate research
- implementation SHA `2e5df5c1feccfca4792bdc890de06434a5766823`
- Run `34907898020` / Job `104188682345` / Artifact `10372929335` / success
- fixed-base Apr-Jun: 107R / 4頭 27.10%
- selected train-only extra gate: `player4_all_win >= 0.230699`
- Apr-Jun selected: 64R / 4頭 32.81%; Apr 27.8% / May 37.0% / Jun 31.6%
- Jul-Aug fixed holdout: 50R / 25頭 / 50.00%; Jul 28R/53.6%, Aug 22R/45.5%
- September remained `UNREAD`; production unchanged.
- `player4_all_win` is prior-only and freezes the whole date before ingesting same-day results.
- ST source is `analysis_v93` / v90-v91 lineage. v93 explicitly treats these as prior-only frozen ST strengths and freezes opponent ranks before official outcome join. Because the original v90/v91 generator is not currently present on main under the expected filename, ST is not needed for the next univariate player-strength Pareto step; do not use ST to justify the chosen threshold until lineage is independently reproducible.

## BEFORE — player4_all_win threshold Pareto refinement
ユーザー指定: 続行。

これからやること:
1. fixed motor baseはそのまま、追加条件を causal `player4_all_win` 単独に限定して閾値Paretoを調べる。
2. 閾値候補はApr-Junだけから事前に作り、Jul-Augで閾値を選び直さない。
3. Apr-JunのR数・頭率・月別頭率を基準にPareto frontierを作り、代表候補をtrain-onlyで固定してからJul-Augを評価する。
4. 目標はApr-Augで100〜150R程度を残しつつ、4号艇頭率35%近辺以上を狙う。ただしholdoutを見て閾値を最適化した場合はpristine扱いしない。
5. STは今回の閾値選択には使わない。ST lineage監査は別系統で継続可能とする。
6. September outcomesは一切読まず `UNREAD` 維持。production `HEAD4_V291_COMP7` は変更しない。
7. 実装→CI→結果回収後、commit SHA / Run / Job / Artifact / Pareto表 / 結論 / 次の再開地点を追記する。

Status: `HEAD4_PLAYER_ALL_WIN_PARETO_STARTED`

## AFTER — player4_all_win threshold Pareto refinement
- BEFORE commit: `c5e11bad05c7570add019d55f58b9eb6e1a806d2`
- implementation commit: `7728506dd653a73bc1ff0827dc7bf0dcc1355662`
- workflow commit / executed SHA: `dfb914e965c874c6c66ab56dae25c4c7ec004f4e`
- Run `34926782402` / Job `104246398587` / Artifact `10379723183` / success
- CI guard: September blind / production frozen PASS.
- train-only Pareto representatives were fixed before holdout evaluation.

Key Pareto points:
- cut 0.204165: Apr-Jun 83R / 27.71%; Jul-Aug 65R / 43.08%; Apr-Aug 148R / 34.46%.
- cut 0.206905: Apr-Jun 80R / 28.75%; Jul-Aug 63R / 42.86%; Apr-Aug 143R / 34.97%.
- cut 0.210863: Apr-Jun 77R / 29.87%; Jul-Aug 61R / 42.62%; Apr-Aug 138R / 35.51%.
- cut 0.215605: Apr-Jun 75R / 30.67%; Jul-Aug 61R / 42.62%; Apr-Aug 136R / 36.03%.
- train-fixed representative cut 0.224982: Apr-Jun 69R / 31.88%; Jul-Aug 50R / 50.00%; Apr-Aug 119R / 39.50%.
- previous cut 0.230699: Apr-Jun 64R / 32.81%; Jul-Aug 50R / 50.00%; Apr-Aug 114R / 40.35%.
- train-fixed high-head representative cut 0.242111: Apr-Jun 59R / 33.90%; Jul-Aug 45R / 53.33%; Apr-Aug 104R / 42.31%.

Conclusion:
- `player4_all_win` 単独でも、R数を136〜138Rまで残しながらApr-Aug頭率35.5〜36.0%の帯に到達した。
- ただしApr-Jun単独の頭率は30%前後であり、35%超はJul-Augの強いholdout成績に支えられている。よって0.210863/0.215605をproduction採用とはしない。
- 0.224982以上はApr-Augでは非常に強いが、母数119R以下。holdoutの50%を見た後なので、今後この結果だけを理由に閾値を選び直すとholdout contaminationになる。
- 次は `0.210863`〜`0.215605` 周辺を「量を保つ基準帯」とし、Apr-Junだけでsecondary causal gateを探索してtrain頭率35%近辺へ上げられるか検証する。候補はmotor_3ren_diff、recent_p2、frame4/player strength等。STはlineage完全監査までは使わない。
- September 2026 remains `UNREAD`; production `HEAD4_V291_COMP7` remains frozen.

Status: `HEAD4_PLAYER_ALL_WIN_PARETO_COMPLETE_NEXT_SECONDARY_TRAIN_ONLY`

## BEFORE — 1号艇v351方式の展示・オリジナル展示を4号艇頭判定へ導入
ユーザー指定: 「1号艇モデルを参考にして展示とオリジナル展示データ入れてやってみて」。

これからやること:
1. 1号艇v351/v326系で実運用されている締切前Boatcast入力を4号艇研究へ移植する。対象は通常展示タイム、スタート展示、オリジナル展示の回り足・直線・複数項目平均。
2. 1号艇方式と同じく6艇相対比較を基本とし、4号艇自身の値だけでなく、4号艇−1〜3号艇、4号艇−全艇平均/最良艇、内3艇に対する優位度を候補化する。4角攻撃なので特に直線・展示STを重視し、回り足とのバランスも検証する。
3. 展示データは `data/previews/tkz`, `data/previews/stt`, `data/previews/original_exhibition` のレース前データだけを使用し、結果・払戻を特徴生成に使わない。ST補正を使う場合は1号艇v326同様、当日を入れる前の過去日まででbiasを凍結する。
4. まず既存fixed motor base + causal player帯を土台に、Apr-Junだけで展示gateを探索する。Jul-Augを見て閾値を選び直さない。
5. 展示欠損率/6艇complete率を必ず出し、欠損したレースを有利に除外して見かけの頭率を上げないよう、complete母集団と適用母集団を分けて報告する。
6. Apr-Junの4号艇頭率35%以上を第一目標とし、R数も維持する。Jul-Augはtrainで固定した条件のみ評価する。
7. 2026年9月結果は一切読まず `UNREAD` 維持。production `HEAD4_V291_COMP7` は変更しない。
8. 実装→CI→結果回収後、commit SHA / Run / Job / Artifact / 月別R数・頭率 / 展示complete率 / 結論 / 次の再開地点を追記する。

参考実装確認:
- 1号艇v351 live probeは締切前にBoatcast `tkz` / `stt` / `orig` を取得し、`tkz_all6`, `stt_all6`, `orig_turn_all6`, `orig_straight_all6`, `orig_avg_all6` をrequired completenessとしている。
- v326は展示タイム・展示ST・回り足・直線・orig平均を6艇相対marginへ変換し、ST biasを過去日までで凍結している。

Status: `HEAD4_EXHIBITION_ORIGINAL_RESEARCH_STARTED`
