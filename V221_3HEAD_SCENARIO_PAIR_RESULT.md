# v221 3-head scenario-aware opponent result

Source workflow run: `34256548572`  
Source commit: `9c1795b48e11e7de3d7cfb8e176ef4920f342811`  
Artifact: `v221-3head-scenario-pair` id `10068204206`  
Artifact digest: `sha256:8761f7a8c2be618dc5903a65c82f6aee4f3e0f264aa735df769707cf66a8dacb`

## Frozen protocol

- 2026-07/08 are excluded from training, tuning and evaluation.
- Evaluation is 2025-12 through 2026-06, strict monthly prior-only.
- Head selectors use the v220 findings: PLAYER and PRIOR12, volume-matched to the legacy BASE p3>=0.30 count each month.
- Opponent ranking is no longer ability-only. v221 adds:
  - prior1/prior2 lane-corrected exhibition and original-exhibition state for both second/third candidates and boat 3;
  - prior-only player general ability and current-frame win/top2 tendencies;
  - relative candidate-vs-candidate and candidate-vs-boat3 state differences;
  - 3-makuri / 3-makurizashi development context and inside-survival / outside-follow interactions.
- Same-day current result is not used to build historical features.
- Historical closing odds are settlement-only.
- Top10 and exact 10,000-yen Hamilton Dutch are fixed diagnostics.

## Aggregate

|head selector|R|3-head|v166 Top10 cov|v221 Top10 cov|v166 ROI|v221 ROI|v166 maxDD|v221 maxDD|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|PLAYER|481|43.45%|79.43%|80.86%|81.05%|83.32%|964,620|839,380|
|PRIOR12|486|39.30%|80.63%|81.15%|82.34%|82.83%|997,450|969,610|

## Robustness

|selector/ranker|ROI rm1|ROI rm3|ROI rm5|
|---|---:|---:|---:|
|PLAYER / v166|79.49%|77.16%|75.53%|
|PLAYER / v221|81.77%|79.37%|77.67%|
|PRIOR12 / v166|80.52%|77.15%|75.02%|
|PRIOR12 / v221|81.01%|77.64%|75.43%|

## Monthly notes

- PLAYER: v221 coverage improves in Jan/Feb/Apr, is flat in Mar/May/Jun, and worsens in Dec. Aggregate ROI improves by +2.28pt.
- PRIOR12: v221 coverage improves in Feb/Mar/Apr/May, is flat in Jan, and worsens in Dec/Jun. Aggregate ROI improves by +0.49pt.
- Therefore the scenario-aware direction is supported, but it is not yet a profitable production rule under the new realized ROI definition.

## Status

- **Research baseline fixed:** v221 scenario-aware opponent ranking replaces ability-only v166 as the next comparison baseline for the redesigned 3-head chain.
- **Production adoption: NOT YET.** Neither PLAYER nor PRIOR12 chain reaches 100% realized ROI in clean pre-Jul evaluation.
- Continue development from v221 without using Jul/Aug as evidence. Sep+ immutable LIVE remains prospective validation.
