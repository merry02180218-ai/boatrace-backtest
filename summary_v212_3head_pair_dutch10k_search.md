# v212 3-head opponent ranking under new Dutch10k ROI — SHADOW

- gate: exact monthly-WF v165 p3head>=.30; pair model trains only on earlier dates.
- ranking search: lambda {0,.25,.5,.75,1.0} x N {5..12}.
- July selects one rule by realized ¥10,000 Dutch ROI; same lambda/N frozen for August.
- odds never rank tickets; they are settlement-only after ticket set is frozen.
- unified odds: od3 preferred, corrected official closing fallback.

## July discovery top rules
|rank|lambda|N|R|hit|avg comp|ROI|
|---:|---:|---:|---:|---:|---:|---:|
|1|0.75|5|87|19.5%|6.660|**113.3%**|
|2|1.00|6|87|21.8%|5.884|**107.0%**|
|3|1.00|7|87|21.8%|5.334|**103.0%**|
|4|0.25|11|87|29.9%|4.229|**102.9%**|
|5|0.75|7|87|21.8%|5.300|**101.9%**|
|6|0.75|6|87|19.5%|5.879|**101.8%**|
|7|0.50|10|87|28.7%|4.375|**101.5%**|
|8|0.50|9|87|26.4%|4.619|**99.6%**|
|9|0.50|11|87|28.7%|4.171|**99.4%**|
|10|1.00|8|87|23.0%|4.905|**98.8%**|
|11|1.00|10|87|26.4%|4.327|**98.7%**|
|12|0.50|5|87|18.4%|6.841|**98.6%**|

July selected: **lambda=0.75, N=5**

## Frozen August comparison
|rule|R|hit|avg comp|return|ROI|
|---|---:|---:|---:|---:|---:|
|v166 current lambda1 Top10 (1.00,N10)|109|30.3%|4.584|¥1,173,880|**107.7%**|
|July-selected (0.75,N5)|109|20.2%|7.300|¥1,207,960|**110.8%**|
|lambda1 same N (1.00,N5)|109|20.2%|7.260|¥1,171,900|**107.5%**|
|selected lambda Top10 (0.75,N10)|109|32.1%|4.630|¥1,209,900|**111.0%**|

## Decision
- This is discovery/shadow, not adoption evidence; August has already been inspected.
- Production v166 lambda=1.00 Top10 remains unchanged until prospective validation.
