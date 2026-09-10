# v276 4-head direct pair feature audit

- Direct target: exact ordered opponent pair `(second, third)` conditional on historical boat-4 wins.
- Each evaluation month trains only on earlier races; Jul/Aug excluded; September not read.
- No odds in pair features/ranking; v268/v273 head selectors unchanged.
- v96 remains the baseline. This is retrospective feature research/model selection.

## Apr-Jun holdout-like comparison: all boat-4 wins

|family|R|features|T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|PAIR_BASE_PRIOR|87|61|12.6%|27.6%|39.1%|56.3%|77.0%|28.7%|44.8%|55.2%|75.9%|
|PAIR_PLAYER_SCENARIO|87|103|16.1%|27.6%|39.1%|50.6%|78.2%|28.7%|44.8%|55.2%|75.9%|
|PAIR_BASE|87|37|13.8%|26.4%|39.1%|56.3%|78.2%|28.7%|44.8%|55.2%|75.9%|
|PAIR_BASE_SCENARIO|87|88|13.8%|26.4%|39.1%|54.0%|77.0%|28.7%|44.8%|55.2%|75.9%|
|PAIR_PLAYER_PRIOR|87|76|12.6%|26.4%|39.1%|50.6%|78.2%|28.7%|44.8%|55.2%|75.9%|
|PAIR_BASE_PLAYER|87|52|17.2%|25.3%|37.9%|49.4%|81.6%|28.7%|44.8%|55.2%|75.9%|
|PAIR_ALL|87|127|13.8%|23.0%|40.2%|51.7%|78.2%|28.7%|44.8%|55.2%|75.9%|

## Frozen S+A selected boat-4 wins, Apr-Jun

|family|R|T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|ΔT2|ΔT4|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|PAIR_BASE_PRIOR|40|12.5%|25.0%|32.5%|47.5%|72.5%|35.0%|45.0%|57.5%|77.5%|-10.0pt|-12.5pt|
|PAIR_BASE|40|15.0%|25.0%|30.0%|52.5%|70.0%|35.0%|45.0%|57.5%|77.5%|-10.0pt|-15.0pt|
|PAIR_PLAYER_SCENARIO|40|15.0%|22.5%|35.0%|45.0%|72.5%|35.0%|45.0%|57.5%|77.5%|-12.5pt|-10.0pt|
|PAIR_PLAYER_PRIOR|40|15.0%|22.5%|35.0%|42.5%|72.5%|35.0%|45.0%|57.5%|77.5%|-12.5pt|-10.0pt|
|PAIR_BASE_PLAYER|40|17.5%|22.5%|30.0%|45.0%|77.5%|35.0%|45.0%|57.5%|77.5%|-12.5pt|-15.0pt|
|PAIR_BASE_SCENARIO|40|10.0%|20.0%|32.5%|52.5%|72.5%|35.0%|45.0%|57.5%|77.5%|-15.0pt|-12.5pt|
|PAIR_ALL|40|15.0%|20.0%|32.5%|42.5%|72.5%|35.0%|45.0%|57.5%|77.5%|-15.0pt|-12.5pt|

## Feature-family finding
- Best direct-pair family by small-N priority: **PAIR_BASE_PRIOR**.
- S+A delta vs v96: Top2 -10.0pt, Top4 -12.5pt, Top6 -10.0pt, Top10 -5.0pt.
- A direct-pair family is only a candidate if it improves the small-N region; broad Top10 gains alone are not enough.
- If no family beats v96 at Top2/Top4, retain v96 and use the discovered player-history variables only for diagnostics or narrowly conditioned tie-break research.
