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
### Reproduction audit
- Eligibility is exact settled+closing-odds usable population plus v288 exclusion.
- March universe reproduced **4,482R**.
- Wave36 reproduced **90R /38 heads**.
- Wave53 reproduced **300R /87 heads**.
- Wave54 reproduced **210R /71 heads** exactly.

### Opponent model
- Training period: **February 2026 only**.
- February boat3-head training races: **478R**, candidate rows **2,390**.
- Candidate-level balanced logistic models estimate second and third probabilities; ordered pair score = P(second) * P(third).
- Inputs are pre-deadline only: lane plus own/relative national ST, national win/2/3-place rates, local win/2-place, motor2/3, boat2.
- Actual order is label/settlement only. Realized 決まり手 is not used.

### Exact March diagnostic ticket results across ALL 210 Wave54 candidates
- **1 ticket/R:** 12 hits; conditional capture 12/71 = **16.90%**; stake ¥21,000; return ¥22,370; **ROI 106.52%**.
- **3 tickets/R:** 27 hits; conditional capture 27/71 = **38.03%**; stake ¥63,000; return ¥67,340; **ROI 106.89%** — best tested ROI.
- **5 tickets/R:** 36 hits; capture **50.70%**; stake ¥105,000; return ¥93,010; **ROI 88.58%**.
- 7 tickets/R: 45 hits; capture 63.38%; ROI 82.77%.
- 10 tickets/R: 52 hits; capture 73.24%; ROI 73.33%.
- 12 tickets/R: 58 hits; capture 81.69%; ROI 84.72%.
- 20 tickets/R: 71 hits; capture 100%; ROI 88.16%.

### Interpretation
- Dedicated ordering does NOT justify broad ticket expansion: capture rises but ROI falls below 100% from 5 tickets onward.
- The interesting compact region is **1-3 tickets**, especially 3 tickets/R at **106.89% diagnostic ROI**.
- This is March research-exposed evaluation and is NOT pristine/OOS adoption evidence.
- Wave52's old Wave36 Top5 captured 48.148% on a different 27-head incremental pool; Wave55 5-ticket capture is 50.70% on the new 71-head pool, so this is not evidence of a major capture breakthrough by itself.
- Result file: `research_v289_3head_wave55_opponent_layer_result.json`.
- Result commit: `6d402473d42c63e321994c6f672b5d45e1394ebe`.
- BEFORE-WORK handoff commit: `8d6df1aad34714f72bf847369a11e519542be7f1`.
- No new Actions Run/Job/Artifact created for Wave55; fixed source Run34754875342 / Artifact10317157868 was reused.
- Status: `DIAGNOSTIC_ONLY_WAVE55_3TICKET_POSITIVE_MARCH_NO_PRISTINE_VALIDATION`.
- September outcomes remain UNREAD; Jul/Aug not used; production unchanged.

## Recommended next experiment — Wave56
- Keep Wave54 head population frozen at 210R/71 heads.
- Focus on **compact 1-3 ticket opponent structures**, not 5+ ticket expansion.
- Split/order opponents using pre-race inner-hold vs outer-rise proxies and test whether 3-ticket ROI/capture can improve while preserving chronological stability.
- Report early/late halves and exact ticket composition frequencies.
- Do not use realized 決まり手 as an input or classifier.
- March remains diagnostic/research-exposed; September stays UNREAD; v288 production unchanged.

## Exact restart point
- **Wave56:** on frozen Wave54 210R, refine Wave55's 3-ticket opponent ordering using pre-deadline inner-vs-outer structure; target >38.03% conditional capture and/or >106.89% all-210 ROI without increasing beyond 3 tickets/R.
