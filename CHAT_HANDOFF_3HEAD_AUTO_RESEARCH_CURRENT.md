# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy / non-negotiables
- Active branch: `research/3head-player-attack-mode`. Latest GitHub wins over old chats/memory. Do not rewrite main from research work.
- Current production baseline remains **v288** and is NOT changed by Wave47-54 research.
- v288 production baseline: **94R / 52 hits / ROI 172.560638%**.
- All research inputs must be pre-deadline only. Never use actual winning move / 決まり手 as an input feature.
- Exact v288 94-race exclusion must be preserved in this research family.
- Jul/Aug 2026 are **NON-PRISTINE** and may not be treated as clean validation.
- September 2026 outcomes/results are **UNREAD** and must remain UNREAD. Never open September outcomes.
- Do not silently promote research to production. Any adoption needs a genuinely untouched future period.

## Fixed source
- Source workflow run: **34754875342**.
- Source artifact: **10317157868** (`3head-wave21-allrace-source-build`).
- Source CSV max date <= 2026-08-31; September absent.
- Exact v288 exclusion: 94 races.

## Wave52 key finding
- In Wave51 incremental 88R / 27 boat3 heads, stronger motor advantage no longer separated hits from misses.
- Remaining signal centered on boat3 own player strength + ST environment.
- Frozen Wave36 conditional opponent Top5 captured only **13/27 = 48.148%** of these motor-first boat3-head wins, motivating a dedicated opponent layer.

## Wave53 high-volume base
- Leading region outside Wave36: **Q50 motor edge + p3>=0.20 = 300R / 87 boat3 heads = 29.000%**.
- Q50 means boat3-vs-boat2 motor2 gap >= +0.1pt and motor3 gap >= 0.0pt.
- Neighbor anchors: p3>=0.22 = 236R/70 heads/29.661%; p3>=0.18 = 389R/103 heads/26.478%.

## Wave54 broad-Q50 head refinement — completed
- Base: Wave53 Q50+p3>=0.20 incremental 300R /87 heads.
- Best volume-preserving frozen February-derived rule: **boat3 national2 minus boat1 national2 >= +9.8pt**.
- Result: **210R /71 boat3 heads =33.8095%**.
- Chronological halves: early **104R/36 =34.6154%**, late **106R/35 =33.0189%**.
- Best tested pair in 180-220R: boat3 national2>=23.8 AND boat1 avg ST<=0.17 = 183R/61 heads/33.3333%.
- Tested frozen player/ST refinements did not reach 35% around 200R.
- Wave54 result commit: `a45f83c11b7c3c7b8c6c75cab227253ea4f1d91f`.
- Result file: `research_v289_3head_wave54_broad_q50_head_refinement_result.json`.
- No new Actions run/job/artifact for Wave54; fixed source Run34754875342 / Artifact10317157868 was used.
- Status: DIAGNOSTIC_ONLY; no production change.

## BEFORE WORK — Wave55 dedicated opponent layer (2026-09-15)
- Fixed head-candidate population: **Wave54 210R /71 actual boat3 heads /33.81%**. Do not retune the head rule during opponent research.
- Objective: design a dedicated opponent-ranking/order layer for the 71 races where boat3 actually won, instead of reusing Wave36 Top5.
- Compare at minimum: second-place capture, third-place capture, exact trifecta capture, average/maximum ticket count, and settlement ROI where closing odds are available.
- Use only pre-deadline features for ranking. Actual finish/order and payout are settlement labels only, never input features.
- Examine separate conditional structures for likely **inner-hold vs outer-rise** opponent patterns using only pre-race proxies. Do NOT use actual winning move/決まり手 to classify or predict.
- Research may inspect whether distinct pre-race proxy families correspond to 3攻め scenarios often described operationally as まくり/まくり差し, but must not use the realized 決まり手 as a feature.
- Preserve exact v288 94-race exclusion and fixed source artifact.
- September 2026 outcomes remain **UNREAD**. Jul/Aug remain NON-PRISTINE. No production changes.
- After work: record exact rules, metrics, commit SHA, any actual Actions Run/Job/Artifact IDs, conclusion, and next restart point here.

## Exact restart point
- **Wave55:** reconstruct Wave54's 210R/71-head membership exactly from the fixed source, then evaluate dedicated opponent ordering/ticket structures on those 71 heads.
- Production **v288 stays unchanged**; September outcomes stay **UNREAD**.
