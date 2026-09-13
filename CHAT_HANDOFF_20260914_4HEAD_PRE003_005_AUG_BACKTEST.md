# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **CANONICAL HISTORICAL WAKU10 MATERIALIZATION IN PROGRESS**

## Frozen production
Production remains unchanged (`HEAD4_V291_COMP7`). July/August 2026 remain NON-PRISTINE; September remains outcome-blind for tuning/model selection.

## Correction to prior July 18->19 conclusion
The prior raw audit read only public BoatraceCSV `data/programs/waku10/YYYY/MM/DD.csv` through `rows()`. GitHub history confirms that a validated historical Waku10 restoration pipeline already exists (v233/v234) using direct BOATCAST historical `bc_j_waku10_*` data and restored replay. Therefore the public-schema break seen on 7/19 is a property of the un-restored public source, not necessarily of the intended historical input set.

## User-requested permanent fix — work-start record written BEFORE implementation
Goal: eliminate the possibility that future models/audits accidentally read sparse historical Waku10 when validated restored Waku10 exists.

Plan:
1. Keep production model/rules unchanged.
2. Reuse the already validated v233/v234 BOATCAST historical restoration parser and source policy; do not invent a new Waku10 definition.
3. Materialize the restored historical Waku10 into the canonical repo path `data/programs/waku10/YYYY/MM/DD.csv` for the historical range covered by the restoration pipeline, rather than keeping it only under an audit-specific directory.
4. Change the shared `rows()` loader so repository-local `data/programs/waku10/...` is preferred automatically before the public BoatraceCSV URL. This makes every old/new model that calls `rows('data/programs/waku10/...')` transparently use the restored canonical copy.
5. Add an idempotent workflow that rebuilds/restores Waku10 and commits only changed canonical files, with `contents: write`; published rich Waku10 remains verbatim where already complete, missing/sparse historical days are replaced by validated BOATCAST reconstruction.
6. Validate coverage/schema before commit: race-code uniqueness, expected Waku10 columns, row counts, and no regression on already-rich dates.
7. Run CI/materialization and verify actual files exist in the canonical repo path.
8. Re-run the HEAD4 7/18->7/19 primitive audit using the canonical path to confirm the false source-boundary disappears or is materially reduced.
9. AFTER completion update this handoff with commits, Run/Job IDs, files/coverage, artifact/hash, corrected interpretation, limitations, and restart point.

## Existing validated restoration lineage to reuse
- `analyze_v234_3head_waku10_restored_replay.py`
- v234 uses published Waku10 verbatim where available, reconstructs missing historical Waku10 from BOATCAST raw files, and validates the parser against a published August day.
- Relevant historical commits include `09edebd3727bdf75f2ce4fef9ce24585530af355` and `f00b4afb44de818e9966425df99bfe1d01ec3e25`.

## Restart protection
If interrupted, resume from canonical Waku10 materialization. Do not continue HEAD4 model interpretation until the shared canonical Waku10 source is fixed and the 7/18->7/19 audit is rerun.
