# 1号艇 v351 手動LIVE 引き継ぎ — 2026-09-15

## 重要ルール
- September 2026結果・払戻は `UNREAD` 維持。研究では `race_code < 20260901` hard guard。
- production profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`。
- HEAD cutoff `.78`、opponent core SECOND G2=.45 / THIRD G3=1.00。
- LIVEでは結果・払戻を絶対に使用しない。`result_or_payout_used=False` / `chronology_guard=True`。
- `half`（半周ラップ）は桐生(JCD01)だけ。`half+turn+straight` は桐生専用schema。
- 正式schema: `lap+turn+straight`, `lap+turn`, `half+turn+straight`, `base`。`turn+straight`は保留。

## exact3〜Wave6 要約
- exact3分解: EXACT3_HIT=106 / OPPONENT_PAIR_MISS=115 / ORDER_MISS=14。主因は相手2艇選択。
- Wave3: 235R、first pair KEEP67 / REPLACE_ONE144 / REPLACE_BOTH24。one-replace方向を研究。
- Wave4 June frozen: 71R、baseline22/71=30.99%。th=-0.05で24/71=33.80%、rescue5/damage3。production変更なし。
- Wave5: 主力lap+turn+straightはrescue3/damage3で差引0。
- Wave6場別: 浜名湖+2、びわこ-2、常滑0、住之江+1、徳山+1。小標本でproduction変更なし。

## Wave7 桐生×2号艇監査 — 完了
- Run `34997552243` / Job `104477496635` / Artifact `10408383148` / success。actual pairに2号艇8/15、現行first pairは2を15/15含む。false keep2=7。

## Wave8 桐生2号艇 KEEP/DROP特徴監査 — 完了
- Run `34999916439` / Job `104485468453` / Artifact `10409258569` / success。
- Artifact SHA256 `bd5241371d62bc7d2f19e7bb123e4d1144837f34729df06e13d09cce897cbe73`。
- KIRYU_R=15 / KEEP2=8 / DROP2=7。half単独分離は弱く、複合guardをLOO評価へ。

## Wave9 — 実行中
- strict fold-local LOO実装済み。production変更なし、September outcomes UNREAD。

## 2026-09-16 03:00 daily failure / recovery
- Run `35006130791` / initial Job `104506215489` failure、retry Job `104583289886` failure。
- failure step: `Resolve JST date and latest rolling cards`。
- exact cause: `PRE_SOURCE_NOT_READY: rolling race cards for 20260916 are not available at 03:00 JST` / exit 30。
- 03:00 workflowが rolling artifactを必須依存にしている設計欠陥。

### BoatRace Biyori daily recovery
- Biyori direct PRE取得へ切替済み。Run `35032210723` / Job `104593063750` success / Artifact `10421874851`。
- 20260916は10場120Rをcache化。`result_or_payout_used=False` / `chronology_guard=True`。
- JCD04/JCD05/JCD07は各1RのHTTP timeoutにより11/12となり、場単位で除外された。

### BEFORE: recover missing Biyori races
- 目的: JCD04/JCD05/JCD07の欠落36Rを再取得し、当日開催13場156Rの完全gridを作る。
- Biyori detail APIの各race取得にretry/backoffを追加し、一時的timeoutで場全体を捨てないようにする。
- fresh workflowで `BIYORI_CARDS ... races=156`、`all_race_cache_R=156`、artifact生成まで確認する。
- 結果・払戻・オッズは取得禁止。`result_or_payout_used=False` / `chronology_guard=True`、September outcomes `UNREAD` 維持。

### AFTER: 正式な当日PRE取得手順 — 2026-09-16確定
- **今後の1号艇v351当日PREはこの方式を標準とする。** 03:00時点でrolling artifactを待つ方式には戻さない。
- データ源は **ボートレース日和 (BoatRace Biyori)**。`fetch_1head_v351_biyori_cards.py --date YYYYMMDD --out race_cards.csv` で当日出走表を直接取得する。
- 取得は `race_shusso.php` で開催/CSRF情報を得て、`request_race_shusso_detail_v4.php` の詳細APIから各場・各Rの事前情報を取得する。簡易HTMLだけをPREへ流さない。
- 各race取得は **retry/backoff** を使う。一時的なHTTP timeoutで11/12になった場を丸ごと捨てず、12R揃うまで再取得する。完全12Rの場だけ当日gridへ採用する。
- 取得対象は事前に確定している出走/選手/モーター等のPRE情報のみ。結果・払戻・オッズは取得・使用しない。必須guardは `result_or_payout_used=False` / `chronology_guard=True`。
- Biyoriカード取得後、`run_v321_1head_julaug_nonpristine_validation.py --stage prepare` でcausal preparationを作成し、続いて `prepare_1head_v351_live_cache.py --date YYYY-MM-DD --cards race_cards.csv --out ...` で全Rのv351 cacheを作る。
- 最後に各race JSONから `race_code / jcd / race / pre_class / final_head_p / base_tickets` を集約してPRE summaryを作成し、Actions artifactとして保存する。
- 2026-09-16の最終検証: Run `35034996720` / Job `104601998526` / **success**。
- Biyori取得結果: JCD `04,05,07,08,09,11,12,13,14,18,19,22,23` の **13場156R**。ログ `BIYORI_CARDS date=20260916 ... races=156 result_or_payout_used=False chronology_guard=True` を確認。
- v351 cache: `all_race_cache_R=156` / `training_cutoff=2026-09-15` / production profile `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`。
- Artifact `10423825328` (`v351-1head-live-cache-20260916`) / SHA256 `bb1361755137655b8abd04d0ee09079b7a4f98910e64f7724bc7ec91b86fffec`。
- この成功Runを、今後の「ボートレース日和から当日カード→causal prepare→全R cache→PRE summary」の再現基準とする。
- September 2026の結果・払戻は引き続き `UNREAD`。今回の取得・cache作成でも使用していない。

### 次の再開地点
- 日次PRE/LIVEでは上記Biyori方式を使用する。ユーザーから特定Rの「判別して」が来た場合、事前候補外でも当該race cacheを起点に展示取得→直前判定を即時実行する。
- 研究側はWave9の結果抽出へ戻る。production変更はWave9監査完了まで行わない。

## BEFORE: opponent mass `.375` 独立監査
- ユーザー指示により、HEAD>=.78を通過したレースを対象に `OPPONENT_MASS_MIN=.375` が本当に有効なgateか監査する。
- 現production定数 `.375` は変更せず、まず historical `race_code < 20260901` のみで評価する。September outcomes/payoutsは `UNREAD` 維持。
- 比較する内容: mass帯別のR数 / HEAD的中率 / exact3的中率、`.375`以上 vs 未満、閾値grid（少なくとも .30/.325/.35/.375/.40/.425/.45）、`.375`で落としたレースのHEAD/exact3、可能なら月別・schema別も確認する。
- 特に今日の津3R/鳴門4Rのような `HEAD>=.78 & mass<.375` 型を捨てることにhistoricalな根拠があるかを見る。
- 閾値選択と評価を同じ標本で行う場合は探索結果と明記し、production変更は独立holdout確認まで行わない。
