# v289 3号艇 add-on auto research — Wave 9 independent PRE head model

- v288 baseline **94R fixed / unchanged**
- target only final v288 NO_BET
- fresh boat3-win classifier trained on all prior-month buyable races; existing p3 excluded
- selected current feature missing => fail closed
- walk-forward Feb-Aug; July/August NON-PRISTINE; September outcomes not loaded

## Methods
| method | frac | add R | hits | hit rate | ROI | profit | min month ROI | red months | max DD | overlap | combined R | combined ROI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| head_ev | 0.15 | 37 | 7 | 18.92% | 57.26% | -158,130 | 0.00% | 5 | 167,870 | 0 | 131 | 140.00% |
| head_prob | 0.15 | 36 | 6 | 16.67% | 50.00% | -179,990 | 0.00% | 5 | 187,870 | 0 | 130 | 138.62% |
| head_ev | 0.25 | 60 | 9 | 15.00% | 45.22% | -328,700 | 0.00% | 5 | 347,840 | 0 | 154 | 122.95% |
| head_prob | 0.25 | 62 | 9 | 14.52% | 43.76% | -348,700 | 0.00% | 5 | 367,840 | 0 | 156 | 121.37% |
| head_prob | 0.40 | 81 | 11 | 13.58% | 40.86% | -479,000 | 17.30% | 5 | 479,000 | 0 | 175 | 111.60% |
| head_ev | 0.40 | 82 | 11 | 13.41% | 40.37% | -489,000 | 17.30% | 5 | 489,000 | 0 | 176 | 110.97% |

## Decision
**NO_ADOPTION_WAVE9**

Only robust historical passers may advance to September outcome-blind shadow; production v288 remains unchanged.
