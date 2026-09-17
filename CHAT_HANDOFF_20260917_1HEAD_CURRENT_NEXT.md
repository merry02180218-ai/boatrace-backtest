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
- 成功時 `out/rows.csv` / `out/summary.json` をartifact化。

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

## 2026-09-17 — BEFORE / Run 35195900311 failure修正
### Run確認
- Workflow: `audit-1head-v351-sep1-16`
- Run: **35195900311** (run #4)
- Job: **105118940286**
- head SHA: `921b575bc6ba4965ae384b1bbac4898c7f878cce`
- conclusion: **failure**
- chronology guard regression: success
- September source build: success
  - feature_rows 2443 / valid_result_rows 2430 / target_or_future_rows 0 / same_day_outcomes_read false
- canonical v321 frozen cache prepare: success
  - wall 267.06 sec / max RSS 3,323,812 KB
- Sep1 rolling target:通過
- Sep2 rolling target: failure
- artifact upload: skipped

### 今回の正確な失敗原因
`prepare_1head_v351_rolling_models.py` line 60:
`fn=v299.STRATEGIES[prod.TICKET_POLICY]`
で `KeyError: 'v320_HYBRID'`。

`onehead_production_profile.py` の正式値は `TICKET_POLICY = 'v320_HYBRID'` だが、`run_v299_1head_trifecta3_policy_search.py::STRATEGIES` のキーは `HYBRID` / `TOP2XTOP2` 等であり、`v320_HYBRID` キーは存在しない。

現行の正式LIVE finalizer `run_1head_v351_live_finalize.py` は明示的に
`v299.STRATEGIES['HYBRID'](...)`
を使っているため、rolling側も同じ semantics に揃えるのが正しい。

### これからやること
1. `prepare_1head_v351_rolling_models.py` のticket policy解決をproduction名 `v320_HYBRID` → v299 strategy `HYBRID` に安全に対応させる。
2. production profileが想定外のpolicy名ならsilent fallbackせず例外にする。
3. 高コストActionsを回す前に、profile policyが解決でき、LIVE finalizerと同じ3-ticket orderingになる軽量回帰チェックをworkflowへ追加する。
4. triggerが `workflow_dispatch` only のままか再確認する。
5. 修正commit後、旧Runのrerunはせず **新しいworkflow_dispatchを1回だけ**発火する。
6. 9/17 result/payoutは引き続き **UNREAD**。

次の再開地点: 上記ticket policy mapping修正と回帰チェックを実装・commitし、その結果をAFTERとして本handoffへ追記する。