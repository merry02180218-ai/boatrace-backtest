# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Active branch: research/3head-player-attack-mode. Do not rewrite main.
- v288 baseline fixed: 94R / 52 hits / ROI172.560638%.
- Pre-deadline only. Jul/Aug NON-PRISTINE. September unread.

## Wave51 motor-first full-universe
- Source Run `34754875342` / Artifact `10317157868`, exact v288 exclusion.
- March full: 4,482R /563 boat3 heads =12.561%.
- Q75 motor edge + p3>=0.25: 133R /47 heads; incremental outside Wave36 =88R /27 heads =30.682%.

## Wave52 key finding
- Inside the Wave51 motor gate, larger motor gaps did not separate hits. Boat3 own player strength and ST environment were more useful.
- Frozen Wave36 opponent Top5 captured only13/27 incremental head wins.

## 2026-09-15 JST — Wave53 BEFORE WORK
- User asked to expand the mother population materially.
- Map broader motor-first regions from February-derived motor cuts and fixed p3 floors, focusing on roughly 200-400 incremental races.
- Research only; no production selection from March outcomes. Jul/Aug unused; September UNREAD; v288 unchanged.
- BEFORE commit: `35785a061ae640d8434b863c51ba3aa5168f35bb`.

## 2026-09-15 JST — Wave53 AFTER
- Frozen source reproduced exactly: March 4,482R /563 heads; Wave36 p3>=0.365448 reproduced 90R /38 heads.
- Main high-volume findings outside Wave36:
  - Q50 motor edge + p3>=0.18: **389R /103 heads =26.478%**.
  - Q50 motor edge + p3>=0.20: **300R /87 heads =29.000%**.
  - Q50 motor edge + p3>=0.22: **236R /70 heads =29.661%**.
  - Q67 motor edge + p3>=0.18: 252R /61 heads =24.206%.
  - Q67 motor edge + p3>=0.20: 193R /51 heads =26.425%.
- Q50 is the strongest volume-rate region: weaker motor entrance but modest p3 floor substantially expands the candidate pool without collapsing head rate.
- Relative to March base 12.561%, Q50+p3>=0.20 remains more than 2.3x base head rate across 300 incremental races.
- Result file: `research_v289_3head_wave53_population_expansion_result.json`.
- Result commit: `432065ba171359c919f01826f9ac9fae0bc99621`.
- No new Actions run/job/artifact was needed or claimed; computation used fixed source Run `34754875342` / Artifact `10317157868` locally and exact 94-race exclusion.
- Decision/status: `DIAGNOSTIC_ONLY_HIGH_VOLUME_REGION_FOUND_NO_PRISTINE_PERIOD`.
- Jul/Aug not used. September outcomes remain UNREAD. Production v288 unchanged.

## Exact restart point
1. Treat Q50+p3>=0.20 (300 incremental /87 heads) as the leading high-volume research region; Q50+p3>=0.22 (236/70) as the higher-selectivity neighbor; Q50+p3>=0.18 (389/103) as the maximum-volume neighbor.
2. Next, build the motor-first family head refinement on this broader Q50 region using pre-deadline boat3 own-strength and ST-environment structure, without increasing the motor threshold.
3. Build a dedicated opponent layer for this family rather than reusing Wave36 Top5 unchanged.
4. Any production adoption requires genuinely untouched future data.