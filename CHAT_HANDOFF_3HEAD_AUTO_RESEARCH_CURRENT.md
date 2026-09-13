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

## Wave36 shrinkage-LDA — RESEARCH CANDIDATE
- Run 34780059085 success; artifact 10324527230.
- March gate p3>=0.365448 top5 q=.98; 90R; head rate 42.222%; early 44.737%; late 40.385%.
- Apr-Jun pristine: 391R / 87 hits / ROI 114.913% / +583,090 yen.
- Apr 121R / 33 hits / ROI 175.280% / +910,890.
- May 145R / 33 hits / ROI 103.005% / +43,570.
- Jun 125R / 21 hits / ROI 70.290% / -371,370.
- min month 70.290%; red months 1; max DD 717,360 yen.
- Jul-Aug NON-PRISTINE shadow: 328R / 79 hits / ROI 89.756% / -335,990.
- baseline + holdout 485R / ROI 126.086% / +1,265,160. exact v288 overlap 0.

## Wave36L leak / temporal audit — PASS
- Run 34781494240 success; artifact 10325173171.
- 63 features verified; suspicious result/payout/odds/target-derived feature names: 0.
- Walk-forward causality PASS for Mar through Aug: every training max date strictly before test min date; Jul/Aug frozen training <= Jun 30.
- Shuffled-label Feb->Mar negative-control AUC 0.506287, consistent with chance.
- Head-rate diagnostic at fixed Wave36 p3 gate: Apr 44.628%, May 40.690%, Jun 37.600%, Jul 38.312%, Aug 43.103%. This is not monotonic time decay; no clear future-information leakage found.
- Wave36 remains RESEARCH_CANDIDATE; proceed to payout/order decomposition before promotion.

## Wave36R robustness decomposition — STARTED
- Do not tune or alter Wave36 gate. Reproduce exact p3>=0.365448/top5 walk-forward selection and Dutch settlement.
- For Apr/May/Jun and Jul/Aug, split chronologically early/late and report selected R, 3-head hits/rate, top5 ticket hits/rate, ROI/profit, mean/median winning payout, top1/top3 payout concentration.
- Decompose misses into (A) 3-head miss and (B) 3-head correct but exact-order top5 miss, so June weakness can be attributed to head gate vs opponent/order model.
- Quantify April outlier sensitivity by recomputing ROI after removing largest 1, 3, and 5 winning returns; diagnostics only, never threshold tuning.
- Keep Jul/Aug NON-PRISTINE and September forbidden. No adoption change until this diagnostic completes.

## Exact restart point
1. Implement and run Wave36R fixed-gate decomposition.
2. Record whether April profitability is broad or payout-concentrated and whether June weakness is head-gate or order-model driven.
3. If robustness remains credible, continue pre-April-only robustness confirmation; otherwise downgrade Wave36 candidate without using Jul/Aug for tuning.
