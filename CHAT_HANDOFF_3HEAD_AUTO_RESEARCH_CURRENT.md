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



---
# 2026-09-23 AFTER — 3HEAD layered research handoff

## Current architecture / user decisions
- CORE: strict v288 high-precision layer; keep untouched. Historical fixed CORE(S) reference 58R/34 heads = 58.62%, ROI 180.75%.
- A+.60 / EXPANDED: independent expansion layer; PLAYER_HISTORY research applies here without weakening CORE.
- FULL_3V2: further PLAYER_HISTORY-based expansion candidate, especially outside A+.60.
- Priority remains CORE > A+.60 > FULL_3V2. Do not merge them as equal-quality bets.
- Opponent/ticket families remain separate: CORE native v242-style variable Top5–Top10 / 5–10-ticket Dutch; A+.60 uses V221 Top6 + protected SECOND4 .50 exact-six. On overlap CORE priority.
- Formal v288 reference remains 94R/52 heads=55.32%, payout 1,622,070 yen, ROI about 172.6% at 10,000/race, Feb-Aug 2026; Jul-Aug NON-PRISTINE.

## PLAYER_HISTORY evidence carried forward
- Shared 30 causal prior-only features = 6 boats x {all_win, all_p2, frame_win, frame_p2, recent_p2}.
- Leakage/parity audit Run 35597225826 / Job 106324736532 / Artifact 10637383105: 23,855 races, 715,650 cells, 0 mismatches, same-day results not used, September outcomes not read.
- 3HEAD v1 Run 35667249381: SAFE_WAKU_BASE 37.70% vs PLUS_3V2 38.62% at equal 1849 volume.
- v2 Run 35670403984: FULL_3V2 714/1849=38.62%; signal distributed rather than one hard all_p2 gate.
- v3 Run 35681239039: COMPACT best probability-quality metrics; FULL_3V2 best selected head rate.
- v4 Run 35684918290: fixed same-volume SAFE_WAKU_BASE 37.70% vs FULL_3V2 38.62%; broad safe-Waku comparison, not formal v288 integration.

## A+.60 baseline and FULL curve
- A+.60 Run 35691601014, Nov-Feb: Nov 30/12=40.0%, Dec 40/17=42.5%, Jan 48/25=52.08%, Feb 32/12=37.5%, combined 150R/66=44.0%. CORE unchanged, A+.60 frozen, September unread.
- FULL curve Run 35694254012: Dec expansion worse; Jan FULL 30R/17=56.67%, 40R/21=52.5%, then degrades; Feb 30R/12=40%, max 39R/15=38.46%. Nov coverage issue.
- Jul-Aug Run 35730161624: July A+.60 39/17=43.59%, FULL max 47/20=42.55%, pure increment +8/3=37.5%. August A+.60 39/15=38.46%, FULL max 51/19=37.25%, pure increment +12/4=33.33%.
- Increment diagnostic Run 35765463293: PRE high half was 50% in both Jul and Aug; motor/PLAYER_HISTORY relative directions were unstable across months.
- PRE stability Run 35780077673: simple global PRE thresholds .925-.98 were not robust; next gate should be multivariate/good-vs-bad regime, not PRE-only.

## This chat — monthly BET audit
- User asked actual monthly BET counts after overlap removal.
- Created research/run_3head_three_layer_monthly_bets_v7.py and workflow research-3head-three-layer-monthly-bets-v7.yml.
- Initial script commit d16c57ac2d135bb1ee1d5f1c6d703227d4bdbc5e; workflow commit 65021f8f1546d2899a3b8b14d7f6c7f85e9025c9.
- Failure 1: Run 35817551282 / Job 107042229297, UnboundLocalError from local variable ov shadowing imported module. Fixed commit 2f1d35ded9fc267c60b8fa48efb15fcc5040e562.
- Failure 2: Run 35821784279 / Job 107054988626, FileNotFoundError because analysis_v243_3head_expand_feature_audit.csv is generated and not committed in main.
- Fix: removed unavailable generated v288 CSV dependency from this Jul/Aug audit. Script commit c52b0b73d1bb1b14260aa957e999d1cd552fb948; workflow commit 389fc5fa33045b143fd7302b55f333fb4d76cc60.
- IMPORTANT: v7 therefore does NOT provide exact CORE overlap. CORE_PRIORITY=0 in v7 is a placeholder and must never be interpreted as CORE having zero races.
- Successful Run 35841968448 / Job 107118918132 / SHA 389fc5fa33045b143fd7302b55f333fb4d76cc60 / Artifact 10742158507 / digest sha256:b79e173f042d703fe1e9ed197287becc456bbef40a31588911371e53803fa963.
- Markers: THREE_LAYER_MONTHLY_BETS_V7_OK, SEPTEMBER_UNREAD, PRODUCTION_UNCHANGED.
- Exact A+.60->FULL Jul/Aug results: July 39R/17 A+.60 + 8R/3 FULL pure add = 47R/20=42.55%. August 39R/15 + 12R/4 = 51R/19=37.25%. Max-expansion reference average ~49R/month.

## Current interpretation / latest user decision
- Naively unioning every layer at equal status is expected to lower aggregate head rate because marginal FULL is weaker than CORE. Keep layered architecture.
- User explicitly observed: if expansion races do not overlap CORE, thresholds can be raised to improve head probability. This is the agreed next research direction.
- CORE must stay frozen. Tighten only non-CORE expansion populations; accepting fewer added races is fine if head rate/ROI improves.
- Discussion target for FULL pure-add was roughly 40–45%+ head rate as a research objective, NOT a precommitted production acceptance threshold.

## NEXT ACTION — highest priority
1. Reconstruct exact CORE membership from reproducible committed/raw inputs; do not depend on missing generated analysis_v243_3head_expand_feature_audit.csv.
2. Build same-period audit, preferably Feb-Aug: CORE independently, A+.60 independently, FULL independently.
3. Pure sets: CORE; A60_PURE=A60-CORE; FULL_PURE=FULL-CORE-A60; TOTAL=union. Settle head outcome independently for every union code.
4. Preserve CORE priority and both frozen opponent/ticket families. Jul-Aug remain NON-PRISTINE; September 2026 stays UNREAD.
5. Then optimize thresholds ONLY on non-CORE expansion populations, especially FULL_PURE and optionally A60_PURE. Test PLAYER_HISTORY + PRE + motor/exhibition jointly; do not rely on PRE-only.
6. Report monthly pure-add R, heads/head rate, overlap, ticket hit rate, payout/ROI by frozen layer settlement, and combined layered ROI. Prefer robust cross-month behavior; no production change before holdout + leakage/parity audit.

## Process rules
- Before every workflow: refetch committed workflow + all used scripts, inspect full files, py_compile/AST, verify paths/dependencies, no malformed literal backslash-n, September unread, no result-derived Waku leakage.
- On failure inspect root cause, fix, refetch, full preflight, then rerun; never blind rerun.
- Never claim fired/completed without GitHub verification. Fresh workflow_dispatch may require user to click Run workflow.
