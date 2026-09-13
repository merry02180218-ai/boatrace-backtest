# CHAT HANDOFF — 2026-09-13 — HEAD4 v291 CURRENT-DAY POST LIVE BUILDER

## Priority / immutable rules
- Latest GitHub is authoritative over older handoffs/chat memory.
- This checkpoint resumed from `CHAT_HANDOFF_20260913_4HEAD_BOATCAST_SERIALIZATION_LINEAGE.md` on top of the then-current main HEAD `8bf18b73824aec3b6e9b454cc46a0f21e9d3642b`; newer unrelated repository work must not be rolled back.
- HEAD4 production model remains frozen at v291.
- Adopted overlay remains `HEAD4_V291_COMP7_VARN_F4_N16`: v291 Top4 composite >= 7.0, then largest N=4..16 with composite >= 4.0, exactly JPY 10,000/race inverse-odds Dutch with JPY 100 Hamilton rounding.
- July/August 2026 outcomes are NON-PRISTINE and were not used.
- September 2026 outcomes remain outcome-blind and were not read for fitting/tuning/evaluation/promotion.
- Missing/late/incomplete LIVE input fails closed. No closing/post-deadline odds substitution.

## What was implemented
Added current-day result-blind exhibition-side POST builder:
- `build_4head_post_live.py`
- `verify_4head_post_live.py`
- `.github/workflows/validate-4head-post-live.yml`

The builder produces the frozen seven exhibition-side POST fields in exact order:
1. `ex_st_rank4`
2. `ex_st_4`
3. `ex_st_edge_4v3`
4. `orig_straight4`
5. `orig_lap4`
6. `orig_turn4`
7. `tilt4`

Sources are allow-listed pre-race surfaces only:
- BOAT RACE official `beforeinfo` for lane-4 tilt.
- BOATCAST `bc_j_stt` for start-display ST using the already-pinned F/L contract.
- BOATCAST `bc_oriten` for original exhibition using label-driven parsing.

The READY JSON records exact source URLs, fetch time, and SHA256 of each raw source. Redirects are refused. No result/payout/odds endpoint is requested by this builder.

## Frozen feature semantics preserved
- ST `F` => negative numeric value.
- ST `L` => missing.
- `ex_st_rank4` uses the frozen lower-is-better `rank_score` semantics.
- `ex_st_edge_4v3 = ST3 - ST4`.
- Original exhibition is label-driven; lane 4 is rank-scored lower-is-better exactly as historical `original_scores`.
- A metric family not supplied by a measured 2-metric venue remains the historical frozen default 0.5. This is the verified historical constructor behavior, not a newly invented imputation.
- `tilt4` preserves historical numeric `tiltval` semantics.
- Missing lane-3/lane-4 required ST, unmeasured original exhibition, missing/ambiguous tilt, malformed/missing boat rows, redirects, HTTP errors, or non-finite features all fail closed and do not emit READY.

## CI history
### Initial dedicated run — FAILURE, guard-only
Run `34739925028`.

Passed:
- dependency setup
- syntax compilation
- offline exact/fail-closed verifier

Failed:
- leakage/source guard only.

Cause: the workflow asserted the literal combined string `race.boatcast.jp/hp_txt/`, while the Python implementation intentionally constructs the URL from `BOATCAST = "https://race.boatcast.jp"` plus `/hp_txt/...`. This was a CI string-contract mismatch, not a model/parser/scientific failure.

### Correction
Commit `9a03e55cc0407944c21e663f69b5dd39b4762a15` changed only the guard to assert the actual URL-builder components (`race.boatcast.jp`, `/hp_txt/`, `bc_j_stt_`, `/txt/`, `bc_oriten_`, `beforeinfo`) while retaining result/odds/result-file prohibitions.

### Corrected dedicated run — SUCCESS
Run `34739945712` completed SUCCESS.

Passed:
- syntax
- offline exact feature/fail-closed verifier
- F negative / L missing contract
- 2-metric original-exhibition frozen-default behavior
- missing/malformed source fail-closed cases
- leakage/source guard
- immutable-policy guard

## Decision
**ACCEPT the seven-field current-day POST builder implementation/contract as the next production building block.**

Reasons:
- It uses only pre-race allow-listed sources and is result-blind by construction.
- It reuses the previously proven BOATCAST raw->parser->archive->feature lineage instead of inventing new feature formulas.
- It reproduces the frozen seven POST feature semantics and order.
- It fails closed rather than fabricating values.
- Dedicated corrected CI is green (`34739945712`).
- v291 and betting overlay are unchanged.

## Important limitation / not yet full AUTO LIVE
This checkpoint does **not** declare complete HEAD4 AUTO LIVE.

The seven exhibition-side POST builder is now present, but the complete chain still requires exact current-day construction/parity for the remaining frozen downstream inputs:

`PRE-side 9 + POST 7 -> ENV_ENTRY 25 -> A-LIVE 17 -> v283 SECOND 5 rows -> conditional THIRD 20 rows -> frozen inference -> pre-deadline odds -> HEAD4_V291_COMP7_VARN_F4_N16 Dutch`

Do not bypass these remaining gates and do not feed partial/default-made downstream rows into inference.

## Safety / contamination audit
- Jul/Aug outcomes used: NO
- September outcomes used: NO
- result/payout files used: NO
- v291 changed: NO
- variable-N overlay changed: NO
- JPY 10,000 Dutch changed: NO

## Next checkpoint
1. Use the frozen downstream artifact/schema to map and implement `ENV_ENTRY` current-day 25 inputs from proven causal sources, fail-closed.
2. Prove exact schema/formula parity against Apr-Jun/result-free fixtures only.
3. Then complete A-LIVE 17-key row and v283 SECOND/conditional THIRD input builders with the same discipline.
4. Only after full downstream parity wire this POST builder into the one-click runner and pre-deadline odds path.
5. Resume additional-BET/variable-ticket practical research only without rewriting the v291 baseline.

Current status: **important implementation milestone: the seven-field current-day POST builder exists and its corrected dedicated CI is green. Full HEAD4 AUTO LIVE remains incomplete at ENV_ENTRY/A-LIVE/v283 downstream construction.**
