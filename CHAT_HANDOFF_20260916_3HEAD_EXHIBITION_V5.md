# boatrace-backtest 3号艇モデル 引き継ぎ — Exhibition v5 / ticket-rescue

Repo: `merry02180218-ai/boatrace-backtest`
Branch: `research/3head-player-attack-mode`
Date: 2026-09-16

## 最重要ルール
1. 最新GitHubと本引き継ぎを優先。
2. 作業前後に、予定・結果・commit SHA・Actions Run/Job/Artifact ID・結論・次の再開地点を記録。
3. September 2026 race outcomes は絶対に読まない。`UNREAD`維持。
4. production は v288 のまま変更しない。94R / 52 hits / ROI 172.560638%。
5. July/August 2026 は NON-PRISTINE。
6. 研究入力は締切前情報のみ。実際の決まり手を入力に使わない。
7. exact v288 94-race exclusion を維持。

## 固定ソース
- Source Run: `34754875342`
- Artifact: `10317157868` (`3head-wave21-allrace-source-build`)
- CSV: `analysis_v289_3head_wave21_allrace_feature_settled.csv`
- source max date <= 2026-08-31
- September outcomes: UNREAD
- February eligible = 3970R / boat3 heads = 478R
- March eligible = 4482R

## Exhibition v5 corrected February freeze
- Run `34994783250` / Job `104468173813` / Artifact `10407605495`
- A frozen baseline 145/390 = 37.17948718%
- B corrected exhibition/ST 143/390 = 36.66666667%
- C + venue-aware original exhibition 135/390 = 34.61538462%
- direct exhibition features: **REJECT**

## post-ranking / ticket-rescue February
- Run `34997702972` / Job `104478008711` / Artifact `10408382688`
- frozen candidate `w_ex=0.08, w_st=0.08, threshold=0.0`
- baseline 145/390 = 37.17948718%
- corrected 153/390 = 39.23076923%
- rescued=14 / broken=6 / net=+8

## March one-shot audit AFTER
- commit `8b34783355fa40c68242a7da637277e69ba79542`
- Run `34998881760` / Job `104482001438` / Artifact `10409495083`
- 472 common-ready head races
- baseline 192 = 40.67796610%
- corrected 201 = 42.58474576%
- rescued=20 / broken=11 / net=+9
- March retuned=false

## Apr-Aug frozen stability audit AFTER — 2026-09-16
Implementation commit `a5327d1fdddf230b7c401c735aeedaba0b77b6d5`
Workflow commit `872924264de70c60e115a8fb80c94001ad8ddf59`
Actions:
- Run `35059260596` SUCCESS
- Job `104675902983` (`apr-aug-stability`)
- Artifact `10432320401` (`research-3head-ticket-rescue-apr-aug`)
- Artifact ZIP SHA256 `de169cc031d855939b3b6149247861dec223d730719956e9eea7605453b4057d`

Frozen `0.08 / 0.08 / threshold 0.0`, no retuning:
- Apr: 414R, baseline 154 (37.1981%), corrected 152 (36.7150%), rescued 12, broken 14, net -2
- May: 563R, baseline 212 (37.6554%), corrected 217 (38.5435%), rescued 14, broken 9, net +5
- Jun: 544R, baseline 195 (35.8456%), corrected 200 (36.7647%), rescued 16, broken 11, net +5
- Jul NON-PRISTINE: 604R, baseline 234 (38.7417%), corrected 236 (39.0728%), rescued 16, broken 14, net +2
- Aug NON-PRISTINE: 591R, baseline 237 (40.1015%), corrected 234 (39.5939%), rescued 15, broken 18, net -3
- Total Apr-Aug: 2716R, baseline 1032 (37.9971%), corrected 1039 (38.2548%), rescued 73, broken 66, net +7

結論: February +8 / March +9 は再現したが、Apr-Augは合計+7に弱まり、Apr/Augは負。全レース一律補正をproduction採用する根拠としては不十分。展示補正が救済する条件と既存的中を壊す条件を分解する。

## Rescue vs Broken decomposition AFTER — 2026-09-16
- 初回 fresh Run `35062170154` / Job `104684604972` は `settle__actual_combo` 読み込み漏れで failure。
- 修正 commit `19321a9d8bb2bc60ab6768312f540152603003b4`。
- 成功 Run `35063772129` / Job `104689492719` / Artifact `10433766645`。
- Artifact SHA256 `4628666869220f29d76fe437434b94ae1e3ce2ccd06287a3364af98df067fca7`。
- Feb-Jun pooled: rescued 72 / broken 57 / net +15。
- discovery best: baseline gap<=0.04 & max_abs_adj>=0.02: 1537R, rescued 69, broken 56, net +13。
- rescued の entered exhibition/ST 平均 0.6599/0.6296、broken は 0.5871/0.5932。中途半端な展示優位で既存的中を壊す可能性がある。
- ただし pooled Feb-Jun は discovery であり、February baseline は同月fitのため、このgateをそのままfreeze/production採用しない。
- July/August NON-PRISTINE、September outcomes UNREAD、production unchanged。

## 展示補正OFF条件分析 BEFORE — 2026-09-16
これから行うこと:
- 主目的を「展示補正を使う条件」ではなく「展示補正を禁止する条件」の抽出へ変更。
- broken（展示補正で元の的中を壊したレース）を中心に rescued と比較する。
- 解析は締切前に観測できる特徴だけを使用する。
- baseline 3位-4位差、入替艇の展示/ST、entered-exited の展示/ST差、補正差、順位変動数を中心に比較する。
- Apr-Jun pristine を主な安定性確認期間とし、Feb-Marは発見/参考、Jul-Augは NON-PRISTINE 参考に分離する。
- 単純で実運用可能な「補正OFF」ルール候補を抽出し、月別 rescued/broken/net を必ず確認する。
- 同じ解析期間で選んだルールはproduction採用しない。候補固定後に独立監査へ進む。
- exact v288 exclusion維持 / September outcomes UNREAD / production unchanged。

## 現在の結論 / 再開地点
- direct exhibition features: REJECT
- 一律展示補正は安定性不足。
- 次: **broken中心の展示補正OFF条件を実装→fresh Actions→Apr-Jun月別安定性→OFF候補freeze→独立監査**
- production v288 unchanged
- September 2026 outcomes **UNREAD**
