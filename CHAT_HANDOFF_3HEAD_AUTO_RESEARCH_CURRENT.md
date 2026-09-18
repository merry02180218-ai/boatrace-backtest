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


## AFTER WORK — fun-site wide-schema baseline (Run 35296265896)
- SUCCESS: Run 35296265896 / Job 105449323190 / Artifact 10527334659.
- Head SHA f2730aeb81922a0f6c31d38c7e652f5e84ba4432; wide-schema parser commit 5b6b19de7e5c2d541ec5b6a50cbebdbfee911ae6.
- Sources 59/59 days each; fun-site 8,707 races; joined Feb 3,970 / Mar 4,482; 180 PRE features; current-meet session fields excluded; September outcomes UNREAD.
- March frozen one-shot: 50%-target 29R/6=20.69%; 45%-target 107R/36=33.64%; 40%-target 169R/59=34.91% (early 84/30=35.71%, late 85/29=34.12%).
- Conclusion: simple balanced logistic + one score threshold does NOT achieve 50%; do not promote.

## BEFORE WORK — broader 50% head-rate search (2026-09-18)
- User explicitly requests broader hypothesis search; do not stop at the 169R/59 baseline.
- Keep production v288 unchanged and September outcomes UNREAD.
- Search materially different PRE-only model families and interactions: nonlinear tree/boosting models, calibrated logistic variants, explicit boat3-vs-each-opponent matchup features, rank/margin features, recent national/local form interactions, venue/grade/race-number regimes where available, and ensemble/consensus gates.
- February remains the only model/threshold selection period; use chronological splits / stability constraints inside February. March labels are one-shot diagnostics per frozen candidate family, not iterative tuning feedback.
- Report Pareto frontier emphasizing >=50% March head rate with meaningful N; also >=45/40 bands, early/late stability, venue dispersion, and incremental/overlap versus prior 169R baseline/Wave54 where reproducible.
- Explicitly guard against tiny-N 50% artifacts and feature leakage.


## FULL HANDOFF — 3号艇「頭率50%を目指して母数を増やす」研究 (2026-09-18 current)

### User intent / restart instruction
- User's explicit priority: do NOT conclude from one logistic model that 50% is impossible. Explore many materially different possibilities and aim for **3号艇 head rate 50% while retaining/increasing race count**.
- Tiny-N 50% is not useful. Research direction is first >=100R at ~50%, then try to expand toward 150R/200R while preserving rate/stability.
- User wants execution, not narration. On restart read this handoff + latest GitHub first, preserve newer main changes, and record BEFORE/AFTER for each work unit.
- If an Actions run fails, inspect exact logs, fix automatically, and require a **fresh workflow_dispatch from current main**; do not tell user to rerun an old failed run because rerun keeps the old head SHA.

### Immutable / safety constraints
- v288 production remains unchanged unless explicitly promoted.
- September 2026 outcomes remain **UNREAD**; never use September result/payout for research selection.
- July/August 2026 are NON-PRISTINE/reference only.
- PRE/head-model inputs must be available pre-deadline. Do not use actual result/deciding move or current exhibition for this PRE head model.
- Current-meet session fields (fun-site race_cards 節D1..D7) are excluded in the current fun-site head-model work.
- Exact v288 exclusion set is preserved in the scripts.
- February is selection/training/stability period; March is frozen one-shot diagnostic. Do not iteratively tune conditions by reading March labels.
- Any future ROI work must use canonical v242 variable TopN / exact ¥10,000 Dutch / composite-odds methodology; do not invent fixed-ticket ROI.

### Canonical production context that must not be confused with this research
- Production-compatible leakage-free PRE replay before September: 94R / 52 heads = 55.319%; stake ¥940,000; payout ¥1,622,070; profit +¥682,070; ROI 172.560638%.
- Production lineage remains result-blind PRE -> exhibition/original exhibition/current odds -> v243 + v288 S/A/B -> v242 variable ticket count -> exact ¥10,000 Dutch.
- This broad fun-site work is DIAGNOSTIC RESEARCH only and has not been promoted.

### BoatraceCSV/fun-site source facts already verified
- Source repo: BoatraceCSV/fun-site.
- Historical URL pattern: https://boatracecsv.github.io/data/{kind}/{YYYY}/{MM}/{DD}.csv
- programs/race_cards, programs/recent_national, programs/recent_local are **one row per race, wide format**, keyed by レースコード; boat fields are 艇1_... through 艇6_....
- race_cards usable static PRE fields include national/local win/2連/3連, national average ST, F/L, motor 2/3連, boat 2/3連.
- recent_national/recent_local contain previous 1..5 meets and 着順列.
- previews/stt, previews/tkz, original exhibition are post-exhibition and are NOT PRE head inputs.
- Probe success: Run 35234503567 / Job 105246832483 / Artifact 10503470393.
- Initial parser failures were caused by wrongly assuming boat-level long format. Wide-schema fix commit: 5b6b19de7e5c2d541ec5b6a50cbebdbfee911ae6.

### First fixed fun-site head model baseline
Workflow: .github/workflows/research_3head_funsite_50pct.yml
Script: research/run_3head_funsite_50pct_model.py
Successful Run **35296265896** / Job **105449323190** / Artifact **10527334659**.
Run head SHA f2730aeb81922a0f6c31d38c7e652f5e84ba4432.
Data:
- source days: 59/59 for race_cards, recent_national, recent_local
- fun-site races 8,707
- joined Feb 3,970 / Mar 4,482
- 180 PRE features
- current-meet session fields unused
- September outcomes unread
Frozen March one-shot:
- 50%-target: 29R / 6 heads = **20.6897%**
- 45%-target: 107R / 36 = **33.6449%**
- 40%-target: 169R / 59 = **34.9112%**
- 169R split: early 84/30 = 35.7143%; late 85/29 = 34.1176%
Interpretation: simple balanced logistic + one threshold failed to transfer at 50%; **do not interpret this as proof that 50% is impossible**. Treat 169R/59 as a useful reference population.

### Broad-50 research implementation
User explicitly requested many more possibilities.
Research script created:
- research/run_3head_funsite_broad50.py
- initial commit be35161db6bd4dde75ef17b7e6d21d21ab8426fe
Workflow created:
- .github/workflows/research_3head_funsite_broad50.yml
- commit 385696c1f59c155aa6fb42c6d00a4a127d7d6929
Families currently coded:
- LogisticRegression
- ExtraTreesClassifier
- RandomForestClassifier
- HistGradientBoostingClassifier
- rank-average ensemble of the four
Features currently include 3号艇 own values plus explicit gaps vs boats 1/2/4/5/6, gap vs mean opponents, gap vs strongest opponent, national/local performance, average ST, F/L, motor/boat 2/3連, and previous national/local 5-meet finish summaries.
Research intent beyond current code: nonlinear interactions, matchup/rank/margin structures, recent-form interactions, venue/field/race-number regimes, model-consensus gates, and eventually overlap/increment vs Wave54 / 169R baseline.

### Broad-50 failures/fixes
First broad Run **35298355173** / Job **105455503615** failed.
Root cause: race number value like "08R" was passed to int due an escaped regex bug.
Fix commit **28cc9dcfb375fd8e01a04ba1e4fcaa3e5ac9101f**: strip non-digits correctly before int conversion.

Fresh broad Run **35302201814** / Job **105466992918** / Artifact **10529953805** then completed SUCCESS, head SHA ca953f3e2191fe8e79690f9b168a7a8d6f40ca70.
But output was not a meaningful research result:
- joined Feb 3,970 / Mar 4,482
- 196 features
- feb_candidates = []
- frozen 0.50/0.45/0.40 all null
- March results all null
Reason: discovery gate itself was too strict (prefix required >=20R at target rate, then Feb second validation required >=20R and target-0.05), so every family disappeared before March. This is **not** evidence that no 50% structure exists.

### Latest fix — CURRENT MAIN / NEXT RUN
Latest main at handoff time: **fafada437d6771bc5be14a476727b4133b246f0e**
Commit message: research: expose broad50 frontiers and relax Feb discovery gate.
Changes in research/run_3head_funsite_broad50.py:
- prefix discovery minimum reduced from 20 to 5 so high-precision small prefixes are visible during hypothesis discovery.
- Feb second stability gate reduced to >=10R and >= target-0.10; this is a discovery relaxation, NOT a production/adoption standard.
- Added mandatory diagnostic TopN frontiers for each base family at **N=10,20,30,50,75,100,150,200** on both Feb validation blocks.
- Purpose: even if frozen candidate selection rejects everything, we can see exactly how head precision decays as N grows and identify where ~50% survives.
- March remains one-shot only for candidates frozen from February.

### Exact next action
1. User needs a **fresh** dispatch of research-3head-funsite-broad50 from current main (not Re-run jobs on an old run). Workflow:
   .github/workflows/research_3head_funsite_broad50.yml
2. After user says 発火した / 終わった / どう, fetch latest run named research-3head-funsite-broad50 and verify head SHA is fafada437... or a later main containing it.
3. Inspect Job/log/Artifact. If failure, fix automatically.
4. If success, analyze diagnostic_topn for logit/extra/rf/hist and frozen/March results.
5. Specifically answer: for each model, what is the largest N in Feb validation blocks that stays near/above 50%; whether this is stable across both Feb blocks; what frozen candidates do on March; and whether any candidate reaches >=50% with meaningful N.
6. Do NOT stop if these four families fail. Next broaden hypotheses while keeping March untuned:
   - explicit rule/tree searches selected only from Feb, with minimum-support and two-block stability;
   - model intersection/consensus (e.g. top quantiles shared by 2/3/4 families), disagreement/margin gates;
   - separate attack archetypes: boat3 strong vs boat2 wall, boat3 strong vs boat1, weak boat4 counter, motor-edge + player-edge combinations;
   - rank features (boat3 rank among six in win rate/ST/motor/recent form) rather than only raw gaps;
   - venue/race-number/field archetype interactions, but enforce minimum support and dispersion to avoid one-venue overfit;
   - recent-national vs recent-local consistency/disagreement and recency-quality summaries;
   - verify previous-meet end dates are before target race date fail-closed before final leak-free claim;
   - reproduce Wave54 exact rule/race codes and report overlap/increment vs Wave54 210R/71 and fun-site 169R/59 baseline.
7. Search target remains **50% head rate with useful volume**, preferably >=100R, then expand toward 150/200R. Tiny-N 50% is diagnostic only.
8. Only after a genuinely frozen candidate exists should opponent mass / immediate pre-race correction / canonical v242 composite-odds ROI optimization be layered on.

### Wave54 / opponent reference retained
- Wave54 broad Q50 base 300R/87=29.0%; best volume-preserving Feb-derived refinement boat3 national2 - boat1 national2 >= +9.8pt => 210R/71=33.8095%; early104/36=34.6154%; late106/35=33.0189%. No ~200R frozen player/ST rule reached 35%.
- Wave55 opponent model on those 210R: Top3 opponent tickets captured 27/71=38.0282%, diagnostic fixed ¥100/ticket ROI106.8889%; this was diagnostic and not canonical production ROI.
- These are useful structural references, not reasons to stop head-model research.

### Handoff discipline
- Preserve all unrelated concurrent sections already in this handoff; do not overwrite them.
- Before each new research modification fetch latest main + latest handoff SHA.
- Append BEFORE before work and AFTER after verified Actions result with exact commit SHA / Run / Job / Artifact / conclusion / next restart.
- Never claim completion just because code was committed; verify the fresh Actions run.
