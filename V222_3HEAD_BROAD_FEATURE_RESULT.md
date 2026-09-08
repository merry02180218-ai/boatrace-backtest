# v222 3-head broad feature audit result

Source workflow run: `34258259552`  
Source commit: `5080be184a53398b6a30ac24f3aa815eef160074`  
Artifact: `v222-3head-broad-feature-audit` id `10069108098`  
Artifact digest: `sha256:2c6bc05b48fa728d5681cc7785bbbcd672facec9c07cbb60d8c66040f8edd393`

## Guard
- Evaluation only: 2025-12 through 2026-06.
- 2026-07/08 excluded from training, tuning, feature selection and evaluation.
- Strict monthly prior-only refits.
- Current-day inputs are pre-deadline race card/waku10 + lane-corrected exhibition/ST/original exhibition + tilt.
- Historical closing odds are settlement-only.
- Fixed Top10 and exact 10,000-yen Hamilton Dutch.
- Head variants are volume-matched to legacy BASE p3>=0.30 monthly count.

## Main result
Best family in this audit: `PRIOR12+CURRENT+REL` head features with the existing v221 scenario-aware pair ranker.

- R: 471
- selected 3-head rate: 47.77%
- Top10 conditional coverage: 80.89%
- trifecta hit: 38.64%
- realized ROI: **87.34%**
- weighted monthly rm1/rm3/rm5 diagnostics: 82.84% / 75.50% / 69.10%
- mean monthly AUC: 0.7163
- mean monthly Brier: 0.10099

Monthly ROI: Dec 81.37%, Jan 84.67%, Feb 84.43%, Mar 79.94%, Apr 106.08%, May 98.41%, Jun 84.49%.
Only Apr exceeds 100%; therefore 87.34% is an improvement but not evidence of a profitable production rule.

## Comparison
- v221 PLAYER + v221 pair: ROI 83.32%, head rate 43.45%, Top10 coverage 80.86%, mean AUC 0.6814.
- v222 PRIOR12+CURRENT+REL + v221 pair: ROI 87.34%, head rate 47.77%, Top10 coverage 80.89%, mean AUC 0.7163.
- The experimental `V222_CURRENT_PAIR` did not beat v221 on the best head family: ROI 86.61% vs 87.34%. Granular current features are more useful in the head/race-selection layer than blindly expanding the pair model.

## Feature conclusion
Keep investigating these families:
1. prior1/prior2 lane-corrected exhibition/original-exhibition state,
2. current boat-3 exhibition/ST/original exhibition/motor state,
3. relative boat-3 edges versus boats 1/2/4/5/6,
4. wall weakness and makuri/makurizashi race-shape composites.

Do not adopt every granular current feature into the opponent model; this audit shows that can reduce Top10 coverage/ROI.

Status: research baseline only; continue searching unused pre-deadline feature families and require Sep+ prospective validation before production adoption.
