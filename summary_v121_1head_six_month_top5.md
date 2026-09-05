# v121 1-head six-month TWO-STAGE operational diagnostic

- Period: **2026-03-01..2026-08-31**.
- Stage 1 PRE: pre-exhibition features only -> daily watch-list.
- Stage 2 LIVE: only those PRE races are judged by full v109; **BUY = p109 >=72% and boat1 remains course1**.
- BUY races use frozen v110 role blend **lambda=.50** for 7/8/10-ticket evaluation.
- No current/final odds, result, or payout is used for PRE or LIVE selection.
- Goal is not to force exactly 5 races/day after exhibition; it is to choose PRE candidates first and have the LIVE BUY count average around 5/day.

## PRE features used
- one_grade, one_wr, one_local, one_motor, one_waku_wr, one_nst_strength, one_waku_sr_strength, one_past_win, one_meet_st_strength
- Explicitly excluded from PRE: current exhibition time/ST/original exhibition, direct score, threat/margin variables, current entry course, odds.

## Six-month candidate-size comparison
|PRE top/day|PRE R/day|BUY R/day|BUY R|①頭率|7点的中率|7点coverage|7点ROI|8点ROI|10点ROI|BUY 3-7R days|BUY 4-6R days|0 BUY days|
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|5|5.00|4.21|770|81.0%|56.0%|69.1%|85.5%|80.5%|76.7%|167/183|148/183|3|
|8|8.00|6.36|1163|80.4%|54.3%|67.6%|84.8%|82.1%|79.3%|116/183|60/183|1|
|10|10.00|7.75|1419|79.8%|53.9%|67.5%|84.7%|82.8%|80.0%|58/183|34/183|1|
|12|12.00|9.14|1673|79.3%|53.7%|67.8%|83.1%|81.2%|78.0%|35/183|20/183|1|
|15|15.00|11.08|2027|79.0%|53.6%|67.9%|82.3%|80.1%|78.4%|20/183|12/183|0|
|20|20.00|14.04|2569|78.7%|53.7%|68.2%|81.7%|79.6%|78.0%|12/183|6/183|0|
|25|25.00|16.67|3050|78.5%|53.6%|68.3%|81.2%|79.1%|77.2%|3/183|3/183|0|

## Mechanical target-count choice: PRE top 5/day
- This choice uses only closeness of average BUY count to 5/day, **not ROI or race outcomes**.
- Six-month PRE watch count: **915R**; LIVE BUY count: **770R**.

## Monthly results for the chosen PRE size
|month|days|PRE R|BUY R|BUY/day|①頭率|7点的中率|7点ROI|8点ROI|10点ROI|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2026-03|31|155|111|3.58|77.5%|47.7%|83.3%|80.4%|76.4%|
|2026-04|30|150|115|3.83|80.9%|56.5%|91.8%|81.2%|74.9%|
|2026-05|31|155|133|4.29|82.0%|61.7%|88.8%|83.8%|77.4%|
|2026-06|29|145|129|4.45|79.1%|55.0%|88.2%|83.2%|80.6%|
|2026-07|31|155|144|4.65|81.2%|56.2%|78.8%|74.7%|73.5%|
|2026-08|31|155|138|4.45|84.8%|57.2%|83.3%|80.5%|77.7%|

## Clean holdout focus: Jun-Aug
- Chosen PRE size: **top 5/day**.
- LIVE BUY: **411R / 91 days = 4.52R/day**.
- ①頭率 **81.8%**.
- 7点: hit **56.2%**, coverage **68.8%**, ROI **83.3%**.
- 8点 ROI **79.3%** / 10点 ROI **77.1%**.

## Guardrails
- Do not reinterpret this as “pick the best five after exhibition.” PRE races are frozen first.
- LIVE p109 is only a BUY/SKIP gate inside that PRE list.
- Mar-May are retrospective development-overlap diagnostics; Jun-Aug matter more for adoption.
- Because v108 historically excludes entry-changed boat1 races before settlement, prospective operation should still keep the explicit LIVE course1 gate and count those PRE watches as SKIP when they occur.
