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
- Wave54 March = 210R / 71 boat3 heads = 33.80952381%

## Exhibition v5 corrected February freeze
初回Run `34992010310` は February heads=489 で canonical 478 と不一致のため INVALID。corrected v5 は canonical eligibility、同一common-ready母集団、GroupKFold OOF、venue-aware original exhibition availabilityを揃えた。

Actions:
- Run `34994783250`
- Job `104468173813`
- Artifact `10407605495`
- checkout research SHA `40950aef8759add2b9ddb27df992a32fcc0857af`

390 common-ready head races:
- A frozen baseline: 145/390 = 37.17948718%
- B + corrected exhibition/ST exhibition: 143/390 = 36.66666667%
- C + venue-aware original exhibition: 135/390 = 34.61538462%

正式freeze: **A wins**。展示/ST展示/オリジナル展示を学習特徴へ直接追加する案は **REJECT**。production unchanged / September outcomes UNREAD。

## post-ranking / ticket-rescue February research
展示は学習特徴へ入れず、frozen baseline A の順位を基準に、corrected exhibition と corrected ST exhibition だけで直前post-ranking補正。baseline top3 missの救済とbaseline hit破壊を同時評価。

実装:
- script `research/run_3head_exhibition_ticket_rescue.py`
- implementation commit `9dbda16dd22c1a45fe17ac9abd6d1fa249c8cde8`
- workflow commit `abd3278b9d57e9974e9c48fa032f2b7a17478769`

Actions:
- Run `34997702972` SUCCESS
- Job `104478008711` (`feb-ticket-rescue`)
- Artifact `10408382688` (`research-3head-ticket-rescue-feb`)

February 390R:
- baseline: 145 hits / 37.17948718%
- grid rows: 140
- best frozen candidate: `w_ex=0.08, w_st=0.08, threshold=0.0`
- corrected: 153 hits / 39.23076923%
- rescued_miss=14
- broken_hit=6
- net_rescue=+8
- positive_net_exists=true
- September outcomes read=false
- production changed=false

結論: direct-feature案はREJECT維持だが、post-ranking / ticket-rescue は February で明確な正のnet rescue。

## March one-shot audit AFTER — 2026-09-16
February freeze `w_ex=0.08, w_st=0.08, threshold=0.0` をMarchで一切再調整せずout-of-time監査。

実装/trigger commit:
- `8b34783355fa40c68242a7da637277e69ba79542`

Actions:
- Run `34998881760` SUCCESS
- Job `104482001438` (`march-one-shot`)
- Artifact `10409495083` (`research-3head-ticket-rescue-march`)

March 472 common-ready head races:
- baseline: 192/472 = 40.67796610%
- corrected: 201/472 = 42.58474576%
- rescued_miss=20
- broken_hit=11
- net_rescue=+9
- march_retuned=false
- exact_v288_exclusion_preserved=true
- September outcomes read=false
- production changed=false

結論: February freezeがMarch独立期間でも +9 net rescue / +1.9068pt を再現。February単月過適合だけでは説明しにくく、4〜8月の月別安定性監査へ進む。

## Apr-Aug stability audit BEFORE — 2026-09-16
これから行うこと:
- frozen `w_ex=0.08, w_st=0.08, threshold=0.0` を完全固定し、4〜8月で再探索・再調整しない。
- baseline A / exact v288 exclusion / canonical eligibility / 締切前特徴のみを維持。
- April, May, June, July, August を月別に baseline hits/capture、corrected hits/capture、rescued_miss、broken_hit、net_rescue で監査する。
- July/August は既知のとおり NON-PRISTINE と明記し、pristine validation と混同しない。
- 月別の符号安定性と合計net rescueを確認し、必要なら攻め方別のrescue分解へ進む。
- September 2026 outcomes は絶対に読まない。`UNREAD`維持。
- production v288は変更しない。

## 現在の結論 / 再開地点
- direct exhibition features: REJECT
- February post-ranking rescue: +8 net
- March frozen one-shot: +9 net
- frozen rescue parameters: `0.08 / 0.08 / threshold 0.0`
- production v288: unchanged
- September 2026 outcomes: **UNREAD**
- 次: **Apr-Aug frozen monthly stability audit を実装→fresh Actions→月別結果回収→本ファイルへAFTER追記**
