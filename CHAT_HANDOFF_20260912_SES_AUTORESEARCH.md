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
Kiryu6 evidence continues to indicate that v17 can place rescued outer rows plausibly; the current blocker is tracker identity preservation, not more race-specific seed movement.

## Tracker history summary
- v8 (`264bf494812b6b72e4af94cacc1d40b009a6dde1`): per-frame joint six-boat assignment. Kiryu12 standard/varied passed, Kiryu3/Kiryu6 failed.
- v9 (`30a7b7ad2e44e51ccd2d0d2c0df0e32b5c265608`): immutable seed-frame appearance memory. Still allowed outer-row wake/background collapse.
- v10: fleet-affine y-cell reference. Rejected after all four matrix jobs failed closed and previously healthier samples regressed.
- v11 (`372aea94e0f718cc7dc2be3502c8761f33433ecf`): immutable slit-motion corridor on top of v9. Run `34788921925` completed and all four jobs failed closed. It prevented unsafe continuation but was too myopic to recover a feasible per-frame assignment.

## v11 artifact audit — run 34788921925
Artifacts:
- Kiryu3 `10327364118`
- Kiryu6 `10327830258`
- Kiryu12 standard `10327513405`
- Kiryu12 varied `10327785765`

Key findings:
- Kiryu3: `FAIL_CLOSED: no feasible joint six-boat assignment` extremely early (last completed step 2 / native frame 4). Candidate counts still existed `[2,3,3,3,2,2]`, showing the motion corridor + single-frame joint geometry eliminated every combination rather than a download/seed/runtime failure. No fallback had been used yet.
- Kiryu3 v17 slit directions remained coherent: boats 3-6 positive dominant_dx; therefore the earlier boat6 reverse/off-frame pathology is a genuine identity issue, but hard per-frame filtering alone is not enough.
- Kiryu6: `FAIL_CLOSED: no feasible joint six-boat assignment` at step 16 / native frame 32. At +0.5s boats5/6 remained distinct and moving right; by +1.0s boat5 had fallen back toward x~728.8 while boat6 was x~1134.8. Fallback counts were boat5=6, boat6=1. This again points to temporal path ambiguity rather than seed placement.
- No quality thresholds were relaxed and no blind race results were read.

Conclusion from v11: do not loosen the corridor/NCC gates. A stronger multi-frame temporal likelihood is required so a locally high-NCC wake/background candidate cannot win repeatedly and so feasible identity paths are judged using recent trajectory history rather than one frame in isolation.

## CURRENT candidate: tracker v12 temporal motion-memory joint assignment
File: `track_exhibition_boats_v12.py`
Implementation commit: `13a929a8a296ac92247ba6664f9e5bd35ec9cb4e`
Workflow: `.github/workflows/regress-exhibition-seed17-track12.yml`
Workflow commit: `c725772c4ec2cf68651a91258159a553b0a53c7c`
Run: `34804266678`

v12 design:
- retain v9 candidate generation, immutable anchor memory, adaptive template rules, dynamic lane cells, NCC thresholds, fallback caps, entry-order/spacing/edge fail-closed checks and stride2;
- retain v11 immutable result-blind slit-direction sanity bounds;
- add a generic four-step per-boat motion memory to joint scoring;
- score candidates against the robust median of recent selected step vectors and penalize acceleration from the immediately prior step;
- hard-reject only dramatic x reversal against a stable recent motion history;
- no future frame, race result, boat-number rule, race-specific offset or threshold relaxation;
- this is a principled temporal-likelihood step toward beam/Viterbi tracking, but remains greedy at each frame. If it still fails, the next architecture should retain multiple fleet hypotheses across frames instead of further threshold tuning.

## v12 validation matrix / exact restart point
Run `34804266678` launched on the Japan self-hosted runner at 2026-09-14 12:56 JST and was queued/in progress at this handoff update.
Unchanged four videos:
1. 2026-09-10 Kiryu3 standard — result remains blind.
2. 2026-09-10 Kiryu6 standard — result remains blind.
3. 2026-09-10 Kiryu12 standard — technical calibration.
4. 2026-09-09 Kiryu12 varied entry `1,2,4,5,6,3` — technical regression.

Next run must:
1. Inspect all four v12 jobs and artifacts, not workflow green alone.
2. Verify Kiryu3 boat6 does not reverse/run off-frame and determine whether v12 survives beyond v11 step2.
3. Verify Kiryu6 boats5/6 remain distinct and physically sane through +1.5s and whether fallback accumulation is reduced.
4. Verify Kiryu12 standard/varied are not regressed.
5. Record accepted/failure reason, fallback fractions/counts, median identity/anchor NCC, min lane separation, +0.5/+1.0/+1.5 centers, and FastClip+seed+tracker latency.
6. If v12 still fails safely, do NOT tune thresholds to force a pass. Implement a true multi-hypothesis beam/Viterbi-style fleet tracker that keeps several joint assignments across frames using immutable appearance + motion + fleet geometry likelihood.
7. Only after one unchanged seed+tracker combination passes all four physically sane and <=60 sec, update `run_exhibition_ses_live_local.py` and perform a self-hosted end-to-end live-style validation.
8. Update this handoff after every meaningful result/design change with exact commit SHA, Run ID and artifact IDs/evidence.

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
