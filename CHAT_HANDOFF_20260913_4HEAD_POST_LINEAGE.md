# CHAT HANDOFF — 2026-09-13 — 4号艇 POST feature lineage

Updated: 2026-09-13 JST
Repository: `merry02180218-ai/boatrace-backtest`
Priority: latest GitHub > older handoffs/chat memory.
Previous handoff: `CHAT_HANDOFF_20260913_4HEAD_LIVE_FEATURE_BUILDER.md`.

## Immutable rules

- Keep v291 race-entry logic unchanged.
- Adopted overlay remains `HEAD4_V291_COMP7_VARN_F4_N16`: original v291 Top4 composite >= 7.0, then largest N=4..16 with composite >= 4.0, exactly ¥10,000/race inverse-odds Dutch with ¥100 Hamilton rounding.
- Jul/Aug 2026 are NON-PRISTINE. Do not use outcomes for fitting/tuning/promotion.
- September 2026 remains strictly outcome-blind. Do not read results/payouts for fitting/tuning/evaluation.
- Missing/late/incomplete LIVE inputs fail closed. Never replace pre-deadline odds with closing/post-deadline odds.

## State inherited from previous handoff

- Variable-N overlay research is complete/adopted as an overlay; historical v291 itself is not rewritten.
- Generalized official `beforeinfo` result-blind acquisition layer is accepted; CI `34721199607` passed.
- Full one-click LIVE remains incomplete at exact current-day feature construction/parity.

## This run — POST 16-feature lineage/schema milestone

Goal: resume the stalled LIVE feature-construction research without changing v291 and without touching Jul/Aug/Sep outcomes.

Compared the frozen production artifact `artifacts/head4_v291_downstream_20260630.json` with the historical causal constructor in `analyze_v250_4head_rebuild_baseline.py`.

Important result: the entire frozen POST schema is now lineage-accounted for **16/16 in exact order**:

1. `legacy_score4`
2. `racer4`
3. `hist_st_edge_4v3`
4. `wall3_weak`
5. `inner12_resistance`
6. `motor4_2ren`
7. `motor4_hist`
8. `turnfoot4_prior`
9. `past_win4`
10. `ex_st_rank4`
11. `ex_st_4`
12. `ex_st_edge_4v3`
13. `orig_straight4`
14. `orig_lap4`
15. `orig_turn4`
16. `tilt4`

The first 9 come from the historical `pre_features(x,s4)` path. The final 7 come from historical `post_features(code,tkz,stt,orig)` and preserve the exact `rank_score`, ST edge, `original_scores`, and `tiltval` semantics rather than reimplementing them from memory.

Added:
- `artifacts/head4_post_feature_lineage_v1.json` — machine-readable source/formula/timing manifest for all 16 POST inputs.
- `verify_4head_post_feature_lineage.py` — fail-closed verifier that requires exact equality with the frozen POST feature order and proves all 16 names are present in the historical constructor.
- `.github/workflows/validate-4head-post-feature-lineage.yml` — CI syntax/schema/lineage/policy guard.

Commits:
- `ce07d643e399688c7dc8070f8ef86589b01d3fdf` — lineage manifest
- `9f0e79b00a63cfc0f239ef7b894ad3265e8638eb` — verifier
- `bd2c1863968995f7684aabe46404284f8ace9c81` — CI workflow
- `2ec4ccfa600812b781c3f1cf65bf8191894cea1f` — this handoff milestone

### CI result

Dedicated workflow `Validate 4-head POST feature lineage` run **`34723924296` completed SUCCESS** on 2026-09-13 JST. It passed syntax compilation, exact frozen POST schema/order verification, historical lineage checks, and the Jul/Aug NON-PRISTINE + September outcome-blind policy guard.

### Decision

**ACCEPT the POST lineage/schema manifest as a research artifact.**

Reason:
- it uses the exact frozen v291 downstream schema;
- it traces to the existing historical constructor instead of inventing feature formulas;
- it does not alter v291, v283, A-LIVE, the variable-N overlay, or bankroll allocation;
- it uses no Jul/Aug/Sep outcomes;
- the verifier explicitly does **not** claim current-day value parity;
- the dedicated CI is green (`34723924296`).

### Not yet accepted

A current-day POST LIVE builder is **NOT accepted yet**. The official `beforeinfo` snapshot still must be mapped to the historical ST/tilt semantics, and the availability/timing of the three original-exhibition values (`straight/lap/turn`) must be proven. Any unavailable field must fail closed; median/default substitution is not authorization to fabricate LIVE data.

## Next research step

1. Map official pre-result source fields to the 7 exhibition-side POST features and parity-test against Apr–Jun result-free fixtures.
2. Then repeat the same source-to-feature proof for ENV_ENTRY 25 inputs, A-LIVE 17 keys, v283 SECOND 5 rows and conditional THIRD 20 rows.
3. Only after exact value parity/schema completeness should these immutable inputs be fed to `run_4head_v291_varn_live.py`.

Current status: **important progress; POST lineage is fully identified 16/16 and dedicated CI is green, but one-click LIVE remains incomplete pending current-day value parity and downstream ENV/A/v283 lineage.**
