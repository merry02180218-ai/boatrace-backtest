# v289 3号艇 add-on auto research — Wave 5 true opponent re-ranking

- v288 baseline **94R fixed / unchanged**
- target: operational PRE S/A + v242-buyable + final v288 NO_BET only
- unlike Wave 2, this retrains the 2着/3着 ordered-pair ranking itself from prior-month reject races
- variants: residual pair probability / V221+residual blend / ticket-level residual probability×pre-race odds EV; each with target3 or Top10 Dutch
- July/August NON-PRISTINE; September outcomes not loaded

## Methods
| method | add R | hits | ROI | profit | min month ROI | red months | max DD | combined R | combined ROI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ev_target3 | 178 | 24 | 82.29% | -315,260 | 0.00% | 6 | 663,710 | 272 | 113.49% |
| ev_top10 | 178 | 24 | 82.29% | -315,260 | 0.00% | 6 | 663,710 | 272 | 113.49% |
| residual_top10 | 178 | 37 | 52.32% | -848,650 | 34.12% | 7 | 876,290 | 272 | 93.88% |
| blend_top10 | 178 | 40 | 52.19% | -851,070 | 27.48% | 7 | 870,790 | 272 | 93.79% |
| blend_target3 | 171 | 27 | 47.91% | -890,780 | 35.30% | 7 | 920,620 | 265 | 92.12% |
| residual_target3 | 178 | 27 | 46.88% | -945,480 | 30.87% | 7 | 973,120 | 272 | 90.32% |

## Decision
**NO_ADOPTION_WAVE5**

Historical passers can advance only to September outcome-blind shadow; v288 production is not replaced.
