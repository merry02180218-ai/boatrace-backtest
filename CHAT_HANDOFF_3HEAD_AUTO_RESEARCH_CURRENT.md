# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline 94R /52 hits / ROI172.560638%.
- Pre-deadline features only; JPY10,000 per selected race. Jul/Aug NON-PRISTINE. September forbidden.

## Wave36 benchmark
- Run34780059085: Apr-Jun 391R/87 hits/ROI114.913%/+583,090.
- Conditional ranking on 160 actual boat3-head cases: Top5=87/160.

## Wave36S-C
- Run34786354062: Apr-Jun305R/74 hits/ROI128.218%/+860,660. RESEARCH_CANDIDATE.

## Rank audit
- Wave36 selected391; actual boat3 head160; Top5 hits87; misses73.
- Blind TopN expansion hurts: Top6 ROI101.224%; Top7 97.775%; Top8 97.932%; Top10 93.085%.

## Wave39 direct linear pair ranker — NO_ADOPTION
- Run34782729676: Apr-Jun68/160 Top5; ROI70.911%/-1,137,370.

## Wave40 blend ranker — NO_ADOPTION
- Run34790604535; artifact10328251093 SHA256 f71035ad3e19d8ccbce9a99df23d5a88257bf720ae7c9796e5acc67ce8a371fa.
- March selected alpha0 pair signal; Apr-Jun68/160 Top5, ROI70.911%/-1,137,370; retained46/lost41/rescued22.

## Wave36G ordinal blend side audit — NO_ADOPTION
- Run34790913552; artifact10328506579. Apr-Jun88/160 Top5 but ROI94.187%/-227,300. Hit-count-only gain destroyed economics.

## Wave41 ExtraTrees pair ranker — COMPLETE / NO_ADOPTION
- Final optimized CI Run34791534572 success; Job103816570018; artifact10328516441; SHA256 9e601629f77fdaa9216f325642d2e457c75c17411ab84a257684c279de6f5870; head SHA d6f239330902a00b13735fab61ef7d32727b3092.
- March selected leaf30:18/38 Top5=47.37%, MRR.3222, mean rank7.158 vs old24/38=63.16%.
- Apr-Jun:71/160 Top5=44.375%; ROI74.814%/-984,790. Monthly Apr82.069%, May71.210%, Jun71.971%. NO_ADOPTION.

## Wave42 factorized second/third ranker — COMPLETE / NO_ADOPTION
- Script commit bb53ff83ce283a9d8aa618683bac48511b5ea167; workflow commit024b2e1edbc955f09b2bb4fcf6a57318cf06c8a0.
- Run34791746174 success; Job103817146598; artifact10328373250; SHA256 c7c851655442a906e4a25e6638568be78cbd47f1aeae0233a615f9ca0c5bc05a; head SHA024b2e1edbc955f09b2bb4fcf6a57318cf06c8a0.
- Architecture: P(second=a|boat3 win) * P(third=b|second=a,boat3 win), static63 pre-deadline features only. Wave36 head gate p3>=0.365448 and Top5 fixed.
- March OOS C=.10: new25/38 Top5 vs old24/38, but frozen Apr-Jun new79/160 vs old87/160.
- Money same391 races:79 hits / ROI90.795% / -359,900. NO_ADOPTION.

## Current ranking conclusion
- Frozen Wave36 conditional multiclass logistic remains the strongest verified opponent ranking.
- Do NOT widen TopN or change stake allocation yet.

## Wave43 conservative correction layer — STARTING
- Work plan written BEFORE implementation as required.
- Preserve Wave36 full ranking as the base; do not replace it globally.
- Learn only a conservative boundary correction around the Top5 cutoff: candidate promotions from ranks6-10 may displace rank4/5 only when pre-April evidence is strong.
- Use pre-deadline/static features plus Wave36 score/rank-margin information only; no closing-result-derived feature and no realized winning odds as a feature.
- Train/design on February and select/freeze thresholds/hyperparameters on March OOS only. Explicitly penalize displacement/loss of existing March Top5 winners; prioritize net rescued-minus-lost and early/late stability, then rank metrics. No March monetary tuning.
- After freezing, open Apr-Jun exactly once. Report old Top5 hits retained/lost, misses rescued, net hits, Top1/3/5/8/10, MRR/mean rank, monthly/aggregate exact JPY10,000 Top5 Dutch ROI/profit/maxDD.
- v288 production untouched and overlap must remain0. Jul/Aug NON-PRISTINE diagnostic only. September forbidden/unread.

## Exact restart point
1. Implement Wave43 conservative Top5-boundary rerank correction on frozen Wave36 ordering.
2. Freeze correction using Feb+March only with explicit old-hit preservation penalty.
3. One-shot Apr-Jun evaluation; reject if economics or robustness deteriorate materially.
4. Update this handoff after CI with exact commits/run/job/artifact/results.
