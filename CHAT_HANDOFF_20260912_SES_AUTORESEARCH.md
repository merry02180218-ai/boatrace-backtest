# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-12 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Purpose
Continue development of the BOATCAST start-exhibition video pipeline until it is reliable enough for live use immediately after exhibition. The target is automatic result-blind acquisition, six-boat seeding/tracking, SES scoring, and later model re-evaluation without manual seed editing.

## Non-negotiable rules
- Latest GitHub code/results always override old chat memory.
- Never inspect race results before locking exhibition-video judgement for a blind/pristine validation sample.
- July/August 2026 are NON-PRISTINE / research-only.
- September 2026 onward is preferred for clean validation, but any sample whose result was already exposed must be marked calibration/non-pristine.
- Do not weaken fail-closed quality thresholds just to obtain `accepted=true`.
- Do not hard-code a boat-number-specific offset learned from one race.
- Do not wire an experimental seed/tracker into production LIVE until it generalizes across multiple independent races.
- GitHub Actions are for validation/logging. Final race-by-race operation should be a persistent process on the Japan self-hosted PC to avoid queue/startup delay.

## Live latency target
Target SES availability: within 30–60 sec after exhibition video becomes available; ideal <30 sec.

Japan self-hosted Python path:
`C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`

Do not guess alternate Python paths.

## BOATCAST acquisition
Player URL pattern:
`https://front.player.boatrace-cdn.jp/player/vod?raceDate=YYYYMMDD&raceNumber=N&raceType=exhibition&service=boatcast&stadium=01kiryu`

Current low-latency downloader:
`download_boatcast_exhibition_fastclip.py`

Typical benchmark setup:
- clip start: 82 sec
- duration: 52 sec
- player autoplay enabled
- playback response polled quickly
- ffmpeg input-side seek / stream copy

Known successful timings:
- 2026-09-10 Kiryu12: fastclip as low as ~4.2 sec on earlier run; latest v6 benchmark acquisition 13.515 sec.
- 2026-09-09 Kiryu12: acquisition 9.309 sec.

## Tracker
Current tracker:
`track_exhibition_boats_v5.py`

Key behavior:
- result-blind
- stride 2 (~15 fps effective on 30 fps video)
- LK prediction + bounded adaptive template matching
- arbitrary exhibition entry order
- lane-separation guard
- confidence-aware HIGH/MEDIUM/LOW quality
- overall `accepted=true` only when all six pass quality gates
- produces `ses_v5` only when accepted

Do not relax quality gates merely to pass.

## Seed history
### v3
`auto_seed_exhibition_motion_v3.py`
- permissive six-row LK detection
- per-row motion direction
- improved boats 2–6 on 2026-09-10 Kiryu12
- boat1 remained LOW in tracker

### boat1 calibration sweep
On 2026-09-10 Kiryu12, a result-blind technical seed sweep found that moving boat1 from `[1289,429]` to `[1169,429]` (x -120) produced tracker `accepted=true`.
This was diagnostic only; never hard-code boat1 -120 globally.

### v4/v5 seed attempts
- v4 moved too many boats and degraded tracking.
- v5 improved boat1 but fallback remained above limit.

### v6
Current file:
`auto_seed_exhibition_motion_v6.py`
Method:
`v3 permissive six-row LK + fleet-relative extreme-motion saturated correction`
- fleet median abs(dx)
- extreme threshold = median * 1.5
- extreme rows shifted by saturated +/-120 px
- boat-number agnostic

## v6 benchmark results
### 2026-09-10 Kiryu12 — technical calibration SUCCESS
Workflow run: `34603144372`
Commit before run: `cae871c60655713e5c3a4cfb61bffc8805ecdb1d`
Entry order: `1,2,3,4,5,6`
Selected sec: 27.75
Only boat1 corrected:
- boat1 motion center `[1289,429]`
- final seed `[1169,429]`
- saturated shift -120

Tracker v5:
- `accepted=true`
- all boats HIGH
- fallback fraction: 1=.348, 2=.000, 3=.000, 4=.130, 5=.000, 6=.043
- median NCC: 1=.965, 2=.848, 3=.831, 4=.825, 5=.875, 6=.883
- SES: 1=-3, 2=+1, 3=+1, 4=0, 5=0, 6=-2

Important warning: boat1 motion magnitude remained suspiciously extreme. Success on this one race is not enough for LIVE.

### 2026-09-09 Kiryu12 — independent generalization FAILURE
Workflow run: `34604306399`
Commit: `4e6b6c0b304506e14f20cbebfaa17f191c99c536`
Entry order: `1,2,4,5,6,3`
Fastclip: 9.309 sec
Seed v6: 5.029 sec
Selected sec: 30.0
Fleet median abs dx: 9.339
Extreme threshold: 14.008
Corrected rows: 2

Seeds:
- 1 `[797.5,429.5]`, no correction
- 2 `[853.0,475.0]`, no correction
- 4 `[912.0,514.5]`, no correction
- 5 `[1027.5,629.5]`, no correction
- 6 motion center `[1133.5,720.0]` -> final `[1253.5,720.0]` (+120)
- 3 motion center `[1069.0,740.5]` -> final `[1189.0,740.5]` (+120)

Tracker v5 failed closed:
`FAIL_CLOSED: lane separation too small`

Diagnosis:
v6's fleet-relative extreme-motion rule can over-correct multiple adjacent/nearby rows. In 9/9 it shifted both 6 and 3 right by +120, causing unsafe geometry/lane separation. Therefore v6 does NOT generalize and must NOT be used in LIVE.

## Exact next research direction: v7+
Build a principled seed refinement that preserves the useful 9/10 boat1 correction while preventing 9/9 multi-row over-correction.

Preferred constraints:
1. Start from v3 seeds.
2. Treat motion-extreme detection only as a proposal, not an unconditional +/-120 move.
3. Add neighbor/geometry constraints before accepting a correction:
   - preserve initial top-to-bottom entry order
   - enforce minimum y separation / lane separation
   - avoid moving two adjacent rows in the same direction if it collapses geometry
   - cap correction based on nearest-neighbor x/y geometry, not a universal fixed 120
   - if corrected candidate violates geometry, reduce shift or revert that row
4. Prefer one-pass automatic refinement; no 21-way tracker sweep in live operation.
5. Remain result-blind.
6. Fail closed if confidence is insufficient.

Possible implementation name:
`auto_seed_exhibition_motion_v7.py`

## Validation plan
Before LIVE integration, require multiple independent races with different entry orders/camera geometry.
Minimum practical acceptance gate before wiring production:
- at least 3 independent September samples (more is better)
- automatic acquisition + automatic seed + tracker only; no manual seed edits
- tracker accepted on all required samples, or a documented fail-closed rate low enough for operational use
- no systematic absurd center displacement / identity jumps
- arbitrary entry order handled correctly
- result-blind lock before any result comparison
- core processing latency around <=30 sec where feasible and <=60 sec maximum target

Then expand toward 10+ samples before treating SES as a stable feature.

## Scientific interpretation of SES
SES is currently an attack/head-support feature candidate, NOT a direct finishing-order ranking.
Known blind sample 2026-09-09 Kiryu12 from earlier v3/manual-seed work:
- locked SES direction supported boat3 attack; boat3 later won by makuri
- lower SES boats still finished 2nd/3rd
Therefore do not equate SES rank with finishing order.

## Production/live wrapper
Current wrapper:
`run_exhibition_ses_live_local.py`
Known state before this handoff:
- still old pipeline using `auto_seed_exhibition_motion_v1.py`
- still using `track_exhibition_boats_v3.py`
- output `exhibition_tracking_v3.json`

Do NOT switch it to v6.
Only after v7+ passes multi-race validation, update wrapper to the validated seed version + tracker v5 (or newer), `--stride 2`, and output the validated SES result.

After that, implement persistent watcher on Japan self-hosted PC:
`exhibition finished -> detect VOD availability -> fetch only start segment -> auto seed -> track/SES -> model re-evaluation -> odds -> betting decision`

## Workflow used for technical benchmark
`.github/workflows/benchmark-fast-exhibition-clip.yml`
It currently supports workflow_dispatch inputs for race_date, stadium, race, clip start/duration, entry order and runs on `[self-hosted, japan]`.

## Required behavior for future ChatGPT sessions
When resuming:
1. Read THIS file first.
2. Read latest GitHub commits/workflows/files; GitHub latest wins over this file if newer.
3. Check whether an automation/research iteration has created v7 or later.
4. Inspect actual workflow logs/results, not just green/red workflow status.
5. Continue implementing/testing autonomously when asked to continue.
6. Keep this handoff updated after meaningful design/result changes, especially before chat context may run out.
7. Never claim success without actual `accepted=true` evidence and geometry sanity across multiple independent races.

## Definition of "done enough to notify user"
Notify the user when the automatic pipeline has reached a credible LIVE-ready milestone:
- a seed/refinement version generalizes across multiple independent September races with varied entry order,
- tracker quality gates pass without manual seeds or race-specific hard-coded offsets,
- geometry/identity checks are sane,
- latency is compatible with post-exhibition live use,
- live local wrapper has been updated to the validated pipeline,
- at least one end-to-end self-hosted validation run succeeds.

Even after this milestone, continue collecting blind samples before declaring SES statistically predictive of race outcomes.
