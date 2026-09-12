# v310 opponent headrisk result

## Status
- CI run 34696379838: SUCCESS.
- Frozen cohort unchanged: 345 races / 290 boat-1 head wins.
- THIRD frozen to v300 conditional THIRD L2=.1.
- p3/p4 are causal monthly walk-forward signals; sparse coverage uses zero sentinel + availability flags; no future backfill.

## Result
Baseline:
- SECOND TOP2: 71.72%
- exact3: 132/345 = 38.26%

Best v310: HEADRISK_L2_3
- SECOND TOP1: 44.48%
- SECOND TOP2: 72.07% (+0.34pp)
- SECOND TOP3: 86.90%
- exact3: 133/345 = 38.55% (+0.29pp)

By actual SECOND:
- boat2 TOP2 98.25%
- boat3 TOP2 84.27%
- boat4 TOP2 38.10% (baseline 35.71%; slight improvement)
- boat5 TOP2 18.75% (no material improvement)
- boat6 TOP2 0.00% (no improvement)

Monthly best v310:
- Feb TOP2 72.55%, exact3 36.51%
- Mar TOP2 60.00%, exact3 43.75%
- Apr TOP2 79.17%, exact3 52.83%
- May TOP2 75.25%, exact3 38.02%
- Jun TOP2 65.33%, exact3 31.52%

## Interpretation
- Causal 3-head/4-head probabilities provide only a small SECOND gain.
- They slightly help boat4 but do not solve outer boats 5/6.
- Therefore p3/p4 should be treated as auxiliary context, not the primary solution for SECOND.
- Main bottleneck remains outer-SECOND recovery.

## Next auto-research
v311 SECOND family auto-research is running as run 34696800597.
- fixed 345R / 290 head wins
- THIRD frozen
- family ablations/combinations over leak-safe PRE/prior features plus causal HEADRISK
- prioritize overall TOP2, worst-month TOP2, outer 4/5/6 TOP2, then exact3
- if no stable material gain, next step is route/gating or pairwise SECOND rather than more p3/p4 stacking
