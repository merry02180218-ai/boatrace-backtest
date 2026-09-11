# v301 1HEAD 3-ticket transfer research: 3-head/4-head features

- Development research only; production unchanged.
- Jul/Aug NON-PRISTINE and excluded upstream; September outcomes unread.
- Same frozen 204-race denominator and TOP2XTOP2 alpha=.60 ticket policy as v299/v300.
- Transferred structures: relative ST/inner-wall pressure, motor edge/history, ST×motor, prior turn/foot, racer/form history.
- Fixed selected races: **204**; head rate **81.37%**.

## Results
|config|S L2|T L2|R|hits|hit rate|delta|worst month|
|---|---:|---:|---:|---:|---:|---:|---:|
|BASE|10|0.3|204|102|50.00%|+0.00pt|44.44%|
|AUG_s30_t0.1|30|0.1|204|100|49.02%|-0.98pt|44.44%|
|AUG_s30_t0.3|30|0.3|204|100|49.02%|-0.98pt|44.44%|
|AUG_s30_t1|30|1|204|100|49.02%|-0.98pt|44.44%|
|AUG_s3_t0.1|3|0.1|204|99|48.53%|-1.47pt|44.44%|
|AUG_s3_t0.3|3|0.3|204|99|48.53%|-1.47pt|44.44%|
|AUG_s3_t1|3|1|204|99|48.53%|-1.47pt|44.44%|
|AUG_s10_t0.1|10|0.1|204|99|48.53%|-1.47pt|44.44%|
|AUG_s10_t0.3|10|0.3|204|99|48.53%|-1.47pt|44.44%|
|AUG_s10_t1|10|1|204|99|48.53%|-1.47pt|44.44%|

## Monthly best-config audit
|month|R|hits|hit rate|
|---|---:|---:|---:|
|2026-02|18|8|44.44%|
|2026-03|29|16|55.17%|
|2026-04|37|19|51.35%|
|2026-05|69|33|47.83%|
|2026-06|51|26|50.98%|

## Decision
- Best v301: **BASE = 50.00% (102/204)**, baseline 50.00% (102/204), delta +0.00pt.
- Worst-month hit rate: **44.44%**.
- Feb-Jun are reused development data; any winning config must be frozen before prospective validation.
