# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch `research/3head-player-attack-mode`; production v288 unchanged 94R/52 hits/ROI172.560638%.
- Pre-deadline inputs only; exact v288 exclusion preserved. Jul/Aug NON-PRISTINE. September outcomes UNREAD.

## Reproducible base
- March eligible 4,482R; Wave54 210R/71 heads=33.8095%.
- February eligible 3,970R/478 boat3 heads.
- Opponent v1/v2 March benchmark: 25/71, ¥62,830, ROI99.7302%.
- v2 February GroupKFold selected C=.25; no March improvement.
- Historical Wave57/Wave58 remain UNVERIFIED.

## BEFORE WORK — opponent v3 structural scoring comparison (2026-09-15)
- Compare score structures using February boat3-head labels only and GroupKFold by race.
- Direct ordered-pair baseline: existing deterministic v2 pipeline.
- Decomposed candidate approach: train separate candidate-level P(second) and P(third) models on candidate boats 1,2,4,5,6; score each ordered pair by P(second=a)*P(third=b), a!=b.
- Candidate features are fixed pre-deadline own lane one-hot, own national ST/win/2/3, local win/2, motor2/3, boat2, and candidate-vs-boat3 gaps. No realized March information used for structure/C selection.
- Compare top3 true-pair capture first; AUC/ranking diagnostics secondary. Regularization grid fixed [.1,.25,.5,1,2,4].
- Freeze February-CV winner before one March settlement. Exactly 3 tickets/R; deterministic tie-break score desc, second asc, third asc.
- Commit executable code/config, CV table, March tickets/summary and double-run hash.
- Do not tune toward historical Wave57. September UNREAD; production unchanged.

## Exact restart point
- Execute v3 February grouped-CV structure comparison, freeze winner, then one March diagnostic and deterministic double-run audit.
