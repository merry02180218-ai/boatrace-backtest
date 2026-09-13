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
- Wave34c Run 34769751846: Apr-Jun 381R / 54 hits / ROI 86.794% / profit -503,130 yen; Apr 95.734 / May 74.626 / Jun 89.808; combined v288 ROI 103.767% / +178,940 yen. NO_ADOPTION and current best Wave34-family pristine ROI.

## Wave34d corrected grouped prototypes — FINAL
- Run 34770655705 success; artifact 10321937503.
- Correct groups: global 63 / boat3_abs 9 / mean_advantage 9 / inner12 18 / outer456 27.
- March selected inner12 / consensus1 / top5: 135R / ROI 153.116%.
- Apr-Jun pristine: 764R / 118 hits / ROI 71.717% / profit -2,160,850 yen.
- Monthly: Apr 203R / ROI 76.787% / -471,220; May 284R / ROI 64.063% / -1,020,600; Jun 277R / ROI 75.847% / -669,030.
- min month 64.063%; red months 3; max DD 2,288,930 yen.
- Jul-Aug NON-PRISTINE shadow ROI 67.714%.
- combined v288 + holdout ROI 82.765% / profit -1,478,780 yen. overlap 0.
- Decision NO_ADOPTION. Group-specific March signal did not generalize; do not continue group decomposition.

## Wave34e — NEXT normalized prototype margin
- User requested continued research.
- Return to Wave34b/34c global 63-feature bootstrap prototype core; do not carry Wave34d group gate.
- Test scale-normalized prototype margin: (d_neg - d_pos) / (d_neg + d_pos + eps), retaining bootstrap mean/std/agreement. Compare against raw-margin baseline inside March only.
- Keep the conditional exact-order logistic model from Wave34b.
- Feb trains. March alone selects a small predeclared gate using normalized mean, agreement and optionally maximum bootstrap std; 30..300 March race floor. Apr-Jun untouched pristine. Jul-Aug frozen shadow only.
- Goal: improve Wave34c Apr-Jun ROI 86.794% and May 74.626% while preserving non-trivial race count.
- Same exact-v288-94 exclusion, 63 static features, no September, closing odds staking-only, JPY10k Dutch, overlap 0.

## Exact restart point
1. Implement Wave34e normalized-margin prototype stability research.
2. Trigger existing Wave34d workflow path as runner if a new workflow cannot be created.
3. If failed, fix automatically without weakening guards.
4. On success record R/hits/ROI/profit/monthly/min month/red months/max DD/overlap/combined and compare Wave34c vs Wave34e.
