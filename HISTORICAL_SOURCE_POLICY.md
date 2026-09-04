# Historical source policy

Updated: 2026-09-04 JST

## waku10 — ADOPTED historical fallback

Primary saved source:
- `BoatraceCSV/data/programs/waku10/YYYY/MM/DD.csv` when present.

Historical fallback:
- BOATCAST `bc_j_waku10` direct source:
  `https://race.boatcast.jp/hp_txt/{jo}/bc_j_waku10_{YYYYMMDD}_{jo}_{rno}.txt`
- loader: `historical_data_loader.waku10_rows()`
- fetcher: `historical_waku10_fetcher.py`

Validation:
- overlap day: 2026-07-20
- saved BoatraceCSV: 156 races
- direct BOATCAST: 156 races
- field comparison: 32,448 / 32,448 = **100.0000%**
- older direct source confirmed on full active race sets:
  - 2025-05-03: 193 races
  - 2025-11-01: 144 races
  - 2026-05-01: 176 races
  - 2026-06-01: 144 races

Decision: **approved** for historical model/backtest inputs. Prefer saved CSV when present; otherwise direct BOATCAST fallback.

## od3 / pre-close trifecta odds — STRICT POLICY

Approved:
- BoatraceCSV `data/previews/od3/YYYY/MM/DD.csv` only when the row has a pre-close acquisition timestamp.
- Current collector is a pre-close aggregating-odds snapshot, not final odds.

Rejected historical substitutes:

### BOATCAST expired `bc_smt_od3`
Older source files return no odds (`data=2`) after retention expiry. Cannot backfill.

### kyotei24 Odds Bank
The historical page explicitly labels its displayed data as `締切時オッズ`.
Overlap check, 2026-09-01 Omura 6R:
- official BoatraceCSV od3 acquired 19:46:23 for 19:56 cutoff
- official pre-close samples:
  - 1-2-3 = 30.2
  - 1-4-5 = 56.0
  - 1-5-4 = 76.9
  - 5-1-4 = 205.3
  - 4-1-5 = 81.3
  - 3-1-2 = 57.2
- kyotei24 deadline-time values differed materially (e.g. 1-4-5 = 39.2, 1-5-4 = 62.0, 5-1-4 = 328.4, 4-1-5 = 102.7, 3-1-2 = 110.3).
Decision for prediction inputs: **reject** as od3 substitute because it is deadline/final-like and would leak future market movement relative to a T-10 simulation.

### boatrace-ai.app historical pages
Search indexes expose historical odds with an update timestamp (examples exist before July 2026), and some timestamps are plausibly pre-close. However the historical payload is not currently reproducibly machine-accessible from the public route/API; the previously embedded Supabase project endpoint is not DNS-resolvable from validation infrastructure. Search-cache extraction is not stable enough for a deterministic backtest.
Decision: **not adopted** unless a reproducible timestamped historical endpoint/archive is found and overlap-validated against official od3.

### lamrongol/BoatraceOdds
README describes periodic updating, but the historical saver (`scraper.php`) explicitly scrapes **yesterday** and writes the dated JSON afterward. Historical files therefore do not establish a pre-close observation time.
Decision: **reject** for strict od3 replacement.

## Final/deadline odds — POST-HOC REPORTING ONLY

User-approved reporting exception (2026-09-04):
- Historical final/deadline trifecta odds may be used for **after-the-fact descriptive statistics**, including average composite odds by model / grade / ticket count.
- Kyotei24 Odds Bank is approved for this limited purpose when the page explicitly shows `締切時オッズ` and the 120 trifecta combinations parse correctly.
- This exception does **not** make final odds a valid prediction-time feature.

Hard prohibition:
- final/deadline/post-race odds must never influence candidate extraction, score, grade, head selection, opponent ranking, ticket ordering, A/S promotion, skip decisions, or any no-leak predictive metric.
- If an EV / odds filter is tested as a prediction rule, it must use a verified pre-close snapshot available at the simulated decision time; final odds cannot substitute for it.

## No-leak invariant
Never substitute a final/deadline/post-race odds archive for a missing pre-close odds snapshot in any prediction-time backtest. Missing historical pre-close od3 stays missing. Final odds are allowed only in explicitly labelled post-hoc reporting outputs such as v102 composite-odds summaries.
