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
