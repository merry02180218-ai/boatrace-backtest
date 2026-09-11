# CHAT HANDOFF — 1号艇 v298 redesign / next chat

作成日時: 2026-09-11 JST
Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール

- 必ず**最新GitHubを最優先**する。古い記憶・過去チャットより最新commit / 最新コード / 最新結果を優先。
- 予想・判定・モデル改良の前に、実際のGitHubコードとデータを確認する。
- **2026年7月・8月は NON-PRISTINE**。モデル選択・調整・最終評価に使わない。
- **2026年9月は prospective / outcome-blind**。9月結果を見て閾値・特徴量・ロジックを調整しない。
- PRE と POST は分離。結果を結合する前に特徴量構築を凍結する。
- final-selected の settled race は全件3連単分母。1号艇が負けたレースも3連単ハズレとして扱う。
- 取消・不成立・返還など truly unsettled / void のみ分母除外可。
- target/result leakage の疑いがある特徴は fail closed。
- 既存production lineageを、development結果だけで勝手に置換しない。

## このブランチの目的

1. 1号艇頭 selector の実現頭率 **90%以上**。
2. その最終選択レースだけに対し、**3連単5点以内**を出す。
3. 最終的に全選択レース分母で exact trifecta hit **80%以上**を狙う。
4. 実運用可能な prospective rule にする。

注意: 頭率90%ちょうどなら、1号艇が勝った条件下で相手5点coverageは最低88.89%必要。v297時点では全く届いていない。

---

# v297 確定事項

## 実装

- `analyze_v297_1head_guard_trifecta5_research.py`
- `.github/workflows/research-20260911-v297-1head-trifecta5.yml`
- wrapper: `run_v297_1head_guard_trifecta5_research.py`
- summary: `summary_v297_1head_guard_trifecta5.md`

## v297設計

- v296 clean PRE family `CLEAN_STATIC6_PLAYER` を起点。
- 1号艇頭: HGB core selector + independent logistic-regression safety/loss guard。
- 3連単: multiclass HGBで20通りの `1-a-b` を順位付けし top5。
- confidence gateとして `top5_mass` を使用。
- expanding walk-forward by month。
- Feb-Junのみdevelopment。

### 主な探索

- HGB quantiles: `.95, .975, .985, .99, .995`
- LR guard quantiles: `.90, .95, .975`
- top5_mass confidence cuts: `0, .45, .50, .55, .60, .65, .70, .75`
- 1〜5点を全評価。
- stable zone: all 5 months / pooled R>=100 / min month R>=10。

## settlement監査の確定仕様

公式settled universeは:

1. `data/results/realtime/YYYY/MM/DD.csv`
2. public `BoatraceCSV/boatracecsv.github.io` payout source
3. 両方に存在しないscheduled rowは **UNSETTLED/VOID** とみなし除外

archive結果で official absent race を復活させない。

最終監査commit: `427aa882c81225310eda2c754ad864b5ea86be0f`

v297最終 workflow run:
- run ID: `34585574541`
- success
- results commit: `343ab191107718f6c5bc36478ce627bd906ef65d`

settlement:
- scheduled: 35,921
- official settled: 35,483 = 98.78%
- unsettled/void: 438
- winner completeness within official: 99.986%
- realtime exact: 35,279
- payout fallback: 183
- archive fallback: 0
- exact completeness among winner-known settled: 99.95%

## v297結果

**stable zoneで head >=90% は NONE**。

Best joint zone:
- rule: `HGB_q0.975_AND_LR_q0.950`
- confidence: `.60`
- R=136
- head = **89.71%**
- 5pt exact = **53.68%**
- worst-month head = **83.33%**
- worst-month 5pt = **23.08%**
- min month R=13

その他:
- `HGB_q0.975_AND_LR_q0.975`, conf .60: R100 / head88.00 / 5pt53.00
- `HGB_q0.975`, conf .60: R170 / head87.06 / 5pt52.94
- `HGB_q0.950`, conf .60: R468 / head85.47 / 5pt52.35
- `HGB_q0.950`, conf .70: R124 / head83.06 / 5pt54.03

Best joint R136の点数別 exact:
- 1点: 21/136 = 15.44%
- 2点: 40/136 = 29.41%
- 3点: 56/136 = 41.18%
- 4点: 65/136 = 47.79%
- 5点: 73/136 = 53.68%

### v297結論

- 90% head + 80% exact <=5点を満たすdevelopment ruleは無し。
- 分母操作や「1号艇勝利時だけ3連単評価」は禁止。
- v297をproductionへ昇格させない。

---

# v294〜v296 leakage history

## v294

`summary_v294_1head_verified_prepost_research.md`

一時 `PRE_HGB_RECCOVERED p_cal>=.980` が約99.09%に見えたが、meeting-slot leakageで無効化。

## v295

問題となったmeeting-derived features:
- `meet_st_strength`
- `meet_win`
- `meet_p2`

## v296

- `analyze_v296_1head_clean_operational_rebuild.py`
- `.github/workflows/research-20260911-v296-1head-clean-operational.yml`
- result commit: `4987332d3ec935945ec5d77163fe00624023ed72`
- summary: `summary_v296_1head_clean_operational.md`

historical race_cards のmeeting slotsに**current-race own ST/result**が入る self-slot leakage を確認。特にFeb-Apr。

clean familiesでは以下を禁止:
- `meet_st_strength`
- `meet_win`
- `meet_p2`

`CLEAN_STATIC6_PLAYER q.975`:
- Feb R6 100%
- Mar R50 90%
- Apr R55 92.73%
- May R89 87.64%
- Jun R93 83.87%
- pooled R293 88.05%
- worst 83.87%

clean ruleで5か月全部90%以上を意味ある件数で満たしたものは無し。

---

# 次にやること = v298

ユーザーの明示指示:

> 「3号艇モデルや4号艇モデルで使った特徴量や手法を真似て」

前チャットではここを**計画しただけで実装完了していない**。v298はまだ未作成。

## まず必ず読むファイル

- `CHAT_HANDOFF_20260911_3HEAD_V288_PRODUCTION.md`
- `CHAT_HANDOFF_20260911_4HEAD_V291_AUTOLIVE.md`
- 必要なら `CHAT_HANDOFF_20260911_4HEAD_V291_LIVE.md`

それらから、実際にproduction / liveで使っているコードファイル・特徴量・rank方式・閾値・scenario分岐を特定する。

特にコード上で確認したい概念:
- `PLAYER_START`
- listwise / race-group candidate ranking
- `TOP2XTOP2`
- `alpha2`
- `COND_BASE`
- relative ST / start strength
- wall / attack role decomposition
- motor strength / motor type
- course / athlete stats
- scenario-specific branch
- 展示後の相対値・役割分解

**名前だけ真似しない。v288/v291の本物の実装を読んでから移植する。**

## v298推奨方向

### A. 1号艇head側

v297のHGB+LRの単純guardだけでなく、3/4号艇モデル同様に「1号艇が負ける脅威」を相対構造で表す。

例:
- 1 vs 2/3/4 のST差・start力差
- 2/3/4の攻撃力
- 2が壁になる / 壁にならない
- 3/4のまくり脅威
- 1の逃げ性能と相手の攻撃性能のinteraction
- motor / player / courseの相対差

head>=90に届かない場合、相手側を調整して誤魔化さず、head threat model自体を改善する。

### B. 3連単相手側

v297の「20クラス一発multiclass」だけではなく、候補展開型を試す。

優先案:
1. **2着 ranker**: 2〜6号艇をrace内で5候補比較
2. **3着 conditional ranker**: 2着候補を固定したうえで残り4艇を比較
3. joint scoreで `1-a-b` 20通りを並べ top5

またはpair-expanded binary/listwise ranker。

candidate features:
- boat1 absolute
- 2着候補 absolute
- 3着候補 absolute
- 1との差
- 2着候補と3着候補の差
- ST/start/motor/player/course relative metrics
- 隣接艇/wall/attack context
- candidate-specific interactions
- v288/v291で本当に効いている役割特徴

### C. 相手confidence gate

training OOFだけから作る。
候補:
- top5 mass
- 5th vs 6th margin
- entropy
- 2着1位 vs 2位 margin
- conditional 3着 concentration

現在月のoutcomeを使ってgate決定しない。

## v298評価出力

最低限:
- R
- heads
- head%
- exact hit count / hit% for 1〜5 points
- monthly R/head%/exact%
- worst-month head%
- worst-month 5pt exact%
- Wilson CI
- stable-zone flag

stable条件はv297相当を維持:
- all five development months
- pooled R>=100
- min month R>=10

結果が悪くても数字をそのまま出す。

---

# 最新GitHub状態

引き継ぎ作成直前に確認したmain先頭:

- `2a74f88dde99de3fd971b163ec6cfe488de721ad`
- message: `Fix PowerShell negative seed offset arguments`

その親:
- `2ec10536f1d13fab4a197aa88136123a7e489dd9`
- `Benchmark boat1 seed localization sweep`

これは別系統のboat1 seed localization sweepが同時進行している状態。

**次チャット開始時に必ず再度最新mainを取得すること。**
Repoは並行更新が多いので、このSHAを固定前提にしない。

---

# 次チャットで最初にやる実作業

1. 最新main commit確認。
2. 上記3HEAD v288 / 4HEAD v291 handoffを全文読む。
3. handoffから参照される本実装script / workflow / summaryを読む。
4. v297コードを再確認。
5. 新規 `v298` ファイルとして実装。既存v297を壊さない。
6. 新規workflowでCI実行。
7. run成功だけで終わらず、job log / generated summary / CSVを確認。
8. R・head%・1〜5点exact%・worst monthを報告。
9. 90%/80%未達なら、その事実を明記して次の改善点まで進める。

## 絶対にしないこと

- また「これからv288/v291を読みます」で止まる。
- v298未実装なのに完了扱いする。
- July/Augustで選ぶ。
- September outcomeを見る。
- 1号艇負けを3連単分母から外す。
- meeting self-slot leakage特徴を復活させる。
- current test month outcomeからthresholdを決める。

---

# 次チャット用の最短指示文

`boatrace-backtest の CHAT_HANDOFF_20260911_1HEAD_V298_NEXT.md と最新GitHubを読んで続き。最新GitHubを優先し、3号艇v288・4号艇v291の実装を実際に読んで、1号艇v298を実装→CI→結果確認まで進めて。7月8月はNON-PRISTINE、9月はoutcome-blind厳守。`
