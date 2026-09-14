# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline 94R /52 hits / ROI172.560638%.
- Pre-deadline features only; JPY10,000 per selected race. Jul/Aug NON-PRISTINE. September forbidden.

## Wave36 benchmark
- Run34780059085: Apr-Jun391R/87 hits/ROI114.913%/+583,090.
- Conditional ranking on160 actual boat3-head cases: Top5=87/160.

## Wave36S-C
- Run34786354062: Apr-Jun305R/74 hits/ROI128.218%/+860,660. RESEARCH_CANDIDATE.

## Rank replacement research
- Wave39 direct linear pair:68/160, ROI70.911%, NO_ADOPTION.
- Wave40 blend:68/160, ROI70.911%, NO_ADOPTION.
- Wave36G ordinal blend:88/160 but ROI94.187%, NO_ADOPTION.
- Wave41 ExtraTrees:71/160, ROI74.814%, NO_ADOPTION.
- Wave42 factorized second/third:79/160, ROI90.795%, NO_ADOPTION.

## Wave43 conservative boundary correction — COMPLETE / NO_ADOPTION
- Plan commit6657d886e6ec0b8bce57c4113fd9275530b8fa8a.
- CI Run34793612036 success; Job103822377750; artifact10328797771.
- March and Apr-Jun correction collapsed to no-op; Apr-Jun old/new Top5 both87/160. NO_ADOPTION.

## User hypothesis / research pivot — ATTACK MODE FIRST
- User correctly raised that opponent ordering may fundamentally depend on whether boat3 wins by MAKURI versus MAKURI-SASHI. This is now the highest-priority structural hypothesis and supersedes the generic miss-subgroup audit.
- Rationale to test, not assume: MAKURI destroys/changes the inside wall and may favor different second/third topology (outer follow, surviving inner boat, attack-line relationships), while MAKURI-SASHI passes through the gap and can preserve different inside/outside boats. A single conditional 20-class ranker may be averaging these distinct mechanisms.
- BEFORE any Apr-Jun opening, inspect available source columns and historical result labels to determine whether actual winning technique (`kimarite`/decision) exists for training labels and, separately, which pre-deadline features can predict MAKURI vs MAKURI-SASHI. Actual kimarite may be used only as historical target/diagnostic, never as a live input.
- Build February training diagnostics split by actual boat3 MAKURI / MAKURI-SASHI; compare second-place identity, third-place identity, pair topology, current Wave36 actual-pair rank and Top5 capture.
- March OOS: train an attack-mode predictor using February only and evaluate mode classification plus opponent ranking by predicted mode. No actual March kimarite may be used to choose tickets; it is evaluation label only.
- Candidate architecture: P(mode | pre-deadline X) then mode-specific P(ordered opponent pair | boat3 wins, mode), optionally mixture-weighted rather than hard routing. Compare against frozen Wave36 ranking.
- Freeze all architecture/hyperparameters using Feb design + March OOS only. Require March improvement with existing-hit retention and early/late support before opening Apr-Jun.
- If source lacks reliable kimarite labels, stop and document that blocker rather than infer actual attack mode from post-race finishing order.
- Production v288 untouched; Wave36 head gate unchanged initially; Top5 and JPY10,000 Dutch unchanged for evaluation. Jul/Aug NON-PRISTINE only; September forbidden/unread.

## Exact restart point
1. Inspect Wave21 source schema/build pipeline for reliable actual kimarite / winning-technique labels.
2. If present, quantify Feb+March MAKURI vs MAKURI-SASHI opponent topology and Wave36 rank performance separately.
3. Train Feb-only pre-deadline mode predictor + mode-specific opponent ranker; select/freeze on March OOS only.
4. Only if March supports it, one-shot Apr-Jun evaluation; update handoff afterward.
