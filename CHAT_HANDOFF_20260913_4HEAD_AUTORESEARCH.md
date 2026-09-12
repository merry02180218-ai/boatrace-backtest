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

## Important audit finding

The existing `analyze_4head_v291_a_targetcomp_rescue.py` was not valid evidence for production A-LIVE rescue because it directly used `analysis_v288_4head_composite_odds_alln_detail.csv` and `layer == 'A'`. Those A identities are historical v271 OOF identities. The frozen final A-LIVE artifact (`HEAD4_V273_A_LIVE_QMAP`) can select different exact race identities even if aggregate/monthly counts are similar.

Therefore old target-composite A-rescue metrics must NOT be promoted or quoted as an exact A-LIVE backtest.

## Research resumed

Commits created to correct the research path:

- `ecf279c2bc78ce9e9b91c19c2b0b90a7d33d5736` — harden workflow with exact A-LIVE identity audit and scikit-learn dependencies.
- `383c6f8115678fde7b17326ac47060e6d5fe8e38` — reconstruct exact frozen A-LIVE identities before any ticket optimization.

Workflow:

- `.github/workflows/research-4head-v291-a-targetcomp.yml`
- current run: `34704536525`

The corrected research now:

1. validates the frozen A-LIVE artifact (`artifacts/head4_v273_a_live_20260630.json`), cutoff 2026-06-30;
2. reconstructs the exact Apr-Jun A-LIVE candidate identities using frozen final-model inference;
3. compares them to old v271 OOF A identities;
4. requires complete archived N=2..20 pre-deadline odds curves for every exact A-LIVE race;
5. fails closed if even one exact A-LIVE identity lacks a complete curve;
6. only if coverage is complete, runs variable-N target-composite rescue research;
7. excludes the frozen v291 base bets from rescue economics;
8. requires standalone all-month safety plus LOMO before a candidate can be considered.

Outputs expected:

- `audit_4head_v291_a_live_identity.json`
- `analysis_4head_v291_a_targetcomp_rescue.csv`
- `analysis_4head_v291_a_targetcomp_rescue_monthly.csv`
- `analysis_4head_v291_a_targetcomp_rescue_lomo.csv`
- `summary_4head_v291_a_targetcomp_rescue.md`
- `head4_v291_a_targetcomp_rescue_candidate.json`

## Resume point

At this handoff update, run `34704536525` is in progress. The next automation/chat must inspect this run first.

If success:
- read `audit_4head_v291_a_live_identity.json` and the summary;
- if `missing_curve_R > 0`, reject any partial-subset ROI claims and continue by reconstructing/fetching immutable archived pre-deadline 120/120 odds for the missing exact identities;
- if all exact curves are available, inspect standalone monthly ROI and LOMO and only then consider a new version/policy ID.

If failure:
- inspect job logs, fix the exact failure, rerun, and update this handoff.

Do not use July/August outcomes or any September result/payout labels to solve failures or select rules.
