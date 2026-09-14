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
- March OOS C-grid [.02,.05,.10,.15,.30] selected C=.10 without monetary criterion. March old:24/38 Top5=63.158%, MRR.2888, mean rank6.553, Top3=11. New:25/38 Top5=65.789%, early13/19=68.421%, late12/19=63.158%, MRR.32045, mean rank6.395, Top3=16. Old hits lost1, misses rescued2.
- Frozen Apr-Jun result:160 actual boat3-head cases; new Top5=79/160=49.375% vs old87/160=54.375%. MRR.3362; mean rank6.569; Top1=27, Top3=56, Top8=110, Top10=124. Retained76 old hits, lost11, rescued3.
- Money on same391 Wave36 selected races:79 hits / payout3,550,100 / profit -359,900 / ROI90.795%; maxDD811,360. Monthly Apr29 hits ROI110.091%/+122,100; May30 hits ROI97.587%/-34,990; Jun20 hits ROI64.239%/-447,010.
- Jul-Aug NON-PRISTINE:79 hits / ROI90.139%/-323,440; v288 overlap0; September forbidden/unread.
- Decision NO_ADOPTION. Factorizing second and third improves March but does not generalize to Apr-Jun.

## Current ranking conclusion
- Frozen Wave36 conditional multiclass logistic remains the strongest verified opponent ranking among tested replacements.
- Wave39/40 linear pair, Wave41 ExtraTrees pair, Wave42 factorized second/third all fail Apr-Jun OOS. Wave36G improved raw Top5 by one hit but materially damaged ROI.
- Do NOT widen TopN or change stake allocation yet; user explicitly wants ranking reviewed first.
- Next ranking research should be a genuinely different learning-to-rank / pairwise-comparison formulation or a conservative correction layer that preserves Wave36 ordering unless pre-April evidence is strong. It must be selected using Feb+March only and must explicitly penalize displacement of existing March Top5 hits.

## Exact restart point
1. Keep Wave36 ranking as current champion; v288 production untouched.
2. Next experiment, if continuing, use a conservative learning-to-rank architecture rather than another flat classifier replacement.
3. Select/freeze on Feb+March only; then one-shot Apr-Jun evaluation with old-hit retention, rescued misses, rank metrics, and unchanged Top5 Dutch economics.
4. Jul/Aug NON-PRISTINE only; September unread.
