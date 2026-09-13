# CHAT HANDOFF — 2026-09-13 — 4号艇 BOATCAST code pin

Updated: 2026-09-13 JST
Repository: `merry02180218-ai/boatrace-backtest`
Priority: latest GitHub > older handoffs/chat memory.
Previous handoff: `CHAT_HANDOFF_20260913_4HEAD_BOATCAST_SOURCE.md`.

## Immutable rules

- Keep v291 race-entry logic unchanged.
- Adopted overlay remains `HEAD4_V291_COMP7_VARN_F4_N16`: original v291 Top4 composite >= 7.0, then largest N=4..16 with composite >= 4.0, exactly ¥10,000/race inverse-odds Dutch with ¥100 Hamilton rounding.
- Jul/Aug 2026 are NON-PRISTINE; their outcomes are not valid for fitting/tuning/promotion.
- September 2026 remains strictly outcome-blind; do not read September result/payout data for fitting/tuning/evaluation.
- Missing/late/incomplete LIVE inputs fail closed. Never fabricate original-exhibition metrics and never substitute closing/post-deadline odds.

## New important result — public executable lineage pinned

The prior handoff had narrowed BOATCAST to a documented implementation candidate. This run reached the actual public executable source and unit-test lineage and pinned it by commit.

External reference repository:
- `BoatraceCSV/boatracecsv.github.io`
- pinned commit: `563c69ccd28853b8b4953489c673877a9dfeb4e8`

Pinned source files:
- `scripts/boatrace/original_exhibition_scraper.py`
- `scripts/boatrace/preview_tsv_scraper.py`
- `scripts/tests/unit/test_preview_tsv_scraper.py`

### Original exhibition endpoint and parser

The executable source explicitly builds:

`https://race.boatcast.jp/txt/{jo:02d}/bc_oriten_{YYYYMMDD}_{jo:02d}_{race:02d}.txt`

The TSV contract in that source is:
- line 1: `data=` marker
- line 2: `{status}\t{ncols}`
- line 3: measurement labels, e.g. `一周 / まわり足 / 直線`
- following rows: boat number, racer name, and value1..value3
- status `1` means measured; `0` measuring; `2` not measurable.

The parser normalizes full-width spacing in labels before exposing the label/value pairs. This means mapping must be label-driven, not hard-coded solely by ordinal position, because venues can expose 2 or 3 metrics and ordering is venue-specific.

### Start-display endpoint and F/L normalization

The executable preview source explicitly builds:

`https://race.boatcast.jp/hp_txt/{jo:02d}/bc_j_stt_{YYYYMMDD}_{jo:02d}_{race:02d}.txt`

Its row contract identifies ST numeric text in column 5 and F/L flag in column 6. The pinned parser applies these exact rules:
- `F` => negate the numeric ST (`.08` + `F` => `-0.08`)
- `L` => `None` / missing; do not synthesize a numeric ST
- otherwise => parse the numeric value as positive
- leading-dot values are normalized before float parsing.

The public unit test independently asserts the negative-F behavior (for example `.09` + `F` => `-0.09`), explicitly describing it as matching existing CSV semantics.

## Research decision

**ACCEPT the exact BOATCAST URL templates, TSV shape, label-driven original-exhibition parsing rule, and F/L normalization above as a frozen source-contract candidate.**

**REJECT production hookup to v291 for now.**

Why the contract is accepted:
- evidence is executable source plus unit tests, not search snippets or prose documentation only;
- it is pre-result acquisition logic and does not require September outcomes;
- it resolves the previously unproven F/L acquisition convention at the candidate-source level;
- it gives an exact machine-readable source for the three missing original-exhibition families.

Why production adoption is still rejected:
- this external code proves its own CSV compatibility, but does not by itself prove numeric parity with this repository's frozen Apr–Jun historical `original_scores` transformation;
- `orig_straight4`, `orig_lap4`, `orig_turn4` are model features, so raw label/value parity and the repository's ranking/score transformation must still be demonstrated end-to-end;
- before accepting LIVE integration we still need result-free Apr–Jun fixtures or a frozen reference artifact from this repository against which the BOATCAST parse can be compared;
- therefore current production behavior remains fail-closed for unavailable original-exhibition inputs.

## Safety / leakage audit for this run

- No September result or payout endpoint/data was used.
- No Jul/Aug outcome was used for model selection, threshold tuning, or promotion.
- v291, v283, A-LIVE, variable-N overlay and ¥10,000 Dutch logic were not changed.
- The only external evidence accepted in this checkpoint is pre-race source/parser lineage.

## Next checkpoint

1. Locate or construct a result-free Apr–Jun parity fixture inside this repository containing the historical original-exhibition raw/feature values required by frozen v291 lineage.
2. Implement an additive BOATCAST parser/contract test in this repository, with the pinned external commit recorded, without wiring it into production.
3. Prove label-to-feature mapping and numeric parity for lane 4: `直線 -> orig_straight4`, `一周 -> orig_lap4`, `まわり足 -> orig_turn4`, including missing/2-column venues.
4. Prove ST F/L parity against Apr–Jun frozen numeric ST values.
5. Only if all parity checks pass, extend the current-day POST builder; then continue ENV_ENTRY 25, A-LIVE 17, v283 SECOND 5 and conditional THIRD 20.
6. Run CI and record the run ID/status here before any production promotion.

Current status: **important executable source lineage is now pinned and accepted as a source-contract candidate. Production POST builder is still incomplete/fail-closed pending Apr–Jun parity. No model or betting-policy change.**
