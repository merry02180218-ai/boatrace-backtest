# 1号艇 v351 現状引き継ぎ — 2026-09-17

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール / ユーザー運用方針
- 最新GitHub + 最新引き継ぎを、古いチャット/記憶より必ず優先する。
- 作業開始前に「これからやること」を本handoffへ記録し、完了後に結果・commit SHA・Actions Run/Job/Artifact・結論・次の再開地点を追記する。
- workflowを書き換える前にtriggerを確認する。不要なpush発火、noop commit、新規workflow乱立は禁止。
- 1回発火→確認→次。失敗時は logs / artifact / existing code / commit履歴を確認してから修正する。
- 未確認の完了/発火/結果を断言しない。
- 自動LIVEより、ユーザーが「判別して」と言った時の手動取得/判定を優先する。
- HEAD学習特徴へ展示を直接追加しない。展示は post-ranking / ticket-rescue / live final correction のみ。

## September結果の扱い
- 今回のretrospectiveに限り **2026-09-01〜09-16** の確定結果・払戻を評価用として読むことをユーザー許可済み。
- **2026-09-17当日結果・払戻は絶対に読まない。UNREAD維持。**
- 9/17 LIVE/判定は pre-race / exhibition のみ使用可。

## 現行1号艇 production
Profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- HEAD: v308 / cutoff 0.78
- opponent mass min: 0.375
- SECOND: v317_OUTER_L2_1
- THIRD: v318_DROPSTART_T0.1
- ticket: `v320_HYBRID`, alpha 0.70, 基本3点
- exhibition: v332_ATTACK_ENV_SOFT_V345_ATTACKCORE, env w=.10 / q=.65
- opponent core: SECOND G2=.45 / THIRD G3=1.00
- formal historical baseline: 276R / 1頭241R=87.32% / exact3 131R=47.46%

## 9/17 formal candidates（結果はUNREAD）
Canonical cache Artifact 10477251012 / Run 35170926144 / head SHA `d951448ff9e6b397454fff796cf70bbf0c08bfcf`。
1. 平和島12R `202609170412`: p=0.7901582366 / opp_mass=0.4212344809 / `1-4-2;1-4-5;1-2-4`
2. 尼崎6R `202609171306`: p=0.8301538300 / opp_mass=0.3867473972 / PRE `1-2-4;1-2-3;1-4-2`; safe post-deadline replay final DROP, Run 35181006387 / Job 105072935543 / Artifact 10480421315
3. 下関4R `202609171904`: p=0.8105814573 / opp_mass=0.4090498291 / `1-2-5;1-2-3;1-3-2`

## 次研究候補
Sep audit確定後、1号艇v351の `THIRD close-margin` 時だけ4点化を formal 276Rで監査。
- 4号艇v283では THIRD差<=0.10 をproduction採用済み（commit `376c636839af499821244ca660e382a43a16d644`）。
- 1号艇は閾値 .05/.10/.15、的中増、追加点数、ROI、月別安定性を比較する。
- 先に現行ticket ranking semanticsを確認し、4号艇実装をそのまま移植しない。

## Sep1-16 retrospective 監査経路
Workflow: `.github/workflows/audit-1head-v351-sep1-16.yml`
- `workflow_dispatch` only。
- `build_1head_september_training_source.py --target-date 2026-09-17 --start-date 2026-09-01`
- canonical Jul/Aug v321 frozen cacheを `run_v321_1head_julaug_nonpristine_validation.py --stage prepare` で生成。
- Sep1はfrozen production history、Sep2+は prior-day September rowsのみでrolling。
- predictions/exhibition pathを先に作り、その後9/1〜9/16 results/payoutsを評価JOIN。
- 成功時 `out/rows.csv` / `out/daily.csv` / `out/summary.json` をartifact化。

## これまでの失敗と修正
### 1) Run 35189567267 / Job 105098929876
- Sep source build成功。
- `cache_v321_julaug_nonpristine_head_full.csv.gz` 不足で失敗。
- canonical v321 prepare stepを追加。
- fix commit `a671089f6a26fb8aff49709ed54c78a69a5d8414`。

### 2) Run 35190832903 / Job 105102822607
- source build / v321 cache prepare成功。
- 9/2 rollingで prior-day 9/1 rowを同月という理由だけで chronology leak扱いして失敗。
- `run_v323_1head_frozen_live_adapter.py` のrolling guardを日付単位に修正。
- rolling=Trueは history date < target_date のみ許可、same-day/futureをreject。
- strict modeは従来の月単位guard維持。
- code fix `32e77ff2c8317dc10947118bc915b36b6ee00eb4`。
- workflow回帰チェック追加 `83d08cdb6209d2ca2384d55609ef70dc55f8b772`。
- handoff update `921b575bc6ba4965ae384b1bbac4898c7f878cce`。

### 3) Run 35195900311 / Job 105118940286
- head SHA `921b575bc6ba4965ae384b1bbac4898c7f878cce`
- chronology guard regression: success
- September source build: success
  - feature_rows 2443 / valid_result_rows 2430 / target_or_future_rows 0 / same_day_outcomes_read false
- canonical v321 frozen cache prepare: success
  - wall 267.06 sec / max RSS 3,323,812 KB
- Sep1 rolling target:通過
- Sep2 rolling target: failure
- artifact upload: skipped
- failure: `prepare_1head_v351_rolling_models.py` が `v299.STRATEGIES[prod.TICKET_POLICY]` を直接参照し、profile値 `v320_HYBRID` に対して `KeyError`。
- `v299.STRATEGIES` 側の正式strategy keyは `HYBRID`。正式LIVE finalizerも `STRATEGIES['HYBRID']` を使用している。

## 2026-09-17 — AFTER / ticket policy fix + runtime parallelization
### ticket policy修正
`prepare_1head_v351_rolling_models.py` に `resolve_ticket_strategy()` を追加。
- `v320_HYBRID` → `HYBRID`
- v299に既存のstrategy名ならそのまま使用
- 未知のproduction policy名はsilent fallbackせず `RuntimeError`
- rolling metaへ `ticket_policy` / `ticket_strategy` を保存

commit:
- **`cb2b35b535f115189f2e80890983bbc5e65359c6`**
- message: `fix: resolve v351 rolling ticket policy name`

### 実データsmoke test
上記code fileは既存 `.github/workflows/test-1head-v351-rolling-models.yml` のpush対象だったため、commit時に既存rollingテストが自動発火した。
- Run: **35199667608**
- Job: **105131123899**
- head SHA: `cb2b35b535f115189f2e80890983bbc5e65359c6`
- conclusion: **success**
- canonical v321 prep: success
- `Train rolling v308 v317 v318`: **success**
- log: `ROLLING_MODELS_OK`
- target: 2026-09-15 / training_cutoff: 2026-09-14
- September rows: 2118
- head/opponent history rows: 47221 / 47221
- SECOND features: 277 / THIRD features: 221
- `ticket_policy = v320_HYBRID`
- `ticket_strategy = HYBRID`
- `same_day_outcomes_read = False`
- `target_or_future_rows = 0`
- `chronology_guard = True`
- races output: **153**
- rolling build: 512.7 sec / wall 514.1 sec
- Artifact: **10488126888** `v351-1head-rolling-models-20260915`
- 3-ticket assertionも全raceで通過。

これにより Run 35195900311 の `KeyError: v320_HYBRID` は実データrolling経路で解消確認済み。

### 長時間問題への修正
Run 35195900311ではSep1〜Sep2だけでもStep 8が非常に重く、16日直列では90分timeoutリスクが高かったため、同時に監査をchunk並列化した。

新script:
- `audit_1head_v351_sep_chunk.py`
- commit **`57fe01ddd37c6383852c93ef4b11cca69140f7e2`**
- 2日単位でrolling/backtestを独立実行。
- chunk開始日前までST stateを再構築し、chunk内は日次更新。
- Sep1のみfrozen production history、Sep2+はprior-day Sep history。
- 9/17以降をhard reject。
- rolling meta chronology / ticket_strategy=HYBRID / 3点uniqueを検証。

workflow parallelization:
- commit **`dee017c223692825e2f3f572daec7da9f0aa60bb`**
- prepare job: chronology regression + ticket policy軽量回帰 + Sep source rebuild + v321 cacheを1回だけ生成・artifact化。
- backtest job: 8並列matrix
  - Sep1-2
  - Sep3-4
  - Sep5-6
  - Sep7-8
  - Sep9-10
  - Sep11-12
  - Sep13-14
  - Sep15-16
- aggregate job: 8 chunkを統合し `rows.csv` / `daily.csv` / `summary.json` を作る。
- aggregateで `20260917` や範囲外race_codeをhard reject。
- workflow triggerは **`workflow_dispatch` only** のまま。

## 2026-09-17 — AFTER / Sep1-16 retrospective SUCCESS
### Run
- Workflow: `audit-1head-v351-sep1-16`
- Run: **35201237033**
- run number: 5
- head SHA: **`08eccc05af82c5d49cd11520732a8fba94f7ca7d`**
- prepare Job: **105136223811** — success
- backtest jobs 8本 — **全success**
- aggregate Job: **105145377812** — success
- final Artifact: **10489485417** `audit-v351-sep1-16-35201237033`
- final artifact digest: `sha256:2680f894bcb79a254aba06b74e9b4d6e93109f74de5f9039ef7230537d522430`

### 確定結果（2026-09-01〜09-16）
- 購入対象: **30R**
- 1号艇1着: **22R / 30R = 73.33%**
- 3連単3点 exact hit: **12R / 30R = 40.00%**
- 投資: **9,000円**（各R 3点×100円）
- 払戻: **8,780円**
- ROI: **97.56%**
- 損益: **-220円**

formal historical baseline 276Rとの単純比較:
- 1頭率: 87.32% → Sep1-16 73.33%（-13.99pt）
- exact3率: 47.46% → Sep1-16 40.00%（-7.46pt）
- ただしSep監査は30Rの小標本なので、この16日間だけでproductionを変更しない。

### 日別購入があった日
- 9/1: 1R / head1 1 / exact3 1 / return 780 / ROI 260%
- 9/3: 2R / 2 / 2 / 930 / 155%
- 9/5: 4R / 2 / 0 / 0 / 0%
- 9/6: 5R / 5 / 4 / 2,670 / 178%
- 9/7: 2R / 0 / 0 / 0 / 0%
- 9/8: 2R / 2 / 1 / 480 / 80%
- 9/9: 2R / 2 / 0 / 0 / 0%
- 9/11: 3R / 3 / 3 / 2,210 / 245.56%
- 9/12: 2R / 1 / 0 / 0 / 0%
- 9/13: 2R / 2 / 1 / 1,710 / 285%
- 9/14: 1R / 0 / 0 / 0 / 0%
- 9/15: 2R / 1 / 0 / 0 / 0%
- 9/16: 2R / 1 / 0 / 0 / 0%

### chronology / 9/17 guard verification
- final `summary.json`: `today_20260917_used = false`
- `chronology_guard = true`
- 8 chunk files全部aggregate成功。
- final `rows.csv` は30Rすべて `20260901`〜`20260916` のrace_code。
- `20260917...` race_codeは **0件**。
- **9/17 result/payoutはUNREAD維持。**

### 次の再開地点
- Sep auditは確定完了。
- 次は予定どおり、1号艇v351の **THIRD close-margin時だけ4点化** をformal 276Rで監査。
- 先に現行v351 ticket ranking semanticsを厳密確認。
- threshold候補 `.05 / .10 / .15` を比較し、追加4点化R数、exact hit増分、総投資、払戻、ROI、月別安定性を評価する。
- 4号艇v283の実装をそのまま移植せず、1号艇のSECOND/THIRD条件付き確率構造に合わせる。
