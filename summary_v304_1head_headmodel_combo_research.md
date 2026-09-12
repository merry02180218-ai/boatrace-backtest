# v304 1HEAD head-model combination research

- Development only; production unchanged.
- Jul/Aug NON-PRISTINE; September outcomes unread.
- Same v303 frozen opponent eligibility and exact monthly selection counts.
- Baseline audit: 204 races / 166 head hits = 81.37%.

## Results
|config|families|R|head hits|head rate|delta|worst month|
|---|---|---:|---:|---:|---:|---:|
|PLUS_TURN_FORM_STMOTOR|STMOTOR+TURN_FORM|204|181|88.73%|+7.35pt|68.63%|
|PLUS_TURN_FORM_WALL_INNER_STMOTOR_ST_EDGE|STMOTOR+ST_EDGE+TURN_FORM+WALL_INNER|204|180|88.24%|+6.86pt|66.67%|
|PLUS_TURN_FORM_WALL_INNER_ST_EDGE|ST_EDGE+TURN_FORM+WALL_INNER|204|179|87.75%|+6.37pt|68.63%|
|TURN_FORM|TURN_FORM|204|179|87.75%|+6.37pt|66.67%|
|PLUS_TURN_FORM_WALL_INNER|TURN_FORM+WALL_INNER|204|179|87.75%|+6.37pt|66.67%|
|PLUS_TURN_FORM_STMOTOR_ST_EDGE|STMOTOR+ST_EDGE+TURN_FORM|204|179|87.75%|+6.37pt|66.67%|
|PLUS_TURN_FORM_ST_EDGE|ST_EDGE+TURN_FORM|204|179|87.75%|+6.37pt|64.71%|
|PLUS_TURN_FORM_WALL_INNER_STMOTOR|STMOTOR+TURN_FORM+WALL_INNER|204|178|87.25%|+5.88pt|64.71%|
|BASE|none|204|166|81.37%|+0.00pt|78.38%|

## Best monthly audit
|month|R|hits|head rate|
|---|---:|---:|---:|
|2026-02|18|18|100.00%|
|2026-03|29|29|100.00%|
|2026-04|37|37|100.00%|
|2026-05|69|62|89.86%|
|2026-06|51|35|68.63%|

## Decision
- Best: **PLUS_TURN_FORM_STMOTOR: 181/204 = 88.73%**, delta +7.35pt vs BASE; worst month 68.63%.
- Prefer a config that improves overall head rate without materially worsening the weakest month; this remains reused Feb-Jun development evidence.
