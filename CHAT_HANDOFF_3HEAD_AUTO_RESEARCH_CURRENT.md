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
- Run34787885427 failed closed: exact v288 opponent orderer covered296/305; 9 missing. Partial ROI invalid until NO-BET semantics fixed.

## Wave36S-F
- Run34789147056 success; artifact10327388998 SHA256 07439a302357495b3052c107e469630256a59bfac201338848da1a6a37b98931.
- Top1-3 JPY8000 + Top4-5 JPY2000: Apr-Jun ROI106.616%/+258,700 vs original114.913%/+583,090. NO_ADOPTION.

## Wave36 boat3-head / Top5-miss rank audit — COMPLETE
- Plan commit348bb24c8f452ba8f1705f09c8022cd24f2e92d3; script commit33fe37d39b3910546dfd94a7f06a050ea8a21704.
- Source run34754875342 artifact10317157868. Rebuilt frozen Wave36 conditional ranking with rolling schedule and exact v288 exclusion.
- Parity check: rebuilt Top5 matched saved Wave36 Top5 on all391/391 Apr-Jun selected races.
- 391 selected; actual boat3 head160; Top5 hits87; boat3-head Top5 misses73.
- Miss actual-rank counts: r6=7,r7=9,r8=12,r9=7,r10=3,r11=6,r12=5,r13=3,r14=2,r15=7,r16=4,r17=3,r18=0,r19=3,r20=2.
- Cumulative miss recovery: Top6 7/73=9.6%; Top7 16=21.9%; Top8 28=38.4%; Top10 38=52.1%; Top15 61=83.6%; Top20 73=100%.
- Diagnostic equal-Dutch expansion: Top5 ROI114.913%; Top6 101.224%; Top7 97.775%; Top8 97.932%; Top10 93.085%; Top15 90.868%; Top20 88.006%.

## Wave36 opponent ranking rebuild — STARTING / USER PRIORITY
- User explicitly decided to review the opponent ranking itself before any selective tail activation, TopN expansion, or stake-allocation research. This supersedes the prior restart point.
- Objective: improve ordering of the 20 conditional combinations 3-X-Y, especially Top5 capture conditional on actual boat3 win, while retaining current good Top5 hits.
- Strict selection protocol: February is training/design only; March is OOS model/ranker selection and stability validation. Freeze the new ranker before any Apr-Jun outcome inspection. Apr-Jun is final pristine evaluation only; no retuning after seeing it.
- Head gate remains frozen Wave36 p3>=0.365448 initially so this experiment isolates opponent-order quality rather than changing head selection.
- Candidate ranking architectures may use only pre-deadline/static features already available in the all-race source. No closing/settlement odds as ranking features. No realized Apr-Jun result or payout may influence selection.
- Evaluate on March first: among actual boat3-head cases, actual-pair MRR/mean rank/median rank and Top1/Top3/Top5/Top8/Top10 capture; early/late March stability. Also record regressions where frozen Wave36 Top5 was correct but candidate drops actual pair outside Top5.
- Only candidate(s) chosen from March may be evaluated on Apr-Jun. Final Apr-Jun comparison must report same rank metrics, Top5 conversion among boat3-head, old-hit retained/lost, old-miss rescued, monthly stability, and optional ROI using unchanged Top5 exact JPY10,000 Dutch solely as evaluation.
- Production v288 untouched; exact v288 overlap0; Jul/Aug diagnostic only if needed; September forbidden/unread.

## Exact restart point
1. Inspect current Wave36 conditional ranking implementation/features and available source columns.
2. Build opponent-ranker candidates using Feb only and select/freeze using March OOS only.
3. Evaluate the frozen winner on Apr-Jun once; do not retune from Apr-Jun.
4. Update this handoff after completion with exact commits/run/artifact/results and decision.
