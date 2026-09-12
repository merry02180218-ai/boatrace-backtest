# CHAT HANDOFF — 2026-09-13 — 4号艇自動研究

Updated: 2026-09-13 JST
Repository: `merry02180218-ai/boatrace-backtest`
Scope: 4号艇 v291 volume expansion / rescue only.

## Immutable production baseline

Current production history remains `HEAD4_V291_COMP7`. Do not mutate it in place.

- PRE >= 0.28
- POST >= 0.25
- ENV_ENTRY >= 0.224790
- frozen v283 opponent order
- Top4 + composite >= 7.0
- exactly 10,000 JPY inverse-odds Dutch / 100-JPY Hamilton rounding

July/August 2026 remain NON-PRISTINE. September 2026 outcomes are outcome-blind and prohibited for fitting, calibration, rule selection or evaluation. v96 is prohibited from production logic.

## Exact A-LIVE identity audit result

Corrected workflow run `34704536525` completed successfully and proved the old OOF-A identity set is not identical to the frozen A-LIVE identity set.

- exact frozen A-LIVE: 47R
- old OOF A curves: 47R
- overlap: 44R
- added vs old: 3R
- dropped vs old: 3R
- identity sets equal: NO
- complete all-N curve coverage before recovery: 44/47
- missing exact identities:
  - `202604190703`
  - `202604272402`
  - `202606130609`

Therefore the old v288 OOF-A target-composite ROI is explicitly rejected as production evidence. No partial-44R ROI claim is allowed.

The run also verified:
- Jul/Aug outcomes used: false
- September outcomes used: false
- v96 production signal used: false
- frozen A-LIVE cutoff: 2026-06-30
- mapped A-LIVE threshold: 0.2710428764008591

## Recovery path implemented

The repository already contains immutable official closing 3T odds archives under `data/official_closing_odds3t/YYYY/MM/DD.csv` with 120 combinations, source metadata, and `snapshot_type=closing_displayed`. These are the same historical closing-odds class already used by the repo's v288 operational replay support.

New recovery implementation:

- `recover_4head_v291_exact_a_live_curves.py`
- commit `2a636b79137e40f4b0affd2544d03b749db648e2`
- workflow hardening commit `e0b8c6daef30f47c33fc94c718716b65c509990f`

Recovery logic is deliberately outcome-blind for ordering/selection:

1. reconstruct the exact frozen A-LIVE IDs;
2. identify only exact A-LIVE races absent from the old all-N table;
3. rebuild generic opponent feature rows from Apr-Jun pre-result data;
4. apply the frozen `head4_v291_downstream_20260630.json` SECOND and conditional THIRD inference states;
5. reproduce frozen v283 `TOP2XTOP2`, alpha2=0.60 full 20-pair order;
6. read immutable 120/120 official closing odds for the missing races;
7. create N=2..20 curves and ¥10,000 / ¥100 Hamilton inverse-odds Dutch economics;
8. append recovered rows only to a separate research CSV, preserving the original v288 OOF table unchanged;
9. rerun exact A-LIVE target-composite search only if 47/47 identity coverage is complete;
10. retain standalone all-month + LOMO promotion gates.

Recovered rows are marked `A_LIVE_RECOVERED`; the old OOF A identity set remains auditable and is not relabeled.

Expected new outputs:

- `audit_4head_v291_a_live_curve_recovery.json`
- `analysis_v291_4head_composite_odds_alln_exactalive.csv`
- `audit_4head_v291_a_live_identity.json`
- `analysis_4head_v291_a_targetcomp_rescue.csv`
- `analysis_4head_v291_a_targetcomp_rescue_monthly.csv`
- `analysis_4head_v291_a_targetcomp_rescue_lomo.csv`
- `summary_4head_v291_a_targetcomp_rescue.md`
- `head4_v291_a_targetcomp_rescue_candidate.json`

## CI failure and automatic resume — 2026-09-13

Workflow run `34707632922` failed before ROI research because `recover_4head_v291_exact_a_live_curves.py` called the frozen downstream inference loader while `artifacts/head4_v291_downstream_20260630.json` did not exist in the clean GitHub Actions checkout.

Exact failure class:
- `FrozenInferenceError: missing frozen artifact`
- this was infrastructure/orchestration failure, not a failed model gate or negative ROI result.

The repository already had `freeze_4head_v291_downstream_artifacts.py`, which reproduces archived June parity first and then fits/serializes only through the hard cutoff `2026-06-30`. The workflow simply had not invoked it.

Fix commit: `e3d4056055407457a9f54f7d96d0cdb70d8deead`.

The rescue workflow is now self-contained and fail-closed:
1. syntax-check freeze/inference/recovery/research code;
2. delete any stale downstream artifact in the runner;
3. rebuild `head4_v291_downstream_20260630.json` from <= Jun history;
4. require artifact and parity status PASS and explicit Jul/Aug=false, September=false, v96=false guards;
5. validate the frozen inference loader;
6. recover the exact missing A-LIVE curves;
7. require 47/47 exact curve coverage;
8. run target-composite / variable-N rescue research;
9. persist audit + research outputs only after all guards pass.

Current resumed workflow run: `34708490537` (`Research 4-head v291 A target-composite rescue`). At this handoff update it is in progress from commit `e3d4056055407457a9f54f7d96d0cdb70d8deead`.

## Current CI / resume point

Inspect run `34708490537` first.

If success:
- require `audit_4head_v291_a_live_curve_recovery.json.status == PASS`;
- require `missing_before_R == recovered_R`;
- require exact identity audit `missing_curve_R == 0` and `PASS_EXACT_CURVES_AVAILABLE`;
- then inspect rescue standalone R/ROI, each Apr/May/Jun ROI, and LOMO;
- only consider a new policy/version if the added route itself passes safety gates; do not use v291 base profit to mask a losing rescue.

If failure:
- inspect the exact failed step/log immediately;
- repair the failing parity, feature reconstruction, official closing-odds lookup, pair ordering, Dutch reconstruction or CI plumbing without relaxing leak guards;
- rerun in the same session and update this handoff again.

Do not use July/August outcomes or any September result/payout labels to solve failures or select rules. Current production `HEAD4_V291_COMP7` remains unchanged until a separately versioned rescue route passes all gates.
