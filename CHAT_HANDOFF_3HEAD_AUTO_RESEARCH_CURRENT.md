# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch `research/3head-player-attack-mode`; production v288 unchanged 94R/52 hits/ROI172.560638%.
- Pre-deadline inputs only; exact v288 exclusion preserved. Jul/Aug NON-PRISTINE. September outcomes UNREAD.

## Reproducible base
- March eligible 4,482R; Wave54 210R/71 heads=33.8095%.
- February eligible 3,970R/478 boat3 heads.
- Current reproducible opponent baseline remains direct ordered-pair C=.25: March 25/71, ¥62,830, ROI99.7302%.

## BEFORE WORK — BoatraceCSV/fun-site 50% head-rate rebuild (2026-09-17)
- User goal changed priority: first raise 3号艇 head probability to at least 50%, then revisit opponent/ticket optimization.
- Use public `BoatraceCSV/fun-site` / BoatraceCSV CSV schema as an additional feature source. Documented pre-deadline families include race_cards, recent_national/local, waku10, motor_stats, estimate/motor_pt, estimate/racer_st; post-exhibition families previews/stt, tkz, sui, original_exhibition are reserved for a separate final layer and must not leak into PRE extraction.
- Start from the reproducible March eligible universe with exact v288 94R exclusion. Wave54 210R/71=33.81% remains a comparison anchor, not a population-size constraint.
- Research target: find PRE rules/model regions with >=50% boat3-head rate while maximizing retained race count. Report the full Pareto frontier (race count vs head rate), not only one cherry-picked threshold.
- Training/selection must be February-only or earlier-history-derived. Freeze thresholds/model before March settlement. March is one diagnostic only. Never tune on March labels after seeing them.
- Candidate feature families to audit: boat3 own national/local form and ST, boat3-vs-inner relative strength, waku10 same-frame performance/ST/start-order, motor2/3 and motor residual/pt summaries, estimated ST and uncertainty, inner wall weakness (1/2), F/L and session form. No realized finish/kimarite/payout as inputs.
- Evaluate at minimum PRE-only target bands >=50%, >=45%, >=40% with race counts, hits, chronological halves, venue dispersion, and overlap/increment vs Wave54. Prefer >=50% with useful volume; if 50% is only achievable at tiny N, state that and keep the best volume/precision frontier instead of forcing adoption.
- After PRE freeze, optional second-stage post-exhibition final filter may use stt/tkz/sui/original_exhibition causally; keep PRE and final metrics separate.
- September outcomes remain UNREAD. Jul/Aug remain NON-PRISTINE. Production unchanged.

## Exact restart point
- Inspect fun-site/BoatraceCSV field availability and historical HTTP paths; implement a February-trained PRE head-probability rebuild using the new feature families; freeze; run one March diagnostic; record exact Run/Job/Artifact/commit and Pareto frontier here.
