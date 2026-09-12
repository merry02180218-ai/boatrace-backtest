# v313 1-head opponent causal cache

## Purpose
- Expensive historical reconstruction is performed once and committed as reusable cache files.
- All subsequent 1-head opponent auto-research should load this cache by default instead of rebuilding historical sources.
- Rebuild only when upstream causal feature logic/data provenance changes, the frozen cohort changes explicitly, or a cache audit fails.

## Files
- `cache_v313_1head_opponent_pre.csv.gz`: frozen PRE/prior opponent universe plus settlement labels, 35462 rows / 580 columns.
- `cache_v313_1head_opponent_p3.csv.gz`: causal monthly walk-forward p3 map, 21692 races.
- `cache_v313_1head_opponent_p4.csv.gz`: audited PRE monthly walk-forward p4 map, 22271 races.

## Causal contract
- PRE/prior features are constructed before settlement joins.
- `meet_*` columns are removed and `meet_*` suffixes are forbidden.
- Outcome / settlement fields are labels only, never model features.
- Month M models train only on rows strictly before M.
- Missing p3/p4 are never future-backfilled; downstream uses availability flags + neutral sentinel.
- Fixed opponent evaluation cohort remains 345 races / 290 boat-1 wins.
- Jul/Aug 2026 remain NON-PRISTINE; September outcomes remain unread.

## Cache-first rule
- Research scripts MUST prefer these cache files when present.
- A research workflow must not repeat the full causal reconstruction merely to test a new model formulation.
- If the cache is missing/stale, build it once, commit it, then continue the queued experiment.
