# 1号艇 v351 手動LIVE 引き継ぎ — 2026-09-15

## 今回の作業開始記録 — 2026-09-16
- September 2026結果・払戻は `UNREAD` 維持。
- exact3原因分解は Run `34986471815` / Job `104439734630` / Artifact `10402739636` で成功済み。
- schema別合計は EXACT3_HIT=106 / OPPONENT_PAIR_MISS=115 / ORDER_MISS=14。主因は順序ではなく相手2艇選択。
- これからHEAD的中historicalのみを対象に、schema別の相手2艇ranking改善を実装する。展示/ST/選手力/攻撃力等の既存causal特徴を候補にし、September 2026結果は使わない。
- 同一データ上のbestをproduction化せず、時系列OOF→独立temporal holdoutで比較する。
- 既存v351のHEAD以外のgate/finalizer条件は勝手に変更しない。`turn+straight`は保留。
- 作業後にcommit SHA / Run・Job・Artifact / 結果 / 結論 / 次再開地点を追記する。

## exact3原因分解確定結果
- Run `34986471815` / Job `104439734630` / Artifact `10402739636` / success。
- `lap+turn+straight`: EXACT3_HIT 81 / OPPONENT_PAIR_MISS 85 / ORDER_MISS 10。
- `lap+turn`: 16 / 18 / 1。
- `half+turn+straight`: 5 / 8 / 2。
- `base`: 4 / 4 / 1。
- 合計: EXACT3_HIT 106 / OPPONENT_PAIR_MISS 115 / ORDER_MISS 14。
- 結論: exact3改善の第一優先は2着3着の順序入替ではなく、相手2艇候補そのもののranking/selection改善。

## 現行production / LIVE
- production profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- HEAD cutoff `.78`、opponent core `SECOND G2=.45 / THIRD G3=1.00`。
- core scripts: `run_1head_v351_live_window.py`, `probe_1head_v351_boatcast_exhibition.py`, `run_1head_v351_live_exhibition_gate.py`, `run_1head_v351_live_finalize.py`。
- レース時刻自動controllerは停止。ユーザーが「判別して」等と依頼したときだけ直前判定。
- 03:00 JST daily preparation承認済み。
- LIVEでは結果・払戻を絶対に使用しない。`result_or_payout_used=False` / `chronology_guard=True`。

## schema production方針
正式対象: `lap+turn+straight`, `lap+turn`, `half+turn+straight`, `base`（baseは低標本フラグ）。
保留: `turn+straight`（OOF0）。

## 次の研究
1. HEAD的中historical母集団で相手艇候補ごとのcausal feature datasetを作る。
2. schema別に相手がtop2へ入る確率を時系列OOFで推定。
3. 現行G2/G3 pairと新pair rankingを比較し、PAIR_HIT率とexact3上限を測る。
4. 独立temporal holdoutで改善が残る場合のみproduction候補にする。
5. 順序モデルはpair改善後に研究する。
