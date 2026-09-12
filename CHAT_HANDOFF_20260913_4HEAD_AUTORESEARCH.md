# CHAT HANDOFF — 2026-09-13 — 4号艇自動研究

Updated: 2026-09-13 JST
Repository: `merry02180218-ai/boatrace-backtest`
Scope: 4号艇 v291 volume expansion / rescue only.

## Immutable production baseline

Current production remains `HEAD4_V291_COMP7`. Do not mutate it in place.

- PRE >= 0.28
- POST >= 0.25
- ENV_ENTRY >= 0.224790
- frozen v283 opponent order
- Top4 + composite >= 7.0
- exactly ¥10,000 inverse-odds Dutch / ¥100 Hamilton rounding

July/August 2026 remain NON-PRISTINE. September 2026 outcomes are outcome-blind and prohibited for fitting, calibration, rule selection or evaluation. v96 is prohibited from production logic.

## Exact A-LIVE audit and recovery

Audit run `34704536525` proved the old OOF-A identity set was not identical to frozen A-LIVE.

- exact frozen A-LIVE: 47R
- old OOF A curves: 47R
- overlap: 44R
- added vs old: 3R
- dropped vs old: 3R
- missing exact identities before recovery:
  - `202604190703`
  - `202604272402`
  - `202606130609`

Therefore old v288 OOF-A ROI is rejected as production evidence.

Recovery implementation uses immutable official closing 3T odds plus frozen v291/v283 ordering logic. Successful workflow run `34708490537` completed the recovery and research pipeline.

Final audit state:
- exact A-LIVE = 47R
- complete all-N curve coverage = 47/47
- `audit_4head_v291_a_live_curve_recovery.json.status == PASS`
- `audit_4head_v291_a_live_identity.json.status == PASS_EXACT_CURVES_AVAILABLE`
- `missing_curve_R == 0`
- Jul/Aug outcomes used = false
- September outcomes used = false
- v96 used = false

Persisted exact research input:
- `analysis_v291_4head_composite_odds_alln_exactalive.csv`

## Added-race rescue result — REJECT

The exact 47R A-LIVE target-composite/additional-race rescue completed after recovery.

Output:
- `head4_v291_a_targetcomp_rescue_candidate.json`
- `summary_4head_v291_a_targetcomp_rescue.md`

Decision: **REJECT**.

Reason:
- no standalone-safe added-race candidate passed the required stability/LOMO gates;
- v291 base profit must not be used to hide a losing rescue route;
- production entry set remains unchanged.

## CI reproducibility finding

A later combined workflow run `34709042736` failed while regenerating the frozen downstream artifact before variable-N research.

Failure:
- v283 conditional THIRD June parity max absolute drift = `9.04380706659e-05`
- fail-closed parity guard blocked the run.

This was not a variable-N model failure. The artifact rebuild itself showed small nondeterministic numeric drift between clean CI runs. The guard was NOT relaxed.

Operational decision:
- keep the already successful/persisted exact 47/47 curves from run `34708490537` as the research input;
- isolate downstream ticket-count research from noisy artifact regeneration;
- do not loosen parity tolerances merely to make CI pass.

Isolated workflow:
- `.github/workflows/research-4head-v291-base-variable-n.yml`

## Immutable-base variable-N research

Goal: improve hit coverage without changing the 29 production race identities or the ¥10,000 per-race bank.

Operational rule family:
- entry identity stays frozen `HEAD4_V291_COMP7`;
- start from frozen v283 ranked pair order;
- choose the largest `N >= 4` whose composite odds remain above a floor, capped by `maxN`;
- total bank remains exactly ¥10,000 per race with the same inverse-odds Dutch/Hamilton economics;
- no additional races are admitted.

Development/evaluation universe:
- April–June 2026 only;
- July/August excluded as NON-PRISTINE;
- September outcomes excluded;
- no v96.

### v1 LOMO implementation bug

Initial isolated run `34709567539` itself completed successfully, but the research code incorrectly required `R == 29` inside every two-month LOMO training split. This made every LOMO split structurally return `NO_TRAIN_CANDIDATE`.

This was a validation-code bug, not negative model evidence.

The rule family and promotion thresholds were not relaxed. v2 changed only expected-R validation so each LOMO training split requires the actual frozen base-race count in those two months.

### Corrected v2 result

Corrected isolated CI run `34709643396`: **SUCCESS**.

All of the following passed:
- frozen 47/47 input audit;
- immutable 29R entry-set guard;
- Jul/Aug exclusion;
- September outcome exclusion;
- v96 exclusion;
- variable-N research;
- corrected LOMO;
- artifact upload and GitHub persistence.

Current research candidate:

- rule: `composite odds floor = 5.0`, `maxN = 6`
- entry races: unchanged 29R
- bank: unchanged ¥10,000/race
- baseline N=4:
  - ROI 300.26%
  - hit rate 31.03%
- candidate:
  - ROI 213.48%
  - hit rate 34.48%
  - average N 5.72
  - average composite odds 6.475
  - minimum monthly ROI 140.37%

Monthly candidate result:

| month | R | ROI | profit | hit rate | avg N |
|---|---:|---:|---:|---:|---:|
| 2026-04 | 12 | 298.52% | +¥238,220 | 50.00% | 5.75 |
| 2026-05 | 9 | 140.37% | +¥36,330 | 22.22% | 5.67 |
| 2026-06 | 8 | 168.18% | +¥54,540 | 25.00% | 5.75 |

Corrected LOMO:

| holdout | training-selected rule | train R | hold R | variable ROI | base ROI | variable hit | base hit |
|---|---|---:|---:|---:|---:|---:|---:|
| Apr | floor=4.0, maxN=16 | 17 | 12 | 239.63% | 481.22% | 58.33% | 50.00% |
| May | floor=5.0, maxN=6 | 20 | 9 | 140.37% | 177.91% | 22.22% | 22.22% |
| Jun | floor=4.0, maxN=12 | 21 | 8 | 122.51% | 166.46% | 25.00% | 12.50% |

All three LOMO holdouts are profitable (>100% ROI).

Candidate status in `head4_v291_base_variable_n_candidate.json`:
- `selection_tier = STRONG_STABLE`
- `lomo_all_holdouts_profitable = true`
- `status = RESEARCH_CANDIDATE_NOT_FROZEN`

## Neighborhood robustness

The `floor=5.0 / maxN=6` result is not a single-cell knife edge.

Examples from the same predeclared grid:
- floor 3.0–4.5 / maxN 6: ROI 208.26%, hit 34.48%, monthly ROI floor 123.53%
- floor 5.0 / maxN 8: ROI 198.24%, hit 34.48%, monthly ROI floor 134.03%
- floor 4.0 / maxN 12: ROI 180.07%, hit 41.38%, monthly ROI floor 122.51%
- floor 4.0 / maxN 16: ROI 188.83%, hit 44.83%, monthly ROI floor 143.52%
- floor 3.0 / maxN 16: ROI 172.41%, hit 51.72%, monthly ROI floor 136.40%

Interpretation:
- there is a broad profitable region for expanding ticket count;
- maxN=6 / floor=5.0 is the current best simple balance under the fixed selection gates;
- more aggressive expansion can raise hit rate substantially, but gives up more ROI and is not the current first promotion candidate.

## Decision / current production status

**Important candidate found, but production v291 is still unchanged.**

Current production remains `HEAD4_V291_COMP7` Top4.

The first promotion candidate for a separately versioned policy is:
- same 29 race entry identities;
- same ¥10,000/race bank;
- expand from Top4 up to Top6 only while composite odds remain >= 5.0.

Why it is a candidate:
- all Apr/May/Jun months profitable;
- corrected LOMO all three holdouts profitable;
- hit rate improves versus Top4;
- neighboring parameter cells remain profitable, so the result is not isolated.

Why it is not frozen yet:
- Apr–Jun sample is still only 29 base races;
- full-period ROI is lower than the Top4 baseline, which is expected from added coverage but must be treated as a deliberate hit-rate/ROI tradeoff;
- September outcomes must remain untouched/outcome-blind, so they cannot be used to promote the rule now.

## Next research point

Resume from the candidate above without changing production v291.

Preferred next work:
1. audit per-race ticket additions for floor=5.0/maxN=6 and verify every added ticket is derivable from pre-deadline odds only;
2. compare fixed Top4 vs candidate at the race level: newly rescued hits, existing-hit dilution, payout/Dutch effects, and N distribution;
3. perform label-free September operational shadow replay only if the repository has the required pre-deadline odds — verify that N and stakes can be generated in real operation, but do NOT inspect September outcomes/payouts;
4. if operational replay is clean, prepare a separately versioned candidate policy; do not overwrite `HEAD4_V291_COMP7`.

Do not use July/August outcomes or any September result/payout labels for further rule selection. Do not relax the frozen-artifact parity guard to force rebuilds to pass.
