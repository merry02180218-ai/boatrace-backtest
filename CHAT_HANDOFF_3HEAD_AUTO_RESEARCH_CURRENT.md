# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline: 94R / 52 hits / ROI 172.560638%.
- FINAL research scope is Wave20 full population: every available six-boat race Feb 1-Aug 31 2026 from BoatraceCSV race_cards pre-deadline program data; no v243/PRE/bet/route candidate prefilter. Exclude exact v288 operational 94R only.
- Jul/Aug NON-PRISTINE shadow only; September outcomes forbidden.
- Prediction uses exactly 63 static pre-deadline features. Settlement and closing odds are evaluation/staking only.
- Stake JPY10,000 per selected race with Dutch allocation; selected overlap with v288 must be zero.

## Stable source / scope correction
- Wave20 Run 34749917116, workflow research-3head-wave20-allrace-universe, head 33c296c008a7a588e9f694feb577a3612b4731d7: SUCCESS. 32,111 six-boat races. Monthly Feb 4,100 / Mar 4,607 / Apr 4,244 / May 4,832 / Jun 4,488 / Jul 4,920 / Aug 4,920. Missing program date 2026-06-17 recorded.
- Wave21 Run 34751314113: exact settlement usable 31,518/32,111.
- Wave22 Run 34752573368: full 120 closing trifecta odds 31,605/32,111.
- Wave19b Run 34749707037 failed due missing payout column and is superseded. Preserve failure; never revert to old v243 678R / non-baseline 584R universe.

## Wave34 family
- Wave34c Run 34769751846: Apr-Jun 381R / 54 hits / ROI 86.794% / profit -503,130 yen; current best Wave34-family pristine ROI.
- Wave34h Run 34773911115: ROI 68.726%; NO_ADOPTION.
- Wave34i Run 34774184349: Apr-Jun 314R / 55 hits / ROI 70.745%; NO_ADOPTION. Relative-motor confirmation family retired.

## Wave35 corrected-scope logistic stable gate — FINAL
- Run 34775954251 success; artifact 10324000675.
- March gate p3>=0.402921, top5 (q=.99). March 45R / head rate 44.444%; early 50.000%; late 40.741%; worst-half 40.741%. Selection used label stability only, no ROI.
- Apr-Jun pristine: 202R / 54 hits / ROI 102.805% / profit +56,660 yen.
- Monthly: Apr 56R / 20 hits / ROI 141.657% / +233,280; May 79R / 20 hits / ROI 90.930% / -71,650; Jun 67R / 14 hits / ROI 84.333% / -104,970.
- min month 84.333%; red months 2; max DD 330,930 yen.
- Jul-Aug NON-PRISTINE shadow: 178R / 49 hits / ROI 102.711% / +48,250 yen.
- combined v288 + holdout: 296R / ROI 124.957% / profit +738,730 yen. exact v288 overlap 0.
- Decision NO_ADOPTION because two pristine months remain red and holdout ROI is below research-candidate threshold. This is nevertheless the strongest corrected-scope post-Wave34 signal so far.

## Wave36 — STARTED
- Distinct corrected-scope full-population head family: shrinkage Linear Discriminant Analysis (LDA) for P(3-head), retaining conditional exact-order logistic only for ticket ordering.
- Use exactly 63 static pre-deadline features, median imputation + standardization, LDA solver=lsqr with automatic shrinkage.
- Feb trains. March selects sparse probability quantile/top-K by label stability only: support in chronological early/late halves, maximize worst-half 3-head head rate, then full-March head rate/ticket coverage/support. No payout/closing odds in selection.
- Freeze after March. Apr-Jun untouched pristine; Jul/Aug NON-PRISTINE frozen shadow. Exact v288 94 exclusion, zero overlap, September forbidden, JPY10k Dutch.
- Report R/hits/ROI/profit/monthly/min month/red months/max DD/overlap/combined and compare to Wave35 102.805%.

## Exact restart point
1. Implement Wave36 shrinkage-LDA stable gate.
2. Launch and auto-fix technical failures without weakening guards.
3. Record results here after completion.
4. If NO_ADOPTION, continue another distinct corrected-scope full-population family automatically.
