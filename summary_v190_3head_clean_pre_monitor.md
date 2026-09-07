# v190 clean 3-head PRE monitor

**PREは監視候補のみ。正式候補は展示後 actual v165 p3head>=30%。**

## No-leak design
- race-card + waku10 only
- no current exhibition / result / payout / odds
- label: frozen monthly-WF v165 p3head>=30%

## Temporal validation
- historical rows: **6743** / missing 3097
- train Jul1-20: R 271, formal 8
- tune Jul21-31: R 1696, formal 22, watch 861 (50.8%), recall 86.4%, precision 2.2%
- frozen cut: **0.001021**
- untouched Aug: R 4776, formal 110, watch 2298 (48.1%), recall 92.7%, precision 4.4%
- gate: **FAIL** (Aug recall>=80%, watch<=35%)

## 2026-09-09 PRE monitor
- scan JST: **2026-09-08 02:20:16**
- active venues: **0**
- scored: **0R** / errors 0R
- PRE watch: **0R**

|締切|場|R|3号艇|級|PRE p|
|---|---|---:|---|---|---:|
|-|-|-|-|-|-|

## Canonical operation
PRE watch -> exhibition -> actual v165 p3head>=30% -> v166 lambda=1.00 Top10. PRE score is never p3head and never BUY.
