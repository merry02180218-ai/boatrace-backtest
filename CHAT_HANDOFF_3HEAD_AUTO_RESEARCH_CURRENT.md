# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline 94R /52 hits / ROI172.560638%.
- Scope Feb-Aug 2026 full six-boat population; exclude exact v288 94R.
- Pre-deadline features only. Settlement/closing odds eval/staking only.
- JPY10,000 per selected race, Dutch. Jul/Aug NON-PRISTINE. September forbidden.

## Wave36 benchmark
- Run 34780059085: Apr-Jun 391R /87 hits / ROI114.913% / +583,090.

## Wave36S — RESEARCH_CANDIDATE
- Run 34785370650; artifact 10326411657.
- Apr-Jun 358R /81 hits / ROI116.938% / +606,380 / head41.341% / conversion54.730% / maxDD625,060.
- Monthly ROI Apr175.280 / May99.502 / Jun73.368 / Jul86.716 / Aug107.155.

## Wave36S-A audit — COMPLETE
- Run 34785891378 success; artifact 10326059528.
- Wave36S adds no races vs raw Wave36; it only removes races.
- Removed subsets: May20R ROI124.9% +49,800; Jun13R ROI43.777% -73,090; Jul24R ROI30.121% -167,710; Aug31R ROI61.784% -118,470.
- Apr-Jun removing largest win leaves ROI100.109%; removing top3 leaves86.201%.
- Apr-Jun halves: early179R ROI164.355% / +1,151,960 / head45.810% / conversion59.756%; late179R ROI69.521% / -545,580 / head36.872% / conversion48.485%.

## Wave36S-B descriptive diagnosis — COMPLETE
- Run 34786166134 success; Job 103801930864; artifact 10325708932; artifact SHA256 c7b39093ee91ae3ae73157b9fefe11405753e5763401952531c8621b617e5336.
- Rules unchanged; 63 features; v288 overlap0; September forbidden.
- Early vs late Apr-Jun confirms combined degradation: head rate 45.81% -> 36.87%, Top5 conversion 59.76% -> 48.48%, median positive return 38,160 -> 35,275 yen; ROI 164.36% -> 69.52%.
- Mean raw p3 barely moved: 0.45439 early vs 0.45291 late. Mean calibrated p3 only modestly fell: 0.52505 -> 0.50897. Therefore score level itself did not warn adequately about the regime change.
- Largest feature drifts were racer-strength relative gaps becoming more favorable to boat3 while realized performance worsened: b3-minus-mean national 2-rate effect +0.442 SD; national 3-rate +0.399; b3-vs4 national 3-rate +0.387; b3-vs2 local 2-rate +0.384; b3-vs2 national 2-rate +0.364.
- Motor signal moved the opposite way: b3-vs6 motor 2-rate -0.339 SD; b3 own motor 2-rate -0.324; b3-vs6 motor 3-rate -0.284; b3 own motor 3-rate -0.276. ST drift smaller; top ST effect b3-vs2 national avg ST -0.284 SD. Boat-number feature drift small.
- Family mean absolute drift: racer_strength 0.228 SD, motor 0.216, ST 0.114, boat 0.040.
- Raw p3 bands deteriorated broadly. Especially late p3 (0.5,0.6] = 27R / head33.33% / conversion22.22% / ROI32.05%, versus early 23R / head47.83% / conversion72.73% / ROI183.5%. Late p3>0.6 only 9R / head33.33% / ROI93.13%.
- Diagnosis: collapse is not just payout compression. It is primarily a combination of head-selection miscalibration and order-conversion failure, with some payout softening. The model increasingly over-trusted racer-strength advantages while motor quality weakened; p3 did not reflect that temporal mismatch.
- No production adoption. Do not derive a cutoff from Apr-Jun.

## Wave36S-C pre-April motor robustness modifier — STARTING
- Preserve Wave36S 63 static pre-deadline features, shrinkage-LDA head model, pooled rolling calibration, conditional-logit Top5, expanding chronology, JPY10,000 Dutch, exact v288 exclusion.
- Design/freeze the modifier using Feb/March evidence only. Apr-Jun outcomes/ROI must not choose its threshold or strength.
- Predeclared idea: construct racer-strength advantage and motor-strength advantage composites from existing static boat3 relative-gap features; penalize head confidence only in the mismatch regime where racer advantage is strong but motor advantage is weak.
- Candidate modifier settings may be compared only on March OOS head quality/stability; monetary ROI is not used to choose the rule. Freeze one setting before Apr-Jun evaluation.
- Evaluate frozen rule on Apr-Jun pristine and Jul/Aug NON-PRISTINE. Report selected R, head hits/rate, Top5 conversion, ROI/profit, monthly ROI, min month, red months, max DD, exact v288 overlap, and comparison with Wave36S/raw Wave36.
- No September data. No settlement or closing-odds feature enters prediction.

## Restart
Implement Wave36S-C, run CI, record exact Run/artifact/results here, then decide whether the pre-April motor robustness modifier improves pristine robustness without sacrificing aggregate edge.
