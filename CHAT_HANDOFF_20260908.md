# CHAT HANDOFF — 2026-09-08 JST

次チャットはこのファイルを最初に読み、さらにGitHub mainの最新commit/production文書を確認してから作業する。古いチャットと競合したら最新commit/production文書を優先。

## 絶対ルール
- 予想・BUY/SKIP・確率・相手順位・買い目はassistantの推察で出さない。必ず現行GitHubコードを実行する。
- スクショは数値を読み取り、LIVE入力へ入れて実プログラムを通す。未実行なら「未計算なので買い目は出さない」。
- 結果/払戻/締切後情報を見る前に買い目freeze。後付け変更禁止。
- 過去検証はwalk-forward/no-leak。テスト月より未来を学習・閾値選択に使わない。
- 同じ期間を見て条件発見→同じ期間で採用判断しない。別期間forward/SHADOWで確認。
- 優先評価: ROI → 的中率 → 頭率/安定性。月別も必ず確認。

## Repository
merry02180218-ai/boatrace-backtest

## 1号艇 現行production
Canonical: `V162_PRODUCTION_ADOPTION.md`
**Legacy PRE -> v109 S-only -> v162 Top7**
- PRE selection unchanged。
- 展示/直前入力をv109へ。
- BUYはv109 Sのみ: p109 >= 0.72。
- BUY時、v162 direct ordered-pair lambda=1.00で20通り `1-s-t` を順位付け。
- Top7提示。実際の点数/金額はユーザー判断。
- v110 role-factorized lambda=.50は旧相手モデル。
- v162 Jun-Aug: conditional coverage 66.43→69.86%、S/Top7 trifecta hit 50.97→53.60%。ROI最大化を証明した採用ではない。
- v116はv109構造を2026-08-31までrefitしたLIVE系。A=.65/S=.72。必要なら最新コード確認。
- LIVE手動系 `predict_v194_1head_live_manual.py` がある。使用前に最新版をfetchして仕様確認。

## 3号艇 現行production
Canonical: `V166_3HEAD_PRODUCTION_RULE.md`
**展示取得 -> v165 p3head>=30% -> v166 direct lambda=1.00 -> Top10**
- v165は展示前PREではない。ex_margin23, st_margin23, straight_margin23, turn_margin23等の当日展示特徴が必要。
- 展示前にp3headを推測/中立補完してproduction扱い禁止。
- 3号艇が展示進入で3コースを外れたら除外。
- v166相手は[1,2,4,5,6]のordered 20通り、Top10。
- Jun-Aug canonical baseline: 270R、3頭38.52%、3連単hit29.26%、3頭時Top10 coverage75.96%、equal-stake ROI103.2%。月ROI 91.2/116.3/100.9。
- v107 structural PREは旧/観察用でproduction代替禁止。
- 展示前モニタリングはv191 clean PREを別物として使える。PREスコアをp3head/BUYと呼ばない。
- LIVE手動: `predict_v192_3head_live_manual.py`, `live_input_3head.json`, workflow `v192-3head-live-manual.yml`。スクショ値を入れて実行する。高速版v193がある可能性は必ず最新GitHubで確認。

## v165/v166実装要点
v165 schema sourceは `analysis_v108_1head_feasibility.csv`。target winner==3。主要features: ex_margin23, margin2, margin_all, st_margin23, straight_margin23, threat2/4/5/6, turn_margin23。StandardScaler + LogisticRegression(C=.35,max_iter=1800)。
v166: direct pair LogisticRegression C=.35、OPP=[1,2,4,5,6]、lambda=1.00、Top10。払戻はsettlementだけに使用。

## 6か月production replay v195
2026-03〜08を現行ルールで検証。
月別:
- Mar 58R head36.21 hit34.48 ROI72.8
- Apr 40R 42.50 32.50 69.3
- May 77R 37.66 31.17 100.5
- Jun 73R 41.10 30.14 91.2
- Jul 87R 29.89 26.44 116.3
- Aug 110R 43.64 30.91 100.9
合計445R、head38.43%、hit30.56%、Top10 coverage79.53%、購入約444,000円/払戻425,030円、ROI95.7%。Mar-Mayはv166開発時のlambda tuningに関係するので6か月全部をpristine OOSとは呼ばない。Jun-Aug canonical OOS再現を基準にする。

## v196 failure diagnostics
同じ445Rを記述的分解。採用条件選択には直接使わない。
- turn_margin23 Q4側: 202R head44.55 hit36.63 coverage82.22 ROI135.3
- Q1側: 136R head34.56 hit25.74 coverage74.47 ROI71.9
- p3帯は単調ではない。35-37.5%=ROI117.2だが高p3帯が必ず高ROIではない。
- 場差大。ただし小標本なので即フィルタ禁止。
- Top10後半にも多数的中。Top5縮小は安易にしない。

## v197 turn-margin pseudo-forward
Mar-May tune -> Jun-Aug testで chosen cut -0.800。
Jun-Aug BASE 270R ROI103.2 → FILTER 246R head38.62 hit30.08 coverage77.89 ROI110.1。
Rolling Apr-Aug BASE ROI99.2 → FILTER ROI110.6。ただしv196でMar-Aug傾向を既に見ているためpristineではなく、production変更なし。

## v198 長期検証 — 最新重要結果
Run 34200909438 SUCCESS。`summary_v198_3head_long_history_validation.md`。
source 2025-11-01..2026-08-31、評価可能2025-12..2026-08の9か月。各月は過去のみでv165/v166学習、rolling turn gateも過去評価月だけで選択。Jul/Augを過去cut選択に使用しない。
BASE月ROI:
2025-12 78.1 / 2026-01 53.2 / Feb85.6 / Mar72.8 / Apr69.3 / May100.5 / Jun91.2 / Jul116.3 / Aug100.9。
Critical PRE-Jul:
- BASE 493R head34.48 hit28.19 coverage81.76 cost491000 return381840 ROI77.8
- ROLLING 329R head33.74 hit27.36 coverage81.08 cost327000 return244790 ROI74.9
Jul-Aug:
- BASE197R ROI107.7
- ROLLING17R ROI139.1
=> 重要: rolling周り足gateは7/8月以前では改善しておらず、むしろ77.8→74.9。7/8月の強さは過学習/期間依存の疑いが強い。現時点でturn gateをproduction採用しない。
固定cutをPRE-Julだけで見ると -0.2:58R ROI115.2、0.0:44R ROI131.0だが、これは同じPRE-Julデータ上の探索結果で小標本。これもそのまま採用禁止。別の未使用期間/将来SHADOWが必要。

## v198の次にやるべきこと
ユーザーの懸念は「7/8月過学習」。v198はそれを支持。次はproductionを変更せず:
1) 2025-12〜2026-06をさらに期間分割（early/late、月別、場別）してturn_marginの安定性確認。
2) 閾値を探索しすぎず、候補を少数（例 -0.2/0.0）に事前固定してSep以降SHADOW。
3) 可能なら2025-11以前の同品質v108/展示データを復元して追加の完全未使用historical OOSを作る。
4) 周り足だけでなく、v196で見えた特徴を単独/複合で試す場合も nested/rolling WFにする。結果を見た同期間で採用禁止。
5) production baselineと比較して候補数、head、hit、coverage、cost/return/ROI、月別ROIを出す。

## 3-head PRE v191
clean PRE monitor only。June train→July tune→Aug untouched。cut .072608。July watch648/4772=13.6%, recall85.1%; Aug679/4776=14.2%, recall85.5%。gate PASS。PRE watch→展示→正式v165>=30→v166 Top10。PRE値をp3head/BUYにしない。

## 2026-09-08 PRE scan
v191 today run 34165346250 success、11場132R、watch33R。80%以上12Rを抽出済み。ただし全てPRE monitoring scoreでproduction確率ではない。

## 既知LIVE 3-head実行例
鳴門5R p3=15.45 SKIP、三国6R p3=19.54 SKIP。スクショからv192実行済み。その他児島8R/平和島9R/江戸川10R等は結果を再利用する前に最新output/logを確認。江戸川はoriginal exhibition無し。欠損処理はassistant判断せずコード挙動を実行確認。

## odds archive
ユーザーは他検証にも使うため全レース3連単oddsを希望。
- BoatraceCSV od3は約締切5分前snapshot。fast archive run34164427274: 44日/6726R available、主に2026-07-19〜08-31。
- official closing parallel fill run34165746292: missing291日、42796 race requests、41908R取得、約888R残り。
- retry workflow run34177912434が過去に開始。最新状態/残数は必要時にGitHubで確認。
- snapshot oddsとofficial closingを同一source扱いで混ぜない。provenance保持。

## 過去モデル/検証
- v179 racer-style soft-pair: alpha=0、改善なし、reject。v166維持。
- v180 style predictive features: Jan-AugでAUC/Brier/logloss改善したがproduction gateではない。
- v181/182/183/185/186 reject。
- v187 odds dynamic reject: OOS dynamic ROI85.6 vs fixed10 86.3。
- v188 style threshold + v166 Top10はodds欠損影響あり、production不採用。

## テスト方法の原則
- Historical validationはstrict walk-forward。JuneならMay以前、JulyならJune以前、AugustならJuly以前。
- 閾値/ハイパーパラメータをtest月で選ばない。
- 開発期間(tune)と完全未使用OOSを明記。
- 期間を見て発見した条件は同期間で「検証済み」と呼ばない。pseudo-forward/diagnosticと明記。
- ROIは100円/点でcostを計算、payout100をreturnに使用。Top10なら通常1000円/R。
- oddsをpredictive featureにするなら締切前snapshotのみ。final oddsは予測特徴禁止。
- 結果・払戻はsettlementだけ。
- 月別再現性を重視し、aggregateだけで採用しない。

## 他の全場モデル
従来運用では3号艇まくり/まくり差し、4角まくり、5頭モデルを全場横断候補抽出。事前候補→展示後S/A/Bの二段階。モーターは2連率だけでなく伸び/行き足/出足/回り足/一周、枠コース補正後の過去展示を評価。3まくり・4角は伸び/行き足/ST、3まくり差し・5頭は出足/回り足を重視。ただし4角/5頭の「現在の正確なversion/threshold/production」は次チャットで必ず最新GitHubを検索して確認し、記憶だけで断定しない。

## 次チャット開始手順
ユーザーが「続き」「引き継ぎ」と言ったら:
1. `CHAT_HANDOFF_20260908.md` をGitHubから読む。
2. `V166_3HEAD_PRODUCTION_RULE.md`, `V162_PRODUCTION_ADOPTION.md` とmain最新commitを確認。
3. 直近v198 summaryを確認。
4. 予想なら対象モデルのLIVEコードを実行。推察禁止。
5. 検証ならno-leak/WFを守り、既視期間とpristine OOSを区別。
