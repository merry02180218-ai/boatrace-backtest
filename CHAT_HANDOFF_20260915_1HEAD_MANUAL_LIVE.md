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
- 実装 commit `b5d1b0a...`、workflow commit `93157a13311da5e1e5900e64896f444175ee2c62`。
- Run `34997552243` / Job `104477496635` / Artifact `10408383148` / success。
- Artifact SHA256 `6ebddd3f56e3c51f3c042564d2d509d082af86c32e315b903ea30ebdce4214f1`。
- 桐生 half+turn+straight historical 15R。
- actual opponent pairに2号艇: 8/15=53.33%。2着3R、3着5R。
- current first pairは2号艇を15/15=100%含む。actual2なのに現行が2を落としたケース=0。
- 一方、actualに2がいないのにcurrent first pairが2を含むケース=7。
- current first pair完全一致=4/15=26.67%。3-ticket unionも2号艇15/15=100%。
- 結論: 桐生で2号艇をさらに優遇する必要はない。むしろ2を残す8Rと外すべき7Rを半周ラップ/ST/ターン/直線で判別する研究が必要。
- `SEPTEMBER_OUTCOMES_USED False` / `PRODUCTION_CHANGED False`。

## 次作業開始 — Wave8 桐生2号艇 KEEP/DROP guard
1. 桐生15Rを対象に、actual_has_2=1（KEEP2）8Rと actual_has_2=0（DROP2候補）7Rを比較する。
2. 2号艇自身の補正展示 `ex`, `st`, 半周 `half`, turn, straight と場内rankを抽出する。
3. 2号艇と他艇（特に現行pair相方・最有力outsider）の差分を作り、KEEP2/DROP2を分離する方向を探る。
4. 15Rだけへの過学習を避けるため、まず単変量の方向・閾値候補とleave-one-out/簡易walk-forward相当を確認し、productionには入れない。
5. Wave4に残るtrain+June median imputation leakageも別途修正対象。Wave8の結論と混同しない。
6. September 2026結果・払戻は絶対に読まない。production変更なし。
