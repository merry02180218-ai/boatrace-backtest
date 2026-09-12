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

## POST 16-feature lineage/schema milestone

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
- `2ec4ccfa600812b781c3f1cf65bf8191894cea1f` — handoff milestone

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

## 2026-09-13 source-availability audit — official beforeinfo vs POST exhibition inputs

The official result-blind `beforeinfo` surface was audited against the seven exhibition-side POST features. No result/payout endpoint or September outcome was used.

### Important result

The central official `beforeinfo` page directly exposes enough pre-result source data for **4/7** POST exhibition features:

- `ex_st_rank4` — start-exhibition ST table exists; exact historical `rank_score` mapping still requires value parity.
- `ex_st_4` — boat-4 start-exhibition ST exists.
- `ex_st_edge_4v3` — boat-3 and boat-4 start-exhibition ST exist.
- `tilt4` — boat-4 tilt exists; exact historical `tiltval` semantics remain fixed.

But the same official central `beforeinfo` page does **not** expose the historical original-exhibition metrics required for:

- `orig_straight4`
- `orig_lap4`
- `orig_turn4`

Therefore the previous assumption that `beforeinfo` alone might complete all seven exhibition-side POST values is rejected. Those three fields remain **UNPROVEN_SOURCE_FAIL_CLOSED**. They must not be replaced by 0.5/defaults merely because historical constructors have fallback values; doing that would fabricate a current-day LIVE input and break production parity.

Added:
- `artifacts/head4_post_live_source_audit_v1.json`
- `verify_4head_post_live_source_audit.py`
- `.github/workflows/validate-4head-post-live-source-audit.yml`

Commits:
- `9b038f75af598ddbf4eba0fcdbea0ae9434060ac` — source audit manifest
- `e2a356528cee61fc6c878d4f0a0c15fa9ceb66b7` — fail-closed verifier
- `43035c631db2bdf3331f368b5b637fc399de8a7c` — dedicated CI workflow
- `7166544631f6724a1b88c68a7e6b5ad3e754e1d3` — exact historical feature-order correction only; no semantics changed

### CI result

- First dedicated run `34726307714`: **FAILURE** because the audit JSON key order put `tilt4` before the three original-exhibition fields; syntax passed and the failure was the verifier's exact-order guard, not a scientific/policy failure.
- Corrected only the manifest key order to match frozen/historical POST order in commit `7166544631f6724a1b88c68a7e6b5ad3e754e1d3`.
- Corrected dedicated run **`34726340979` completed SUCCESS** on 2026-09-13 JST, proving exact audit schema/order plus fail-closed classifications and policy guard.

### Decision

**ACCEPT the source-availability classification as research evidence; DO NOT accept a complete current-day POST builder yet.**

Reason:
- source availability is proven without touching outcomes;
- v291/v283/A-LIVE/variable-N semantics are unchanged;
- missing original-exhibition fields are explicitly fail-closed rather than imputed/fabricated;
- exact ST numeric representation (including F-start handling) and Apr–Jun parity still must be demonstrated before feeding these values into frozen inference;
- corrected dedicated CI is green (`34726340979`).

## Not yet accepted / current blocker

A current-day POST LIVE builder is **NOT accepted yet**.

Remaining work now narrows to:
1. Prove exact official-beforeinfo -> historical `stt` numeric mapping, including F-start representation, on Apr–Jun result-free fixtures.
2. Identify and prove a pre-result causal source for original-exhibition straight/lap/turn values. If no source can be proven for a target venue/race, production must fail closed for that target.
3. After complete POST parity, repeat source-to-feature proof for ENV_ENTRY 25 inputs, A-LIVE 17 keys, v283 SECOND 5 rows and conditional THIRD 20 rows.
4. Only after exact value parity/schema completeness feed immutable inputs to `run_4head_v291_varn_live.py`.

Current status: **important new result: official central beforeinfo covers 4/7 exhibition-side POST inputs, while original-exhibition 3/7 remain source-unproven and are now explicitly fail-closed. Corrected dedicated CI is green. v291 remains unchanged.**
