# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **FIXED AUGUST INPUT / TRAINING-ONLY WAKU10 AUDIT IN PROGRESS**

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

## Canonical Feb-Aug reruns — COMPLETE
- Common frozen Jan-31 model: Run `34781257580`, Job `103788567081`: SUCCESS.
  - Artifact ID `10325587160`, SHA256 `3032d71a7bf7c7f08abc417c94478215e6192cb7fc8994ca2d334d627b154b32`.
  - PRE .03-.05: Feb 609/20=3.28%, Mar 740/24=3.24%, Apr 743/12=1.62%, May 817/24=2.94%, Jun 716/29=4.05%, Jul 872/27=3.10% NON-PRISTINE, Aug 843/29=3.44% NON-PRISTINE.
- Rolling fit cutoff rerun: Run `34781279884`, Job `103788629685`: SUCCESS.
- Regime drift rerun: Run `34781297306`, Job `103788675802`: SUCCESS.
- Production unchanged.

## Important correction / open question
User correctly noted that July/August Waku10 already existed historically, so August raw target inputs should not materially change merely because canonical historical Waku10 was materialized. The corrected Jan-31 frozen model can still change because its Dec-Jan training features changed after historical Waku10 restoration. This needs a direct controlled audit rather than inference.

## CURRENT WORK-START RECORD — written BEFORE implementation
Goal: isolate the effect of TRAINING-period Waku10 restoration while holding August 2026 target features exactly fixed.

Exact plan:
1. Build an audit-only script; production code/thresholds remain untouched.
2. Construct one single canonical August 2026 feature matrix and freeze it in memory. Use exactly the same target rows/features for both model variants.
3. Fit two Jan-31 PRE models on the same Dec-2025 through Jan-2026 race labels:
   - `CANONICAL_TRAIN`: local restored canonical Waku10 for training.
   - `PUBLIC_ONLY_TRAIN`: bypass local canonical Waku10 only for training-period Waku10 reads and fetch the public BoatraceCSV historical path, reproducing the old sparse lineage as closely as currently available. No imputation/fabrication.
4. Verify training race codes/labels are identical between variants and report which raw/derived training features differ, including missing/default shares.
5. Score the exact same frozen canonical August matrix with both fitted models. Compare PRE mean/median, PRE-bin counts, PRE .03-.05 membership overlap, entries gained/lost, and 4-head descriptive hit rates. July/August remain NON-PRISTINE; outcomes are descriptive only.
6. Also report model coefficient/scaler shifts so we can identify which restored training features move the PRE scale.
7. Fail closed if public-only training source cannot be reconstructed or if August target feature hashes differ between variants.
8. Run CI, inspect logs/artifact, fix automatically on audit errors.
9. AFTER completion update this handoff with Run/Job/Artifact IDs/hash, exact controlled results, conclusion, production status, and restart point.

## Restart protection
If interrupted, resume from fixed-August-input / training-only Waku10 controlled audit. Do not attribute August changes to target Waku10 unless the fixed-input audit proves it.
