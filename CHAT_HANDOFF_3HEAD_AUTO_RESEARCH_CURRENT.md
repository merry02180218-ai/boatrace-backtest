# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline: 94R / 52 hits / ROI 172.560638%.
- Research scope: all available six-boat races Feb-Aug 2026 minus exact v288 94R only.
- Jul/Aug NON-PRISTINE shadow only; September outcomes forbidden.
- Prediction uses exactly 63 static pre-deadline features. Closing odds are staking/evaluation only.
- Stake JPY10,000 per selected race with Dutch allocation; selected overlap with v288 must be zero.

## Stable source
- Wave20 Run 34749917116: success; full six-boat universe 32,111R.
- Wave21 Run 34751314113: exact settlement usable 31,518/32,111.
- Wave22 Run 34752573368: full 120 closing trifecta odds 31,605/32,111.
- Wave19b Run 34749707037 failed due missing payout column and is superseded; never revert scope.

## Wave34 family
- Wave34c Run 34769751846: Apr-Jun 381R / 54 hits / ROI 86.794% / profit -503,130 yen; Apr 95.734 / May 74.626 / Jun 89.808. Current best Wave34-family pristine ROI.
- Wave34f diagnosis Run 34772303065: May hit rate did not collapse; relative motor strength was strongest diagnostic separator.
- Wave34g Run 34773416433: Apr-Jun 186R / 23 hits / ROI 68.726%; NO_ADOPTION.

## Wave34h March stability — FINAL
- Run 34773911115 success; artifact 10322927304.
- March selected b3_minus_b1_モーター2連対率 >= -0.0500, top3.
- March full 31R / ROI 215.332%; early 10R / 194.340%; late 21R / 225.329%; worst-half 194.340%.
- Apr-Jun pristine: 186R / 23 hits / ROI 68.726% / profit -581,700 yen.
- Monthly: Apr 40R / 4 hits / ROI 58.735% / -165,060; May 68R / 13 hits / ROI 97.506% / -16,960; Jun 78R / 6 hits / ROI 48.759% / -399,680.
- min month 48.759%; red months 3; max DD 790,460 yen.
- Jul-Aug shadow 270R / 39 hits / ROI 73.474% / -716,200 yen.
- combined v288 + holdout 280R / ROI 103.585% / +100,370 yen; overlap 0. NO_ADOPTION.
- Conclusion: even a gate strong in both March halves failed to generalize. Stop selecting motor gates by realized March ROI.

## Wave34i — NEXT / STARTED
- User requested continued automatic research.
- Change selection objective structurally: do NOT optimize realized March payout/ROI.
- Keep Wave34b prototype core and the same 63 static pre-deadline features, exact v288 exclusion and no September.
- Build a motor-strength confirmation score from the four predeclared relative-motor variables using February-only robust scaling. Candidate gates are fixed quantiles learned from February feature distribution, not from March payouts.
- Use February labels only to determine orientation/weight signs if needed; no closing odds in gate selection. March is validation only: require adequate support and improved 3-head hit rate / exact-order top-K hit coverage versus ungated prototype, with chronological early/late consistency. Rank by label-based stability, not monetary ROI.
- Freeze chosen gate after March validation; evaluate untouched Apr-Jun pristine with Dutch ROI. Jul/Aug shadow only.
- Report R/hits/ROI/profit/monthly/min month/red months/max DD/overlap/combined plus March validation hit-rate stability.

## Exact restart point
1. Implement Wave34i non-monetary structural motor confirmation.
2. Launch workflow and auto-fix technical failures without weakening guards.
3. Record exact result here after completion.
4. If NO_ADOPTION, continue distinct full-population research automatically.
