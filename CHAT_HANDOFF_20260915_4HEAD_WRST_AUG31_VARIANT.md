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

## RESULT — player4_all_win Pareto
- Run `34926782402` / Job `104246398587` / Artifact `10379723183` / success
- cut .210863: Apr-Jun 77R/29.87%; Jul-Aug 61R/42.62%; total 138R/35.51%
- cut .215605: Apr-Jun 75R/30.67%; Jul-Aug 61R/42.62%; total 136R/36.03%
- cut .224982: Apr-Jun 69R/31.88%; Jul-Aug 50R/50.00%; total 119R/39.50%
- cut .230699: Apr-Jun 64R/32.81%; Jul-Aug 50R/50.00%; total 114R/40.35%
- cut .242111: Apr-Jun 59R/33.90%; Jul-Aug 45R/53.33%; total 104R/42.31%

## BEFORE — オリジナル展示を項目単位availabilityへ分離
ユーザー指定: 「展示タイム／展示ST＝全場共通 → 回り足／直線／その他オリジナル展示＝それぞれ独立availability → オリジナル展示提供場そのものを加点しない」。
- `basic_complete` = 展示タイム+展示ST。
- `turn_available` / `straight_available` / `orig_avg_available` を独立判定。
- availability自体は加点しない。同一availability母集団内のベース頭率との差で評価する。
- Apr-Jun選択、Jul-Aug固定、Sep UNREAD、production frozen。
Status: `HEAD4_EXHIBITION_ITEM_AVAILABILITY_FIX_STARTED`

## RESULT — 項目別展示 頭率改善
- Run `34962290514` / Job `104358460571` / Artifact `10394097349` / success
- Apr-Jun `player4_all_win >= .210863` の直線available母集団: 64R / 4頭28.13%
- train-only selected: `straight4_adv_inside >= 0.0`: 37R / 14頭 / 37.84%（同一availability母集団比 +9.71pt）
- 緩め `straight4_adv_inside >= -0.0667`: 39R / 35.90%
- Jul-Aug fixed: selected 21R / 11頭 / 52.38%（同一availability母集団48.72%比 +3.66pt）
- availability自体は加点していない。Sep UNREAD、production frozen。

## BEFORE — モーター条件緩和 × 展示判定 Pareto
ユーザー指定: 「モーター条件緩めるとどうなる？」「やってみて」。

これからやること:
1. 現行 `motor_win_diff_4v3 >= .010782 AND motor_2ren_diff_4v3 >= .4000pt` を基準点として、Apr-Junだけでモーター条件を段階的に緩和する。
2. motor win差 / 2連対率差の閾値をtrain分位点と現行閾値でグリッド化し、現行107Rより広い150R/200R/250R近辺も含む母集団Paretoを作る。
3. 各モーター母集団に causal `player4_all_win` と、全場共通の展示タイム・展示STを適用し、さらに各orig項目がavailableな場合だけ回り足/直線/orig平均を追加評価する。
4. orig availabilityそのものは加点しない。各orig条件の改善幅は必ず同一availability母集団のベース頭率との差で評価する。
5. 第一目的はApr-Junで最終4号艇頭率35%以上を保ちながらR数最大化。35%未満もParetoとして残し、頭率と件数の交換関係を出す。
6. 閾値・構成の選択はApr-Junだけ。Jul-Augはtrainで固定した代表候補だけ評価し、holdoutを見て再選択しない。
7. 2026年9月結果は一切読まず `UNREAD`。production `HEAD4_V291_COMP7` は凍結。
8. 実装→Actions→結果回収後、commit SHA / Run / Job / Artifact / モーター母集団R / 最終R・頭率 / 月別 / holdout / 結論をAFTERへ追記する。

Status: `HEAD4_RELAXED_MOTOR_EXHIBITION_PARETO_STARTED`

## AFTER — モーター条件緩和 × 展示判定 Pareto
- Run `34966369280` / Job `104371677153` / Artifact `10394589438` / success
- executed head SHA `f40ad8c5c697de14e2aaef303789af9020b168ed`
- Apr-Jun最大ボリューム35%超: 111R / 4頭36.94%。
- 条件: relaxed motor `motor_win_diff_4v3 >= -0.029936` / `motor_2ren_diff_4v3 >= -7.08pt` + `player4_all_win >= .215605` + `st4_adv_inside >= -0.60`。
- 同条件の展示ST判定前 Apr-Jun: 130R / 34.62%。展示STで +2.32pt。
- Jul-Aug fixed: 96R / 39.58%。同条件base 39.82%からほぼ横ばい。
- orig平均 `orig4_adv_inside` は候補条件で Apr-Jun 101R / 38.61%、Jul-Aug 92R / 44.57%。同一availability比 Apr-Jun +3.97pt / Jul-Aug +3.82pt。
- 9月結果は `UNREAD` 維持。production `HEAD4_V291_COMP7` は変更なし。
Conclusion: 35%以上を保ちながら100R超へ拡張できた。次は111R/36.94%系を軸にorig項目をavailability非加点のまま組み合わせ、100R前後を維持して40%近辺を狙う。

## BEFORE — 111R母集団 × オリジナル展示組み合わせ
ユーザー指定: 「続けて」。

これからやること:
1. Apr-Junで選択済みの111R/36.94%系（relaxed motor + player4_all_win + basic展示ST）を固定の出発点にする。
2. `turn4_*` / `straight4_*` / `orig4_adv_inside` を項目別availabilityで扱い、availabilityそのものは加点しない。
3. 単項目だけでなく、利用可能項目に応じたAND/OR/スコア型の組み合わせをApr-Junだけで比較する。
4. 第一目的は100R前後を維持しながら4号艇頭率40%近辺。件数を大きく落とす条件は別Paretoとして分離する。
5. 各orig条件は必ず同一availability母集団のベース頭率との差を併記し、提供場バイアスを頭率改善として数えない。
6. Apr-Junだけで閾値・構成を決定。Jul-Augは固定候補のみ評価し、holdout結果で再選択しない。
7. 2026年9月結果は一切読まず `UNREAD`。production `HEAD4_V291_COMP7` は凍結。
8. 実装→Actions→結果回収→AFTERに commit SHA / Run / Job / Artifact / Apr-Jun件数・頭率 / Jul-Aug固定評価 / 結論 / 次の再開地点を記録する。

Status: `HEAD4_111R_ORIG_COMBO_STARTED`
