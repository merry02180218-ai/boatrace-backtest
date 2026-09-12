# v302 1HEAD 3-ticket transferred-feature ablation

- Development research only; production unchanged.
- Jul/Aug NON-PRISTINE; September outcomes unread.
- Same frozen 204-race denominator and TOP2XTOP2 alpha=.60 policy.
- Baseline is v300 winning regularization: SECOND L2=3, THIRD L2=.1.

## Results
|config|families|R|hits|hit rate|delta|worst month|
|---|---|---:|---:|---:|---:|---:|
|V300|none|249|124|49.80%|+0.00pt|46.88%|
|ONLY_ST_EDGE|ST_EDGE|249|124|49.80%|+0.00pt|46.88%|
|ONLY_MOTOR|MOTOR|249|124|49.80%|+0.00pt|46.88%|
|ONLY_STMOTOR|STMOTOR|249|124|49.80%|+0.00pt|46.88%|
|COMBO_ST_EDGE_MOTOR|MOTOR+ST_EDGE|249|124|49.80%|+0.00pt|46.88%|
|COMBO_ST_EDGE_STMOTOR|STMOTOR+ST_EDGE|249|124|49.80%|+0.00pt|46.88%|
|COMBO_MOTOR_STMOTOR|MOTOR+STMOTOR|249|124|49.80%|+0.00pt|46.88%|
|COMBO_ST_EDGE_MOTOR_STMOTOR|MOTOR+STMOTOR+ST_EDGE|249|124|49.80%|+0.00pt|46.88%|
|ONLY_WALL|WALL|249|123|49.40%|-0.40pt|46.88%|
|ONLY_TURN_FORM|TURN_FORM|249|122|49.00%|-0.80pt|43.75%|

## Individually non-harmful families
- ST_EDGE, MOTOR, STMOTOR

## Best monthly audit
|month|R|hits|hit rate|
|---|---:|---:|---:|
|2026-02|20|10|50.00%|
|2026-03|28|17|60.71%|
|2026-04|46|24|52.17%|
|2026-05|91|43|47.25%|
|2026-06|64|30|46.88%|

## Decision
- Best: **V300 = 49.80% (124/249)**, delta vs v300 +0.00pt.
- Only individually non-harmful transferred families were eligible for combination search.
- Feb-Jun are reused development evidence; freeze any winner before prospective validation.
