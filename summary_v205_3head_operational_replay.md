# v205 3-head actual operational replay

- pipeline: frozen v191 PRE watch -> actual v165 production pass (v195) -> frozen v166 Top10 -> optional PICK UP gate -> 10,000-yen Dutch settlement
- PRE cut: 0.072608 (chosen on July, frozen for August)
- PICK UP: p3head>=0.30 & turn_margin23>=-0.2 & st_margin23>=-0.2, only after PRE watch
- odds: unified settlement series per user instruction; BoatraceCSV od3 preferred where available, corrected official closing used as fallback
- July is TUNE/DESCRIPTIVE because PRE cut was selected on July
- August is the clean untouched PRE test and the primary operational result

## Results
|segment|R|hit|avg composite|cost|return|ROI|
|---|---:|---:|---:|---:|---:|---:|
|JUL tune all production|87|26.44%|4.327|870000|858800|98.7%|
|JUL tune PRE pass|73|27.40%|3.316|730000|508180|69.6%|
|JUL tune PICK UP|4|25.00%|2.149|40000|20160|50.4%|
|AUG untouched all production|109|30.28%|4.584|1090000|1173880|107.7%|
|AUG untouched PRE pass|93|32.26%|3.739|930000|909810|97.8%|
|AUG untouched PICK UP|9|22.22%|2.788|90000|68760|76.4%|

## Odds-source coverage
|month|source|R|
|---|---|---:|
|2026-07|boatracecsv_od3|30|
|2026-07|official_closing|57|
|2026-08|boatracecsv_od3|109|

## PICK UP races
|split|date|race_code|source|PRE p|p3head|turn|ST|hit|comp|return|profit|
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|tune_july|2026-07-09|202607091103|official_closing|1.0000|0.3247|-0.200|0.400|0|2.036|0|-10000|
|tune_july|2026-07-12|202607120409|official_closing|0.9989|0.4414|-0.200|0.200|1|2.008|20160|10160|
|tune_july|2026-07-20|202607201204|boatracecsv_od3|0.1285|0.3348|-0.200|-0.200|0|2.353|0|-10000|
|tune_july|2026-07-27|202607271004|boatracecsv_od3|0.9987|0.3288|0.200|-0.200|0|2.198|0|-10000|
|untouched_aug|2026-08-09|202608092307|boatracecsv_od3|0.9778|0.3293|-0.200|0.600|0|1.329|0|-10000|
|untouched_aug|2026-08-18|202608181101|boatracecsv_od3|0.9994|0.4075|-0.200|0.200|0|2.267|0|-10000|
|untouched_aug|2026-08-20|202608200201|boatracecsv_od3|0.8865|0.3057|-0.200|0.200|0|5.254|0|-10000|
|untouched_aug|2026-08-21|202608210305|boatracecsv_od3|0.2813|0.3389|0.000|0.400|1|2.956|29640|19640|
|untouched_aug|2026-08-22|202608220303|boatracecsv_od3|0.6777|0.3482|0.000|0.400|1|3.869|39120|29120|
|untouched_aug|2026-08-22|202608220407|boatracecsv_od3|0.9973|0.4206|-0.200|-0.200|0|2.965|0|-10000|
|untouched_aug|2026-08-26|202608260304|boatracecsv_od3|0.9988|0.3895|0.000|0.400|0|1.952|0|-10000|
|untouched_aug|2026-08-26|202608260904|boatracecsv_od3|0.9993|0.3698|-0.200|-0.200|0|2.407|0|-10000|
|untouched_aug|2026-08-31|202608310403|boatracecsv_od3|0.9938|0.3765|-0.200|-0.200|0|2.097|0|-10000|

## Interpretation
- Production adoption must be judged primarily from August untouched, not July tune.
- PICK UP remains SHADOW unless the untouched sample is sufficiently large and stable.
