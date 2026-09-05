# v125 v110 fixed7 opponent-pair miss diagnostics

- v109 head gate remains **p109>=72%**.
- v110 baseline remains **lambda=.50 / fixed top7**.
- This step is diagnostic only: no Sep result is used to tune a new ranking rule.

|period|S races|①head hits|head-hit fixed7 misses|miss rate among head hits|
|---|---:|---:|---:|---:|
|Jun-Aug v110 holdout|3308|2538|851|33.5%|
|Sep1-4 frozen PRE sample|18|14|4|28.6%|

## Miss decomposition
|period|both roles present / wrong pair|2nd role missing|3rd role missing|both roles missing|
|---|---:|---:|---:|---:|
|Jun-Aug v110 holdout|339|337|160|15|
|Sep1-4 frozen PRE sample|0|2|2|0|

## Next-step rule
- Do **not** change v109 or add another head filter from this analysis.
- If pair/order misses dominate, next validation should change only the 20-combination pair scoring / top7 construction.
- If role omissions dominate, improve second/third role features instead.
- Any new v110 rule must be selected on an earlier development block and evaluated once on a later untouched block; Sep outcomes stay confirmation-only.
