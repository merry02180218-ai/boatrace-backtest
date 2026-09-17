# 1号艇 v351 現状引き継ぎ — 2026-09-17 15:24 JST

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール / ユーザー運用方針
- 最新GitHub + 最新引き継ぎを、古いチャット/記憶より必ず優先する。
- 「無い」と判断する前に、最新mainだけでなく **commit履歴 / 既存script / workflow / Actions Run / Artifact** まで検索する。今回、昨日作成済みのSeptember rolling経路を見落としたため、以後これは必須。
- 作業開始前に「これからやること」を引き継ぎへ記録し、作業完了後に結果・commit SHA・Run/Job/Artifact・結論・次の再開地点を追記する。
- workflowを書き換える前にtriggerを確認する。不要なpush発火、noop commit、新規workflow乱立は禁止。
- 1回発火→確認→次。エラー→commit→発火の無確認ループは禁止。
- ユーザーは実作業と厳密確認を希望。未確認の完了/発火/結果を断言しない。
- 自動LIVEより、ユーザーが「判別して」と言った時の手動取得/判定を優先する。
- HEAD学習特徴へ展示を直接追加しない。展示は post-ranking / ticket-rescue / live final correction のみ。

## September結果の扱い（今回の特例）
- 通常historical hard guardは `race_code < 20260901`。
- ユーザーが2026-09-17に明示的に「昨日までの9月のレースバックテスト」を依頼したため、**今回のretrospectiveに限り 20260901〜20260916 の確定結果・払戻を評価用として読むことを許可**。
- **20260917当日結果・払戻は絶対に読まない。UNREAD維持。**
- 9/17 LIVE/判定データは pre-race / exhibition のみ使用可。`result_or_payout_used=False`, `chronology_guard=True`。

## 現行1号艇 production
profile:
`1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`

構成:
- HEAD model: v308
- HEAD cutoff: 0.78
- opponent mass min: 0.375
- SECOND: v317_OUTER_L2_1
- THIRD: v318_DROPSTART_T0.1
- ticket policy: v320_HYBRID
- exhibition: v332_ATTACK_ENV_SOFT_V345_ATTACKCORE
- exhibition env: w=.10 / q=.65
- opponent core: SECOND G2=.45 / THIRD G3=1.00

formal historical baseline:
- 購入対象 276R
- 1号艇1着 241R = 87.32%
- exact3 131R = 47.46%
- 基本3点

## このチャットで確認した9/17 LIVE情報
9/17 v351 canonical cache:
- Artifact 10477251012
- Run 35170926144
- head SHA `d951448ff9e6b397454fff796cf70bbf0c08bfcf`

formal candidates:
1. 平和島12R `202609170412`
   - final_head_p 0.7901582366125368
   - opp_mass 0.42123448085672327
   - tickets `1-4-2;1-4-5;1-2-4`
2. 尼崎6R `202609171306`
   - final_head_p 0.8301538300238417
   - opp_mass 0.38674739724923224
   - PRE tickets `1-2-4;1-2-3;1-4-2`
   - safe post-deadline replay final = DROP (`head_exhibition_pass=false`), final tickets=[]
   - replay Run 35181006387 / Job 105072935543 / Artifact 10480421315
   - result/payout未使用、chronology_guard=true
3. 下関4R `202609171904`
   - final_head_p 0.8105814572971805
   - opp_mass 0.4090498291303686
   - tickets `1-2-5;1-2-3;1-3-2`

## Wave / close-margin整理
- 1号艇 Wave17/18 は production 276Rを直接変更するルールではなく、opponent_mass .350-.375 のbelow-cutoff rescue研究。
- Wave17 `BOAT3_STRONGER -> boat5 THIRD rescue`。候補は frozen choice で `1-3-5`。add4 と fixed3 を比較。
- 尼崎6RにはWave17/18条件は発火しないため、強制購入ならPRE 3点のまま。
- ユーザーが覚えていた「3着候補が僅差なら4点化 / 3着だけ両方押さえる」はWave17とは別。
- 4号艇 v283 では THIRD close-margin 0.10 が正式productionへ昇格済み（commit `376c636839af499821244ca660e382a43a16d644`）。
- 1号艇v351について同様のclose-margin 4点化は、今回の9月auditが終わった後に276R基準で別監査候補。閾値0.05/0.10/0.15等を比較し、的中増・追加点数・ROI・月別安定性を見る。ただし現行ticket ranking semanticsを確認してから定義し、推測で作らない。

## Sep1-16 retrospective — ここまでの経緯
ユーザー依頼: 現行1号艇v351を **2026-09-01〜09-16** でバックテスト。

### 失敗した旧方式
最初に `.github/workflows/audit-1head-v351-sep1-16.yml` を作り、daily cache + Boatcast postrace probeを1Rずつ直列で再取得した。
- Run 35185302721
- Job 105085988789
- 45分 timeout / cancelled
- 原因: 1RずつBoatcast再取得で20〜60秒級、全レースを直列処理したため。
- さらにartifact検索上、frozen daily cacheは主に9/15・9/16しか見えていなかった。
- この旧方式をそのまま再実行しない。

### BoatraceCSVを確認
ユーザー提示: `BoatraceCSV/boatracecsv.github.io`
確認結果:
- 1レース1行CSV、12桁race_code `YYYYMMDDjjrr` でJOIN可能。
- 9月実データあり。
- 主なpath:
  - `data/programs/race_cards/YYYY/MM/DD.csv`
  - `data/programs/waku10/YYYY/MM/DD.csv`
  - `data/programs/recent_national/...`
  - `data/programs/recent_local/...`
  - `data/programs/motor_stats/...`
  - `data/programs/motor_history/...`
  - previews: `tkz / stt / sui / original_exhibition`
  - results: `data/results/realtime/YYYY/MM/DD.csv`
  - payouts: `data/results/payouts/YYYY/MM/DD.csv`
  - odds: `data/previews/od3/YYYY/MM/DD.csv`
- 9/1について展示CSV、original_exhibition、payoutsの実在を確認済み。
- 予測側データと結果/払戻を分離して扱えるのでretrospectiveに適する。

### 重要: 昨日すでにSeptember rolling経路を実装済みだった
当初「9/1〜14はcacheが無いので新規再構築が必要」と誤認したが、commit履歴を再検索して既存経路を発見。今後は毎回この確認を先にする。

既存主要commit:
- `5910d1e` — September chronology-safe training source builder
- `b3849cd` — v308 / v317 / v318をSeptember prior-dayまでrolling学習
- `1aeb459` — v351 rolling models through September prior-day
- `b94ef694e34981d54586325e3412d165412e6f4a` — BoatraceCSV race_cardsを使う正式loader修正

既存主要script:
- `build_1head_september_training_source.py`
  - 既存のstrict historical rowsを維持し、BoatraceCSV race_cardsからSeptember prior-dayの追加学習行を作る。
  - 対象日当日の結果は学習に使わないchronology-safe設計。
- `prepare_1head_v351_rolling_models.py`
  - 対象日ごとに `training_cutoff = target_date - 1 day`
  - v308 HEAD / v317 SECOND / v318 THIRD / v320 ticket / v332 exhibition等の現行v351系をrolling再現する経路。

## 現在のSep1-16 workflow（重要）
`.github/workflows/audit-1head-v351-sep1-16.yml`

最新修正commit:
- `bf69cd3f48001109aaa3d103499726b98ee80651`
- message: `audit: use existing September rolling model path`
- このcommitによる予期しないpush Actions runは0件確認済み。

現在のworkflow方針:
1. `build_1head_september_training_source.py --cutoff 2026-09-16` で既存chronology-safe September sourceを再構築。
2. `prepare_1head_v351_rolling_models.py` を使い、9/1〜9/16を日付順に既存v351 rolling経路でバックテスト。
3. 予測/候補生成後にのみBoatraceCSV results/payoutsをJOINして評価。
4. 9/17データは取得しない。
5. 購入R / 1頭数・率 / exact3数・率 / 投資 / 払戻 / ROI / 日別明細をartifact化する設計。
6. workflow triggerは `workflow_dispatch` のみ。

## 現在発火中のRun — 次チャットはここから
ユーザーが手動発火済み。
- Workflow: `audit-1head-v351-sep1-16`
- Run: **35189567267**
- Run number: 2
- head SHA: `bf69cd3f48001109aaa3d103499726b98ee80651`
- Job: **105098929876**
- 2026-09-17 15:24 JST時点 status: **in_progress**

現在のstep:
- setup: success
- dependencies: success
- **Step 5 `Rebuild chronology-safe September source through Sep16`: in_progress**
- Step 6 `Backtest existing v351 rolling path Sep1-16`: pending
- artifact upload: pending

Job実行中のためlogs downloadはまだ404 BlobNotFoundだった。これはjob終了前なので異常とは限らない。

Run URL:
`https://github.com/merry02180218-ai/boatrace-backtest/actions/runs/35189567267`

## 次チャットで最初にやること
1. **まず最新GitHub / このhandoff / Run 35189567267 を確認。**
2. Runがまだin_progressならJob 105098929876のstepsを確認して待つ。新しいRunを重ねない。
3. Run完了後:
   - conclusion確認
   - job logs確認
   - artifact ID/name確認・中身確認
   - 9/1〜9/16の購入R、1頭率、exact3率、投資、払戻、ROI、日別/レース別明細を厳密に確認
   - 9/17結果が使われていないことを確認
4. 成功ならこのhandoffへAFTERとして Run / Job / Artifact / 結果 / 結論 / 次の研究地点を追記。
5. 失敗なら、**ログを読んで原因を特定してから**修正。闇雲に再発火しない。
6. その後、必要なら1号艇v351の「THIRD close-margin時だけ4点化」監査へ進む。

## 次チャット用の短い開始文
`CHAT_HANDOFF_20260917_1HEAD_CURRENT_NEXT.md と最新GitHubを読んで、Run 35189567267 / Job 105098929876 の結果確認から続けて。9/1〜9/16 retrospective はユーザー許可済み、9/17結果はUNREAD維持。`

## 2026-09-17 15:27 JST — BEFORE / このチャットの作業開始
- 最新main / 本handoff / Run 35189567267 / Job 105098929876 を確認してから続行。
- 指定Run以外を重ねて発火しない。
- Run完了後は conclusion → logs → artifact → 指標/日別/レース別明細 → chronology guard の順で厳密確認する。
- 9/1〜9/16 retrospective の結果・払戻はユーザー許可済み。
- **9/17結果・払戻は取得・閲覧せず UNREAD 維持。**
- audit成功時は結果を本handoffへAFTER追記し、その後 `THIRD close-margin` 4点化監査の設計/実行へ進む。

## 2026-09-17 — AFTER / Run 35189567267 failure analysis + canonical fix
### Run結果
- Workflow: `audit-1head-v351-sep1-16`
- Run: **35189567267**
- Job: **105098929876**
- head SHA: `bf69cd3f48001109aaa3d103499726b98ee80651`
- conclusion: **failure**
- Step 5 `Rebuild chronology-safe September source through Sep16`: **success**
  - base_rows = 14760
  - added_sep_rows = 1752
  - total_rows = 16512
- Step 6 `Backtest existing v351 rolling path Sep1-16`: **failure**
- Artifact upload: skipped; Run artifact = **0件**

### 失敗原因
- 9/1の `prepare_1head_v351_live_cache.py` から `run_v323_1head_frozen_live_adapter.py` に入り、canonical frozen history cacheを読む時点で停止。
- exception:
  `FileNotFoundError: cache_v321_julaug_nonpristine_head_full.csv.gz`
- current v323が必要とするcanonical history inputは:
  - `cache_v321_julaug_nonpristine_head_full.csv.gz`
  - `cache_v321_julaug_nonpristine_slim.csv.gz`
- repo常駐ファイルではなく、workflow内で再生成する前提だった。

### commit履歴まで検索して正式な既存解決経路を確認
- commit `63bc1ef6550f71de121f1a91bf72148033ee8ea3`
  - message: `fix: prepare v321 frozen caches before rolling fit`
  - `.github/workflows/test-1head-v351-rolling-models.yml` に、rolling fit前に
    `python run_v321_1head_julaug_nonpristine_validation.py --stage prepare`
    を実行して `head_full` / `slim` を作る正式stepを追加した過去修正。
- commit `db3407f03d6199453195ee00c0a313493b5e1b6d`
  - v323 LIVE用のfull chronological head cacheをv321 prepareで保存する変更。
- commit `6aaa178499f5a9f1bad6342dee9d783025719959`
  - v323 LIVE workflowで `head_full` の存在チェックを正式追加。
- したがって今回も新しいロジックを発明せず、この既存canonical経路を再利用するのが正しい。

### 修正
`.github/workflows/audit-1head-v351-sep1-16.yml` に Step 5 とrolling backtestの間で以下を追加:
- `Prepare canonical v321 frozen history caches`
- `/usr/bin/time ... python run_v321_1head_julaug_nonpristine_validation.py --stage prepare`
- `test -s cache_v321_julaug_nonpristine_head_full.csv.gz`
- `test -s cache_v321_julaug_nonpristine_slim.csv.gz`

fix commit:
- **`a671089f6a26fb8aff49709ed54c78a69a5d8414`**
- message: `fix: prepare canonical v321 caches before Sep audit`
- workflowは `workflow_dispatch` only のため、このpushによる予期しないActions runは **0件確認済み**。

### chronology / 9/17 guard
- v321 prepareはJul/Augまでのfrozen causal history生成で、Septemberを含むと明示的にrejectする。
- Sep source builderはtarget 2026-09-17に対し cutoff=2026-09-16。
- retrospective loopはSep1〜Sep16のみ。
- **2026-09-17結果・払戻は未取得・未閲覧のまま。UNREAD維持。**

### 次の再開地点
- 新fix SHA `a671089f...` で `audit-1head-v351-sep1-16` を **新規workflow_dispatchで1回だけ発火**する。
- 旧Jobのrerunは旧SHA `bf69cd...` のworkflowを再実行してしまうため禁止。
- 現在のGitHub connectorには新規workflow_dispatch write actionが無いため、ユーザー側でGitHub Actions画面から手動発火が必要。
- 発火後は新Run ID / Job IDを確認し、成功時に logs → Artifact ID/name/content → summary/rows → 日別/レース別 → 9/17未使用guard の順で監査する。
- Sep auditが確定してから、次に1号艇v351 `THIRD close-margin` 4点化監査へ進む。
