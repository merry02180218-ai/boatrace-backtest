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

## Wave57 current research leader
- February-only ordered-pair interaction model, 478 training races /9,560 pair rows.
- February grouped CV: AUC **0.704**, top3 ordered capture **41.6%**.
- March diagnostic: **29/71=40.8451%**, ¥63,000 -> ¥74,110, **ROI117.6349%**; early14/36, late15/35.
- Result commit `e2803294d68cb7fe5cf849651febb35595f370bf`; AFTER `d6b49c15dd7eead2c1c2ce9b67ccb782dae5d952`.
- Diagnostic only; not production evidence.

## BEFORE WORK — Wave58 robustness audit (2026-09-15)
- Freeze population 210R/71 and 3 tickets/R. Do NOT optimize on March outcomes.
- Reconstruct Wave57 and audit robustness using February-only grouped CV.
- Test regularization sensitivity and feature-family ablations: remove lane/structure indicators; remove racer-strength interactions; remove ST interactions; remove motor/boat interactions; remove pair-relative/gap interactions. Also test probability calibration/ranking invariance where appropriate.
- Require improvement to be distributed across February folds and to survive removal of any single interaction family; flag any family whose removal collapses performance.
- March is used only after February choices are frozen, for diagnostic settlement and early/late stability. Audit Wave55->Wave57 ticket substitutions and the two net newly captured hits, but do not use them to select a model.
- Report fold-level top3 capture/AUC, ablation summary, March hits/capture/ROI/early/late for the frozen robust specification, and whether Wave57 should be frozen for future untouched validation.
- No realized 決まり手 input. September outcomes remain UNREAD. Jul/Aug NON-PRISTINE. Production v288 unchanged.

## Exact restart point
- Execute Wave58 robustness audit, commit result JSON, then append AFTER-WORK result/commit IDs/conclusion here.
