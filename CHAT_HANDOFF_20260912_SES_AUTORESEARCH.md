# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-15 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Non-negotiable rules
Latest GitHub/artifacts win. 2026-09-10 Kiryu3/6/9 results remain unread. 2026-09-09 Kiryu12 and 2026-09-10 Kiryu12 are exposed technical samples only. July/August NON-PRISTINE. Never relax fail-closed/NCC/geometry/motion gates merely to pass. No boat/race-specific offsets. Production target persistent Japan self-hosted PC; ideal <=30 sec, maximum <=60 sec. Exact Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.

## Seed
Keep `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`. Current blocker is tracker identity/path representation, not race-specific seed movement.

## Retained progression
v8-v24 established independent/per-frame identity, immutable appearance alone, lane-cell geometry and fixed proposal reachability were insufficient. v25 causal trajectory reachability removed gross wrong-direction paths. v26 translation camera compensation improved feasibility but remained insufficient. v27 leave-one-out similarity run `34893353398` failed all four and was too slow. v28 run `34900743347` failed all four; Kiryu3 died step9/native18, tracker 54.566 sec. v29 run `34906246958` failed all four; shared robust similarity did not solve coordinate mismatch, Kiryu3 died step8/native16, 43.713 sec. Do not widen 24/20/42 motion caps. v30 had a monkey-patch integration defect and is not scientific evidence. v31 fixed-hook run `34939987130` exposed initial/later coordinate-model inconsistency. v32 run `34947013447` showed unconstrained initial affine fitting was too flexible and was rejected.

## v33 robust initial translation + later affine — rejected
`track_exhibition_boats_v33.py`; workflow bridge commit `e6c22636c552114dbfb650f6b01a7f7c0f723bad`; run `34952256254`. All four unchanged matrix jobs failed closed. FastClip and seed v17 succeeded; failures are tracker-scientific, not acquisition/runtime failures.

Kiryu3 artifact `10389529832` is especially diagnostic. v33 passed the first transition and survived to step9/native frame18, proving the robust initial shared translation solved the v31/v32 first-step degeneracy without relaxing the 42 px absolute ceiling. It then exhausted the beam. Diagnostics: v33 initial translation calls=90, initial relative-residual rejects=2, initial absolute-speed rejects=0; later v31 calls=2364 with relative-residual rejects=1271 and relative-acceleration rejects=292. Last centers included boat6 around [520,1016] from seed [616,961], while result remains unread. Therefore the dominant blocker moved to the later affine camera model / coordinate representation, not the initial transition.

Run `34952256254` artifact IDs: Kiryu3 `10389529832`, Kiryu6 `10389394053`, Kiryu12 `10390330408`, Kiryu12var `10390041110`. All four tracker jobs failed closed.

## CURRENT candidate: v34 robust shared translation on every transition
File `track_exhibition_boats_v34.py`, implementation commit `3e05d17d081faa126845a5e0cfeb3934f8be1cc2`. Workflow `.github/workflows/regress-exhibition-seed17-track27.yml` updated at commit `9881ee756934d80bec2618425791a8ec8c941ee9` to run only the unchanged four-sample technical matrix; the live-wrapper job was removed until a tracker actually passes the matrix.

Principle: use coordinate-wise median six-boat displacement as shared camera translation at every stride, not only the first. Gate each boat's camera-subtracted residual at the unchanged 24 px/native-frame cap and raw step at the unchanged 42 px/native-frame ceiling. From transition two onward compare camera-subtracted residual velocity to the previous camera-subtracted residual velocity with the unchanged 18 px/native-frame relative-acceleration cap. Reverse corridor remains unchanged. No future frame, result, boat-number rule, race-specific offset, or confidence relaxation.

Why v34 is principled: v33 showed initial translation is feasible while later affine generated the bulk of rejection. A 2-frame stride is short enough to test whether low-DOF shared translation is a more stable camera representation than repeatedly fitting candidate-dependent affine transforms. If v34 is too rigid, do not widen gates; move to externally estimated background camera motion or another candidate-independent low-DOF model.

Matrix remains unchanged:
1. 2026-09-10 Kiryu3 standard — result blind.
2. 2026-09-10 Kiryu6 standard — result blind.
3. 2026-09-10 Kiryu12 standard — exposed technical calibration.
4. 2026-09-09 Kiryu12 varied `1,2,4,5,6,3` — exposed technical regression.

## Exact restart point
1. Locate the Actions run triggered by workflow commit `9881ee756934d80bec2618425791a8ec8c941ee9` and inspect all four jobs/artifacts. If GitHub has not yet registered the push-triggered run, check again; do not assume it ran.
2. Record v34 dead-frame depth, `diagnostics_v34` residual/acceleration/absolute/reverse reject counts, accepted/failure reason and tracker latency for each sample.
3. For any accepted sample inspect +0.5/+1.0/+1.5 centers, on-frame identity sanity, fallback/NCC and min lane separation. Workflow green alone is insufficient.
4. If v34 still exhausts due shared-translation rigidity, next principled direction is candidate-independent camera motion estimated from background features (or a tightly bounded low-DOF model), not widening 24/18/42 caps.
5. Preserve Kiryu3/6/9 result blindness.
6. Only after one unchanged seed+tracker passes all four sane and <=60 sec should the production-style wrapper be pointed at that validated tracker, followed by >=1 Japan self-hosted end-to-end live-style validation.

## Production wrapper warning
Repository `run_exhibition_ses_live_local.py` currently points to v33. This conflicts with the older handoff claim that it was still v1/v3. Latest code wins: v33 is now known to fail the unchanged four-sample matrix, so DO NOT treat the current wrapper as live-ready and do not run it for betting decisions. v34 has deliberately NOT been production-wired.

## Live-ready milestone
Multiple independent September samples incl varied entry; fully automatic acquisition+seed+tracker; sane identity/geometry with fail-closed retained; <=60 sec (ideal <=30); production wrapper updated only to a validated tracker; >=1 self-hosted end-to-end live-style success. Prefer 10+ samples before treating SES as stable/predictive. SES is an attack/head-support feature candidate, not direct finishing-order rank.
