# v286 pre-result variable-N / exact 10k Dutch

- **No outcome/odds tuning of N.** Feb-Mar S+A/A-score rows do not exist, so the failed supervised-tune design was discarded.
- Calibration domain: Feb-Mar broad head candidates PRE>=.18 and POST>=.18.
- Metric: SECOND PLAYER_START/L2=10 normalized probability concentration = 1 - entropy/log(5).
- Thresholds are calibration-distribution quartiles only; results and odds are not used.
- Rule: >=Q75 N4; >=Q50 N6; >=Q25 N8; otherwise N10.
- Apr-Jun frozen S+A is the first economic evaluation of this N rule.
- v283 and v284 are reported separately; Apr-Jun is not used here to tune/select between them.
- Every BET race costs exactly 10,000 yen; boat-4 loss => payout 0.
- Archived odds are retrospective settlement proxy only, not formal prospective OOS.
- Jul/Aug excluded; September not read; v96 is not used for ranking/N selection.

## Pre-Apr frozen N rule

- calibration races: **75**
- Q25/Q50/Q75: **0.062173 / 0.131203 / 0.193914**

## Apr-Jun S+A economics

|scope|policy|R|avg N|N4/N6/N8/N10|4-head wins|hits|return|profit|ROI|
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
|A|FIXED_v283_N4|47|4.00|47/0/0/0|21|9|736770|+266770|156.76%|
|A|FIXED_v284_N10|47|10.00|0/0/0/47|21|18|655760|+185760|139.52%|
|A|VARIABLE_v283|47|6.43|17/8/17/5|21|12|513560|+43560|109.27%|
|A|VARIABLE_v284|47|6.43|17/8/17/5|21|13|605120|+135120|128.75%|
|S|FIXED_v283_N4|53|4.00|53/0/0/0|19|9|524440|-5560|98.95%|
|S|FIXED_v284_N10|53|10.00|0/0/0/53|19|12|394130|-135870|74.36%|
|S|VARIABLE_v283|53|6.23|19/15/13/6|19|10|403820|-126180|76.19%|
|S|VARIABLE_v284|53|6.23|19/15/13/6|19|10|404470|-125530|76.32%|
|S+A|FIXED_v283_N4|100|4.00|100/0/0/0|40|18|1261210|+261210|126.12%|
|S+A|FIXED_v284_N10|100|10.00|0/0/0/100|40|30|1049890|+49890|104.99%|
|S+A|VARIABLE_v283|100|6.32|36/23/30/11|40|22|917380|-82620|91.74%|
|S+A|VARIABLE_v284|100|6.32|36/23/30/11|40|23|1009590|+9590|100.96%|

## Apr-Jun monthly S+A

|policy|month|R|avg N|N4/N6/N8/N10|hits|profit|ROI|
|---|---|---:|---:|---|---:|---:|---:|
|FIXED_v283_N4|2026-04|31|4.00|31/0/0/0|6|+267460|186.28%|
|FIXED_v283_N4|2026-05|34|4.00|34/0/0/0|8|+62180|118.29%|
|FIXED_v283_N4|2026-06|35|4.00|35/0/0/0|4|-68430|80.45%|
|FIXED_v284_N10|2026-04|31|10.00|0/0/0/31|8|+31390|110.13%|
|FIXED_v284_N10|2026-05|34|10.00|0/0/0/34|12|+12790|103.76%|
|FIXED_v284_N10|2026-06|35|10.00|0/0/0/35|10|+5710|101.63%|
|VARIABLE_v283|2026-04|31|6.84|6/10/11/4|7|+24910|108.04%|
|VARIABLE_v283|2026-05|34|6.24|13/8/9/4|9|-23270|93.16%|
|VARIABLE_v283|2026-06|35|5.94|17/5/10/3|6|-84260|75.93%|
|VARIABLE_v284|2026-04|31|6.84|6/10/11/4|6|+2080|100.67%|
|VARIABLE_v284|2026-05|34|6.24|13/8/9/4|10|+12200|103.59%|
|VARIABLE_v284|2026-06|35|5.94|17/5/10/3|7|-4690|98.66%|

## Interpretation

- This is a cleaner test of variable N than optimizing thresholds on Apr-Jun, because the N thresholds were frozen without any Apr-Jun result or odds.
- Do not choose between v283 and v284 as a formal OOS winner from the same Apr-Jun comparison; treat both as development candidates for prospective/live validation.
