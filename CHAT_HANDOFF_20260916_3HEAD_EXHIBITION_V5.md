# boatrace-backtest 3号艇モデル 引き継ぎ — Exhibition v5 / ticket-rescue

Repo: `merry02180218-ai/boatrace-backtest`
Branch: `research/3head-player-attack-mode`
Date: 2026-09-16〜17

## 最重要ルール
1. 最新GitHubと本引き継ぎを優先。
2. 作業前後に、予定・結果・commit SHA・Actions Run/Job/Artifact ID・結論・次の再開地点を記録。
3. September 2026 race outcomes は絶対に読まない。`UNREAD`維持。
4. production は v288 のまま変更しない。94R / 52 hits / ROI 172.560638%。
5. July/August 2026 は NON-PRISTINE。
6. 研究入力は締切前情報のみ。実際の決まり手を入力に使わない。
7. exact v288 94-race exclusion を維持。
8. ユーザーへの説明は日本語を基本とし、英語の内部変数名だけで説明を終えない。

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

## Apr-Aug frozen stability audit AFTER
- Run `35059260596` / Job `104675902983` / Artifact `10432320401`
- Apr -2 / May +5 / Jun +5 / Jul NON-PRISTINE +2 / Aug NON-PRISTINE -3; total +7。
- 結論: 一律展示補正はproduction根拠として不足。

## Rescue vs Broken decomposition AFTER
- 修正 commit `19321a9d8bb2bc60ab6768312f540152603003b4`
- Run `35063772129` / Job `104689492719` / Artifact `10433766645`
- Feb-Jun pooled: rescued 72 / broken 57 / net +15。
- rescued entered exhibition/ST mean 0.6599/0.6296、broken 0.5871/0.5932。
- gapだけでは分離不足。swap-specific evidenceを見る。

## 展示補正OFF分析 AFTER
- script `research/run_3head_exhibition_off_gate.py`
- script commit `ecffb441008fe944faf0c0c083f9ba998567015a`
- workflow commit `49163da4726d206686cefa730f63e723dfef9d19`
- Run `35065912592` SUCCESS / Job `104696025937`
- Artifact `10434665644` / SHA256 `4e3df5c1613ebf932d5cd61e4d318e80674b385743acd53e54251d1c4717724d`
- 単純OFF条件はApr-Junで強く再現せず。production unchanged / September UNREAD。

## モーター差入りv288保護監査 AFTER
- BEFORE commit `eda0d57aa06f28896e0ecd50435828e14093f837`
- implementation commit `6e737a9fe39cf292c2450c2549b83baed8408a28`
- workflow commit `603bb5c85374b9f2097b8b0423801a55584798fb`
- Run `35081477233` SUCCESS / Job `104746260511`
- Artifact `10441015163`
- SHA256 `26305639a9b1926538d00e808e55665794b007c8ee2e92e563fcdbf18b6ee572`
- March ruleは対象0Rとなり、閾値決め打ち方式を中止。

## モーター差分布研究 AFTER — 2026-09-17
### 実装・Actions
- BEFORE/handoff update commit: `76e51b4...`
- distribution script commit: `70cff7d...`
- workflow commit/head SHA: `584633c9524c84a44446e08384acf9f6029d6907`
- script: `research/run_3head_motor_distribution.py`
- Run: `35111654588` — **SUCCESS**
- Job: `104846612766` (`motor-distribution`) — **SUCCESS**
- Artifact: `10453170462` (`research-3head-motor-distribution`)
- Artifact ZIP SHA256: `f6951901bfb3a89fe2bc326bf955ac58b5e8cf1be1badc2fa3ac6677dedea753`
- exact v288 exclusion preserved=true
- candidate_selected_using_apr_jun=false
- September outcomes read=false
- production changed=false

### Marchでの実分布
展示補正で外れ→的中になった `rescued` は20R（motor有効19R）。
- motor_adv平均 +0.0137316（約+1.37ポイント）
- 中央値 +0.002775（約+0.28ポイント）
- 25%点 -0.01755 / 75%点 +0.054225
- motor_adv<=0 は42.1%

展示補正で的中→外れになった `broken` は11R。
- motor_adv平均 +0.0140909（約+1.41ポイント）
- 中央値 +0.009725（約+0.97ポイント）
- 25%点 -0.00855 / 75%点 +0.031225
- motor_adv<=0 は27.3%

### March-only候補探索結果
Marchのrescued/broken実分布から候補閾値を生成し、Apr-Jun結果は選択に使わなかった。
最上位候補でも:
- base_gap_min=0
- ex_adv_max=.15
- st_adv_max=.30
- motor_adv_max=.0082
- 対象7R
- 防げたbroken=1R
- 失ったrescued=1R
- net=0

正のnetとなるMarchルールが無かったため:
- `frozen_march_rule = null`
- Apr/May/Junへのfreeze検証は実施対象なし
- `apr_jun_all_positive=false`

### 結論
- 単純な「入替艇と外れ艇のモーター2連率/3連率の合成差」では、rescuedとbrokenを分離できなかった。
- rescued平均 +1.37pt、broken平均 +1.41pt とほぼ同等で、モーター差単独の保護gateは不採用。
- これはモーター情報自体を全否定するものではない。現行の単純合成差が識別材料にならなかった、という結論。
- production v288は変更しない。
- September 2026 outcomesは **UNREAD維持**。

## このチャット内の運用変更
- `auto-live-3head-v288-production` の5分ごとの自動実行は停止済み。
- commit `a029b144a7a8ce52b0238b3fea6aecf1445cd3ef`
- `schedule` を削除し、`workflow_dispatch` の手動実行は残している。
- これは3号艇研究本体とは別のLIVE運用変更。

## 次チャットの再開地点
次は **展示タイム差 + 展示ST差 + 元のv288順位差 + 実際に入れ替わった組み合わせ** を組み合わせて、展示補正をON/OFFすべき条件を調べる。

優先候補:
1. `ex_adv`（入替側の展示優位差）
2. `st_adv`（入替側の展示ST優位差）
3. `base_gap`（v288元順位3位と4位の確率差）
4. `changed_pairs` / 入替艇・外れ艇の組み合わせ特性
5. 必要ならmotor2/motor3を別々に補助情報として再確認するが、単純合成motor_adv gateには戻らない。

研究設計は引き続き、Marchのみで発見・freeze → Apr/May/Junを月別独立検証。July/AugustはNON-PRISTINE参考のみ。September outcomesは絶対に読まずUNREADを維持する。

## 現在の最終状態
- production: **v288 unchanged**
- direct exhibition training features: **REJECT**
- uniform post-ranking exhibition correction: 月別安定性不足
- simple motor protection gate: **REJECT / no freeze**
- 次: **展示差・ST差・v288順位差・入替組み合わせによるON/OFF条件研究**
- September 2026 outcomes: **UNREAD**
