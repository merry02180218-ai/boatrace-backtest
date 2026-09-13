# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## Mandatory operating rule
Before every work unit, record current position and intended next action here. After work, record commit/run/result/next action. Latest GitHub wins.

## Frozen production stack
v308 PRE head -> v317 SECOND OUTER_L2_1 -> v318 THIRD DROPSTART_T0.1 -> v320 HYBRID alpha=.70 exactly 3 tickets -> three odds -> composite odds `1/(1/o1+1/o2+1/o3)`.
Development regression: 345 selected / 290 head wins / 139 exact3. Jul/Aug 2026 NON-PRISTINE/reference-only. September outcomes unread. `meet_*` forbidden.

## Production adapter status
v323 implementation was completed and a successful GitHub Actions production run was verified: run **34757079269** (`live-1head-v323-20260913`). Historical regression remained 345/290/139 and frozen hcut 0.8073405637. 2026-09-13 current scoring selected 2 races and calculated current 3-ticket composite odds. No BUY cutoff was frozen; status remained fail-safe.

## WORK UNIT 2026-09-13-4 — Jul/Aug composite-odds BUY reference audit — COMPLETED
User hypothesis: with roughly 40% exact-3-ticket hit probability, a composite-odds BUY condition around 3.0 may be reasonable. User explicitly requested testing this on July/August.

Implementation:
- `run_v324_1head_julaug_composite_odds.py`
- `.github/workflows/v324-1head-julaug-composite-odds.yml`
- commits:
  - `7346141821c540c3dc72563393ee0e44ae5ce6db` — add v324 audit script
  - `c0ef06d56065f928fa5099e35bcfd824c9c0bf53` — add workflow
  - `8307774bda882110cf7f761faab15b21bad687d4` — fix historical odds lookup to match v322 source

Actions:
- first run `34762913278` failed because the initial odds lookup implementation did not match v322's historical odds DataFrame interface.
- corrected run **34762939723**: **completed / success**
- job ID: `103738822011`
- artifact: `v324-1head-julaug-composite-odds`, artifact ID `10318928652`
- frozen v321 reconciliation: **55 selected / 21 exact3 hits / 55 complete odds**, missing odds = 0.

### July
|rule|R|H|hit rate|return units|profit units|ROI|
|---|---:|---:|---:|---:|---:|---:|
|ALL|13|3|23.08%|6.059|-6.941|46.61%|
|>=2.5|4|1|25.00%|2.643|-1.357|66.06%|
|>=2.7|1|0|0.00%|0.000|-1.000|0.00%|
|>=3.0|1|0|0.00%|0.000|-1.000|0.00%|
|>=3.2|0|0|n/a|0.000|0.000|n/a|
|>=3.5|0|0|n/a|0.000|0.000|n/a|

### August
|rule|R|H|hit rate|return units|profit units|ROI|
|---|---:|---:|---:|---:|---:|---:|
|ALL|42|18|42.86%|41.052|-0.948|97.74%|
|>=2.5|18|5|27.78%|14.834|-3.166|82.41%|
|>=2.7|16|4|25.00%|12.243|-3.757|76.52%|
|>=3.0|9|1|11.11%|3.713|-5.287|41.25%|
|>=3.2|7|1|14.29%|3.713|-3.287|53.04%|
|>=3.5|6|1|16.67%|3.713|-2.287|61.88%|

### Jul+Aug combined
|rule|R|H|hit rate|return units|profit units|ROI|
|---|---:|---:|---:|---:|---:|---:|
|ALL|55|21|38.18%|47.111|-7.889|85.66%|
|>=2.5|22|6|27.27%|17.476|-4.524|79.44%|
|>=2.7|17|4|23.53%|12.243|-4.757|72.02%|
|>=3.0|10|1|10.00%|3.713|-6.287|37.13%|
|>=3.2|7|1|14.29%|3.713|-3.287|53.04%|
|>=3.5|6|1|16.67%|3.713|-2.287|61.88%|

Conclusion / guardrail:
- The Jul/Aug NON-PRISTINE reference **does not support composite odds >=3.0 as a BUY cutoff**. Combined >=3.0 gave only 1/10 exact3 = 10.00% and ROI 37.13%.
- Even >=2.5 underperformed ALL on Jul+Aug (79.44% vs 85.66%).
- The ~40% unconditional exact3 rate cannot be converted directly into a fair-odds threshold without conditioning hit probability on composite odds; observed hit probability fell sharply in the higher-odds subset.
- Do NOT freeze/promote any BUY cutoff from this reused Jul/Aug evidence. Keep production fail-safe until a cutoff has genuinely out-of-sample support.

## WORK UNIT 2026-09-13-5 — Exhibition-time post-PRE filter for exact3 >=50% — written BEFORE execution
User goal: raise the frozen 3-ticket exact3 hit rate from ~40% toward **50% or more** by using data that becomes available after exhibition, rather than changing the frozen PRE model itself.

Do now:
1. Keep the frozen PRE stack unchanged: v308 -> v317 -> v318 -> v320, exactly 3 tickets. The new logic is an additional post-exhibition PASS/SKIP layer only.
2. Inspect existing repository sources for same-race exhibition data already available historically and in live operation: exhibition time, exhibition ST, actual exhibition entry/course, and original exhibition metrics such as straight, one-lap, turn/handling where available.
3. Build candidate same-race exhibition features as **relative/field-adjusted values**, not raw times alone. At minimum inspect boat1 vs field, predicted SECOND/THIRD boats vs field, and ticket-covered opponents vs uncovered opponents.
4. Explicitly separate current-race exhibition data from PRE predictors. These same-race exhibition fields are allowed only in the new post-exhibition filter and must never leak into v308/v317/v318/v320 training/scoring.
5. First objective is classification/calibration: among races already selected by the frozen PRE stack, identify exhibition patterns associated with exact3 hits versus misses. Optimize for useful retained race count while testing whether PASS exact3 can reach >=50%; report coverage, head hit rate, exact3 hit rate, and odds/ROI diagnostics where odds are complete.
6. Use development data for feature research/training. Jul/Aug 2026 remain NON-PRISTINE/reference-only and may only be used as a final reference check after a rule/model is fixed. September outcomes remain unread.
7. Avoid simple threshold overfitting on individual exhibition times. Prefer causal, interpretable relative features and month-forward/OOS validation where possible.
8. Before implementing the filter, identify exact source files/columns and historical coverage. If original exhibition coverage is partial, quantify missingness and make the filter fail-safe rather than silently imputing future/post-race values.

Success criteria for this work unit:
- exact source and timing of exhibition/original-exhibition columns are audited;
- same-race exhibition data is isolated to a post-PRE layer;
- a reproducible dataset for the frozen selected races is created with exact3 label + exhibition features;
- no September outcome is read;
- if a candidate filter is tested, report retained R, exact3 H/rate, head H/rate, and Jul/Aug reference only after freezing the candidate on development data.

If interrupted: resume WORK UNIT 5 from item 2. Do not alter the frozen PRE stack and do not tune on Jul/Aug.
