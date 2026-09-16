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
- March/Feb discoveryの単純OFF条件はApr-Junで強く再現せず。例 `.55/.20/0` は Apr-Jun broken blocked 5 / rescues lost 5 / net 0。
- validation側で +2 のルールは存在するが、validationを見て選ぶためfreeze不可。
- production unchanged / September UNREAD。

## モーター差入りv288保護監査 AFTER
- BEFORE commit `eda0d57aa06f28896e0ecd50435828e14093f837`
- implementation commit `6e737a9fe39cf292c2450c2549b83baed8408a28`
- workflow commit `603bb5c85374b9f2097b8b0423801a55584798fb`
- Run `35081477233` SUCCESS / Job `104746260511`
- Artifact `10441015163` (`research-3head-motor-protection`)
- Artifact SHA256 `26305639a9b1926538d00e808e55665794b007c8ee2e92e563fcdbf18b6ee572`
- motor definition: lane=mean(motor2rate,motor3rate)/100, pair=.55*second+.45*third, motor_adv=entered-exited。
- March-only discoveryで選ばれた rule: base_gap>=0, ex_adv<=.10, st_adv<=.10, motor_adv<=-.05。
- しかし March off_races=0。Apr=0, May=0, Jun=1で、broken_blocked/rescues_lost/netは全て0。`apr_jun_all_positive=false`。
- 結論: モーター差を使う発想の否定ではなく、`motor_adv<=-.05` 等の事前固定gridが実分布に対して厳しすぎ、対象が消えた。閾値決め打ちは中止。
- production unchanged / September UNREAD。

## モーター差分布研究 BEFORE — 2026-09-16
これから行うこと:
- broken / rescued の実際の `motor_adv` 分布を先に測る。先に閾値を決めない。
- Marchを主発見期間とし、中央値・四分位・符号比率と、ex_adv / st_adv / base_gapとの関係を出す。
- その分布から単純な候補閾値を作る。Apr/May/Junの結果を使って候補選択しない。
- Marchで候補をfreezeした後だけ、Apr/May/Junを月別検証する。
- 目的は「v288が強い＋入替側モーター優位が弱い時に展示補正を止める」保護gate。
- July/AugustはNON-PRISTINE参考のみ。
- exact v288 exclusion維持 / September outcomes UNREAD / production unchanged。

## 現在の結論 / 再開地点
- direct exhibition features: REJECT。
- 一律展示補正は安定性不足。
- モーター差固定gridは対象消失で失敗。
- 次: **motor_adv実分布→March-only候補freeze→Apr/May/Jun月別独立検証**。
- production v288 unchanged。
- September 2026 outcomes **UNREAD**。
