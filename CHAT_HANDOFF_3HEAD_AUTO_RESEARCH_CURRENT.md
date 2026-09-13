# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline 94R /52 hits / ROI172.560638%.
- Pre-deadline features only; JPY10,000 per selected race. Jul/Aug NON-PRISTINE. September forbidden.

## Wave36 benchmark
- Run34780059085: Apr-Jun 391R/87 hits/ROI114.913%/+583,090.

## Wave36S-C
- Run34786354062: Apr-Jun305R/74 hits/ROI128.218%/+860,660. RESEARCH_CANDIDATE.

## Wave36S-D
- Run34787885427 failed closed: exact v288 opponent orderer covered296/305; 9 missing. Superseded for current research direction.
- Diagnostic rerun34788719785 confirmed all 9 are absent_from_legacy_v108, so exact legacy-orderer parity cannot cover full Wave36S-C universe without violating fail-closed.

## Wave36S-F
- Run34789147056 success; artifact10327388998.
- Top1-3 JPY8000 + Top4-5 JPY2000: Apr-Jun ROI106.616%/+258,700 vs original114.913%/+583,090. NO_ADOPTION.

## Wave36 boat3-head / Top5-miss rank audit — COMPLETE
- Rebuilt frozen Wave36 Top5 exactly on391/391 Apr-Jun selected races.
- 391 selected; actual boat3 head160; Top5 hits87; boat3-head Top5 misses73.
- Miss recovery if blindly expanding: Top6 7/73, Top7 16/73, Top8 28/73, Top10 38/73, but equal-Dutch ROI falls from Top5 114.913% to Top6 101.224%, Top7 97.775%, Top8 97.932%, Top10 93.085%.

## Prior Wave39 direct pair ranker — COMPLETE / NO_ADOPTION
- Run34782729676 success; pair45 binary ranker chosen C0.08 from March only.
- March selected conversion 24/38=63.158% with equal early/late halves.
- Apr-Jun frozen evaluation:391R/68 hits; conditional conversion68/160=42.5%; ROI70.911%/-1,137,370. Apr95.099%, May64.463%, Jun54.978%. Therefore direct pair ranker is rejected.

## Wave40 blended opponent ranker — RUNNING
- Purpose: preserve the strong frozen Wave36 conditional multiclass ranking while testing whether March-validated pair information can improve rank order without sacrificing old Top5 hits.
- Script commit ffe2557a7b618d3c490e97fe09c80d8fad61ff49; workflow commit a9f842c7f935e72a4547e976c246c0fccaac0fea.
- Run34790604535 workflow research-3head-wave40-blend-ranker currently in progress.
- Frozen head gate remains Wave36 p3>=0.365448. Static63 baseline score blended with pair45 C0.08 score at alpha baseline weights [0,.25,.5,.75,1].
- February trains/designs; March OOS selects alpha by worst-half Top5 capture, then old-hit retention, full Top5 capture, MRR. No March money used. Apr-Jun evaluated once after freeze. Jul/Aug diagnostic only.
- Report March rank metrics and stability; Apr-Jun MRR/mean/median rank/Top1/3/5/8/10, old Top5 retained/lost, old misses rescued, monthly Top5 ROI/profit/maxDD, v288 overlap0.

## Exact restart point
1. Inspect Run34790604535.
2. If failure, fix implementation plumbing only and rerun; do not change candidate protocol from Apr-Jun results.
3. If success, record artifact/results and decision here.
4. If Wave40 does not robustly beat frozen Wave36, continue with a distinct pre-April ranker architecture rather than tuning alpha on Apr-Jun.
