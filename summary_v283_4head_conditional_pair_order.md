# v283 conditional pair-order audit

- v282 model probabilities are frozen; no retraining here.
- No v96 signal enters ordering or selection; v96 is benchmark-only.
- Ordering mode/alpha/threshold selected on Feb-Mar only; Apr-Jun untouched.
- Jul/Aug excluded upstream; September not read; no odds.

## Frozen pair-order policy

- mode: **TOP2XTOP2**
- alpha2: **0.60**
- confidence threshold: **1.50**
- tune T2/T4/T6/T10: **27.8% / 40.7% / 57.4% / 75.9%**

### Top policy grid

|mode|alpha|thr|T1|T2|T4|T6|T10|objective|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|TOP2XTOP2|0.60|1.50|13.0%|27.8%|40.7%|57.4%|75.9%|37.37|
|TOP2XTOP2|0.65|1.50|13.0%|27.8%|40.7%|57.4%|74.1%|37.28|
|JOINT|0.65|1.50|13.0%|27.8%|40.7%|55.6%|74.1%|37.06|
|JOINT|0.60|1.50|13.0%|27.8%|38.9%|57.4%|75.9%|36.85|
|TOP2XTOP2|0.55|1.50|13.0%|27.8%|40.7%|53.7%|74.1%|36.83|
|TOP2XTOP2|0.50|1.50|13.0%|27.8%|40.7%|50.0%|77.8%|36.57|
|JOINT|0.70|1.50|13.0%|25.9%|40.7%|57.4%|72.2%|36.17|
|TOP2XTOP2|0.70|1.50|13.0%|25.9%|40.7%|57.4%|72.2%|36.17|
|CONF_HYBRID|0.70|1.30|13.0%|25.9%|40.7%|57.4%|72.2%|36.17|
|CONF_HYBRID|0.65|1.30|13.0%|25.9%|40.7%|55.6%|74.1%|36.04|
|TOP2XTOP2|0.75|1.50|13.0%|25.9%|40.7%|55.6%|72.2%|35.94|
|CONF_HYBRID|0.60|1.30|13.0%|25.9%|38.9%|57.4%|75.9%|35.83|
|JOINT|0.75|1.50|13.0%|25.9%|40.7%|53.7%|72.2%|35.72|
|CONF_HYBRID|0.75|1.30|13.0%|25.9%|40.7%|53.7%|72.2%|35.72|
|JOINT|0.55|1.50|13.0%|27.8%|35.2%|53.7%|74.1%|35.28|
|JOINT|0.50|1.50|13.0%|27.8%|35.2%|51.9%|77.8%|35.24|
|CONF_HYBRID|0.70|1.15|13.0%|24.1%|40.7%|57.4%|72.2%|35.15|
|CONF_HYBRID|0.70|1.50|13.0%|24.1%|40.7%|57.4%|72.2%|35.15|
|CONF_HYBRID|0.70|1.80|13.0%|24.1%|40.7%|57.4%|72.2%|35.15|
|CONF_HYBRID|0.65|1.15|13.0%|24.1%|40.7%|55.6%|74.1%|35.02|

## Apr-Jun holdout-like result

|scope|R|Pair T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|ALL 4-head wins|87|21.8%|34.5%|51.7%|59.8%|69.0%|28.7%|44.8%|55.2%|75.9%|
|Frozen S+A head-wins|40|12.5%|25.0%|45.0%|52.5%|65.0%|35.0%|45.0%|57.5%|77.5%|

## S+A monthly

|month|R|T2|T4|T6|T10|v96 T2|T4|T6|T10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2026-04|11|36.4%|54.5%|54.5%|63.6%|27.3%|36.4%|36.4%|54.5%|
|2026-05|15|26.7%|53.3%|53.3%|66.7%|46.7%|53.3%|66.7%|86.7%|
|2026-06|14|14.3%|28.6%|50.0%|64.3%|28.6%|42.9%|64.3%|85.7%|

## Decision
- Prefer the frozen structural policy only if Apr-Jun small-N coverage improves without a single-month collapse.
- If it fails, the remaining issue is regime-specific opponent behavior rather than generic pair ordering; proceed to pre-Apr-frozen inner-survival/outer-follow regime models.
