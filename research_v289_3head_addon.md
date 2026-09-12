# v289 3号艇 add-on auto research — wave 1

- baseline: **v288 operational 94R fixed**
- target: only operational PRE S/A + buyable races where v288 final route is `NO_BET`
- test: 2026-02..2026-08 strict prior-month training
- July/August: **NON-PRISTINE**
- September outcomes used for tuning: **NO**

## Baseline
- 94R / 52 hits / ROI 172.561% / profit +682,070 yen

## Wave-1 methods

| method | target frac | add R | hits | add ROI | add profit | min month ROI | combined R | combined ROI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| return_rank | 45% | 84 | 15 | 54.92% | -378,700 | 21.07% | 178 | 117.04% |
| residual_hit | 45% | 80 | 13 | 48.66% | -410,720 | 21.07% | 174 | 115.59% |
| orthogonal_consensus | 45% | 83 | 12 | 43.92% | -465,460 | 19.67% | 177 | 112.24% |
| ev_calibrated | 45% | 85 | 12 | 43.45% | -480,680 | 21.07% | 179 | 111.25% |
| return_rank | 25% | 36 | 5 | 41.68% | -209,960 | 0.00% | 130 | 136.32% |
| attack_style_split | 45% | 84 | 11 | 40.55% | -499,370 | 0.00% | 178 | 110.26% |
| attack_style_split | 15% | 30 | 4 | 39.72% | -180,840 | 0.00% | 124 | 140.42% |
| exhibition_upgrade | 45% | 80 | 10 | 38.37% | -493,030 | 0.00% | 174 | 110.86% |
| orthogonal_consensus | 25% | 41 | 5 | 36.49% | -260,410 | 0.00% | 135 | 131.23% |
| attack_style_split | 25% | 45 | 5 | 33.56% | -299,000 | 0.00% | 139 | 127.56% |
| residual_hit | 25% | 39 | 4 | 30.87% | -269,600 | 0.00% | 133 | 131.01% |
| ev_calibrated | 25% | 39 | 4 | 30.87% | -269,600 | 0.00% | 133 | 131.01% |
| exhibition_upgrade | 25% | 39 | 4 | 30.22% | -272,150 | 0.00% | 133 | 130.82% |
| residual_hit | 15% | 25 | 2 | 23.69% | -190,770 | 0.00% | 119 | 141.29% |
| return_rank | 15% | 25 | 2 | 23.69% | -190,770 | 0.00% | 119 | 141.29% |
| ev_calibrated | 15% | 26 | 2 | 22.78% | -200,770 | 0.00% | 120 | 140.11% |
| orthogonal_consensus | 15% | 27 | 2 | 21.94% | -210,770 | 0.00% | 121 | 138.95% |
| exhibition_upgrade | 15% | 20 | 1 | 14.63% | -170,740 | 0.00% | 114 | 144.85% |

## Decision
**NO_ADOPTION_WAVE1**

Wave 1 is research/model-selection evidence only. A method is not production-adopted from this report alone.
Weak methods remain recorded so later research does not repeat dead ends.
