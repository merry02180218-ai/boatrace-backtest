# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy / non-negotiables
- Active branch: `research/3head-player-attack-mode`. Latest GitHub wins over old chats/memory.
- Production remains **v288: 94R /52 hits / ROI172.560638%**. Research does not change production.
- Inputs pre-deadline only; actual order/payout settlement labels only; realized 決まり手 never an input.
- Exact v288 94-race exclusion preserved.
- Jul/Aug 2026 NON-PRISTINE. September 2026 outcomes **UNREAD** and must remain UNREAD.

## Fixed source
- Run **34754875342**, Artifact **10317157868**, source max date <=2026-08-31.

## Frozen Wave54 head family
- Q50 motor edge + p3>=0.20 outside Wave36, then boat3 national2 - boat1 national2 >=+9.8pt.
- Exact **210R /71 heads =33.8095%**; early 104/36=34.6154%, late106/35=33.0189%.
- Wave54 commit `a45f83c11b7c3c7b8c6c75cab227253ea4f1d91f`.

## Wave55 dedicated opponent layer
- February-only candidate-level balanced logistic second/third models, 478 boat3-head races /2390 candidate rows.
- 3 tickets/R baseline: **27/71 =38.0282% capture**, stake ¥63,000, return ¥67,340, **ROI106.8889%**.
- Early 13/36 heads captured; late14/35.
- Result commit `6d402473d42c63e321994c6f672b5d45e1394ebe`.

## Wave56 — compact inner-vs-outer refinement — completed
### BEFORE commit
- `027c4e1c47c5139416fe66e7b097e151febfa2ab`.

### Method
- Frozen Wave54 210R/71 heads and maximum 3 tickets/R.
- Retained Wave55 February-trained second/third pair score.
- Added a race-level pre-deadline inner(1/2)-vs-outer(4/5/6) blend from national2, national3, motor3 and average ST, standardized on February distributions.
- Tested diagnostic blend weights lambda 0, .1, .2, .35, .5, .75, 1.0. March is research-exposed; nonzero weights are diagnostic only.

### Exact results
- lambda0 baseline: **27 hits /38.0282% / ROI106.8889%**, early13/36, late14/35.
- lambda.1: 25 hits /35.2113% / ROI77.9365%, early12, late13.
- lambda.2: 26 /36.6197% / ROI75.4762%, early11, late15.
- lambda.35: 25 /35.2113% / ROI75.2857%, early13, late12.
- lambda.5: 25 /35.2113% / ROI75.2857%, early13, late12.
- lambda.75: 27 /38.0282% / ROI87.9048%, early15, late12.
- lambda1.0: 26 /36.6197% / ROI82.7619%, early14, late12.

### Conclusion
- **Reject the coarse inner-vs-outer race-level blend.** No nonzero weight beats Wave55; all lose ROI and most lose capture.
- Keep Wave55 3-ticket ordering as the current compact opponent benchmark: 27/71, ROI106.89% diagnostic.
- Negative evidence suggests the next opponent improvement should be **candidate/pair-level**, not a single race-level inner/outer prior.
- A useful next direction is February-trained attack-structure proxy interaction at candidate/pair level (e.g. boat1/2 hold strength and boat4/5/6 rise strength as pair-specific interactions), still without realized 決まり手.
- Result file `research_v289_3head_wave56_compact_inner_outer_result.json`.
- Result commit `ee32e5122a522eca6b78878432ab1bcc7ce40c53`.
- No new Actions Run/Job/Artifact; reused Run34754875342 / Artifact10317157868.
- Status `DIAGNOSTIC_ONLY_WAVE56_INNER_OUTER_BLEND_REJECTED_KEEP_WAVE55`.
- September outcomes remain UNREAD; Jul/Aug not used; production unchanged.

## Exact restart point
- **Wave57:** keep 210R/71 and <=3 tickets/R frozen; refine Wave55 at candidate/pair level with February-trained pre-race attack-structure interactions. Target >27/71 capture and/or >106.89% ROI, with early/late stability. Do not use realized 決まり手. September UNREAD; v288 unchanged.
