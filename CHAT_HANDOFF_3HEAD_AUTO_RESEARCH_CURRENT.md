# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy / non-negotiables
- Active branch: `research/3head-player-attack-mode`. Latest GitHub wins over old chats/memory. Do not rewrite main from research work.
- Current production baseline remains **v288** and is NOT changed by Wave47-55 research.
- v288 production baseline: **94R / 52 hits / ROI 172.560638%**.
- All research inputs must be pre-deadline only. Never use actual winning move / 決まり手 as an input feature.
- Exact v288 94-race exclusion must be preserved.
- Jul/Aug 2026 are **NON-PRISTINE**. September 2026 outcomes/results are **UNREAD** and must remain UNREAD.
- No research promotion without genuinely untouched future validation.

## Fixed source
- Run **34754875342**, Artifact **10317157868**, source max date <= 2026-08-31.
- Exact v288 exclusion: 94 races.

## Wave53 / Wave54 fixed head family
- Wave53 Q50 motor edge + p3>=0.20 outside Wave36: **300R /87 heads =29.000%**.
- Wave54 adds frozen Feb-Q80 player-strength gap: **boat3 national2 - boat1 national2 >= +9.8pt**.
- Wave54 exact result: **210R /71 heads =33.8095%**; early 104/36=34.6154%, late 106/35=33.0189%.
- Wave54 result commit `a45f83c11b7c3c7b8c6c75cab227253ea4f1d91f`.

## Wave55 — dedicated opponent layer — completed
- March universe 4,482R; Wave36 90R/38; Wave53 300R/87; Wave54 210R/71 reproduced exactly.
- Opponent model trained on February 2026 boat3-head races only: 478R / 2,390 candidate rows.
- Candidate-level balanced logistic second/third models; pair score=P(second)*P(third), pre-deadline inputs only.
- 1 ticket/R: 12/71 capture 16.90%, ROI 106.52%.
- **3 tickets/R: 27/71 capture 38.03%, stake ¥63,000, return ¥67,340, ROI 106.89%**.
- 5 tickets/R: 36/71 capture 50.70%, ROI 88.58%; broader ticket expansion worsens ROI.
- Result file `research_v289_3head_wave55_opponent_layer_result.json`; commit `6d402473d42c63e321994c6f672b5d45e1394ebe`.
- No new Actions; fixed Run34754875342 / Artifact10317157868 reused.
- Diagnostic only; September UNREAD; production unchanged.

## BEFORE WORK — Wave56 compact inner-vs-outer opponent refinement (2026-09-15)
- Freeze Wave54 head population at **210R /71 actual boat3 heads** and freeze maximum ticket count at **3 tickets/R**.
- Baseline to beat: Wave55 **27/71 =38.03% conditional capture**, all-210 **ROI 106.89%**.
- Reconstruct Wave55 February-trained opponent scores and evaluate pre-deadline structural refinements that distinguish inner-hold propensity (boats1/2) from outer-rise propensity (boats4/5/6).
- Do not use actual March order, payout, or realized 決まり手 to define an input/classifier. They are settlement labels only.
- Candidate refinements may use February-trained pair/order models, explicit pre-race inner/outer strength/ST/motor aggregates, or February-frozen thresholds. March-observed alternatives must be labeled exploratory, never OOS validation.
- Report exact 3-ticket capture/ROI, early-vs-late chronological stability, and ticket composition frequencies. Also retain 1-ticket reference where useful.
- Do not increase beyond 3 tickets/R.
- September outcomes stay UNREAD. Jul/Aug remain NON-PRISTINE and are not used as clean validation. Production v288 remains unchanged.

## Exact restart point
- Execute Wave56 locally from fixed source Artifact10317157868; compare compact inner-vs-outer 3-ticket structures against Wave55 27/71 and ROI106.89%, commit result, then append AFTER-WORK audit details here.
