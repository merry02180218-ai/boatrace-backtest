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
- 桐生 half+turn+straight historical 15R。actual pairに2号艇 8/15=53.33%、現行first pairは2を15/15含む。actual2なのに落とした=0、false keep2=7。first pair完全一致4/15=26.67%。
- 結論: 2号艇をさらに優遇せず、KEEP2/DROP2判別を研究。

## Wave8 桐生2号艇 KEEP/DROP特徴監査 — 完了
- Run `34999916439` / Job `104485468453` / Artifact `10409258569` / success。
- Artifact SHA256 `bd5241371d62bc7d2f19e7bb123e4d1144837f34729df06e13d09cce897cbe73`。
- checkout SHA `5685c287b702a16ddd32222ad921e5a9faedd3fa`。
- KIRYU_R=15 / KEEP2=8 / DROP2=7。
- half: KEEP mean .200 / DROP .257、rank 1.875 / 2.000。半周単独の分離は弱い。
- ex: KEEP mean .500 / DROP .229、ex_vs_best .500 / .171。単純な「展示が良いほどKEEP」ではなく逆方向を含み、単独閾値は危険。
- turn: KEEP .375 / DROP .286、ST: KEEP .525 / DROP .571、straight: KEEP .400 / DROP .429。
- 結論: 単一特徴guardではなく、展示×半周×turn×ST等の複合guardをLOOで評価する。15Rのためproduction昇格はしない。
- `SEPTEMBER_OUTCOMES_USED False` / `PRODUCTION_CHANGED False`。

## 次作業開始 — Wave9 桐生2号艇複合guard LOO
1. Wave8の15Rだけを用い、leave-one-outでKEEP2/DROP2を予測する複合guardを検証する。
2. まず shared features（ex/st/turn/straight/orig_avg）と、half追加版を同じLOO条件で比較し、halfの増分価値を確認する。
3. 標準化・欠損補完は各LOO train foldだけでfitし、held-out raceの情報を前処理に使わない。
4. accuracyだけでなく、DROP2 precision/recall、KEEP2誤DROP数を出す。現行は全KEEPなので、false drop damageを特に重視する。
5. 15R小標本につき診断研究のみ。production変更なし。
6. September 2026結果・払戻は絶対に読まない。
