# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline: 94R / 52 hits / ROI 172.560638%.
- Research scope: all available six-boat races Feb-Aug 2026 minus exact v288 94R only.
- Jul/Aug NON-PRISTINE shadow only; September outcomes forbidden.
- Prediction uses exactly 63 static pre-deadline features. Closing odds are staking/evaluation only.
- Stake JPY10,000 per selected race with Dutch allocation; selected overlap with v288 must be zero.

## Wave34 family
- Wave34 Run 34768428513: Apr-Jun 386R / 53 hits / ROI 84.243%; Apr 96.157 / May 66.650 / Jun 90.880.
- Wave34b Run 34769342335: Apr-Jun 387R / 54 hits / ROI 85.449%; Apr 94.839 / May 73.993 / Jun 87.591.
- Wave34c Run 34769751846: success; artifact 3head-wave34c-loss-filter ID 10321796538.
- Wave34c March: 45R / 14 hits / ROI 189.300%. Loss-risk q=1.00, therefore loss filter was effectively non-binding.
- Wave34c Apr-Jun: 381R / 54 hits / ROI 86.794% / profit -503,130 yen.
- Wave34c monthly ROI: Apr 95.734 / May 74.626 / Jun 89.808. Combined v288 + holdout ROI 103.767%, profit +178,940 yen.
- Wave34 -> 34b -> 34c pristine ROI improved 84.243 -> 85.449 -> 86.794, so continue this family despite NO_ADOPTION.

## Wave34d — NEXT
- User requested continued research.
- Preserve prototype-distance family. Test feature-group prototype decomposition rather than another generic loss filter.
- Deterministically split the same 63 static features into boat-3 centered, inner boats 1/2, outer boats 4/5/6, and global/non-slot groups where possible.
- Compute positive-vs-negative prototype-distance score per group plus consensus/agreement across groups.
- Feb trains; March alone selects a fixed sparse gate and top-K. Apr-Jun remains untouched pristine evaluation. Jul-Aug shadow only.
- Goal: exceed Wave34c Apr-Jun ROI 86.794%, especially May 74.626%, without a trivial sample.

## Exact restart point
1. Implement and launch Wave34d feature-group prototype decomposition.
2. If failed, inspect logs and fix automatically without weakening guards.
3. Compare Wave34d directly against Wave34/34b/34c; adoption uses Apr-Jun only.
