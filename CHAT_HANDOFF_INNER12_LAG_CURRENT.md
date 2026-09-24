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
