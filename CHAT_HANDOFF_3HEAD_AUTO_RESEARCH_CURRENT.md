# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy / non-negotiables
- Active branch: `research/3head-player-attack-mode`. Latest GitHub wins over old chats/memory. Do not rewrite main from research work.
- Current production baseline remains **v288** and is NOT changed by Wave47-53 research.
- v288 production baseline: **94R / 52 hits / ROI 172.560638%**.
- All research inputs must be pre-deadline only. Never use actual winning move / 決まり手 as an input feature.
- Exact v288 94-race exclusion must be preserved in this research family.
- Jul/Aug 2026 are **NON-PRISTINE** and may not be treated as clean validation.
- September 2026 outcomes/results are **UNREAD** and must remain UNREAD. Never open September outcomes.
- Do not silently promote research to production. Any adoption needs a genuinely untouched future period.

## Core benchmark context
- Wave36 benchmark Apr-Jun: **391R / 87 hits / ROI 114.913% / +583,090 yen**.
- Wave36S-C Apr-Jun: **305R / 74 hits / ROI 128.218% / +860,660 yen**, status RESEARCH_CANDIDATE only.
- Wave47 head-condition zoning passed March structural gate but Apr-Jun failed: **174R / 36 hits / ROI 95.511% / -78,100 yen**; NO_ADOPTION.
- Wave48 diagnosis found June failure was `MIXED_HEAD_AND_OPPONENT_FAILURE`. Strongest pre-race clue was shrinkage in boat3-vs-boat2 motor edge: motor3 gap mean +29.261 -> +16.448 and motor2 gap +23.8625 -> +13.1323 from Apr+May to June. This motivated explicit 3-vs-2 motor-edge work.
- Wave49 learned/logistic motor-wall blend did not beat Wave47; NO_ADOPTION.

## Wave50 — explicit 3-vs-2 motor-edge regimes
- Purpose: test explicit pre-race motor regimes without a learned blended score.
- Regime thresholds derived from **February feature distribution only**:
  - motor2 gap low/high = -4.0 / +3.9
  - motor3 gap low/high = -4.6 / +4.633333...
- March results inside Wave36 universe:
  - STRONG: 49R /22 boat3 heads = **44.898%**
  - MEDIUM: 30R /14 heads = **46.667%**
  - WEAK: 11R /2 heads = **18.182%**
- Critical interpretation: the biggest separation is **WEAK vs non-WEAK**, not STRONG vs MEDIUM. Weak motor edge appears primarily a **head-layer failure**, because when boat3 did win in WEAK, frozen Top5 captured both wins.
- Status: `DIAGNOSTIC_ONLY_NO_PRISTINE_PERIOD`; no production change.
- Wave50 implementation commit: `f070b53445ab59968c48e87c2deff89b6342162e`.
- Wave50 result commit: `e60dda90f7f44068e5f5d6ace592bd3182a162f3`.
- Wave50 AFTER handoff commit: `0e749710e179d1db095e7303083fee41ce62883a`.
- No GitHub Actions Run/Job/Artifact IDs for Wave50; workflow writes were blocked, so exact fixed source artifact was used directly.

## Fixed source used by Wave48 / Wave50 / Wave51 / Wave52 / Wave53
- Source workflow run: **34754875342**.
- Source artifact: **10317157868** (`3head-wave21-allrace-source-build`).
- Artifact digest from earlier audit: `sha256:01d84cc2b5b63ae9ec240c730cd556c168caeae184355fd6d74e8beb9a4bf8b1`.
- Source CSV: `analysis_v289_3head_wave21_allrace_feature_settled.csv`.
- Exact v288 exclusion file: `v288_operational_pre_replay_94_baseline_codes.csv` with 94 race codes.
- September filter is enforced; source max date remains <= 2026-08-31.

## Wave51 — motor-first full-universe candidate discovery
### Why Wave51 existed
- User pointed out that the Wave50 motor-edge clue might be more useful as an **upstream candidate generator**, not merely as a Wave36 filter.
- Wave51 therefore started from the full March eligible universe instead of Wave36-only candidates.

### Full March baseline
- March eligible universe after exact v288 exclusion: **4,482R**.
- Boat3 heads: **563R = 12.56135654%**.
- Reproduced Wave36 March candidate set: **90R / 38 heads = 42.222%**.

### February-derived motor quantile cuts
- Q50: motor2 gap >= **+0.1pt**, motor3 gap >= **0.0pt**.
- Q67: motor2 gap >= **+4.0pt**, motor3 gap >= **+4.8pt**.
- Q75: motor2 gap >= **+6.2pt**, motor3 gap >= **+7.2pt**.
- Q80: motor2 gap >= **+7.9pt**, motor3 gap >= **+9.1pt**.
- Q90: motor2 gap >= **+12.32pt**, motor3 gap >= **+14.1pt**.
- Motor advantage alone was too broad/weak: head rates stayed roughly 14-15%.

### Key Wave51 focused candidate
- Frozen rule: both boat3-vs-boat2 motor2/motor3 gaps >= Feb Q75 **AND p3>=0.25**.
- Total selected: **133R /47 boat3 heads =35.338%**.
- Wave36 overlap: **45R**.
- Incremental outside Wave36: **88R /27 heads =30.682%**.
- This established that a separate motor-first 3HEAD family can add meaningful races outside Wave36.
- Wave51 result commit: `b7d5d0f9b3f6042976d8820771def4d89aa33278`.
- Status: `RESEARCH_FAMILY_WORTH_CONTINUING_DIAGNOSTIC_ONLY_NO_PRISTINE_PERIOD`.

## Wave52 — structure of Wave51's incremental 88R
### Exact target
- Reproduced Wave51 incremental pool exactly: **88R /27 boat3 heads /61 misses =30.682%**.
- Candidate definition was frozen: Feb Q75 motor2/motor3 gate + p3>=0.25, excluding Wave36 March subset.

### Hit-vs-miss findings
- Important negative finding: **more motor advantage did NOT separate hits after entering the motor gate**.
  - motor2 gap hit mean **+16.867** vs miss **+18.448**.
  - motor3 gap hit **+20.700** vs miss **+21.793**.
  - p3 hit **0.30209** vs miss **0.30255** — essentially identical.
- Stronger remaining pre-race separation was boat3's own player strength plus ST environment:
  - boat3 national win rate: **6.403 vs 5.904** (SMD +0.649).
  - boat3 national 3-place rate: **64.530 vs 58.543** (SMD +0.619).
  - boat1 avg ST: **0.1589 vs 0.1710** (lower/faster on hits; SMD -0.579).
  - boat3 national 2-place rate: **46.044 vs 41.152** (SMD +0.540).
  - boat3-vs-boat1 national2 gap: **19.378 vs15.252**.
  - boat3-vs-boat1 national win gap: **1.584 vs1.242**.
  - boat2 avg ST: **0.1637 vs0.1721**.

### February-derived single-dimension slices
These are diagnostic, using February-derived cut points rather than March-fitted thresholds:
- boat3 national win >= **6.18**: **41R /17 heads =41.463%**.
- boat3 national2 >= **43.5**: **45R /18 =40.000%**.
- boat3 national3 >= **61.4**: **40R /15 =37.500%**.
- boat1 avg ST <= **0.16**: **43R /18 =41.860%**.
- boat2 avg ST <= **0.16**: **37R /13 =35.135%**.

### Exploratory March-observed combinations — NOT validated
- boat3 national win>=6.18 + boat1 ST<=0.16: **26R /14 heads =53.846%**.
- boat3 national2>=43.5 + boat1 ST<=0.16: **25R /13 =52.000%**.
- These were observed after looking at March and therefore must NOT be treated as OOS/adoption evidence. They are future hypotheses only.

### Opponent-layer problem
- Frozen Wave36 conditional opponent Top5 captured only **13/27 =48.148%** of Wave51 incremental boat3-head wins.
- Therefore a separate motor-first family likely needs its **own opponent-ranking layer**, rather than blindly reusing Wave36 Top5.
- Wave52 result file: `research_v289_3head_wave52_incremental88_structure_result.json`.
- Wave52 result commit: `210b4608ea540652b8ac942069faaf670b2fb891`.
- Wave52 AFTER handoff commit: `6fb10061b0ca33ab81969ed222bae9854efa329e`.
- No new CI was claimed; fixed source Run34754875342 / Artifact10317157868 was used.

## Wave53 — expand mother population / high-volume motor-first region
### User goal
- User wanted **more population** than Wave51's incremental 88R.
- Aim was roughly **200-400 incremental races**, while retaining a materially elevated 3-head rate.
- Start-of-work handoff commit: `35785a061ae640d8434b863c51ba3aa5168f35bb`.

### Method
- Kept the same full March eligible universe and exact v288 exclusion.
- Reused frozen February motor quantile cuts (especially Q50/Q67/Q75).
- Crossed broad fixed p3 floors and measured:
  - selected races
  - boat3 heads/head rate
  - Wave36 overlap
  - incremental races outside Wave36
  - incremental heads/head rate
- No production threshold was adopted from March; this is population mapping only.

### Main high-volume findings OUTSIDE Wave36
- **Q50 motor edge + p3>=0.18:** **389R /103 heads =26.478%**.
- **Q50 motor edge + p3>=0.20:** **300R /87 heads =29.000%**.
- **Q50 motor edge + p3>=0.22:** **236R /70 heads =29.661%**.
- Q67 motor edge + p3>=0.18: **252R /61 heads =24.206%**.
- Q67 motor edge + p3>=0.20: **193R /51 heads =26.425%**.

### Main Wave53 interpretation
- **Q50 is the strongest volume-vs-rate region.** A looser motor entrance plus a modest p3 floor works better for coverage than demanding very large motor gaps.
- Relative to full-March base rate 12.561%, Q50+p3>=0.20 gives **29.000% across 300 incremental races**, more than **2.3x base head rate**.
- Compared with Wave51 focused incremental candidate:
  - Wave51: **88R /27 heads =30.682%**.
  - Wave53 Q50+p3>=0.20: **300R /87 heads =29.000%**.
- Thus population expands roughly **3.4x** (88 -> 300) while head rate drops only about **1.68 percentage points** (30.68% ->29.00%). This is a very strong research finding.
- Q50+p3>=0.22 is the higher-selectivity neighbor: 236R /70 heads =29.661%.
- Q50+p3>=0.18 is the maximum-volume neighbor: 389R /103 heads =26.478%.
- Increasing motor threshold from Q50 to Q67/Q75 is NOT the preferred direction for this family; once a basic motor advantage exists, p3/player-strength/ST refinement is more promising.

### Wave53 records / audit trail
- Result file: `research_v289_3head_wave53_population_expansion_result.json`.
- Result commit: `432065ba171359c919f01826f9ac9fae0bc99621`.
- Wave53 AFTER handoff commit: `044d725fb24a66bd77b1c197c7f513b628fb4790`.
- No new GitHub Actions Run/Job/Artifact was needed or claimed for Wave53.
- Computation used fixed source Run **34754875342** / Artifact **10317157868** locally, with exact 94-race v288 exclusion.
- Decision/status: `DIAGNOSTIC_ONLY_HIGH_VOLUME_REGION_FOUND_NO_PRISTINE_PERIOD`.

## Current best research hypothesis after Wave53
- Treat **Q50 motor edge + p3>=0.20** as the leading high-volume motor-first research region:
  - incremental outside Wave36: **300R /87 boat3 heads =29.000%**.
- Nearby sensitivity anchors:
  - Q50+p3>=0.22 = **236R /70 heads =29.661%**.
  - Q50+p3>=0.18 = **389R /103 heads =26.478%**.
- Do NOT tighten the motor gap further just because the Wave50 diagnosis began with motor edge. Wave52 showed that once inside the gate, larger motor gaps did not distinguish hits from misses.
- The likely next useful head-layer signals are:
  1. boat3 own national win/2-place/3-place strength
  2. boat1 ST environment
  3. boat2 ST / wall environment
  4. boat3-vs-boat1 player-strength gaps
- The likely next useful opponent-layer work is a dedicated motor-first conditional ordering, because Wave36 Top5 only captured 48.148% of the old incremental 27 head wins.

## Recommended exact next experiment
### Wave54 candidate — broad Q50 head refinement
1. Start from the **Q50 motor edge + p3>=0.20** incremental 300R region outside Wave36.
2. Preserve Q50 motor threshold; do **not** raise it.
3. Add independently frozen pre-deadline boat3 own-strength and ST-environment structure.
4. Primary research target: retain roughly **180-250R** while seeing whether head rate can move from 29% toward the mid-30s.
5. Use February-derived cuts / frozen structure where possible. Do not outcome-fit a March threshold and label it validation.
6. Report chronological early/late stability.
7. Separately begin a dedicated motor-first opponent layer; do not assume Wave36 Top5 is adequate.
8. Apr-Jun are contaminated for this hypothesis and must not be called pristine validation. Jul/Aug remain NON-PRISTINE. September must stay UNREAD.
9. v288 production remains unchanged until genuinely untouched validation exists.

## Important workflow / audit behavior for next chat
- At the beginning of any new work, first read this handoff and latest GitHub branch state.
- Before substantive implementation/runs, append a BEFORE-WORK plan to this same handoff and commit it.
- After work, append results, exact metrics, commit SHA, any Actions Run/Job/Artifact IDs actually used, conclusion, and exact restart point.
- Never fabricate CI IDs. Wave50-53 often used the already-fixed source artifact directly; if no new CI run exists, state that explicitly.

## Exact restart point
- **Next action: Wave54 broad-Q50 head refinement** on the 300 incremental Q50+p3>=0.20 March research pool, emphasizing boat3 own strength + ST environment and keeping enough volume.
- In parallel/afterward, design a dedicated motor-first opponent ranking layer.
- September 2026 outcomes remain **UNREAD**.
- Production **v288 stays unchanged**.