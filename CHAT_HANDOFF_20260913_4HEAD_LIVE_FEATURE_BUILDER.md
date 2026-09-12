# CHAT HANDOFF — 2026-09-13 — 4号艇 LIVE feature builder

Updated: 2026-09-13 JST
Repository: `merry02180218-ai/boatrace-backtest`
Priority: latest GitHub > older handoffs/chat memory.

## Immutable production / research rules

- Keep v291 race-entry logic unchanged.
- Adopted ticket overlay remains `HEAD4_V291_COMP7_VARN_F4_N16`.
- Original v291 entry gate remains Top4 composite >= 7.0.
- After that gate, select largest N=4..16 with composite >= 4.0.
- Exactly ¥10,000/race inverse-odds Dutch with ¥100 Hamilton rounding.
- Jul/Aug 2026 are NON-PRISTINE; do not use outcomes for fitting/tuning/promotion.
- September 2026 outcomes remain outcome-blind and prohibited for fitting/tuning/evaluation.
- v96 prohibited.
- Missing/late/incomplete LIVE input fails closed.
- Never substitute closing/post-deadline odds for LIVE purchase-time odds.

## Existing important research state

Variable-N research is complete and the operational overlay was already adopted separately from historical v291 evidence.

Apr–Jun evidence for floor=4.0/maxN=16:
- R=29
- ROI=188.83%
- hit rate=44.83%
- average N=9.97
- minimum monthly ROI=143.52%

The immutable v291 Top4 baseline on the same 29 races remains ROI=300.26%, hit=31.03%. The overlay is therefore an explicit hit-rate/ROI tradeoff; historical v291 is not rewritten.

A-LIVE added-race rescue remains REJECTED because no standalone-safe added-race route passed the required stability/LOMO gates. Base-v291 profit must not mask a losing rescue route.

S/A variable-N market runner remains implementation-complete:
- `run_4head_v291_varn_live.py`
- `verify_4head_v291_varn_live.py`
- `.github/workflows/validate-4head-v291-varn-live.yml`
- corrected CI `34711859515`: SUCCESS

Frozen downstream artifact blocker is resolved:
- `artifacts/head4_v291_downstream_20260630.json`
- persisted after parity-passing CI `34714996270`
- no Jul/Aug/Sep labels and no v96 production signal
- POST / ENV_ENTRY / v283 SECOND / conditional THIRD parity PASS

## This run — generalized result-blind beforeinfo acquisition

The remaining one-click blocker was generalized current-day pre-result source acquisition and exact LIVE feature construction.

Implemented first causal layer:
- `fetch_4head_beforeinfo_live.py`
- `verify_4head_beforeinfo_live.py`
- `.github/workflows/validate-4head-beforeinfo-live.yml`

Implementation properties:
- arbitrary `YYYYMMDD / jcd / rno` target;
- allow-listed official endpoint only: `https://www.boatrace.jp/owpc/pc/race/beforeinfo`;
- never follows links;
- redirects are refused;
- no result/payout endpoint is requested;
- raw HTML is persisted unchanged;
- metadata persists JST fetch timestamp, exact source URL and SHA256 of raw HTML;
- parsed table structure is persisted for later causal feature extraction;
- invalid date/JCD/race targets fail closed;
- this layer deliberately does NOT invent POST/ENV_ENTRY/A/v283 feature values.

Commits:
- `1134496f31d555628a32aead2dd5195a2fc00f18` — generalized result-blind beforeinfo fetcher
- `2a5ac6e098bec81f31d6d5a85589ddaa61b7780f` — offline fail-closed verifier
- `a55c2c6649b29d987ff8c49d3631e6a8b187d8c9` — CI workflow

CI:
- run `34721199607`
- syntax check: SUCCESS
- offline fail-closed verifier: SUCCESS
- leakage/source guard: SUCCESS
- job conclusion: SUCCESS

Decision: **ACCEPT generalized beforeinfo acquisition layer.**

Reason:
- it removes the date/target-specific fetch limitation without touching v291/v283/A model semantics;
- it is result-blind and immutable/auditable;
- it does not fabricate features or refit anything;
- it provides the source snapshot needed for exact parity work.

## Remaining blocker — exact feature mapping/parity

Full one-click LIVE is still NOT complete.

Remaining chain:

`beforeinfo snapshot + frozen PRE-side inputs -> exact POST row -> exact ENV_ENTRY row -> exact A-LIVE 17-key row -> exact v283 SECOND 5 rows -> exact v283 conditional THIRD 20 rows -> frozen inference -> pre-deadline odds -> variable-N Dutch`

The frozen downstream artifact exposes the exact feature schemas, but current-day causal derivation for every required feature still needs to be mapped to the historical source lineage and parity-tested. Historical research frames must not be silently treated as LIVE builders.

Next work:
1. Reuse exact historical feature constructors where they are demonstrably causal/pre-result (`analyze_v250_4head_rebuild_baseline.py`, v264/v270, v279/v282 lineage) instead of reimplementing formulas from memory.
2. Build a source-to-feature manifest showing every required POST, ENV_ENTRY, A 17-key, SECOND and conditional THIRD field, source, timing and formula.
3. Fail closed for any field whose current-day causal source/formula cannot be proven.
4. Prove parity on Apr–Jun/result-free fixtures only; do not use Jul/Aug outcomes or any September outcomes.
5. Emit immutable pre-result input JSON with source timestamps/hashes and feed it to `run_4head_v291_varn_live.py`.
6. Add CI for feature parity/schema completeness and then wire the daily PRE candidate path into the builder.

Current status: **important progress / CI PASS, but one-click LIVE orchestration remains incomplete at exact feature construction/parity.**
