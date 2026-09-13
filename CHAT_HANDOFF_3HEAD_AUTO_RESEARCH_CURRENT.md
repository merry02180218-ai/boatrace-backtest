# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline 94R /52 hits / ROI172.560638%.
- Pre-deadline features only; JPY10,000 per selected race. Jul/Aug NON-PRISTINE. September forbidden.

## Wave36 benchmark
- Run34780059085: Apr-Jun 391R/87 hits/ROI114.913%/+583,090.

## Wave36S-C
- Run34786354062: Apr-Jun305R/74 hits/ROI128.218%/+860,660. RESEARCH_CANDIDATE.

## Wave36 boat3-head / Top5-miss rank audit
- 391 selected; actual boat3 head160; Top5 hits87; Top5 misses73.
- Blind expansion hurts ROI: Top5 114.913%; Top6 101.224%; Top7 97.775%; Top8 97.932%; Top10 93.085%.

## Wave39 direct pair ranker — COMPLETE / NO_ADOPTION
- Run34782729676 success; pair45 binary ranker chosen C0.08 from March only.
- Apr-Jun391R/68 hits; conditional conversion68/160=42.5%; ROI70.911%/-1,137,370. Rejected.

## Wave40 blended opponent ranker — COMPLETE / NO_ADOPTION
- Run34790604535 success; artifact10328251093 SHA256 f71035ad3e19d8ccbce9a99df23d5a88257bf720ae7c9796e5acc67ce8a371fa.
- March candidate grid alpha baseline [0,.25,.5,.75,1] selected alpha0 by worst-half Top5; March 38 boat3-head cases, Top5 24/38=63.158% with early=late=63.158%; MRR .3824; mean rank5.526.
- Apr-Jun frozen result collapsed to 391R/68 hits, ROI70.911%/-1,137,370; old Top5 hits87 -> new68; retained46, lost41, rescued22. NO_ADOPTION.
- Jul/Aug NON-PRISTINE ROI83.343%/-546,340. v288 overlap0; September unread.
- Conclusion: pair45 linear rank signal is unstable across periods and must not replace/blend into Wave36 ranking.

## Wave36G local/CI side audit
- Run34790913552 success; artifact10328506579. Alternate ordinal blend produced Apr-Jun Top5 88/160 vs old87/160 but ROI94.187%/-227,300, so also NO_ADOPTION. This reinforces that hit-count-only ranking improvement can destroy payout economics.

## Wave41 ExtraTrees opponent ranker — STARTING
- User priority remains ranking rebuild before TopN/stake work.
- Distinct architecture from Wave39/40: candidate-pair 45 pre-deadline features with ExtraTrees binary scorer; no odds/settlement features.
- February trains/designs only. March selected Wave36 races is the model-selection surface; compare min_samples_leaf candidates using Top5 capture, early/late stability, MRR, mean rank, Top3/8/10. Freeze chosen tree ranker before Apr-Jun evaluation.
- Preliminary March-only diagnostics indicate ExtraTrees leaf15 can match old Top5 24/38 while materially improving MRR/mean rank/Top3; this is not yet an adoption result.
- Keep Wave36 p3>=0.365448 fixed, Top5 fixed, exact JPY10,000 Dutch for evaluation, v288 overlap0, Jul/Aug diagnostic only, September forbidden/unread.

## Exact restart point
1. Implement Wave41 ExtraTrees pair ranker with March-only model selection.
2. Freeze winner and run Apr-Jun comparison against frozen Wave36 old ranker: Top1/3/5/8/10, MRR/mean rank, retained/lost/rescued Top5 hits, monthly ROI/profit/maxDD.
3. Reject if it gains rank metrics but damages economics materially; do not tune on Apr-Jun.
4. Update handoff after CI with exact run/job/artifact/results.
