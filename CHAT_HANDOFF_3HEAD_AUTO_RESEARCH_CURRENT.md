# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch `research/3head-player-attack-mode`; production v288 unchanged 94R/52 hits/ROI172.560638%.
- Pre-deadline inputs only; exact v288 exclusion preserved. Jul/Aug NON-PRISTINE. September outcomes UNREAD.

## Reproducible base
- March eligible 4,482R; Wave54 210R/71 heads=33.8095%.
- February eligible 3,970R/478 boat3 heads.
- Opponent v1/v2 March benchmark: 25/71, ¥62,830, ROI99.7302%.
- Historical Wave57/Wave58 remain UNVERIFIED.

## Opponent v3 structural comparison — COMPLETE
### BEFORE commit
- `c54d3a496c3b95f27412212efbe7add44550d3b9`.
### February-only GroupKFold(5)
- Direct C=.10/.25/.5/1/2/4 capture: 38.0811%, **38.4978%**, 38.4978%, 38.4978%, 38.4978%, 38.4978%. Tie broken by AUC => direct C=.25 (AUC .696827).
- Decomposed P(second)*P(third) C=.10/.25/.5/1/2/4 capture: 37.4561%, **37.6667%**, 37.6667%, 37.6645%, 37.4561%, 37.4561%; best AUC among top capture C=.25=.695602.
- Therefore decomposed scoring loses ~0.83pp February top3 capture and also lower AUC. Frozen winner before March = **direct ordered-pair C=.25**, identical to v2.
### March one-shot
- 210R/71 heads; 25 hits=35.2113%; ¥63,000 -> ¥62,830; ROI99.7302%.
- Ticket SHA256 `50f71ee9626c43472552549da7a3496719077ac2f5dc8b561c2046687d27271d`; independent second run identical.
### GitHub
- v3 contract commit `b54af3f290e5daf6a1067e94a9e043f7c7b8e7e5`.
- v3 result commit `5eae95ddff3465576c50c3567d0ddfebea3e0350`.
- No new Actions; source Run34754875342 / Artifact10317157868 reused.
### Conclusion
- REJECT decomposed P(second)*P(third); retain direct v2 baseline. Structural decomposition did not improve February CV or March diagnostic.
- Next research should remain February-only and test feature-information improvements inside direct pair ranking (controlled feature-family ablation/addition), not more C tuning or decomposition.
- September UNREAD; production unchanged.

## Exact restart point
- Start v4 direct-pair feature-family research using February GroupKFold only. Freeze any feature change before one March diagnostic; preserve deterministic double-run audit.
