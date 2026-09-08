# v205 3-head actual operational replay

- pipeline: frozen v191 PRE watch -> actual v165 production pass (v195) -> frozen v166 Top10 -> optional PICK UP gate -> 10,000-yen Dutch settlement
- PRE cut: 0.072608 (chosen on July, frozen for August)
- PICK UP: p3head>=0.30 & turn_margin23>=-0.2 & st_margin23>=-0.2, only after PRE watch
- odds: corrected official closing-displayed odds; settlement only, never selection
- July is TUNE/DESCRIPTIVE because PRE cut was selected on July
- August is the clean untouched PRE test and the primary operational result

## Results
|segment|R|hit|avg composite|cost|return|ROI|
|---|---:|---:|---:|---:|---:|---:|
|JUL tune all production|57|22.81%|4.337|570000|608210|106.7%|
|JUL tune PRE pass|48|22.92%|3.260|480000|282030|58.8%|
|JUL tune PICK UP|2|50.00%|2.022|20000|20160|100.8%|
|AUG untouched all production|0|0.00%|0.000|0|0|0.0%|
|AUG untouched PRE pass|0|0.00%|0.000|0|0|0.0%|
|AUG untouched PICK UP|0|0.00%|0.000|0|0|0.0%|

## PICK UP races
|split|date|race_code|PRE p|p3head|turn|ST|hit|comp|return|profit|
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|tune_july|2026-07-09|202607091103|1.0000|0.3247|-0.200|0.400|0|2.036|0|-10000|
|tune_july|2026-07-12|202607120409|0.9989|0.4414|-0.200|0.200|1|2.008|20160|10160|

## Interpretation
- Production adoption must be judged primarily from August untouched, not July tune.
- PICK UP remains SHADOW unless the untouched sample is sufficiently large and stable.
