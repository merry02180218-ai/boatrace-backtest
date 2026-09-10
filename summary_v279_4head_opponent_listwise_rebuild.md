# v279 independent 4-head opponent listwise rebuild

- **No v96 score/rank/order is used in training, features, candidate membership, blending, or tiebreaking.**
- Separate SECOND/THIRD listwise-softmax rankers choose among all five opponents.
- Pair ranking is `P(second=s) * P(third=t)` with `s != t`.
- Features: primitive ability/course, frozen player history, frozen prior exhibition/ST, current exhibition components, and race-relative transforms.
- Family/L2 choice uses Feb-Mar only. Apr-Jun is holdout-like model-choice evaluation.
- Jul/Aug excluded; September not read; no odds. v96 appears only as a post-freeze benchmark.

## Feb-Mar model choice

- chosen family: **PLAYER_START**
- chosen L2: **0.3**
- tune objective: **39.81**
- average features: **25**

### Top tune configurations

|family|L2|R|T2|T4|T6|T10|objective|
|---|---:|---:|---:|---:|---:|---:|---:|
|PLAYER_START|0.3|54|25.9%|44.4%|51.9%|70.4%|39.81|
|PLAYER_START|1|54|25.9%|44.4%|51.9%|68.5%|39.63|
|CORE|1|54|24.1%|42.6%|55.6%|72.2%|39.17|
|CORE|3|54|24.1%|42.6%|55.6%|72.2%|39.17|
|PLAYER_START|3|54|25.9%|40.7%|53.7%|68.5%|38.80|
|PLAYER|10|54|25.9%|42.6%|48.1%|68.5%|38.52|
|CORE|0.3|54|22.2%|42.6%|55.6%|72.2%|38.33|
|PLAYER_START|10|54|25.9%|40.7%|48.1%|70.4%|38.15|
|CORE|10|54|24.1%|37.0%|55.6%|72.2%|37.50|
|PLAYER|0.3|54|22.2%|42.6%|51.9%|68.5%|37.41|

## Apr-Jun holdout-like result

|scope|R|2nd T1|2nd T2|3rd T1|3rd T2|Pair T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|ALL 4-head wins|87|41.4%|62.1%|26.4%|48.3%|19.5%|31.0%|40.2%|49.4%|71.3%|28.7%|44.8%|55.2%|75.9%|
|Frozen S+A head-wins|40|35.0%|55.0%|27.5%|42.5%|20.0%|25.0%|35.0%|42.5%|65.0%|35.0%|45.0%|57.5%|77.5%|

## Apr-Jun monthly stability (S+A)

|month|R|T2|T4|T6|T10|v96 T2|T4|T6|T10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2026-04|11|36.4%|36.4%|36.4%|54.5%|27.3%|36.4%|36.4%|54.5%|
|2026-05|15|26.7%|33.3%|53.3%|93.3%|46.7%|53.3%|66.7%|86.7%|
|2026-06|14|14.3%|35.7%|35.7%|42.9%|28.6%|42.9%|64.3%|85.7%|

## Decision rule
- This is the first genuinely independent opponent rebuild. Do not force adoption merely because it is new.
- If Apr-Jun S+A small-N coverage (especially Top2/Top4) is competitive and month-stable, the next step is exact 10,000-yen Dutch/composite-odds economics using this frozen order.
- If it is weak, use v279 diagnostics to refine role-specific features/model class while staying independent of v96; do not fall back to v96 as a feature.
