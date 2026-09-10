# v277 4-head opponent Top4 player-history tiebreak

- Exact v96 Top4 pair membership is preserved; only ordering inside Top4 may change.
- Extra signal is SECOND-role BASE7_PLAYER score only; THIRD remains v96.
- Alpha selected on Feb-Mar only; Apr-Jun not used for alpha selection.
- Jul/Aug excluded; September not read; no odds used.
- v268/v273 head selectors unchanged.

## Feb-Mar alpha choice

- chosen alpha: **1.00**
|alpha|R|Top1|Top2|Top3|Top4|objective|
|---:|---:|---:|---:|---:|---:|---:|
|0.00|54|11.1%|20.4%|33.3%|42.6%|19.35|
|0.05|54|13.0%|20.4%|33.3%|42.6%|19.81|
|0.10|54|14.8%|20.4%|33.3%|42.6%|20.28|
|0.15|54|13.0%|20.4%|31.5%|42.6%|19.63|
|0.20|54|11.1%|20.4%|29.6%|42.6%|18.98|
|0.25|54|11.1%|20.4%|31.5%|42.6%|19.17|
|0.30|54|11.1%|20.4%|31.5%|42.6%|19.17|
|0.40|54|11.1%|20.4%|31.5%|42.6%|19.17|
|0.50|54|13.0%|24.1%|31.5%|42.6%|22.04|
|0.75|54|13.0%|22.2%|31.5%|42.6%|20.83|
|1.00|54|13.0%|25.9%|31.5%|42.6%|23.24|

## Apr-Jun comparison

|scope|model|R|Top1|Top2|Top3|Top4|Top6|Top10|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|HOLD_ALL|V96|87|16.1%|26.4%|33.3%|44.8%|56.3%|77.0%|
|HOLD_ALL|TOP4_PLAYER_TB|87|16.1%|31.0%|37.9%|44.8%|56.3%|77.0%|
|HOLD_SA|V96|40|15.0%|30.0%|37.5%|45.0%|57.5%|77.5%|
|HOLD_SA|TOP4_PLAYER_TB|40|12.5%|30.0%|35.0%|45.0%|57.5%|77.5%|

## S+A monthly stability

|month|model|R|Top1|Top2|Top4|Top6|Top10|
|---|---|---:|---:|---:|---:|---:|---:|
|2026-04|V96|11|0.0%|18.2%|36.4%|36.4%|54.5%|
|2026-04|TOP4_PLAYER_TB|11|0.0%|27.3%|36.4%|36.4%|54.5%|
|2026-05|V96|15|26.7%|40.0%|53.3%|66.7%|86.7%|
|2026-05|TOP4_PLAYER_TB|15|20.0%|33.3%|53.3%|66.7%|86.7%|
|2026-06|V96|14|14.3%|28.6%|42.9%|64.3%|85.7%|
|2026-06|TOP4_PLAYER_TB|14|14.3%|28.6%|42.9%|64.3%|85.7%|

## Decision
- S+A delta: Top1 -2.5pt, Top2 +0.0pt, Top3 -2.5pt.
- Top4/Top6/Top10 are intentionally preserved by construction.
- Only if Top2 improves without unstable month behavior should this proceed to an exact new-ROI ticket-order test. Otherwise retain pure v96.
