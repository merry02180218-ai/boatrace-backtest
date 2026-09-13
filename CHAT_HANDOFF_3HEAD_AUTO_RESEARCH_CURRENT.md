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
- Wave19b failed and is superseded; never revert to old 584R/678R scope.

## Wave34 family
- Wave34 ROI 84.243%.
- Wave34b ROI 85.449%.
- Wave34c Run 34769751846: Apr-Jun 381R / 54 hits / ROI 86.794% / profit -503,130 yen; Apr 95.734 / May 74.626 / Jun 89.808. Current best Wave34-family pristine ROI.
- Wave34d corrected Run 34770655705: Apr-Jun ROI 71.717%. NO_ADOPTION.
- Wave34e Run 34771060051: Apr-Jun 365R / 50 hits / ROI 81.640% / profit -670,130 yen. NO_ADOPTION.

## Wave34f diagnosis — FINAL
- Run 34772303065 success; artifact 10322665846.
- Fixed Wave34b/c gate diagnostic: mean>=0.233221, agreement>=0.55, top3.
- Monthly reproduction: Apr 107R / 15 hits / ROI 94.839%; May 118R / 17 hits / ROI 73.993%; Jun 162R / 22 hits / ROI 87.591%.
- Prototype-level distributions are NOT the main cause: Apr/May/Jun prototype mean 0.2534/0.2519/0.2554, agreement all 1.000, hit rates 0.140/0.144/0.136. May does not collapse in hit rate; payout/selection quality is weaker.
- Largest May-vs-Apr+Jun pre-deadline shifts include: b3_全国平均ST lower/faster (0.140 vs 0.150), b3_全国勝率 higher (7.00 vs 6.75), stronger b3-vs-b2/b4 national win-rate/2-ren advantages, but weaker b3-vs-b5 local 2-ren advantage.
- Largest May hit-vs-miss diagnostic separators concentrate on relative motor strength and some local-strength gaps: b3_minus_b1_モーター2連対率, b3_minus_mean_モーター2連対率, b3_minus_b1_モーター3連対率, b3_minus_b2_モーター2連対率, plus b3-vs-b2/b5 local/national strength. These are diagnostic-only and MUST NOT be thresholded from May.

## NEXT: Wave34g pre-April hypothesis
- Hypothesis: Wave34 prototype head signal needs an independent pre-deadline relative-motor-strength confirmation to avoid low-quality 3-head selections. This is motivated by diagnosis, but thresholds must be selected using Feb/March only.
- Build a very small confirmation family from existing 63 features only: relative motor 2-ren and 3-ren strength versus inner boats / field mean, optionally combined with the existing prototype mean gate.
- Feb trains prototype. March alone selects confirmation thresholds and ticket count from a small predeclared grid with race-count floor. Apr-Jun remains untouched pristine. Jul/Aug shadow only.
- Do NOT use May labels to set thresholds or choose feature cut values.

## Exact restart point
1. Implement Wave34g relative-motor confirmation using only existing static features and March-only selection.
2. Run Apr-Jun untouched and compare directly to Wave34c 86.794% / May 74.626%.
3. Record final metrics and continue only if materially improved.
