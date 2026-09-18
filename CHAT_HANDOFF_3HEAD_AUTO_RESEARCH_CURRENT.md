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
