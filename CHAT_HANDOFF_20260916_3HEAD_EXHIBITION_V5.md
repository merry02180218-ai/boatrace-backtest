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

結論: direct-feature案はREJECT維持だが、post-ranking / ticket-rescue は February で明確な正のnet rescue。Marchへ進める価値あり。

## March one-shot audit BEFORE — 2026-09-16
これから行うこと:
- Februaryで選んだ `w_ex=0.08, w_st=0.08, threshold=0.0` を**完全freeze**し、Marchで再探索しない。
- Februaryでbaseline Aをfitし、March common-ready boat3-head racesへout-of-time適用する。March自身でモデル/重み/thresholdをfit・tuneしない。
- Marchで baseline hits/capture と frozen rescue後 hits/capture、rescued_miss、broken_hit、net_rescue を一発診断する。
- exact v288 exclusion、canonical eligibility、締切前特徴のみを維持。
- March結果はこの監査目的でのみ読む。September 2026 outcomes は引き続き絶対に読まず `UNREAD`。
- production v288は変更しない。
- Marchで正のnet rescueが再現した場合だけ、次に4〜8月の月別安定性/攻め方別rescue監査へ進む。再現しなければFebruary過適合としてREJECT候補。

## 現在の結論 / 再開地点
- direct exhibition features: REJECT
- February post-ranking rescue: +8 net rescue
- frozen rescue parameters: `0.08 / 0.08 / threshold 0.0`
- production v288: unchanged
- September 2026 outcomes: **UNREAD**
- 次: **March one-shot out-of-time ticket-rescue audit を実装→Actions→結果回収→本ファイルへAFTER追記**
