# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline: 94R / 52 hits / ROI 172.560638%.
- FINAL scope: Wave20 full six-boat population Feb 1-Aug 31 2026; exclude exact v288 operational 94R only.
- Jul/Aug NON-PRISTINE shadow only; September outcomes forbidden.
- Prediction uses pre-deadline card information only. Settlement/closing odds evaluation/staking only.
- JPY10,000 per selected race, Dutch; v288 overlap must be zero.

## Stable source
- Wave20 Run 34749917116 success: 32,111R.
- Wave21 Run 34751314113: settlement usable 31,518R.
- Wave22 Run 34752573368: full 120 closing odds 31,605R.

## Wave36 shrinkage-LDA — RESEARCH CANDIDATE
- Run 34780059085; Apr-Jun 391R / 87 hits / ROI 114.913% / +583,090 yen.
- Apr 175.280%, May 103.005%, Jun 70.290%; Jul-Aug shadow 89.756%; overlap 0.

## Wave37 opponent/order research — COMPLETE
- Run 34782216334 success; artifact 10325149135.
- March conditional conversion: logit 63.158%, position 50.000%, ExtraTrees 34.211%.
- Apr-Jun 391R / 87 hits / ROI 114.913%; conditional conversion 54.375%.

## Wave38 opponent structural features — COMPLETE
- Run 34782510443 success; artifact 10325785027.
- Expanded 198-feature opponent set lost to static63 on March; no improvement. Apr-Jun remains 114.913%.

## Wave39V combined-odds variable ticket count — COMPLETE
- Run 34782837106 success; artifact 10325389748.
- March chose combined-odds floor 3.5.
- Apr-Jun variable K: 391R / 92 hits / ROI 103.009% / +117,670 yen; avg K 6.069; min month 67.066%; red months 2; overlap 0.
- Monthly: Apr 147.838%, May 96.587%, Jun 67.066%. Fixed Top5 remained better at 114.913%.
- Conclusion: uniform combined-odds floor expands tickets too broadly despite +5 hits.

## Wave39C confidence-aware variable ticket count — STARTED
- Freeze Wave36 head gate p3>=0.365448, chronology, and Wave37 static63 conditional-logit ticket ranking. Do not retune prediction models.
- Test confidence-aware K: high-confidence races use fewer tickets (target 3-5); lower-confidence races may expand toward 6-10 only when combined/effective Dutch odds remains acceptable.
- Confidence inputs must be model-derived pre-deadline quantities only (head p3 and/or ranked ticket probability concentration/margin). Historical closing odds may only determine staking/ticket-count feasibility, never prediction ranking.
- Predeclare a small grid of confidence cutoffs and K/floor mappings. Select rule using March only, prioritizing full/early/late ROI robustness and avoiding one-half collapse; Apr-Jun cannot tune rule.
- JPY10,000 Dutch per selected race, JPY100 units. Report Apr-Jun races/hits/ROI/profit/monthly/min month/red months/max DD/avg K/K distribution, fixed-Top5 comparison, and exact v288 overlap. Jul/Aug NON-PRISTINE shadow only; September forbidden.

## Exact restart point
1. Implement and launch Wave39C confidence-aware variable-K test.
2. Auto-fix technical failures without weakening guards.
3. On completion, update this handoff with exact Run/artifact/metrics before reporting.
4. If no pristine improvement over fixed Top5 114.913%, continue automatically to the next predeclared staking robustness idea without using Apr-Jun for tuning.
