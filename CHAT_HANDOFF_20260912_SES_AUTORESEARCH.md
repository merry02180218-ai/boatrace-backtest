# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-12 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Purpose
Continue development of the BOATCAST start-exhibition video pipeline until reliable enough for immediate post-exhibition live use: result-blind clip acquisition -> automatic six-boat seed/tracking -> SES -> later model re-evaluation, with no manual seed editing.

## Non-negotiable rules
- Latest GitHub code/results override old chat memory and this handoff.
- Never inspect race results before locking exhibition-video judgement for a blind/pristine validation sample.
- July/August 2026 are NON-PRISTINE / research-only. Prefer September for clean validation.
- Do not weaken fail-closed quality gates merely to get `accepted=true`.
- Do not hard-code boat-number-specific or race-specific offsets.
- Do not production-wire an experimental seed/tracker until it generalizes across multiple independent races.
- GitHub Actions are validation/logging; final race-by-race operation should be a persistent process on the Japan self-hosted PC.
- Japan Python is exactly `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`; do not guess another path.

## Live latency target
SES ideally <=30 sec after video availability, maximum <=60 sec.
Downloader: `download_boatcast_exhibition_fastclip.py`.
Tracker: `track_exhibition_boats_v5.py` with stride 2, arbitrary entry order, confidence tiers and fail-closed gate. Do not relax tracker gates.

## Historical baseline and diagnosis
v9 was the prior best baseline, with accepted September technical passes on 2026-09-10 Kiryu12 standard order and 2026-09-09 Kiryu12 varied order `1,2,4,5,6,3`.
v11 then failed on result-blind 2026-09-10 Kiryu3 because fleet geometry alone could seed wake/background instead of hull identity.
v12 added multi-horizon NCC persistence and rescued boat5, but boat6 still falsely passed persistence while its matched track moved opposite the row's dominant LK direction.

## v13 CURRENT LEADING CANDIDATE
File: `auto_seed_exhibition_motion_v13.py`
Implementation commit: `2e4c8966637f5ea175a50e227f03f48659dfd23d`

Generic/result-blind method:
- wraps v12 candidate generation;
- every final seed must pass v9-style multi-horizon persistence;
- if `abs(dominant_dx) >= 2.5 px`, the persistence track must move in the same horizontal direction with net magnitude >=4 px;
- near-zero motion rows are exempt from sign gating;
- failed rows search a resolution-relative horizontal grid and must pass persistence + direction + fleet/neighbor geometry guards;
- no boat number, race result, or race-specific offset is used.

### Blind technical sample: 2026-09-10 Kiryu3
Run `34688954987`, job `103540747403`, standard entry order.
- accepted=true, ALL SIX HIGH.
- FastClip 6.855 sec, seed 14.025 sec, tracker ~6.98 sec, core ~27.9 sec.
- fallback: 1 0, 2 0, 3 0, 4 0, 5 .261, 6 .478.
- median NCC: 1 .969, 2 .874, 3 .918, 4 .880, 5 .953, 6 .978.
- all centers remained on-frame through +1.5 sec.
Locked exhibition-only SES (DO NOT look up result yet): 1=-3, 2=-1, 3=+1, 4=+1, 5=0, 6=+2.

### UNCHANGED v13 regression: 2026-09-10 Kiryu12
Workflow-only default change commit `36fb7fd196637a5c9f07a1975dc8c9606b25de4c`; v13 code unchanged.
Run `34698720223`, job `103566588458`.
- selected_sec 27.75.
- accepted=true, ALL SIX HIGH.
- seeds: 1 [1169,429], 2 [1157,471], 3 [1033,498], 4 [1070.5,559], 5 [939.5,589.5], 6 [587,707].
- v13_rescued_row_count=0; direction checks sane.
- fallback: 1 .348, 2 0, 3 0, 4 .130, 5 0, 6 .043.
- median NCC: 1 .965, 2 .848, 3 .831, 4 .825, 5 .875, 6 .883.
- FastClip 12.904 sec, seed 9.971 sec, tracker 7.744 sec, core ~30.62 sec. Slightly above ideal 30 only due slower clip/network, well below 60.
- geometry/on-frame checks passed.

### UNCHANGED v13 varied-entry regression: 2026-09-09 Kiryu12
Workflow-only default change commit `1ef1ff173a913e9c17f99ce5b830a525148d3755`; v13 code unchanged.
Run `34698851667`, job `103566940681`, entry order `1,2,4,5,6,3`.
- selected_sec 30.0.
- v12 rescued rows 1 and 2 generically; v13_rescued_row_count=0 after direction checks.
- final seeds: 1 [745.5,429.5], 2 [686,475], 4 [916,514], 5 [1023,625], 6 [1134,720], 3 [1069,740.5].
- accepted=true, ALL SIX HIGH.
- fallback: 1 .304, 2 .304, 3 0, 4 0, 5 0, 6 0.
- median NCC: 1 .979, 2 .907, 3 .805, 4 .910, 5 .890, 6 .948.
- FastClip 7.123 sec, seed 9.391 sec, tracker 7.199 sec, core ~23.71 sec.
- all +0.5/+1.0/+1.5 centers remained on-frame and ordered consistently with the supplied varied entry order.
- This improves the older v9 regression, where boat3 was only MEDIUM; v13 makes all six HIGH without changing quality thresholds.

## Current validation state
UNCHANGED v13 is now **3-for-3 on September technical video samples**:
1. 2026-09-10 Kiryu3 — accepted=true, ALL HIGH, blind SES locked, result still not accessed.
2. 2026-09-10 Kiryu12 — accepted=true, ALL HIGH.
3. 2026-09-09 Kiryu12 varied entry `1,2,4,5,6,3` — accepted=true, ALL HIGH.
This is strong technical generalization evidence, but NOT yet live-ready.

## Fourth-sample source
Historical result-blind acquisition workflow `.github/workflows/blind-validate-kiryu-20260910-batch.yml`, run `34579347851`, originally produced race3/race6/race9 artifacts. Old race6 artifact `10191134655` is now unavailable/expired (fresh download returned 404), so reacquire a fresh result-blind clip for Kiryu6 or Kiryu9. Derive entry order only from pre-race video/overlay/contact sheet; do not inspect results.
Results for 2026-09-10 Kiryu3/6/9 have not been looked up in this SES thread. Preserve that blindness.

## Production/live wrapper
`run_exhibition_ses_live_local.py` is still old (seed v1 + tracker v3). Do NOT update until the fourth independent sample is technically validated. Once validated, wire v13 + tracker v5 stride2 + `exhibition_tracking_v5.json`, then run one self-hosted end-to-end live-style validation.

## Performance optimization
v13 seed time is inflated because it nests v11 -> v12 -> v13 checks. Correctness is currently acceptable (<60 sec total on tested samples). After fourth-sample validation and before/after wrapper integration, refactor to a single-pass equivalent only if outputs/quality are preserved exactly; do not trade away gates for speed.

## Live-ready milestone
Before notifying user as complete:
- multiple independent September samples including varied entry order;
- automatic acquisition + automatic seed + tracker only, no manual seed/race-specific offset;
- tracker accepted with sane identity/geometry and fail-closed retained;
- core ideally <=30 sec, <=60 sec maximum;
- `run_exhibition_ses_live_local.py` updated to validated pipeline;
- at least one end-to-end self-hosted live-style validation succeeds.
Ideally expand to 10+ samples before treating SES as stable/predictive. SES remains an attack/head-support feature candidate, not direct finishing-order rank.

## Immediate next actions
1. Freshly reacquire result-blind 2026-09-10 Kiryu6 or Kiryu9 exhibition clip.
2. Determine actual exhibition entry order only from the video/overlay, without race-result lookup.
3. Run UNCHANGED v13 and inspect full tracker JSON/logs/geometry, not merely workflow green.
4. If fourth sample passes, update `run_exhibition_ses_live_local.py` to v13 + tracker v5 stride2 and perform one self-hosted end-to-end live-style validation.
5. Update this handoff after each meaningful result or design change.
