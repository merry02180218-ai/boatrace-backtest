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



### Wave19 failure/repair + official rerun (2026-09-18)
- Run **35336822315** / Job **105573463674** failed before producing results. Exact cause: October was incorrectly requested as a PRE-score target even though October is only the historical training month in the Wave17 protocol; its prediction frame could be empty, leading to `AttributeError: DataFrame has no attribute family`.
- Implementation-only repair commit **ebf7dc23095de8a0bab2702f2b1b49bd9d443377**: score only Nov-Dec-Jan-Feb and keep October as PRE history. Research gates/features/thresholds unchanged. Fresh Run **35345961408** started but is superseded by the performance-only rerun below.
- Performance-only commit **ec7ed0bcf300544c3b66fc02a2586bcab6d20a2d**: Wave19 uses only the frozen 42-day Logistic PRE score actually needed by the candidate grid, instead of recomputing unused 21-day and HistGradient models. Also removes unused September-2025 PRE build; October remains the training-history month exactly as in Wave17. No selection rule, labels, or feature definitions changed.
- New official fresh Run **35346043952** from head SHA **ec7ed0bcf300544c3b66fc02a2586bcab6d20a2d**. Use this run for the formal Wave19 result. Run 35345961408 is superseded even if it completes.


## AFTER WORK — Wave19 PRE→motor→exhibition head gate (Run 35346043952, 2026-09-18)
- Official fresh Run **35346043952** / Job **105602747195** / Artifact **10547641418** SUCCESS; head SHA **ec7ed0bcf300544c3b66fc02a2586bcab6d20a2d**.
- Source/audit: motor history snapshot is prior-day only (`same_day_results_used=false`); 243 motor-card days, 151 post/exhibition days, 104,837 motor events, 21,769 post rows, 16,179 common-ready exhibition rows. Added 68 motor features + 41 exhibition features. Feb winner cross-source check was 3970/3970 = 100%.
- Candidate grid 476 total; 10 candidates met the strict final 40-70 races/month rule across Nov-Dec-Jan.
- **PRE** best remained Wave17-equivalent: R1-8 / broad q=.99, Nov 41R, Dec 41R, Jan 46R; total **128R / 44 heads = 34.375%**, avg **42.67R/month**, persistent worst half **28.57%**. This was the overall best strict selector.
- **EXHIBIT** had 8 strict eligible selectors. Best: R1-12 / broad q=.99 / post q=.50. Nov 42R, Dec 44R, Jan 52R; total **138R / 43 heads = 31.16%**, avg **46.0R/month**, persistent worst half **22.58%**. Therefore the learned exhibition head gate **reduced** both precision and temporal stability versus PRE-only.
- **MOTOR** had **0** selectors satisfying 40-70R/month in every Nov-Dec-Jan month plus half-month support/venue gates. **BOTH (motor+exhibition)** also had **0** strict eligible selectors. Thus the learned post-score gates could not maintain the requested volume/stability envelope.
- February reference in this Wave19 output is NON-PRISTINE and should not be used as a formal comparison. PRE showed 13/32=40.63%; EXHIBIT 11/27=40.74%, but the runtime Feb frame contained 4,072 result-linked rows whereas the canonical Wave17 universe is 3,970. Cross-source overlap was perfect for the canonical 3,970, but the reference universe is not exactly identical, so formal conclusions are based on Nov-Dec-Jan only.
- Prior exhibition-v5 finding remains consistent: direct exhibition addition did not help pair ranking; Wave19 now also shows that a learned exhibition yes/no head gate does not improve stable 3-head precision at ~50R/month.
- Conclusion: current learned MOTOR/EXHIBIT/BOTH gates are REJECTED. PRE-only remains best at ~34.4%. If continuing this branch, do **not** add another generic classifier. Next justified test is an interpretable/manual relative gate on a broad PRE pool: e.g. boat3 exhibition-time rank/edge, start-exhibition edge vs 1/2, motor current-form edge vs 2/4, and conjunctions, with thresholds frozen on Nov-Dec-Jan and explicit volume frontier. March remains unopened; September-2026 outcomes UNREAD; production v288 unchanged.


## BEFORE WORK — Wave20 interpretable manual exhibition/motor gates (2026-09-18)
- User approved continuing after Wave19 rejected learned MOTOR/EXHIBIT/BOTH classifiers.
- Wave20 must **not** fit a second-stage black-box classifier. Reuse the frozen 42-day ENHANCED Logistic PRE score only as the broad candidate score, then apply explicit physically interpretable relative gates.
- Broad PRE grid: R1-8 / R1-12 and q=.90/.925/.95/.97/.98/.985/.99. Final operational target remains **40-70 races/month** in each Nov/Dec/Jan month, half-month >=8 races and >=6 venues.
- Manual exhibition primitives: boat3 exhibition-time rank/field edge; boat3-vs-2 and boat3-vs-inner exhibition edge; boat3 start-exhibition rank/field edge; boat3-vs-2 and boat3-vs-inner start edge; course-3 shift/fixed-course flags. Positive edge always means boat3 is better/faster.
- Manual motor primitives: boat3-vs-2 and boat3-vs-4 current motor top2/top3 gaps, EWMA-rank advantage, EWMA-ST advantage, and boat3-vs-inner motor advantage. Motor state remains strict prior-day only.
- Test single primitives plus predeclared 2-way/3-way conjunction families that represent an attack scenario (e.g. exhibition stretch + ST edge vs2; motor edge vs2 + exhibition edge; motor+exhibition+ST). Do not generate arbitrary feature products or fit labels into thresholds.
- Candidate selection is Nov-Dec-Jan only, ranked by worst of six half-month head rates, then combined rate, then closeness to 50 races/month. February remains NON-PRISTINE/reference only. March remains unopened; September-2026 outcomes UNREAD; production v288 unchanged.


### Wave20 implementation failure / repair (2026-09-18)
- Initial Run **35350314199** / Job **105616609920** failed after source build and gate evaluation began. Exact cause: some strict manual gates produced a zero-support half-month; `summary()` called `min()` across rates containing `None`, raising `TypeError`.
- This is implementation-only. Data retrieval, causal motor state, PRE score construction, and exhibition merge completed before the failure. No research result was produced and the failed run must not be used.
- Repair commit **02c6d4d74369482b187243e3d7ba1d2f4d0a0b04** assigns `persistent_worst=-1` whenever any half-month has no rate; such rows are then rejected by the unchanged support/venue eligibility gate. No thresholds, gate definitions, volume target, or train/test split changed.
- A fresh current-main run is required for the official Wave20 result.


## AFTER WORK — Wave20 interpretable manual exhibition/motor gates (Run 35351033915, 2026-09-18)
- Initial Run 35350314199 failed on zero-support `None` handling; implementation-only repair commit **02c6d4d74369482b187243e3d7ba1d2f4d0a0b04**. Official fresh Run **35351033915** / Job **105618951554** / Artifact **10549734884** SUCCESS; head SHA **02c6d4d74369482b187243e3d7ba1d2f4d0a0b04**.
- Audit: February canonical/realtime winner agreement **3970/3970 = 100%**; Feb frame canonicalized to exactly 3970. Motor state strict prior-day; no same-day results. 185 interpretable gates / 2,590 PRE+gate candidates; 298 strict candidates satisfied 40-70R/month in each Nov-Dec-Jan month and half-month >=8R / >=6 venues.
- PRE baseline reproduced: R1-8 / PRE q=.99, **128R / 44 heads = 34.375%**, avg 42.67R/month, worst half **28.57%**.
- Stability-first formal best was MOTOR_ST: R1-8 / PRE q=.925 / motor3 top2-rate edge vs boat2 >= +0.03 AND boat3 start-exhibition rank <=2. Nov 50R/16=32.0%, Dec 57R/17=29.82%, Jan 60R/21=35.0%; total **167R/54=32.34%**, avg55.67/month, worst half **29.41%**. It improves worst-half stability slightly but loses combined precision, so it is not a head-rate promotion candidate.
- Important precision clue: **MOTOR_EX** manual gate materially beat PRE combined precision. Candidate: R1-8 / PRE q=.95 / boat3 motor EWMA-rank advantage vs boat2 >=0 AND boat3 exhibition-time rank <=2.
  - Nov: **47R/18=38.30%** (H1 9/18=50.0%, H2 9/29=31.03%).
  - Dec: **60R/20=33.33%** (H1 7/25=28.0%, H2 13/35=37.14%).
  - Jan: **68R/31=45.59%** (H1 22/43=51.16%, H2 9/25=36.0%).
  - Combined **175R / 69 heads = 39.43%**, avg **58.33R/month**, worst half **28.0%**. This is +5.05pt combined vs PRE, but worst-half stability is 0.57pt lower than PRE.
  - February NON-PRISTINE reference: **34R/14=41.18%** (H1 46.15%, H2 38.10%). This is supportive only, not a clean holdout.
- A second MOTOR_EX variant (motor top2 edge vs2 >=0 + exhibition rank<=2, same R1-8/q=.95) reached **170R/65=38.24%**, avg56.67/month; Nov34.0%, Dec37.04%, Jan42.42%.
- MOTOR-only at exactly ~50/month also improved over PRE: R1-12/q=.985 + boat3 motor top2 rate >= boat2 motor top2 rate -> **150R/56=37.33%**, avg50.0/month; Nov38.78%, Dec31.37%, Jan42.0%; worst half27.27%.
- EXHIBIT-only best: R1-8/q=.95 + boat3 exhibition-time rank #1 -> **152R/54=35.53%**, avg50.67/month; only modest improvement over PRE.
- Learned Wave19 gates had failed, but Wave20 shows an interpretable relative **motor-vs-2 + exhibition-rank** gate contains incremental head signal. This is the first post-Wave17 branch to lift combined pre-Feb precision close to 40% at useful monthly volume.
- Do NOT promote yet: Nov-Dec-Jan were used for gate/threshold selection and February is NON-PRISTINE. The correct next step is to freeze the primary MOTOR_EX rule above **without any more threshold tuning**, then use still-unopened March as the one-shot diagnostic. If March is opened, no post-March retuning may be presented as holdout-valid.
- March remains unopened as of this AFTER record; September-2026 outcomes UNREAD; production v288 unchanged.


## AFTER WORK — Wave20 interpretable manual exhibition/motor gates (Run 35351033915, 2026-09-18)
- Official fresh Run **35351033915** / Job **105618951554** / Artifact **10549734884** SUCCESS; head SHA **02c6d4d74369482b187243e3d7ba1d2f4d0a0b04**.
- Feb universe was repaired to exact canonical 3,970R with realtime winner agreement **3970/3970 = 100%**. Motor state remained strict prior-day only; no same-day results; March unopened; September-2026 outcomes UNREAD; production v288 unchanged.
- Manual grid: 185 interpretable gates × PRE bands/thresholds = **2,590 candidates**. Strict 40-70/month eligible: **298**; wide 30-80/month: **673**.
- Formal overall ranking by persistent worst-half selected MOTOR_ST `m_top2_vs2_3__st_rank2` (R1-8, PRE q=.925): 167R/54 heads = **32.34%**, avg 55.67/month, persistent worst half **29.41%**. This is not the preferred precision candidate because combined head rate is low.
- Most important precision result: **MOTOR_EX** candidate `m_rank_vs2_0__ex_rank2`, R1-8, PRE q=.95:
  - Gate = boat3 prior-day motor EWMA-rank advantage vs boat2 **>= 0** (boat3 motor no worse than boat2) AND boat3 exhibition-time rank **<= 2**.
  - Nov **47R / 18 heads = 38.30%**.
  - Dec **60R / 20 heads = 33.33%**.
  - Jan **68R / 31 heads = 45.59%**.
  - Pre-Feb total **175R / 69 heads = 39.43%**, avg **58.33R/month**, persistent worst half **28.0%**.
  - Feb NON-PRISTINE reference: **34R / 14 heads = 41.18%** (H1 6/13=46.15%, H2 8/21=38.10%). This is reference-only, not a fresh holdout.
- Neighboring MOTOR_EX `motor_top2_vs2>=0 AND ex_rank<=2`, R1-8 PRE q=.95: **170R / 65 = 38.24%**, avg 56.67/month, showing the main effect is not unique to one motor encoding.
- Pure MOTOR candidate `motor_top2_vs2>=0`, R1-8 PRE q=.985: **131R / 50 = 38.17%**, avg 43.67/month. R1-12 q=.985 version lands exactly 50/month: **150R / 56 = 37.33%**.
- Pure EXHIBIT best `ex_rank3<=1`, R1-8 PRE q=.95: **152R / 54 = 35.53%**, avg 50.67/month. Thus exhibition alone adds modest precision; motor+exhibition together are materially stronger.
- START-only and EX_ST gates did not materially improve precision. Three-way MOTOR+EX+ST also underperformed the two-way MOTOR_EX signal, implying start exhibition adds noise once motor current-form + display rank are known.
- Compared with PRE-only Wave17-equivalent **128R/44 = 34.38%**, the best MOTOR_EX result improves combined head rate by about **+5.05pt** while keeping useful volume (~58/month). However temporal half-month stability is not improved (28.0% worst vs PRE 28.57%), so this is a promising research candidate, **not yet production promotion**.
- Next justified work: targeted local-neighborhood/stability audit around MOTOR_EX only (PRE q .925/.95/.97/.98, motor rank/top2 thresholds around neutral, exhibition rank 1/2/3 and modest edge thresholds), checking month/half/venue stability without opening March or retuning on February. Avoid broad new feature search.


## BEFORE WORK — Wave21 MOTOR_EX local-neighborhood stability audit (2026-09-18)
- Wave20 produced the first materially stronger interpretable candidate: PRE R1-8 q=.95 + boat3 motor EWMA-rank edge vs2 >=0 + exhibition rank <=2, 175R/69=39.43%, avg 58.3/month, but Dec=33.33% and persistent worst-half=28.0%.
- Wave21 is a **local stability audit only**, not a new broad feature search. Reuse the same causal PRE/motor/exhibition data construction and do not add new information sources.
- Search only neighboring MOTOR_EX gates: PRE q=.925/.95/.97/.98/.985; band R1-8 and R1-12; motor rank edge vs2 thresholds -0.20/0/.20/.40; motor top2 gap vs2 -0.03/0/.03/.05/.08; exhibition rank <=1/2/3; exhibition edge vs2 >= -0.02/0/.01/.02/.03. Also limited motor-inner/ex-rank variants as sensitivity checks.
- Strict volume remains 40-70 races in **each** Nov/Dec/Jan month, half-month >=8 and >=6 venues.
- Selection metric is predeclared for this stability audit: maximize **minimum monthly head rate across Nov/Dec/Jan**, then three-month combined head rate, then persistent worst-half rate, then closeness to 50/month. This directly addresses Wave20's December weakness while preserving useful volume.
- Report venue concentration and leave-one-venue-out combined rate range for the selected candidate to detect dependence on one venue. Candidate must not be promoted if one venue dominates or leave-one-venue-out behavior is unstable.
- February is reference-only and must not affect candidate selection. March unopened; September-2026 outcomes UNREAD; v288 unchanged.


## AFTER WORK — Wave21 MOTOR_EX local-neighborhood stability audit (Run 35357990437, 2026-09-18)
- SUCCESS: Run **35357990437** / Job **105641962771** / Artifact **10553536727**; head SHA **9b14ef8e44e72a7ff8d8f8762a82626e82a2467c**.
- Search was intentionally local around Wave20 MOTOR_EX only: 78 neighboring gates, 780 total PRE×gate candidates, 123 strict 40-70/month eligible. Feb canonical agreement remained **3970/3970 = 100%**. Motor history prior-day only; same-day results unused; March unopened; Sep-2026 UNREAD; v288 unchanged.
- Formal stability-rank winner (minimum monthly rate first): R1-8 / PRE q=.925 / `motor_inner_top2_gap >= .05` AND exhibition rank3 <=2.
  - Nov **40R/15 = 37.50%**
  - Dec **47R/20 = 42.55%**
  - Jan **63R/24 = 38.10%**
  - total **150R/59 = 39.33%**, exactly **50.0R/month average**; minimum monthly rate **37.50%**.
  - Half-month rates: 50.0%, 30.77%, 47.62%, 38.46%, 45.24%, 23.81%; persistent worst-half **23.81%**, so intra-month instability remains.
  - Venue audit is healthy: largest single venue share only **8.67%**; leave-one-venue-out combined rate range **37.76%-40.69%**, so the 39.33% is not explained by one venue.
  - Feb NON-PRISTINE reference: **36R/12 = 33.33%**. Therefore this exact stability-selected row does not transfer strongly to Feb.
- More important precision/stability neighborhood: R1-12 / PRE q=.925 / exhibition rank3 <=1 with boat3 motor EWMA-rank edge vs2 near neutral-positive is robust across nearby thresholds:
  - motor rank edge >= **0.00**: Nov 44R/17=38.64%, Dec 60R/22=36.67%, Jan 64R/30=46.88%; **168R/69 = 41.07%**, avg 56/month, min month 36.67%, worst half 28.57%.
  - motor rank edge >= **+0.20**: Nov 41R/15=36.59%, Dec 53R/20=37.74%, Jan 63R/30=47.62%; **157R/65 = 41.40%**, avg **52.33/month**, min month 36.59%, worst half 28.57%.
  - motor rank edge >= **-0.20**: Nov 47R/17=36.17%, Dec 66R/25=37.88%, Jan 70R/31=44.29%; **183R/73 = 39.89%**, avg 61/month, min month 36.17%, worst half 28.57%.
- This local plateau is important: the ~40-41% signal is **not a single knife-edge threshold**. The repeating structure is `boat3 exhibition-time rank = 1` plus `boat3 current motor EWMA rank not materially worse than boat2`, on a broad PRE q=.925 R1-12 pool.
- Compared with PRE-only 34.38%, this plateau gives about **+5.5 to +7.0 percentage points** pre-Feb at ~52-61 races/month.
- No production promotion yet. The current evidence supports freezing candidates before opening the pristine March diagnostic.
- PREDECLARED candidates for the next one-shot March diagnostic (freeze now; do not change after March labels are opened):
  - **A precision candidate**: R1-12 / PRE q=.925 / motor EWMA-rank edge vs2 >= **+0.20** / exhibition rank3 <= **1**. Pre-Feb 157R/65 = **41.40%**, avg 52.33/month.
  - **B stability candidate**: R1-8 / PRE q=.925 / motor inner top2 gap >= **+.05** / exhibition rank3 <= **2**. Pre-Feb 150R/59 = **39.33%**, avg 50/month, min-month 37.5%, but Feb reference 33.33%.
  - **Control**: Wave17 PRE-only R1-8 / q=.99.
- Restart point: if proceeding, run a single March diagnostic for exactly A/B/control, with no March-based tuning or additional thresholds afterward. Also report March volume/head rate and half-month/venue stability. If A fails materially, do not rescue it by adjusting thresholds against March.


## AFTER WORK — Wave20 interpretable manual motor/exhibition gates (Run 35351033915, 2026-09-18)
- Official fresh Run **35351033915** / Job **105618951554** / Artifact **10549734884** SUCCESS; head SHA **02c6d4d74369482b187243e3d7ba1d2f4d0a0b04**.
- Methodology: no second-stage black-box model. 185 explicit interpretable gates over causal prior-day motor state and archived exhibition/start/original-exhibition features; 2,590 PRE+gate candidates. Nov-Dec-Jan only for selection; February NON-PRISTINE/reference; March unopened; Sep-2026 UNREAD; production v288 unchanged. Feb canonical/realtime agreement 3970/3970 = 100%.
- Strict final volume rule (40-70 races/month each Nov-Dec-Jan, half-month >=8R and >=6 venues) retained **298** candidates; wide 30-80 retained 673.
- PRE-only baseline reproduced: R1-8 / q=.99, **128R / 44 heads = 34.375%**, avg 42.67R/month, persistent worst-half 28.57%.
- Highest combined-rate strict manual gate was **MOTOR_EX**: PRE R1-8 / q=.95 + `post_motor_rank_edge2 >= 0` + `post_ex_rank3 <= 2` (boat3 motor EWMA-rank no worse than boat2, and boat3 exhibition time top-2 of field).
  - Nov: **47R / 18 = 38.30%**
  - Dec: **60R / 20 = 33.33%**
  - Jan: **68R / 31 = 45.59%**
  - Combined: **175R / 69 = 39.43%**, avg **58.33R/month**; persistent worst half **28.00%**.
  - This improves combined head rate by **+5.05pt** versus PRE-only (39.43% vs 34.38%) while staying within the user's desired ~50R/month regime, though half-month stability does not improve.
  - Feb NON-PRISTINE canonical reference: **34R / 14 = 41.18%** (H1 46.15%, H2 38.10%). Treat only as supporting reference because Feb was already seen in previous waves.
- Second MOTOR_EX option: R1-8 / q=.95 + motor top2 gap vs2 >=0 + exhibition rank top2: **170R / 65 = 38.24%**, avg 56.67/month, worst-half 26.67%.
- MOTOR-only strong option: R1-8 / q=.985 + motor top2 rate vs2 >=0: **131R / 50 = 38.17%**, avg 43.67/month; Nov 40.0%, Dec 34.09%, Jan 40.43%, worst-half 26.32%.
- Exact ~50/month MOTOR option: R1-12 / q=.985 + motor top2 vs2 >=0: **150R / 56 = 37.33%**, avg exactly 50/month.
- EXHIBIT-only best: PRE R1-8 / q=.95 + boat3 exhibition-time rank 1st: **152R / 54 = 35.53%**, avg 50.67/month. Helpful but much weaker than MOTOR_EX.
- START-only, EX+ST, original-exhibition and triple motor+exhibition+ST gates did not beat the MOTOR_EX combined-rate result. Best stability-ranked overall candidate was MOTOR_ST (`motor top2 gap vs2 >=.03` + start-exhibition rank top2) with worst-half 29.41% but only 32.34% combined, so it is not the preferred precision candidate.
- Conclusion: unlike Wave19's learned post classifier, an interpretable manual gate **does reveal incremental signal**. The most promising branch is specifically **boat3 motor form relative to boat2 + boat3 exhibition-time rank**, not generic start-exhibition or original-exhibition metrics. This is the first new-information branch to lift the ~34-35% combined ceiling to ~39.4% at useful monthly volume. It still does not achieve robust 50% head rate and the month/half-month instability remains material.
- Recommended next research: narrow around the MOTOR_EX relationship only, preserving predeclared causal logic: vary PRE q/band minimally around the existing frontier and inspect motor-vs2 residual definitions + exhibition rank/edge thresholds. Do not reopen generic 185-gate search, do not tune on Feb, and keep March untouched until a single predeclared freeze candidate is chosen.
