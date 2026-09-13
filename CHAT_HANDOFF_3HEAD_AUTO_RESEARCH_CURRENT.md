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

## Wave34i structural motor — FINAL
- Run 34774184349 success; artifact 10322014882.
- March validation used no monetary ROI: Feb-derived q=.20 structural motor cut -1.1074, top5; 39R; 3-head rate 51.282%, early 50.000%, late 52.174%.
- Apr-Jun pristine: 314R / 55 hits / ROI 70.745% / profit -918,620 yen.
- Monthly: Apr 70R / 13 hits / ROI 89.496% / -73,530; May 103R / 20 hits / ROI 73.360% / -274,390; Jun 141R / 22 hits / ROI 59.525% / -570,700.
- min month 59.525%; red months 3; max DD 1,088,140 yen.
- Jul-Aug shadow 406R / ROI 75.950%.
- combined v288 + holdout: 408R / ROI 94.202% / profit -236,550 yen. overlap 0. NO_ADOPTION.
- Conclusion: relative-motor confirmation family does not generalize; stop iterating it.

## Wave35 — STARTED
- Distinct corrected-scope family. Re-test a simple probabilistic head gate under the FINAL Wave20 population, because older Waves27-31 were later found to have excluded the old 678R universe and are not definitive corrected-scope evidence.
- Use exactly 63 static pre-deadline features. Feb trains a regularized logistic P(3-head) model plus conditional exact-order logistic model.
- March selects only a sparse probability threshold/top-K using label stability, NOT payout/ROI: require support in both chronological March halves and maximize worst-half 3-head hit rate/lift, with tie preference for larger support and simpler threshold. No closing odds in gate selection.
- Freeze after March. Apr-Jun untouched pristine; Jul/Aug frozen NON-PRISTINE shadow. Exact v288 94 exclusion, zero overlap, no September, JPY10k Dutch.
- Report R/hits/ROI/profit/monthly/min month/red months/max DD/overlap/combined.

## Exact restart point
1. Implement Wave35 corrected-scope logistic head gate + conditional exact-order model.
2. Launch and auto-fix technical failures without weakening guards.
3. Record results here after completion.
4. If NO_ADOPTION, continue a distinct corrected-scope full-population family automatically.
