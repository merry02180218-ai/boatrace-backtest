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

## v310 concept / current status
Use causal head-risk probabilities from the existing 3-head and 4-head models as opponent-context features for SECOND ranking.
- p3: v243-family monthly walk-forward 3-head probability.
- p4: v250 PRE monthly walk-forward 4-head probability.
- THIRD stays frozen to v300 conditional THIRD L2=.1 for attribution.
- Test SECOND L2 = 1, 3, 10, 30 plus BASE.
- Add role interactions so p3/p4 pressure can affect boats 2-6, including outer boats.
- Run 1: 34691636653 failed because pre-Feb SECOND training rows had no p3/p4.
- Run 2: 34694162406 failed because some Feb-Jun rows had cross-pipeline p3/p4 coverage gaps.
- Fix 1 commit: 283a85661c7ac701e45b1ff2abcd9ff3e2e53620.
- Fix 2/current v310 commit: ebb82bcbb7e718e20b72ab053c3a489a9670f9d2.
- Missing p3/p4 policy: explicit availability flags + zero sentinel; no future backfill; denominator remains 345R.
- Current run 3: 34696379838 was in progress when v311 auto-research was launched.

## v311 auto-research — launched
Script: `run_v311_1head_opponent_second_family_autoresearch.py`
Workflow: `.github/workflows/research-20260912-v311-second-family-autoresearch.yml`
Script commit: a4a1cb84bf2f3982778f2fe878a8372a135e22c9
Workflow commit: 2eba72b0e1d68693e70c6e5b0b1dd5c3c7f7b71b

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

v311 outputs when successful:
- `analysis_v311_1head_opponent_second_family_autoresearch_configs.csv`
- `analysis_v311_1head_opponent_second_family_autoresearch_features.csv`
- `analysis_v311_1head_opponent_second_family_autoresearch_best_by_second.csv`
- `analysis_v311_1head_opponent_second_family_autoresearch_best_monthly.csv`
- `analysis_v311_1head_opponent_second_family_autoresearch_best_race.csv`
- `summary_v311_1head_opponent_second_family_autoresearch.md`

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
5. Report at minimum:
   - exact3 / full 345 denominator,
   - SECOND TOP1/TOP2/TOP3 on head-hit races,
   - conditional THIRD TOP1/TOP2/TOP3 when THIRD is under study,
   - by actual SECOND boat,
   - outer 4/5/6 capture,
   - monthly breakdown,
   - worst month,
   - change vs BASE.
6. Prefer broad, stable gains over one-month spikes.
7. If a gain comes from a suspicious feature, stop and perform a causal/leakage audit before continuing.
8. Save summary markdown + config CSV + race-level CSV to GitHub.
9. Update this handoff after every meaningful result, failure, fix, or design change.
10. Never discard failed experiments silently; record why they failed and whether the result is invalid.
11. Preserve the next auto-research step so a new chat can resume without redesigning the research plan.

## Automatic next-step policy
After v311:
- If one or more clean families improve SECOND TOP2 stably, build v312 as a compact SECOND model around those families and test outer-specialist/gating blends.
- If gains are concentrated only in one month or one boat, audit before continuing.
- If SECOND TOP2 cannot improve materially, move to alternative ranking formulations (pairwise or inner-vs-outer route gating) without changing the fixed cohort.
- Once SECOND is stable, rebuild conditional THIRD separately.
- After SECOND/THIRD stabilize, test a direct 20 ordered-pair model and then ticket policy.

## Research roadmap
A. SECOND rebuild from scratch
- clean families: lane prior, racer/form, ST/start, motor, prior player/form, causal p3/p4 head-risk.
- compare family-only and compact combinations.
- specifically optimize outer SECOND recovery without collapsing boat2/3 precision.

B. Alternative SECOND formulations
- listwise softmax/logistic.
- pairwise ranking.
- route/gating model: normal inner route vs outer-SECOND route.
- optional specialist for boats 4-6, blended causally with base ranker.

C. THIRD rebuild after SECOND stabilizes
- conditional THIRD model P(third | second).
- evaluate using actual SECOND diagnostically and predicted SECOND operationally.

D. Joint ordered-pair model
- direct ranking/classification over 20 ordered (second, third) pairs.
- compare top-3 pair coverage against separate SECOND×THIRD factorization.

E. Ticket policy
- only after probability/ranking models are stable.
- compare top-3 joint pairs vs TOP2xTOP2/diversity-aware policies.
- keep exactly 3 tickets for clean comparison initially.

## Promotion rule
Do not promote opponent changes merely because Feb-Jun development improves. Require leak-safe implementation, stable month-by-month behavior, production-compatible calibration, and prospective/outcome-blind validation before production adoption.
