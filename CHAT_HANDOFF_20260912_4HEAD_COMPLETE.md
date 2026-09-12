# CHAT HANDOFF — 2026-09-12 — 4号艇モデル完全版

Updated: 2026-09-12 JST
Repository: `merry02180218-ai/boatrace-backtest`
Scope: **4号艇モデルのみ**

---

# 0. このファイルの目的

このファイルは、4号艇モデルだけを別チャットへ完全に引き継ぐための専用handoff。

以下を1本に集約する。

- 4号艇モデルを作り始めた背景
- 初期4カド/4号艇攻撃モデルから現在までの経緯
- 途中で何を試し、何が弱く、何を捨てたか
- v250以降の4号艇1着モデル再構築
- PRE / POST / ENV_ENTRY の考え方
- Sランク v268
- Aランク v273
- 相手選び v282/v283
- market/ticket overlay v291
- 現在の実運用ルール
- 2026-09-11 / 2026-09-12のPRE実運用結果
- まだ未完成の部分
- productionで絶対に破ってはいけないルール
- 次チャットで最初に何を確認し、どこから再開するか

**次チャットでは、このファイルを最初に読み、その後に必ず最新GitHubを確認すること。**
このファイルより新しい4号艇関連commit/fileがある場合は、最新GitHubを優先する。

このファイル作成直前に確認したmain HEAD:

`ad8612328a42ab56f6df5c28fb9e20fb559fde6e`

ただしmainは他モデル開発でも進むため、SHAを現行HEADとして固定解釈しない。

---

# 1. 現在の結論を先に

現行の4号艇prospective policyは:

**`HEAD4_V291_COMP7`**

ただしv291は頭判定そのものを作り直したversionではなく、

- 頭S判定 = v268
- A拡張 = v273（LIVE score mapping未完成）
- 相手 = independent v283
- ticket/market filter = v291

を組み合わせた現行branch。

現時点で正式に実運用可能な頭候補の中心は **S layer**。

## S layer

- `PRE >= 0.28` inclusive
- `POST >= 0.25` inclusive
- `ENV_ENTRY >= 0.224790` inclusive

Sはこの3条件をすべて満たす必要がある。

## A layer

S以外について:

- `PRE >= 0.18`
- `POST >= 0.18`
- frozen v271/v272 semantics の `A_SCORE >= 0.28`

ただしA_SCORE 0.28はmonthly walk-forward OOF scaleの値。
最終LIVEモデルのscore scale mappingがまだ完全freezeされていないため、**Aはまだ正式LIVE投入してはいけない**。

## v291 market rule

eligible S/A raceに対して:

- head = 4固定
- independent v283で相手順位
- Top4固定
- exactly 4 tickets
- 公式締切前3連単120通りsnapshot必須
- Top4合成オッズ `>= 7.0` でBET
- `< 7.0` はPASS
- 7.000000ちょうどはBET
- 1R exactly 10,000円
- inverse-odds Dutch
- 100円単位Hamilton / largest remainder rounding
- 外れは payout 0 / profit -10,000円

---

# 2. PRODUCTION絶対遵守ルール

以下は4号艇モデルで最優先。
ユーザーが明示的に方針変更しない限り緩めない。

## 2.1 2026-07 / 08 は NON-PRISTINE

7月・8月は既にモデル選定・特徴量探索等で見ている。

禁止:

- 性能評価のpristine/OOS扱い
- threshold調整
- rescue rule探索
- model selection
- September LIVE失敗後の救済材料

feature parity確認に使う場合でもoutcomeは見ない。

## 2.2 2026-09 は outcome-blind

9月の:

- 結果
- 払戻
- 的中/不的中
- race outcome

を使って:

- fitting
- calibration
- threshold selection
- rescue rule
- feature selection
- model choice

を行わない。

BET/PASS/NO_BETをfreezeする前に同日結果を取得しない。

## 2.3 v96はproduction route禁止

古い4号艇pair rankingで使われたv96は現在はhistory/benchmarkのみ。

productionでは:

- featureに入れない
- candidate restrictionに使わない
- rankingに使わない
- blendingしない
- tiebreakしない
- fallbackしない

## 2.4 締切後オッズ禁止

正式LIVEで使用可能なのは:

**公式3連単120通りの締切前snapshotのみ。**

以下は `ERROR_NO_BET`:

- 締切超過
- 120通り未満
- timestamp不明
- snapshot欠落
- source整合性不明

締切後オッズ、確定オッズ、後取得データで代替しない。

## 2.5 必須データ不足はfail closed

必要なもの:

- PRE
- POST
- ENV_ENTRY
- v283 SECOND p2
- v283 conditional THIRD
- official pre-deadline odds 120/120

不足・不整合・期限切れなら:

`ERROR_NO_BET`

推測値、dummy、旧モデル、後日補完でBETしない。

## 2.6 LIVEで再fit禁止

LIVE/current 7月・8月・9月rowを使って:

- imputer
- scaler
- model
- calibration
- threshold

を `.fit()` / 再fitしない。

v291 productionは原則として2026-06-30まででfreezeされたrecipe/artifactのinferenceのみ。

## 2.7 auditを結果より先に保存

結果取得前に最低限:

- race_code
- policy version
- layer
- PRE
- POST
- ENV_ENTRY
- v283 scores
- Top4
- odds snapshot
- odds hash
- source timestamps
- composite odds
- BET / PASS / NO_BET / ERROR_NO_BET
- ticket stakes

を永続化する。

---

# 3. 4号艇モデルの最初の思想

初期の4号艇モデルは、現在の「4号艇1着確率model」とは違い、主に:

**4コース / 4角から攻めるレースを見つける**

という発想だった。

狙いは:

- 4号艇まくり
- 4号艇まくり差し
- 4が3号艇を叩く展開

を全場横断で抽出すること。

初期から重視していたもの:

- 4号艇ST力
- 4コース攻撃力
- 4号艇の伸び/行き足
- 3号艇の壁弱さ
- 1/2/3号艇の内側抵抗力
- 4と3のST差
- モーター2連率だけでなく足質
- 展示ST
- 展示直線
- オリジナル展示
- 枠/コース補正

モーターも単純な数字ではなく:

- 伸び型
- 出足型
- 回り足型
- バランス型

に分ける思想だった。

4号艇まくりでは特に伸び・行き足を重視した。

### 古いv18 / v50系

2026-09-03頃にはv18 core 4-corner系があり、3-head/5-headと同時に研究していた。

古いhandoffに残っている参考値:

- v50系 2026/8/3〜9/2
- 4-head A+ 頭的中率 約26.9%
- ROI 約45.1%

これは現在のモデル性能ではない。
7/8月を含み、現在の評価ルールではNON-PRISTINE。

重要なのは、この初期系が十分強くなかったため、後に「4カド決まり手を当てる」よりも **4号艇が1着になること自体を直接学習する**方向へ再設計したこと。

Reference:

- commit `6bf483615d07ca41bdb04453725332caab172f5e` — v18 core 4-corner / 5-head backtest
- `CHAT_HANDOFF_4HEAD_5HEAD_20260910.md`

---

# 4. 大きな転換点 — v250 4号艇1着モデル再構築

## 4.1 なぜ作り直したか

旧4カド系は「4が攻める特定シナリオ」に寄りすぎていた。

v250では目的変数を:

**`y4head = 4号艇が1着か`**

に変更。

つまり:

- まくりだけ
- まくり差しだけ
- 特定決まり手だけ

に限定せず、4号艇1着そのものを学習するhead modelへ移行した。

この方針転換は現在のv268/v291まで続いている。

## 4.2 PRE / POSTを明確に分離

v250の重要設計:

- PRE = 当該レース展示前に確定している情報のみ
- POST = current-race展示を追加
- outcomeはfeature freeze後にjoin

これは現在のLIVE設計の基礎。

## 4.3 v250 PRE features

現行PREでも基本的にこの9featureを使う。

```text
legacy_score4
racer4
hist_st_edge_4v3
wall3_weak
inner12_resistance
motor4_2ren
motor4_hist
turnfoot4_prior
past_win4
```

意味:

### `legacy_score4`
旧4号艇攻撃score由来の集約signal。

### `racer4`
4号艇選手力。

### `hist_st_edge_4v3`
過去情報ベースの4号艇 vs 3号艇 ST優位。
4が攻めるには3との相対差が重要という初期思想を継承。

### `wall3_weak`
3号艇の壁弱さ。

### `inner12_resistance`
1/2号艇の内側抵抗力。
4だけ強くても内側が残れば4頭になりにくいので必要。

### `motor4_2ren`
4号艇motor 2連率系。

### `motor4_hist`
motor historical performance。

### `turnfoot4_prior`
当該レース以前の回り足/展示履歴系prior。

### `past_win4`
4号艇の過去勝利/コース実績系。

## 4.4 PRE model recipe

現行daily PRE scannerで使うrecipe:

```text
median imputer
-> StandardScaler
-> LogisticRegression(C=0.35, class_weight=None)
```

v250 research codeではmax_iter=1800の記録があるが、現行daily scanner側の実装はmax_iter=1000で運用されている。
実装を触る場合は必ず最新scannerを優先して確認する。

## 4.5 v250 POST features

PREに加えて:

```text
ex_st_rank4
ex_st_4
ex_st_edge_4v3
orig_straight4
orig_lap4
orig_turn4
tilt4
```

特に重要な思想:

- 生展示値だけでなくrank
- 4対3の相対ST edge
- straightだけでなくlap/turnも分離

Reference:

- `analyze_v250_4head_rebuild_baseline.py`
- commit `a7be4224480904904bdc68c8085e2e0c65a4bfa3`

---

# 5. v251 — 「頭が当たる」から「1R1万円の3連単収支」へ

v250でhead probabilityを作った後、v251で実際の3連単settlementへ橋渡しした。

重要な考え方:

- 1R stake = 10,000円
- losing race = payout 0 / profit -10,000
- ROI = total payout / total settled stake * 100
- Dutchはinverse odds
- 100円単位Hamilton rounding

ここから以後、4号艇モデルでは単なる頭率だけでなく:

- head rate
- trifecta hit
- composite odds
- ROI
- volume

を別々に見るようになった。

Reference:

- commit `305fbbdd20c08b811a8524527441a2507bb8e5d8` — v251 bridge

---

# 6. v252 — PRE候補 → POST最終gateを確立

v252で現在まで続く二段階構造を明示的に探索した。

設計:

1. PREで候補を絞る
2. 展示後POSTで最終gate
3. その後ticket / odds settlement

結果のrobustness shortlistでは、例えば:

- PRE 0.30 / POST 0.30 / Top2: 80R, head 46.25%, ROI 141.57%, Feb-Jun ROI 122.07%
- PRE 0.28 / POST 0.28 / Top2: 102R, head 44.12%, ROI 119.22%, Feb-Jun ROI 106.17%
- PRE 0.28 / POST 0.25 / Top2: 123R, head 43.90%, ROI 112.56%, Feb-Jun 96R, ROI 103.81%

この探索から `PRE>=0.28 / POST>=0.25` は、volumeを保ちつつFeb-Junでもプラス圏を維持する実用的なbase gateとして重要になった。

注意:

- これはretrospective/model-selection evidence
- Jul/AugはNON-PRISTINE
- grid最高ROIをそのまま採用しない

Reference:

- `summary_v252_4head_pre_post_gate_search.md`
- commit `c7c12b6b25f3bc63560bcde5340a4f1173564263`

---

# 7. v253〜v257 — 点数と合成オッズの探索

v252後はhead gateだけでなく、3連単の買い方を検証。

主な流れ:

## v253
variable TopNを比較。

## v254
race volume / monthly stabilityを重視して探索。

## v255
fixed TopNとの比較。

## v256
variable ticket countでcomposite odds 5〜10付近を探索。

## v257
composite target 10〜15へ範囲を拡張。

ここで重要だった学び:

**頭モデルとticket economicsを混ぜない。**

4号艇頭の質が同じでも:

- 相手順位
- TopN
- composite odds
- Dutch

でROIが大きく変わる。

そのため以後:

- head selection
- opponent selection
- market filter
- stake allocation

を別レイヤーとして扱う方向になった。

---

# 8. v258 — 3号艇型のdirect ordered-pairを4号艇へ移植したが不採用

v258では3-head v221思想を4号艇の相手選びへ構造移植。

- 20 ordered-pair direct logistic
- monthly prior-only
- 過去4号艇勝利のみでpair training
- player/frame traits
- prior corrected exhibition/original exhibition

しかし結果は全体として旧rankerより弱かった。

GATE PRE>=0.28 / POST>=0.25 のFeb-Jun primary evidence:

- old variable target10 ROI 101.34%
- v258 ROI 81.59%

TopN coverageも多くの領域で悪化。

したがって:

**3号艇で効いたpair architectureを、そのまま4号艇へコピーしても良くならない**

という重要なnegative result。

Reference:

- `summary_v258_4head_scenario_pair.md`
- commit `db8d880807f0712b499e8ae5149af24cd01192d2`

---

# 9. v259 — v96を残したconservative rerankerも大きな改善なし

v258が弱かったため、v259ではv96をdominantに残し、learned residualを少量blendする方式を試した。

GATE PRE>=0.28 / POST>=0.25:

- alpha=0.00: ROI 101.34%
- alpha=0.05: ROI 101.34%
- alpha=0.10: ROI 101.34%
- alpha>=0.15で悪化傾向

大きな改善はなかった。

この時点ではv96 lineageをまだ研究benchmarkとして使っていたが、後のv282/v283でindependent opponent branchが成立した後、**v291 productionではv96を完全禁止**した。

Reference:

- `summary_v259_4head_v96_reranker.md`
- commit `1df5aa14f2ff37ddb312c476ac8ec3aea8e8e12f`

---

# 10. v260 — PRE>=0.28 / POST>=0.25をbaseとしてticket economicsを整理

v260ではadaptive composite targetを探索。

特徴:

- v96 opponent rankingを当時は固定
- N=2..20
- exact 10,000円 Dutch/Hamilton
- PRE/POST gateを保ったままcomposite targetを探索

代表base:

`PRE>=0.28 / POST>=0.25`

123Rの例:

- avg N 約2.33
- avg composite 約8.045
- hit 13.82%
- ROI 114.74%
- Feb-Jun 96R
- Feb-Jun ROI 106.60%

この段階で:

**head gateとして0.28/0.25を残し、相手/market側を別改善する**

流れが強くなった。

Reference:

- `summary_v260_4head_adaptive_comp_target.md` 相当output
- commit `96d7a9defde1bb405d43f57b3fd51c53f2e36780`

---

# 11. v261 / v262 — 古いモデルとの比較と「頭率40% + volume」問題

v261ではold vs new monthly comparisonを実施。

v262ではPRE/POST thresholdだけで:

- 4号艇頭率40%以上
- 十分なvolume、目安200R

を両立できるか探索した。

ここから得た重要な方向性:

**PRE/POSTの2確率だけでは、volumeを維持しながら頭率をさらに上げるには限界がある。**

そこで次に:

- player/course
- prior foot
- opponent context
- environment / entry

などのfeature familyへ拡張した。

Reference:

- `analyze_v262_4head_headrate40_r200_search.py`
- commit `e5a8f7136785734b804a21a82486953a2180f1b7`

---

# 12. v263 — 3号艇で有効だったplayer/history思想を4号艇へ移植

v263では3-head由来の特徴量設計を4-headへ移植。

主なfamily:

```text
b4_pl_all_win
b4_pl_all_p2
b4_pl_frame_win
b4_pl_frame_p2
b4_pl_recent_p2
```

さらに3号艇側と比較:

```text
b3_pl_*
rel_pl_*
```

prior exhibition:

```text
b4_vh_p12_display
b4_vh_p12_overall
b4_vh_p12_turn
b4_vh_p12_straight
b4_vh_delta_display
b4_vh_delta_turn
b4_vh_delta_straight
```

重要なのは絶対値だけでなく:

**4号艇 − 相手艇のrelative feature**

を作ったこと。

この思想はv264/v273にもつながった。

Reference:

- `analyze_v263_4head_3head_features_player_history.py`
- commit `3ce9c75c09c86694e5e81e0e2fc2e7366adad37b`

---

# 13. v264 — exhaustive feature auditでENV_ENTRYが有力化

v264は4号艇feature研究の重要な節目。

Feb-Junをprimary、monthly walk-forward、Jul/Aug除外で広範囲にaudit。

feature family:

```text
BASE_P4
ST_3HEAD_ANALOG
PLAYER_COURSE
PRIOR_FOOT
OPP_CONTEXT
ENV_ENTRY
ALL_SAFE_LINEAR
ALL_SAFE_HGB
```

リークfieldは明示的に除外:

- winner
- second
- third
- payout
- actual
- hit
- ticket
- result
- kimarite
- target

等。

## relative feature

4 vs 1/2/3/5/6について:

- ST
- player/course
- prior foot

のrelative差を大量に構築。

## interactions

例:

```text
p4_joint = PRE * POST
attack4_st_edge3
attack4_corr_strength_edge3
attack4_stretch_x_st
post_x_entry_same
```

## 特に重要だったfamily

`ENV_ENTRY`

auditではAUC約 **0.6362**。

単純BASEより強い候補になった。

ENV_ENTRYが重視する本質:

- PRE/POST
- environment
- actual/preview entry consistency
- wind
- legacy exhibition score
- interaction

## 強かった個別feature例

v264 univariate上位には:

```text
rel_pl_all_win_4v1
rel_pl_all_p2_4v1
rel_pl_recent_p2_4v1
v91_ex
score_wind_v83
score_CORR20_v91
b1_pl_all_p2 (low direction)
score_RAW20_v91
score_BASE_v91
b1_pl_all_win (low direction)
preview_comp
opp_national_b1_v93 (low)
p4_joint
POST
PRE
opp_grade_b1_v93
b1_pl_frame_win
rel_pl_frame_win_4v1
```

ここで重要だった発見:

**4号艇自身の強さだけではなく、1号艇とのrelative player strengthや1号艇側の弱さが強いsignal。**

つまり4頭モデルは「4が強い」だけではなく:

- インが弱い
- 4が相対的に強い
- 進入/環境が4に合う

の組み合わせが重要。

Reference:

- `analyze_v264_4head_feature_exhaustive.py`
- `analysis_v264_4head_feature_univariate.csv`
- `summary_v264_4head_feature_exhaustive.md`
- commit `11c3d1bc7b373de185ebe5a9bd68ba6c90e248fa`
- result commit `ceb94024caacf60ea5df448a511a1527787d8bdb`

---

# 14. v265 / v266 / v267 — consensusからENV_ENTRY overlayへ

## v265

複数feature familyをcompact consensusとして組み合わせるaudit。

例:

```text
ENV_ENTRY
OPP_CONTEXT
ALL_SAFE_HGB
```

## v266

v265系scoreを実際のnew ROIへ橋渡し。

## v267

既存v260 base selectorをfreezeしたまま、consensus overlayだけ追加して比較。

base:

- PRE >= 0.28
- POST >= 0.25

overlay候補:

- ENV_ENTRY
- OPP_CONTEXT
- ALL_SAFE_HGB combination

ここでJul/Augは明示的に除外。

最終的にS layerへ入ったのが:

**ENV_ENTRY top 80% overlay**

で、threshold:

`ENV_ENTRY >= 0.224790`

v267 development evidenceとして残された値:

- settled 53R
- 4号艇頭率 35.85%
- trifecta hit 15.09%
- avg N 2.28
- avg composite 7.715
- return 606,860円
- profit +76,860円
- ROI 114.50%
- monthly minimum ROI 100.70%

月別:

- 2026-04: 17R / ROI 134.17%
- 2026-05: 22R / ROI 100.70%
- 2026-06: 14R / ROI 112.30%

これはdevelopment evidenceでありformal OOSではない。

Reference:

- `analyze_v267_4head_v260_consensus_overlay.py`
- commit `e87e1a6207734a1c2498bbee5c9c58dfae914280`

---

# 15. v268 — Sランクfreeze

2026-09-10、September outcome tuning前にS候補をfreeze。

## HEAD4_V268

```text
PRE >= 0.28
POST >= 0.25
ENV_ENTRY >= 0.224790
```

これが現在のv291 S layerそのもの。

### 当時のticket rule

v268 freeze時点ではまだ:

- v96 lineage opponent rank
- N=2..20
- composite target 10.5に最も近いN
- 1R10,000円 Dutch

だった。

**このticket部分は後にv291で廃止/上書き。**

head S selectionだけが現在まで継承されている。

Reference:

- `HEAD4_V268_FROZEN_20260910.md`
- commit `ac76999aacbf01f60bffd9fbc6f63b497971af18`

---

# 16. v271 / v272 / v273 — Aランクでrace countを増やす

Sだけではrace countが少ないため、Sを壊さず独立A layerを研究。

重要:

- S first
- SならSのみ
- AはS外のみ
- 同一raceでS+A二重購入禁止

## v273 frozen A rule

S外で:

```text
PRE >= 0.18
POST >= 0.18
A_SCORE >= 0.28
```

A_SCOREの17feature:

```text
v91_ex
score_CORR20_v91
score_wind_v83
score_RAW20_v91
score_BASE_v91
preview_comp
rel_pl_all_win_4v1
rel_pl_all_p2_4v1
rel_pl_recent_p2_4v1
opp_grade_b1_v93
opp_score_b1_v93
opp_national_b1_v93
b1_pl_all_win
b1_pl_all_p2
b1_pl_frame_win
rel_pl_recent_p2_4v3
b4_pl_recent_p2
```

model family:

- median imputation
- StandardScaler
- LogisticRegression C=0.18

## Development evidence Apr-Jun

A cut 0.28:

- S 53R
- A added 47R
- S+A 100R
- A head rate 44.68%
- A trifecta hit 17.02%
- A ROI 150.16%
- S+A head rate 40.00%
- S+A trifecta hit 16.00%
- S+A ROI 131.26%
- S+A monthly floor 104.00%

月別S+A:

- Apr 31R / ROI 104.00%
- May 34R / ROI 170.66%
- Jun 35R / ROI 117.13%

ただしA-onlyは全holdout月で安定黒字ではない。
AはSと組み合わせたportfolio expansionとしてfreezeされた。

## 現在の重要な未完成点

`A_SCORE >= 0.28` はOOF scale。
最終LIVE fitのraw probabilityにそのまま0.28を当ててはいけない。

必要:

1. 2026-06-30まででfinal LIVE model fit
2. Jul/Aug除外
3. outcome-blind score-scale mapping
4. coefficients/scaler/imputer/feature order freeze
5. mapped LIVE threshold freeze

これが済むまでAはformal prospectiveに入れない。

Reference:

- `HEAD4_V273_ARANK_FROZEN_20260910.md`
- commit `6af4938940f4fcb985ff92354f0cf1fc943006b8`

---

# 17. 相手モデルの独立化 — v282 / v283

4号艇head selectionと「2着3着相手」を切り離す方針へ移行。

理由:

- v258のdirect pair移植が弱かった
- v96依存から脱却したかった
- 2着と3着を役割として別に学習する方が構造的に自然

現行v283 frozen semantics:

## SECOND

**independent PLAYER_START listwise**

- L2 = 10

## THIRD

**conditional `P(third=t | candidate second=s, pre-result context)`**

- family = `COND_BASE`
- L2 = 0.3

## pair ordering

`TOP2XTOP2`

- alpha2 = 0.60
- head fixed = 4

productionではv96を一切使わない。

Reference:

- `analyze_v283_4head_conditional_pair_order.py` 相当
- commits:
  - `446ea037795dc15cfd3d0c3d3ff67d3af70a987d`
  - `c875529baa99b490071c367a2d4c1fc9fe79353a`
  - `a3d37acdf9f90cb00fc423eb2932901f41db4b0a`

---

# 18. v289 / v290 → v291 — Top4 + composite odds 7.0へ

v268/v273ではvariable N + target composite 10.5だった。

その後v283 independent opponent orderingを前提にmarket overlayを再検証。

v289/v290 diagnosticsを経て、v291をfreeze。

## Development evidence Apr-Jun archived-odds proxy

v283 Top4 fixed:

### Unfiltered
- 100R
- ROI 126.12%

### composite >= 6.0
- 40R
- head rate 50.0%
- hit rate 25.0%
- ROI 233.33%
- max DD 77,280円
- min-month ROI 110.97%

### composite >= 7.0
- 28R
- head rate 64.3%
- hit rate 32.1%
- ROI 310.98%
- max DD 60,000円
- max losing streak 6
- min-month ROI 166.46%

### composite >= 8.0
- 21R
- head rate 71.4%
- hit rate 38.1%
- ROI 380.01%
- max DD 70,000円
- max losing streak 7
- min-month ROI 174.80%

8.0は同sample上のROIは高かったが件数が減る。
**7.0をrisk / coverage balanceとしてfreeze。**

LOMO diagnostic:

- hold Apr: 6.0 selected on other two months -> ROI 339.68%
- hold May: 6.0 -> ROI 202.45%
- hold Jun: 7.0 -> ROI 166.46%
- combined LOMO ROI 259.26%

注意:

これらはhistorical archived odds proxy。
formal LIVE OOS利益ではない。

Reference:

- `HEAD4_V291_COMP7_FROZEN_20260911.md`
- commit `e34bd8c9d01414c3981afb6e38375ad7fec2e928`

---

# 19. 現行v291の完全な判定フロー

Sについて現在目指している正式chain:

```text
全場PRE scan
  ↓
PRE >= 0.28 ?
  ↓ yes
展示/進入取得
  ↓
POST >= 0.25 ?
  ↓ yes
ENV_ENTRY >= 0.224790 ?
  ↓ yes
v283 SECOND inference
  ↓
v283 conditional THIRD inference
  ↓
TOP2XTOP2 / alpha2=.60
  ↓
Top4 exactly
  ↓
公式3連単120/120締切前snapshot freeze
  ↓
Top4 composite odds = 1 / Σ(1/odds_i)
  ↓
comp >= 7.0 ?
  ├─ no -> PASS / stake 0
  └─ yes -> BET
             ↓
       exact 10,000円 Dutch
             ↓
       audit persist BEFORE result
```

---

# 20. PRE daily automation — 完成済み

2026-09-11にgeneralized daily PRE automationを実装。

主要files:

- `fetch_4head_v291_pre_inputs_live.py`
- `scan_4head_v291_pre_live.py`
- `.github/workflows/live-4head-v291-pre-daily.yml`

date-specific reproducibility:

- `scan_20260911_4head_v291_pre.py`
- `fetch_kyoteibiyori_v291_pre_inputs.py`
- `.github/workflows/scan-20260911-4head-v291-pre.yml`

## daily PREのルール

- target date = JST
- active venues auto-discover
- 全R保持
- tolerant Waku10 handling
- target-day結果なし
- target-day展示なし
- target-daySTなし
- target-day original exhibitionなし
- labelsは2026-06-30まで
- Jul/Aug/Sep labelsはfit/calibration/thresholdに使わない
- threshold exactly `PRE >= 0.28`
- CSV / Markdown / audit artifact出力

Important commits:

- `75c482e9eb63fae009281827a79c584c31fa8e3c` — result-blind PRE scan
- `cf250593cdec15c592a52ca4f1403b0d1ba44d52` — tolerant input fetcher
- `68cc32c29a81a5a7c4fd5c91f8ac81e70c7c9aab` — workflow update
- `3f3f27147be69588025dcf6783b8021d2f14e7bf` — generic PRE fetcher
- `f8faf9ce8f81d7b7d34491ba32d51daa0ae99abc` — generic PRE scanner
- `2f618b60cdeee1ff965a0b542c117c57a226347f` — daily workflow

---

# 21. 2026-09-11 PRE実運用結果

正式result-blind scan:

- 12 venues
- 144 / 144 races
- `PRE >= 0.28`: **0 races**

Top PRE:

1. 住之江7R: 0.1365504771
2. JCD05 5R: 約0.050062
3. JCD13 6R: 約0.044671
4. JCD02 5R: 約0.033657
5. JCD06 8R: 約0.033594

結論:

- S PRE candidateなし
- POST/ENV_ENTRYへ進めない
- low distributionを理由にthresholdを下げない

Verified runs:

- `34557396065`
- `34558379641`

---

# 22. 2026-09-12 PRE実運用結果 — 最新

2026-09-12 02:37 JST頃、daily v291 PREを正式起動。

trigger commit:

`4b129534faddc66c636296958631a2444ca8273d`

GitHub Actions:

- run `34628722346`
- conclusion `success`
- artifact `live-4head-v291-pre-2`
- artifact id `10275587624`

input fetch:

- active venues: 13
- 156 / 156 PRE rows

JCD:

```text
02,05,06,08,09,10,12,16,17,18,20,21,24
```

PRE result:

- current race rows: 156
- `PRE >= 0.28`: **0**

したがって2026-09-12もformal S PRE candidateなし。

確認した上位PRE:

1. 多摩川2R: 0.101762
2. 戸田9R: 0.078473
3. 浜名湖6R: 0.077651
4. 住之江2R: 0.057761
5. 常滑5R: 0.056211

全て0.28から大きく下。
threshold rescue禁止。

---

# 23. market/ticket LIVE runner — 実装済み部分

file:

`run_20260911_4head_v291_live.py`

commit:

`c2a63a1998d6cac4d137b87bfb15e2de964927af`

このrunnerは既にfreeze済みの:

- PRE
- POST
- ENV_ENTRY
- p2
- conditional THIRD scores

を入力として受け取れば:

- S gate
- exact v283 Top4
- official odds fetch
- 120/120 validation
- deadline check
- composite calculation
- comp >= 7 BET
- comp < 7 PASS
- exact 10k Dutch
- JSONL audit

まで行える。

### verifier

`verify_20260911_4head_v291_live.py`

commit:

`d5f8e54ca3610aae832358056ee37c484428f702`

verifies:

- threshold inclusive
- exactly 4 unique tickets
- 全ticket head=4
- comp exactly 7.0 is BET
- below 7 is PASS
- exact 10,000
- 100円unit
- v96 prohibited
- S fail NO_BET
- expired deadline hard fail

workflow:

`.github/workflows/validate-4head-v291-live.yml`

commit:

`b09aaa64f793b4ac9cd4c1a9fadaef134b0b33b4`

successful validation run:

`34555835579`

---

# 24. 現在の最大の未完成点

**PRE後の完全自動化はまだ完成していない。**

現在:

- PRE daily scan = 完成
- final market/ticket runner = 部分完成

間の:

```text
PRE candidate
-> raw exhibition/entry
-> exact frozen POST inference
-> exact frozen ENV_ENTRY inference
-> exact frozen v283 SECOND
-> exact frozen conditional THIRD
```

のproduction-safe接続が未完成。

`run_20260911_4head_v291_pipeline.py` はfail-closed orchestratorとして存在するが、downstream frozen artifactsが安全に接続されない場合はBLOCK/ERRORにする思想。

重要commit:

- `34d9c25dcf103f19d109da8ea2473b8368efc43d` — fail-closed PRE-to-live orchestrator
- `b49f2474049cd24914eda67740cf810fdb8e7a2f` — pipeline after PRE
- `db0c9f90bc0eb431e6f952bbdaafdc1e59487e56` — production invariants embedded in pipeline audit

---

# 25. PRE feature parityの既知の監査課題

2026-09-11 current PRE scanで:

`turnfoot4_prior = 0.5`

が144Rすべて同値だったことが確認されている。

可能性:

- prior exhibition cache
- player name matching
- source state
- current input reconstruction

のどこかでhistorical model時とLIVE時のsemantic parityが崩れている可能性。

これはまだ「必ずバグ」と断定してはいけないが、production-safe宣言前に監査必須。

安全な監査方法:

- Jul 1等の既存artifactをfeature parity比較にだけ使う
- outcomeは見ない
- historical frozen feature vs current builderを比較
- performance tuningには使わない

---

# 26. 過去に試して弱かった/現在使わないもの

次チャットで古いものを誤って復活させないこと。

## 26.1 古い4カド決まり手専用モデル

現在のhead modelの代替にはしない。

理由:

- 4号艇1着全体を目的変数にしたv250以降へ移行済み

## 26.2 v258 direct 20-pair model

そのままproduction opponent modelにしない。

理由:

- Feb-Junで旧rankerより悪化した。

## 26.3 v259 v96 residual blend

productionに戻さない。

理由:

- 大きな改善なし
- 現行v291ではv96明示禁止

## 26.4 v268 variable N / composite target 10.5

v291 branchではticket constructionとしてsuperseded。

現在は:

- v283 order
- Top4 fixed
- comp >=7

## 26.5 threshold救済

9/11, 9/12にPRE candidateが0でも:

- 0.28を下げない
- top1だけ救済しない
- 当日distribution percentileで候補を作らない

---

# 27. ROIとcomposite oddsの定義

ユーザーが確定したROI定義:

```text
1 race stake = 10,000 JPY
ROI = total payout / total settled stake * 100
```

例:

- 外れ = payout 0
- profit = -10,000

**composite oddsはROIではない。**

Top4 composite:

```text
COMPOSITE = 1 / Σ(1 / odds_i)
```

これはmarket/ticket filter。

---

# 28. データ再現性に関する注意

過去の他モデル監査で、BoatraceCSV `main` のhistorical preview/result/payoutが後日更新されることが確認されている。

4号艇でも同様に注意。

原則:

- frozen artifactをgolden baselineとして保存
- historical raw source revisionとmodel changeを分けて監査
- LIVEは最新source
- historical再生成で数字が変わっても、直ちにmodel regressionと決めつけない

特にformal evidenceでは:

- artifact hash
- source timestamp
- commit SHA

を残す。

---

# 29. 現在の重要ファイル一覧

## Frozen policy

- `HEAD4_V268_FROZEN_20260910.md`
- `HEAD4_V273_ARANK_FROZEN_20260910.md`
- `HEAD4_V291_COMP7_FROZEN_20260911.md`

## Handoffs

- `CHAT_HANDOFF_4HEAD_5HEAD_20260910.md` — 古い4/5共通
- `CHAT_HANDOFF_20260911_4HEAD_V291_AUTOLIVE.md` — v291 auto-live直前handoff
- **`CHAT_HANDOFF_20260912_4HEAD_COMPLETE.md` — このファイル、4号艇専用complete history**

## PRE

- `fetch_4head_v291_pre_inputs_live.py`
- `scan_4head_v291_pre_live.py`
- `.github/workflows/live-4head-v291-pre-daily.yml`

## LIVE

- `run_20260911_4head_v291_live.py`
- `verify_20260911_4head_v291_live.py`
- `run_20260911_4head_v291_pipeline.py`
- `.github/workflows/validate-4head-v291-live.yml`

## Historical research

- `analyze_v250_4head_rebuild_baseline.py`
- v251 new-ROI bridge
- v252 PRE/POST gate search
- v253 variable TopN
- v254 volume stability
- v255 fixed TopN
- v256/v257 composite target
- v258 scenario pair
- v259 v96 reranker
- v260 adaptive composite
- v262 head-rate / volume search
- v263 player/history
- v264 exhaustive feature audit
- v265 consensus
- v266 ROI bridge
- v267 v260 consensus overlay
- v282/v283 independent opponent work
- v289/v290 market diagnostics

---

# 30. 重要commit timeline

古い順に主要なものだけ:

```text
6bf4836  v18 core 4-corner / 5-head

a7be422  v250 4-head rebuild baseline
305fbbd  v251 trifecta new-ROI bridge
4385646  v252 PRE/POST gate search
c7c12b6  v252 results
bd9f185  v253 variable TopN
f8d6c1c  v254 volume stability
8a5fe65  v255 fixed TopN
fdde877  v256 variable composite 5-10
2895364  v257 variable composite 10-15
53e938c  v258 scenario-aware pair
b580f50  v259 v96 reranker
bd49f41  v260 adaptive comp target
f978367  v261 old-vs-new monthly comparison
e5a8f71  v262 40% head-rate / 200R search
3ce9c75  v263 player/history
11c3d1b  v264 exhaustive feature audit
ceb9402  v264 results
ef30da8  v265 consensus
90700dc  v266 ROI bridge
e87e1a6  v267 v260 + consensus overlay
ac76999  v268 S candidate freeze
6af4938  v273 A-rank freeze
446ea03  v283 conditional pair audit
a3d37ac  v283 results

e34bd8c  v291 COMP7 freeze
280881a  machine-readable v291 policy
34c4768  executable v291 policy
c2a63a1  v291 live market runner
d5f8e54  v291 invariant verifier
75c482e  result-blind v291 PRE scan
cf25059  tolerant PRE input fetcher
3f3f271  generic PRE input fetcher
f8faf9c  generic PRE scanner
2f618b6  daily PRE workflow
34d9c25  fail-closed PRE-to-live orchestrator
a98e362  v291 auto-live handoff
ffd7bd3  production invariants explicit
db0c9f9  production invariants in pipeline
4b12953  trigger 2026-09-12 formal PRE scan
```

---

# 31. 次チャットで最初に確認する順番

4号艇モデルの続きをやる場合:

1. このファイルを読む。
2. 最新main HEADを確認。
3. `HEAD4_V291_COMP7_FROZEN_20260911.md` を確認。
4. `CHAT_HANDOFF_20260911_4HEAD_V291_AUTOLIVE.md` の最新versionを確認。
5. `scan_4head_v291_pre_live.py` のlatestを確認。
6. `run_20260911_4head_v291_live.py` を確認。
7. `run_20260911_4head_v291_pipeline.py` を確認。
8. v268 POST/ENV_ENTRY exact frozen inference lineageを実コードで特定。
9. v283 SECOND/THIRD exact frozen implementation/artifactを特定。
10. LIVEで`.fit()`していないことを確認。
11. PRE feature parity、特に`turnfoot4_prior`を監査。
12. PRE candidateが出た日のみpost-exhibition chainを起動。

---

# 32. 次に実装すべきもの

最優先はモデルをさらにいじることではなく、現在freeze済みv291を完全にLIVE化すること。

## Task A — frozen downstream inference確定

- exact v268 POST
- exact ENV_ENTRY
- exact v283 SECOND
- exact conditional THIRD

を2026-06-30までのfrozen artifact/recipeからinference-onlyで動かす。

## Task B — post-exhibition runner

PRE>=0.28のみ対象。

- exhibition
- ST
- original exhibition
- actual entry
- wind/environment

を取得し、timestamp/hash保存。

## Task C — complete market path

- Top4
- official 120/120 odds
- before-deadline timestamp
- composite >=7
- exact Dutch
- audit

## Task D — CI parity

historical frozen referenceとLIVE inferenceが同じfeature semanticsになることをtest。

## Task E — A layer

S productionが安定した後に:

- v273 final LIVE A_SCORE
- score-scale mapping
- artifact freeze

を別versionとして完成させる。

---

# 33. やってはいけない再開方法

禁止:

- 「今日候補0だから0.28を下げる」
- September結果を見てfeatureを足す
- v96 fallbackを復活
- odds取得が遅れたので締切後を使う
- missing POSTを0.5等で埋めてBET
- v283が作れないので旧pair orderを使う
- Jul/Aug ROIを根拠に新thresholdを選ぶ
- PREとPOSTを同一時点featureとして混ぜる
- historical結果を先にjoinしてからfeature生成
- current-day全レースのpercentileでthresholdを作る

---

# 34. モデル設計上の最重要学習事項

4号艇研究全体から得た本質:

## 34.1 「4が強い」だけでは不足

必要なのは相対構造。

- 4 vs 3 ST
- 4 vs 1 player/course
- 内側抵抗
- 3壁
- opponent weakness

## 34.2 PREとPOSTを分ける

PREは候補抽出。
POSTは展示後confirm。

## 34.3 environment / entryが重要

v264/v267でENV_ENTRYが有効。

## 34.4 head modelと相手モデルを分ける

4頭判定と2/3着順位を一体化しない。

## 34.5 ticket economicsをhead probabilityと分ける

同じhead signalでもmarketによって価値が違う。
v291ではTop4 composite >=7をmarket gateにした。

## 34.6 高ROI cellをそのまま採用しない

件数・monthly floor・LOMO・prospective disciplineを優先。

## 34.7 zero candidate dayは正常

9/11と9/12が0候補でも、それはモデルのfailureではない。
thresholdを守ること自体がprospective validation。

---

# 35. 現在のステータスまとめ

```text
HEAD selection S: FROZEN
PRE daily scan: OPERATIONAL
POST inference full-auto: NOT YET COMPLETE
ENV_ENTRY full-auto: NOT YET COMPLETE
A_SCORE LIVE mapping: NOT YET COMPLETE
v283 semantics: FROZEN
v283 full LIVE inference connection: NOT YET COMPLETE
Top4 / comp7 rule: FROZEN
Official odds validation: implemented in market runner
Dutch: implemented
Audit: market runner implemented / full upstream audit still integration task
Formal profitable OOS claim: NOT YET
```

最も重要:

**v291は有望なretrospective development policyとしてfreeze済みだが、正式なLIVE OOS利益が証明済みという意味ではない。**

---

# 36. 新チャット開始文

以下をそのまま使える。

`boatrace-backtest の CHAT_HANDOFF_20260912_4HEAD_COMPLETE.md と最新GitHubを読んで、4号艇モデルだけの続きから進めて。古い記憶より最新GitHubを優先。現行はHEAD4_V291_COMP7で、SはPRE>=0.28 / POST>=0.25 / ENV_ENTRY>=0.224790、相手はindependent v283、Top4固定、締切前公式120オッズの合成>=7、1R1万円Dutch。7月8月NON-PRISTINE、9月outcome-blind、v96禁止、LIVE再fit禁止、締切後オッズ禁止を厳守。まず最新の4号艇関連コード/commitを確認し、PRE後のPOST/ENV_ENTRY/v283完全自動化とfeature parity監査の現在地を特定して。`

---

# END

このファイルは4号艇専用。
1号艇・3号艇・5号艇の現行ロジックを4号艇productionへ混ぜない。
他モデルから特徴量アイデアを研究する場合も、新versionで検証し、v291 historyを書き換えない。
