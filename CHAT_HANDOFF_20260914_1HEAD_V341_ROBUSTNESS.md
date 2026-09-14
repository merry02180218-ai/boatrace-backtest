# 1号艇モデル 引き継ぎ — v341 v340購入後段ルール堅牢性監査

作成日: 2026-09-14
repo: merry02180218-ai/boatrace-backtest

## 作業開始記録
- 前回正式引き継ぎ: `CHAT_HANDOFF_20260914_1HEAD_V340_ODDS_DUTCH.md`
- 正式production本体は変更しない: `1HEAD_PRODUCTION_20260914_HEAD078`
  - HEAD/PRE cutoff = `0.78`
  - exhibition = v332 `ATTACK_ENV_SOFT`, env_w=0.1, q=0.65
  - SECOND = v317 `OUTER_L2_1`
  - THIRD = v318 `DROPSTART_T0.1`
  - ticket ranking = v320 `HYBRID alpha=.70`
- production identity: PASS 276R / head 241 / exact3(top3) 119 / SHA256 `89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73`
- 2026年7月・8月はNON-PRISTINE。
- 2026年9月outcomesはUNREADを厳守し、今回も一切読まない。

## v339完走確認
- Run `34787687379`: SUCCESS
- final audit Job `103807404470`: SUCCESS
- final Artifact `10327069135`: `v339-1head-cutoff-local-stability`
- v339結論は0.78維持。0.7775/0.7750で頭率が明確に悪化し、0.7850はvolume/exact3が悪化。

## v340確定結果
- Run `34796402852`: SUCCESS
- final Artifact `10329904344`: `v340-1head-adaptive-odds-dutch-sharded`
- official closing trifecta odds coverage 276/276, missing 0
- baseline top3 all: stake 2,760,000円 / return 2,567,630円 / profit -192,370円 / ROI 93.0301%
- adaptive: skip 243R / keep3 26R / expand 7R / bought 33R / hits 11R
- adaptive: stake 330,000円 / return 381,260円 / profit +51,260円 / ROI 115.5333%
- `SEPTEMBER_OUTCOMES_READ=false`

## 今回やること — v341
v340の購入後段ルールをproduction昇格させる前に、固定済みrace-level結果だけで堅牢性と寄与を分解する。

1. Feb-Junのみ（pristine扱い）のadaptive ROI / 損益 / hit率を再集計し、Jul/Aug NON-PRISTINEを除いてもプラスか確認する。
2. skip / keep3 / expand別にR数・頭的中・top3 exact3・adaptive hit・stake・return・profit・ROIを分解する。
3. expand 7Rについて、同じ7Rをtop3のまま1万円Dutch購入した場合と実際のexpanded購入を直接比較し、点数追加の純増分を測る。
4. skip群について、top3を買っていた場合の仮想損益を集計し、「見送り」がどれだけROI改善へ寄与したかを定量化する。
5. 正式production本体およびv340購入後段候補は、この監査だけで黙って変更しない。
6. 9月outcomesはUNREADを維持する。

## v341 完了記録

### 実装 / CI
- pre-work handoff commit: `17c90f6d0ef0cfea299d91063d6aaed9dce97e18`
- audit script commit: `005f9c3770cf5830a1d93b9049875bd43399f878`
- workflow commit: `89a84d9b2b3290239f705142c75707fca12b3010`
- script: `run_v341_1head_v340_robustness_audit.py`
- workflow: `.github/workflows/v341-1head-v340-robustness-audit.yml`
- workflowはtop-level `name:` を置かない構成。

### GitHub Actions
- Run: `34804055509`
- conclusion: SUCCESS
- audit Job: `103852292649`
- Job conclusion: SUCCESS
- Artifact: `10332666746` — `v341-1head-v340-robustness-audit`
- artifact digest: `sha256:0c8f9a2b4fcbcef89d171658e858572e717697fde54895251d55ddc17b541493`

### Production identity guard
- R = 276
- head = 241
- exact3(top3) = 119
- expected identity SHA256 = `89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73`
- September row assertion = PASS
- `SEPTEMBER_OUTCOMES_READ=false`

### Feb-Jun pristine-only
母集団220R。Jul/Aug NON-PRISTINEを完全除外して集計。

adaptive:
- bought = 26R
- hits = 9
- hit rate = 34.6154%
- stake = 260,000円
- return = 314,060円
- profit = +54,060円
- ROI = 120.7923%

baseline top3 all:
- R = 220
- hits = 94
- hit rate = 42.7273%
- stake = 2,200,000円
- return = 2,045,970円
- profit = -154,030円
- ROI = 92.9986%

pristine actions:
- skip = 194R
- keep3 = 20R
- expand = 6R

=> Jul/Augを除いてもadaptiveはROI 120.79%、+54,060円でプラスを維持。NON-PRISTINE月だけに依存した改善ではない。

### action別寄与（全276R）

#### skip 243R
- head hits = 210 / 243 = 86.4198%
- top3 exact3 = 108 / 243 = 44.4444%
- 仮にtop3を全購入した場合:
  - stake = 2,430,000円
  - return = 2,186,370円
  - profit = -243,630円
  - ROI = 89.9741%
- 実際は見送りなので損益0円。
- 見送りによる損益改善 = **+243,630円**

#### keep3 26R
- head hits = 25 / 26 = 96.1538%
- top3 exact3 / adaptive hit = 9 / 26 = 34.6154%
- stake = 260,000円
- return = 294,520円
- profit = +34,520円
- ROI = 113.2769%
- top3のままなのでbaselineとの差分0円。

#### expand 7R
- head hits = 6 / 7 = 85.7143%
- top3 exact3 = 2 / 7 = 28.5714%
- adaptive hit = 2 / 7 = 28.5714%
- expanded stake = 70,000円
- expanded return = 86,740円
- expanded profit = +16,740円
- expanded ROI = 123.9143%

同じ7Rをtop3のまま購入した場合:
- hits = 2
- stake = 70,000円
- return = 86,740円
- profit = +16,740円
- ROI = 123.9143%

expand純増分:
- hit delta = 0
- return delta = 0円
- profit delta = **0円**

=> 今回の固定276Rでは、追加した4〜6点目は1件も追加的中を生んでいない。expandそのものはROI改善へ寄与していない。

### v340改善の分解
v340 baseline top3 all profit = -192,370円。
adaptive profit = +51,260円。
差 = +243,630円。

この+243,630円は、skip243Rで回避した仮想損失 -243,630円と完全一致する。
keep3/expandでの買い方変更による純増分は0円。

つまり現時点のデータでは、v340の利益改善要因は100%「top3合成オッズ3.0未満を買わない」フィルタで説明できる。`4.0以上なら点数追加` は少なくともこの276Rでは付加価値を示していない。

## 結論
1. 正式production本体 `HEAD .78 / v332 q=.65 / v317 / v318 / v320` は維持。
2. 購入後段については、v340全体をそのままproduction化するより、まず **combined odds <3.0 skip** を単独ルールとして検証・候補化する価値が高い。
3. Feb-Jun pristine-onlyでもROI 120.79%のため、skip効果はJul/Aug NON-PRISTINE依存ではない。
4. expand 7Rは純増分0円なので、現状では不要候補。追加点を入れる根拠は弱い。
5. 次は、正式モデルを固定したまま「skip閾値」の近傍感度（例 2.7 / 2.8 / 2.9 / 3.0 / 3.1 / 3.2 / 3.3）をpristine中心に比較し、3.0が局所的な偶然でないか確認する。
6. その際もJul/AugはNON-PRISTINEとして補助扱い、2026年9月outcomesはUNREADを維持する。

## 次の再開地点
- v342: combined-odds skip threshold local stability audit。
- HEAD/展示/相手/買い目順位は一切再学習せず、v340の公式締切オッズ付き固定276R artifactだけを使う。
- 主評価はFeb-Jun pristine-onlyのROI / profit / bought_R / hit率 / 月別安定性。
- 3.0周辺の閾値感度を比較して、単独skipルールのproduction候補可否を判断する。
- `SEPTEMBER_OUTCOMES_READ=false` を厳守。
