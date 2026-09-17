# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- v288 production unchanged; baseline 94R / 52 hits / payout 1,622,070 yen.
- July/August NON-PRISTINE. September outcomes remain UNREAD.
- Pre-deadline inputs only for the head-probability rebuild.

## BEFORE WORK — fun-site 3号艇頭率50% rebuild (2026-09-17)
- Probe Run 35234503567 / Job 105246832483 completed SUCCESS; Artifact 10503470393.
- February availability confirmed: programs/race_cards 28/28 days (4,100 rows), programs/recent_national 28/28 (4,106), programs/recent_local 28/28 (4,106).
- February unavailable at probed historical paths: programs/waku10, programs/motor_stats, estimate/racer_st, estimate/motor_pt/motors. Do not assume these features exist for the Feb/Mar temporal validation.
- Build the actual PRE head model using available race_cards + recent_national/local, joined to the existing leak-audited settled universe/labels.
- Selection/training and threshold choice use February or earlier only. Freeze before reading March labels; March is one diagnostic only.
- Objective: maximize retained race count subject to useful head-rate precision. Report Pareto bands >=50%, >=45%, >=40%, chronological halves, venue dispersion, overlap/increment vs Wave54. Do not force >=50% if it only exists at tiny N.
- No realized finish/kimarite/payout is an input feature. Current-session history is allowed only when the referenced run is chronologically before the target race; otherwise exclude it.
- Production unchanged unless explicitly promoted by user.

## Exact restart point
- Implement model/backtest workflow on main, dispatch it, inspect result artifact, then append AFTER WORK with exact commit / Run / Job / Artifact / metrics / conclusion.
