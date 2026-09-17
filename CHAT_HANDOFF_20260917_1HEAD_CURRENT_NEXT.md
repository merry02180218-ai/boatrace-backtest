# 1号艇 v351 現状引き継ぎ — 2026-09-17

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール
- 最新GitHubを最優先。作業開始前/完了後に引き継ぎを更新する。
- September 2026 の結果・払戻は絶対に読まない。`UNREAD`維持。
- historical hard guard: `race_code < 20260901`。
- LIVE/当日判定では `result_or_payout_used=False`, `chronology_guard=True`。
- 自動LIVE運用は廃止済み。ユーザーが「判別して」「候補出して」等と依頼した時だけ取得/判定する。
- HEAD学習特徴へ展示を直接追加しない。展示は post-ranking / ticket-rescue / live final correction のみ。

## 現行production
- profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- HEAD cutoff `.78`
- opponent core SECOND G2=.45 / THIRD G3=1.00
- formal baseline: 276R / 1号艇1着241=87.32% / exact3 131=47.46%（3点）
- 901Rはthreshold audit母集団であり最終購入276Rではない。
- formal schemas: `lap+turn+straight`, `lap+turn`, `half+turn+straight`, `base`。half系は桐生のみ。

## Wave17/18 固定救済研究
- cutoff未満 `[.350,.375)` の追加購入研究で、現行276Rとは別母集団。
- 固定ルール: BOAT3_STRONGER / candidate `1-3-5` / slot2 replacement。
- Wave18 May-Jun holdout 25R: baseline 5/25 -> fixed3 7/25、rescue2 damage0 net+2。
- ただし25R/救済2件と小標本、かつ仮説由来にMay/June探索の影響があるためproduction未採用。
- Wave18 Run `35125138250` / Job `104892212739` / Artifact `10458594916`。

## Wave19 — 本番276Rで固定救済ルールを直接監査
ユーザー指示: 「本番276Rで見たい」。

### 設計
- 現行production 276Rを正規production経路から再現する。
- `276R` と baseline exact3 `131` の二重hard guardを通してからのみ固定救済を適用。
- eligibilityは事前情報だけ。candidate `1-3-5`、3点維持。重複時はno-op。
- rescue / damage / net、月別等を監査。
- 結果を見てproductionを自動変更しない。

### 失敗履歴
1. Run `35129446541` / Job `104906510773`: Wave10前提ファイル名不一致で失敗。
2. Run `35133449401` / Job `104919825318`: Wave10低mass CSVを`.375以上`へ反転利用する誤設計によりproduction側日付集合が空、`max(days)`で失敗。
3. このためWave10低mass経路から切り離し、正式production経路で276Rを再構築するよう修正。
   - Wave19本体 commit `8d76cd8e68ad61888b01c5865e058a26c6ce44e9`
   - workflow commit `ba29e0902e606d36055046ae09a8c8c86e610151`
4. 最新確認 Run `35136277468` / Job `104929337412` も失敗。
   - 前処理は成功。
   - 本番276R監査で `cache_v321_julaug_second.pkl` が無く `FileNotFoundError`。
   - まだ `131/276 -> 救済後` の結果は出ていない。
   - このRunでもSeptember結果/払戻は未使用、production変更なし。

### Wave19 次の再開地点
- 不足している SECOND/THIRD cache を正式生成工程で作るよう workflow を修正する。
- その後Wave19を再発火。
- 成功時は必ず `276 / 131` sentinelを確認し、final exact3 / rescue / damage / netをArtifactまで確認する。
- AFTERとして実装commit、workflow commit、Run/Job/Artifact ID、結果、採否、次の再開地点をこの引き継ぎへ追記する。

## 2026-09-17 今日の事前候補 — 現在の未完了作業
ユーザーから「今日の事前候補出して」→「続けて」→「お願いします」と依頼あり。

### 確認済み
- manual LIVE workflow: `.github/workflows/manual-1head-v351-live.yml`
- これは `live_requests/1head_v351.json` のpushで単一レースを手動判定する入口。
- judge時は当日全場cache artifact `v351-1head-live-cache-${DATE}` を要求し、各race_code JSONと `v351_exhibition_train.csv` を使う。
- LIVE判定は結果/払戻を使わないguardあり。
- 9/15用cache generatorは削除されておらず `.github/workflows/prepare-1head-v351-live-cache-20260915.yml` としてmainに存在する。旧説明の「mainから外れている」は誤り。
- 9/15 PRE workflowはSeptember outcome rowsをrolling学習へ含める設計になっているため、今回の明示ルール（September結果UNREAD）には流用不可。

### 未完了
- 2026-09-17の「事前候補一覧」はまだユーザーへ出せていない。
- 推測や古い候補を出してはいけない。

### BEFORE — 2026-09-17 result-blind PRE/cache recovery
- 9/17専用PRE workflowとcache workflowを9/15実装から作る。
- PRE学習は `race_code < 20260901` hard guardで固定し、September outcome/result/payoutを一切読まない。
- 9/17当日カード/枠情報だけ取得し、S/A/B PRE候補を作る。
- cacheは現行production profileで `final_head_p`, `opp_mass`, `base_tickets` を作り、`result_or_payout_used=False`, `chronology_guard=True` を必須化。
- workflow成功後、Artifactから候補を締切順に一覧化する。

### 次の再開地点
1. 9/17 PRE/cache workflowを作成してpush発火。
2. PRE→cacheのRun/Job/Artifactを確認。
3. 場/R/締切/事前HEAD確率/opp_mass/事前3点を出す。
4. September結果/払戻はUNREAD維持。
5. AFTERを追記。

## LIVE運用の注意
- 事前候補に実進入・当日展示など未確定/締切直前情報を混ぜない。
- 展示後は展示タイム/ST/オリジナル展示/場補正を使うが、結果・払戻は使わない。
- 事前候補外レースもユーザーが指定すれば手動判別可能にしてある。
