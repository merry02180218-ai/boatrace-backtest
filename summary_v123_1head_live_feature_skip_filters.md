# v123 1-head LIVE exhibition-feature skip validation

- Frozen PRE operation: **v121 PRE top5/day**. No race is added after exhibition.
- Baseline LIVE BUY: v121 p109>=72% and boat1 course1.
- Discovery: Mar-May only. Clean one-shot evaluation: Jun-Aug.
- Candidate gates use only LIVE/exhibition features; no odds/result/payout in filtering.

## Baseline
|period|R|①頭率|7点的中率|7点ROI|
|---|---:|---:|---:|---:|
|Mar-May dev|359|80.2%|55.7%|88.0%|
|Jun-Aug holdout|411|81.8%|56.2%|83.3%|

## Development search top candidates
|feature|skip lower tail|threshold|R|①頭率|7点的中率|7点ROI|
|---|---:|---:|---:|---:|---:|---:|
|margin2|40%|0.12120|215|84.2%|60.9%|98.6%|
|ex_margin23|35%|-0.23500|233|83.3%|59.2%|97.5%|
|ex_margin23|40%|-0.20000|233|83.3%|59.2%|97.5%|
|margin23|30%|0.04667|251|83.3%|60.6%|97.5%|
|one_lap|35%|0.60000|249|82.7%|58.6%|96.2%|
|one_lap|40%|0.60000|249|82.7%|58.6%|96.2%|
|margin2|30%|0.08598|251|83.7%|59.8%|96.1%|
|margin2|20%|0.05571|287|83.6%|61.0%|95.5%|
|margin2|25%|0.06671|269|83.3%|60.2%|95.5%|
|one_orig_avg|40%|0.53333|216|83.3%|58.8%|95.4%|
|margin2|35%|0.10745|233|83.7%|60.1%|94.6%|
|one_lap|30%|0.50000|266|81.6%|57.9%|93.9%|
|one_orig_avg|20%|0.37333|287|81.5%|58.5%|93.6%|
|one_orig_avg|25%|0.40000|287|81.5%|58.5%|93.6%|
|margin23|35%|0.05933|233|84.1%|60.9%|93.5%|
|ex_margin23|25%|-0.40000|284|82.0%|57.4%|93.1%|
|ex_margin23|30%|-0.40000|284|82.0%|57.4%|93.1%|
|margin23|25%|0.02858|269|82.2%|58.7%|92.7%|
|one_direct|40%|0.49067|215|83.3%|57.7%|92.4%|
|margin3|20%|0.05100|287|81.2%|57.5%|92.3%|

## Frozen selected gate
- **Keep only ex_margin23 >= -0.23500** (development lower-tail skip 35%).
- Dev: 233R / ①頭 83.3% / hit 59.2% / ROI 97.5%.

## Clean Jun-Aug holdout result
|rule|R|①頭率|7点的中率|7点ROI|
|---|---:|---:|---:|---:|
|baseline|411|81.8%|56.2%|83.3%|
|v123 frozen gate|275|83.6%|58.2%|84.5%|

## Decision rule
- PASS only if Jun-Aug ROI improves AND hit rate does not worsen. Otherwise FAIL; do not adopt.
- **V123 = PASS**

## Guardrail
- This is still one-dimensional filtering to reduce overfit risk. If FAIL, do not start combinatorial feature mining on the same holdout. Move to prospective Sep validation or a new untouched time block.
