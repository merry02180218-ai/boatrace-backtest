# CHAT HANDOFF — 4HEAD CLEAN 49.61 / OPPONENT / 6M CLOSING
Updated: 2026-09-21 JST
Repo: merry02180218-ai/boatrace-backtest

## 最重要ルール
- 最新GitHub/mainを古いチャット・記憶より優先。
- September 2026 outcomes/payouts は UNREAD 維持。明示許可なしに読まない。
- Waku10 はリーク注意。欠損を将来結果・結果由来データからバックフィル/復元しない。
- production は明示採用まで変更しない。
- Workflow変更後は発火前にGitHub上の実ファイルを再取得し、literal \\n 混入、YAML構造、実行スクリプト、env/pathを確認する。エラー時は盲目的に再発火せずログ/ソース/入力を徹底調査。
- ユーザーは日本語・具体的進捗を希望。「続けて/発火した/終わった？」にはツールで実確認してから答える。

## 1. 旧LIVEの問題
旧 current LIVE の exact August replay:
Run 35490239458 / Job 106023817951 / Artifact 10599191705
- strict 851R
- BET 323R, 10.77R/day
- head4 95
- 3連単 hits 53
- stake 3,230,000 / payout 3,039,690
- profit -190,310 / ROI 94.108%
- DD 524,560 / losing streak 19
旧研究の156R universeは v93<-v91<-v90<-v83<-v74<-v20 legacy gateで狭められていたため、現在LIVE利益性の証明には使わない。

## 2. clean-slate 4HEAD
Clean dataset Run 35499385294: Mar-Aug exact current exhibition parity, legacy gate false, Waku backfill false.
Head baseline Run 35500144059:
- LogisticRegression C=.5, 66 PRE features
- DEV Mar-May / VAL Jun / HOLD Jul-Aug
- p=.36 chosen June only
Exhibition audit Run 35500981477:
Frozen candidate = p>=.36 + ORIG>=-.06
- DEV 124/49 =39.516%
- Jun 50/24=48.0%
- HOLD Jul-Aug 127/63=49.6063%
  - Jul 65/32=49.231%
  - Aug 62/31=50.0%
ユーザーが 49.61 を正式な頭候補として固定する方針。
ORIGは場固有計測ソースだが補正/重みは共通lane correction。ユーザーは場別ORIG補正は不要と判断。
Motor hard gateは悪化（ORIG only hold49.606%, ORIG+motor46.59%, fullPRE47.56%）。
p relaxation / low-p rescue は不採用。
May弱さは広範で、ユーザーはブレと判断。
リーク監査: direct result leakageなし、Waku10未使用、legacy gate未使用、Sept UNREAD、Jul-Augはp=.36選定に未使用。ただし ORIG -.06 は研究中に評価済みなので完全pristine thresholdではない。

## 3. Frozen 49.61 + current v283 exact August
Run 35507996419 SUCCESS
- strict/decision 851
- BET 44
- mean2.095/day median2 max5
- head4 22/44 =50.0%
- 3連単 hits10
- stake440,000 payout369,420 profit -70,580 ROI83.9591%
- DD160,000 / losing streak16
- Sept false / production unchanged
結論: 頭モデルは機能したが current v283 opponent/ticket selection がボトルネック。

## 4. Opponent miss decomposition
Run 35509349203 SUCCESS
- head4_R22 / exact hits10 / misses12
- miss_second_not_covered 8
- second covered but third wrong 4
- actual 2nd v283 rank: 1位7, 2位7, 3位1, 4位5, 5位2
- actual 3rd conditional rank: 1位5, 2位6, 3位6, 4位5
=> 最大問題は2着モデル。

Feature diagnosis Run 35510040870 SUCCESS:
実2着が4-5位へ落ちた7R vs v283 top予測艇:
- pos_boat_number delta +1.286
- pos_distance4 -0.857
- cur_orig_straight -0.757
- v93_local -0.352
- pos_inside4 -0.286 / outside4 +0.286
- v93_national -0.285
- cur_orig_turn +0.271
- v93_grade -0.250
- v93_nst -0.209
- pref_pl_recent_p2 -0.188
- cur_orig_avg -0.183
- pref_pl_all_p2 -0.182
- cur_st -0.129
解釈: v283が通常の「選手力/直線/ST強者」を2着上位に置きすぎ、4頭特殊展開で拾う艇を落としている可能性。

Shadow scramble rescue Run 35511032334 SUCCESS:
- 2着取り逃し8R
- 追加1艇で rescue 1R =12.5%
- rank4-5 7R中 rescue1
=> 単純レスキューはREJECT。v283補正だけより、4号艇1着専用2着モデルを6か月から研究する方向。

## 5. 場差の仮説
ユーザー: 「場とかにもよりそう」
8月22 head-correctのみでは母数が小さいため場別ルールはまだ作らない。
次にやる候補:
- 3〜8月の「4号艇が実際に1着」の全レースで
  venue × actual2 × 展開/展示/ST/ORIG を集計
- 場別の2着構造が本当に安定しているか母数付きで確認
- 場別補正はその後。8月少数例へ過学習しない。

## 6. ユーザー最新依頼: frozen model半年分を締切時オッズでテスト
ユーザー:
「あと締切時オッズでいいからこのモデルの半年分のテスト結果をみたい」

要件:
- Mar-Aug 2026
- head selection frozen p>=.36 + ORIG>=-.06
- current v283 opponent/tickets
- current 4-6 tickets
- JPY10,000 Dutch/race
- official closing trifecta odds
- monthly BET/head4/3連単 hits/stake/payout/profit/ROI
- total ROI/profit, max DD, max losing streak, venue ROI
- September UNREAD
- production unchanged
- Waku10 result-derived backfill禁止

### 追加済みコード
1) prepare_4head_6m_v93_neutral_waku.py
commit ecb14f6eaed5cc3f94d1fbce4e1e1cbc91ded50d
- clean long datasetからMar-Aug struct_ready parentを作る
- rebuild_4head_v93_all_parentを利用
- historical Waku10欠損時は同race codeの空rowを与え、race-card fallback/neutral-low waku primitive
- 結果からWakuを復元しない
注意: このneutral-Waku方針は完全なLIVE parityではなく、半年カバレッジ用の保守的proxy。結果解釈時に明記すること。

2) audit_4head_6m_frozen4961_closing.py
initial commit 4bf61c60...
fix commit e5fe35a8f0e771b25deebffd69c235d6d0461a65
- official closing odds: data/official_closing_odds3t/2026/MM/DD.csv
- frozen p>=.36 + ORIG>=-.06
- v283 + current production_tickets + Dutch
- Mar-Aug truth only
- monthly/venue/total metrics
- fallback reads BoatraceCSV checkout for race cards/results

3) Workflow
.github/workflows/audit-4head-6m-frozen4961-closing.yml
commit cbd12fa2d0004a8a796218c15ec1c7c1686c28b6
Preflight verified by re-fetch:
- literal \\n = false
- workflow_dispatch present
- prep script present
- audit script present
- Mar-Aug markers present
- official_closing_odds3t present
- September flag present
発火リンク:
https://github.com/merry02180218-ai/boatrace-backtest/actions/workflows/audit-4head-6m-frozen4961-closing.yml

### IMPORTANT: まだこの半年Workflowの結果は未確認
次チャットの最初:
1. 最新GitHub/mainとこのhandoffを読む。
2. 上記workflowが発火済みかActions latestを確認。
3. 未発火ならユーザーに上記リンクを出す。
4. 発火済みならRun/Jobを確認。
5. FAILUREなら full relevant logs を読み、原因を直す。盲目的rerun禁止。
6. SUCCESSなら artifact/logから monthly + total + venue + DD + streak を回収。
7. 8月 pre-close exact ROI83.96%とは「締切時オッズ」「neutral Waku proxy」という条件差を明記して比較。
8. その後、場別2着傾向の6か月調査へ進む。

## 7. 重要な過去Run/Commit
- exact old LIVE Aug ROI: 35490239458
- clean dataset: 35499385294
- clean head baseline: 35500144059
- exhibition frozen49.61 audit: 35500981477
- frozen49.61 Aug profit: 35507996419
- opponent decomposition: 35509349203
- second feature diagnosis: 35510040870
- second rescue shadow: 35511032334
- opponent script commit 85451ee...
- fixed opponent workflow commit 6b109c9...
- feature script beaac426...
- feature workflow 67882da...
- rescue script 4926f36...
- rescue workflow d90da1b...

## 8. 今後の優先順
A. 半年締切時オッズWorkflowの結果回収/修正
B. 6か月場別2着構造調査
C. 4号艇1着専用2着モデルを6か月データで構築
D. 3着conditional model再研究
E. 最後にROI/点数/Dutchを再検証
頭モデル p>=.36 + ORIG>=-.06 は当面固定し、相手研究中に触らない。
