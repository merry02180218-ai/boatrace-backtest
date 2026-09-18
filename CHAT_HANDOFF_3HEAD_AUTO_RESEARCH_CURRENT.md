# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research version: `v289-addon-wave1`
- decision: **NO_ADOPTION_WAVE1**
- v288 production is unchanged; baseline replay assertion is 94R / 52 hits / payout 1,622,070 yen.
- July/August are NON-PRISTINE. September outcomes were not loaded or used.
- Candidate universe is only v288 final NO_BET among operational PRE S/A and v242-buyable races.

## Wave-1 result
- candidate pool: 178 races
- best tested variant: `return_rank@0.45`
- best add-on: 84R / 15 hits / ROI 54.92% / profit -378,700 yen
- combined: 178R / ROI 117.04%

## Methods tested / dead ends retained
- `residual_hit`: prior-reject outcome effect ranking over pre-race safe features.
- `exhibition_upgrade`: current exhibition/ST/original-exhibition family only.
- `return_rank`: prior-reject realized-return ranking trained only on prior months.
- `attack_style_split`: separate stretch-vs-turn regimes, then outcome ranking.
- `orthogonal_consensus`: residual + exhibition + return independent-score consensus.
- `ev_calibrated`: residual hit score plus current composite odds, alpha chosen on prior months only.

## Real-operation audit
- all scoring inputs are columns already present before settlement in the canonical v243/v288 audit artifact;
- decisions use only prior-month outcomes for fitting; current test-month result/payout enters settlement only;
- missing features are median-imputed from prior training; production promotion must replace any required-current missingness with fail-closed gates;
- overlap with v288 baseline is zero by construction;
- no production workflow/model was changed.

## Next restart point
- If no wave-1 variant passes, next research must change the information/ticket family rather than loosen v288 thresholds.
- Priority next: opponent/ticket re-ranking on NO_BETs, PRE-B/new-population research with full leak audit, and venue/field archetype residual models.
- Before any promotion, build live shadow scorer with fail-closed source checks and exact 10,000-yen Dutch.

## Generated artifacts
- `research_v289_3head_addon.json`
- `research_v289_3head_addon.md`



## AFTER WORK — Broad50 Wave10 nonlinear interaction result (Run 35315697326, 2026-09-18)
- Final optimized SUCCESS: Run **35315697326** / Job **105506745578** / Artifact **10535610790**; head SHA **eebc3aa7e59c99214d126ace72cc7b01b4612fff**.
- Existing PRE only; nonlinear components/interactions were predeclared; daily walk-forward; February-only diagnostic. March was not opened. September outcomes UNREAD; production v288 unchanged.
- Evaluated **84,240** nonlinear scenario/model candidates using percentile and positive-superiority gating. Components included WALL_BREAK, INNER_COLLAPSE, ATTACK_SYNERGY, COUNTER_SAFETY, geometric/min/harmonic aggregators, and selected pair/triple/four-way products.
- The nonlinear family **did not beat Wave9 at any useful support floor**. Worst-half ceiling vs Wave9:
  - >=20R/half: Wave10 **38.10%** (H1 8/21=38.10%, H2 13/34=38.24%, 21/55=38.18%) vs Wave9 39.13% (**-1.04pt**). Best: window28 / R1-8 / `wall_x_attack` q=.95 + logistic q=.95.
  - >=30R/half: **35.48%** vs 37.50% (**-2.02pt**). Best: window28 / R1-10 / `wall_min` q=.80 + logistic q=.95.
  - >=50R/half: **33.96%** vs 34.41% (**-0.45pt**). Best: window42 / R1-8 / `wall_x_attack` q=.925 + logistic q=.925.
  - >=75R/half: **31.45%** vs 34.41% (**-2.96pt**).
  - >=100R/half: **29.63%** vs 32.35% (**-2.72pt**).
  - >=150R/half: **28.49%** vs 29.74% (**-1.25pt**).
  - >=200R/half: **26.00%** vs 27.61% (**-1.61pt**).
- Weekly instability remained, especially Feb 15-21. Example >=20R best weeks: 22.22%, 50.0%, 27.78%, 50.0%.
- Conclusion: intuitive multiplicative scenario construction from the current signals does not create additional stable predictive information; the same temporal weakness remains. This rejects the hand-crafted interaction path, not all possible interactions.

## BEFORE WORK — Broad50 Wave11 automated interaction discovery on prior months (2026-09-18)
- To avoid hand-picking formulas after seeing February labels, interaction discovery will move one period earlier.
- Fetch **December 2025 + January 2026** PRE/results from BoatraceCSV. Use leakage-safe daily walk-forward with prior-day labels only.
- Generate a curated base set of oriented PRE signals, normalize each against trailing history, and automatically enumerate pairwise multiplicative interactions (plus a limited set of triple interactions selected only from prior-month evidence).
- **Discovery/selection uses January only**: require chronological Jan halves, venue dispersion and support; rank interactions by worst-half head rate, not combined rate. February labels are not used to choose which interaction formulas survive.
- Freeze the top diverse January-stable interactions, their thresholds, window/band definitions and any small interaction ensemble before February evaluation.
- February is then a one-shot transfer test for the frozen interaction family. Report the same support-size ceiling (20/30/50/75/100 per half) and direct comparison to Wave9. Do not iterate Wave11 formulas from February result.
- March remains unopened. September outcomes UNREAD; production v288 unchanged.


### Wave11 failure/repair note (Run 35316102805)
- Initial Wave11 Run **35316102805** / Job **105507965184** failed before any February transfer result was produced.
- Cause: candidate universe was generated from globally available base signals, while some rolling window/mode caches legitimately lacked an interaction column when one member signal had insufficient finite trailing support. Evaluator raised `KeyError` instead of treating that candidate as unavailable for that cache.
- Repair is implementation-only: fail-closed skip candidates whose exact interaction column is absent in that window/mode cache. Discovery rules, support floors, formulas and February transfer protocol remain unchanged. A fresh run from current main is required; do not rerun the stale failed SHA.


## AFTER WORK — Broad50 Wave11 prior-month automated interaction transfer (Run 35316272342, 2026-09-18)
- Repaired fresh SUCCESS: Run **35316272342** / Job **105508476110** / Artifact **10535127216**; head SHA **690b2d0cc12cf0b4fca818566dfa0ef985fab0a2**. Initial Run 35316102805 failed on a rolling-cache missing interaction column and produced no result; repair only added fail-closed skipping for unavailable columns.
- Discovery used December history + January labels only. February was a one-shot transfer and did not choose interaction formulas. March unopened; September UNREAD; production v288 unchanged.
- Clean source: Dec 4,647R / Jan 4,963R / Feb 3,970R; previous-session date violations 0; canonical-vs-realtime Feb winners 3970/3970 = 100%.
- Automated base set: 19 oriented PRE signals -> **171 pair interactions**. January pair discovery could reach worst-half 50% at >=20/30R per half; top signal vocabulary then generated 56 triple interactions.
- Top prior-month interaction vocabulary: vs1 national2, attack-player-inner, b1 pressure, vs2 national2, attack-start-inner, vs2 ST, vs1 ST, b2 wall-break.
- Frozen from January before February: **258 candidate settings / 33 unique interactions**.
- February transfer support frontier:
  - >=20R/half: **H1 9/22=40.91%, H2 12/30=40.00%, worst-half 40.00%, combined 21/52=40.38%**. This is **+0.87pt** worst-half over Wave9's 39.13%. Winning formula: positive-gated window21 / R1-10 / q=.95, triple `sig_vs1_全国2連対率 × sig_attack_player_inner × sig_b1_pressure`.
  - >=30R/half: worst-half **31.82%** (below Wave9 37.50%).
  - >=50R/half: **28.57%** (below 34.41%).
  - >=75R/half: **25.00%** (below 34.41%).
  - >=100R/half: **24.00%** (below 32.35%).
- Interpretation: automated prior-month interaction discovery finds a real-looking **narrow high-precision pocket around pressure on boat1**, and is the first cross-month interaction test to edge above the Wave9 20R/half ceiling. It does not yet scale in volume; larger-support transfer deteriorates sharply.

## BEFORE WORK — Broad50 Wave12 January-frozen interaction ensemble / union expansion (2026-09-18)
- Goal: test whether the narrow ~40% cross-month interaction pocket can be expanded in volume without selecting ensemble rules from February.
- Reconstruct the exact Wave11 January discovery/freeze procedure. For each unique frozen interaction, choose its representative setting using January worst-half precision/support only.
- Build January-only ensemble candidates over the top representative interactions: top-N sets (3/5/8/12/20/all available), vote thresholds including union (k=1), small-k consensus, and fractional-majority gates.
- Select/freeze ensemble definitions using January only, stratified by useful support. February does **not** select N, k, members, thresholds, windows or formula settings.
- Replay the frozen ensembles once on February and report worst-half precision at >=20/30/50/75/100 races per half. Primary comparison is Wave11 40.0% at >=20R/half and Wave9 volume ceilings.
- March remains unopened; September outcomes UNREAD; production v288 unchanged.


## AFTER WORK — Broad50 Wave12 January-frozen interaction ensemble result (Run 35316568275, 2026-09-18)
- SUCCESS: Run **35316568275** / Job **105509396833** / Artifact **10535217625**; head SHA **da6f4e9189027815dd6217d142046f6347cd161b**.
- January-only ensemble search itself produced strong in-sample stability (e.g. n_top=12,k=3: Jan H1 24/43=55.81%, H2 16/29=55.17%; n_top=20,k=5 at >=30R: 27/53=50.94%, 19/37=51.35%).
- But the frozen January ensembles did not transfer to February:
  - >=20R/half: best Feb H1 9/24=37.50%, H2 13/38=34.21%, worst-half **34.21%**, combined 22/62=35.48%.
  - >=30R/half: worst-half **34.00%**, combined 29/83=34.94%.
  - >=50R/half: worst-half **26.25%**, combined 54/195=27.69%.
  - >=75R/half: worst-half **26.25%**.
  - >=100R/half: worst-half **21.60%**, combined 88/370=23.78%.
- This is materially below Wave11's narrow single-interaction pocket (40.0% at >=20R/half) and below Wave9 at useful volumes. Conclusion: January-only voting/union over frozen interactions amplifies month-specific overfit rather than producing robust volume.
- March unopened; September UNREAD; production v288 unchanged.

## BEFORE WORK — Broad50 Wave13 multi-month persistent interaction freeze (2026-09-18)
- Goal: remove the remaining prior-month overfit by requiring interaction settings to survive **both December and January** before any February evaluation.
- Use November 2025 only as history for December walk-forward; December outcomes are first validation month. January is second validation month. February is a one-shot transfer month and does not select formulas/settings.
- Enumerate the same 19 oriented PRE base signals and pair interactions. For each exact candidate setting (window/mode/band/interaction/q), compute December H1/H2 and January H1/H2. Rank by the minimum rate across all four half-month blocks, with support/venue floors enforced in both months.
- Build triple vocabulary only from signals appearing repeatedly among pair candidates that are jointly stable in December+January. Triple settings must also pass the same two-month persistence test before freeze.
- Freeze candidate settings separately for minimum support 15/20/30/50/75/100 per half-month, deduplicate exact definitions, and then evaluate the frozen set once on February.
- Primary output is February worst-half support frontier vs Wave11 (40.0% at >=20R/half) and Wave9. No March. September UNREAD; production v288 unchanged.


## AFTER WORK — Broad50 Wave13 multi-month persistent interaction transfer (Run 35317690758, 2026-09-18)
- SUCCESS: Run **35317690758** / Job **105512857146** / Artifact **10535234565**; head SHA **4b2c2660e27fc7231e9ba761863deadb6e85d4bb**.
- Source/audit clean: Nov 3,825R / Dec 4,647R / Jan 4,963R / Feb 3,970R; February canonical-vs-realtime winner agreement remained 100%; previous-session date violations remained 0. March unopened; September UNREAD; production v288 unchanged.
- Used the same 19 oriented PRE signals -> 171 pair interactions; triple vocabulary was derived only from interactions jointly stable in December+January. Candidate settings were frozen using the minimum rate across Dec H1 / Dec H2 / Jan H1 / Jan H2, with venue/support floors, before February was scored.
- Interesting pre-Feb persistence existed: at >=15R/half-month, pair vs1 national2 × vs2 national2 reached persistent worst 50.0%; at >=20R, best persistent worst was 40.74%; at >=30R 37.93%; >=50R 37.74%; >=75R 36.05%; >=100R 34.62%.
- Frozen set: **222 settings / 28 unique interactions**.
- One-shot February transfer:
  - >=20R/half: best H1 **7/22=31.82%**, H2 **11/29=37.93%**; worst-half **31.82%**, combined 18/51=35.29%. Formula: positive window42 / R1-8 / q=.925, b1_pressure × vs1 national2 × b2_wall_break.
  - >=30R/half: H1 10/30=33.33%, H2 13/41=31.71%; worst-half **31.71%**, combined 23/71=32.39%.
  - >=50R/half: H1 16/53=30.19%, H2 20/64=31.25%; worst-half **30.19%**, combined 36/117=30.77%.
  - >=75R/half: worst-half **25.0%**, combined 55/183=30.05%.
  - >=100R/half: worst-half **24.0%**, combined 62/213=29.11%.
- Comparison: Wave13 is worse than Wave11 at >=20R (-8.18pt) and worse than Wave9 at every support tier. It only marginally exceeds Wave11 at >=50R (+1.62pt), while still well below Wave9.
- Conclusion: requiring December+January persistence does not rescue fixed multiplicative interactions. There are strong-looking interaction pockets in individual prior months, but they do not transfer reliably into February. This materially strengthens the conclusion that the current PRE feature family is regime-sensitive/nonstationary rather than missing only a simple interaction formula.
- Recommended next direction: stop searching more static pair/triple products from the same signals. If continuing with current PRE only, move to regime detection / conditional model selection (learn which interaction family is active from contemporaneous PRE distribution without target labels), or switch objective from raw head-rate to odds-aware EV where 30-40% pockets may still be valuable.


## BEFORE WORK — Broad50 Wave14 PRE-distribution regime switching (2026-09-18)
- Wave13 strengthens the nonstationarity hypothesis: fixed pair/triple interactions can look strong in prior months but do not transfer reliably. Wave14 therefore changes the mechanism rather than searching more static formulas.
- Regime assignment must use **PRE distribution only**. No outcome, payout, exhibition or same-day result enters regime features.
- Build one descriptor per race day from the cross-race distribution of the existing 19 oriented PRE signals (median / upper quartile / positive-share). Fit StandardScaler + KMeans on **Nov+Dec+Jan descriptors only** for K=2/3/4; assign February days using the frozen scaler/centroids.
- Candidate interaction library is fixed before February: all 171 pairs from the 19 signals plus the 56 triples from the Wave11 January-only top-8 signal vocabulary. Do not add formulas based on Wave11/12/13 February results.
- For each pre-Feb regime cluster, evaluate each exact interaction setting separately on Nov / Dec / Jan using leakage-safe daily walk-forward scores. Candidate settings must have minimum per-month cluster support; rank by the **worst monthly head rate** across Nov/Dec/Jan, then combined rate/support.
- Freeze regime selectors for K=2/3/4, per-cluster support floors 5/8/12/16, and top-1 or top-2 union per cluster. Every selector definition is frozen from Nov-Dec-Jan only.
- Pre-Feb selector diagnostics must report each month H1/H2 support/rate. February is then a one-shot transfer: each day is assigned a regime from PRE descriptors and only the frozen interaction(s) for that regime may fire.
- Primary February comparison remains worst-half rate at >=20/30/50/75/100 races per half versus Wave9. March stays unopened. September outcomes UNREAD; production v288 unchanged.


### Wave14 failure/repair note (Run 35318413001)
- Initial Wave14 Run **35318413001** / Job **105515130842** failed before any regime-transfer result was produced.
- Cause: some daily regime descriptor columns were entirely missing/NaN across Nov-Dec-Jan, so the historical median itself was NaN and KMeans rejected the matrix.
- Repair is implementation-only: drop descriptor dimensions with no finite historical median, median-impute the remaining dimensions, and fail if fewer than 5 finite regime features remain. Research definitions (K values, interaction library, support floors, February protocol) are unchanged.
- Performance-only improvement in the same repair: candidate statistics are scanned once per K and cached for all support/top-N variants; research gates are unchanged.
- A fresh run from current main is required; do not reuse failed Run 35318413001.


## AFTER WORK — Broad50 Wave14 PRE-distribution regime switching (Run 35318638285, 2026-09-18)
- Initial Run 35318413001 failed before results because 3 descriptor dimensions were all-NaN across the historical regime-fit window. Implementation-only repair dropped all-NaN dimensions, median-imputed the remaining 54 descriptor dimensions, and cached candidate scans. Fresh Run **35318638285** / Job **105515840810** / Artifact **10536705768** succeeded; head SHA **ad493755bf5de44199cfe8cae605e1e53aa844ae**.
- Regime definition used PRE distribution only: 19 oriented signals × median/q75/positive-share, KMeans K=2/3/4 fitted on Nov+Dec+Jan descriptors without outcomes. Candidate library: 171 pairs + 56 fixed pre-Feb triples = 227 interactions / 43,584 settings.
- 24 regime-selector variants were constructed entirely from Nov-Dec-Jan. Only 2 unique selectors survived the pre-Feb half-month support/venue freeze.
- Best precision pre-Feb selector (K=2, cluster floor16, top1) had persistent worst half **47.83%**, combined **55.56%** across Nov-Dec-Jan. February one-shot: H1 **5/10=50.0%**, H2 **9/25=36.0%**, total 14/35=40.0%; H1 support/venue dispersion was too small for the >=20R/half frontier.
- Broader selector (K=4, cluster floor8, top2) had pre-Feb persistent worst **46.67%**, combined **54.59%**. February one-shot: H1 **5/18=27.78%**, H2 **14/42=33.33%**, total 19/60=31.67%.
- Therefore February support frontier had **0 eligible selectors** at >=20/30/50/75/100 races per half. Regime switching did not rescue useful-volume transfer; the high pre-Feb precision again collapsed or lost support in February.
- Conclusion: within the current 19-signal PRE family, static interactions, multi-month persistence, voting/union, and PRE-distribution regime switching have all failed to produce a robust useful-volume 40-50% selector. March remains unopened; September UNREAD; production v288 unchanged.

## BEFORE WORK — Wave15 unused PRE field audit (2026-09-18)
- Before abandoning PRE head-rate research, audit the raw BoatraceCSV program sources for PRE columns that the current feature builder never consumes.
- Compare actual schemas and non-null/cardinality coverage for race_cards, recent_national and recent_local over representative pre-Feb dates. Classify every field as: currently used, identifier/text-only, potentially numeric/categorical PRE, current-meet/session-derived, or post-exhibition/unsafe.
- Explicitly preserve the current rule that current-meet session fields are excluded unless independently shown to be pre-deadline and leakage-safe. Exhibition/original-exhibition remains excluded from PRE.
- If materially useful unused PRE fields exist with broad historical coverage, next wave should add only those fields and repeat strict time-split/walk-forward validation. If none exist, shift the research objective to odds-aware EV or external PRE sources.
- March outcomes stay unopened for this audit. September outcomes UNREAD; production v288 unchanged.


## AFTER WORK — Wave15 raw PRE schema audit (2026-09-18)
- Compared the current feature builder against actual BoatraceCSV race_cards / recent_national / recent_local schema. The current builder consumes only 13 race-card performance fields plus aggregated finish strings and date-derived recency.
- Material unused **pre-race** fields found in race_cards: racer age, class (級別), period (期別), branch/origin, prize-exclusion flag, motor/boat flags, and 早見 (same-day other-race schedule). Registration/name and motor/boat IDs are identifiers and should not be used as naive ordinal predictors.
- Material unused fields in recent_national/recent_local: per-meet grade, per-meet venue, and exact per-meet finish sequences. Current features collapse all five meets into aggregate finish rates, losing last-meet/second-meet form and competition-grade context. Start/end dates are already audited and used for fail-closed recency.
- Current-meet 節D1..D7 fields remain excluded by policy. Exhibition/original-exhibition remain post-PRE and excluded. No change to production v288; March outcomes remain unopened; September UNREAD.

## BEFORE WORK — Broad50 Wave16 enhanced unused-PRE transfer test (2026-09-18)
- Add only generalizable, leakage-safe derived fields from the audited unused schema; do not use racer name, raw registration number, raw motor/boat number, or current-meet outcomes.
- New race-card features per boat: age, period number, ordinal class score (A1>A2>B1>B2), prize-exclusion indicator, motor/boat flags, home-branch-at-current-venue indicator, same-day-other-race flag, second-appearance flag, and other-race number delta.
- New historical-meet features per boat/source: exact last-meet and second-meet starts/mean/win/top2/top3, last/mean/max grade score, grade-weighted finish rates, national recent venue diversity and same-current-venue share. All prior-meet end dates must remain strictly < target date.
- Create boat3-vs-1/2/4 and inner-mean gaps for the new numeric fields; keep raw six-boat values so models can learn non-monotonic age/experience effects.
- Compare two model families under an identical leakage-safe daily walk-forward protocol: BASE=current sig_* features vs ENHANCED=BASE+new PRE features. Freeze model/window/band/percentile settings using Nov-Dec-Jan only, ranked by minimum H1/H2 rate across all three months with support/venue floors. February is a one-shot transfer.
- Primary output: Feb worst-half support frontier at >=20/30/50/75/100 per half for BASE vs ENHANCED. Improvement only counts if ENHANCED beats BASE and Wave9 at the same support tier. March unopened; September UNREAD; production v288 unchanged.


## AFTER WORK — Broad50 Wave16 enhanced unused-PRE transfer (Run 35319514745, 2026-09-18)
- SUCCESS: Run **35319514745** / Job **105518649837** / Artifact **10536369864**; head SHA **a934ec7b8c8aa667ea2b202d2b9a27c31fdd36fe**.
- Source integrity: Nov 3,825R / Dec 4,647R / Jan 4,963R / Feb 3,970R; Feb canonical-vs-realtime winner agreement **3970/3970 = 100%**. March unopened; September UNREAD; production v288 unchanged.
- Feature counts: BASE **128**; new unused-PRE derived features **242**; ENHANCED **370** total. Added leakage-safe fields from age/class/period/branch/other-race schedule and exact recent-meet/grade/location context; current-meet 節D1..D7 and exhibition remained excluded.
- IMPORTANT methodology note: the JSON `feb_support_frontier` selects the best row among the already frozen candidate pool using February labels and is therefore **diagnostic only**, not a deployable one-shot result. Formal result must use the single pre-Feb best row selected from Nov-Dec-Jan for each support stratum before opening February.
- Formal pre-Feb-frozen BASE results on February:
  - support15/20 freeze: H1 16/45=35.56%, H2 20/65=30.77%, combined 36/110=32.73%, worst-half **30.77%**.
  - support30 freeze: H1 27/90=30.00%, H2 36/126=28.57%, combined 63/216=29.17%, worst-half **28.57%**.
  - support50 freeze: combined 76/263=28.90%, worst-half **28.32%**.
  - support75 freeze: combined 49/164=29.88%, worst-half **27.69%**.
  - support100 freeze: combined 110/394=27.92%, worst-half **27.72%**.
- Formal pre-Feb-frozen ENHANCED results on February:
  - support15 freeze: H1 15/40=37.50%, H2 16/52=30.77%, combined 31/92=33.70%, worst-half **30.77%**.
  - support20 freeze: H1 28/82=34.15%, H2 33/111=29.73%, combined 61/193=31.61%, worst-half **29.73%**.
  - support30 freeze: H1 19/55=34.55%, H2 26/75=34.67%, combined **45/130=34.62%**, worst-half **34.55%**. This is the strongest strict Wave16 result and materially better than the strict BASE support30 row (28.57%), but still below 40%.
  - support50 freeze: combined 68/225=30.22%, worst-half **27.27%**.
  - support75 freeze: combined 97/361=26.87%, worst-half **25.00%**.
  - support100 freeze: combined 115/447=25.73%, worst-half **24.51%**.
- Diagnostic-only February frontier among the pre-frozen pool reached ENHANCED worst-half **34.55%** at >=20/30/50 support (130R combined), vs BASE **32.54%** (298R combined). This shows the unused PRE fields contain real incremental signal, but candidate choice using February labels must not be promoted.
- Conclusion: adding previously-unused leakage-safe PRE improves some medium-support transfer (especially support30), but does **not** produce a robust 40-50% useful-volume selector. The strongest strict result is ENHANCED 130R / 45 heads = 34.62% combined with 34.55% worst-half. Continue only with genuinely new information/representation; do not keep tuning thresholds against February.


## BEFORE WORK — Broad50 Wave17 ~50 races/month precision target (2026-09-18)
- User explicitly changed the operational volume target: **~50 races/month is sufficient**. Previous support targets of ~100-300 races/month are no longer necessary.
- Reuse Wave16 ENHANCED leakage-safe PRE family (370 total features) and daily walk-forward protocol; do not add new raw fields in this wave.
- Candidate settings are frozen from Nov-Dec-Jan only. Target practical monthly volume **40-70 races/month** in each pre-Feb month, with half-month minimum support >=8 and >=6 venues per half. Also report a slightly wider 30-80/month diagnostic.
- Expand score thresholds into the extreme tail: q = .95/.96/.97/.975/.98/.985/.99/.9925/.995, because the user now accepts much lower volume in exchange for precision. Bands include R1-4/R1-6/R1-8/R1-10/R1-12; windows 21/42; model score = logit/hist/mean.
- Freeze primary candidate by maximum **worst half-month head rate across all six Nov/Dec/Jan halves**, then persistent combined rate, then closeness of average monthly volume to 50. No February label may affect candidate choice.
- February is reference one-shot for the frozen candidate. Because February has already been inspected in prior waves, label this result as NON-PRISTINE/reference, not a new untouched holdout. March stays untouched in this wave; September UNREAD; production v288 unchanged.


## AFTER WORK — Wave17 ~50 races/month precision target (Run 35325973943, 2026-09-18)
- SUCCESS: Run **35325973943** / Job **105538984352** / Artifact **10538494568**; head SHA **198620ffea0baf18efc343ea4dcd7cb337454d5f**.
- User operational target changed to ~50 races/month. Wave17 therefore searched only high-score ENHANCED candidates around 40-70 races/month pre-Feb, using Nov-Dec-Jan for freeze and February as NON-PRISTINE reference only. March remained unopened; September UNREAD; production v288 unchanged.
- 8 strict 40-70/month candidates and 26 wide 30-80/month candidates were found.
- Primary pre-Feb candidate: ENHANCED / trailing window42 / races R1-8 / logistic percentile q=.99.
  - Nov: 41R / 14 heads = **34.15%**; H1 7/17=41.18%, H2 7/24=29.17%.
  - Dec: 41R / 13 heads = **31.71%**; H1 5/13=38.46%, H2 8/28=28.57%.
  - Jan: 46R / 17 heads = **36.96%**; H1 13/32=40.63%, H2 4/14=28.57%.
  - Pre-Feb average volume **42.67 races/month**; total 128R / 44 heads = **34.38%**; persistent worst half-month **28.57%**.
- February NON-PRISTINE reference for the frozen candidate: H1 3/5=60.0%, H2 8/25=32.0%, total **11/30=36.67%**, worst-half 32.0%. February volume fell below the desired 40-70 band, so this is not yet a production-ready ~50/month selector.
- A candidate centered even closer to 50/month existed (window42 / R1-12 / logistic q=.99): pre-Feb avg 49.67/month, but persistent worst half-month only **25.0%** (Nov 49R/16=32.65%, Dec 47R/13=27.66%, Jan 53R/19=35.85%). Thus simply forcing exact 50/month worsened stability.
- Conclusion: lowering the volume target from ~130/month to ~50/month helps concentration, but the current ENHANCED PRE model still does not show a stable 40-50% head rate across prior months. Best pre-Feb precision/stability compromise is about **34-35% at ~43 races/month**. Do not claim 50% achievable yet from this family.


## BEFORE WORK — Wave18 causal course/ST/deciding-move PRE enrichment (2026-09-18)
- User asked to add genuinely new information and test again after Wave17 remained ~34-35% at ~43 races/month.
- Raw BoatraceCSV `results/realtime` was verified to contain **actual course -> boat number, actual ST, F flag, winner and deciding move**. `race_cards` provides racer registration number by boat. Therefore course-specific racer history can be reconstructed causally without using the repository's current precomputed estimate tables.
- Do **not** consume present-day `data/estimate/racer_st` or `course_win_rate` snapshots because their historical training cutoff is not guaranteed for old target dates. Rebuild all added features from archived daily result/race-card files with a strict `< target date` cutoff.
- Historical source window begins 2025-04-01. For every target day Nov 2025-Feb 2026, freeze the course-history state before processing that day's results; same-day earlier race outcomes are deliberately excluded.
- New causal PRE features per racer at expected pre-race course (= frame number): historical starts, shrunk win/top2/top3 rate, average/ST SD, exponentially weighted ST, actual-course-vs-frame stability, and winning-move rates. Key explicit concepts: boat3 course-3 win/ST/makuri/makuri-sashi; boat1 course-1 win/escape; boat2 course-2 wall/ST; boat4 course-4 counter/ST.
- New venue priors: venue×course win rate and venue×race-number×course win rate, both computed only from prior dates with shrinkage toward the historical global course rate.
- Add derived matchup gaps (3 vs 1/2/4 course win strength and ST edge) and attack/defense composites. Raw racer IDs are join keys only and must not enter the model numerically.
- Compare ENHANCED (Wave16 370 PRE features) versus COURSEPLUS (ENHANCED + causal course/ST/move features) under the same leakage-safe daily walk-forward model. Operational target remains ~50 races/month: candidate freeze on Nov-Dec-Jan only with 40-70 races/month, half-month >=8R and >=6 venues, high percentile thresholds .95-.995. February is NON-PRISTINE/reference only. March stays unopened. September outcomes UNREAD. production v288 unchanged.


### Wave18 implementation-failure note (2026-09-18)
- Run **35328363382** / Job **105546668199** reached the post-feature candidate-evaluation stage but failed before producing a research result.
- Exact cause: candidates with a zero-support half-month had `rate=None`; `pre_metrics()` called `min()` across those values and raised `TypeError`. This is an implementation bug only; course-history reconstruction itself completed.
- Fix commit **97bd4de7794381783fc01084c518618a1111c734**: zero-support candidates receive `persistent_worst=-1` and are naturally rejected by the existing support/rate eligibility gate. No feature, threshold, monthly-volume rule, or train/test split changed.
- Fresh run from current main is required; failed Run 35328363382 must not be used as a result.


## AFTER WORK — Wave18 causal course/ST/deciding-move enrichment (Run 35329805431, 2026-09-18)
- SUCCESS: Run **35329805431** / Job **105551285628** / Artifact **10540539135**; head SHA **97bd4de7794381783fc01084c518618a1111c734**.
- Causal history source: 2025-04-01..2026-02-28; 334 calendar days checked, 302 race-card days, 120 result days, 17,510 matched result races, 104,834 boat-course events. Same-day outcomes were explicitly excluded; all course-history features used only prior dates.
- Added **120 new causal course-history features** to Wave16 ENHANCED 370 features = **COURSEPLUS 490 features**. Included expected-course racer win/top2/top3, avg/ST SD/EWMA ST, frame-to-course stability, deciding-move rates, venue×course and venue×race-number×course priors, and boat3-vs-1/2/4 course/ST matchup gaps.
- Operational target remained 40-70 races/month, frozen on Nov-Dec-Jan only, February NON-PRISTINE reference only. March unopened; September UNREAD; production v288 unchanged.
- 10 strict 40-70/month candidates and 22 wide 30-80/month candidates existed.
- Primary strict COURSEPLUS candidate: trailing window21 / all R1-12 / logistic percentile q=.9925.
  - Nov: 43R / 12 heads = **27.91%**; H1 6/17=35.29%, H2 6/26=23.08%.
  - Dec: 62R / 18 heads = **29.03%**; H1 11/30=36.67%, H2 7/32=21.88%.
  - Jan: 56R / 24 heads = **42.86%**; H1 15/31=48.39%, H2 9/25=36.00%.
  - Pre-Feb total **161R / 54 heads = 33.54%**, avg **53.67R/month**, persistent worst half-month **21.88%**.
- February NON-PRISTINE reference for the frozen candidate: H1 5/13=38.46%, H2 13/43=30.23%, total **18/56=32.14%**, worst-half 30.23%.
- Wave17 baseline was pre-Feb total 128R/44 heads = **34.38%**, avg 42.67R/month, persistent worst half 28.57%; Feb reference 36.67%. Therefore COURSEPLUS was **worse** on both pre-Feb combined precision (-0.84pt) and temporal stability (-6.70pt), and worse on Feb reference (-4.52pt).
- Several COURSEPLUS settings show strong January rates (roughly 40-47%) but materially weak November/December rates (roughly 19-32%), confirming severe temporal instability rather than a missing static course-history signal.
- Conclusion: adding causal actual-course/ST/deciding-move/venue-course history did **not** break the ~34-35% ceiling. The new course-history family should not be promoted. Current evidence strongly suggests the remaining limitation is not simply absence of course-specific historical strength; future research should shift toward a qualitatively different information source or objective rather than stacking more historical PRE aggregates.


## BEFORE WORK — Wave19 PRE→motor→exhibition head-gate research (2026-09-18)
- User approved shifting 3-head research from additional static PRE history to **motor current-form + exhibition**.
- Prior exhibition-v5 work is explicitly not reused as a direct ranking model: corrected Feb A/B/C audit on 390 common-ready 3-head races found A=static only capture 37.18%, B=+展示/展示ST 36.67%, C=+original exhibition 34.62%; therefore adding exhibition directly to second/third-place ranking was REJECTED. Wave19 instead uses exhibition only as a **head yes/no gate** after a broad PRE candidate.
- Architecture: (1) ENHANCED PRE daily walk-forward score creates a broad candidate universe; (2) causal motor current-form features from venue+motor number history refine candidate quality; (3) post-exhibition features decide whether boat 3 is sufficiently strong *today*. Final operational target remains ~40-70 races/month, ideally ~50.
- Motor state is rebuilt causally from archived race_cards + results/realtime. For each target day, snapshot before ingesting that day's results. Features: venue+motor starts, shrunk win/top2/top3, mean/EMA rank, mean/EMA actual ST, and boat3-vs-1/2/4 motor gaps. Raw motor number is a join key only.
- Exhibition source is archived previews/tkz + previews/stt + previews/original_exhibition. Common-ready requires all-six 展示タイム and スタート展示. Head features include boat3 field-relative exhibition time, start-exhibition edges vs 1/2/4, exhibition course shift, tilt/weight-adjustment, and available original-exhibition turn/straight/lap relative edges. Original metrics are optional with explicit availability flags.
- Post models are daily rolling logistic gates, trained only on prior days. Compare PRE-only, MOTOR, EXHIBIT, and BOTH (motor+exhibition) using the same PRE score as an input. No same-day result enters training.
- Freeze broad PRE threshold + post-score threshold using Nov-Dec-Jan only. Candidate grid targets final 40-70 races/month in each month, half-month >=8 and >=6 venues. Rank by worst of six half-month head rates, then combined rate, then closeness to 50/month. February is NON-PRISTINE/reference only; March remains unopened. September **2026** outcomes remain UNREAD; production v288 unchanged.


### Wave19 implementation / active run checkpoint (2026-09-18)
- Added `research/run_3head_wave19_motor_exhibition_gate.py`: commit **e4e2e47d6209da5bb3ac0d0f82e3b02fc99835b5**.
- Added `.github/workflows/research-3head-wave19-motor-exhibition-gate.yml`: commit **761410a77c557235d3a4842fc177a75606643fa4**.
- Fresh official run **35336822315** / Job **105573463674** is currently executing from head SHA **761410a77c557235d3a4842fc177a75606643fa4**.
- The run compares four final head gates under identical Nov-Dec-Jan freeze rules: PRE, MOTOR, EXHIBIT, BOTH. Final target is 40-70 races/month. Motor state is snapshotted before same-day results; exhibition enters only after the broad PRE gate. February is reference-only; March/September-2026 remain unopened.
- Restart point if interrupted: check Run 35336822315. If success, extract best per variant + overall and append AFTER result. If failure, inspect Job 105573463674 logs and issue a fresh run after implementation-only repair.
