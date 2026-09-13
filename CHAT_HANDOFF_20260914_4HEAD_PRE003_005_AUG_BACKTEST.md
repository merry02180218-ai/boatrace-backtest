# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **JULY 18->19 RAW PRIMITIVE LINEAGE AUDIT COMPLETE**

## Frozen production
Production remains unchanged (`HEAD4_V291_COMP7`). July/August 2026 remain NON-PRISTINE; September remains outcome-blind for tuning/model selection.

## Prior findings
- Motor-history source starts 2026-07-01 and becomes causally usable 2026-07-02.
- Dominant PRE break is later, 2026-07-19: `inner12_resistance` 0.245328->0.699611, `wall3_weak` 0.715926->0.195410, `past_win4` 0->0.0938657, `legacy_score4` 46.209->36.2835, PRE<.01 share 0->80.7292%.

## Formula lineage
`inner12_resistance` depends on boat1/2 `waku_wr`, national `wr`, and `waku_st`.
`wall3_weak` depends on boat3 `waku_wr` plus 3-vs-4 `waku_st` edge.
`past_win4` is first-place share over numeric boat4 past-10 Waku10 finishes.

## Implementation / correction
- analysis: `analyze_4head_jul18_19_primitives_20260914.py`
- workflow: `.github/workflows/analyze-4head-jul18-19-primitives.yml`
- work-start commit: `b678824b43e792539f44227df16449c784ce0277`
- initial analysis commit: `f8361f06e1fc0fb3725ce05bedc710b5b6982ae6`
- workflow commit: `1820426f31edad4e3d9b538792a1355d79c1a3df`
- first CI failed because raw `race_features()` output was passed directly to `score4v4()` without v4-added fields (`mhist`, `stretch`).
- correction commit: `006dc5e418c4bf2e367e1915f50d132027a8c5f7`; replay now uses the causal `process_features()` state for `legacy_score4`, while raw Waku/card diagnostics remain outcome-blind.

## Successful CI
- Run ID `34776896951`
- Job ID `103776546968`
- conclusion: SUCCESS
- Artifact `head4-jul18-19-primitives`
- Artifact ID `10324181759`
- size 20422 bytes
- SHA256 `ecad422375095ffd8d209798fb007fb028cbd835a55df1986153665e0d643608`

## Root-cause evidence
The 7/18 -> 7/19 break is overwhelmingly a **Waku10 source-schema/coverage boundary**, not an ordinary one-day race-population shift.

Exact evidence:
- race-card schema: +0 / -0 columns (unchanged)
- Waku10 schema: **+208 / -0 columns on 7/19**
- On 7/18, for boats 1-4:
  - mean numeric past-10 count = **0.0**
  - `waku_wr` = **0.0** because source fields are absent
  - `waku_st` raw blank share = essentially **100%**, so code falls back to national ST
  - `waku_sr` defaults to **3.5**
- On 7/19:
  - past-10 numeric observations suddenly become ~**9.8/10 per boat**
  - boat1 `waku_wr` mean = **7.867969**
  - boat2 `waku_wr` mean = **5.714792**
  - boat3 `waku_wr` mean = **5.401563**
  - boat4 `waku_wr` mean = **4.724844**
  - frame-specific ST fields become populated for ~99.5-100% of rows
  - boat1 `waku_sr` 3.5 -> **2.931771**; boat3 3.5 -> **3.044792**; boat4 3.5 -> **3.241667**
- Resulting feature shifts exactly align:
  - `wall3_weak`: 0.715926 -> **0.195410**
  - `resistance12`: 0.245328 -> **0.699611**
  - `past_win4`: 0 -> **0.093866**
  - `legacy_score4`: 46.209026 -> **36.283451**

## Interpretation
This identifies the primary source of the July-19 PRE collapse: **Waku10 changed from a sparse/old schema with the required frame-specific and past-10 fields absent to a richer schema with those fields populated.** Before July 19, the feature code silently used defaults (`waku_wr=0`, `waku_sr=3.5`, `waku_st` fallback to national ST, `past_win=0`). From July 19 onward the real Waku10 values enter, dramatically changing the feature distribution.

Therefore the earlier July/August drift is substantially a data-lineage compatibility problem, not evidence by itself of a genuine racing-regime change. July/August remain NON-PRISTINE and cannot be used to tune production.

## Next restart point
1. Identify the exact Waku10 schema introduction history around July 19 and whether equivalent rich fields exist for older dates under another source/path.
2. Build a schema-consistent causal replay for historical months using one fixed information definition: either reconstruct rich Waku10 historically where legitimately available, or explicitly restrict all periods to the common pre-July field set.
3. Re-run Feb-Aug PRE distributions on that consistent lineage before drawing conclusions about model drift.
4. Do not change production until the corrected lineage backtest is complete.
