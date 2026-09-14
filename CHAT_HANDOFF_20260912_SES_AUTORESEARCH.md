# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-14 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Purpose
Continue BOATCAST start-exhibition video development until immediate post-exhibition live use is reliable: result-blind FastClip -> automatic six-boat seed -> automatic tracking -> SES -> later model re-evaluation, with no manual seed editing.

## Non-negotiable rules
- Latest GitHub code/results override this handoff and old chat memory.
- Never inspect race results before locking exhibition-only judgement on blind/pristine samples.
- 2026-09-10 Kiryu3/6/9 results remain unread; preserve blindness.
- 2026-09-09 Kiryu12 and 2026-09-10 Kiryu12 are exposed technical samples only.
- July/August 2026 are NON-PRISTINE/research-only.
- Never weaken fail-closed gates merely to obtain accepted=true.
- Never hard-code boat-number/race-specific offsets.
- accepted=true is necessary but not sufficient: trajectories must remain physically sane/on-frame and preserve identity.
- Final race-by-race operation should be persistent on Japan self-hosted PC; Actions are validation/logging.
- Exact Japan Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.
- Live latency target: ideal <=30 sec after video availability, maximum <=60 sec.

## Seed state
Current seed remains `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`.
Evidence continues to indicate the principal blocker is tracker identity/path preservation, not race-specific seed movement.

## Tracker progression retained
- v8 joint per-frame assignment: Kiryu12 std/var passed, Kiryu3/6 failed.
- v9 immutable appearance memory: rejected.
- v10 fleet-affine y reference: rejected.
- v11 slit-motion corridor: safe but insufficient.
- v12 short motion memory: failed safely.
- v13 first multi-hypothesis fleet beam: beams eventually died.
- v14 prediction-local diversification: unstable; one weak Kiryu6 acceptance only.
- v15 immutable-anchor lattice + beam: all four accepted=false.
- v16 motion-aware reranking: all four failed; candidate generation still depended on prior hypothesis.
- v17 fixed state-independent candidate graph + temporal fleet DP: all four failed; each frame still had 96 safe states but globally pruned states lost coherent paths.
- v18 hypothesis-diverse fixed-state DP: completed and rejected below.

## v18 completed audit — authoritative
File `track_exhibition_boats_v18.py`, implementation commit `06595fa7358635bb8a3ff61bc3d96e2cc7beaeae`.
Regression workflow `.github/workflows/regress-exhibition-seed17-track18.yml`, workflow commit `ceff05bd59a0d391c0933fee61028f9dbea6d1d5`, trigger commit `5849d9d3a96feaa0e816b280a8e4675a26e3e566`.
Run **`34826924155`**.
Artifacts:
- Kiryu12 standard: `10340945535`
- Kiryu12 varied: `10340459285`
- Kiryu3: `10340249913`
- Kiryu6: `10339919034`

All four tracker jobs failed closed. FastClip and seed v17 succeeded; this is algorithmic search/path exhaustion, not environment/import failure. No results were read and no quality gate was relaxed.

Exact v18 diagnostics from artifact JSON:
- Kiryu3: `FAIL_CLOSED: fixed-candidate DP exhausted; no feasible temporal path`; last completed step 2 / native frame 4; frame states `[96,96,96]`; beam sizes `[2,1]`; tracker 3.247s; FastClip 5.388s. Last centers included boat6 `[555,948]` from seed `[616,961]`, already moving opposite its positive slit `dominant_dx=+13.269`.
- Kiryu6: same failure; last step 6 / native frame 12; seven frames each retained 96 states; beam sizes `[1,1,1,1,1,1]`; tracker 6.710s; FastClip 4.145s. Last centers boat5 `[826,816]`, boat6 `[954,866]`; slit directions remained strongly positive for 5/6.
- Kiryu12 standard: same failure; last step 8 / native frame 16; nine frames each retained 96 states; beam sizes `[5,3,4,2,2,2,2,4]`; tracker 5.515s; FastClip 4.222s.
- Kiryu12 varied: same failure; last step 6 / native frame 12; seven frames each retained 96 states; beam sizes `[1,1,1,1,1,1]`; tracker 6.414s; FastClip 5.411s.

Conclusion: v18 search diversity after a GLOBAL current-frame state pool is still too late. Even with 96 safe states on every processed frame, the temporally reachable alternatives are not retained. Increasing the fixed global state budget or loosening safety/NCC gates is not the principled fix.

## CURRENT candidate: tracker v19 predecessor-conditioned fleet beam
File `track_exhibition_boats_v19.py`.
Implementation commit **`a305634c8a136e40165303f3df9c88cc4af591bd`**.
Regression workflow `.github/workflows/regress-exhibition-seed17-track19.yml`.
Workflow creation commit **`9b7739c3316c009c3a954541751ebc4272068787`**.
Run **`34835647158`** launched on the Japan self-hosted runner and was queued/running at this handoff update.

### v19 design
v19 implements the exact next principled direction from the v18 failure and keeps the v17 visual/safety/final gates unchanged.
- Current-frame search is conditioned on EACH surviving beam predecessor instead of first globally truncating current-frame fleet states.
- For each boat/predecessor, candidate search combines immutable-anchor peaks from the full immutable seed-derived lane band with additional immutable-anchor NCC peaks inside the predecessor's physically reachable window.
- Candidates still must satisfy the same per-step maximum movement; no unsafe fallback is restored.
- Joint fleet states are built and safety-checked separately for each predecessor, then scored with the unchanged v17 transition function.
- Keep up to 5 distinct per-boat candidates and 12 K-best joint expansions per predecessor; combine all predecessor expansions, then choose an identity-diverse global beam of 24 using maximum per-boat displacement for deduplication.
- Workflow uses `--stride 2 --topk 6 --per-boat-keep 5 --per-path-keep 12 --beam-width 24`.
- Same min-NCC .48, strong-NCC .80, geometry/order, edge, duplicate-patch, slit-motion reverse, step-size and final confidence gates.
- Candidate generation uses only immutable slit appearance plus current/past frame predecessor state; no future frame/result leakage, no boat-number rule, no race-specific offset.

## Exact restart point
1. Inspect Run `34835647158` all four jobs as soon as they complete.
2. If there is a coding/runtime error, inspect logs, fix and rerun immediately.
3. If tracker executes, inspect artifact JSONs, not workflow color alone.
4. Record accepted/failure reason, predecessor_counts, expanded_counts, beam_sizes, median NCC, min lane separation, +0.5/+1.0/+1.5 centers, physical sanity, FastClip/seed/tracker latency.
5. Specifically require Kiryu3 boat6 not to run reverse-left/off-frame and Kiryu6 boats5/6 to remain distinct/sane through +1.5s.
6. Confirm Kiryu12 standard and varied-entry samples are not regressed.
7. Do NOT relax min-NCC, reverse corridor, geometry/order, edge, step-size or confidence gates merely to pass.
8. If v19 fails because predecessor-conditioned per-boat candidate lists still vanish, next inspect whether the immutable anchor itself has become appearance-unstable; consider a causally updated appearance ensemble gated by agreement with the immutable anchor and motion/geometry, not a free adaptive template.
9. If v19 succeeds technically but runtime exceeds 60s, optimize matchTemplate reuse/response caching before any production wiring.
10. Only after one unchanged seed+tracker passes all four physically sane and <=60 sec, update `run_exhibition_ses_live_local.py` and perform a Japan self-hosted end-to-end live-style validation.
11. Update this handoff after every meaningful result/design change with exact commits, Run IDs, artifact IDs/evidence and restart point.

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
