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

## Wave55 dedicated opponent benchmark
- February-only candidate-level balanced logistic second/third models, 478 boat3-head races /2390 candidate rows.
- 3 tickets/R baseline: **27/71 =38.0282% capture**, stake ¥63,000, return ¥67,340, **ROI106.8889%**.
- Early 13/36 heads captured; late14/35.
- Result commit `6d402473d42c63e321994c6f672b5d45e1394ebe`.

## Wave56 coarse inner-vs-outer refinement — rejected
- Race-level inner(1/2)-vs-outer(4/5/6) blend did not beat Wave55.
- Best nonzero capture tied 27/71 but ROI fell to 87.90%; other weights lost capture and ROI.
- Keep Wave55 as benchmark. Result commit `ee32e5122a522eca6b78878432ab1bcc7ce40c53`; AFTER commit `51ce1c52ca5c3b7e22cbfadcf0891163abf348e0`.

## BEFORE WORK — Wave57 pair-level attack-structure interactions (2026-09-15)
- Freeze Wave54 population **210R /71 heads** and max **3 tickets/R**.
- Baseline to beat: Wave55 **27/71 capture, ROI106.8889%, early13/36, late14/35**.
- Train only on February boat3-head races. Build candidate/pair-level interaction features instead of a single race-level inner/outer prior.
- Explicitly model whether each ordered opponent pair contains inner boats1/2, outer boats4/5/6, mixed inner/outer, and pair-specific strength/ST/motor relationships to boat3 and to each other.
- Candidate/pair inputs remain strictly pre-deadline: lane, national ST/win/2/3, local win/2, motor2/3, boat2, plus derived gaps/means/interactions. Actual finish/order is training/settlement label only; payout is settlement only; realized 決まり手 never used.
- Compare pair-level February-trained models against Wave55's independent second*third pair score at exactly 3 tickets/R. Report hits/capture, all-210 ROI, early/late stability, and ticket composition frequencies.
- Any March-based model/threshold selection must be labeled exploratory. Prefer February model selection/frozen hyperparameters.
- No Jul/Aug clean validation; September outcomes remain UNREAD; production v288 unchanged.

## Exact restart point
- Execute Wave57 from fixed Artifact10317157868, commit exact result JSON, then append AFTER-WORK metrics/commit IDs/conclusion here.
