# CHAT HANDOFF — 2026-09-13 — 4号艇 BOATCAST parity contract

Updated: 2026-09-13 JST
Repository: `merry02180218-ai/boatrace-backtest`
Priority: latest GitHub > older handoffs/chat memory.
Previous 4-head handoff: `CHAT_HANDOFF_20260913_4HEAD_BOATCAST_CODE_PIN.md`.

## Immutable rules

- Keep v291 race-entry logic unchanged.
- Adopted betting overlay remains `HEAD4_V291_COMP7_VARN_F4_N16`: original v291 Top4 composite >= 7.0, then largest N=4..16 with composite >= 4.0, exactly ¥10,000/race inverse-odds Dutch with ¥100 Hamilton rounding.
- Jul/Aug 2026 are NON-PRISTINE. Do not use their outcomes for fitting, tuning, rescue rules, threshold selection, or promotion.
- September 2026 remains strictly outcome-blind. Do not read September results/payouts for fitting, tuning, evaluation, or promotion.
- Missing/late/incomplete LIVE inputs fail closed. Never fabricate original-exhibition values and never substitute post-deadline odds.

## Work performed in this checkpoint

The prior checkpoint pinned the public executable BOATCAST source contract but left Apr-Jun parity unresolved. This checkpoint implemented an additive result-free audit:

- `audit_4head_boatcast_parity_contract.py`
- `.github/workflows/audit-4head-boatcast-parity-contract.yml`
- `artifacts/head4_boatcast_parity_contract_20260630.json`

The audit does not modify or invoke any September outcome path and does not wire BOATCAST into production.

## Exact frozen POST transformation now confirmed

The frozen v250/v291 POST lineage does **not** feed BOATCAST raw values directly into the model. `analyze_v23_20260902_daypreview.original_scores()` maps original-exhibition measurements to lane-specific rank scores:

- labels containing `直線` -> `orig_straight4`
- labels containing `一周`, `周`, or `ラップ` -> `orig_lap4`
- labels containing `まわり`, `回り`, or `ターン` -> `orig_turn4`
- lower raw measurement value ranks better
- lane 4 receives `1 - position/(n-1)` among available boats
- a measurement family that is not published remains the frozen neutral `0.5`

The BOATCAST parser remains label-driven because venues can expose two or three original-exhibition metrics and column order cannot be treated as globally fixed.

Start-display normalization remains:
- `F` => negative numeric ST
- `L` => missing / no synthesized numeric value

## CI history

### Initial run — FAILED

Run: `34735541879`

Failure was in the newly added audit harness, not in v291 or feature parity. The first version incorrectly assumed Apr-Jun preview CSVs were present in the repository checkout, so it found zero historical rows.

Decision: reject that audit result as invalid source discovery; fix the harness without changing any model or betting policy.

### Corrected run — SUCCESS

Fix commit: `b066ba89bff825232f456f007d08301a724f5ea5`
Run: `34735635732`
Conclusion: **SUCCESS**

The corrected audit uses the repository's existing `backtest.rows` fetch layer against the archived BoatraceCSV pre-race preview source.

Result-free Apr-Jun audit, 2026-04-01 through 2026-06-30:

- original-exhibition dates: 91
- ST dates: 91
- original-exhibition rows: 12,250
- ST rows: 12,749
- rows exposing straight metric: 10,578
- rows exposing lap metric: 12,250
- rows exposing turn metric: 12,250
- two-metric original-exhibition rows: 1,672
- three-metric rows: 10,578
- lane-4 frozen score mismatches: **0**
- archived negative ST values: 14,757
- result/payout files read by this audit: **0**

The CI guards also assert:
- Jul/Aug not used
- September outcomes not used
- v291 unchanged
- production hookup remains false

## Research decision

### ACCEPT

1. The exact BOATCAST original-exhibition and start-display source contract pinned in the previous handoff.
2. F => negative numeric, L => missing.
3. Label-driven mapping from BOATCAST original-exhibition families to the frozen v250/v291 POST features.
4. The exact lane-4 rank-score transformation semantics used by frozen v291 lineage.
5. Archived Apr-Jun feature-semantic parity: 12,250 original-exhibition rows checked with zero lane-4 score mismatches.

### REJECT production hookup for now

Direct BOATCAST -> v291 POST production wiring remains rejected at this checkpoint.

Reason: this audit proves parser behavior plus archived CSV -> frozen feature semantics, but it has not yet demonstrated byte/value parity between historical raw BOATCAST TSV responses and the archived BoatraceCSV source values used by the model lineage. Production remains fail-closed rather than assuming the archived CSV is an exact raw-source mirror.

This is deliberately stricter than merely proving the feature formula.

## Leakage / safety audit

- No September result or payout data was read.
- No Jul/Aug outcomes were used.
- v291 race-entry logic was not changed.
- v283 was not changed.
- `HEAD4_V291_COMP7_VARN_F4_N16` was not changed.
- ¥10,000 Dutch and ¥100 Hamilton rounding were not changed.

## Next checkpoint

1. Establish raw-source parity evidence between BOATCAST TSV and the archived pre-race source representation using <=2026-06-30 fixtures or an independently frozen historical raw artifact.
2. Verify both original-exhibition raw values/labels and ST F/L values before feature conversion.
3. If exact raw-source parity passes, extend the current-day POST builder with this frozen parser and preserve fail-closed behavior for status != 1, missing families, L, incomplete races, or stale inputs.
4. Then complete current-day ENV_ENTRY, A-LIVE 17, v283 SECOND 5 and conditional THIRD 20 generation/parity.
5. Only after the full pre-result chain is reproducible should the production LIVE runner proceed to official pre-deadline odds and the already-adopted variable-N overlay.

Current status: **important parity milestone passed, but production AUTO LIVE remains incomplete. v291 and its adopted betting overlay remain unchanged.**
