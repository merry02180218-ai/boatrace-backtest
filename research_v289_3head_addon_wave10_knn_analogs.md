# v289 3号艇 add-on auto research — Wave 10 KNN analogs

- v288 baseline **94R fixed / unchanged**
- final v288 NO_BET only
- nonparametric nearest-neighbour analog models; existing p3 excluded
- current selected feature missing => fail closed
- walk-forward Feb-Aug; Jul/Aug NON-PRISTINE; September outcomes unused

## Methods
| method | frac | add R | hits | hit rate | ROI | profit | min month ROI | red | max DD | overlap | combined R | combined ROI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| knn_head_k25 | 0.40 | 166 | 23 | 13.86% | 42.31% | -957,580 | 30.87% | 7 | 976,180 | 0 | 260 | 89.40% |
| knn_consensus_k25 | 0.40 | 166 | 23 | 13.86% | 42.31% | -957,580 | 30.87% | 7 | 976,180 | 0 | 260 | 89.40% |
| knn_head_k50 | 0.40 | 171 | 23 | 13.45% | 41.08% | -1,007,580 | 30.87% | 7 | 1,026,180 | 0 | 265 | 87.72% |
| knn_consensus_k50 | 0.40 | 171 | 23 | 13.45% | 41.08% | -1,007,580 | 30.87% | 7 | 1,026,180 | 0 | 265 | 87.72% |
| knn_head_k75 | 0.40 | 172 | 23 | 13.37% | 40.84% | -1,017,580 | 30.87% | 7 | 1,036,180 | 0 | 266 | 87.39% |
| knn_consensus_k75 | 0.40 | 172 | 23 | 13.37% | 40.84% | -1,017,580 | 30.87% | 7 | 1,036,180 | 0 | 266 | 87.39% |
| knn_value_k25 | 0.25 | 176 | 23 | 13.07% | 39.91% | -1,057,580 | 30.58% | 7 | 1,076,180 | 0 | 270 | 86.09% |
| knn_value_k75 | 0.25 | 176 | 23 | 13.07% | 39.91% | -1,057,580 | 30.58% | 7 | 1,076,180 | 0 | 270 | 86.09% |
| knn_value_k50 | 0.25 | 177 | 23 | 12.99% | 39.68% | -1,067,580 | 30.58% | 7 | 1,086,180 | 0 | 271 | 85.77% |
| knn_value_k25 | 0.40 | 178 | 23 | 12.92% | 39.46% | -1,077,580 | 30.58% | 7 | 1,096,180 | 0 | 272 | 85.46% |
| knn_value_k50 | 0.40 | 178 | 23 | 12.92% | 39.46% | -1,077,580 | 30.58% | 7 | 1,096,180 | 0 | 272 | 85.46% |
| knn_value_k75 | 0.40 | 178 | 23 | 12.92% | 39.46% | -1,077,580 | 30.58% | 7 | 1,096,180 | 0 | 272 | 85.46% |
| knn_head_k25 | 0.15 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |
| knn_value_k25 | 0.15 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |
| knn_consensus_k25 | 0.15 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |
| knn_head_k25 | 0.25 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |
| knn_consensus_k25 | 0.25 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |
| knn_head_k50 | 0.15 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |
| knn_value_k50 | 0.15 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |
| knn_consensus_k50 | 0.15 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |
| knn_head_k50 | 0.25 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |
| knn_consensus_k50 | 0.25 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |
| knn_head_k75 | 0.15 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |
| knn_value_k75 | 0.15 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |
| knn_consensus_k75 | 0.15 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |
| knn_head_k75 | 0.25 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |
| knn_consensus_k75 | 0.25 | 0 | 0 | nan% | nan% | +0 | nan% | 0 | 0 | 0 | 94 | 172.56% |

## Decision
**NO_ADOPTION_WAVE10**

Only robust passers may advance to September outcome-blind shadow; v288 production remains unchanged.
