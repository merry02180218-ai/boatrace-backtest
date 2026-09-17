# 1号艇 v351 現状引き継ぎ — 2026-09-17

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール / ユーザー運用方針
- 最新GitHub + 本handoffを、古いチャット/記憶より必ず優先する。
- 作業開始前に「これからやること」、完了後に結果・commit SHA・Actions Run/Job/Artifact・結論・次の再開地点を本handoffへ記録する。
- 失敗時は logs / artifact / existing code / commit履歴を先に確認し、盲目的にrerunしない。
- 未確認の完了/成功を断言しない。
- 自動LIVEより、ユーザーが「判別して」と言った時の手動取得/判定を優先。
- HEAD学習特徴へ展示を直接追加しない。展示は post-ranking / ticket-rescue / live final correction のみ。

## September結果の扱い
- retrospective評価に限り **2026-09-01〜09-16** の結果・払戻は読み取り許可済み。
- **2026-09-17当日結果・払戻は絶対に読まない。UNREAD維持。**
- 9/17は pre-race / exhibition のみ使用可。

## 現行1号艇 production
Profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- HEAD v308 / cutoff 0.78
- opponent mass min 0.375
- SECOND `v317_OUTER_L2_1`
- THIRD `v318_DROPSTART_T0.1`
- ticket `v320_HYBRID`, alpha 0.70, 基本3点
- exhibition `v332_ATTACK_ENV_SOFT_V345_ATTACKCORE`, env w=.10 / q=.65
- opponent core SECOND G2=.45 / THIRD G3=1.00
- formal historical baseline: **276R / 1号艇頭241R=87.32% / exact3 131R=47.46%**

## 9/17 formal candidates（結果UNREAD）
Canonical cache Artifact **10477251012** / Run **35170926144** / head `d951448ff9e6b397454fff796cf70bbf0c08bfcf`
1. 平和島12R `202609170412`: p=0.7901582366 / opp_mass=0.4212344809 / `1-4-2;1-4-5;1-2-4`
2. 尼崎6R `202609171306`: p=0.8301538300 / opp_mass=0.3867473972 / PRE `1-2-4;1-2-3;1-4-2`; safe replay final DROP, Run **35181006387** / Job **105072935543** / Artifact **10480421315**
3. 下関4R `202609171904`: p=0.8105814573 / opp_mass=0.4090498291 / `1-2-5;1-2-3;1-3-2`

## Sep1-16 retrospective 確定
Workflow `.github/workflows/audit-1head-v351-sep1-16.yml`
Run **35201237033** / aggregate Job **105145377812** / Artifact **10489485417**
- 30R
- 1号艇1着 22/30 = 73.33%
- exact3 12/30 = 40.00%
- stake 9,000円
- return 8,780円
- ROI 97.56%
- profit -220円
- `today_20260917_used=false`
- `chronology_guard=true`
- 20260917 race_code 0件
- **9/17 result/payout UNREAD維持**

---

# 現在の作業: THIRD close-margin時だけ4点化
ユーザー指示: **「3着候補が僅差のときだけ4点化」**

## 1号艇用の確定semantics
現行 `v320_HYBRID` の3点は保持する。HYBRIDは:
- ticket #1 = joint最上位 `(SECOND=s, THIRD rank1)`
- ticket #2 = 同じSECOND=sの次点 `(s, THIRD rank2)`
- ticket #3 = 別SECOND枝の最上位

したがって4点化は、主SECOND枝 `s` の条件付きTHIRDについて
`P(rank2|s) - P(rank3|s) <= threshold`
の時だけ、`(s, THIRD rank3)` を**4点目として1点だけ追加**する。
- baseline3点は置換しない
- expanded raceは必ずexactly 4 tickets
- threshold比較: **.05 / .10 / .15**
- 4号艇v283の考え方を参照するが、1号艇HYBRID構造に合わせた実装

参考: 4号艇production close-margin commit
- `376c636839af499821244ca660e382a43a16d644`
- 4号艇はTHIRD rank2-rank3差 <=0.10をproduction採用済み

## BEFORE記録
handoff commit:
- `4babb2539385fc926723e5a164f361ad7a28c5c8`
- message `handoff: start 1head third close-margin audit`

## 監査実装
script:
- `run_v351_1head_third_close_margin_audit.py`
- commit **`80e8dccb248c768a5f2116705ee3155fb1597e42`**
- message `audit: add v351 third close-margin 4-ticket analysis`

workflow:
- `.github/workflows/v351-1head-third-close-margin-audit.yml`
- commit **`752e1e0737dbab811d4b86789e0f1fa5a6e4134f`**
- message `workflow: run v351 third close-margin audit`

監査scriptの重要guard:
- formal v351母集団を `legacy.current_selected()` から再構築
- opponent core調整後にHYBRID top3を再生成
- payoutを読む前にformal sentinelを強制確認
- expected: PASS=276 / HEAD=241 / EXACT3=131
- race identity SHA / ticket identity SHAもproduction定数と一致必須
- Feb-Jun sentinel: 220R / exact3 107
- Jul-Aug support-only sentinel: 56R / exact3 24
- 9/17以降のpayout/result requestはhard reject
- thresholdごとに expanded_R / added tickets / exact hit gain / stake / return / ROI / monthly を出力

## Run #1 — 失敗、原因確定
Workflow: `v351 1-head THIRD close-margin audit`
Run **35217755431** / run #1 / head **`752e1e0737dbab811d4b86789e0f1fa5a6e4134f`**
Conclusion: **failure**

Jobs:
- prepare **105190185352** — success
- third **105191627528** — success
- base-third **105191627562** — success
- second **105191627671** — success
- audit **105193097452** — failure

Artifacts generated before audit failure:
- **10495950804** `v351-third-margin-prepare-35217755431`
- **10496156494** `v351-third-margin-second-35217755431`
- **10495886548** `v351-third-margin-base-third-35217755431`
- **10496506040** `v351-third-margin-third-35217755431`
- final audit artifactは未生成

### 重要: formal 276R sentinelは通過済み
失敗位置は payout join loop 内 `_payout()`。コード上、PASS/HEAD/EXACT3・identity SHA・Feb-Jun/Jul-Aug sentinel確認を通過した後にしか到達しないため、**Run #1は正式276R / 241頭 / 131 exact3母集団を再現した上で払戻JOINまで進んでいる**。

### 失敗原因
Audit log:
`RuntimeError: missing payout row for 202602102303`

BoatraceCSV `data/results/payouts/2026/02/10.csv` には
- 23場01R,02R,04R... はある
- **`202602102303` (23場03R) だけ欠損**
一方 `data/results/realtime/2026/02/10.csv` には `202602102303` が存在し、結果は `1-3-4` と確認できる。
つまりモデル/母集団の失敗ではなく、**BoatraceCSV historical payout row欠損**が原因。

## 払戻fallback修正
最新main commit:
- **`eeb7e8a020e1f0c725a10770bc01db334a8a24e6`**
- message `fix: fallback to official payouts for v351 margin audit`

変更:
- BoatraceCSV payoutをprimaryのまま維持
- BoatraceCSVで有効なhistorical raceのpayout rowが欠損した場合のみ、BOAT RACE公式 `resultlist` をfallback
- official fallbackでも `day >= 20260917` はhard reject
- official fallback race codeを `official_fallback_codes` としてresultに記録
- BoatraceCSV + official双方に無ければfail closed
- comboがactualと不一致、payout<=0もfail closed
- **9/17 result/payoutは読まない**

---

# 現在走っているRun — 次チャットはここから
修正版pushで自動発火済み:
- Workflow: `v351 1-head THIRD close-margin audit`
- **Run 35221732112**
- run #2
- head SHA **`eeb7e8a020e1f0c725a10770bc01db334a8a24e6`**
- snapshot時点: **in_progress**

snapshot job状態:
- prepare Job **105203286991** — success
- base-third Job **105204954293** — success
- second Job **105204954402** — success
- third Job **105204954418** — success
- audit Job **105206482047** — queued

## 次の再開地点（最優先）
次チャットでは最初に最新GitHub + 本handoffを読み、**Run 35221732112 / Job 105206482047 の結果確認から再開**する。

成功した場合:
1. final audit Artifact IDを取得
2. `result.json`, `summary.csv`, `monthly.csv`, `rows.csv` を確認
3. formal sentinelが **276 / 241 / 131** か再確認
4. `.05 / .10 / .15` それぞれについて以下を比較
   - expanded_R
   - added_tickets
   - exact3_hits / gain_hits
   - hit rate
   - stake_yen
   - return_yen
   - profit_yen
   - ROI
   - 月別安定性
5. `official_fallback_R` / `official_fallback_codes` を確認
6. `TODAY_20260917_RESULT_OR_PAYOUT_USED=false` / September outcomes unread を確認
7. 監査結果だけで勝手にproduction昇格せず、結果をユーザーへ詳しく報告
8. AFTERとしてRun/Job/Artifact/metrics/結論/次再開地点を本handoffへ追記

失敗した場合:
- rerun前に Job **105206482047** のlogsを読む
- payout fallback parserなのか別のmissing rowなのかを特定
- formal sentinel driftなら修正せず原因調査を優先

## 現時点のproduction状態
- **v351 productionはまだ3点のまま。4点化は未昇格。**
- `.05/.10/.15` の正式監査結果待ち。
- **2026-09-17 result/payoutはUNREAD。**
