# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline: 94R / 52 hits / ROI 172.560638%.
- Research scope: all available six-boat races Feb-Aug 2026 minus exact v288 94R only.
- Jul/Aug NON-PRISTINE shadow only; September outcomes forbidden.
- Prediction uses exactly 63 static pre-deadline features. Closing odds are staking/evaluation only.
- Stake JPY10,000 per selected race with Dutch allocation; selected overlap with v288 must be zero.

## Stable source
- Wave20 Run 34749917116: success; full six-boat universe 32,111R. Monthly Feb 4100 / Mar 4607 / Apr 4244 / May 4832 / Jun 4488 / Jul 4920 / Aug 4920.
- Wave21 Run 34751314113: exact settlement usable 31,518/32,111.
- Wave22 Run 34752573368: full 120 closing trifecta odds 31,605/32,111.
- Wave19b Run 34749707037 failed due missing payout column and is superseded; never revert to old 584R/678R scope.

## Wave34 family
- Wave34: Apr-Jun ROI 84.243%.
- Wave34b: Apr-Jun ROI 85.449%.
- Wave34c Run 34769751846: Apr-Jun 381R / 54 hits / ROI 86.794% / profit -503,130 yen; Apr 95.734 / May 74.626 / Jun 89.808; combined v288 ROI 103.767% / +178,940 yen. NO_ADOPTION.

## Wave34d initial run — INVALID FOR INTENDED GROUP TEST
- True Wave34d Run 34770530725 succeeded technically; artifact 10322391192.
- Output: Apr-Jun 716R / 91 hits / ROI 81.303% / -1,338,740 yen; Apr 91.856 / May 67.655 / Jun 85.088; shadow 77.497%; combined 91.893%; overlap 0; NO_ADOPTION.
- However group diagnostics showed {'global':63,'nonslot':63}. The grouping regex failed to recognize the actual feature names, so boat-specific decomposition was not performed. Do not treat this as the intended Wave34d comparison.
- Actual 63 feature names from build_static are structured as: b3_<metric> (9), b3_minus_mean_<metric> (9), b3_minus_b1/b2_<metric> (18), b3_minus_b4/b5/b6_<metric> (27).

## Wave34d retry — NEXT
- Fix grouping deterministically using the actual prefixes above: boat3_abs=9, mean_advantage=9, inner12=18, outer456=27, plus global=63.
- Re-run identical Feb-train / March-select / Apr-Jun pristine / Jul-Aug shadow protocol. No Apr-Jun tuning.
- If the corrected grouped prototype test improves Wave34c 86.794%, continue this family; otherwise record NO_ADOPTION and move to the next distinct prototype refinement.

## Exact restart point
1. Patch research_v289_3head_wave34d_group_prototypes.py grouping only.
2. Trigger the existing Wave34d runner and inspect result automatically.
3. Record final corrected Wave34d metrics and update handoff.
