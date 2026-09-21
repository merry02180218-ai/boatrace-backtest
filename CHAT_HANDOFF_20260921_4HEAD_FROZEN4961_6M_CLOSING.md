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


## MANDATORY PRE-FIRE FULL INSPECTION RULE (2026-09-21 user instruction)

Before every GitHub Actions workflow dispatch/rerun, do NOT fire immediately after editing.

Mandatory sequence:
1. Refetch the actual committed workflow and every edited/used script from GitHub main.
2. Inspect the complete relevant files, not only changed lines.
3. Check literal escaped newline mistakes (`\\n`), quoting/indentation, YAML structure, syntax, env/path/file names, dependencies, permissions, artifact/run IDs, timeout/loop risks.
4. Perform every available static/syntax sanity check before dispatch. Python committed source must be syntactically valid; YAML actual committed structure must be inspected.
5. Confirm inputs/data paths and leakage guards (September UNREAD; no result-derived Waku10 reconstruction).
6. Only after ALL checks pass may the workflow be fired or the user be asked to fire it.
7. On failure, inspect full logs + source + inputs and identify root cause before any rerun. Never blindly rerun.
8. Record failure cause, fix, pre-fire checks, run/job/artifact IDs and result in this handoff.

Permanent project rule: repeated literal `\\n` failures are zero-tolerance; always verify the actual GitHub file before firing.


## 2026-09-21 — Boatcast Waku10 historical reconstruction / 6M coverage / Waku10 head-model v1

### User direction
- User first wanted the frozen 4-head model six-month official-closing-odds audit.
- After discovering Waku10 historical coverage was incomplete, user explicitly requested historical Waku10 reconstruction, leak checking, and shared storage usable by ANY model.
- User later changed research priority: before opponent/2nd-place model work, improve the 4-head HEAD model itself using Waku10.
- Production remains unchanged. September 2026 outcomes remain UNREAD.

### Historical Waku10 source investigation
- BoatraceCSV Waku10 source was traced to Boatcast:
  https://race.boatcast.jp/hp_txt/{jo:02d}/bc_j_waku10_{YYYYMMDD}_{jo:02d}_{race:02d}.txt
- Boatcast historical files were confirmed available for Mar-Jun 2026.
- Kyoteibiyori player_kako10 was tested and rejected as a substitute because it did not semantically match BoatraceCSV Waku10.
- Boatcast format: player name, frame-specific win rate, frame-specific average ST, frame-specific average start rank, then up to 10 prior runs x finish/course/grade.

### Leakage / lineage audit
- audit_boatcast_waku10_leak.py + workflow were added.
- Run 35527070792 SUCCESS:
  - tested 5 historical targets
  - repeated fetches identical
  - no direct result fields
  - LEAK_AUDIT_OK
- Important wording: this is strong evidence of no leakage indicators, NOT mathematical proof that Boatcast never rewrote a historical file after race day.
- Full semantic parity audit against BoatraceCSV existing Waku10 for 2026-07-19 through 2026-08-31 eventually succeeded:
  - Run 35558286203
  - 44 CSV days
  - 1,424,736 cells
  - 0 semantic mismatches
  - RESULT_FILES_READ False
  - SEPTEMBER_OUTCOMES_READ False
  - FULL_PARITY_OK
- Semantic normalization allowed harmless representation differences: whitespace in names, 6.40 vs 6.4, '-' vs blank missing numeric.
- Therefore reconstructed historical Boatcast data has strong same-source/data-lineage evidence with BoatraceCSV Waku10.

### Reconstruction history
- First sequential Mar-Jun reconstruction Run 35527152093 was CANCELLED after 2h; artifact step never ran, so runner partial files were lost.
- Fast monthly reconstruction was created with 24 threads, monthly matrix, 45-min timeout, and always-upload partial artifacts.
- Run 35547108828 SUCCESS:
  - Mar REQUESTED/SAVED 4607/4607, missing 0
  - Apr 4244/4244, missing 0
  - May 4832/4832, missing 0
  - Jun 4488/4488, missing 0
  - total 18,171 files, missing 0
  - result files not read; September outcomes not read
- Validation Run 35547394740 SUCCESS:
  - FILES 18171
  - FORMAT_BAD 0
  - SOURCE_SAMPLES 40 / MISMATCH 0
  - known Jul19 match true
  - VALIDATION_OK
- Shared promotion Run 35561996464 SUCCESS.
- Shared Mar-Jun commit:
  6410b14d209eb7247cce2770693a73b6f3f7cc04
  message: data: add shared historical Boatcast Waku10 Mar-Jun 2026
- Canonical shared path:
  data/shared_historical/waku10_boatcast/2026/MM/DD/JJ_RR.txt

### July reconstruction / shared storage
- July-only reconstruction workflow commit:
  bfab0925d4fc57e4099114fa991e57adc48a2214
- Run 35568270269 SUCCESS:
  - MONTH 07 REQUESTED 4920 SAVED 4920 MISSING 0
  - MONTH_RECONSTRUCT_OK
- July shared promotion workflow commit:
  1da2cfdd9dbf5cf8fae61590968c038cd4842fb3
- Promotion Run 35570488453 SUCCESS:
  - JULY_SHARED_WAKU10_FILES 4920
  - RESULT_FILES_READ False
  - SEPTEMBER_OUTCOMES_READ False
  - PROMOTE_JULY_OK
- July shared data commit:
  edcb7be33d35b1fc5a50b8635f36bd5685028cf3
  message: data: add shared historical Boatcast Waku10 July 2026
- Shared Boatcast Waku10 is therefore available Mar-Jul and intended as common input for all models, not 4HEAD-only.

### Six-month Waku10 loader bug and fix
- prepare_4head_6m_v93_neutral_waku.py was wired to shared historical Waku10.
- Initial coverage failures:
  - Run 35563549072: V93 21195/23855
  - diagnostic Run 35564294166: 20698/23855
  - missing by month then: Mar123 Apr74 May196 Jun104 Jul2660
- July 2660 was mainly because shared July was not yet connected.
- After July connection commit bb81828c924da0d9017b548203f9de3e36bc1614:
  - Run 35571710194 failed at 23220/23855 = 97.338%
  - missing Mar123 Apr74 May196 Jun104 Jul138
  - SHARED_DIAG_20260303 returned only 12 rows and missed known race codes.
- Root cause found: nested day directory loader bug.
  Actual path is e.g.
  data/shared_historical/waku10_boatcast/2026/03/03/04_01.txt
  but after entering /03/03 the loader incorrectly searched for 03_*.txt instead of *.txt.
- Fixed in commit:
  44231256976040596f30b859158073b1ae278046
  by using root.glob("*.txt") for the day directory.
- Pre-fire inspection after fix: literal escaped newline false, old bad pattern absent, shared path correct, Python preflight present, September guard present.

### Final six-month complete-Waku audit
- Run 35572435087 SUCCESS at head SHA 44231256976040596f30b859158073b1ae278046.
- Waku coverage:
  - parent_R 23855
  - v93_R 23855
  - MISSING_BY_MONTH {}
  - 100% coverage
  - rebuilt monthly: Mar3550 Apr3282 May4260 Jun4049 Jul4487 Aug4227
  - shared_historical_waku10_used True
  - waku10_backfill_used False
  - source: Boatcast shared historical Mar-Jul + BoatraceCSV existing Jul-Aug
  - September outcomes false
- Official closing odds six-month current-ticket audit also completed:
  - strict_R 23855
  - decision_R 17649
  - production_BET_R 233
  - mean 2.099 bets/day, median2, max5
  - head4 106 / 233 = 45.49%
  - trifecta hits 52
  - stake 2,330,000 JPY
  - payout 2,075,330 JPY
  - profit -254,670 JPY
  - ROI 89.069957%
  - max drawdown 531,530 JPY
  - max losing streak 20
  - base120_BET_R 183
  - newfeature_add_BET_R 41
  - closing_odds_used true
  - production unchanged
  - September UNREAD
- Monthly examples preserved from audit:
  - Mar 32R / head4 13 / hits9 / ROI100.49375 / +1,580
  - Apr 33R / head4 17 / hits10 / ROI113.81818 / +45,600
  - previous audit monthly totals for May-Aug remain in earlier section/logs.
- Key conclusion: Waku10 coverage uncertainty is now removed. Current ticket ROI is still below 100%; opponent selection remains a later bottleneck, but user explicitly wants HEAD model Waku research first.

### Current research priority: Waku10 HEAD model improvement
User explicitly said:
「ていうかまずwaku10使った頭モデル改善したい」
So DO NOT jump to the 2nd-place/opponent model yet.

Baseline/frozen reference:
- frozen head candidate: p>=.36 + ORIG>=-.06
- complete six-month current-ticket audit selection: 233 bets, 106 head4 = 45.49%
- earlier frozen Jul-Aug head-only audit was ~49.61%, but threshold/orig research history means do not treat it as pristine untouched validation.
- Goal: test whether Waku10 can improve head selection while retaining useful race volume; avoid tiny-sample 50% gates.

### Waku10 head-model v1 implementation
Created:
- research_4head_waku10_headmodel_v1.py
  commit 3189418e4698a36552651efaf4596d9bc7c2f77f
- .github/workflows/research-4head-waku10-headmodel-v1.yml
  commit 7088580afa02f124bbe1c9578d5c9c2e71e88fe5

v1 design:
- rebuild complete Waku parent first using prepare_4head_6m_v93_neutral_waku.py
- compare BASE vs BASE_WAKU
- DEV = Mar-May
- VAL = Jun
- HOLD = Jul-Aug
- threshold selected from June only, requiring >=50 selected races
- Jul-Aug holdout is never used for threshold selection
- obvious outcome/result/payout/odds/finish columns forbidden from predictors
- result path direct reference absent in v1 research script
- September outcomes UNREAD
- production unchanged
- Python compile preflight
- literal escaped newline checked false before firing

### CURRENT ACTIVE RUN — NEXT CHAT START HERE
User fired Waku10 head-model v1.
Current Run:
- Run 35576576982
- workflow: research-4head-waku10-headmodel-v1
- head SHA: 7088580afa02f124bbe1c9578d5c9c2e71e88fe5
- status at handoff write time: IN_PROGRESS
- conclusion: not yet available

NEXT ACTION:
1. Fetch Run 35576576982 status/jobs/logs.
2. If FAILURE: obey mandatory rule — inspect full logs + actual committed script/workflow + inputs, identify root cause, fix, refetch actual GitHub files, full pre-fire inspection, only then ask/fire again. Never blind rerun.
3. If SUCCESS: inspect BASE vs BASE_WAKU DEV/VAL/HOLD results carefully.
4. Check actual feature list/count and ensure the identified Waku columns really are Waku10-derived rather than unrelated frame-named columns.
5. Evaluate Jul-Aug HOLD without using it to tune. Report R, head4, head rate and volume change.
6. If Waku improves robustly, next research should inspect individual Waku families and relative wall features (4 vs 1/2/3), using train/validation only for selection and preserving holdout.
7. Do not modify production without explicit user adoption.
8. Keep September UNREAD.

### Permanent pre-fire rule reminder
Before EVERY workflow dispatch/rerun:
- refetch actual committed workflow and all edited/used scripts from main
- inspect complete relevant files
- literal escaped newline check
- YAML/quoting/indentation/syntax/env/path/dependency/permissions/artifact IDs/timeout checks
- Python syntax/preflight
- verify leakage guards and September UNREAD
- only then fire/ask user to fire
- on failure inspect logs/source/inputs before any rerun
- record cause/fix/run/job/artifact/result in handoff
