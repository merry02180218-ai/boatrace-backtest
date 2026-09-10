# v275 4-head opponent PLAYER blend

- v274 finding used: player history is strongest for 2nd; 3rd remains anchored to v96 unless Feb-Mar evidence supports a small player blend.
- Lambda chosen only on Feb-Mar 2026; Apr-Jun then held out from opponent-blend selection.
- Jul/Aug excluded; September not read; head selectors v268/v273 unchanged.
- No odds used in ranking or lambda selection.

## Feb-Mar lambda search

- v96 tune baseline: Top2 20.4%, Top4 42.6%, Top6 55.6%, Top10 79.6%.
- selected lambda2 (SECOND player blend): **0.30**
- selected lambda3 (THIRD player blend): **0.00**
- Selection objective weights Top2/Top4 most heavily and requires tune Top2 and Top4 not below v96.

## Holdout comparison

|scope|model|R|Top1|Top2|Top4|Top6|Top10|Top20|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|TUNE_ALL|V96|54|11.1%|20.4%|42.6%|55.6%|79.6%|100.0%|
|TUNE_ALL|PLAYER_BLEND|54|11.1%|24.1%|42.6%|53.7%|75.9%|100.0%|
|HOLD_ALL|V96|87|16.1%|26.4%|44.8%|56.3%|77.0%|100.0%|
|HOLD_ALL|PLAYER_BLEND|87|16.1%|27.6%|41.4%|57.5%|77.0%|100.0%|
|HOLD_SA|V96|40|15.0%|30.0%|45.0%|57.5%|77.5%|100.0%|
|HOLD_SA|PLAYER_BLEND|40|12.5%|30.0%|40.0%|60.0%|82.5%|100.0%|

## Apr-Jun month stability (S+A selected 4-head wins)

|month|model|R|Top2|Top4|Top6|Top10|
|---|---|---:|---:|---:|---:|---:|
|2026-04|V96|11|18.2%|36.4%|36.4%|54.5%|
|2026-04|PLAYER_BLEND|11|27.3%|36.4%|45.5%|63.6%|
|2026-05|V96|15|40.0%|53.3%|66.7%|86.7%|
|2026-05|PLAYER_BLEND|15|40.0%|46.7%|66.7%|86.7%|
|2026-06|V96|14|28.6%|42.9%|64.3%|85.7%|
|2026-06|PLAYER_BLEND|14|21.4%|35.7%|64.3%|92.9%|

## Decision
- S+A holdout delta: Top2 +0.0pt, Top4 -5.0pt, Top6 +2.5pt, Top10 +5.0pt.
- If small-N coverage improves or is preserved, next stage may test exact 10,000-yen Dutch ROI with this frozen blend candidate.
- If Top2/Top4 deteriorate, keep v96 and treat player-history features as informative diagnostics rather than a ranking replacement.
