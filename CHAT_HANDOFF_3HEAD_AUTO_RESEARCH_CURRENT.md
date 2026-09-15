# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch `research/3head-player-attack-mode`; production v288 unchanged 94R/52 hits/ROI172.560638%.
- Pre-deadline inputs only; exact v288 exclusion preserved. Jul/Aug NON-PRISTINE. September outcomes UNREAD.

## Reproducible base
- March eligible 4,482R; Wave54 210R/71 heads=33.8095%.
- February eligible 3,970R/478 boat3 heads.
- Current reproducible opponent baseline remains direct ordered-pair C=.25: March 25/71, ¥62,830, ROI99.7302%.

## Opponent v4 feature-family research — COMPLETE / REJECTED
### BEFORE
- `34def27b5c653aaa66280336a4f2ab225766fe56`.
### February GroupKFold(5), March unopened during selection
- baseline67: capture 38.4978%, AUC .696827.
- best eligible CV candidate = **no_local**, removing 当地勝率/当地2連対率 feature families: 55 features, capture **38.9101%**, AUC **.697839**.
- fold captures: 37.50%, 43.75%, 36.4583%, 35.7895%, 41.0526%; fold SD .03025, within predeclared concentration guard.
- no_pair_mean tied baseline capture 38.4978% but slightly lower AUC .696796.
- no_national_strength collapsed to 32.4276%; no_lane_structure collapsed to 24.4737%, showing national strength and lane/structure are important.
### Frozen-winner March one-shot
- no_local: Wave54 210R/71 heads; **23 hits=32.3944% capture**.
- ¥63,000 -> **¥56,350 / ROI89.4444%**.
- This is worse than baseline 25 hits / ROI99.7302%; therefore **REJECT no_local as successor** despite slight February-CV improvement.
- Ticket SHA256 `c8b2efd41a3feb2378ec38918225b77ffced0b75d0d31f28fb159b8d9c86a160`; second full execution identical.
- Executed local script SHA256 `296b8be435b81a1225904d5c99e5efa3befc32f048e35e9912e0f8760f3f9854`.
### GitHub
- v4 executable contract commit `b22f25966708ab648a5e5ccec0f537039183d271`.
- v4 result commit `a4ad90d2496802ebf95295d3bc244300f0adb52c`.
- No new Actions; source Run34754875342 / Artifact10317157868 reused.
### Conclusion
- Retain direct C=.25 baseline; v4 does not improve March.
- Do not remove local-strength family based on March and do not tune against March.
- Strong February ablation evidence: lane/structure and national-strength features are essential; motor/boat/gap families have smaller but nonzero ranking value.
- Next experiment should use a stronger February-only validation design (time-split/rolling February or January->February if source permits) before proposing another feature change, because tiny +0.41pp mean-CV gains did not transfer to March.
- September UNREAD; production unchanged.

## Exact restart point
- Build v5 validation-stability audit: evaluate the fixed baseline and a small set of predeclared feature candidates across chronological February splits (and January->February if valid), without opening additional post-March outcomes. Use stability, not single mean CV, to decide whether any successor deserves March diagnostic.
