# v306 1HEAD unsafe meeting-feature attribution

- Development only; no unsafe feature is eligible for production adoption.
- Same frozen 204-race coverage as v303-v305. Jul/Aug NON-PRISTINE; September outcomes unread.

## One-at-a-time add-back
|config|feature|hits/R|rate|delta vs strict|worst month|
|---|---|---:|---:|---:|---:|
|ADD_01|`v303_turn_form_b1_minus_b2_meet_win`|182/204|89.22%|+6.86pt|76.47%|
|ADD_02|`v303_turn_form_b1_minus_b3_meet_win`|181/204|88.73%|+6.37pt|78.43%|
|ADD_06|`v303_turn_form_b1_minus_maxopp_meet_win`|181/204|88.73%|+6.37pt|68.63%|
|ADD_05|`v303_turn_form_b1_minus_b6_meet_win`|180/204|88.24%|+5.88pt|76.47%|
|ADD_03|`v303_turn_form_b1_minus_b4_meet_win`|175/204|85.78%|+3.43pt|66.67%|
|ADD_04|`v303_turn_form_b1_minus_b5_meet_win`|174/204|85.29%|+2.94pt|68.63%|
|ADD_08|`v303_stmotor_b1v3_meet_st_strength_motor`|169/204|82.84%|+0.49pt|78.38%|
|ADD_09|`v303_stmotor_b1v4_meet_st_strength_motor`|169/204|82.84%|+0.49pt|77.78%|
|ADD_07|`v303_stmotor_b1v2_meet_st_strength_motor`|167/204|81.86%|-0.49pt|79.31%|

- BASE: **166/204 = 81.37%**, worst month 78.38%.

- STRICT_SAFE: **168/204 = 82.35%**, worst month 72.22%.

- FULL_ALL9: **181/204 = 88.73%**, worst month 68.63%.

## Decision
- Largest single unsafe lift: `v303_turn_form_b1_minus_b2_meet_win` => **182/204 = 89.22%** (+6.86pt vs strict).
- Treat all nine meeting-snapshot features as contaminated until a causal prior-race-only reconstruction reproduces the signal.
