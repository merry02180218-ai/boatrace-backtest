# v287 composite-odds variable N — independent 4-head opponents

- Target composite odds: **10.5**, inherited unchanged from frozen v268/v273 before September outcomes.
- For every BET race, opponent order is inferred first, then N is chosen from the odds row; result/payout is not used in N selection.
- Composite odds = 1 / sum(1/ticket_odds). Exact 10,000-yen inverse-odds Dutch, 100-yen Hamilton rounding.
- v283/v284 are independent opponent models; v96 is not used in ranking or N selection.
- Archived odds are retrospective proxy only, not immutable pre-deadline LIVE snapshots.
- Jul/Aug excluded; September outcomes not read.

- portfolio races: **100**
- odds-evaluable races: **100**
- missing odds rows: **0**

## Reinference verification vs v285

|model|fixed N|R|new return|v285 return|diff|new ROI|v285 ROI|
|---|---:|---:|---:|---:|---:|---:|---:|
|v283|4|100|1261210|1261210|+0|126.12%|126.12%|
|v284|10|100|1049890|1049890|+0|104.99%|104.99%|

## Apr-Jun S+A aggregate

|model|policy|R|avg N|N distribution|hits|avg comp|avg |comp-10.5||return|profit|ROI|
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
|v283|ODDS_2_10_T10.5|100|2.40|2:75,3:13,4:10,5:1,6:1|12|8.321|2.506|1033950|+33950|103.39%|
|v283|ODDS_2_20_T10.5|100|2.40|2:75,3:13,4:10,5:1,6:1|12|8.321|2.506|1033950|+33950|103.39%|
|v283|ODDS_4610_T10.5|100|4.04|4:98,6:2|18|5.818|4.725|1209100|+209100|120.91%|
|v284|ODDS_2_10_T10.5|100|2.48|2:69,3:19,4:9,5:1,6:2|11|8.361|2.392|939720|-60280|93.97%|
|v284|ODDS_2_20_T10.5|100|2.48|2:69,3:19,4:9,5:1,6:2|11|8.361|2.392|939720|-60280|93.97%|
|v284|ODDS_4610_T10.5|100|4.06|4:97,6:3|14|5.902|4.606|894320|-105680|89.43%|

## S / A separately

|scope|model|policy|R|avg N|hits|profit|ROI|
|---|---|---|---:|---:|---:|---:|---:|
|A|v283|ODDS_2_10_T10.5|47|2.62|6|+98140|120.88%|
|A|v283|ODDS_2_20_T10.5|47|2.62|6|+98140|120.88%|
|A|v283|ODDS_4610_T10.5|47|4.09|9|+214660|145.67%|
|A|v284|ODDS_2_10_T10.5|47|2.77|6|+58550|112.46%|
|A|v284|ODDS_2_20_T10.5|47|2.77|6|+58550|112.46%|
|A|v284|ODDS_4610_T10.5|47|4.13|7|+35550|107.56%|
|S|v283|ODDS_2_10_T10.5|53|2.21|6|-64190|87.89%|
|S|v283|ODDS_2_20_T10.5|53|2.21|6|-64190|87.89%|
|S|v283|ODDS_4610_T10.5|53|4.00|9|-5560|98.95%|
|S|v284|ODDS_2_10_T10.5|53|2.23|5|-118830|77.58%|
|S|v284|ODDS_2_20_T10.5|53|2.23|5|-118830|77.58%|
|S|v284|ODDS_4610_T10.5|53|4.00|7|-141230|73.35%|

## Monthly S+A

|month|model|policy|R|avg N|hits|avg comp|profit|ROI|
|---|---|---|---:|---:|---:|---:|---:|---:|
|2026-04|v283|ODDS_2_10_T10.5|31|2.45|5|9.184|+195690|163.13%|
|2026-05|v283|ODDS_2_10_T10.5|34|2.26|4|7.702|-49680|85.39%|
|2026-06|v283|ODDS_2_10_T10.5|35|2.49|3|8.158|-112060|67.98%|
|2026-04|v283|ODDS_2_20_T10.5|31|2.45|5|9.184|+195690|163.13%|
|2026-05|v283|ODDS_2_20_T10.5|34|2.26|4|7.702|-49680|85.39%|
|2026-06|v283|ODDS_2_20_T10.5|35|2.49|3|8.158|-112060|67.98%|
|2026-04|v283|ODDS_4610_T10.5|31|4.00|6|6.335|+267460|186.28%|
|2026-05|v283|ODDS_4610_T10.5|34|4.00|8|5.406|+62180|118.29%|
|2026-06|v283|ODDS_4610_T10.5|35|4.11|4|5.761|-120540|65.56%|
|2026-04|v284|ODDS_2_10_T10.5|31|2.58|2|9.281|-113980|63.23%|
|2026-05|v284|ODDS_2_10_T10.5|34|2.26|5|7.810|+66940|119.69%|
|2026-06|v284|ODDS_2_10_T10.5|35|2.60|4|8.081|-13240|96.22%|
|2026-04|v284|ODDS_2_20_T10.5|31|2.58|2|9.281|-113980|63.23%|
|2026-05|v284|ODDS_2_20_T10.5|34|2.26|5|7.810|+66940|119.69%|
|2026-06|v284|ODDS_2_20_T10.5|35|2.60|4|8.081|-13240|96.22%|
|2026-04|v284|ODDS_4610_T10.5|31|4.06|3|6.471|-41690|86.55%|
|2026-05|v284|ODDS_4610_T10.5|34|4.00|7|5.369|+41450|112.19%|
|2026-06|v284|ODDS_4610_T10.5|35|4.11|4|5.915|-105440|69.87%|

## Descriptive result

- Best of these frozen-target odds-variable policies: **v283 / ODDS_4610_T10.5 = ROI 120.91%**, avg N 4.04, profit +209100 yen.
- This uses archived historical odds to choose N and settle the same races, so it is development evidence only. For prospective use, N must be chosen from an immutable pre-deadline odds snapshot.
