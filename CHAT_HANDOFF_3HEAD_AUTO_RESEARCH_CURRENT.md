# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch `research/3head-player-attack-mode`; production v288 unchanged 94R/52 hits/ROI172.560638%.
- Pre-deadline inputs only; exact v288 exclusion preserved. Jul/Aug NON-PRISTINE. September outcomes UNREAD.

## Reproducible base
- March eligible 4,482R; Wave54 210R/71 heads=33.8095%.
- February eligible 3,970R/478 boat3 heads.
- Opponent v1: 25/71, ¥62,830, ROI99.7302%, hash `6d35377b...`.
- Historical Wave57/Wave58 remain UNVERIFIED.

## Opponent v2 — February-only CV completed
### BEFORE
- `a5a509d04059a1fd0d63a575f66990ec34e880ee`.
### Selection
- GroupKFold(5) by race, February boat3-head races only; 478 races /9,560 ordered pairs.
- Same deterministic v1 67-feature pipeline; C grid [.1,.25,.5,1,2,4,10].
- Mean (top3 capture, pair AUC): .1=(.380811,.696966); .25=(.384978,.696827); .5=(.384978,.696696); 1=(.384978,.696596); 2=(.384978,.696575); 4=(.384978,.696557); 10=(.384978,.696567).
- Predeclared priority top3 capture then AUC freezes **C=.25** before March settlement.
### March one-shot diagnostic
- 210R/71 heads; **25 hits /35.2113% capture**.
- ¥63,000 -> **¥62,830 / ROI99.7302%**.
- Identical hit/return/ROI to v1; therefore v2 is NOT a performance improvement.
- Ticket hash `50f71ee9626c43472552549da7a3496719077ac2f5dc8b561c2046687d27271d`; independent second execution produced identical hash.
### GitHub
- v2 specification/code delta commit `dbe826a0f3803886334d3e2468156a2d267d92d7`.
- result commit `c3c7ebaf1e7e010de85ae3c167071daa43356adb`.
- No new Actions; source Run34754875342 / Artifact10317157868 reused.
### Conclusion
- Regularization tuning alone does not improve the reproducible baseline. Do not tune C further on March.
- Next experiment should change opponent score structure, selected strictly with February grouped CV, e.g. decomposed P(second)*P(third) versus direct ordered-pair classifier, while preserving deterministic code/output audit.
- September UNREAD; production unchanged.

## Exact restart point
- Build opponent v3 structural scoring comparison using February-only grouped CV. Freeze structure before one March diagnostic. Keep v1/v2 as immutable reproducible baselines.
