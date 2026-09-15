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

## 2026-09-16 03:00 daily failure — BEFORE recovery
- Run `35006130791` / Job `104506215489` failure。
- failure step: `Resolve JST date and latest rolling cards`。
- exact cause: `PRE_SOURCE_NOT_READY: rolling race cards for 20260916 are not available at 03:00 JST` / exit 30。
- 03:00 workflowが `v351-1head-live-pre-sab-$DATE-rolling` artifactを必須依存にしている設計欠陥が顕在化。
- これから、rolling artifactが無い時も当日カードを取得/構築してdaily all-R cacheを作れるfallbackを実装し、fresh runで復旧確認する。
- LIVE chronology guard維持。結果・払戻は使用しない。September 2026 outcomesはUNREAD維持。
