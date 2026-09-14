# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-14 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Purpose
Continue BOATCAST start-exhibition video development until immediate post-exhibition live use is reliable: result-blind FastClip -> automatic six-boat seed -> automatic tracking -> SES -> later model re-evaluation, with no manual seed editing.

## Non-negotiable rules
- Latest GitHub code/results override this handoff and old chat memory.
- Never inspect race results before locking exhibition-only judgement on blind/pristine samples.
- July/August 2026 are NON-PRISTINE/research-only; September preferred.
- Never weaken fail-closed quality gates merely to obtain `accepted=true`.
- Never hard-code boat-number-specific/race-specific offsets.
- `accepted=true` is necessary but not sufficient: trajectories must be physically sane/on-frame and preserve identity.
- Final race-by-race operation should be persistent on Japan self-hosted PC; Actions are validation/logging.
- Exact Japan Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.
- Live latency target: ideal <=30 sec after video availability, maximum <=60 sec.

## Blindness status
- 2026-09-10 Kiryu3/6/9 results remain unread. Preserve blindness.
- 2026-09-09 Kiryu12 result is exposed technical regression only.
- 2026-09-10 Kiryu12 is exposed technical calibration.

## Seed state
Current seed remains `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`.
Kiryu6 evidence continues to indicate that v17 can place rescued outer rows plausibly. Current blocker is tracker identity/path preservation, not more race-specific seed movement.

## Tracker history summary
- v8 (`264bf494812b6b72e4af94cacc1d40b009a6dde1`): per-frame joint six-boat assignment. Kiryu12 standard/varied passed, Kiryu3/Kiryu6 failed.
- v9 (`30a7b7ad2e44e51ccd2d0d2c0df0e32b5c265608`): immutable seed-frame appearance memory. Outer-row wake/background collapse remained.
- v10: fleet-affine y reference. Rejected; all four failed closed and healthier samples regressed.
- v11 (`372aea94e0f718cc7dc2be3502c8761f33433ecf`): immutable slit-motion corridor. Safe but all four failed closed.
- v12 (`13a929a8a296ac92247ba6664f9e5bd35ec9cb4e`): short motion memory, still greedy. Failed safely.
- v13 (`ed02d51599da88c3930370116d70b5d390d5ee0b`): first multi-hypothesis fleet beam. Every beam eventually died.
- v14 (`a2df021c038a09f4df324545426b4892800e9eda`): prediction-local candidate diversification. One weak Kiryu6 acceptance, three failures; unstable.
- v15 (`1d18621d725343437aed81554713a1db8017eb68`): full-cell immutable-anchor lattice + v13 beam. All four artifact JSONs `accepted=false`; appearance-heavy ranking still spent beam capacity on wrong paths.
- v16 (`29a83e3c88c8a8bdfa2e359452b48d873715b1f7`): motion-aware reranking of v15 candidate lattice. Completed audit below; rejected.

## v16 completed audit — authoritative
Workflow `.github/workflows/regress-exhibition-seed17-track16.yml`.
Run `34819659194`, head SHA `706db93595f8838c9b69b3978774e4b03a07cb04`.
Artifacts:
- Kiryu3 `10337124738`
- Kiryu6 `10337579200`
- Kiryu12 standard `10337757708`
- Kiryu12 varied `10337806966`

All four tracker jobs failed closed. FastClip and seed v17 succeeded, so this is algorithmic tracker failure, not environment/import failure.

### Kiryu3
- `accepted=false`, `FAIL_CLOSED: beam exhausted; no feasible multi-frame fleet hypothesis`.
- Died after step 2 / native frame 4.
- Beam sizes `[2,3]`.
- dominant dx: 1 -17.217, 2 -6.933, 3 +5.369, 4 +13.916, 5 +12.186, 6 +13.269.
- Seed boat6 `[616,961]`; best path boat6 already `[555,948]`, still moving strongly left against positive slit direction.
- No fallback was used. Soft reranking did not solve candidate/path feedback.
- FastClip metadata total ~5.554s.

### Kiryu6
- `accepted=false`, same beam-exhausted failure.
- Died after step 12 / native frame 24 (~0.8s).
- Beam sizes `[1,1,1,1,1,1,1,2,4,5,7,4]`.
- +0.5s centers were still plausible/distinct: 1 `[949.8,449.9]`, 2 `[884.9,502.1]`, 3 `[1001.8,606.8]`, 4 `[927.0,739.9]`, 5 `[857.3,825.1]`, 6 `[979.1,868.1]`.
- +0.5 identity NCC `[.876,.837,.920,.818,.848,null]`; anchor NCC `[.784,.743,.827,.708,.728,null]`; only boat6 had one fallback.
- FastClip metadata total ~5.773s.

### Kiryu12 standard
- Tracker reached the full 1.5s segment but failed the unchanged confidence gate rather than beam exhaustion.
- `accepted=false`, `FAIL_CLOSED: confidence-aware tracking quality insufficient`.
- Final beam size 7; minimum lane separation 23.888px.
- Fallback fractions: 1 .174, 2 .652, 3 .261, 4 0, 5 0, 6 .043.
- Median identity NCC: 1 .956, 2 .850, 3 .609, 4 .786, 5 .791, 6 .848.
- Boat2 is LOW because fallback fraction .652; boat3/4/5 MEDIUM. This is not a technical pass.
- +1.5 centers show 1/2/3 heavily left while 4/5 remain near x930-985, so physical identity still requires caution even aside from confidence failure.
- FastClip metadata total ~5.700s.

### Kiryu12 varied `1,2,4,5,6,3`
- `accepted=false`, beam exhausted after step 8 / native frame 16 (~0.53s).
- Beam sizes `[2,3,5,6,6,7,7,8]`.
- No fallback used on best path.
- +0.5 identity NCC `[.909,.939,.735,.914,.858,.785]`; anchor NCC `[.827,.878,.601,.859,.685,.634]`.
- Appearance is healthy at the visible horizon yet the prediction-feedback beam becomes globally infeasible.
- FastClip metadata total ~8.467s.

### v16 conclusion
Motion-aware reranking is insufficient because candidate generation and lane cells still depend on the previous hypothesis. A wrong hypothesis can therefore change which candidates exist in later frames. Increasing beam width or weakening NCC/reverse/geometry gates is not the principled fix.

## CURRENT candidate: tracker v17 fixed-candidate fleet DP
File `track_exhibition_boats_v17.py`.
Implementation commit `55868226fc372d8655beee4c46bc19ed6248fa16`.
Workflow `.github/workflows/regress-exhibition-seed17-track17.yml`.
Workflow creation/trigger commit `fa38030263ccdf58552b0612b3c5dd53cd41d3c3`.
Run **`34823290910`** launched on the Japan self-hosted runner; it was queued at this handoff update.

### v17 design
This is the first deliberately state-independent visual candidate graph in the tracker line.
- Each frame/boat builds immutable seed-anchor NCC peaks once, independent of every previous track hypothesis.
- Search lane bands come only from immutable slit-frame seed y geometry plus a resolution-relative elapsed-time expansion; they never follow tracked centers.
- Per-frame six-boat fleet states enforce entry-order, minimum separation, edge, duplicate-patch and immutable slit-direction cumulative safety.
- A temporal fleet DP/beam then links those fixed current-frame states with unchanged-style maximum-step and reverse-direction hard gates.
- Transition scoring penalizes reverse slit-motion and abrupt velocity changes, but does not alter which visual candidates exist.
- No prediction fallback is synthesized: if a boat has no anchor candidate >= the existing min NCC (.48), v17 fails closed.
- No result, future-frame candidate generation, boat-number rule, race-specific offset, or confidence-threshold relaxation is used.

Workflow args: `--stride 2 --topk 6 --frame-state-keep 96 --beam-width 24`.
These widths increase path coverage but do not relax any visual/safety acceptance gate.

## Exact restart point
1. Inspect Run `34823290910` jobs/artifacts as soon as they complete.
2. If there is a coding/runtime error, fix v17/workflow and rerun immediately.
3. If tracker executes, inspect artifact JSON rather than workflow conclusion alone.
4. For each race record accepted/reason, failure step, frame-state sizes, beam sizes, median NCC, min separation, +0.5/+1.0/+1.5 centers, trajectory sanity, tracker runtime, FastClip time and total operational latency.
5. Specifically require Kiryu3 boat6 not to take early reverse-left path and Kiryu6 boats5/6 to remain distinct through +1.5s.
6. Verify Kiryu12 standard and varied do not regress.
7. Do NOT relax min-NCC, reverse corridor, geometry/order, or edge gates merely to pass.
8. If fixed-candidate v17 still fails due anchor-only appearance ambiguity, next principled direction is state-independent multi-scale/descriptor appearance candidates (e.g. immutable patch pyramid/gradient descriptor) feeding the same fixed candidate graph, not a return to prediction-feedback cells.
9. Only after one unchanged seed+tracker passes all four physically sane and <=60s, update `run_exhibition_ses_live_local.py` and perform a self-hosted end-to-end live-style validation.
10. Update this handoff after every meaningful change with exact commits, Run IDs, artifact IDs/evidence and restart point.

## Production wrapper
`run_exhibition_ses_live_local.py` remains old seed v1 + tracker v3. DO NOT update until an unchanged seed+tracker passes the full technical matrix with sane identity/geometry and <=60 sec.

## Live-ready milestone
Before user notification as complete:
- multiple independent September samples including varied entry;
- automatic acquisition + seed + tracker only, no manual/race-specific edits;
- accepted with sane identity/geometry and fail-closed retained;
- ideally <=30 sec, maximum <=60 sec;
- `run_exhibition_ses_live_local.py` updated to validated pipeline;
- >=1 self-hosted end-to-end live-style success.
Prefer 10+ samples before treating SES as stable/predictive. SES remains an attack/head-support feature candidate, not direct finishing-order rank.
