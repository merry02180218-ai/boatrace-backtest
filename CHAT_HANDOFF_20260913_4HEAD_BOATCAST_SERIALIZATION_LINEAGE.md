# CHAT HANDOFF — 2026-09-13 — HEAD4 v291 BOATCAST SERIALIZATION LINEAGE

## Priority / immutable rules
- Latest GitHub is authoritative over older chat memory/handoffs.
- HEAD4 production model remains frozen at v291.
- Adopted betting overlay remains `HEAD4_V291_COMP7_VARN_F4_N16`:
  - original v291 Top4 composite >= 7.0
  - then largest N=4..16 with composite >= 4.0
  - exactly JPY 10,000/race inverse-odds Dutch
  - JPY 100 Hamilton rounding
- July/August 2026 outcomes are NON-PRISTINE and must not be used for fitting/tuning/promotion.
- September 2026 outcomes remain outcome-blind and must not be read for tuning/evaluation/promotion.
- Missing/late/incomplete LIVE inputs fail closed. Never fabricate values or use post-deadline odds.

## Repo context
Newer repository work such as v319/v320 is a different head/model stream and does not supersede frozen HEAD4 v291. HEAD4 research therefore resumed from the latest HEAD4 BOATCAST parity checkpoint rather than adopting those commits.

## Research completed in this checkpoint
The remaining BOATCAST hidden-transform concern was audited by pinning the exact external BoatraceCSV source commit:

`563c69ccd28853b8b4953489c673877a9dfeb4e8`

Pinned source lineage proves:
1. Original exhibition BOATCAST TSV is read from the pinned `bc_oriten` endpoint.
2. Measure labels are preserved; `value1/value2/value3` are parsed directly as floats.
3. Converter writes those labels and numeric values directly to archived original-exhibition CSV cells; only `None -> blank` and normal numeric string serialization occur.
4. Start-display BOATCAST TSV `bc_j_stt` uses `st_value` + `st_flag`.
5. Pinned ST parser uses `flag.upper() == "L" -> None` and `flag.upper() == "F" -> num = -num`.
6. Converter writes `RacePreview.start_timing` directly to archived preview CSV.

This closes the previously unresolved possibility that archived Apr-Jun BoatraceCSV fields had an undocumented transformation between BOATCAST raw parsing and the values used by the frozen HEAD4 feature logic.

## Existing result-free Apr-Jun semantic parity retained
Window: 2026-04-01 through 2026-06-30 only.
- original-exhibition dates: 91
- ST dates: 91
- original-exhibition rows: 12,250
- ST rows: 12,749
- straight-label rows: 10,578
- lap-label rows: 12,250
- turn-label rows: 12,250
- two-metric rows: 1,672
- three-metric rows: 10,578
- frozen lane-4 score mismatches: 0
- archived negative ST values: 14,757
- result/payout files read: false

Therefore the evidence chain is now:

`BOATCAST raw TSV -> pinned parser -> direct archived CSV serialization -> Apr-Jun frozen feature semantics -> 0 lane4 score mismatches`

## CI history
### Initial run — failure, audit-only
Run: `34738462928`

The existing Apr-Jun result-free semantic audit PASSED in this run. The new serialization-lineage step failed because the audit harness looked for equivalent pseudocode strings:
- `if flag == "L"`
- `if flag == "F"`
- `return -abs(parsed)`

The pinned implementation instead uses:
- `if flag.upper() == "L"`
- `if flag.upper() == "F"`
- `num = -num`

This was a test-harness string-contract error, not a scientific/model failure.

### Correction
Fix commit: `eaadda670611a23ecbbbbff45cc887ecde9fb5a1`

The audit was changed to assert the exact pinned implementation rather than pseudocode-equivalent text.

### Corrected CI — SUCCESS
Dedicated run: `34738543306`
Conclusion: SUCCESS

All steps passed, including syntax, source-lineage audit, immutable guards, artifact upload, and audit-result step.

Recorded artifact:
`artifacts/head4_boatcast_serialization_lineage_20260630.json`

Artifact commit:
`ceeec76451c89af9077a4d706f465a7ec03db6dc`

## Decision
### ACCEPT
Accept the archived Apr-Jun BoatraceCSV preview/original-exhibition representation as the exact serialized output of the pinned BOATCAST parser lineage for the HEAD4 fields audited here.

This closes the previous hidden-transform/raw-source provenance blocker for:
- `orig_straight4`
- `orig_lap4`
- `orig_turn4`
- start-display ST F/L semantics

### NOT YET production-connected
Do not change v291 and do not silently enable bets merely because source lineage is now proven.

The next production gate is a current-day, result-free, fail-closed POST builder/field-completeness test that combines:
- the four already-established official central-beforeinfo POST inputs, and
- the three BOATCAST original-exhibition inputs.

Only after all seven exhibition-side POST inputs are produced with the frozen feature semantics and missing/late inputs fail closed should production POST hookup advance.

Then continue the remaining ENV_ENTRY / A-LIVE / v283 SECOND-THIRD LIVE feature chains before declaring full HEAD4 auto-LIVE complete.

## Safety / contamination audit
- Jul/Aug outcomes used: NO
- September outcomes used: NO
- result/payout files used in this checkpoint: NO
- v291 changed: NO
- adopted variable-N/Dutch overlay changed: NO

## Next checkpoint
Implement and CI-test the current-day HEAD4 POST builder using the now-proven BOATCAST lineage, preserving exact frozen v291 semantics and fail-closed behavior. After that, continue ENV_ENTRY/A-LIVE/v283 LIVE feature completion, then return to additional-BET/variable-ticket practical research without changing the v291 baseline.
