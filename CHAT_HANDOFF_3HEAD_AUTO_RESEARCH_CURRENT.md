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

## 2026-09-21 — 3HEAD opponent protected Top6 freeze (BEFORE FEB OUTCOME REVEAL)

### Frozen upstream gates
- HEAD: adopted A gate.
- Purchase: `post_motor_inner_rank_edge >= +0.60`.
- Opponent baseline: V221 direct ordered-pair ranking.
- Development opponent evaluation: Dec 2025 + Jan 2026 only, 41 boat3-head wins.
- Nov role split: cold-start / not evaluated.
- February outcomes: **UNREAD FOR OPPONENT RULE AT FREEZE**.
- March outcomes: **UNREAD / ONE-SHOT RESERVED**.
- September 2026 outcomes: **UNREAD**.

### Frozen candidate opponent rule
Exactly 6 tickets:
1. Start from V221 ordered-pair Top6.
2. Read pre-settlement 4号艇 turn metric `vh_p12_turn`.
3. If `turn4 >= 0.50`, find the highest V221-ranked `3-4-X` pair outside Top6.
4. Protect every existing Top6 `3-4-X`; never drop one.
5. Among Top6 tickets whose SECOND is not 4, drop the weakest / lowest V221-ranked slot.
6. Insert the selected `3-4-X`. Keep exactly six tickets.
7. If no promotable `3-4-X` or no droppable non-4 SECOND slot exists, leave V221 Top6 unchanged.

### Frozen development evidence
- V221 baseline Top6: 25/41 = 60.98%.
- Protected turn4>=0.50: 29/41 = 70.73%.
- rescued +5 / lost -1 / net +4.
- 0.45 and 0.50 were identical on development; **0.50 is frozen as the more conservative candidate**.
- No further threshold tuning from February is permitted if February is consumed as forward validation.

### Pre-FEB availability audit
- Run 35547462348 / Job 106175856772: SUCCESS.
- Nov/Dec/Jan selected counts = 30/40/48; frozen total remains 118.
- February selected codes = 32; feature rows = 32.
- February outcomes were not used for opponent-rule selection in this audit.
- March used=false; September 2026 used=false; odds used=false.

### Freeze provenance
- Candidate implementation file: `research/run_3head_a_opponent_rolesplit_dev.py`.
- Candidate implementation content SHA at freeze: `ed5db03cf26c1998a74199a4a2bb8543528733be`.
- Latest syntax/cohort-audit fix commit before freeze: `4614fd6e29a5c3a1d8e59e9444db14c569e93121`.
- Successful pre-FEB audit trigger: `e65b41b51dca787444d2a58e7fa7aa4fbb57808d`.

### Next action
Build a **separate one-shot February validation path**. Do not tune thresholds/features using February. Apply the frozen rule first from pre-settlement features, then attach February settlement only for scoring. Do not touch March.

## MANDATORY OPERATING RULE — NEVER TRIGGER BEFORE FULL PREFLIGHT
This is a permanent rule for this project and must be followed by every continuation/chat/agent.

**Do not patch and immediately trigger GitHub Actions.**
Before every trigger/rerun, inspect the fresh latest files and verify the complete execution path, not only the line that failed.

Required pre-trigger audit:
1. Python syntax/compile for the target script and directly imported local modules.
2. Confirm every imported module/file exists at its real repository path.
3. Inspect called-function contracts and hidden input requirements (required dict keys/months, columns, return shapes, types).
4. Trace the execution path through all stages that occur before settlement/result reveal.
5. Validate month/data scopes and frozen cohorts; ensure no unintended March or September-2026 outcome access.
6. Validate V221 ordering types/format and protected fixed-six replacement logic.
7. Validate JSON/CSV output construction and artifact paths.
8. Check workflow YAML, trigger path, dependencies, timeout and artifact upload behavior.
9. Inspect adjacent failure risks exposed by the previous error; never fix only the first exception.
10. Only after the above audit passes may a trigger commit be created.
11. After a run, verify actual Job/log/artifact/race-level output before claiming success.

For one-shot/holdout validation, a failed run that does not reach settlement does NOT consume the holdout. Record whether settlement was reached.

### Current Feb one-shot status
- Run 35550024261 failed in preflight due to an incorrect assumed V221 file path; settlement not reached.
- Run 35550190379 passed workflow preflight but failed before cohort scoring because `make_pre_scores()` requires frames for oct/nov/dec/jan/feb and the one-shot script supplied only feb.
- Run 35550190379 therefore did **not** reach February settlement; February outcomes remain unrevealed by this validation path.
- Next action: perform the mandatory full execution-path audit first, then patch. Do not trigger until that audit is complete.

## FEB ONE-SHOT RESULT — SUCCESS (2026-09-21)
Run 35555440389 / Job 106198082962 / Artifact 10620315572 / head 460c5c01ca90070bf02041d284b385aa7d62a47b.
Strict preflight SUCCESS; one-shot SUCCESS; artifact SUCCESS.
Frozen pre-settlement cohort: 32 races. Decisions were frozen before February settlement; 13 protected swaps.
February settlement: 32/32; boat3 wins 12.
V221 baseline Top6: 6/12 = 50.00%.
Protected SECOND=4 / turn>=0.50 fixed-six: 6/12 = 50.00%.
rescued=0, lost=0, net=0.
Therefore the protected rule's Nov-Jan development lift (25/41 -> 29/41) did NOT forward-replicate in February; it was neutral, not harmful, on this holdout.
Do not tune threshold or rule using February. February is now READ and must never again be treated as pristine holdout.
March remains UNREAD and reserved as final one-shot only. September 2026 remains UNREAD.
Before any March trigger, mandatory full preflight/audit rule above applies.

## 2026-09-21 — Decision after February forward validation
Do **not** tune the protected rule from February. The frozen candidate remains exactly turn4>=0.50 / protected SECOND=4 / fixed six if it is taken to March.
Evidence available without opening March:
- development Dec-Jan: baseline 25/41 (60.98%) -> protected 29/41 (70.73%), net +4.
- February forward: baseline 6/12 (50.00%) -> protected 6/12 (50.00%), net 0; 13 swaps.
- combined descriptive Dec-Feb (NOT a new tuning sample): baseline 31/53=58.49%, protected 35/53=66.04%, net +4.
Interpretation: February did not reproduce the development lift, but it also produced no protected-rule damage. Evidence is therefore weaker than the Dec-Jan development result and not sufficient to justify changing the frozen rule.
Next research action before any March reveal: build/inspect a March **pre-settlement-only dry run** that freezes the March cohort and all six-ticket decisions, validates invariants and writes a prediction artifact WITHOUT loading March settlement. Only after that dry run succeeds and is audited may the separate March settlement one-shot be triggered. March threshold/features must remain unchanged.

## 2026-09-21 — March dry-run PRETRIGGER audit
March settlement remains UNREAD. Added dedicated dry-run script and workflow, but trigger is intentionally withheld until workflow/static contracts are audited.
Leak firewall:
- March PRE uses build_pre_enhanced(..., False), so no March result rows.
- PRE training labels end Feb-28.
- Motor state is reconstructed through Feb-28 and then frozen; March fetch kinds exclude results/realtime.
- V221 historical fit labels end Feb-28.
- V221 day_fetch is wrapped so dates >= 2026-03-01 force res=[].
- March cards/tkz/stt/original_exhibition may be read because they are pre-settlement inputs.
- March settlement and September-2026 outcomes remain unread.
Workflow commit: 5f99fe39331de1bdbc442af119fe89af030d8fbc.
Do not trigger until final fresh-file audit passes.

### March dry-run failed-run audit / strengthened firewall
Run 35556371118 / Job 106200674093 failed before March settlement access: AttributeError on nonexistent w20.choose_features. No artifact. March remains UNREAD.
Follow-up static audit found and fixed nonexistent w20.pct_ref reference.
Critical firewall fix: previous wrapper called original V221 day_fetch before clearing res, which could still request March result files. Commit 4d66a4ae749e61bd3594f96727e538a2e0823a4d now bypasses original day_fetch entirely for dates >= 2026-03-01 and directly requests cards/tkz/original only with res=[].
Workflow preflight strengthened in eec4c7e9d5aac9682f92ceaad6aa35d61a587ffc. Do not claim March UNREAD after any future run unless logs/code confirm this firewall was the executed revision.

### March pre-settlement dry-run SUCCESS / predictions frozen
Run 35557725947 / Job 106204537001 / Artifact 10621281342 SUCCESS. Executed head SHA 840611614c76e9f5a09788b33dfb9121c5b0207b.
Artifact audit: 33 selected races / 33 decisions / 18 protected swaps. Every base and protected ticket set has exactly 6 unique tickets. Policy says dry_run_only=true, threshold=.50, tickets=6, march_settlement_loaded=false, sep2026_loaded=false. Recursive artifact audit found no actual/result/hit/ROI/payout/odds fields; only the policy key march_settlement_loaded contains a settlement-related word.
March predictions are now FROZEN in Artifact 10621281342. Do not alter threshold/features/ticket replacement before March one-shot settlement. March remains UNREAD at this point.
Next: build a separate settlement-only evaluator that consumes the frozen artifact decisions and March official outcomes, without recomputing predictions. Preflight must verify artifact/prediction identity before revealing outcomes.

### March one-shot settlement SUCCESS / opponent rule evidence update
Run 35559071435 / Job 106208304825 / Artifact 10621551141 SUCCESS; head SHA 32cddc1ecffcdc41c6a839f25129ef7dd1939593. Frozen predictions verified against Artifact 10621281342: n=33, swaps=18, threshold=.50. March settlement coverage 33/33. boat3 wins=15. V221 base Top6=10/15=66.67%; protected Top6=11/15=73.33%; rescued=1, lost=0, net=+1. March is now READ and must never again be described as pristine/UNREAD. Sep-2026 remains UNREAD.

Descriptive combined evidence for the already-frozen rule (no retuning):
- Dec-Jan development: base 25/41=60.98%, protected 29/41=70.73%, net +4.
- Feb one-shot: base 6/12=50.00%, protected 6/12=50.00%, net 0.
- March one-shot: base 10/15=66.67%, protected 11/15=73.33%, net +1.
- Feb+March forward only: base 16/27=59.26%, protected 17/27=62.96%, net +1.
- Dec-Mar descriptive total: base 41/68=60.29%, protected 46/68=67.65%, net +5.
Do not threshold-tune on Feb or March after reveal. Preserve threshold=.50 protected SECOND=4 fixed-six rule as the frozen candidate. Next research should audit the single March rescue and combined lost/rescued structure, or move toward production shadow validation without using Sep-2026 outcomes.

