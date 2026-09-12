# CHAT_HANDOFF_20260912_1HEAD_OPPONENT_AUTORESEARCH

## Scope
1号艇頭モデルを固定したうえで、相手選び（SECOND / THIRD / exact 3-ticket）をゼロベースで自動研究する。

## Fixed head model / evaluation cohort
- Current reference head operating point: v308 q=.980, opponent mass>=.375 cohort as currently frozen for opponent research.
- Frozen evaluation set: 345 races.
- Head hits: 290/345 = 84.06%.
- Do not silently change denominator during opponent-model comparisons.
- Boat-1 losses remain misses in final exact-trifecta metrics.
- July/August 2026 are NON-PRISTINE and must not be used as pristine validation.
- September outcomes remain unread / outcome-blind unless latest repo explicitly changes this rule.

## v309 audit findings
Current v300 opponent model on fixed 345R:
- exact 3-ticket: 132/345 = 38.26%.
- among 290 head-hit races, actual SECOND TOP2 inclusion = 71.72%.
- given actual SECOND, conditional THIRD TOP2 = 72.76%.
- major failure decomposition on head-hit races:
  - actual SECOND outside TOP2: 82R (28.28%).
  - SECOND candidate captured but THIRD outside TOP2: 51R (17.59%).
  - pair/ticket ordering loss despite candidate coverage: 25R (8.62%).
- SECOND TOP2 by actual second boat was highly biased inward:
  - boat2: 98.25%
  - boat3: 84.27%
  - boat4: 35.71%
  - boat5: 18.75%
  - boat6: 0%
Main bottleneck: SECOND ranking, especially boats 4-6.

## v310 result
Use causal head-risk probabilities from the existing 3-head and 4-head models as opponent-context features for SECOND ranking.
- p3: v243-family monthly walk-forward 3-head probability.
- p4: v250 PRE monthly walk-forward 4-head probability.
- THIRD stayed frozen to v300 conditional THIRD L2=.1 for attribution.
- Final successful run: 34696379838.
- Best: HEADRISK_L2_3.
- SECOND TOP2: 71.72% -> 72.07%.
- exact3: 132/345 = 38.26% -> 133/345 = 38.55%.
- actual SECOND boat4 TOP2: 35.71% -> 38.10%.
- boat5 remains 18.75%; boat6 remains 0%.
Conclusion: causal p3/p4 is a small useful auxiliary signal, not a solution to outer-SECOND failure.

## v311 auto-research — launched
Script: `run_v311_1head_opponent_second_family_autoresearch.py`
Workflow: `.github/workflows/research-20260912-v311-second-family-autoresearch.yml`
Script commit: a4a1cb84bf2f3982778f2fe878a8372a135e22c9
Workflow commit: 2eba72b0e1d68693e70c6e5b0b1dd5c3c7f7b71b
Run: 34696800597

Purpose:
- Keep exact frozen 345R / 290 head wins.
- Keep THIRD frozen at v300 conditional L2=.1.
- Attribute SECOND performance to leak-safe feature families.
- Compare BASE, FULL_HEADRISK, leave-one-family-out variants, and compact family combinations.

Feature families automatically audited/tested:
- HEADRISK: causal v310 p3/p4 + availability/role interactions.
- START: nst_strength-derived PRE/prior features.
- MOTOR: motor-derived PRE/prior features.
- PLAYER: symmetric `pl_*` prior-player fields.
- FORM_STATIC: grade/wr/local/f_safety.
- POSITION: candidate lane/role geometry.
- OTHER_SAFE: remaining audited within-race relative transforms from the existing PRE/prior opponent pipeline.

v311 development best ordering:
1. overall SECOND TOP2
2. worst-month SECOND TOP2
3. outer 4/5/6 SECOND TOP2
4. exact3
This selection is development-only and must not be promoted directly.

## Leakage / causal safety rules — mandatory
1. Never use same-race result, later-race result, end-of-day aggregates, post-race exhibition, payout/result fields, or any feature reconstructed with future information.
2. All historical/player/motor/foot features must be available strictly before prediction time. Prefer prior-day frozen state when exact intraday versioning is not proven.
3. Any feature whose source table is not time-versioned must be treated as unsafe until causal reconstruction proves availability.
4. `meet_*` features remain unsafe for this research unless separately reconstructed causally. Do not reintroduce contaminated v304/v306 signals.
5. Monthly walk-forward: for month M, train only on dates/months before M. Never fit on the evaluation month and never calibrate with its outcomes.
6. Missing p3/p4 coverage must not be backfilled from a future model. Use explicit availability flags and neutral sentinel values, while keeping the fixed race denominator unchanged.
7. Hyperparameter/config selection on Feb-Jun is development-only. Do not present it as pristine prospective validation.
8. Global future-distribution thresholds are not production-compatible calibration. Convert to prior-only/absolute thresholds before promotion.
9. Every experiment must assert frozen cohort size 345 and head-hit count 290 before scoring opponent models.
10. Keep SECOND, THIRD, and ticket-policy changes separable so attribution is possible.
11. Every new auto-research feature must be assigned a provenance family and leak status before use.
12. If a suspiciously large gain appears, pause model expansion and run a dedicated causal/leakage audit before accepting it.

## Auto-research operating procedure
For every new opponent experiment:
1. Inspect latest GitHub and this handoff first; latest code wins if conflict.
2. Freeze/assert the evaluation race IDs and head hits.
3. Record feature provenance and leakage status before fitting.
4. Run a clean BASE in the same script/run.
5. Report at minimum exact3/full345, SECOND TOP1/TOP2/TOP3, by-boat outer capture, monthly, worst month, and delta vs BASE.
6. Prefer broad stable gains over one-month spikes.
7. If a gain comes from a suspicious feature, stop that branch and perform a causal/leakage audit before accepting it.
8. Save summary markdown + config CSV + race-level CSV to GitHub.
9. Update this handoff after every meaningful result, failure, fix, or design change.
10. Never discard failed experiments silently; record why they failed and whether the result is invalid.
11. Preserve the next auto-research step so a new chat can resume without redesigning the research plan.

## Self-continuing research rule — mandatory
The auto-research must NOT stop merely because the current hypothesis or model family fails.
- A failed or flat experiment is diagnostic evidence, not a stopping condition.
- After each valid negative result, inspect the failure decomposition and choose the next materially different hypothesis automatically.
- Do not endlessly tune one weak formulation. If incremental tuning saturates, switch model class or target decomposition.
- Keep the 345R/290-head-hit cohort fixed while opponent research is being compared, unless a separate explicitly-labelled experiment studies cohort definition.
- Keep leak rules unchanged when switching model classes.
- Continue until one of these explicit stop conditions is reached: (a) a user stops/redefines the research; (b) all planned materially distinct leak-safe approaches have been exhausted and the handoff records the evidence; or (c) a technical/data blocker prevents a valid experiment and the blocker is documented.

## Automatic branch sequence after each result
1. Feature-family attribution / compact listwise SECOND (v311 line).
2. Inner-vs-outer route gating with a dedicated outer SECOND specialist for boats 4/5/6.
3. Pairwise SECOND ranking, including outer-balanced weighting where causally valid.
4. Multiclass/listwise alternatives with class/route balancing that do not alter evaluation denominator.
5. Error-driven feature engineering from PRE/prior-only ST, motor, player/form, lane geometry, prior foot/turn, and causal p3/p4; no unsafe `meet_*`.
6. Once SECOND capture stabilizes, rebuild conditional THIRD separately.
7. If factorized SECOND×THIRD remains the bottleneck, fit a direct model over 20 ordered (second, third) pairs.
8. Only after ranking/probability models stabilize, optimize the exactly-3-ticket policy.
9. For any suspicious large gain, branch immediately into a leakage/causal audit before further optimization.

## Decision rules for moving branches
- If SECOND TOP2 improves only <= ~0.5pp and outer boats remain essentially unchanged, treat it as weak and move on rather than over-tune.
- If improvement is concentrated in one month/boat, audit stability and do not accept it as general improvement.
- If outer capture improves but inner 2/3 collapses enough to reduce overall TOP2/exact3 materially, try gated blending rather than replacing the base ranker wholesale.
- If SECOND TOP2 stops being the dominant error, move research effort to THIRD or ordered-pair coverage according to the latest failure decomposition.
- Promotion still requires production-compatible calibration and prospective/outcome-blind validation; Feb-Jun search remains development-only.

## Research roadmap
A. SECOND rebuild from scratch / family attribution.
B. Route/gating and outer-specialist SECOND.
C. Pairwise/multiclass alternative SECOND formulations.
D. Conditional THIRD rebuild.
E. Direct 20 ordered-pair model.
F. Three-ticket policy research.
G. Prospective production-compatible validation.

## Promotion rule
Do not promote opponent changes merely because Feb-Jun development improves. Require leak-safe implementation, stable month-by-month behavior, production-compatible calibration, and prospective/outcome-blind validation before production adoption.
