# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **CANONICAL WAKU10 HEAD4 FEB-AUG FULL RE-RUN STARTED**

## Frozen production
Production remains unchanged (`HEAD4_V291_COMP7`). July/August 2026 remain NON-PRISTINE; September remains outcome-blind for tuning/model selection.

## Permanent canonical Waku10 fix — COMPLETE
- Canonical materialization workflow: `.github/workflows/materialize-canonical-waku10.yml`.
- Retry Run `34778943467`, Job `103782266148`: SUCCESS.
- Canonical data commit: `fbf863c8d2b91d1232c60cdd55374b4e0d33dd8d`.
- Coverage: 100% every month 2025-12 through 2026-08.
- Artifact ID `10324971412`, SHA256 `5fc79e7d91424024176b3066cf2f81f0506e9dfe03bcdc5a72a8501f7146e530`.
- Shared rows loader prefers repository-local canonical `data/programs/waku10/...`.

## Canonical 7/18->7/19 re-audit — COMPLETE
- Run `34780264422`, Job `103785870696`: SUCCESS.
- Artifact `head4-jul18-19-primitives`, ID `10325316297`, SHA256 `bc43dae403b4838bd349528811e22cd478047b9db0d81036f9838ca1e4f23659`.
- Rich Waku10 schema is populated on both days; schema additions/removals = 0/0.
- Corrected 7/18 -> 7/19 changes: legacy_score4 36.381158 -> 36.283451 (-0.097707), resistance12 .720583 -> .699611 (-.020972), wall3_weak .208704 -> .195410 (-.013294), past_win4 .098148 -> .093866 (-.004282).
- Therefore the old huge 7/19 discontinuity was caused by sparse public Waku10 lineage and is INVALID for model/regime decisions.

## CURRENT WORK-START RECORD — written BEFORE implementation/run
Goal: recompute the key HEAD4 February-August diagnostics with canonical restored Waku10 and determine whether the August anomaly/low-PRE behavior remains.

Exact plan:
1. Fetch current implementations/workflows for common frozen-scale, rolling fit-cutoffs, regime drift/day-boundary, and PRE .03-.05 analyses; ensure they resolve canonical local Waku10 through the shared loader.
2. Re-run the common frozen-scale February-August distribution/performance comparison under one fixed causal model.
3. Re-run rolling causal fit cutoffs through 2026-06-30, with 2026-07-31 diagnostic-only, to test whether August recentering/collapse survives corrected Waku10.
4. Re-run outcome-independent regime/day-boundary diagnostics to remove the false sparse-public-Waku10 discontinuity.
5. Recompute PRE .03-.05 counts and 4-head performance for pristine Feb-Jun and descriptive NON-PRISTINE Jul-Aug. No July/August tuning or production selection.
6. September outcomes remain unused/outcome-blind. Production `HEAD4_V291_COMP7` remains unchanged.
7. Inspect CI logs/artifacts. Fix and rerun automatically if any audit error occurs.
8. AFTER all required runs complete, update this handoff with exact Run/Job/Artifact IDs/hashes, corrected numbers, which old conclusions survive/disappear, production status, and restart point.

## Restart protection
If interrupted, resume from canonical-Waku10 HEAD4 Feb-Aug full rerun. Never reuse pre-canonical Waku10 results for model decisions.
