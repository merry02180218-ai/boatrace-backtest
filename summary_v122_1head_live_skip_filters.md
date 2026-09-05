# v122 LIVE skip-filter validation

- Frozen operation: PRE top5/day from v121, then LIVE BUY gate inside that list only.
- Discovery/tuning: Mar-May. Clean evaluation: Jun-Aug.
- No odds; no post-race variable is used by the gate.
- Candidate gate family is deliberately simple: LIVE p109 minimum only.

## Mar-May discovery
|LIVE p109 min|BUY R/day|R|①頭率|7点的中率|7点ROI|
|---:|---:|---:|---:|---:|---:|
|72%|3.90|359|80.2%|55.7%|88.0%|
|74%|3.61|332|81.9%|57.5%|90.4%|
|76%|3.33|306|82.7%|59.2%|92.4%|
|78%|3.05|281|82.6%|59.1%|90.0%|
|80%|2.60|239|84.1%|61.5%|86.1%|
|82%|2.21|203|84.7%|63.5%|90.6%|
|84%|1.75|161|85.1%|63.4%|89.4%|
|86%|1.21|111|85.6%|63.1%|85.8%|

- Frozen selected gate from development block: **p109 >= 76%** (requires dev BUY >=2.5R/day).

## Clean Jun-Aug holdout
|rule|BUY R/day|R|①頭率|7点的中率|7点ROI|
|---|---:|---:|---:|---:|---:|
|v121 baseline p109>=72%|4.52|411|81.8%|56.2%|83.3%|
|v122 frozen p109>=76%|4.00|364|81.9%|57.7%|82.7%|

## Guardrail
- Do not adopt a stricter LIVE cut merely because it improves Mar-May. Adoption requires Jun-Aug improvement without collapsing race count, then prospective Sep confirmation.
- This v122 intentionally does not mine many exhibition subfeatures yet; first test whether the existing calibrated LIVE probability alone supplies a robust skip gate.
