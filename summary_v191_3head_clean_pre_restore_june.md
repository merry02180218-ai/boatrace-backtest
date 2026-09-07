# v191 clean 3-head PRE — June restored

**PREは監視候補のみ。正式候補は展示後 actual v165 p3head>=30%。**

## June restoration
- historical waku10: saved BoatraceCSV -> validated BOATCAST fallback
- waku source days: {'boatracecsv_saved': 44, 'boatcast_direct': 47, 'missing': 1}
- race-card missing dates: ['2026-06-17']
- unmatched race rows: 392

## Temporal validation
- June train: R 4388, formal 73
- July tune: R 4772, formal 87, watch 648 (13.6%), recall 85.1%, precision 11.4%
- frozen cut: **0.072608**
- August untouched: R 4776, formal 110, watch 679 (14.2%), recall 85.5%, precision 13.8%
- gate: **PASS** (Aug recall>=80%, watch<=35%)

## 2026-09-09 PRE monitor
- scan JST: **2026-09-08 02:44:18**
- active venues: **0**
- scored: **0R** / errors 0R
- PRE watch: **0R**

|締切|場|R|3号艇|級|PRE p|
|---|---|---:|---|---|---:|
|-|-|-|-|-|-|

## Canonical operation
PRE watch -> exhibition -> actual v165 p3head>=30% -> v166 lambda=1.00 Top10. PRE score is never p3head and never BUY.
