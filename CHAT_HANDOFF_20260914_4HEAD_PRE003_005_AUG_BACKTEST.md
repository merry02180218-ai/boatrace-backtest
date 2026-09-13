# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **CANONICAL WAKU10 HEAD4 7/18->7/19 RE-AUDIT IN PROGRESS**

## Frozen production
Production remains unchanged (`HEAD4_V291_COMP7`). July/August 2026 remain NON-PRISTINE; September remains outcome-blind for tuning/model selection.

## Correction to prior July 18->19 conclusion
The prior raw audit read only public BoatraceCSV `data/programs/waku10/YYYY/MM/DD.csv` through `rows()`. GitHub history confirms that a validated historical Waku10 restoration pipeline already exists (v233/v234) using direct BOATCAST historical `bc_j_waku10_*` data and restored replay. Therefore the public-schema break seen on 7/19 is a property of the un-restored public source, not necessarily of the intended historical input set.

## Permanent canonical Waku10 fix — COMPLETE
- Canonical materialization workflow: `.github/workflows/materialize-canonical-waku10.yml`.
- Retry Run `34778943467`, Job `103782266148`: SUCCESS.
- Restored Waku10 was generated, validated, committed and pushed to `main`.
- Canonical data commit: `fbf863c8d2b91d1232c60cdd55374b4e0d33dd8d` (`Materialize restored historical Waku10 canonically`).
- Coverage: 100% for every month from 2025-12 through 2026-08; 2026-07-18 = 180/180 rows, 2026-07-19 = 192/192 rows.
- Artifact `canonical-waku10-materialization`, ID `10324971412`, SHA256 `5fc79e7d91424024176b3066cf2f81f0506e9dfe03bcdc5a72a8501f7146e530`.
- Shared `rows()` loader now prefers repository-local `data/programs/waku10/...` before public BoatraceCSV, so models/audits transparently use canonical restored Waku10.

## Current work-start record — written BEFORE re-audit
Goal: invalidate or confirm the previous 7/18->7/19 feature-break conclusion using the now-canonical restored Waku10 source.

Plan:
1. Keep production unchanged and keep July/August NON-PRISTINE.
2. Re-run the existing HEAD4 7/18->7/19 primitive audit on current `main`, where `rows('data/programs/waku10/...')` must resolve to canonical restored local files.
3. Verify 7/18 and 7/19 both expose the same rich Waku10 schema and populated frame-specific/past-10 primitives.
4. Recompute and compare `inner12_resistance`, `wall3_weak`, `past_win4`, and `legacy_score4` across 7/18->7/19.
5. Determine whether the previously observed PRE collapse disappears, materially shrinks, or persists after lineage correction.
6. If the existing audit workflow does not trigger from canonical-data changes, make the minimum audit-only trigger/change needed and rerun; do not alter production logic.
7. Inspect successful CI artifact/results and record exact Run/Job/Artifact IDs, hashes, findings, and limitations.
8. AFTER completion update this handoff with corrected interpretation and next restart point.

## Restart protection
If interrupted, resume from canonical Waku10 HEAD4 7/18->7/19 re-audit. Do not use the old sparse-public-Waku10 conclusion for model decisions.
