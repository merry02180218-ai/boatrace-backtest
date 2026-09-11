# v300 1HEAD exact-trifecta 3-ticket opponent feature upgrade

- Development research only; production unchanged.
- Jul/Aug excluded upstream; September outcomes unread.
- Evaluation race set is frozen to the v299/v298 baseline selector; every config uses the same denominator.
- Boat-1 losses remain exact-trifecta misses. Ticket policy is fixed TOP2XTOP2 alpha=.60.
- Fixed selected races: **204**; head rate: **81.37%**.

## Baseline
|config|R|hits|3pt hit|worst month|
|---|---:|---:|---:|---:|
|BASE|204|102|50.00%|44.44%|

## Feature/regularization candidates
|config|S L2|T L2|R|hits|hit rate|delta|worst month|
|---|---:|---:|---:|---:|---:|---:|---:|
|AUG_s3_t0.1|3|0.1|204|104|50.98%|+0.98pt|44.44%|
|AUG_s3_t0.3|3|0.3|204|104|50.98%|+0.98pt|44.44%|
|AUG_s3_t1|3|1|204|104|50.98%|+0.98pt|44.44%|
|AUG_s10_t0.1|10|0.1|204|104|50.98%|+0.98pt|44.44%|
|AUG_s10_t0.3|10|0.3|204|104|50.98%|+0.98pt|44.44%|
|AUG_s10_t1|10|1|204|104|50.98%|+0.98pt|44.44%|
|AUG_s30_t0.1|30|0.1|204|104|50.98%|+0.98pt|44.44%|
|AUG_s30_t0.3|30|0.3|204|104|50.98%|+0.98pt|44.44%|
|AUG_s30_t1|30|1|204|104|50.98%|+0.98pt|44.44%|
|BASE|10|0.3|204|102|50.00%|+0.00pt|44.44%|

## Monthly best-config audit
|month|R|hits|hit rate|
|---|---:|---:|---:|
|2026-02|18|8|44.44%|
|2026-03|29|17|58.62%|
|2026-04|37|18|48.65%|
|2026-05|69|34|49.28%|
|2026-06|51|27|52.94%|

## Decision
- v300 improves the frozen 3-point baseline from **50.00% (102/204)** to **50.98% (104/204)** on the identical races.
- Winning development config: **AUG_s3_t0.1**, worst-month hit rate **44.44%**.
- Feb-Jun is reused development evidence; freeze this config before any prospective validation.
