# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline: 94R / 52 hits / ROI 172.560638%.
- FINAL research scope is Wave20 full population: every available six-boat race Feb 1-Aug 31 2026 from BoatraceCSV race_cards pre-deadline program data; no v243/PRE/bet/route candidate prefilter. Exclude exact v288 operational 94R only.
- Jul/Aug NON-PRISTINE shadow only; September outcomes forbidden.
- Prediction uses exactly 63 static pre-deadline features. Settlement and closing odds are evaluation/staking only.
- Stake JPY10,000 per selected race with Dutch allocation; selected overlap with v288 must be zero.

## Stable source / scope correction
- Wave20 Run 34749917116: SUCCESS. 32,111 six-boat races. Monthly Feb 4,100 / Mar 4,607 / Apr 4,244 / May 4,832 / Jun 4,488 / Jul 4,920 / Aug 4,920. Missing program date 2026-06-17 recorded.
- Wave21 Run 34751314113: exact settlement usable 31,518/32,111.
- Wave22 Run 34752573368: full 120 closing trifecta odds 31,605/32,111.
- Wave19b Run 34749707037 failed due missing payout column and is superseded; never revert to 678R/584R scope.

## Wave35
- Run 34775954251 success. Apr-Jun 202R / 54 hits / ROI 102.805%; Apr 141.657 / May 90.930 / Jun 84.333; Jul-Aug shadow 102.711%; overlap 0; NO_ADOPTION.

## Wave36 shrinkage-LDA — RESEARCH CANDIDATE, AUDIT REQUIRED
- Run 34780059085 success; artifact 10324527230.
- March gate p3>=0.365448 top5 q=.98; 90R; head rate 42.222%; early 44.737%; late 40.385%.
- Apr-Jun pristine: 391R / 87 hits / ROI 114.913% / +583,090 yen.
- Apr 121R / 33 hits / ROI 175.280% / +910,890.
- May 145R / 33 hits / ROI 103.005% / +43,570.
- Jun 125R / 21 hits / ROI 70.290% / -371,370.
- min month 70.290%; red months 1; max DD 717,360 yen.
- Jul-Aug NON-PRISTINE shadow: 328R / 79 hits / ROI 89.756% / -335,990.
- baseline + holdout 485R / ROI 126.086% / +1,265,160. exact v288 overlap 0.
- Decision RESEARCH_CANDIDATE, but user flagged temporal degradation as possible leakage. Do not promote until audit passes.

## Wave36L leak / temporal audit — STARTED
- Audit before any adoption. Do not tune a new production gate in this wave.
- Verify the exact 63 feature names produced by build_static contain no settlement/result/payout/odds/current-meet post-race fields and no suspicious target-derived names.
- Verify walk-forward index causality: every prediction row's training max date must be strictly earlier than test month/date; March trained Feb only; Apr train <Apr; May <May; Jun <Jun; Jul/Aug frozen <=Jun.
- Verify preprocessing is fit inside each training fold only (SimpleImputer, StandardScaler, shrinkage LDA and conditional logistic all pipeline-fit on trainX).
- Quantify temporal degradation without changing gate: split Apr, May, Jun and Jul/Aug chronologically; report R/hits/head rate/ticket hit rate/ROI/profit and high-payout concentration. Determine whether April ROI is driven by a few outlier payouts versus sustained hit quality.
- Add a negative-control leakage test: shuffled training labels should collapse predictive head separation; fail audit if suspiciously strong.
- Required current feature missing => fail closed. September forbidden. Jul/Aug remains NON-PRISTINE.

## Exact restart point
1. Implement Wave36L audit script/workflow.
2. Launch and auto-fix technical failures without weakening guards.
3. Record PASS/FAIL and diagnostics here.
4. Only if PASS, continue Wave36 robustness research; if FAIL, invalidate Wave36 and repair source/features automatically.
