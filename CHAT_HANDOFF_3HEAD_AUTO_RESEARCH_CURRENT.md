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
- Exact **210R /71 heads =33.8095%**; early104/36=34.6154%, late106/35=33.0189%.

## Wave55 benchmark
- February-only independent second/third candidate models.
- 3 tickets/R: **27/71=38.0282%**, ¥63,000 -> ¥67,340, **ROI106.8889%**; early13/36, late14/35.
- Commit `6d402473d42c63e321994c6f672b5d45e1394ebe`.

## Wave56
- Coarse race-level inner-vs-outer prior rejected. Commit `ee32e5122a522eca6b78878432ab1bcc7ce40c53`.

## Wave57 — pair-level attack-structure interactions — completed
### BEFORE commit
- `f5d32409dda70801b1f41f733cff20fe683bb757`.

### Method
- Population frozen: **210R/71 heads**, exactly 3 tickets/R.
- February 2026 boat3-head training only: 478 races, 9,560 ordered-pair rows.
- Balanced logistic ordered-pair classifier with lane identities, candidate own/relative national ST, national win/2/3, local win/2, motor2/3, boat2, boat3 gaps, pair gaps/means, inner/outer/mixed indicators, and pair-specific interactions.
- Hyperparameter/model selection by February grouped 5-fold CV only; March labels not used for model selection.
- February CV: baseline pair AUC 0.681 -> interaction AUC **0.704**; top3 ordered capture 37.9% -> **41.6%**.

### March diagnostic result
- Wave55 baseline: **27/71 =38.0282%, ROI106.8889%, early13/36, late14/35**.
- Wave57: **29/71 =40.8451% capture**.
- All 210 x 3 tickets: stake **¥63,000**, return **¥74,110**, **ROI117.6349%**.
- Improvement: **+2 hits, +2.8169pp capture, +10.7460pp ROI**.
- Early: **14/36** captured; late: **15/35** captured. Both halves improve by one hit versus Wave55.
- Ticket composition: all-inner 18.1%, mixed inner/outer 57.6%, all-outer 24.3%.

### Conclusion
- Pair-level interaction structure is materially better than Wave56's coarse race-level prior and improves the Wave55 compact benchmark on both capture and diagnostic ROI.
- This is still March research-exposed diagnostic evidence, NOT pristine validation and NOT a production promotion.
- Result file `research_v289_3head_wave57_pair_interaction_result.json`.
- Result commit `e2803294d68cb7fe5cf849651febb35595f370bf`.
- No new Actions Run/Job/Artifact; fixed Run34754875342 / Artifact10317157868 reused.
- Status `DIAGNOSTIC_ONLY_WAVE57_PAIR_INTERACTION_IMPROVES_WAVE55_NO_PRISTINE_VALIDATION`.
- September outcomes remain UNREAD; Jul/Aug not used; production unchanged.

## Recommended next experiment — Wave58
- Keep 210R/71 and 3 tickets/R frozen.
- Audit Wave57's two newly captured hits and Wave55->Wave57 ticket substitutions without optimizing on March outcome.
- Use February-only CV to test regularization/feature-family ablations and probability calibration; require the gain to survive removal of any single interaction family.
- Report February fold stability plus March early/late diagnostic stability. If robust, freeze Wave57-family opponent specification for future untouched validation rather than further March tuning.

## Exact restart point
- **Wave58 robustness audit** of Wave57 pair interactions. September UNREAD; production v288 unchanged.
