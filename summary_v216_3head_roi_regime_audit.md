# v216 3-head ROI regime audit

- source: v215 fixed lambda=1.00 / Top10 per-race rows only
- no model, threshold, lambda, point-count, or PRE rule is changed
- comparison: Dec-2025..Jun-2026 vs Jul-Aug 2026
- stake: 10,000 yen/race Dutch settlement from v215 odds series


## Baseline
|period|R|hits|hit|avg_p3|avg_comp|ROI|profit|
|---|---:|---:|---:|---:|---:|---:|---:|
|Dec-Jun|486|138|28.40%|0.344|4.528|78.2%|-1060540|
|Jul-Aug|196|56|28.57%|0.347|4.470|103.7%|+72680|

## p3head band decomposition
|period|p3head|R|hit|avg_comp|ROI|profit|
|---|---:|---:|---:|---:|---:|---:|
|Dec-Jun|.30-.35|325|26.2%|4.999|72.9%|-881660|
|Dec-Jun|.35-.40|117|33.3%|3.585|94.0%|-70170|
|Dec-Jun|.40-.50|41|34.1%|3.625|80.8%|-78710|
|Dec-Jun|>=.50|3|0.0%|2.551|0.0%|-30000|
|Jul-Aug|.30-.35|123|30.1%|4.797|123.5%|+289090|
|Jul-Aug|.35-.40|54|25.9%|4.227|77.9%|-119560|
|Jul-Aug|.40-.50|17|29.4%|3.155|54.8%|-76850|
|Jul-Aug|>=.50|2|0.0%|2.046|0.0%|-20000|

## Composite-odds band decomposition
|period|comp|R|hit|ROI|profit|
|---|---:|---:|---:|---:|---:|
|Dec-Jun|<3|290|36.9%|77.2%|-661260|
|Dec-Jun|3-4|61|27.9%|90.7%|-56740|
|Dec-Jun|4-5|33|6.1%|26.3%|-243060|
|Dec-Jun|5-7|39|20.5%|121.5%|+83890|
|Dec-Jun|>=7|63|6.3%|70.9%|-183370|
|Jul-Aug|<3|118|36.4%|83.1%|-199230|
|Jul-Aug|3-4|22|22.7%|79.4%|-45310|
|Jul-Aug|4-5|10|10.0%|41.4%|-58560|
|Jul-Aug|5-7|12|16.7%|99.8%|-220|
|Jul-Aug|>=7|34|14.7%|210.6%|+376000|

## Largest-hit removal stress test
|period|drop_top_hits|R|ROI|profit|
|---|---:|---:|---:|---:|
|Dec-Jun|0|486|78.2%|-1060540|
|Dec-Jun|1|485|75.0%|-1211500|
|Dec-Jun|3|483|71.1%|-1394380|
|Dec-Jun|5|481|68.3%|-1526620|
|Dec-Jun|10|476|62.6%|-1779400|
|Jul-Aug|0|196|103.7%|+72680|
|Jul-Aug|1|195|89.9%|-196320|
|Jul-Aug|3|193|77.9%|-426020|
|Jul-Aug|5|191|68.9%|-593320|
|Jul-Aug|10|186|58.0%|-780410|

## Per-race gross-return cap stress test
|cap|period|ROI|profit|
|---|---:|---:|---:|
|20000|Dec-Jun|54.2%|-2225620|
|20000|Jul-Aug|55.6%|-869910|
|30000|Dec-Jun|65.2%|-1692060|
|30000|Jul-Aug|69.9%|-590030|
|50000|Dec-Jun|71.6%|-1381060|
|50000|Jul-Aug|78.8%|-415920|
|100000|Dec-Jun|76.8%|-1127980|
|100000|Jul-Aug|91.3%|-170600|
|200000|Dec-Jun|78.2%|-1060540|
|200000|Jul-Aug|99.7%|-6320|

## Gross-return concentration
|period|top_hits|gross_return_share|
|---|---:|---:|
|Dec-Jun|1|4.2%|
|Dec-Jun|3|9.6%|
|Dec-Jun|5|13.6%|
|Dec-Jun|10|21.6%|
|Jul-Aug|1|13.7%|
|Jul-Aug|3|26.0%|
|Jul-Aug|5|35.2%|
|Jul-Aug|10|46.9%|

## Jul-Aug largest winning races
|month|race_code|p3head|comp|actual|return|profit|
|---|---:|---:|---:|---:|---:|---:|
|2026-07|202607010608|0.302|26.703|3-5-4|279000|+269000|
|2026-08|202608112308|0.311|12.365|3-1-4|129690|+119690|
|2026-08|202608041902|0.353|12.204|3-6-1|120010|+110010|
|2026-08|202608210409|0.332|11.571|3-2-5|114580|+104580|
|2026-08|202608230402|0.346|7.448|3-2-5|72720|+62720|
|2026-07|202607110401|0.347|6.953|3-1-6|72600|+62600|
|2026-07|202607122206|0.325|5.048|3-4-1|47180|+37180|
|2026-07|202607300402|0.330|4.218|3-2-5|41440|+31440|
|2026-08|202608220303|0.348|3.869|3-1-5|39120|+29120|
|2026-08|202608160208|0.352|3.711|3-1-4|36750|+26750|
|2026-08|202608020803|0.301|3.592|3-5-1|36240|+26240|
|2026-08|202608030107|0.372|3.227|3-5-6|31680|+21680|
|2026-08|202608200406|0.321|3.088|3-5-2|30900|+20900|
|2026-07|202607091408|0.320|2.870|3-2-1|30800|+20800|
|2026-08|202608041008|0.310|2.981|3-1-6|29700|+19700|

## Interpretation rule
- A late-period ROI that collapses after removing only a few largest hits or under moderate return caps is payout-concentration evidence, not robust model improvement.
- Similar hit rates with materially different ROI and composite-odds mix indicates odds/payout regime is the main driver.
- This audit is diagnostic only; no production rule is adopted from these inspected periods.
