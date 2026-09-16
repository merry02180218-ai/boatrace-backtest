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

## Wave9 — 実行済み
- strict fold-local LOOを実行。桐生half追加は改善せず、多くの設定で悪化。`SHARED_PLUS_HALF` をproductionへ入れない方向。
- production変更なし、September outcomes UNREAD。

## 2026-09-16 daily PRE
- 正式取得は BoatRace Biyori。`fetch_1head_v351_biyori_cards.py --date YYYYMMDD --out race_cards.csv`。
- `race_shusso.php` + `request_race_shusso_detail_v4.php`、retry/backoff、完全12Rの場だけ採用。
- 結果・払戻・オッズは取得しない。`result_or_payout_used=False` / `chronology_guard=True`。
- Biyori -> v321 causal prepare -> `prepare_1head_v351_live_cache.py` -> PRE summary -> Actions artifact。
- 2026-09-16基準Run `35034996720` / Job `104601998526` / Artifact `10423825328` / 13場156R / SHA256 `bb1361755137655b8abd04d0ee09079b7a4f98910e64f7724bc7ec91b86fffec`。

## opponent mass `.375` 独立監査
### BEFORE
- HEAD>=.78を通過したhistorical raceだけで `OPPONENT_MASS_MIN=.375` の有効性を監査する。
- `race_code < 20260901` hard guard。September 2026 outcomes/payoutsは `UNREAD` 維持。
- 比較: `.30/.325/.35/.375/.40/.425/.45`、mass帯別R/HEAD/exact3、月別。production定数 `.375` は監査完了まで変更しない。
- 初回Run `35037266265` / Job `104609063946` はworkflow自体successだが、mass監査stepは `cache_v321_julaug_nonpristine_slim.csv.gz` 不在で結果未生成。
- **これから行うこと**: `.github/workflows/backtest.yml` のmass監査前に `run_v321_1head_julaug_nonpristine_validation.py --stage prepare` を追加して必要cacheをfresh生成し、その後mass監査を実行する。fresh RunのRun/Job/Artifact IDと閾値結果を確認してAFTERへ記録する。
- cache生成・監査ともSeptember結果を読まないことを確認し、production変更は結果確認後に判断する。

## BEFORE: 手動即時LIVE入口の復旧 — 2026-09-16
- ユーザーの「○○R判別して」だけで、こちらからGitHubへtrigger fileをpushして任意Rを即時発火できる入口を復旧する。
- レース時刻controllerの自動運用は復活させない。明示要求時だけ発火する。
- triggerには `race_code` と締切JSTを記録し、そのpushで専用workflowを起動する。
- workflowは当日 `v351-1head-live-cache-YYYYMMDD` artifactを取得し、PRE候補外でも対象JSONを使用する。
- `probe_1head_v351_boatcast_exhibition.py` -> `run_1head_v351_live_exhibition_gate.py` -> merge -> `run_1head_v351_live_finalize.py` を実行し、PASS/DROPと3連単3点をartifactへ残す。
- 締切前のみ。結果・払戻・オッズは読まない。`result_or_payout_used=False` / `chronology_guard=True` を維持。
- production profile / HEAD cutoff / opponent mass / G2/G3 / ticket policy は変更しない。
- 実装後はfresh Actions Runで入口を監査し、Run/Job/Artifact ID・結論・次の再開地点をAFTERへ記録する。
