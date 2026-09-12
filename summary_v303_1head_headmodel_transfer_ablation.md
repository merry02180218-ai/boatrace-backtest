# v303 1HEAD head-model transferred-feature ablation

- Development only; production unchanged.
- Jul/Aug NON-PRISTINE; September outcomes unread.
- Opponent-confidence eligibility is frozen to v298/v299 BASE.
- Every candidate preserves the exact baseline selected count in each month; denominator cannot shrink.
- Baseline audit asserted: 204 races / 166 head hits = 81.37%.

## Results
|config|R|head hits|head rate|delta|worst month|
|---|---:|---:|---:|---:|---:|
|ONLY_TURN_FORM|204|179|87.75%|+6.37pt|66.67%|
|ONLY_WALL_INNER|204|175|85.78%|+4.41pt|80.39%|
|ONLY_STMOTOR|204|173|84.80%|+3.43pt|78.43%|
|ONLY_ST_EDGE|204|168|82.35%|+0.98pt|76.47%|
|BASE|204|166|81.37%|+0.00pt|78.38%|
|ONLY_MOTOR|204|166|81.37%|+0.00pt|78.38%|

## Non-harmful single families
- ST_EDGE, WALL_INNER, MOTOR, TURN_FORM, STMOTOR

## Best monthly audit
|month|R|hits|head rate|
|---|---:|---:|---:|
|2026-02|18|18|100.00%|
|2026-03|29|29|100.00%|
|2026-04|37|37|100.00%|
|2026-05|69|61|88.41%|
|2026-06|51|34|66.67%|

## Decision
- Best single-family head model: **ONLY_TURN_FORM: 179/204 = 87.75%**, delta +6.37pt vs frozen baseline.
- If a family improves, next step is combination/interaction research at the same monthly counts; do not promote from reused Feb-Jun development evidence.
