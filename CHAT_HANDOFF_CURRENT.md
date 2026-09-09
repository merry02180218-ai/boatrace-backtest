# Chat handoff — canonical current state

Updated: 2026-09-10 JST
Repository: `merry02180218-ai/boatrace-backtest`
Default branch: `main`

## Mandatory next-chat startup
1. Read this file first.
2. Then inspect actual latest repo files/commits/results through GitHub before any prediction, judgment, backtest conclusion, audit, or model change.
3. Latest GitHub file/commit supersedes older chat/memory when they conflict.
4. Never calculate a LIVE prediction from memory alone. Run the actual current program with current inputs.
5. Freeze prediction/tickets before result/payout/post-deadline information.

## CRITICAL — contamination / validation status
- 2026-07 and 2026-08 have been repeatedly inspected and are NON-PRISTINE.
- Dec2025-Jun2026 has also been heavily used for feature/rule discovery and is selection-contaminated.
- User explicitly allowed Jul/Aug to be included in the current historical optimization, but results must be described as historical/in-sample/model-selection evidence, NOT pristine future validation.

## ROI / staking definition — mandatory
- Exactly 10,000 yen total stake per selected/settled race.
- Dutch allocation inverse to odds.
- 100-yen units with Hamilton/largest-remainder rounding; total exactly 10,000 yen.
- Zero-stake tickets are not purchased.
- Composite odds: `O_combined = 1 / sum(1/o_i)`; it is a value feature, NOT ROI.
- Realized ROI = total payout / (settled selected races * 10,000).
- Losing race payout=0 and profit=-10,000 yen.
- Canonical implementation: `analyze_v205_3head_operational_replay.py::round_dutch`.

# CURRENT OFFICIALLY ADOPTED 3-HEAD MODEL
User formally adopted this pipeline on 2026-09-10. This supersedes the older statement that v165/v166/v219+ had no production replacement.

Operational chain:
1. **Strict PRE candidate selection: v249 S+A**
   - Rolling / chronologically prior-month training logic.
   - Current-race exhibition-derived features excluded from PRE.
   - S and A are currently treated together as the PRE candidate set; do NOT use S as a stronger staking tier because historical S ROI was not better than A.
2. **After exhibition: canonical v243 final selection**
   - Canonical cached v243 artifact/run: run `34383567078`, artifact `10118044294`.
   - Exact canonical target reconstruction:
     - base = bet==1 & p3>=0.45 & raw_top_n 7..18 & comp_odds 3.05..4.0
     - keep base when `f__c_b3_minus_b5_st >= -0.1999999999999999`
     - rescue outside base when `f__c_attack3_stretch <= 0.5672342857142857`
   - Do NOT round the keep threshold to literal -0.2; that selects four extra historical races.
3. **Odds / ticket stage: v242 variable TopN**
   - Evaluate unconstrained TopN N=2..20 and choose N whose composite odds is closest to 3.00.
   - If raw N<5: NO BET.
   - If raw N>10: cap purchase at Top10.
   - If raw N=5..10: buy that N.
   - Exact 10,000-yen Dutch using canonical rounding.

Short canonical description:
**v249 PRE S+A -> v243 exhibition/final selection -> v242 variable 5-10 tickets -> 10,000 yen Dutch.**

## Adopted historical performance reference
For the rolling portion used in the v249 evaluation (Feb-Aug):
- PRE S+A + final purchase: 104 settled races
- hits: 39
- hit rate: 37.50%
- total stake: 1,040,000 yen
- total payout: 1,200,350 yen
- profit: +160,350 yen
- realized ROI: **115.42%**
Comparison without the v249 PRE gate in the same rolling period: 119 races, 44 hits, hit 36.97%, ROI 113.32%.
Dropped B group: 15 races, 5 hits, hit 33.33%, ROI 98.74%.
S alone historically: 40 races, ROI 101.41%; A alone: 64 races, ROI 124.18%. Therefore use S+A together for operational PRE screening.
Monthly adopted-pipeline ROI reference: Feb226.44%, Mar102.38%, Apr216.80%, May146.02%, Jun67.52%, Jul32.09%, Aug117.39%.
These are NOT pristine future-performance estimates; Jul/Aug especially remain non-pristine/overfit.

## v249 details
- script: `analyze_v249_3head_pre_rolling_sab_optimize.py`
- workflow: `.github/workflows/v249-3head-pre-rolling-sab-optimize.yml`
- workflow commit: `1bf72b764f14dc38b76c3218300de8c73b692ddf`
- successful run: `34396394990`
- artifact: `10121675319`, `v249-3head-pre-rolling-sab-optimize`
- rolling optimization result: S+A 388/480 candidates (80.83%), captured 104/119 canonical final targets = 87.39%.
- monthly S+A target capture: Feb100%, Mar75%, Apr90.91%, May85%, Jun86.67%, Jul95%, Aug86.67%.
- threshold search itself is retrospective model selection.

## v247 strict PRE rolling reference
Successful run `34395014723`, artifact `10121153797`.
At 80% candidate fraction, rolling capture was 103/119 = 86.55%; monthly Feb100, Mar75, Apr81.82, May85, Jun86.67, Jul95, Aug86.67. v249 is the operational S/A/B optimization built from this direction.

## v242 baseline historical reference
Dec-Aug v242 baseline: 522 bets, hit27.20%, ROI84.15%. Monthly ROI Dec90.71 Jan70.65 Feb111.39 Mar83.03 Apr127.54 May113.96 Jun71.32 Jul51.30 Aug83.56.

## Legacy 3-head context
v165/v166 and v219+ remain research/ancestry of the current line. v165 uses current exhibition/direct margins and boat3 must exhibit course3; v166 ranks ordered opponent pairs. They are no longer the top-level production description; use the adopted v249->v243->v242 chain above.

## 1-head
Canonical chain remains Legacy PRE -> v109 S-only -> v162 Top7 unless a newer repo commit explicitly supersedes it.

## 4-corner / 5-head
Models exist. Re-fetch exact latest repo rules before use; do not infer from old chat.

## LIVE rule
Before any live 3-head prediction, fetch current repo and actual race inputs. Apply the adopted chain from actual code/data. Historical odds settlement must never be described as true pre-deadline live odds unless a snapshot was actually captured before deadline.

## Open audits / next improvements
- v245 first-day/new-motor/venue audit remains a separate research audit and does not block adoption of the current 3-head chain.
- Venue-level performance should be reviewed when v245 finishes successfully.
- Future validation should use genuinely unseen/pristine data; do not retune adopted thresholds on each new loss/month without explicitly treating it as a new research branch.
