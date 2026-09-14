# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Active branch: research/3head-player-attack-mode. Do not rewrite main.
- v288 baseline fixed: 94R / 52 hits / ROI172.560638%.
- Pre-deadline only. Jul/Aug NON-PRISTINE. September unread.
- Hourly 3-head monitor remains disabled unless user asks.

## Benchmarks
- Wave36: Apr-Jun 391R / 87 hits / ROI114.913% / +583,090 yen.
- Wave36S-C: Apr-Jun 305R / 74 hits / ROI128.218% / +860,660 yen. RESEARCH_CANDIDATE.

## Wave50 key finding
- February-derived WEAK 3-vs-2 motor-edge regime: March 11R / 2 boat3 heads = 18.182%; dominant failure is head selection.
- Diagnostic only; no production change.

## Wave51 motor-first full-universe — COMPLETE / DIAGNOSTIC ONLY
- Source Run `34754875342` / Artifact `10317157868`, exact v288 exclusion.
- Full March: 4,482R / 563 boat3 heads = 12.561%.
- Motor-only is too broad, but Feb-Q75 motor edge (+6.2 motor2 / +7.2 motor3) + p3>=0.25 produced 133R / 47 heads = 35.338%.
- Wave36 overlap45; incremental outside Wave36 = 88R / 27 heads = 30.682%.
- Result commit `b7d5d0f9b3f6042976d8820771def4d89aa33278`.
- No Apr-Jun tuning; Jul/Aug unused; September unread; v288 unchanged.

## 2026-09-15 JST — Wave52 BEFORE WORK
- User approved drilling into Wave51's 88 incremental motor-first races outside Wave36 (27 boat3 heads / 61 misses).
- Preserve Wave51 candidate definition exactly: February-Q75 joint 3-vs-2 motor cuts (+6.2pt motor2, +7.2pt motor3) and p3>=0.25, then exclude the Wave36 March p3>=0.365448 subset.
- Do NOT optimize thresholds on the 27 vs 61 March outcomes. Use descriptive comparisons and bins/cuts derived from February distributions where possible.
- Compare hit vs miss pre-deadline structure: boat1 strength, boat2 wall/ST, boat3 national/local strength, boat3-vs-1 and boat3-vs-2 gaps, and motor-edge magnitude. Also inspect whether frozen conditional opponent ranking can capture the actual trifecta among the 27 heads.
- Goal: identify stable structural dimensions that could narrow the 88R pool while preserving useful volume, as a future independent motor-first 3HEAD family.
- March is research-exposed; Apr-Jun contaminated for this line; Jul/Aug NON-PRISTINE; September outcomes remain UNREAD. No production adoption from this work. v288 unchanged.
- Status: `WAVE52_STARTED_INCREMENTAL_88_HIT_MISS_STRUCTURE`.

## Exact restart point
- Execute Wave52 on the frozen Wave21 source, reproduce the exact 88R incremental pool, compare 27 heads vs 61 misses without outcome-fitted threshold search, then save result and AFTER handoff.