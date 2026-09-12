# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-13 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Purpose
Continue BOATCAST start-exhibition video development until immediate post-exhibition live use is reliable: result-blind FastClip -> automatic six-boat seed -> automatic tracking -> SES -> later model re-evaluation, with no manual seed editing.

## Non-negotiable rules
- Latest GitHub code/results override this handoff and old chat memory.
- Never inspect race results before locking exhibition-only judgement on blind/pristine samples.
- July/August 2026 are NON-PRISTINE/research-only; September preferred.
- Never weaken fail-closed quality gates merely to obtain `accepted=true`.
- Never hard-code boat-number-specific/race-specific offsets.
- Do not production-wire experimental code until multi-race technical generalization is demonstrated.
- Final race-by-race operation should be persistent on Japan self-hosted PC; Actions are validation/logging.
- Exact Japan Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.

## Latency target
Ideal <=30 sec after video availability; maximum <=60 sec.
Downloader: `download_boatcast_exhibition_fastclip.py`.

## v13 baseline — strong but fourth-sample failure
`auto_seed_exhibition_motion_v13.py`, commit `2e4c8966637f5ea175a50e227f03f48659dfd23d`.
Generic/result-blind NCC persistence + dominant-LK direction consistency + horizontal rescue.
UNCHANGED v13 passed three September technical samples with tracker v5:
1. 2026-09-10 Kiryu3 standard — run `34688954987`, accepted=true, ALL HIGH, core ~27.9s. Blind SES locked: 1=-3,2=-1,3=+1,4=+1,5=0,6=+2; result still MUST NOT be looked up.
2. 2026-09-10 Kiryu12 standard — run `34698720223`, accepted=true, ALL HIGH, core ~30.62s.
3. 2026-09-09 Kiryu12 varied entry `1,2,4,5,6,3` — run `34698851667`, accepted=true, ALL HIGH, core ~23.71s.

Fourth result-blind sample 2026-09-10 Kiryu6 exposed a new generic failure:
- commit/default `c53361a056965ef68633092a24e139b6b214be0a`, run `34699132130`, job `103567660609`.
- selected 28.0; seeds 1 [1025,459],2 [937,497],3 [990,599],4 [849,711],5 [749,770.5],6 [778,891.5].
- boat6 dominant LK dx +10.544 but persistence net dx -44, so v13 correctly rejected it; horizontal rescue found nothing.
- Result-blind frame inspection showed boat6 seed y~891.5 on a foreground rail/fence, with actual hull roughly ~96 px higher. Generic diagnosis: wrong-row/y seed cannot be fixed by x-only rescue.
- Race result remains unread and MUST remain blind.

## v14 — generic 2D fallback seed rescue
`auto_seed_exhibition_motion_v14.py`.
Starts from v12 and retains v13-style short persistence + direction gate. Only rows that fail those checks are searched on a resolution-relative 2D grid with fleet y-order/gap and neighbor-x geometry constraints. No race/boat rule.
Kiryu6 benchmark run `34699280445`, job `103568051600`:
- boat6 rescued generically from [778,891.5] to [818,795.5] (x+40,y-96).
- FastClip ~5.385s, seed ~31.807s, tracker v5 ~6.935s, core ~44.1s (<60).
- tracker v5 accepted=false: boats1-4 HIGH, boat5 MEDIUM fallback .391/NCC .874, boat6 LOW fallback .609/NCC .923.
- 5/6 trajectories converged by +1.0/+1.5 despite distinct seeds.
Diagnosis shifted from seed-only to tracker identity collision.

## Tracker v5 design limitation
`track_exhibition_boats_v5.py` tracks each boat independently. Template fallback uses a broad search ROI with no pairwise exclusion/dynamic lane partition; adjacent boats can converge onto the same wake/background patch. Lane separation is checked only after estimates are chosen. Therefore high NCC can still represent the wrong neighboring texture.

## v15/v16 experiment — reject as production direction
`auto_seed_exhibition_motion_v15.py` adds generic predicted-y 2D danger-row rescue.
`auto_seed_exhibition_motion_v16.py`, commit `466dbbce20912697efe554dc7c9bf3ad5d3d9544`, adds longer-horizon (~0.6/0.9/1.2s) validation and x-only long rescue.
Regression workflow commit `dd93b718ce12ee53f52665a246a11beca868ab9c`, run `34701030505`.
- Kiryu12var passed ALL HIGH (~44s total), but
- Kiryu3 failed lane separation because boat6 bad-y seed was moved only in x, leaving y wrong.
- Kiryu12 failed because v16 overrode known-good v13 boat3 [1033,498] after long-horizon NCC latched to an opposite-direction background/wake track; it moved boat3 to [1233,498], then tracker failed lane separation.
Conclusion: long-horizon template evidence is not trustworthy enough to override a seed that already passes v13 short persistence/direction. Future seed logic must preserve healthy v13-equivalent rows and use 2D fallback ONLY for rows v13-equivalent validation rejects.

## CURRENT tracker candidate: v6 dynamic lane partition
`track_exhibition_boats_v6.py`, commit `4436499f9bb2dd7cc8a3b49a3b75db81e198d13d`.
Principled change from v5:
- retain stride2, LK/template fusion and the SAME NCC/fallback fail-closed thresholds;
- determine entry order from initial seed y-order;
- before each tracking step, create dynamic vertical cells bounded by midpoints between neighboring previous centers;
- clip each boat's template search to its own cell and clip predictions into the cell;
- preserve entry order and >4px separation fail-closed checks;
- record minimum lane separation.
Goal: prevent adjacent 5/6 from matching the same wake/texture without relaxing quality gates.

## CURRENT regression in progress
Workflow `.github/workflows/regress-exhibition-seed14-track6.yml`, commit `a01689495e893dd3b4d5c8406a19c367ee733f0f`, run `34711310461`.
Matrix uses result-blind FastClip -> seed v14 -> tracker v6 unchanged on:
- 2026-09-10 Kiryu3 standard
- 2026-09-10 Kiryu6 standard
- 2026-09-10 Kiryu12 standard
- 2026-09-09 Kiryu12 varied entry `1,2,4,5,6,3`
At handoff update time first job was running and remaining jobs queued. Inspect actual logs/JSON, not workflow green alone.

## Blindness status
Results for 2026-09-10 Kiryu3/6/9 remain unread in this SES research thread. Preserve blindness. 2026-09-09 Kiryu12 result was exposed only after its earlier blind lock and is technical regression only now. 2026-09-10 Kiryu12 is technical calibration/exposed, not pristine predictive proof.

## Production wrapper
`run_exhibition_ses_live_local.py` remains old (seed v1 + tracker v3). Do NOT update until a candidate seed+tracker passes the four-sample technical matrix with sane identity/geometry and <=60s.

## Immediate next actions
1. Inspect run `34711310461` all four jobs/logs.
2. For each: seed decisions, selected_sec, runtime, tracker accepted, fallback fractions, median NCC, min lane separation, +0.5/+1.0/+1.5 centers and physical identity sanity.
3. If v14+tracker v6 passes all four unchanged and <=60s, freeze/refactor naming as needed, update `run_exhibition_ses_live_local.py`, then run one self-hosted end-to-end live-style validation.
4. If tracker v6 fails, do NOT relax thresholds. Diagnose whether dynamic cells are too rigid or bad seed geometry remains; next tracker change should remain generic and result-blind.
5. Update this handoff after every meaningful result/design change.

## Live-ready milestone
Before notifying user as complete:
- multiple independent September samples incl varied entry;
- automatic acquisition+seed+tracker only, no manual/race-specific edits;
- accepted with sane identity/geometry and fail-closed retained;
- ideally <=30s, maximum <=60s;
- `run_exhibition_ses_live_local.py` updated to validated pipeline;
- >=1 self-hosted end-to-end live-style success.
Prefer 10+ samples before treating SES as stable/predictive. SES remains an attack/head-support feature candidate, not direct finishing-order rank.
