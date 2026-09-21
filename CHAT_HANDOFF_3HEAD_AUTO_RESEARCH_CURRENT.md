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



## 2026-09-22 — AFTER: PLAYER_HISTORY shadow v1 SUCCESS
- Workflow: research-3head-player-history-shadow-v1
- Run: 35667249381
- Job: 106555642663
- Artifact: 10670660826
- Run head SHA: d45172b9e64e081030dcec5fc6ac9a4e0f31c4c4
- SUCCESS. Existing 30 PLAYER_HISTORY columns were present and reused.
- Guards: strict prior-date PLAYER_HISTORY; September outcomes UNREAD; production unchanged; no threshold tuning.
- Equal-volume aggregate Mar-Aug (1849 selected each):
  - SAFE_WAKU_BASE 697/1849 = 37.70%, AUC .7216
  - PLUS_OWN3 701/1849 = 37.91%, AUC .7224
  - PLUS_3V2 714/1849 = 38.62%, AUC .7232  <-- strongest head-rate result
  - PLUS_3V4 705/1849 = 38.13%, AUC .7228
  - PLUS_ALL30 708/1849 = 38.29%, AUC .7232
- PLUS_3V2 gain vs BASE: +17 heads at same 1849 races, +0.92 percentage point head rate. It also improves Brier .10331 -> .10316 and LogLoss .34872 -> .34810.
- Monthly PLUS_3V2: Mar 41.10%, Apr 43.02%, May 35.40%, Jun 38.33%, Jul 36.73%, Aug 38.12%. Jul/Aug remain NON-PRISTINE descriptive shadow.
- Interpretation: 4HEAD lesson transfers: PLAYER_HISTORY is useful as a model/ranking feature, especially boat3 + boat2 wall relationship; all-30 does not beat targeted 3-vs-2 set. Do NOT hard-gate yet.
- Next: isolate the 3-vs-2 PLAYER_HISTORY components/relative features, test stability on pristine months and then apply to the current dual-head CORE/A+.60 same-universe experiment; settlement ROI only after membership is frozen.
