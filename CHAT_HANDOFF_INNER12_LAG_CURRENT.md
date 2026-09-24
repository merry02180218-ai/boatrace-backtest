# CHAT_HANDOFF_INNER12_LAG_CURRENT

Updated: 2026-09-24

## Purpose
New independent research model requested by user.

Target mechanism:
- boat 1 and boat 2 both have causal pre-race reasons to start late;
- downstream outcome of interest is either:
  1. boat 3 wins by まくり, or
  2. boat 4 wins by まくり差し.

User constraint:
- do NOT make boat3/boat4 raw strength the main driver.
- model should be driven primarily by the simultaneous weakness/start-lag structure of boats 1 and 2.

## Model ID
`INNER12_LAG_3M_4MS_V1`

Research script:
`research/research_inner12_lag_3m4ms_v1.py`

Manual-only workflow:
`.github/workflows/research-inner12-lag-3m4ms-v1.yml`

Production is unchanged.

## V1 architecture

### PRE
For boats 1 and 2 independently, build a start-lag score from:
- Waku10 frame average ST;
- national average ST;
- current-meeting ST;
- Waku10 frame average start order;
- causal prior actual-ST mean;
- causal prior late-start rate (>0.20).

The core pair score is:
`dual_late_pre = min(late1_pre, late2_pre)`

Using min rather than mean is intentional: both boat1 and boat2 must carry lag evidence.

No boat3/boat4 player power or motor power is used in this primary score.

### POST
Current exhibition ST is converted to a predicted actual ST using each player's strictly prior exhibition->actual ST bias.
Then:
- `late1_post = .55 * late1_pre + .45 * current_predicted_slow1`
- `late2_post = .55 * late2_pre + .45 * current_predicted_slow2`
- `dual_late_post = min(late1_post, late2_post)`

Boat3/boat4 current predicted ST is recorded only as structural context, not the primary score.

## Exact target labels
- `target3_makuri = winner == 3 AND kimarite == まくり`
- `target4_makurisashi = winner == 4 AND kimarite == まくり差し`
- `target_any = target3_makuri OR target4_makurisashi`

3号艇のまくり差し is NOT included in v1 target.
4号艇のまくり is NOT included in v1 target.

## Leakage / evaluation contract
- history starts 2025-10-01 only to warm causal prior state;
- research rows start 2026-03-01;
- development/tuning: 2026-04-01 through 2026-06-30;
- fixed holdout: 2026-07-01 through 2026-08-31;
- September outcomes are not read;
- all target-day features are frozen before target-day results are opened;
- prior actual-ST and exhibition-bias histories are updated only after that date's feature freeze;
- production models are not modified.

V1 sweeps PRE and POST dual-late thresholds from .45 to .90.
Any candidate cutoff is selected using development months only, with minimum sample/target-count guards.
July-August is report-only holdout.

## Outputs
Artifact directory:
`/tmp/inner12_lag_3m4ms_v1/`

Expected:
- `race_features.csv`
- `threshold_grid.csv`
- `monthly_selected.csv`
- `meta.json`
- `run.log`

## Next action
Manually fire workflow `research-inner12-lag-3m4ms-v1`.
After SUCCESS:
1. inspect PRE vs POST combined-target lift;
2. inspect July and August separately;
3. inspect whether 3まくり and 4まくり差し respond to the same dual-lag cutoff;
4. if combined mechanism is real, build V2 as two-stage:
   - stage A: INNER12_LAG occurrence probability;
   - stage B: route split 3_MAKURI vs 4_MAKURI_SASHI;
5. keep boat3/4 strength features low-weight/minimum-viability only unless data proves they are necessary;
6. only after head/development signal is stable, add opponent/ticket and odds/ROI work.

## Commits
- script: `762d9ee1355bb9b30107d0f76701ea43ca2a3559`
- manual workflow: `7724ad1e6a569ab913b4ac36c4a45256c53898fd`


## V1 result — Run 35963686632 SUCCESS
Run:
- https://github.com/merry02180218-ai/boatrace-backtest/actions/runs/35963686632
- commit: `f0517b84cbe93d30cd83bdd4567a4740ab13071f`
- status: SUCCESS
- rows: 28,011
- September outcomes read: false
- same-day results used for features: false
- production changed: false

### Baseline rates
Development Apr-Jun:
- PRE population: 13,564R / target 1,013 = 7.4683%
- POST-available population: 12,377R / target 927 = 7.4897%

Holdout Jul-Aug:
- PRE population: 9,840R / target 762 = 7.7439%
- POST-available population: 9,588R / target 743 = 7.7493%

### Chosen PRE rule (selected on Apr-Jun only)
`dual_late_pre >= .55`
- Apr-Jun: 154R / target 25 = 16.2338% (lift 2.174x)
  - 3 makuri: 17/154 = 11.0390%
  - 4 makuri-sashi: 8/154 = 5.1948%
- Jul-Aug holdout: 99R / target 10 = 10.1010% (lift 1.304x)
  - 3 makuri: 7/99 = 7.0707%
  - 4 makuri-sashi: 3/99 = 3.0303%
- holdout volume: about 49.5 races/month.

Monthly:
- Jul: 50R / 5 target = 10.00%; all 5 were 3-makuri.
- Aug: 49R / 5 target = 10.20%; 3-makuri 2, 4-makuri-sashi 3.

### Chosen POST rule (selected on Apr-Jun only)
`dual_late_post >= .70`
- Apr-Jun: 124R / target 23 = 18.5484% (lift 2.477x)
  - 3 makuri: 16/124 = 12.9032%
  - 4 makuri-sashi: 7/124 = 5.6452%
- Jul-Aug holdout: 105R / target 13 = 12.3810% (lift 1.598x)
  - 3 makuri: 10/105 = 9.5238%
  - 4 makuri-sashi: 3/105 = 2.8571%
- holdout volume: about 52.5 races/month.

Monthly:
- Jul: 61R / 8 target = 13.11%; 3-makuri 6, 4-makuri-sashi 2.
- Aug: 44R / 5 target = 11.36%; 3-makuri 4, 4-makuri-sashi 1.

### Interpretation
- The core hypothesis is supported out-of-sample: simultaneous boat1+boat2 start-lag risk raises the combined target rate.
- POST is clearly stronger than PRE on Jul-Aug: 12.38% vs 10.10%, with similar volume.
- Most robust signal is boat3 makuri:
  - POST holdout 9.52% vs background POST 3-makuri rate 5.16%, about 1.84x.
- Boat4 makuri-sashi signal is much weaker on holdout:
  - POST holdout 2.86% vs background 2.59%, only a small lift.
- Therefore V2 should not treat 3-makuri and 4-makuri-sashi as one homogeneous endpoint.

## V2 recommended design
Two-stage structure:
1. Stage A = INNER12_LAG gate, keep POST `dual_late_post >= .70` as current research anchor.
2. Stage B = route classifier:
   - route 3_MAKURI
   - route 4_MAKURI_SASHI

For route split, keep 3/4 raw strength low-weight. Prefer structural variables first:
- predicted ST ordering of boats 3 and 4 relative to 1/2;
- 3-vs-4 predicted ST gap;
- boat3 ability to cross boat2 / boat4 ability to take the opened lane;
- boat3 turn/straight balance and boat4 turn entry only as minimum-viability/soft features;
- 2 wall-collapse tendency and 3's likely trajectory;
- current exhibition course changes;
- PLAYERHistory/Waku10 only where they describe start/development role rather than generic strength.

Do not production-adopt V1 yet. It is a validated mechanism gate, not yet a complete betting model.


## User precision requirement — 2026-09-24
User rejected ~20% class precision as insufficient and set a practical target of **at least 40%** for the combined endpoint (3-makuri OR 4-makuri-sashi). Lower race volume is acceptable if necessary.

### V2 created for high precision
Files:
- `research/research_inner12_lag_high_precision_v2.py`
- `.github/workflows/research-inner12-lag-high-precision-v2.yml`

Research split:
- Apr-May 2026: search/train
- Jun 2026: validation used for candidate selection
- Jul-Aug 2026: final holdout only
- September outcomes remain unread
- same-day results never used in features
- production unchanged

V2 mechanism remains start/development based; generic 3/4 class/motor strength is not used.
New structural requirements/search axes:
- both inner boats' `dual_late_post`
- minimum predicted actual ST of boats 1 and 2
- boat3 start margin over boat2 (`pred2 - pred3`)
- boat3 start margin over boat1 (`pred1 - pred3`)
- boat4 follow distance behind boat3 (`pred4 - pred3`)
- independent start-lag evidence count for both boats 1 and 2
- standard 1-2-3-4 exhibition course order as optional strict gate

Two tracks:
- STABLE: train >=24R and June validation >=10R
- AGGRESSIVE: train >=12R and June validation >=6R
Selection first looks for >=40% in both train and validation. Jul-Aug never participates in selection.

Next action:
- manually dispatch `research-inner12-lag-high-precision-v2`
- inspect success/failure
- if success, verify chosen stable/aggressive rules and Jul-Aug holdout precision/monthly stability
- do not production-adopt unless the 40% target is supported out-of-sample.


## Simultaneous-lag factor discovery — 2026-09-24
User requested a broader search for unexpected reasons why boats 1 and 2 may BOTH be late at the start.

Created:
- `research/research_inner12_factor_discovery_v1.py`
- `.github/workflows/research-inner12-factor-discovery-v1.yml`

### Goal
Do not start from the 3/4 head outcome. First explain/predict the inner-pair start collapse itself.

### Labels
- `dual_abs20`: actual ST1 >= .20 AND actual ST2 >= .20
- `dual_vs3_03`: both ST1 and ST2 are >= .03 slower than actual ST3
- `inner_vs_outer03`: faster of 1/2 is still >= .03 slower than faster of 3/4

The final route endpoint (3 makuri OR 4 makuri-sashi) is recorded only as a secondary diagnostic and is NOT used to select lag factors.

### Split / leakage contract
- history bootstrap: 2025-10-01
- Mar 2026: warm-up/research rows
- Apr-May: train/search
- Jun: validation used for factor screening
- Jul-Aug: final holdout only
- September outcomes unread
- same-day result rows are loaded only after all target-day features are frozen
- production unchanged

### Broad feature families
Known ST family:
- national / Waku10 / meeting ST
- prior actual-ST mean
- recent3 / recent6 / recent12
- prior ST volatility
- late-start rates
- last-start / recent drift
- current exhibition ST and player-corrected predicted actual ST

Unexpected/non-ST family:
- motor 2/3ren and prior motor-history strength
- prior original exhibition / turn / straight / standard display / foot type
- current display time/rank
- current original exhibition lap/turn/straight
- tilt
- wind speed / relative wind / wave / air/water temp / weather from cutoff snapshot where available
- venue
- race band
- meeting day
- 1/2 grade combination
- selected raw pre-race race-card fields: F/L, accidents, age/weight, win/ren rates, meeting ST/finish and similar numeric context

### Outputs
- `factor_rows.csv`
- `numeric_factor_ranking.csv`
- `nonst_surprise_ranking.csv`
- `categorical_factor_ranking.csv`
- `interaction_ranking.csv`
- `label_monthly.csv`
- `meta.json`
- `run.log`

Numeric thresholds/directions are learned from Apr-May. June and Jul-Aug reuse those frozen thresholds. Pair interactions are chosen from train+June only; Jul-Aug never chooses a feature/rule.

Next action:
- dispatch `research-inner12-factor-discovery-v1`
- inspect especially NON_ST surprises that have lift >1 in train, June, and Jul-Aug
- prioritize factors that reproduce across more than one simultaneous-lag label
- only after the lag mechanism is understood, feed the robust factors into the >=40% route model.


## Factor discovery V1 result — Run 35967044073 SUCCESS
Run:
- https://github.com/merry02180218-ai/boatrace-backtest/actions/runs/35967044073
- 27,251 labeled races
- September outcomes unread
- same-day feature freeze preserved
- production unchanged

### Baseline simultaneous-lag rates
- dual_abs20:
  - train 13.20%
  - June validation 13.81%
  - Jul-Aug holdout 13.59%
- dual_vs3_03:
  - train 16.84%
  - validation 16.97%
  - holdout 16.41%
- inner_vs_outer03:
  - train 29.52%
  - validation 30.53%
  - holdout 30.18%

### Stable non-ST finding: weak inner pair
The strongest broadly reproducible non-ST factor was low 1/2 performance level.
Examples:
- pair minimum national win rate <=4.19, dual_abs20:
  - train 18.53%, validation 18.94%, holdout 18.86%
- pair mean national win rate <=4.90, dual_abs20:
  - train 18.00%, validation 18.48%, holdout 19.64%
- pair mean national win rate <=4.90, inner_vs_outer03:
  - train 34.54%, validation 36.03%, holdout 34.84%
- low 2-boat national win/2ren/3ren metrics reproduced across all three lag labels.

Interpretation: racer quality is related not only to race result, but to simultaneous start-collapse risk. This is a real candidate feature family, not merely a head-strength feature.

### Unexpected environmental finding
Strong wind had a large effect on absolute simultaneous lateness:
- relative headwind 5m+ (dual_abs20):
  - train 22.17% (1.68x)
  - validation 31.34% (2.27x)
  - holdout 20.41% (1.50x)
- left-crosswind 5m+:
  - train 23.13%
  - validation 21.43%
  - holdout 19.36%
- all 5m+:
  - train 19.27%
  - validation 19.92%
  - holdout 14.93%

Important distinction:
- wind is much stronger for absolute late ST (both >=.20) than for relative lag versus boats3/4.
- therefore wind may slow the whole start field rather than uniquely opening the 3/4 attack route. It should be a lag-context feature, not assumed to directly predict the route.

### Venue effects reproduced
- Kiryu, dual_abs20:
  - train 19.95%, validation 19.81%, holdout 19.46%
- Gamagori, dual_abs20:
  - 20.81%, 20.56%, 15.89%
- Amagasaki is especially strong on relative lag:
  - dual_vs3_03: 23.45%, 25.86%, 24.39%
  - inner_vs_outer03: 36.55%, 39.92%, 40.13%
- Suminoe is especially strong on inner_vs_outer03:
  - 38.11%, 45.07%, 38.90%

### Grade-pair effects
Weak inner grade combinations are reproducible:
- B1-B1 dual_abs20: 17.92%, 17.27%, 18.48%
- B1-B2 dual_abs20: 18.42%, 22.73%, 20.61%
- B2-B1 dual_abs20: 22.13%, 19.12%, 17.36%
B1/B2-heavy inner pairs also raise relative-lag labels.

### Other weaker but reproducible non-ST candidates
- poor prior standard exhibition / poor prior original exhibition
- weak turnfoot / prior turn
- poor motor2/motor3 in some relative-lag definitions
- poor meeting finishes
- boat1 age >=47 had a small stable dual_abs20 lift
These are weaker than national-strength / venue / strong-wind effects but worth interaction tests.

### Existing ST interaction remains very strong
For inner_vs_outer03:
- pair min Waku start rank >=3.1 AND boat2 prior ST mean >=0.17675:
  - train 43.99%
  - validation 46.84%
  - holdout 41.85%
This is already a >40% Stage-A relative-lag detector.

### Exploratory category+numeric combinations worth strict V2 validation
These were inspected after V1 and must NOT yet be treated as frozen/adopted rules because they need a clean train/validation-only selection workflow:
- Suminoe + pair max local win rate <=5.33:
  - inner_vs_outer03 Apr 51.9%, May 46.2%, Jun 53.1%, Jul 43.1%, Aug 48.1%
- Amagasaki + pair mean national win rate <=4.9:
  - Apr 38.2%, May 51.4%, Jun 53.1%, Jul 50.0%, Aug 52.9%
- Suminoe + pair minimum motor2 <=20:
  - Apr 48.1%, May 28.9%, Jun 58.8%, Jul 61.3%, Aug 57.1%
- strong wind 5m+ + Kiryu, dual_abs20:
  - Apr 23.6%, May 36.4%, Jun 37.5%, Jul 30.8%, Aug 26.9%

Key conclusion:
- There ARE unexpected start-collapse factors beyond ST averages.
- The most promising relative-lag structure is venue + weak inner pair, with motor as a possible secondary interaction.
- Strong wind is real for absolute lateness but should not be mistaken for direct route opening.
- Stage A can already exceed 40% out-of-sample in several definitions; the remaining problem is Stage B: among those collapse races, discriminate 3-makuri vs 4-makuri-sashi so final route precision can approach the user's >=40% goal.


## Stage-A precision continuation — 2026-09-24

After Factor Discovery V1, two fixed Stage-A candidates were prepared for independent causal replay.

### A. SUMINOE_ULTRA
Rule:
- venue = Suminoe
- min(b1_prior_late18_rate, b2_prior_late18_rate) >= 0.435
- prior_late18 = prior-only smoothed rate of actual ST >= .18, with 4 pseudo-races at 35%

Exploratory replay from factor_rows showed:
- Mar: 28R / 60.7%
- Apr: 19R / 68.4%
- May: 16R / 50.0%
- Jun: 31R / 67.7%
- Jul: 20R / 60.0%
- Aug: 9R / 55.6%
Primary label is inner_vs_outer03.

Independent validator:
- `research/validate_inner12_stagea_suminoe_v1.py`

### B. GLOBAL_STAGEA
A non-venue-specific rule was found using only start-history/Waku structure:
- pair_mean_waku_sr >= 3.7
- pair_mean_prior_st_mean >= 0.17811274129319477
- pair_min_prior_late18_rate >= 0.43497650793650783

Exploratory replay:
- Apr-May train combined: 432R / 51.39%
- Jun validation: 201R / 50.25%
- Jul-Aug confirmation: 411R / 50.36%
- monthly:
  - Mar 264R / 44.7%
  - Apr 200R / 45.0%
  - May 232R / 56.9%
  - Jun 201R / 50.25%
  - Jul 231R / 53.25%
  - Aug 180R / 46.67%

This is much higher-volume than Suminoe Ultra and remains around 50% over Jul-Aug combined.

Independent validator:
- `research/validate_inner12_stagea_global_v1.py`

Combined manual workflow:
- `.github/workflows/validate-inner12-stagea-v1.yml`
- runs both fixed validators
- manual-only
- preflight checks both thresholds and September block
- artifacts: both Stage-A validation directories

Important methodology note:
- Jul-Aug has already been observed during exploratory factor discovery. It is now confirmation/replay, not a pristine untouched holdout.
- September outcomes remain unread and should be preserved for later prospective/fresh validation unless the user explicitly changes that policy.
- Stage-A target is the start-collapse mechanism, NOT final 3-makuri/4-makuri-sashi route precision.
- Next after validator SUCCESS: inspect final Stage-A parity and then build Stage-B route discriminator inside Stage-A candidates.


## Frozen Stage-A validation result — Run 35971699925 SUCCESS
Run:
- https://github.com/merry02180218-ai/boatrace-backtest/actions/runs/35971699925
- head SHA: 44b356bab4379bc364f76e32909f8617c8dc867a
- both validators SUCCESS
- September outcomes unread
- same-day result leakage: false
- production unchanged

### SUMINOE_ULTRA authoritative replay
Rule:
- venue Suminoe
- min(b1_prior_late18_rate,b2_prior_late18_rate) >= 0.435

Overall Mar-Aug:
- 123R / inner_vs_outer03 76 = **61.79%**
- dual_abs20 37/123 = 30.08%
- dual_vs3_03 38/123 = 30.89%
- final route endpoint (3 makuri OR 4 makuri-sashi) 19/123 = 15.45%

Monthly inner_vs_outer03:
- Mar 17/28 = 60.71%
- Apr 13/19 = 68.42%
- May 8/16 = 50.00%
- Jun 21/31 = 67.74%
- Jul 12/20 = 60.00%
- Aug 5/9 = 55.56%

Jul-Aug route endpoint:
- Jul 7/20 = 35.0%
- Aug 2/9 = 22.22%
- combined 9/29 = **31.03%**
  - 3-makuri 6/29 = 20.69%
  - 4-makuri-sashi 3/29 = 10.34%

### GLOBAL_STAGEA authoritative replay
Rule:
- pair_mean_waku_sr >= 3.7
- pair_mean_prior_st_mean >= 0.17811274129319477
- pair_min_prior_late18_rate >= 0.43497650793650783

Apr-Jun:
- 622R / inner_vs_outer03 317 = **50.96%**
- final route endpoint 102/622 = **16.40%**
  - 3-makuri 63 = 10.13%
  - 4-makuri-sashi 39 = 6.27%

Jul-Aug confirmation:
- 409R / inner_vs_outer03 205 = **50.12%**
- final route endpoint 51/409 = **12.47%**
  - 3-makuri 36 = 8.80%
  - 4-makuri-sashi 15 = 3.67%

Monthly inner_vs_outer03:
- Mar 45.56%
- Apr 45.23%
- May 56.58%
- Jun 50.26%
- Jul 52.84%
- Aug 46.67%

### Interpretation
- Stage A is now validated as a real start-collapse detector:
  - GLOBAL ~50%
  - SUMINOE ~62%
- Stage A alone is NOT the final route model.
- The final route rate remains 12.47% on Jul-Aug for GLOBAL and 31.03% for Jul-Aug SUMINOE.
- Therefore the next problem is specifically Stage B:
  **given that inner12 collapse risk is high, identify when 3 can convert it into makuri or 4 can convert it into makuri-sashi.**
- Do not add more generic 1/2-lag filters blindly; the bottleneck has shifted from detecting collapse to predicting conversion/route.


## Stage-B route discovery V1 — prepared 2026-09-24

User asked to continue after adding 4-corner makuri and other attack patterns.

Created:
- `research/research_inner12_stageb_route_discovery_v1.py`
- `.github/workflows/research-inner12-stageb-route-v1.yml`

Workflow is manual-only.

### Frozen Stage-A input
Only GLOBAL_STAGEA_V1 candidates enter Stage B:
- pair_mean_waku_sr >= 3.7
- pair_mean_prior_st_mean >= 0.17811274129319477
- pair_min_prior_late18_rate >= 0.43497650793650783

Suminoe Ultra membership is recorded as a diagnostic flag.

### Stage-B primary route labels
Individual:
- 1 escape
- 3 makuri
- 3 makuri-sashi
- 4 makuri
- 4 makuri-sashi
- 5 makuri
- 5 makuri-sashi

Grouped:
- 3 family = 3M + 3MS
- 4 family = 4M + 4MS
- 5 family = 5M + 5MS
- outer CORE = 3M + 3MS + 4M + 4MS + 5MS
- outer WIDE = CORE + 5M

Exploratory baseline from previously generated factor_rows inside GLOBAL Stage-A:
- Apr-May:
  - outer CORE ~35.88%
  - outer WIDE ~37.96%
- June:
  - CORE ~30.35%
  - WIDE ~31.84%
- Jul-Aug:
  - CORE ~28.71%
  - WIDE ~30.41%

Thus the grouped outer-attack target starts close enough to 40% that a reproducible Stage-B conversion filter may be feasible.

### Added Stage-B feature families
For boats 3/4/5:
- national / local strength
- motor2 / motor3
- Waku10 ST / win / start rank
- meeting ST
- prior actual-ST mean / recent ST / volatility / late rates
- prior motor / exhibition / turn / straight / display / foot
- current exhibition ST and player-corrected predicted actual ST
- current display time/rank
- current tilt
- current original exhibition lap/turn/straight/avg
- raw bounded pre-race fields

Relative attack geometry:
- boat3 minus boat4 feature gaps
- boat4 minus boat5 gaps
- boat3 minus boat5 gaps
- predicted-ST gaps 3 vs 4, 4 vs 5, 3 vs 5
- inner-fast vs attack-fast predicted ST

Environment / venue categories remain available.

### Leakage corrections made before dispatch
Important preflight finding:
1. initial generated source had a literal escaped `\n` in meta JSON source.
2. more importantly, lag outcome columns were not initially inside META_KEYS and could have entered numeric feature discovery.

Both were fixed BEFORE workflow dispatch:
- outcome columns excluded:
  - actual_st*
  - dual_abs20
  - dual_vs3_03
  - inner_vs_outer03
  - route_target
  - all route labels
- holdout is not used for threshold direction, category choice, interaction candidate choice, or ranking tie-breaks.
- Jul-Aug remains report-only.
- September outcomes unread.
- production unchanged.

Workflow preflight explicitly checks these leakage guards plus py_compile.

Next action:
- manually dispatch `research-inner12-stageb-route-v1`
- on SUCCESS inspect:
  - route baselines
  - individual route differentiators
  - outer CORE/WIDE rules with >=40% train+June if any
  - Jul-Aug report-only reproduction
  - which 3/4/5 features actually matter
- do not adopt a final route rule until the conversion structure is understood.


## Stage-B Run 35990165189 false-success incident
GitHub displayed SUCCESS because the research command was piped to `tee` without `set -o pipefail`.
Actual script status: FAILED.

Actual traceback:
- `KeyError: 5`
- at `post_inner_fast_vs_attack_fast_pred=min(pred[1],pred[2])-min(pred[3],pred[4],pred[5])`
- the exhibition prediction loop still iterated `for b in (1,2,3,4)`, so `pred[5]` did not exist.

Fixes:
- source commit `59628b24c240b2d7b2fd2a55c842b328594a5bad`
  - prediction loop now includes boats 1..5.
- workflow commit `d8c7a4ecc532468f1bf1e271aeb7c2a9efded99e`
  - adds `set -o pipefail`
  - preflight now asserts the exact boat5 prediction loop exists.
- therefore future Python failure can no longer be hidden by `tee`.

Do NOT rerun Run 35990165189 because it is pinned to the old head SHA.
Start a fresh manual workflow_dispatch of `research-inner12-stageb-route-v1.yml`.


## Stage-B route discovery V1 result — Run 35992940551 SUCCESS
Run:
- https://github.com/merry02180218-ai/boatrace-backtest/actions/runs/35992940551
- run_number 4
- SUCCESS
- head SHA a9adef7670e3d698afd41990890b6f16633c4a5e
- Preflight SUCCESS
- Stage-B body SUCCESS
- marker: INNER12_STAGEB_ROUTE_DISCOVERY_V1_OK
- rows: 1290
- September unread
- production unchanged
- artifact: 10805697327 / inner12-stageb-route-v1 / 2,653,260 bytes
- digest sha256:1d84106496ee1b35d0eaeb0691216dc8702ed0bd907587cbb46466d20051b3f6

### Baseline route rates inside frozen GLOBAL_STAGEA
Train Apr-May / Validation Jun / Jul-Aug confirmation:
- 1 escape: 37.24% / 41.54% / 38.39%
- 3 makuri: 11.48% / 7.18% / 8.80%
- 3 makuri-sashi: 5.62% / 5.13% / 7.09%
- 4 makuri: 6.56% / 6.67% / 6.60%
- 4 makuri-sashi: 7.49% / 3.59% / 3.67%
- 5 makuri: 2.11% / 1.54% / 1.71%
- 5 makuri-sashi: 4.45% / 7.69% / 2.69%
- 3 family: 17.10% / 12.31% / 15.89%
- 4 family: 14.05% / 10.26% / 10.27%
- 5 family: 6.56% / 9.23% / 4.40%
- outer CORE: 35.60% / 30.26% / 28.85%
- outer WIDE: 37.70% / 31.79% / 30.56%

### Important route findings

#### 3-family
Strong train+June interactions did NOT hold at 40% in Jul-Aug.
Examples:
- b3 vs b4 prior ST mean gap <= -0.0194 and b3 last ST <= .12:
  - train 40.54%
  - Jun 32.00%
  - Jul-Aug 21.21%
- b3 last ST <= .12 and b3 WR >= 5.91:
  - 37.14% / 26.92% / 22.45%
- b3 WR advantage over b4 >=1.23 and b3 last ST <=.12:
  - 36.84% / 34.78% / 26.67%

Conclusion: 3 route conversion is real but not yet precise enough.

#### 4-family — strongest stable structural signal
Most interesting rule:
- attack_gap_3minus4_wr <= -1.18
  => boat4 national WR is >=1.18 higher than boat3
- AND attack_gap_3minus4_prior_recent12_st >= 0.02583
  => boat3 recent12 ST is at least ~0.026 slower than boat4

Results:
- train: 13/40 = 32.50%
- Jun: 6/16 = 37.50%
- Jul-Aug: 12/37 = 32.43%
This is a very strong lift over 4-family baseline ~10–14% and reproduces in Jul-Aug.

Another stable 4-family rule:
- b4 clearly stronger than b3 (WR gap)
- b4 prior late18 rate <=0.3495
Results:
- 31.11% / 27.27% / 20.00%

Conclusion:
- 4 route has a clean mechanistic discriminator:
  **4 stronger than 3 + 4 starts more reliably/faster than 3**.
- This should be split next into 4-makuri vs 4-makuri-sashi.

#### 5-family
Best reproducible signal:
- b5 local WR >=5.62
- b5 current-meeting/first-race finish <=2
Results:
- train 20.45%
- Jun 31.25%
- Jul-Aug 14.29%
Still too low for final head-route precision, but 5 route lift is genuine.

### Outer attack grouped target
Best CORE interaction:
- b3 Waku WR >=6.1
- b3 prior mean ST <=0.1549
Results:
- train 59.62%
- Jun 55.00%
- Jul-Aug 33.87%

Best WIDE interaction:
same structural b3 combination:
- train 59.62%
- Jun 60.00%
- Jul-Aug 33.87%

Other WIDE:
- b3 late18 rate <=0.339 + b3 Waku WR >=6.1:
  - 55.32% / 54.55% / 35.00%
- weak b1 national+local:
  - 51.79% / 58.33% / 34.15%

Therefore:
- >=40% can be achieved in Apr-Jun but not yet robustly in Jul-Aug.
- The broad outer-attack target has substantial season/regime degradation in Jul-Aug.
- Do NOT adopt the 50–60% Apr-Jun rules as final.
- The strongest next research direction is the 4-family route because its relative-strength + relative-ST structure reproduces across all periods.

### Recommended next step
Build Stage-B V2 with explicit branch order:
1. 1-escape survivor classifier
2. 4-family classifier:
   - b4 vs b3 strength gap
   - b4 vs b3 recent ST reliability
   - exhibition ST / corrected predicted ST
   - 4 original exhibition stretch/turn balance
   - venue / wind interactions
   - then split 4-makuri vs 4-makuri-sashi
3. 3-family classifier
4. 5-follow-through classifier
Use walk-forward/month-specific stability checks and preserve September unread.


## Novel non-overlap pivot — 2026-09-24
User correctly noted that the strongest Stage-B 4-family finding was conceptually too similar to the existing production 4HEAD model.

Research objective changed:
- Do NOT build another generic "4 is stronger/faster" model.
- Explicitly exclude races where the existing 4HEAD production model fires.
- Research only incremental routes:
  - 3 direct attack -> 3 head
  - 3 attack -> 4 picks up the opening
  - 3/4 attack -> 5 follows/picks up the opening
  - 1-survival rejection
- A 4-head outcome may remain only if the exact production 4HEAD model did not fire.

Exact existing 4HEAD production reference:
- source: `audit_4head_ph5_live_walkforward.py`
- exact frozen decision: `selected=bool(hp>=.36 and orig>=-.06)`
- policy: PH5 head_prob >= .36 AND orig4_adv_inside >= -.06

Created:
- `research/research_inner12_novel_nonoverlap_v1.py`
- `.github/workflows/research-inner12-novel-nonoverlap-v1.yml`

### Strict non-overlap definition
A Stage-A race is used in rule discovery only when:
1. it is present in the exact 4HEAD `race_detail.csv`, and
2. `production_bet == 0`.

Rows absent from the 4HEAD comparison output are reported as `not_comparable` and are NOT silently treated as nonfire.

### Time split
Because exact current 4HEAD walk-forward comparison is cleanly available for Jun-Aug:
- June = train/search
- July = validation
- August = report-only confirmation
- September outcomes remain unread

August is prohibited from:
- choosing features
- choosing directions
- choosing thresholds
- choosing categories
- choosing interactions
- ranking/tie-breaking selected rules

### Targets
- route_3_family
- route_4_family
- route_5_family
- route_outer_core
- route_outer_wide
- route_1_escape retained as survival diagnostic

### Anti-duplication preference
Generic boat4-strength-only factors are flagged:
- boat4 WR/local/motor/Waku strength style fields
- preferred_novel output removes rules composed only of generic 4-strength factors

Mechanistic/novel axes remain allowed:
- boat3 attack/ST/exhibition structure
- boat3-vs-4 relative start/exhibition geometry
- boat5 follow-through/local/context
- inner weakness / 1-survival
- environment/venue if reproducible

### Workflow safety
- manual-only `workflow_dispatch`
- no push trigger
- py_compile preflight
- literal `\\n` guard
- exact 4HEAD audit replay is rebuilt in the same workflow
- three pipeline stages use `set -o pipefail`
- exact 4HEAD `race_detail.csv` is merged; no approximate clone gate
- production unchanged

Next:
- manually dispatch `research-inner12-novel-nonoverlap-v1`
- inspect monthly incremental volume (how many additional races/month)
- inspect 3/4/5 route precision after exact 4HEAD exclusion
- prioritize rules >=40% in June+July with meaningful volume, then inspect August only as confirmation
- if no robust >=40% remains, change the route decomposition rather than drifting back into the existing 4HEAD model.


## Strict non-overlap salvage + clean posthoc candidate — 2026-09-24

Run:
- 35998682116
- workflow: research-inner12-novel-nonoverlap-v1
- displayed FAILURE

Root cause:
- Stage-B rebuild: SUCCESS
- exact 4HEAD historical primitive prep: SUCCESS
- exact 4HEAD replay itself completed and printed `HEAD4_PH5_LIVE_WALKFORWARD_OK`
- the shell step failed only because `tee` tried to open `/tmp/head4_ph5_live_walkforward/run.log` before that directory existed:
  `tee: /tmp/head4_ph5_live_walkforward/run.log: No such file or directory`
- exact `race_detail.csv` was nevertheless generated and uploaded in artifact 10809251848.

Workflow fix:
- commit `273b8d2cd038e0a227b29fd6cc1fe6d0cdc80bb7`
- creates `/tmp/head4_ph5_live_walkforward` before tee.

Search hygiene fix:
- numeric venue code had accidentally been eligible as a numeric feature.
- commit `a300dc6911b898cf74f04931256732a4b3325ec7`
- venue is now categorical only.

### Artifact salvage analysis
Used exact artifacts:
- Stage-B completed artifact from Run 35992940551 / artifact 10805697327
- exact 4HEAD replay artifact from Run 35998682116 / artifact 10809251848

Strict non-overlap means:
- race is present in exact 4HEAD race_detail
- existing 4HEAD `production_bet == 0`

Monthly strict non-overlap universe:
- Jun: Stage-A 195 / strict non-overlap 173 / existing4 overlap 5 / not comparable 17
- Jul: Stage-A 229 / strict non-overlap 214 / existing4 overlap 4 / not comparable 11
- Aug: Stage-A 180 / strict non-overlap 146 / existing4 overlap 6 / not comparable 28

Baseline in strict non-overlap:
- outer WIDE:
  - Jun 31.21%
  - Jul 30.37%
  - Aug 33.56%
- outer CORE:
  - Jun 29.48%
  - Jul 28.50%
  - Aug 31.51%

### Rejected apparent rule
An apparent high-volume rule using `pre_pair_absdiff_stretch` looked strong, but audit found that `stretch` can default to 0.5 when prior preview data is unavailable.
About one-third of selected rows had both inner boats at default 0.5.
After removing both-default rows, the August rate fell below 40%.
Therefore this branch is REJECTED as missing-default contaminated.

### Clean posthoc Shadow candidate
After removing missing-default-driven ideas and generic 4-strength ideas, the simplest stable candidate was:

- existing 4HEAD production NONFIRE
- GLOBAL Stage-A already satisfied
- `boat4 prior_late20_rate <= 0.20`
  OR
- `boat5 prior_late20_rate >= 0.40`

Interpretation:
- boat4 has a reliable prior-only start history,
  OR
- boat5 has a distinctly late prior-start profile.
This is a field/start-configuration signal, not a generic "boat4 is strong" signal.

These are prior-only causal player-ST history features from `player_stats`; same-day outcomes are not used to construct them.

Historical rates in the exact 4HEAD NONFIRE universe:
- Jun: 65R / outer WIDE 26 = **40.00%**
- Jul: 72R / outer WIDE 29 = **40.28%**
- Aug: 52R / outer WIDE 21 = **40.38%**
- total: 189R / 76 = **40.21%**
- average volume: 63R/month

Outer WIDE definition:
- 3 makuri
- 3 makuri-sashi
- 4 makuri
- 4 makuri-sashi
- 5 makuri
- 5 makuri-sashi

Aggregate route composition in 189R:
- 3 family: 37/189 = **19.58%**
  - 3 makuri 20 = 10.58%
  - 3 makuri-sashi 17 = 8.99%
- 4 family: 29/189 = **15.34%**
  - 4 makuri 17 = 8.99%
  - 4 makuri-sashi 12 = 6.35%
- 5 family: 10/189 = **5.29%**
  - 5 makuri 2 = 1.06%
  - 5 makuri-sashi 8 = 4.23%
- outer CORE (excludes 5 makuri): 74/189 = 39.15%
- 1 escape: 67/189 = 35.45%

Monthly composition:
Jun 65R:
- WIDE 40.00%
- CORE 38.46%
- 1 escape 36.92%
- 3 family 18.46%
- 4 family 10.77%
- 5 family 10.77%

Jul 72R:
- WIDE 40.28%
- CORE 40.28%
- 1 escape 31.94%
- 3 family 22.22%
- 4 family 16.67%
- 5 family 1.39%

Aug 52R:
- WIDE 40.38%
- CORE 38.46%
- 1 escape 38.46%
- 3 family 17.31%
- 4 family 19.23%
- 5 family 3.85%

This is materially different from the existing 4HEAD production model:
- existing 4HEAD fires are explicitly excluded.
- 3-family is the largest head component overall.
- target is a 3/4/5 external-attack regime, not 4-head alone.

### Threshold robustness
Nearby rounded thresholds were also checked.
Example:
- b4 late20 <= .20 OR b5 late20 >= .40:
  40.00 / 40.28 / 40.38 by month.
This is not a knife-edge exact-quantile result.

Important caveat:
- August had already been seen by the time this cleanup/salvage analysis was done.
- Therefore this candidate is **POSTHOC_SHADOW_ONLY**, not a newly pristine validated production rule.
- September outcomes remain unread and must not be used casually.
- production remains unchanged.

Recommended next step:
- freeze this simple rounded Shadow rule as the first genuine non-overlap candidate.
- next research should predict WHICH head among 3/4/5 inside this regime, rather than rediscovering whether 4 is strong.
- 3-family should be the first branch because it is the largest component (19.58%).


## Shadow V2 branch geometry — 2026-09-24 late session

Starting point:
- Frozen Shadow V1 = exact existing 4HEAD production nonfire
- GLOBAL Stage-A candidate
- b4 prior_late20_rate <= .20 OR b5 prior_late20_rate >= .40
- historical Jun/Jul/Aug outer WIDE = 40.00% / 40.28% / 40.38%
- 189R total, 76 WIDE = 40.21%
- POSTHOC_SHADOW_ONLY; September unread; production unchanged.

### New branch geometry discovery
Two simple causal attack-geometry conditions were found inside the 189R Shadow:

A:
- `attack_gap_3minus4_waku_st >= .038`
- meaning boat3 Waku10 mean ST is at least .038 slower than boat4.

B:
- `post_gap_b3_vs_b5_pred <= -.09`
- meaning corrected predicted actual ST3 is at least .09 faster than ST5.

Important:
- these are not generic boat4 strength / motor / win-rate signals.
- A uses course-specific start history.
- B uses current exhibition ST corrected by prior-only player exhibition->actual ST bias.
- same-day outcomes are not part of these features.

### Historical branch anatomy
A only:
- 53R total
- outer WIDE 29/53 = 54.72%
- 3-family 12/53 = 22.64%
- 4-family 13/53 = 24.53%
- 5-family 4/53 = 7.55%
- 1 escape 14/53 = 26.42%
Monthly WIDE:
- Jun 9/18 = 50.00%
- Jul 9/16 = 56.25%
- Aug 11/19 = 57.89%

B only:
- 32R total
- outer WIDE 19/32 = 59.38%
- 3-family 13/32 = 40.63%
- 4-family 3/32 = 9.38%
- 5-family 3/32 = 9.38%
- 1 escape 7/32 = 21.88%
Monthly WIDE:
- Jun 6/11 = 54.55%
- Jul 7/12 = 58.33%
- Aug 6/9 = 66.67%
Monthly 3-family:
- Jun 4/11 = 36.36%
- Jul 6/12 = 50.00%
- Aug 3/9 = 33.33%

Both A and B:
- only 6R
- outer WIDE 2/6 = 33.33%
- 1 escape 3/6 = 50.00%
- ambiguous/conflicting branch; reject.

Neither:
- 98R
- outer WIDE 26/98 = 26.53%
- 1 escape 43/98 = 43.88%
- clearly weak external-attack geometry; reject.

### Frozen Shadow V2 gate
Use **A XOR B** only.

Historical:
- Jun 29R / 15 WIDE = 51.72%
- Jul 28R / 16 WIDE = 57.14%
- Aug 28R / 17 WIDE = 60.71%
- total 85R / 48 WIDE = 56.47%
- average ~28.3R/month
- 1 escape total 21/85 = 24.71%
- 3-family total 25/85 = 29.41%
- 4-family total 16/85 = 18.82%
- 5-family total 7/85 = 8.24%

Interpretation:
- B-only is the clearest 3-leaning branch.
- A-only is a mixed 3/4 attack branch with a modest 4 lean.
- both = conflict; reject.
- neither = no strong external geometry; reject.

### Code / workflow
Created:
- `research/research_inner12_shadow_branch_v2.py`
  - commit `f89837d2b5006aa99e2fd7e93b39b997255f8ab6`
- fast workflow:
  - `.github/workflows/research-inner12-shadow-branch-v2.yml`
  - commit `711a541a2afca8ad582ce200d25ed6e97badb2d0`

Fast workflow does NOT rebuild 40+ minutes of history.
It downloads pinned prior artifacts:
- Stage-B Run 35992940551 / `inner12-stageb-route-v1`
- exact 4HEAD replay Run 35998682116 / `inner12-novel-nonoverlap-v1`

Preflight verified:
- manual workflow_dispatch only
- no push trigger
- pinned artifact runs
- expected files must exist
- py_compile
- literal `\\n` guard
- pipefail
- September unread
- production unchanged

Next:
1. manually dispatch `research-inner12-shadow-branch-v2`.
2. confirm frozen historical numbers match.
3. Do NOT promote: this is posthoc shadow.
4. Future unseen period should validate Shadow V2.
5. For further research, B-only can be treated as a 3-leaning branch; A-only needs more work to separate 3 vs 4 without reverting to generic 4HEAD strength.


## Shadow V3 — B-only strong 3-head branch

Parent:
- Shadow V2 Run 36016060009 SUCCESS
- exact reproduction:
  - V2 selected 85R / outer WIDE 48 = 56.47%
  - A-only 53R / WIDE 54.72%
  - B-only 32R / WIDE 59.38%
  - B-only 3-family 13/32 = 40.63%

### Strong 3-head signal found inside B-only
Fixed rounded prior-only rule:
- `pre_pair_absdiff_prior_recent3_st >= .04`

Meaning:
- within the Stage-A dual-lag context, the prior causal recent-3 actual-ST histories of boats1 and2 differ by at least .04.

Historical B-only results:
- Jun: 5R / 3-family 3 = 60.00%
- Jul: 5R / 3-family 4 = 80.00%
- Aug: 5R / 3-family 3 = 60.00%
- total: 15R / 10 = 66.67%
- exactly 5R/month in these three months
- 3 makuri = 5
- 3 makuri-sashi = 5
- no 1-escape among the 15
- no 4-family / 5-family among the 15; the 5 misses were other routes (mostly boat2 head, plus one boat4 difference route not classed as 4M/4MS).

Threshold robustness:
- >=.030: 17R / 64.71%, monthly 50% / 83.33% / 60%
- >=.035: 16R / 68.75%, monthly 60% / 83.33% / 60%
- >=.040: 15R / 66.67%, monthly 60% / 80% / 60%
- >=.045: 14R / 71.43%, monthly 75% / 80% / 60%
- >=.050: 11R / 72.73%, monthly 75% / 75% / 66.67%
Thus .04 is a reasonable rounded Shadow threshold, not an exact knife-edge quantile.

### Current-exhibition confirmation
Within B-only:
- `post_b3_ex_st <= .10`
gives:
- Jun 8R / 3-head 4 = 50%
- Jul 9R / 5 = 55.56%
- Aug 6R / 3 = 50%
- total 23R / 12 = 52.17%

Combining strong prior rule + current exhibition confirmation:
- prior inner recent3 ST absdiff >= .04
- AND 3号艇 current exhibition ST <= .10
results:
- Jun 4R / 3 = 75%
- Jul 4R / 4 = 100%
- Aug 4R / 3 = 75%
- total 12R / 10 = 83.33%
- 3M 5 / 3MS 5
- no 1 escape
This is very small-N and remains diagnostic/Shadow only.

A diagnostic veto was also observed:
- one strong+exhibition miss was boat2 head when predicted ST2 beat ST3 by about .10.
- do NOT freeze a boat2 veto yet; sample is too small and that would be overfit.

### Code
Created:
- `research/research_inner12_shadow_3head_v3.py`
  - commit `9045781599a44e3cd495a89294b9ce372071cf99`
- `.github/workflows/research-inner12-shadow-3head-v3.yml`
  - commit `e47b4b21996591f34e7c24d84bcfe0868ae64f50`

Workflow:
- manual only
- downloads frozen V2 artifact from Run 36016060009
- no historical rebuild
- py_compile + literal-newline guard
- pipefail
- September unread
- production unchanged

Status:
- POSTHOC_SHADOW_ONLY
- not production approved
- future unseen confirmation needed.

Next:
- fire the fast V3 workflow and confirm exact reproduction.
- A-only exact 3-vs4 single-head classifier was explored; current predicted 3-vs4 ST alone was not good enough, so do not force it.
- priority after V3 confirmation: study the 5 B-only/strong misses as an inner-2 survival/veto mechanism without overfitting.


## Operational Shadow V4 — A-only dual-head adoption

User proposed:
- A-only should not be forcibly classified into 3-head vs 4-head.
- Buy both 3 and 4 heads.

This is supported by the actual A-only winner distribution.

A-only total 53R:
- winner 3: 12
- winner 4: 16
- winner 3 or 4: 28/53 = 52.83%
- winner 1: 16
- winner 2: 3
- winner 5: 5
- winner 6: 1

Monthly 3-or-4 head:
- Jun: 7/18 = 38.89%
- Jul: 9/16 = 56.25%
- Aug: 12/19 = 63.16%

Important:
- 4-family (4M/4MS) was only 13/53.
- Actual boat4 wins were 16/53 because there were additional 4差し/4抜き outcomes.
- Therefore A-only should use **boat3 OR boat4 head**, not only the M/MS route labels.

Combined operational routing frozen as Shadow V4:
- A-only -> heads 3 and 4
- B-only AND pre_pair_absdiff_prior_recent3_st >= .04 -> head 3 only
- B-only without strong gap -> PASS
- both -> PASS
- neither -> PASS

Combined historical race-level selected-head hit:
- Jun: 23R / 10 = 43.48%
- Jul: 21R / 13 = 61.90%
- Aug: 24R / 15 = 62.50%
- total: 68R / 38 = 55.88%
- average selected volume = 22.67R/month

Because A-only has two heads:
- total head slots = 121
- hit per head-slot = 38/121 = 31.40%
This is NOT directly comparable to a single-head model's head probability.
Opponent/ticket construction and ROI are still untested.

Created:
- `research/research_inner12_operational_shadow_v4.py`
  - commit `4a9189f286844eacaff2147ece7e80000849ee33`
- `.github/workflows/research-inner12-operational-shadow-v4.yml`
  - commit `f932346a9d074faa0ba19f4dabee3761bf6ac958`

Status:
- POSTHOC_SHADOW_ONLY
- September unread
- production unchanged

Next priority:
- build opponent/ticket anatomy for A-only separately by actual head3 vs head4.
- join result top3 only AFTER frozen V4 decisions are fixed.
- derive second/third distributions and candidate ranking from causal pre-race features.
- avoid using outcome frequencies to mutate the V4 head gate.


## V4/V5 execution results — 2026-09-24

### Operational Shadow V4
Run:
- 36021348905
- SUCCESS
- all steps SUCCESS
Markers:
- INNER12_OPERATIONAL_SHADOW_V4_OK
- POSTHOC_SHADOW_ONLY
- SEPTEMBER_UNREAD
- PRODUCTION_UNCHANGED

Monthly selected-head results:
- Jun: 23R / 10 hit = 43.48%
- Jul: 21R / 13 = 61.90%
- Aug: 24R / 15 = 62.50%
- total: 68R / 38 = 55.88%

A dual-head:
- 53R / 28 head hit = 52.83%
B strong 3-head:
- 15R / 10 = 66.67%

### Opponent anatomy V5
Run:
- 36021366565
- SUCCESS
- all steps SUCCESS
Markers:
- INNER12_OPPONENT_ANATOMY_SHADOW_V5_OK
- DECISION_FROZEN_BEFORE_RESULTS
- SEPTEMBER_UNREAD
- PRODUCTION_UNCHANGED

Important: V4 decision is frozen before outcome join. V5 is descriptive opponent anatomy only.

#### A-only when actual head = 3
N=12
Second:
- 1: 6/12 = 50%
- 4: 3/12 = 25%
- 2: 2/12 = 16.67%
- 5: 1/12 = 8.33%
Third:
- 4: 5/12 = 41.67%
- 1: 2/12 = 16.67%
- 2: 2/12 = 16.67%
- 6: 2/12 = 16.67%
- 5: 1/12 = 8.33%
Most frequent exact pair:
- 3-1-4: 4/12 = 33.33%
Other repeated:
- 3-4-2: 2/12 = 16.67%

#### A-only when actual head = 4
N=16
Second:
- 1: 5/16 = 31.25%
- 5: 4/16 = 25%
- 2: 3/16 = 18.75%
- 6: 3/16 = 18.75%
- 3: 1/16 = 6.25%
Third:
- 5: 5/16 = 31.25%
- 1: 4/16 = 25%
- 2: 3/16 = 18.75%
- 6: 3/16 = 18.75%
- 3: 1/16 = 6.25%
Most frequent exact pairs:
- 4-1-5: 3/16 = 18.75%
- 4-6-1: 3/16 = 18.75%
- 4-1-2: 2/16 = 12.5%
- 4-2-5: 2/16 = 12.5%

#### B-strong when actual head = 3
N=10
Second:
- 1: 3/10 = 30%
- 6: 3/10 = 30%
- 4: 2/10 = 20%
- 5: 2/10 = 20%
Third:
- 2: 3/10 = 30%
- 6: 3/10 = 30%
- 1: 2/10 = 20%
- 4: 2/10 = 20%
Exact pairs:
- 3-1-4: 2/10 = 20%
- 3-6-2: 2/10 = 20%
- remaining six patterns 1 each

### Opponent-any on head-hit rows
A head-hit rows:
- boat1 appears in 2nd/3rd: 17/56 slots = 30.36%
- boat5: 11/56 = 19.64%
- boat2: 10/56 = 17.86%
- boat4: 8/56 = 14.29%
- boat6: 8/56 = 14.29%
- boat3: 2/56 = 3.57%

B head-hit rows:
- boat6: 6/20 slots = 30%
- boat1: 5/20 = 25%
- boat4: 4/20 = 20%
- boat2: 3/20 = 15%
- boat5: 2/20 = 10%

### Immediate ticket-research implication
Do not use one common opponent order across A and B.

A, head3:
- strongest structural anchor is 3-1-4.
- second tier should preserve 4-2, plus 1-x variants.

A, head4:
- 1/5/6 dominate opponent anatomy.
- promising core exact pairs: 4-1-5, 4-6-1, 4-1-2, 4-2-5.

B, head3:
- second is concentrated on 1 or 6.
- third is concentrated on 2 or 6, with 1/4 secondary.
- promising cores: 3-1-4 and 3-6-2.

Next:
- build ticket candidates separately for A-head3 / A-head4 / B-head3.
- compare coverage vs point count.
- then, only after a fixed ticket set exists, join historical predeadline/closing odds for ROI diagnostics.
- do not change head gate from opponent outcomes.


## V6 fixed-ticket ROI setup — 2026-09-25 JST

Based on V5 opponent anatomy, fixed posthoc ticket sets were frozen BEFORE odds/ROI evaluation.

### LEAN
A-only (8 pts):
- 3-1-4
- 3-4-2
- 4-1-2
- 4-1-5
- 4-2-5
- 4-2-6
- 4-5-1
- 4-6-1

B-strong (4 pts):
- 3-1-4
- 3-4-6
- 3-5-6
- 3-6-2

Historical exact-ticket coverage before odds:
- total 24/68 = 35.29%
- Jun 8/23 = 34.78%
- Jul 8/21 = 38.10%
- Aug 8/24 = 33.33%
- A 18/53 = 33.96%
- B 6/15 = 40.00%

### BALANCED
A-only (10 pts):
- 3-1-4
- 3-1-6
- 3-4-2
- 4-1-2
- 4-1-5
- 4-2-5
- 4-2-6
- 4-3-6
- 4-5-1
- 4-6-1

B-strong (5 pts):
- 3-1-4
- 3-1-6
- 3-4-6
- 3-5-6
- 3-6-2

Coverage before odds:
- total 27/68 = 39.71%
- Jun 9/23 = 39.13%
- Jul 9/21 = 42.86%
- Aug 9/24 = 37.50%
- A 20/53 = 37.74%
- B 7/15 = 46.67%

### WIDE
A-only (12 pts):
- 3-1-4
- 3-1-5
- 3-1-6
- 3-4-2
- 4-1-2
- 4-1-5
- 4-2-5
- 4-2-6
- 4-3-6
- 4-5-1
- 4-5-2
- 4-6-1

B-strong (7 pts):
- 3-1-4
- 3-1-6
- 3-4-6
- 3-5-2
- 3-5-6
- 3-6-1
- 3-6-2

Coverage before odds:
- total 31/68 = 45.59%
- Jun 10/23 = 43.48%
- Jul 10/21 = 47.62%
- Aug 11/24 = 45.83%
- A 22/53 = 41.51%
- B 9/15 = 60.00%

### ROI evaluation policy
Created:
- research/research_inner12_ticket_roi_v6.py
  - commit b707e1fa1e0795fe5b8eb3699dc1010631a74caf
- .github/workflows/research-inner12-ticket-roi-v6.yml
  - commit 7aec843cce8ff1221a180119510ea64d4fbba75a

Frozen rules:
- ticket sets above are fixed before odds/ROI
- JPY5,000 per BET
- 100-yen inverse-odds Dutch
- evaluate ALL and composite odds >=5.0 gate
- prefer historical BoatraceCSV predeadline OD3
- official closing odds fallback only if predeadline snapshot absent
- manual workflow only
- V5 artifact pinned to Run 36021366565
- py_compile/literal-newline guard/pipefail
- September outcomes unread
- production unchanged
- POSTHOC_SHADOW_ONLY

Next:
- fire research-inner12-ticket-roi-v6
- inspect ROI by Lean/Balanced/Wide, month, A/B branch
- compare ALL vs COMP5
- do not change ticket sets after seeing ROI in this evaluation.


## V6 Run #1 completed but ROI INVALID due closing-odds path bug

Run:
- 36024005637
- workflow research-inner12-ticket-roi-v6
- GitHub conclusion SUCCESS
- all steps SUCCESS
- markers printed:
  - INNER12_FIXED_TICKET_ROI_SHADOW_V6_OK
  - TICKETS_FROZEN_BEFORE_ODDS_ROI
  - POSTHOC_SHADOW_ONLY
  - SEPTEMBER_UNREAD
  - PRODUCTION_UNCHANGED

However the ROI output from this run MUST NOT be used for model/ticket adoption.

Observed:
- only 35/68 frozen races had odds
- June had 0 evaluated races
- 33 races reported missing odds
- all evaluated rows were predeadline OD3; closing_fallback_R=0

Root cause:
- V6 script lives under `research/`
- it used `ROOT=Path(__file__).resolve().parent`
- therefore closing fallback searched the wrong path:
  `research/data/official_closing_odds3t/...`
- actual committed data is under repository root:
  `data/official_closing_odds3t/2026/06...`
  and June closing-odds files are present.

Fix:
- commit `cc2e9dfd90f88207c2010d7d838fb5f10dc55164`
- use `ROOT=Path(__file__).resolve().parents[1]`
- add hard guard:
  every one of the 68 frozen V4 races must exist in the combined odds map.
- if even one frozen race lacks odds, V6 now fails instead of silently reporting partial ROI.
- print ODDS_COVERAGE for audit.

Verified after refetch:
- repo_root_fix true
- full_coverage_guard true
- workflow remains manual-only
- pipefail true
- literal escaped-newline count 0

Important:
- Old Run 36024005637's displayed ROI numbers (300–1200% etc.) are invalid as evaluation because they are based on only 35/68 and exclude all June.
- Do not rerun old SHA. Start a new workflow_dispatch run after commit cc2e9dfd.
- Ticket sets remain frozen exactly as before; no ticket changes were made after viewing the invalid partial ROI.
- September remains unread.
- production unchanged.


## V6 Run #2 full-coverage ROI results — authoritative descriptive result

Run:
- 36026915473
- SUCCESS
- SHA 302e3bbd06df11602906af223b56380b8a3fab35

Critical audit:
- ODDS_COVERAGE 68
- frozen_missing 0
- all 68 frozen V4 races have odds
- 35 predeadline OD3
- 33 official closing fallback
- June: all 23 closing fallback
- July: 11 predeadline / 10 closing fallback
- August: all 24 predeadline
- ticket sets remained frozen before odds/ROI
- September unread
- production unchanged
- POSTHOC_SHADOW_ONLY

### LEAN
ALL:
- 68R / 24 hits = 35.29%
- stake 340,000
- payout 1,194,970
- profit +854,970
- ROI 351.46%
Monthly:
- Jun 195.90%
- Jul 541.75%
- Aug 334.04%
Branch:
- A: 53R / 18 hits = 33.96%, ROI 211.94%
- B: 15R / 6 hits = 40.00%, ROI 844.43%

COMP>=5:
- 59R / 17 hits = 28.81%
- ROI 362.56%
Monthly:
- Jun 181.93%
- Jul 580.47%
- Aug 366.78%
Branch:
- A: ROI 198.29%
- B: ROI 844.43%

### BALANCED
ALL:
- 68R / 27 hits = 39.71%
- ROI 306.09%
Monthly:
- Jun 191.92%
- Jul 476.77%
- Aug 266.15%
Branch:
- A ROI 197.03%
- B ROI 691.44%

COMP>=5:
- 50R / 15 hits = 30.00%
- ROI 322.69%
Monthly:
- Jun 136.24%
- Jul 545.13%
- Aug 313.42%
Branch:
- A ROI 168.81%
- B ROI 760.66%

### WIDE
ALL:
- 68R / 31 hits = 45.59%
- ROI 290.95%
Monthly:
- Jun 189.77%
- Jul 441.10%
- Aug 256.55%
Branch:
- A: 53R / 22 hits = 41.51%, ROI 195.67%
- B: 15R / 9 hits = 60.00%, ROI 627.61%

COMP>=5:
- 42R / 15 hits = 35.71%
- ROI 329.44%
Monthly:
- Jun 115.21%
- Jul 596.85%
- Aug 316.34%
Branch:
- A ROI 178.70%
- B ROI 754.25%

### Interpretation
- Lean maximizes descriptive ROI.
- Wide maximizes exact-ticket hit rate and has the lowest losing-streak / drawdown profile among ALL variants.
- Balanced is intermediate but not clearly dominant.
- B-strong is exceptionally profitable in-sample/posthoc across all ticket widths, but only 15 races total.
- A-only remains profitable descriptively at roughly 196–212% ALL ROI depending width.
- Composite >=5 does not universally improve branch-level A performance; it removes races and often reduces A ROI.
- For the whole set, COMP5 modestly improves headline ROI for Lean/Wide but not enough to erase the posthoc caveat.

### Major caveat
These ticket sets were derived from the same Jun-Aug outcome anatomy used for evaluation.
Therefore these ROI values are POSTHOC DESCRIPTIVE, not out-of-sample validation.
Also June uses closing odds only, so June is weaker evidence for LIVE parity than August.
Do not production-promote based on these figures alone.

Suggested shadow hierarchy:
- ROI-oriented: LEAN ALL as primary shadow candidate
- hit-rate-oriented: WIDE ALL as alternate shadow
- B-strong should remain separately tracked because it behaves materially differently from A-only.
- Do not use COMP5 automatically for A-only; evaluate prospectively first.


## September unseen validation authorized — 2026-09-25 JST

User explicitly approved opening the previously unread September outcomes for a fixed, no-retune validation.

Policy:
- September outcomes may now be read for validation only.
- No threshold, branch definition, head routing, ticket set, composite gate, or staking rule may change based on September during V7.
- Jun-Aug logic stays frozen.
- Production unchanged.

Validation period:
- 2026-09-01 through 2026-09-24.
- 2026-09-25 excluded.

Frozen replay:
- GLOBAL Stage-A unchanged.
- Existing 4HEAD exclusion uses exact frozen artifact HEAD4_PH5_PRODUCTION_V31_20260831.
- Exact 4HEAD production overlap = head_prob >= .36 AND orig4_adv_inside >= -.06.
- PH5 PLAYERHistory is causal through target_date-1.
- Shadow V1/V2, Operational V4, and V6 LEAN/BALANCED/WIDE tickets are unchanged.
- JPY5,000 Dutch; ALL and COMP>=5 both reported.

Daily causal order:
1. freeze candidate/head decisions from prior history + same-day pre-race/exhibition;
2. freeze existing4 overlap, A/B branch, V4 action and tickets;
3. load market odds;
4. only then read target-day results;
5. settle and update histories for the next day.

Added:
- research/validate_inner12_unseen_sep_v7.py
  - bf14cc356cfbf6c16009059c0638c04ef79134c4
  - c72e66b68c4e65faebe000840c9f559348fc9b07
  - 72f39c1a206826762504148c181e0022cf6d903f
- .github/workflows/validate-inner12-unseen-september-v7.yml
  - c7e8f9fab5f4c0f56be73dd69cd32a06c7eae7da

Workflow safeguards:
- manual-only workflow_dispatch
- py_compile
- frozen threshold and ticket-count checks
- PH5 artifact ID/cut/feature-count/leakage checks
- requires Sep24 cards/results
- set -o pipefail
- artifact upload always
- production unchanged

Next:
- manually dispatch validate-inner12-unseen-september-v7.
- On success report Stage-A, existing4 overlap, V4 selected count, A/B head rates, fixed ticket hit rates, ALL/COMP5 ROI and odds coverage.
- No September retuning.


## V7 pristine September validation — AUTHORITATIVE unseen result

Run:
- 36053754347
- Job 107815507476
- conclusion SUCCESS
- validation period 2026-09-01 through 2026-09-24
- artifact 10830784797 / inner12-unseen-september-v7

Audit markers:
- INNER12_SEPTEMBER_V7_PREFLIGHT_OK
- INNER12_PRISTINE_SEPTEMBER_VALIDATION_V7_OK
- SEPTEMBER_OUTCOMES_READ_TRUE
- SEPTEMBER_USED_FOR_TUNING_FALSE
- DECISIONS_FROZEN_BEFORE_SAME_DAY_RESULTS
- PRODUCTION_UNCHANGED

This is the first true unseen result for the frozen INNER12 Shadow V4/V6 logic.

### Frozen head-gate result
Stage-A:
- 149R

Exact existing 4HEAD overlap:
- 5R excluded

Frozen V4 selected:
- 19R
- all 19 settled

Selected-head hit:
- 10/19 = **52.63%**

A-only dual head 3/4:
- 12R
- 5 selected-head hits
- **41.67%**

B-strong head3:
- 7R
- 5 head3 hits
- **71.43%**

Interpretation:
- the HEAD/branch logic survived unseen September materially better than the fixed opponent tickets.
- B-strong is especially promising, but only 7 unseen races.
- A-only fell from the Jun-Aug posthoc 52.83% dual-head hit to 41.67%, but remains near the original >=40% target.
- combined operational head selection is 52.63%.

### Frozen ticket result — failed unseen validation

All 19 selected races had real predeadline OD3:
- predeadline_R = 19
- closing fallback = 0
- odds missing = 0

LEAN ALL:
- 19R / 1 exact trifecta
- hit rate 5.26%
- stake 95,000
- payout 25,120
- profit -69,880
- **ROI 26.44%**

LEAN COMP5:
- 17R / 1 hit
- ROI 29.55%

BALANCED ALL:
- 19R / 2 hits
- hit rate 10.53%
- stake 95,000
- payout 41,670
- profit -53,330
- **ROI 43.86%**

BALANCED COMP5:
- 14R / 0 hit
- ROI 0%

WIDE ALL:
- 19R / 2 hits
- hit rate 10.53%
- stake 95,000
- payout 38,590
- profit -56,410
- **ROI 40.62%**

WIDE COMP5:
- 10R / 0 hit
- ROI 0%

Conclusion:
- Jun-Aug posthoc ticket ROI did NOT validate.
- Do not adopt LEAN/BALANCED/WIDE V6 ticket sets.
- Do not use COMP5 gate for this branch based on current evidence.
- The failure is opponent selection, not primarily head selection.

### Opponent capture on the 10 unseen head-hit races
Actual head-hit trifectas:
- B: 3-1-2
- A: 4-3-6
- B: 3-2-6
- B: 3-4-2
- A: 3-5-6
- A: 4-6-5
- A: 3-1-4
- A: 3-4-6
- B: 3-2-6
- B: 3-1-5

Frozen ticket capture among those 10 correct-head races:
- LEAN: 1/10 = **10%**
- BALANCED: 2/10 = **20%**
- WIDE: 2/10 = **20%**

Branch split:
- A head-hit rows: 5
  - LEAN captured 1
  - BALANCED/WIDE captured 2
- B head-hit rows: 5
  - all three frozen ticket policies captured **0/5**

This is the central failure.

Especially B-strong:
- head3 itself validated very well: 5/7 = 71.43%
- but fixed B opponent tickets missed all five correct-head trifectas:
  - 3-1-2
  - 3-2-6
  - 3-4-2
  - 3-2-6
  - 3-1-5
- Jun-Aug B tickets were therefore strongly overfit to old opponent anatomy.

A unseen correct-head shapes also shifted:
- 4-3-6
- 3-5-6
- 4-6-5
- 3-1-4
- 3-4-6
Only 3-1-4 was captured by LEAN; BALANCED/WIDE also captured 4-3-6.

### Research implication
Preserve/freeze the V4 head gate for further shadow observation.
Reject V6 fixed opponent ticket sets.

Next opponent research should NOT start from old Jun-Aug exact combo frequencies.
Instead:
1. treat the selected head as fixed;
2. rank 2nd and 3rd using causal pre-race features per race;
3. specifically study B-strong where head3 is strong but 2nd/3rd ordering failed completely;
4. use PLAYERHistory, Waku10, current exhibition, motor, and relative structure for opponent ranking;
5. use September only as validation/diagnostic now that it has been opened; do not fit/tune on it if another unseen period is desired;
6. if continuing model development, fit on pre-September data and reserve post-2026-09-24 future races as the next untouched shadow validation.

Production remains unchanged.


## V8 opponent redesign — reference latest 1HEAD production

User direction:
- "相手選びは最新の1号艇モデル参考にして"

Latest 1HEAD main was inspected on 2026-09-25.
Relevant current production architecture:
- separate SECOND and conditional THIRD models;
- production opponentCore overlay:
  - EX 0.40
  - corrected ST 0.25
  - original straight 0.15
  - original average 0.20
- SECOND opponentCore coefficient G2 = 0.45
- THIRD opponentCore coefficient G3 = 1.00
- ticket pair alpha = 0.70
- HYBRID3 ticket structure:
  1. global best ordered pair
  2. another pair with the same second-place boat
  3. best pair with a different second-place boat
- latest 1HEAD also has wall3 / 5->6 / 1->5 top-up rules, but these are head-1-specific and are NOT blindly transferred.

Latest production evidence inspected:
- onehead_production_profile.py
- run_1head_v351_live_finalize.py
- run_v317_1head_opponent_error_features.py
- run_v318_1head_opponent_third_rebuild.py
- run_v299_1head_trifecta3_policy_search.py
- latest strong-signal production commit exists, but it concerns the 1HEAD 1->5 regime and is not a generic INNER12 opponent rule.

### INNER12 V8 design
Head gate remains exactly frozen V4:
- A-only -> heads 3 and 4
- B-strong -> head 3
- no head-gate retuning

New dynamic opponent model:
- training universe = Jun-Aug GLOBAL Stage-A races with actual winner 3 or 4
- September is NOT used for fitting
- SECOND and conditional THIRD are separate logistic models
- causal candidate features include:
  - grade
  - national/local strength
  - motor
  - Waku10 WR/ST/start-rank
  - national ST strength
  - prior PLAYERHistory all_win/all_p2/frame_win/frame_p2/recent_p2
  - current corrected exhibition / ST / original turn / straight / avg
  - opponentCore
  - candidate-vs-head relative features
  - conditional THIRD adds second/third relative features
- fixed regularization C=.25 for SECOND and THIRD; not tuned on September
- after base probabilities, apply exact latest 1HEAD opponentCore coefficients G2=.45 / G3=1.00
- pair alpha=.70
- exact HYBRID3 structure

Ticket count:
- A-only: 3 tickets for head3 + 3 tickets for head4 = 6 total
- B-strong: 3 tickets for head3
- no fixed historical combo list
- no automatic COMP5 gate
- no 1HEAD-specific top-up overlays yet

September handling:
- Sep1-24 has already been opened by V7, so V8 Sep1-24 is diagnostic only, not pristine model selection.
- future untouched shadow begins Sep25.
- do not alter V8 architecture based on Sep1-24 diagnostic if preserving Sep25+ prospective validation.

Files:
- research/research_inner12_onehead_opponent_v8.py
  - commit 74e515ea39f2a92b3763fe6e92cccedf0a9fbb55
- .github/workflows/research-inner12-onehead-opponent-v8.yml
  - commit 110b2fae84ee6e52a837dc753ecc4da063eb112c

Workflow safeguards verified:
- manual-only workflow_dispatch
- Stage-B artifact pinned Run 35992940551
- September V7 frozen decisions pinned Run 36053754347
- py_compile preflight
- exact current 1HEAD alpha/G2/G3/core-weight assertions
- set -o pipefail
- September used for fit = false
- production unchanged

Next:
- manually dispatch research-inner12-onehead-opponent-v8
- inspect TRAIN row counts and Sep1-24 diagnostic:
  - exact3 hits
  - SECOND top2 on correct-head rows
  - THIRD top2 conditional on actual second
  - BASE-no-core vs onehead-style core
  - flat 100-yen and JPY5,000 Dutch ROI
  - A vs B split
- do not promote from Sep1-24; prospective Sep25+ is the next untouched validation.


## V8 ticket width updated by user — 2026-09-25 JST

User direction:
- "3点は少ないよ倍あっていいと思う"

Operational interpretation adopted for V8 research:
- use top 6 HYBRID-ranked tickets per selected head, not top 3.
- A-only dual-head:
  - head3 top6
  - head4 top6
  - maximum 12 tickets total
- B-strong:
  - head3 top6
  - 6 tickets total

Unchanged:
- V4 head gate
- separate SECOND / conditional THIRD models
- 1HEAD opponentCore weights
- G2=.45 / G3=1.00
- alpha=.70
- no fixed historical combo list
- no COMP5 automatic gate
- production unchanged

Implementation:
- research/research_inner12_onehead_opponent_v8.py
  - commit cecae8daf0ca4d28aec6d875d99408d7630286f4
- .github/workflows/research-inner12-onehead-opponent-v8.yml
  - commit 3b9e493175d3c7cd230a9e055e5443a65a7ea1c5
- preflight now explicitly asserts top6 and A12/B6 ticket counts.

Bankroll note:
- JPY5,000 Dutch remains feasible with 12 tickets because each can receive at least JPY100.


## V8 six-ticket result — Run 36056529731

Workflow:
- research-inner12-onehead-opponent-v8
- Run 36056529731
- Job 107824830028
- SUCCESS
- Artifact 10831913795
- head SHA 0dc1ca1bb8ae6ad1c21475de7b472b0852540dcc

Preflight:
- INNER12_ONEHEAD_V8_PREFLIGHT_OK
- V4 head gate unchanged
- Sep labels not used for fitting
- future untouched period starts 2026-09-25
- production unchanged

Training:
- Jun-Aug GLOBAL Stage-A, actual head3/4 only
- train head races = 96
- SECOND rows = 480
- THIRD rows = 384
- separate logistic SECOND / conditional THIRD
- transferred current 1HEAD constants:
  - alpha=.70
  - G2=.45
  - G3=1.00
  - opponentCore EX .40 / ST .25 / straight .15 / orig avg .20
- top6 HYBRID per head

Sep1-24 diagnostic:
- V4 selected R=19
- head hits=10/19=52.63%
- exact3 hits=7/19=36.84%
- no-core baseline also 7 hits
- correct-head SECOND top2 = 70%
- correct-head THIRD top2 = 90%

Ticket widths:
- A-only: 12 tickets (6 for head3 + 6 for head4)
- B-strong: 6 tickets (head3)

ROI:
Flat 100 yen/ticket:
- stake 18,600
- payout 20,750
- profit +2,150
- ROI 111.56%

JPY5,000 Dutch:
- stake 95,000
- payout 152,670
- profit +57,670
- ROI 160.71%

Branch:
- A-only: 12R / exact3 2 hits = 16.67%
- B-strong: 7R / exact3 5 hits = 71.43%

B-strong is the standout:
- all five Sep correct-head B races were exact3-captured by V8 top6:
  - 3-1-2
  - 3-2-6
  - 3-4-2
  - 3-2-6
  - 3-1-5
- therefore B went from 0/5 opponent capture in fixed V6 tickets to 5/5 among correct-head races in dynamic V8.

A-only detailed diagnosis:
Correct-head A races = 5:
- hits:
  - 3-5-6
  - 3-1-4
- misses:
  - 4-3-6
  - 4-6-5
  - 3-4-6

For all 3 A correct-head misses:
- actual THIRD was within conditional THIRD top2 = 1
- actual SECOND was NOT within SECOND top2 = 0

Therefore current A failure is specifically SECOND ranking, not THIRD ranking.
This is a strong attribution result:
- THIRD model is already placing the eventual third boat well on these misses.
- A-side SECOND selection needs redesign / branch-specific training.
- Do not widen ticket count again before testing an A-specific SECOND model; the current 12 points already cover enough THIRD breadth.

OpponentCore overlay:
- exact3 hits with core = 7
- base no-core exact3 hits = 7
So the transferred 1HEAD core overlay is neutral on Sep1-24 in exact-hit count. It can remain for now, but no evidence yet that it adds hits.

Status:
- V8 is RESEARCH_SHADOW only.
- Sep1-24 is diagnostic because V7 had already opened it.
- prospective untouched shadow starts Sep25.
- production unchanged.

Next research priority:
1. preserve B V8 unchanged;
2. preserve V4 head gate;
3. build A-only-specific SECOND model / reranker;
4. use A branch geometry (actual candidate head3 vs head4, inside/outside relation, relative start, Waku10, PLAYERHistory, motor, current exhibition) to improve second-place rank;
5. keep conditional THIRD largely fixed initially, because A miss attribution points to SECOND.
