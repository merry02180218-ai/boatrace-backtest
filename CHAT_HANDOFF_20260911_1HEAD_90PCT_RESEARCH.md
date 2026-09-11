# CHAT HANDOFF — 2026-09-11 — 1HEAD 90% RESEARCH

## 目的
別チャットで「1号艇が1着になる確率を極端に高く絞る新しい1号艇頭モデル」を研究するための引き継ぎ。

最終目標は、単にモデル出力 `p1 >= 0.90` を作ることではなく、**未知データで選ばれたレースの実測1号艇頭率が90%以上になる領域を、リーク無し・十分な件数で見つけること**。

raw probability 0.90 と実測90%は同義ではない。必ず calibration / reliability と実測 head rate を確認すること。

この研究は現行1号艇productionを直ちに置き換えるものではない。まず別versionで研究し、walk-forward / untouched prospective validationを通す。

---

## 最優先ルール
- repo: `merry02180218-ai/boatrace-backtest`
- 次チャット開始時は**必ず最新GitHubを先に読む**。このhandoffより新しいcommit/fileがある場合は最新GitHubを優先する。
- 2026-07/08 は NON-PRISTINE / model-selection済み期間。新モデルの性能選定・閾値調整・救済条件探索に使わない。
- 2026-09 は prospective / outcome-blind を維持する。9月結果を見て新モデルのfeature・threshold・calibrationを調整しない。
- current-race result / payout / post-deadline information は予測特徴量に絶対使用しない。
- 特徴量は予測時点でfreezeし、その後に結果をjoinする。
- PREとPOSTを混ぜない。PREは当該レース展示前、POSTは展示/進入確定後として明確に分離する。
- 小標本で90%になっただけのルールは採用しない。R、heads、head rate、月別floor、95% Wilson CIを必ず報告する。

---

# 1. 現行1号艇モデルの出発点
2026-09-08時点の現行LIVE lineageには `predict_v194_1head_live_manual.py` があり、v109系head model + v162相手選びを使用している。

現行head側の主な数値特徴量:

```text
one_grade
one_wr
one_local
one_motor
one_waku_wr
one_nst_strength
one_waku_sr_strength
one_past_win
one_meet_st_strength
one_ex
one_st
one_lap
one_turn
one_straight
one_orig_avg
one_direct
one_score
threat2
threat3
threat4
threat5
threat6
threat23_max
threat_all_max
margin2
margin3
margin23
margin_all
st_margin2
st_margin3
st_margin23
ex_margin23
turn_margin23
straight_margin23
+ venue one-hot
```

現行v194は StandardScaler + LogisticRegression(C=0.5) で、S-only cutは0.72。相手はv162 lambda=1.0 Top7。

**新しい90%頭率研究では、既存0.72を0.90へ上げるだけでは不十分。** raw pが校正されている保証がないため、モデル・特徴量・calibration・selected head rateを一から監査する。

Reference:
- commit `11837ef9e03cabb0b54e84f2515125f303c1f204`
- `predict_v194_1head_live_manual.py`

---

# 2. 3号艇モデルから引き継ぐべき成功要素

## 2.1 「単体能力」より相対差
3-head v288/v243系で最終選別に効いたのは、3号艇の絶対値だけではなく**隣接艇・内外艇との相対差**だった。

代表的な有効feature / gate:

```text
f__c_b3_minus_b4_waku_st
f__c_b3_minus_b4_st
f__c_b3_meetst
f__c_wall12_weak
f__c_b3_minus_b2_motor
f__c_b3_inside_nst
f__c_b3_minus_b5_st
f__c_attack3_stretch
```

v288で採用された構造:
- S core: 3 vs 4 の枠/ST差 + meet ST
- A rescue: 3 vs 4 ST優位 + 1/2号艇の壁弱さ
- B rescue: 3 vs 2 motor優位 + inside NST
- precedence: `S -> else A -> else B`

1号艇へ移植する時の考え方:
- `boat1 absolute strength` だけでなく `boat1 - boat2`, `boat1 - boat3`, `boat1 - max(2..6)` を作る。
- 特に2/3号艇を主要attack threatとして扱う。
- ST、motor、選手力、当地/コース実績、展示、直線、回り足、一周を**相対margin**にする。
- 「1号艇が強い」だけでなく「攻め手が弱い」「壁が成立する」を別featureとして持つ。

### 1号艇向け候補
```text
p1_vs2_st
p1_vs3_st
p1_vs23_st_min
p1_vs_all_st_min
p1_vs2_motor
p1_vs3_motor
p1_vs_all_motor_min
p1_vs2_player
p1_vs3_player
p1_vs_all_player_min
p1_vs23_straight
p1_vs23_turn
p1_vs23_lap
threat23_max
threat_all_max
wall23_strength / attack23_weakness
```

現在の1headには既に `threat*` と `margin*` があるため、まず既存定義を確認し、重複を増やすのではなく**3-headで効いた相対構造が完全に表現されているか**監査する。

Reference:
- `verify_v288_3head_100r_replay_v2.py`
- `run_20260911_3head_v288_live.py`
- commit `c86a4c12f13d141347edfd4f3e722c37b59d8349`
- commit `b3fe5f4a7e5953049e72800dcd1b153a4810cace`

## 2.2 PREで広く候補化、POSTで強く絞る
3-head productionで重要だったのは、レース前情報と展示後情報を同じ時点のfeatureとして扱わないこと。

PRE:
- 選手/コース能力
- 過去ST
- 過去motor/足
- 過去成績
- 当日展示より前に分かる情報

POST:
- current exhibition time
- current start exhibition
- original exhibition（straight / turn / lap）
- actual entry/course
- tilt 等

1-head 90%モデルでは、まず:
1. `P1_PRE` — 展示なしで高信頼候補を絞る
2. `P1_POST` — 展示・進入・気象を入れて最終90%ゾーンを絞る

という二段階を優先する。

## 2.3 current test set内 percentile を使わない
3-head v288 productionで、同月/当日candidate内 percentile はstrict LIVEではリーク的運用になるため廃止した。

正しい方法:
- training universeだけでscore distributionを作る
- threshold / quantileをtraining側でfreeze
- current raceはその固定閾値へ当てるだけ

1-headでも同じ。

**禁止:** 今日の全レースを見て「上位10%だからS」にすること。

**推奨:** training OOF scoreで閾値を決め、現在レースを固定閾値評価する。

Reference:
- commit `9b6f2990eba7440867019db1274a4581d2787d15`
- `scan_20260911_3head_v288_pre.py`

## 2.4 単一巨大モデルより「core + 独立gate」の比較
v288では1本の複雑モデルだけでなく、意味の違う条件をS/A/Bとして分けることで運用しやすくなった。

ただし1-head 90%研究では「rescueで件数を増やす」よりprecision優先。
最初は:
- CORE ultra-high-confidence
- optional CONFIRM gates

として、**90%を下回るrescueは作らない**。

---

# 3. 4号艇モデルから引き継ぐべき成功要素

## 3.1 4-head v250 PRE feature design
4号艇頭そのものを目的変数にして再構築したv250のPRE:

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

1号艇へ一般化すると:
- 自艇能力
- historical ST edge
- 最大attack艇の弱さ/強さ
- inner/outer resistance構造
- motor current rate + historical motor trend
- prior turn-foot
- past course win

を別featureとして持つ。

Reference:
- `analyze_v250_4head_rebuild_baseline.py`
- commit `a7be4224480904904bdc68c8085e2e0c65a4bfa3`

## 3.2 4-head POST feature design
v250 POSTで追加:

```text
ex_st_rank4
ex_st_4
ex_st_edge_4v3
orig_straight4
orig_lap4
orig_turn4
tilt4
```

1号艇向け:
```text
ex_st_rank1
ex_st_1
ex_st_edge_1v2
ex_st_edge_1v3
ex_st_edge_1v23_best_attacker
orig_straight1
orig_lap1
orig_turn1
relative_orig_*_1v23
actual_course1
entry_shift_threat
wind/angle interaction
```

特に**絶対展示値だけではなく相対rank/edge**を必ず比較する。

## 3.3 4-head exhaustive auditで強かったfeature family
v264ではFeb-Jun、monthly walk-forward、Jul/Aug除外で広範なfeature auditを実施。

有力だった考え方:
- `PLAYER_COURSE`
- `OPP_CONTEXT`
- `ENV_ENTRY`
- 3-head analog relative ST
- prior-foot relations

特に `ENV_ENTRY` family はAUC約0.6362で、単純BASEより強かった。

強い個別feature上位には:
```text
rel_pl_all_win_4v1
rel_pl_all_p2_4v1
rel_pl_recent_p2_4v1
score_wind_v83
preview_comp
p4_joint
POST
PRE
b1 opponent/player weakness features
post_x_entry_same
```

が入った。

ここから1-headへ持ち込むべき本質:
1. **相手とのplayer/course実績差**
2. **進入が想定通りか**
3. **気象×場×脚/スタートのinteraction**
4. **PREとPOSTのconsensus/joint signal**
5. **最強attack opponentのcontext**

Reference:
- `analyze_v264_4head_feature_exhaustive.py`
- `summary_v264_4head_feature_exhaustive.md`
- commit `11c3d1bc7b373de185ebe5a9bd68ba6c90e248fa`
- result commit `ceb94024caacf60ea5df448a511a1527787d8bdb`

## 3.4 player/course history + prior exhibition
v263では3-head由来の発想を4-headへ移植し、以下を比較した:

```text
b4_pl_all_win / all_p2 / frame_win / frame_p2 / recent_p2
b3 equivalents
relative player differences
prior exhibition p12_display / overall / turn / straight
prior exhibition deltas
```

1-headでも以下を艇1単体だけでなく2/3号艇との差にする:
```text
all_win
all_p2
frame/course win
frame/course p2
recent p2
prior exhibition display/overall/turn/straight
```

Reference:
- `analyze_v263_4head_3head_features_player_history.py`
- commit `3ce9c75c09c86694e5e81e0e2fc2e7366adad37b`

## 3.5 HEAD modelと相手モデルを分離する
4-head v283では、頭判定と2/3着予測を分離した。

Frozen concept:
- SECOND: independent listwise model
- THIRD: `P(third=t | candidate second=s, pre-result context)`
- pair orderingはSECONDとconditional THIRDから作る

1-head 90%研究でも、**最初の研究目的は1号艇頭率だけ**にする。
2/3着精度やROIをhead modelの学習目的へ混ぜない。

1-head頭率90%ゾーンが確認できてから、相手モデルを別途最適化する。

Reference:
- v283 commits `446ea037795dc15cfd3d0c3d3ff67d3af70a987d`, `c875529baa99b490071c367a2d4c1fc9fe79353a`, `a3d37acdf9f90cb00fc423eb2932901f41db4b0a`

---

# 4. 1HEAD 90%で優先して作るfeature groups

次チャットでは最初から全featureを1モデルに投入せず、family別に比較する。

### A. BASE_1
既存v109/v194の艇1能力中心。

### B. RELATIVE_ATTACK
艇1と2/3/4/5/6、特に2/3との相対差。
- ST
- corrected ST
- motor
- player/course win/p2
- exhibition
- straight
- turn
- lap

### C. WALL_THREAT
- threat2 / threat3 / threat23_max / threat_all_max
- 2号艇が壁になるか
- 2が遅れて3/4が攻めやすいか
- 2/3 simultaneous attack risk
- まくり/差しattack profile

### D. PRIOR_FORM
- recent player/course form
- prior same-series exhibition
- prior straight/turn/lap
- prior start trend
- motor historical trend

### E. ENV_ENTRY
- actual entry course / entry change
- entry_confirmed_same
- wind speed / direction / relative angle
- venue interaction
- tilt
- water/weather if strictly available before decision

### F. POST_EXHIBITION
- current exhibition rank + absolute
- current ST rank + edge
- original exhibition straight / turn / lap
- relative 1v2 / 1v3 / 1v23 / 1vAll margins

### G. CONSENSUS
Separate models:
- PRE model
- POST model
- ENV_ENTRY model

Then test consensus such as:
```text
high PRE AND high POST
high PRE AND high POST AND high ENV_ENTRY
min(calibrated_PRE, calibrated_POST)
weighted logit consensus
```

Do not choose weights from Jul/Aug/Sep outcomes.

---

# 5. 推奨研究手順

## Step 1 — labelを明確化
Primary target:
```text
y1head = 1 if actual winner == 1 else 0
```

`逃げ`決まり手限定にはしない。まず「1号艇1着」そのものを予測する。

別診断として:
- 1コース進入維持
- イン逃げ
- 1号艇敗戦パターン

を分析する。

## Step 2 — 時系列freeze
各日/各月で:
1. その時点で利用可能なfeatureをfreeze
2. model scoreを出す
3. その後でresultをjoin

monthly expanding walk-forwardを第一候補にする。

## Step 3 — BASE比較
最低でも:
- current v109/v194 LogisticRegression
- LR with new relative families
- HistGradientBoosting challenger

を同じsplitで比較。

複雑モデルが勝っても、小標本thresholdだけなら採用しない。

## Step 4 — calibrationを必須化
「90%」を名乗るため、classification rankingだけでなくcalibrationを見る。

必須:
- Brier score
- log loss
- reliability bins
- predicted 0.80-0.85 / 0.85-0.90 / 0.90-0.95 / >=0.95 の実測head rate

Platt / isotonicを試すなら**OOF training predictionsだけ**でfitする。test monthへfitしない。

## Step 5 — threshold diagnostics
thresholdごとに:
```text
R
heads
head_rate
Wilson 95% CI
monthly R
monthly head_rate
worst-month head_rate
```

を出す。

raw p thresholdだけでなく、training-OOF calibration後probability / training-score quantileも比較する。

## Step 6 — 90%領域を探す
優先順位:
1. 90%以上で十分なRがあること
2. 月別に崩れていないこと
3. calibrationが破綻していないこと
4. PREだけでも候補化可能か
5. POSTでさらにprecisionを上げられるか

「5R中5勝」「10R中9勝」のような小標本は候補発見に留め、完成扱いしない。

## Step 7 — untouched prospective
Jul/Aug/Sepを見てルールを救済しない。
選んだruleをfreezeし、その後の新規LIVEレースで検証する。

---

# 6. 特に監査すべき敗戦要因
90%を目指すなら、勝ちを学ぶだけでなく**1号艇が飛ぶ条件を除外するモデル/gate**が重要。

優先監査:
- 1号艇ST遅れ
- 2号艇ST先行 + 差し足
- 3号艇強攻撃
- 2号艇壁崩壊
- 1 vs 2/3 motor負け
- 1 vs 2/3 straight負け
- 1号艇turn/lap弱い
- 進入変化
- 1号艇コース別/当地/近況弱化
- 強風/向い風/追い風などvenue-specific environment
- F/L持ち、平均ST/スタート勘など事前に合法な情報

**negative-risk model**（boat1 loses）を別に作り、`P1_head high AND P1_loss_risk low` のintersectionも比較する価値がある。

---

# 7. やってはいけないこと
- v109のcutを0.90へ上げただけで「90%モデル」と呼ぶ。
- 予測月の全レースを使ったpercentile ranking。
- Jul/Augの結果を見ながらruleを追加。
- Sepの外れを見てthresholdを救済。
- 結果join後にfeature生成。
- odds / payout / actual ticket resultをhead probability featureへ混ぜる。
- current exhibitionをPREへ混ぜる。
- 90%を達成した小標本だけを報告する。
- 3-head/4-headの閾値数値を1-headへそのままコピーする。

---

# 8. 重要な3-head / 4-head source files
次チャットでは最低限これらの**最新GitHub版**を確認すること。

3-head:
```text
CHAT_HANDOFF_20260911_3HEAD_V288_PRODUCTION.md
run_20260911_3head_v288_live.py
scan_20260911_3head_v288_pre.py
verify_v288_3head_100r_replay_v2.py
verify_v288_operational_pre_replay.py
docs/FEATURES_THAT_WORKED_3HEAD_V288_20260911.md
analyze_v243_3head_expand_feature_audit.py
```

4-head:
```text
CHAT_HANDOFF_20260911_4HEAD_V291_AUTOLIVE.md
HEAD4_V268_FROZEN_20260910.md
analyze_v250_4head_rebuild_baseline.py
analyze_v263_4head_3head_features_player_history.py
analyze_v264_4head_feature_exhaustive.py
summary_v264_4head_feature_exhaustive.md
analyze_v267_4head_v260_consensus_overlay.py
run_20260911_4head_v291_live.py
```

Current 1-head baseline:
```text
predict_v194_1head_live_manual.py
analyze_v108_1head_feasibility.py
analyze_v162_1head_pair_direct.py
analysis_v108_1head_feasibility.csv
```

---

# 9. 次チャットで最初にやること
1. このhandoffと最新GitHubを読む。
2. 現行1-head feature定義を完全に列挙し、3/4-head成功featureとの重複/不足をmatrix化する。
3. 2026-06-30までを主なmodel-selection領域として、1-head direct target datasetをリーク無しで再構築する。
4. PRE / POST / ENV_ENTRYを分離する。
5. BASE / RELATIVE_ATTACK / WALL_THREAT / PRIOR_FORM / ENV_ENTRY / POST_EXHIBITION / CONSENSUSをmonthly walk-forward比較する。
6. calibrationを入れ、selected real head rate 90%以上の領域を探す。
7. Rと月別floorを優先し、小標本90%は採用しない。
8. Jul/Aug NON-PRISTINE、Sep outcome-blindを維持する。
9. 最良候補をfreezeして、その後だけprospective LIVE評価する。

---

# Recommended next-chat opening prompt

`boatrace-backtest の CHAT_HANDOFF_20260911_1HEAD_90PCT_RESEARCH.md と最新GitHubを読んで、1号艇の実測頭率90%以上を狙う新モデル研究を開始して。現行v194/v109の特徴量を基準に、3号艇v288/v243と4号艇v250/v264/v267で有効だった相対ST・相対motor・壁/attack threat・player/course history・prior exhibition・PRE/POST分離・ENV_ENTRY・consensusを1号艇向けに移植して比較する。raw p>=0.90ではなくunknown dataでselected head rate>=90%が目標。monthly expanding walk-forward、training-only threshold/calibration、結果はfeature freeze後joinを厳守。7月8月はNON-PRISTINE、9月はoutcome-blind。まず既存1-head featureとの重複/不足を監査してから、BASE→feature family比較→calibration→90%領域探索まで実行して。`
