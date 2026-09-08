# v217 p3head .30-.35 x composite-odds temporal audit

- source: v216 annotated fixed v165->v166 lambda=1.00 / Top10 rows
- no PRE/model/threshold/lambda/points change
- Dec-2025..Jun-2026 is the only discovery/temporal-audit window
- Jul-Aug is already inspected and shown only as reference; it is not a validation set for any rule selected here
- stake: 10,000 yen/race Dutch settlement

## Dec-Jun month-by-month
|slice|R|hits|hit|avg_comp|ROI|profit|
|---|---:|---:|---:|---:|---:|---:|
|2025-12 all .30-.35|68|13|19.1%|6.230|80.9%|-129790|
|2025-12 comp>=3|44|6|13.6%|8.377|87.5%|-54990|
|2025-12 comp>=4|33|4|12.1%|10.018|98.3%|-5480|
|2025-12 comp>=5|24|3|12.5%|12.081|117.5%|+42040|
|2025-12 comp>=7|13|1|7.7%|17.279|123.8%|+30960|
|2026-01 all .30-.35|69|17|24.6%|5.371|67.3%|-225750|
|2026-01 comp>=3|30|6|20.0%|9.356|70.3%|-89010|
|2026-01 comp>=4|19|1|5.3%|12.855|26.7%|-139280|
|2026-01 comp>=5|16|1|6.2%|14.451|31.7%|-109280|
|2026-01 comp>=7|13|0|0.0%|16.514|0.0%|-130000|
|2026-02 all .30-.35|19|6|31.6%|7.798|111.2%|+21330|
|2026-02 comp>=3|8|1|12.5%|15.612|133.1%|+26480|
|2026-02 comp>=4|7|1|14.3%|17.313|152.1%|+36480|
|2026-02 comp>=5|6|1|16.7%|19.470|177.5%|+46480|
|2026-02 comp>=7|6|1|16.7%|19.470|177.5%|+46480|
|2026-03 all .30-.35|40|13|32.5%|4.089|67.5%|-129800|
|2026-03 comp>=3|13|1|7.7%|8.156|26.2%|-95920|
|2026-03 comp>=4|8|0|0.0%|11.089|0.0%|-80000|
|2026-03 comp>=5|6|0|0.0%|13.247|0.0%|-60000|
|2026-03 comp>=7|4|0|0.0%|16.935|0.0%|-40000|
|2026-04 all .30-.35|28|8|28.6%|5.654|62.5%|-105010|
|2026-04 comp>=3|14|1|7.1%|9.234|25.5%|-104360|
|2026-04 comp>=4|12|0|0.0%|10.259|0.0%|-120000|
|2026-04 comp>=5|11|0|0.0%|10.746|0.0%|-110000|
|2026-04 comp>=7|5|0|0.0%|16.606|0.0%|-50000|
|2026-05 all .30-.35|53|13|24.5%|3.919|66.2%|-178910|
|2026-05 comp>=3|23|4|17.4%|6.275|71.1%|-66480|
|2026-05 comp>=4|14|1|7.1%|8.073|47.0%|-74220|
|2026-05 comp>=5|11|1|9.1%|9.015|59.8%|-44220|
|2026-05 comp>=7|6|0|0.0%|11.669|0.0%|-60000|
|2026-06 all .30-.35|48|15|31.2%|3.184|72.1%|-133730|
|2026-06 comp>=3|16|2|12.5%|5.280|42.4%|-92150|
|2026-06 comp>=4|8|0|0.0%|7.066|0.0%|-80000|
|2026-06 comp>=5|5|0|0.0%|8.487|0.0%|-50000|
|2026-06 comp>=7|3|0|0.0%|9.881|0.0%|-30000|

## Chronological split inside pre-Jul history
|slice|R|hits|hit|avg_comp|ROI|profit|
|---|---:|---:|---:|---:|---:|---:|
|Dec-Feb discovery|156|36|23.1%|6.041|78.6%|-334210|
|Dec-Feb discovery comp>=3|82|13|15.9%|9.441|85.7%|-117520|
|Dec-Feb discovery comp>=4|59|6|10.2%|11.797|81.6%|-108280|
|Dec-Feb discovery comp>=5|46|5|10.9%|13.869|95.5%|-20760|
|Dec-Feb discovery comp>=7|32|2|6.2%|17.379|83.6%|-52560|
|Mar-Jun forward|169|49|29.0%|4.038|67.6%|-547450|
|Mar-Jun forward comp>=3|66|8|12.1%|7.032|45.6%|-358910|
|Mar-Jun forward comp>=4|42|1|2.4%|9.080|15.7%|-354220|
|Mar-Jun forward comp>=5|33|1|3.0%|10.281|19.9%|-264220|
|Mar-Jun forward comp>=7|18|0|0.0%|13.913|0.0%|-180000|

## Rolling prior-only threshold selection
|slice|R|hits|hit|avg_comp|ROI|profit|
|---|---:|---:|---:|---:|---:|---:|
|2026-01 chosen>=5|16|1|6.2%|14.451|31.7%|-109280|
|2026-02 chosen>=5|6|1|16.7%|19.470|177.5%|+46480|
|2026-03 chosen>=5|6|0|0.0%|13.247|0.0%|-60000|
|2026-04 chosen>=5|11|0|0.0%|10.746|0.0%|-110000|
|2026-05 chosen>=3|23|4|17.4%|6.275|71.1%|-66480|
|2026-06 chosen>=3|16|2|12.5%|5.280|42.4%|-92150|

- rolling aggregate: R=78, ROI=49.8%, profit=-391430 yen

## Jul-Aug reference only (NOT validation)
|slice|R|hits|hit|avg_comp|ROI|profit|
|---|---:|---:|---:|---:|---:|---:|
|Jul-Aug reference all .30-.35|123|37|30.1%|4.797|123.5%|+289090|
|Jul-Aug reference comp>=3|54|10|18.5%|8.013|159.9%|+323470|
|Jul-Aug reference comp>=4|40|7|17.5%|9.580|189.3%|+357210|
|Jul-Aug reference comp>=5|33|6|18.2%|10.665|216.9%|+385770|
|Jul-Aug reference comp>=7|23|4|17.4%|12.733|259.1%|+365990|

## Pre-Jul robustness summary
|slice|R|hits|hit|avg_comp|ROI|profit|
|---|---:|---:|---:|---:|---:|---:|
|comp>=3|148|21|14.2%|8.367|67.8%|-476430 (LOO worst 59.5%)|
|comp>=4|101|7|6.9%|10.667|54.2%|-462500 (LOO worst 32.8%)|
|comp>=5|79|6|7.6%|12.371|63.9%|-284980 (LOO worst 40.5%)|
|comp>=7|50|2|4.0%|16.131|53.5%|-232560 (LOO worst 28.8%)|

## Interpretation guardrails
- A threshold is not robust merely because aggregate ROI exceeds 100%; month-by-month and forward/rolling behavior must agree.
- Jul-Aug cannot be used as pristine validation because it has already been inspected repeatedly.
- This is a diagnostic audit only. No production rule is adopted automatically.
