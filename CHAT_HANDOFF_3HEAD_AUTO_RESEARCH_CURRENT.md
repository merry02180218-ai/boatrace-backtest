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
- Exact **210R /71 heads =33.8095%**.

## Wave55 benchmark
- 3 tickets/R: **27/71=38.0282%**, ROI **106.8889%**; early13/36, late14/35.

## Wave57 opponent specification — FROZEN after Wave58
- February-only ordered-pair interaction model, 478 training races /9,560 ordered-pair rows.
- Inputs: lane identities; candidate own/relative national ST, national win/2/3, local win/2, motor2/3, boat2; boat3 gaps; pair gaps/means; inner/outer/mixed indicators; pair-specific interactions.
- February grouped CV: AUC **0.704**, top3 ordered capture **41.6%**.
- March diagnostic: **29/71=40.8451%**, ¥63,000 -> ¥74,110, **ROI117.6349%**; early14/36, late15/35.
- Wave57 result commit `e2803294d68cb7fe5cf849651febb35595f370bf`.

## Wave58 robustness audit — completed
### BEFORE commit
- `d8a7bb9cecddec056ee4a1febfdcebece1738579`.

### February fold stability
- Fold1 AUC .699 / top3 40.2%; Fold2 .711 /42.8%; Fold3 .702 /40.9%; Fold4 .708 /42.1%; Fold5 .700 /41.8%.
- No fold collapse; top3 range only **40.2-42.8%**.

### Regularization sensitivity
- C=.25: AUC .702/top3 41.2%; C=.5: .704/41.5%; C=1.0: .704/41.6%; C=2.0: .703/41.4%; C=4.0: .701/41.0%.
- Broad plateau; specification is not knife-edge. Freeze **C=1.0**.

### Feature-family ablations
- Remove lane/structure: CV AUC .697/top3 40.3%; March diagnostic 28 hits/ROI111.22%.
- Remove racer-strength interactions: .692/39.7%; March27/ROI104.90%.
- Remove ST interactions: .699/40.6%; March28/ROI112.37%.
- Remove motor/boat interactions: .701/41.0%; March28/ROI114.03%.
- Remove pair-relative gaps: .695/40.0%; March27/ROI107.75%.
- **No single-family removal improves February CV.** Racer-strength interactions and pair-relative gaps are most important, but the result is not dependent on only one family.

### Ticket substitution audit
- Wave55 27 hits -> Wave57 29 hits.
- Wave57 loses 1 old Wave55 hit but adds 3 different hits = **net +2**.
- These March substitutions were not used for model selection.

### Conclusion / freeze decision
- Wave57 passes the planned robustness audit: stable February folds, broad regularization plateau, and all ablations worsen February CV.
- **FREEZE Wave57 opponent specification now. Do not tune it further on March.**
- Next evidence must be genuinely untouched future validation before any production promotion.
- Wave58 result file `research_v289_3head_wave58_robustness_audit_result.json`.
- Result commit `2eded90296f0f04f3a20fb4362adaae2de999456`.
- No new Actions Run/Job/Artifact; fixed Run34754875342 / Artifact10317157868 reused.
- Status `FREEZE_WAVE57_OPPONENT_SPEC_PENDING_PRISTINE_FUTURE_VALIDATION`.
- September outcomes remain UNREAD; Jul/Aug not used; production v288 unchanged.

## Exact restart point
- Do **not** continue March tuning of Wave57. Preserve frozen Wave54 head rule + frozen Wave57 3-ticket opponent specification for a genuinely untouched future-period validation. September outcomes remain UNREAD until the user explicitly authorizes reading them. Production v288 unchanged.
