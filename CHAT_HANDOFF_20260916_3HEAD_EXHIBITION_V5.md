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
- workflow commit/head SHA: `584633c9524c84a44446e08384acf9f6029d6907`
- Run: `35111654588` SUCCESS / Job: `104846612766` / Artifact: `10453170462`
- March rescued 20R / broken 11R。単純motor_advでは分離不能。
- `frozen_march_rule = null`; production unchanged; September UNREAD。

## このチャット内の運用変更
- `auto-live-3head-v288-production` の5分ごとの自動実行は停止済み。
- commit `a029b144a7a8ce52b0238b3fea6aecf1445cd3ef`
- `schedule` を削除し、`workflow_dispatch` の手動実行は残している。

## 2026-09-17 追加研究 BEFORE — close-margin 4点目
ユーザー指示: 4号艇モデル同様、僅差なら4点目も買う方式を3号艇で検証する。

これからやること:
1. v288/既存3点ランキングは変更しない。
2. 3位と4位のbase score差（margin）が小さいレースだけ4点目を追加する。
3. まず `margin-only` をMarchで候補探索し、Apr/May/Junへfreezeして独立検証する。
4. 次に `margin + exhibition/ST` 条件を比較し、4点目追加による追加的中と追加投資を分離する。
5. 指標は追加購入R、追加的中、incremental hit、可能なら払戻/ROI、月別安定性を出す。
6. July/AugustはNON-PRISTINE参考のみ。September outcomesは絶対に読まずUNREAD維持。
7. production v288は研究終了まで変更しない。

## 次の再開地点
**close-margin fourth-ticket audit 実装 → Actions発火 → March freeze / Apr-Jun OOS比較。**
