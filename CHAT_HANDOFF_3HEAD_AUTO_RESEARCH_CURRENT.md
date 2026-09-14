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
- Protocol unchanged: Feb design/train, March OOS selection only, Wave36 p3>=0.365448 fixed, Top5 fixed, no odds as features.
- March tree grid leaf[5,10,15,20,30] selected leaf30 by worst-half Top5. Chosen March:18/38 Top5=47.37%, early=47.37%, late=47.37%, MRR.3222, mean rank7.158. This is already below old Wave36 24/38=63.16%.
- Apr-Jun:71/160 Top5=44.375%; MRR.2759; mean rank7.413; retained48, lost39, rescued23.
- Money391R/71 hits/ROI74.814%/-984,790. Monthly Apr82.069%, May71.210%, Jun71.971%. Jul-Aug NON-PRISTINE ROI79.203%/-682,140. v288 overlap0; September unread.
- Decision NO_ADOPTION. Tree pair architecture is not a replacement for current Wave36 ordering.

## Wave42 factorized second/third ranker — STARTING
- Distinct architecture: model P(second=a | boat3 wins) and P(third=b | second=a, boat3 wins), then score ordered pair as product. This respects 3-X-Y structure instead of direct 20-class or flat pair binary ranking.
- Uses only existing static63 pre-deadline features. No odds/settlement features.
- February trains. March selected Wave36 races chooses C from [.02,.05,.10,.15,.30] using worst-half Top5, full Top5, MRR, mean rank; no money criterion.
- Preliminary March-only check: C=.10 gives Top5 25/38=65.79% vs old24/38=63.16%, worst-half63.16%, MRR.3204 vs old.2888, mean rank6.395 vs old6.553, Top3 16/38 vs11/38. This is not yet an adoption result.
- Freeze C after March, then evaluate Apr-Jun once with fixed Wave36 head gate/Top5/JYP10,000 Dutch. Report retained/lost/rescued, monthly and aggregate ROI, rank metrics, v288 overlap0. Jul/Aug diagnostic only; September forbidden/unread.

## Exact restart point
1. Implement Wave42 factorized second/third ranker and March-only C selection.
2. Freeze winner before Apr-Jun evaluation.
3. Compare against frozen Wave36 ranking; reject if economics or robustness deteriorate materially.
4. Update handoff after CI with exact run/job/artifact/results.
