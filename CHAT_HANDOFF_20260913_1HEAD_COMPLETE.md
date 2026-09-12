# CHAT_HANDOFF_20260913_1HEAD_COMPLETE

## Purpose
This is the complete handoff for the current boat-1 head model and its opponent-selection research. A fresh chat should read this file AND latest GitHub, with latest GitHub code/results taking precedence over this handoff if they conflict.

## Non-negotiable project rules
- Always inspect actual latest GitHub code/data before prediction, model changes, backtests, or conclusions.
- Latest GitHub wins over old chat/memory/handoffs.
- July/August 2026 are NON-PRISTINE / overfit and must not be treated as pristine validation.
- September 2026 outcomes are unread/outcome-blind unless latest repo explicitly changes this.
- Boat-1 losses remain misses in final exact-trifecta denominator. Never condition final exact hit rate only on boat-1 wins.
- Head model and opponent-selection model are separate. Head decides whether boat1 is winner; opponent model predicts exact `1-x-y` after selection.
- SECOND and conditional THIRD must remain separately attributable during research.
- Historical/player/motor/foot features must be available strictly before prediction time.
- `meet_*` is forbidden unless separately causally reconstructed and audited.
- Same-race/later-race results, end-of-day aggregates, post-race exhibition, payout/result fields, or future-contaminated reconstruction must never be predictors.
- Monthly walk-forward: month M trains only before M.
- Missing stacked p3/p4 must never be future-backfilled.
- Suspiciously large gains require a leakage/causal audit before acceptance.
- 204 races is NOT a fixed target. It is only a minimum floor. Fewer than 204 is unacceptable; more races are preferred if win rate is maintained/improved.

# 1. Historical boat-1 baseline and development path

## Original frozen 204-race baseline
Historical selected cohort was 204 races.
- head hits: 166/204 = 81.37%.

### v298 opponent baseline
Commit: `6e46239dbf2f7d6ecacf0cea5260d160ca4ce001`
CI: `34622447642` success.
Output commit: `d108efc59317b28d8b2b84adb9a9e6cbb1d9692`.
Summary: `summary_v298_1head_threat_listwise_trifecta5.md`.
Best stable zone `HGB_q0.950`, conf=.45:
- R=204
- head 166/204 = 81.37%
- exact 1pt 45/204 = 22.06%
- exact 2pt 82/204 = 40.20%
- exact 3pt 102/204 = 50.00%
- exact 4pt 108/204 = 52.94%
- exact 5pt 120/204 = 58.82%
- worst monthly head 78.38%
- worst monthly 5pt exact 50.00%
- exact settlement coverage 99.95%
Not promoted.

### v299
3-ticket policy search. CI `34624287429` success.
- R=204
- head 81.37%
- baseline TOP2XTOP2 alpha=.60 = 102/204 = 50.00%
- no ticket policy beat baseline.

### v300 opponent feature upgrade
Script: `run_v300_1head_trifecta3_feature_upgrade.py`
Commit: `c8e550b844c7f489cfa26f3e2743cf3bdc81bd3d`
Workflow fix: `c5ddc386e0db1c13429706e78ce4d15afa6e090d`.
Result:
- R=204
- BASE 102/204 = 50.00%
- all nine augmented configs 104/204 = 50.98%, +0.98pp
- tie-selected `AUG_s3_t0.1`
Monthly: Feb 44.44%, Mar 58.62%, Apr 48.65%, May 49.28%, Jun 52.94%.
Development only.

### v301 transfer experiment
Transferred 3-head/4-head feature families broadly into 1-head opponent model.
CI `34631767100` success.
- BASE 102/204=50.00%
- broad transferred version 100/204=49.02%
Conclusion: broad transfer hurt; v300 remained opponent dev best.

### v302 invalid experiment warning
Script `run_v302_1head_trifecta3_feature_ablation.py`.
Initial CI `34673974106` success technically but result INVALID because it selected 249 races instead of frozen 204.
Cause: selection was recomputed with v300 opponent probabilities instead of original baseline selector, causing gate drift.
Do NOT compare its 124/249 against 104/204.
If ever repaired, freeze exact original 204 IDs, assert selected==204 and head hits==166, then evaluate tickets on those IDs only.

# 2. Boat-1 head-model leakage investigation

### v303
Head transfer ablation, CI `34678292661`.
Suspicious results:
- ONLY_TURN_FORM 179/204=87.75%
- ONLY_WALL_INNER 175/204=85.78%
- ONLY_STMOTOR 173/204=84.80%
- BASE 166/204=81.37%.
Early months were suspiciously near 100%.

### v304
CI `34679297385`.
Best TURN_FORM + STMOTOR:
- 181/204=88.73%
- Feb/Mar/Apr 100%, May 89.86%, Jun 68.63%.
Suspicious and not accepted.

### v305 leakage audit
CI `34683451381`.
Summary `summary_v305_1head_leakage_audit.md`.
- V304_FULL 181/204=88.73%, worst 68.63%
- STRICT_TURN_FORM 168/204=82.35%, worst 78.38%
- STRICT_TURN_FORM_STMOTOR 168/204=82.35%, worst 72.22%
- BASE 166/204=81.37%.
Unsafe signals included six `meet_win` differences and three `meet_st_strength_motor` interactions because historical race-card snapshots were not intraday-versioned/proven available at prediction time.

### v306 unsafe attribution
CI `34685914583`.
Summary `summary_v306_1head_unsafe_feature_leavein.md`.
- BASE 166/204=81.37%
- STRICT_SAFE 168/204=82.35%
- FULL_ALL9 181/204=88.73%.
Largest unsafe feature was `v303_turn_form_b1_minus_b2_meet_win`, producing 182/204=89.22%.
Conclusion: v304 gain was mostly contaminated `meet_win`; do not use it.

# 3. v307 causal head reconstruction — accepted development basis

Script: `run_v307_1head_causal_turn_form.py`
Commit: `0be725a7fcdad17d0b980c5d5a68f57e1fd50626`
Workflow commit: `a0d51deb0b8b0f7d5c4fab0be93d46e883c46f21`
CI: `34687794250` success.
Summary: `summary_v307_1head_causal_turn_form.md`.

Causal provenance was audited through `analyze_v221_3head_scenario_pair.py::build()`:
- player/prior-exhibition histories frozen before current-day preview/results are ingested;
- same-day results not used;
- day-D historical traits frozen before ingesting day D;
- therefore `pl_*`, `vh_*`, `gh_*` from this path are prior-day safe.

Causal feature construction:
- `prior_form` = .35 all_win + .25 all_p2 + .20 frame_win + .10 frame_p2 + .10 recent_p2
- `frame_form` = .55 frame_win + .30 frame_p2 + .15 recent_p2
- `prior_foot` = mean available prior-day vh/gh p12 turn/straight/overall
- `start_motor` = nst_strength * motor when both available
- boat1 minus boat2..boat6 and max-opponent comparisons
- b1-vs-b2 interactions: prior_form×prior_foot, frame_form×prior_foot, prior_form×start_motor
- NO `meet_*`.

v307 results on original 204:
- STRICT_PLUS_CAUSAL 171/204 = 83.82%, +2.45pp vs BASE; worst month 78.43%
- STRICT_SAFE 168/204 = 82.35%
- BASE 166/204 = 81.37%
- CAUSAL_ONLY 164/204 = 80.39%.
Monthly best: Feb 83.33%, Mar 93.10%, Apr 86.49%, May 82.61%, Jun 78.43%.
Development only; prospective validation still required for promotion.

# 4. v308 current FIXED boat-1 head reference

Script: `run_v308_1head_volume_opponent_joint.py`
Initial commit: `33aebef48dbec21256f0d476fb9a404ae79a4916`
API fix commit: `07e1ae1b7c2aaa5d7e10215fde347b5ce729667c`
CI final run: `34689078192`, job `103541064770`, success.
Artifact `10296292759`, `v308-volume-opponent-joint`.
Summary: `summary_v308_1head_volume_opponent_joint.md`.

v308 used v307 leak-safe head features and jointly recomputed v300 opponent exact3 while allowing R>204.

## FIXED research operating point
- q=.980
- opponent mass >= .375
- **R=345**
- **boat1 head hits 290/345 = 84.06%**
- exact 3-ticket at that stage 132/345 = 38.26%
- worst monthly head 80.95%
- worst monthly exact3 30.43%.

Monthly:
- Feb 63R: head 51/63=80.95%, exact3 23/63=36.51%
- Mar 16R: head 15/16=93.75%, exact3 7/16=43.75%
- Apr 53R: head 48/53=90.57%, exact3 28/53=52.83%
- May 121R: head 101/121=83.47%, exact3 46/121=38.02%
- Jun 92R: head 75/92=81.52%, exact3 28/92=30.43%.

Important interpretation:
- compared with v307 171/204=83.82%, v308 expanded volume to 345 races (+69%) while slightly improving overall head rate to 84.06%.
- This is why the user explicitly froze the boat1 head model here.
- User instruction: `とりあえず頭モデルはこれで固定で`.
- Therefore current opponent research MUST NOT silently alter the 345 selected race IDs or 290 head-hit count.
- Every opponent experiment must assert R=345 and head hits=290 before scoring.

Caveat:
- v308 q threshold used a global Feb-Jun `p_head.quantile(q)` distribution. This uses no outcomes, so it is not label leakage, but it is not directly production-compatible calibration. Before promotion/live deployment it must be converted to prior-only or an absolute production-compatible threshold and prospectively validated.

# 5. Opponent selection reset after head freeze

User then explicitly requested opponent selection be rebuilt from scratch: `相手選びもう一度一から洗い直そう`.

## v309 zero-base audit
Script `run_v309_1head_opponent_zero_base_audit.py`
CI `34690019375` success.
Summary `summary_v309_1head_opponent_zero_base_audit.md`.
Frozen exact v308 345 IDs; asserts R=345/head hits=290.
Current benchmark opponent stack:
- SECOND v300 augmented listwise L2=3
- conditional THIRD v300 L2=.1
- TOP2XTOP2 alpha=.60.

Full denominator:
- exact3 132/345 = 38.26%.
On 290 boat1-head-win races:
- actual SECOND TOP2 = 71.72%
- actual THIRD TOP2 given actual SECOND = 72.76%.
Failure decomposition:
- SECOND outside TOP2: 82R = 28.28%
- SECOND in TOP2 but THIRD outside TOP2 given actual second: 51R = 17.59%
- combination/order miss: 25R = 8.62%
- exact3 hits 132R.

SECOND TOP2 by actual second boat:
- boat2 98.25%
- boat3 84.27%
- boat4 35.71%
- boat5 18.75%
- boat6 0%.
Conclusion: SECOND is primary bottleneck, especially outer boats 4/5/6.

# 6. v310 causal 3-head/4-head probability stacking

User idea: use 3-head and 4-head head probabilities as auxiliary opponent-selection signals.
Historical research must use causal month-by-month probabilities, never a future-trained frozen production model retroactively.

Script: `run_v310_1head_opponent_headrisk_second.py`
Initial commit `d0fe19895e94a691e7275229d779ea8eaeb2471b`
Workflow commit `5171a253f662896283ae49db49a5df552a0a790d`
Final sparse-coverage fix commit `ebb82bcbb7e718e20b72ab053c3a489a9670f9d2`.
Final CI run `34696379838`, job `103560468268`, success.
Summary `summary_v310_1head_opponent_headrisk_second.md`.
Dedicated handoff `CHAT_HANDOFF_20260912_1HEAD_OPPONENT_V310_RESULT.md`, commit `bd7ecda3c3ea6632e22243fee9c6b9608a04fc93`.

Causal p3:
- v242/v234/v223 monthly walk-forward `fit_head`, month M trained before M.
Causal p4:
- PRE rows from `analysis_v250_4head_rebuild_baseline.csv`, monthly walk-forward.
Missing p3/p4:
- neutral 0.0 + availability flags; NEVER future-backfilled.

Added SECOND features include p3head, p4head, attack34 max/sum/gap, candidate headrisk, candidate-role interactions and availability-role interactions.
THIRD held fixed at v300 `.1` to isolate SECOND changes.

Best `HEADRISK_L2_3`:
- SECOND TOP1 44.48%
- SECOND TOP2 **72.07%**, +0.34pp vs baseline 71.72%
- SECOND TOP3 86.90%
- exact3 **133/345=38.55%**, +1 race.
By actual second:
- boat2 TOP2 98.25%
- boat3 84.27%
- boat4 38.10% (improved from 35.71%)
- boat5 18.75%
- boat6 0%.
Conclusion: causal p3/p4 is useful but only a small auxiliary signal. It does not solve outer boat5/6 recovery.

# 7. v311 SECOND feature-family auto-research

Script: `run_v311_1head_opponent_second_family_autoresearch.py`
Script commit `a4a1cb84bf2f3982778f2fe878a8372a135e22c9`
Workflow commit `2eba72b0e1d68693e70c6e5b0b1dd5c3c7f7b71b`
Run `34696800597`.
Model calculation succeeded; final push conflicted, but computed development result is recorded in handoff.

Feature families:
- HEADRISK causal p3/p4
- START nst_strength
- MOTOR
- PLAYER `pl_*`
- FORM_STATIC grade/wr/local/f_safety
- POSITION lane/boat geometry
- OTHER_SAFE audited relative transforms.
No `meet_*`.
THIRD remained fixed v300 `.1`.

Development best: `DROP_START`.
- SECOND TOP2 **72.41%** vs 71.72% BASE
- outer 4/5/6 TOP2 **26.44%** vs 24.14%
- exact3 **136/345 = 39.42%** vs 132/345=38.26%
- boat4 TOP2 40.48%
- boat5 18.75%
- boat6 0%.
But worst-month SECOND TOP2 fell to 60.00%, so this is development-only and not promotion-ready.
Conclusion: boat5/6 remains unresolved; this motivates route/gating or pairwise SECOND rather than endless p3/p4 stacking.

# 8. v313 CACHE-FIRST infrastructure — MANDATORY going forward

The user explicitly requested that heavy causal reconstruction not be repeated every experiment.

Builder:
- `build_v313_1head_opponent_causal_cache.py`
Workflow:
- `.github/workflows/research-20260913-v313-opponent-causal-cache.yml`
Cache files intended:
- `cache_v313_1head_opponent_pre.csv.gz`
- `cache_v313_1head_opponent_p3.csv.gz`
- `cache_v313_1head_opponent_p4.csv.gz`
Manifest:
- `CACHE_V313_1HEAD_OPPONENT_CAUSAL.md`.

Mandatory cache rules:
1. Full PRE/prior reconstruction, causal p3 reconstruction, p4 loading, history/race-card fetches and settlement joins are performed once when cache is built/refreshed.
2. Subsequent SECOND/THIRD/pairwise/ordered-pair/ticket experiments load cache by default.
3. Research scripts MUST NOT silently fall back to full historical reconstruction when cache is missing. Fail fast, build/refresh cache once, then resume queued research.
4. Rebuild only if upstream causal feature/provenance changes, cohort explicitly changes, or cache audit fails.
5. Cached PRE removes `meet_*`. Outcome/settlement may exist only as labels/evaluation fields and never enter predictor lists.
6. Month M training remains strictly `<M` even with all months in cache.
7. Missing p3/p4 never future-backfilled; use availability + neutral sentinel.
8. Jul/Aug remain NON-PRISTINE and September remains outcome-blind regardless of cache contents.

At time this complete handoff is written, v313 cache generation had been launched and was the current infrastructure dependency. Fresh chat MUST inspect latest GitHub/workflow state rather than assume it is still running.

# 9. v312 current opponent branch

Script: `run_v312_1head_opponent_outer_gate.py`
Workflow: `.github/workflows/research-20260912-v312-outer-gate.yml`
Purpose: inner-vs-outer SECOND gating / outer specialist while fixed boat1 cohort remains 345R/290 head hits.

v312 was changed to HARD REQUIRE v313 cache and no longer perform full historical reconstruction itself. If cache is absent it should fail fast intentionally. Cache commit is intended to trigger/restart v312 automatically.

Decision after v312:
- if stable SECOND TOP2 and outer capture materially improve, build compact/gated successor around those signals;
- if gain <= about 0.5pp with essentially unchanged outer capture, or result is unstable/month-concentrated, move automatically to pairwise SECOND rather than over-tuning gating.

# 10. Automatic research roadmap

The user wants the automatic research CONTENT/STATE/QUEUE itself to survive chats, not just result summaries.

Self-continuing rule:
- A failed/flat experiment is diagnostic evidence, not a stopping condition.
- After each valid negative result, inspect failure decomposition and automatically choose the next materially different leak-safe hypothesis.
- Do not endlessly tune one weak formulation; switch model class/target decomposition when gains saturate.
- Keep frozen 345R/290-head-hit cohort during opponent comparisons unless user explicitly requests a separate cohort experiment.
- If research is found stopped and the next handoff step is clear, restart it automatically.
- Continue until user stops/redefines it, materially distinct leak-safe approaches are exhausted/documented, or a technical/data blocker prevents valid research.

Automatic branch sequence:
1. v311 feature-family attribution / compact listwise SECOND — completed.
2. v312 inner-vs-outer gating / outer specialist — current.
3. Pairwise SECOND ranking with outer-balanced weighting if v312 weak.
4. Multiclass/listwise alternatives with route/class balancing.
5. Error-driven PRE/prior feature engineering: ST, motor, player/form, lane geometry, prior foot/turn, causal p3/p4; never unsafe `meet_*`.
6. Once SECOND capture stabilizes, rebuild conditional THIRD separately.
7. If factorized SECOND×THIRD remains limiting, direct 20 ordered `(second,third)` pair model.
8. Only after ranking/probability models stabilize, optimize exactly-3-ticket policy.
9. Any suspicious large gain -> immediate leakage/causal audit branch.

Metrics every experiment must report:
- exact3 on full 345 denominator
- SECOND TOP1/TOP2/TOP3 on 290 head-win races
- conditional THIRD TOP1/TOP2/TOP3 when relevant
- by actual SECOND boat
- outer 4/5/6 capture
- monthly breakdown
- worst month
- delta vs clean BASE.

# 11. Promotion / production rules

Nothing from Feb-Jun dev alone is production promotion evidence.
Promotion requires:
- leak-safe causal implementation
- stable monthly behavior
- production-compatible threshold/calibration
- prospective/outcome-blind validation.

Current boat1 head research reference is FIXED v308 345R/290=84.06%, but its global q=.980 threshold must eventually be converted to production-compatible prior-only/absolute calibration before live promotion.

Opponent research remains development work; current clean benchmark is v309 BASE 132/345 exact3, v310 best 133/345, and v311 dev best 136/345 but unstable worst month.

# 12. ROI definition if/when evaluated

Broader project ROI convention:
- one race budget ¥10,000
- payout / settled stake ×100
- losing race payout=0 and profit=-¥10,000
- do not drop losing races from denominator.
Always inspect latest implementation before reporting ROI because project definition/code may have evolved.

# 13. Exact fresh-chat resume instruction

On a new chat, user can say:
`boatrace-backtest の CHAT_HANDOFF_20260913_1HEAD_COMPLETE.md と最新GitHubを読んで、1号艇モデルの続きから進めて。最新GitHubを優先して、自動研究を止めずに続けて。`

Fresh chat must then:
1. inspect this handoff and latest GitHub;
2. inspect latest v313 cache workflow/status and whether cache files/manifest exist;
3. if cache missing and no valid build active, fix/trigger v313 rather than reverting experiments to full reconstruction;
4. once cache exists, verify v312 runs from cache;
5. on v312 completion, record result into persistent handoff and automatically choose next branch by rules above;
6. preserve fixed boat1 cohort 345R and 290 head hits throughout opponent comparison;
7. update the persistent handoff after every meaningful result, failure, fix, design change, and next-step decision.

## Core one-line state
**Boat1 head is frozen at v308: 345 races, 290 hits, 84.06%. Current work is opponent selection only; SECOND outer boats 4/5/6 are the main bottleneck; v313 cache-first infrastructure must be used, then v312 gating -> pairwise if weak, with automatic leak-safe research continuing across chats.**
