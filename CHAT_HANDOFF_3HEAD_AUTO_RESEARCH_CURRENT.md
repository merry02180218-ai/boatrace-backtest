# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research version: `v289-addon-wave1`
- decision: **NO_ADOPTION_WAVE1**
- v288 production is unchanged; baseline replay assertion is 94R / 52 hits / payout 1,622,070 yen.
- July/August are NON-PRISTINE. September outcomes were not loaded or used.
- Candidate universe is only v288 final NO_BET among operational PRE S/A and v242-buyable races.

## Wave-1 result
- candidate pool: 178 races
- best tested variant: `return_rank@0.45`
- best add-on: 84R / 15 hits / ROI 54.92% / profit -378,700 yen
- combined: 178R / ROI 117.04%

## Methods tested / dead ends retained
- `residual_hit`: prior-reject outcome effect ranking over pre-race safe features.
- `exhibition_upgrade`: current exhibition/ST/original-exhibition family only.
- `return_rank`: prior-reject realized-return ranking trained only on prior months.
- `attack_style_split`: separate stretch-vs-turn regimes, then outcome ranking.
- `orthogonal_consensus`: residual + exhibition + return independent-score consensus.
- `ev_calibrated`: residual hit score plus current composite odds, alpha chosen on prior months only.

## Real-operation audit
- all scoring inputs are columns already present before settlement in the canonical v243/v288 audit artifact;
- decisions use only prior-month outcomes for fitting; current test-month result/payout enters settlement only;
- missing features are median-imputed from prior training; production promotion must replace any required-current missingness with fail-closed gates;
- overlap with v288 baseline is zero by construction;
- no production workflow/model was changed.

## Next restart point
- If no wave-1 variant passes, next research must change the information/ticket family rather than loosen v288 thresholds.
- Priority next: opponent/ticket re-ranking on NO_BETs, PRE-B/new-population research with full leak audit, and venue/field archetype residual models.
- Before any promotion, build live shadow scorer with fail-closed source checks and exact 10,000-yen Dutch.

## Generated artifacts
- `research_v289_3head_addon.json`
- `research_v289_3head_addon.md`



## 2026-09-22 — AFTER: PLAYER_HISTORY 3-vs-2 component ablation v2 SUCCESS
- Run 35670403984 / Job 106565354725 / Artifact 10671018125 / head 57044cc293865b03dd0e186a4e5af2d645c41b84.
- Cache saved: v234-restored-waku10-20251201-20260831-v1 (future related runs can skip Waku materialization).
- Equal-volume Mar-Aug, 1849 selected:
  - BASE 697 = 37.70%
  - FULL_3V2 714 = 38.62% (+17 heads, +0.92pp)
  - REL32_ALL 712 = 38.51%
  - OWN3_B2 712 = 38.51%
  - OWN3_REL32 710 = 38.40%
  - B2_REL32 706 = 38.18%
- Best single/atomic selected-head result: OWN3_frame_win 708 = 38.29%; TRIO_frame_win 709 = 38.35%. REL32_all_win / all_p2 each 706/705. recent_p2 and frame_p2 weak.
- Important: unlike 4HEAD, raw all_p2 alone is not the main 3HEAD driver. The useful signal is distributed, with 3-vs-2 relative bundle and boat3 frame-win especially useful.
- Pristine Mar-Jun FULL_3V2 monthly: 41.10%, 43.02%, 35.40%, 38.33%; BASE 40.13%,42.25%,35.10%,36.59%. Improvement in all four pristine months.
- Jul/Aug descriptive only: FULL_3V2 36.73%,38.12% vs BASE 34.01%,38.67%.
- September UNREAD; production unchanged; no hard gate / no threshold tuning.
- Next: independent falsification of compact bundles (REL32_ALL, OWN3_B2, FULL_3V2, compact frame_win + relative all_win/all_p2) using fixed same-volume rules; then freeze candidate and test CORE/A+.60 membership + settlement ROI.


## 2026-09-22 — START: PLAYER_HISTORY compact falsification v3
- Continue from v2 Run 35670403984.
- Goal: falsify/confirm the apparent 3-vs-2 gain before CORE/A+.60 integration.
- Fixed candidates only (no search): BASE, REL32_ALL, OWN3_B2, FULL_3V2, COMPACT = boat3 frame_win + rel32 all_win + rel32 all_p2.
- Primary evidence: pristine Mar-Jun only; Jul-Aug descriptive only.
- Same monthly volume as BASE p>=.30; no threshold tuning, no hard gate.
- Add leave-one-pristine-month-out stability summary and delta-vs-BASE.
- September outcomes UNREAD; production unchanged.


## 2026-09-22 — AFTER v3 / START: FULL_3V2 CORE/A+.60 same-universe integration
- v3 success: Run 35681239039 / Job 106598437891 / Artifact 10675351417.
- Fixed FULL_3V2 remains strongest selected head-rate candidate: 1849R/714 = 38.62% vs BASE 1849/697 = 37.70%.
- Pristine Mar-Jun FULL_3V2 beats BASE in all four months.
- Next experiment freezes FULL_3V2 membership logic; no further feature/threshold search.
- Apply BASE vs FULL_3V2 to the current CORE/A+.60 same-universe structure and measure membership changes, head capture, ticket/capture diagnostics and settlement ROI only from available historical closing odds.
- September outcomes remain UNREAD. Jul/Aug descriptive only. Production unchanged until integration audit passes.


## 2026-09-22 — START: A+.60 + PLAYER_HISTORY expansion research
- User decision: keep v288 CORE as the high-precision anchor; focus PLAYER_HISTORY research on the independent A+.60 / EXPANDED side.
- Goal: increase total buyable race count without unnecessarily weakening CORE.
- Freeze CORE semantics. Do not tune CORE thresholds in this phase.
- Add audited causal PLAYER_HISTORY to A+.60 ranking/gating research, starting with the proven FULL_3V2 family (boat3 + boat2 + 3-minus-2 relatives).
- Evaluate fixed race-count / head-rate curves for expanded side before settlement ROI; avoid choosing a single threshold from Jul/Aug outcomes.
- Primary evidence remains cleaner pre-Jul window; Jul/Aug descriptive NON-PRISTINE only. September outcomes remain UNREAD.
- Production unchanged until independent validation and settlement audit pass.
