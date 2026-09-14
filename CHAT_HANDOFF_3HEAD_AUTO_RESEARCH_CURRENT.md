# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Active branch: research/3head-player-attack-mode. Do not rewrite main.
- v288 baseline fixed: 94R / 52 hits / ROI172.560638%.
- Pre-deadline only. Jul/Aug NON-PRISTINE. September unread.

## Wave51 motor-first full-universe — COMPLETE / DIAGNOSTIC ONLY
- Source Run `34754875342` / Artifact `10317157868`, exact v288 exclusion.
- Full March: 4,482R / 563 boat3 heads = 12.561%.
- Feb-Q75 3-vs-2 motor edge (+6.2 motor2 / +7.2 motor3) + p3>=0.25: 133R / 47 heads =35.338%.
- Wave36 overlap45; incremental outside Wave36 =88R /27 heads =30.682%.
- Result commit `b7d5d0f9b3f6042976d8820771def4d89aa33278`.

## 2026-09-15 JST — Wave52 BEFORE WORK
- BEFORE handoff commit: `dfe49bcae4822cb1f5700738d24746260e9f4c50`.
- Preserve exact Wave51 88R definition. Descriptive hit-vs-miss analysis only; no March outcome threshold optimization. September UNREAD; v288 unchanged.

## 2026-09-15 JST — Wave52 AFTER
- Reproduced exact Wave51 incremental pool from frozen Wave21 source: 88R /27 boat3 heads /61 misses =30.682%.
- Result file `research_v289_3head_wave52_incremental88_structure_result.json`; result commit `210b4608ea540652b8ac942069faaf670b2fb891`.
- No new CI was required/claimed; computation used the already-fixed source Run `34754875342` / Artifact `10317157868` and exact v288 exclusion.
- Largest hit-vs-miss pre-deadline shifts: boat3 national win rate 6.403 vs5.904 (SMD +0.649); boat3 national 3-place rate64.530 vs58.543 (+0.619); boat1 average ST0.1589 vs0.1710 (-0.579); boat3 national 2-place rate46.044 vs41.152 (+0.540). Boat3-vs-boat1 national2 gap19.378 vs15.252 (+0.395); national win gap1.584 vs1.242 (+0.388); boat2 average ST0.1637 vs0.1721 (-0.371).
- Crucially, once inside Wave51's motor gate, MORE motor advantage did not separate hits: motor2 gap hit16.867 vs miss18.448; motor3 gap hit20.700 vs miss21.793. p3 was also essentially identical: hit0.30209 vs miss0.30255.
- Therefore the next signal is not 'even more motor edge'. The clearest remaining structure is boat3's own player strength plus the ST environment.
- February-derived single-dimension diagnostic slices (not March-fitted): boat3 national win>=FebQ75 6.18 =>41R/17 heads=41.463%; boat3 national2>=FebQ75 43.5 =>45R/18=40.000%; boat3 national3>=FebQ75 61.4 =>40R/15=37.500%; boat1 avgST<=Feb median0.16 =>43R/18=41.860%; boat2 avgST<=0.16 =>37R/13=35.135%.
- Exploratory combinations discovered after looking at March, therefore NOT validation/adoption evidence: boat3 national win>=6.18 + boat1 ST<=0.16 =>26R/14 heads=53.846%; boat3 national2>=43.5 + boat1 ST<=0.16 =>25R/13=52.000%.
- Frozen Wave36 conditional opponent Top5 captured only13 of the27 incremental head wins =48.148%. Thus an independent motor-first family needs not only a refined head gate but also a separate opponent-ranking layer.
- Decision/status: `DIAGNOSTIC_ONLY_STRONG_FUTURE_HYPOTHESIS_NO_PRISTINE_PERIOD`. No production change.
- Apr-Jun were not reopened for tuning; Jul/Aug unused; September outcomes remain UNREAD.

## Exact restart point
1. Freeze the Wave51 motor-first entrance gate; do not increase the motor-gap threshold because hit/miss separation did not improve with larger motor gaps.
2. Future head-layer hypothesis: combine motor-first entrance with independently frozen boat3 own-strength and ST-environment features. The March-observed 52-54% combinations are exploratory targets only, not validated rules.
3. Build a separate motor-first opponent layer because frozen Wave36 Top5 captures only 48.148% of the 27 incremental head wins.
4. Any adoption requires a genuinely untouched future period; v288 production remains unchanged.