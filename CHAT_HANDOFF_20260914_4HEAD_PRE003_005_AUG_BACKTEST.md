# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **JULY 2026 DAY-LEVEL PIPELINE BOUNDARY AUDIT COMPLETE**

## Frozen production
Production remains unchanged. S PRE >= 0.28; A PRE >= 0.18; frozen downstream rules remain in force. July/August 2026 remain NON-PRISTINE; September remains outcome-blind for tuning.

## Prior completed findings
- Common frozen-scale: Feb-Jun 2026 PRE .03-.05 head rate 3.67%; July 6.97%; August 23.18% (July/Aug NON-PRISTINE).
- Outcome-independent drift audit: July PRE<.01 28.48%, August 68.90% under Jan-31 frozen model.
- Rolling fit-cutoff diagnostic: even Jun-30 fit gives August PRE<.01 77.83%; Jul-31 diagnostic fit recenters August to 7.40%.
- Seasonal YoY audit: 2025 has almost no June->July feature shift, while 2026 has large shifts. `motor_hist_keys_end` is 0 through June 2026 then 1590 in July/August. CI Run `34774806390`, Job `103770858036`, Artifact `10323355651`.

## Day-level July boundary audit work-start plan
Written BEFORE implementation. Production frozen; target window outcome-blind; trace motor-history source onset, causal effective date, daily focal features and fixed pre-boundary PRE distribution; do not force causal attribution if dates do not align.

## Implementation
- analysis: `analyze_4head_july_boundary_20260914.py`
- workflow: `.github/workflows/analyze-4head-july-boundary.yml`
- work-start handoff commit: `dbee248f55b324633b548beb983011208bcf9680`
- analysis commit: `1fb1c3f7acb9a5ba056bf2b1e250b56a90fbcdb1`
- workflow/head commit: `5a53d18f8a9a1ebb264eab1eddcc37eedeca4dc6`

Method:
- causal replay from 2026-02-01 through 2026-07-20
- fixed PRE model trained only on rows before 2026-06-20
- target audit window 2026-06-20 through 2026-07-20 does not load target outcomes
- score each day before ingesting that day's motor history, matching causal order
- daily focal feature means/medians/zero shares plus fixed PRE bin shares
- production unchanged.

## CI
- workflow `head4-july-boundary`
- Run ID `34775332112`
- Job ID `103772292898`
- conclusion: SUCCESS
- Artifact `head4-july-boundary`
- Artifact ID `10323142377`
- size 5892 bytes
- SHA256 `9a1c36bc45255fc9b90297712db5884c0cfdcdedba8ccbd51e7c4f515380bf62`

## Exact transition findings
- First date with motor-history source rows: **2026-07-01**.
- Because scoring occurs before same-day ingest, the first scoring date that can use the newly available motor history is **2026-07-02**.
- However, the dominant PRE/feature collapse does **not** occur on 2026-07-02.
- The largest observed day-over-day break in the audit window is **2026-07-19**:
  - `inner12_resistance_mean`: 0.245328 -> 0.699611 (abs change 0.454284)
  - `wall3_weak_mean`: 0.715926 -> 0.195410 (abs change 0.520516)
  - `past_win4_mean`: 0 -> 0.0938657
  - `legacy_score4_mean`: 46.209 -> 36.2835
  - fixed pre-boundary `PRE<.01` share: 0 -> **0.807292**
- `motor4_hist_mean` largest daily move is on 2026-07-18: 0.487352 -> 0.468607, only 0.018745 absolute.
- `racer4_mean` largest move is 2026-07-17: 0.371198 -> 0.441101.
- `hist_st_edge_4v3_mean` largest move is 2026-06-25, before the motor-history source onset.

## Interpretation
The July-1 motor-history availability boundary is real, but the day-level timing does **not** support it as the direct sole cause of the major PRE collapse. Motor history becomes causally usable on July 2, while the strongest simultaneous break in `inner12_resistance`, `wall3_weak`, `past_win4`, `legacy_score4`, and PRE distribution occurs on July 19. Therefore the next audit should trace the raw inputs/history/default logic feeding those non-motor features around July 18->19 rather than attributing the collapse to `motor_hist` alone.

This also weakens a simple generic summer explanation: the prior YoY audit found no comparable 2025 July shift, and the 2026 dominant break is concentrated on a specific mid-July date rather than July 1 itself.

## Limitations
- This audit identifies timing alignment, not full causal attribution.
- July/August 2026 remain NON-PRISTINE and cannot select production changes.
- The fixed PRE model is diagnostic only.
- Production remains `HEAD4_V291_COMP7` unchanged.

## Restart point
Next safest audit:
1. Trace raw primitives and history/default paths feeding `resistance12(x)`, `features4(x)['3壁弱さ']`, boat-4 `past_win`, and `score4v4` across **2026-07-18 -> 2026-07-19**.
2. Compare race-card/program source schema, missing/default shares, day/series-state inputs, and any source-file coverage change on those dates.
3. Determine whether July 19 is a source/schema/history-reset boundary or a genuine race-population change.
4. Recompute July 19 under a held-consistent pre-July/pre-boundary input policy if technically possible, score-distribution only first.
5. Do not modify production until the lineage cause is documented.
