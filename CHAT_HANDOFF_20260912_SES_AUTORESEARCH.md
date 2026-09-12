# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-12 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Purpose
Continue development of the BOATCAST start-exhibition video pipeline until it is reliable enough for live use immediately after exhibition. The target is automatic result-blind acquisition, six-boat seeding/tracking, SES scoring, and later model re-evaluation without manual seed editing.

## Non-negotiable rules
- Latest GitHub code/results always override old chat memory or this handoff.
- Never inspect race results before locking exhibition-video judgement for a blind/pristine validation sample.
- July/August 2026 are NON-PRISTINE / research-only.
- September 2026 onward is preferred for clean validation; exposed-result samples may be technical calibration only and results must not influence seed/tracker tuning.
- Do not weaken fail-closed quality thresholds just to obtain `accepted=true`.
- Do not hard-code a boat-number-specific or race-specific offset.
- Do not wire an experimental seed/tracker into production LIVE until it generalizes across multiple independent races.
- GitHub Actions are for validation/logging. Final race-by-race operation should be a persistent process on the Japan self-hosted PC to avoid queue/startup delay.

## Live latency target
Target SES availability: within 30–60 sec after exhibition video becomes available; ideal <30 sec.
Japan self-hosted Python path: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.
Do not guess alternate Python paths.

## Current acquisition / tracker
Downloader: `download_boatcast_exhibition_fastclip.py`.
Tracker: `track_exhibition_boats_v5.py` (result-blind, stride 2, arbitrary entry order, confidence HIGH/MEDIUM/LOW, fail closed). Do not relax tracker gates.

## Historical leading baseline: v9
`auto_seed_exhibition_motion_v9.py` uses geometry-aware timing plus multi-horizon 0.15/0.30/0.45/0.60 sec persistence to decide isolated extreme-motion shifts.
Confirmed unchanged-code September technical passes:
- 2026-09-10 Kiryu12, standard order, run `34687887563`: accepted=true, ALL HIGH, core ~17.1 sec.
- 2026-09-09 Kiryu12, order `1,2,4,5,6,3`, run `34687982108`: accepted=true; 1/2/4/5/6 HIGH, 3 MEDIUM, core ~18.2 sec.
This remains an important regression baseline.

## v11 third-sample failure — 2026-09-10 Kiryu3
Latest GitHub before this automation had `auto_seed_exhibition_motion_v11.py` (2D fleet-coherence guarded seed). Run `34688425067`, job `103539381219`, result-blind standard order `1,2,3,4,5,6`.
- selected 27.75 sec
- seeds: 1 [1100,417], 2 [1011,485], 3 [948,581], 4 [830,665], 5 [642.5,810], 6 [776,865]
- tracker accepted=false
- 1–4 HIGH; 5 LOW fallback .957/NCC .904; 6 LOW fallback .826/NCC .882
- boat6 center ran off-frame by +1.5 sec.
Contact/technical inspection showed boat5 seed on wake/background. This proved fleet geometry alone does not guarantee boat identity.

## v12 — persistence rescue
File `auto_seed_exhibition_motion_v12.py`, implementation commit `38e6480caba4fc25c0140fd21932dde71f70025e`; benchmark workflow commit `fd197b0f62ca98baddd6981a1753b795b38a4674`; run `34688826265`.
Generic/result-blind method:
1. Start from v11.
2. Evaluate every final seed with v9 multi-horizon persistence.
3. Keep persistence-pass seeds.
4. Only failed rows search a resolution-relative horizontal grid.
5. Candidate must pass persistence and neighbor-jump sanity.
6. Among near-best visual candidates, prefer local fleet x-vs-y geometry.
No boat-number-specific rule.

Kiryu3 evidence:
- FastClip 6.95 sec; v12 seed 9.749 sec; tracker 6.983 sec; core ~23.7 sec.
- boat5 base [642.5,810] failed persistence; rescue chose x802.5 (+160) based on strong persistence plus fleet geometry.
- boat5 improved to HIGH fallback .261/NCC .953.
- boat6 remained LOW because its seed falsely passed NCC persistence.
- overall accepted=false.
Critical diagnosis: boat6 seed x776 had dominant LK dx +13.269, but v9 persistence matched centers moved left (roughly 742→735→679→625; net about -151 px). Thus coherent background/wake texture can pass NCC while moving opposite the row's observed motion.

## v13 CURRENT LEADING CANDIDATE — direction-consistent persistence rescue
File `auto_seed_exhibition_motion_v13.py`.
Implementation commit `2e4c8966637f5ea175a50e227f03f48659dfd23d`.
Benchmark workflow commit `e9463d6eec6e002d041d8cfb085b1ddf3e3234f6`.
Run `34688954987`, job `103540747403` on result-blind 2026-09-10 Kiryu3, standard entry order.

Method:
- Wraps v12.
- Every final v12 seed is checked with v9 persistence AND a generic direction-consistency rule.
- For rows with |dominant_dx| >= 2.5 px, net horizontal matched-track motion must have the same sign and magnitude >=4 px.
- Near-zero-motion rows are exempt from sign gating because direction is not reliable enough.
- If persistence or direction fails, search a resolution-relative horizontal grid; rescue candidate must pass both, plus neighbor/fleet geometry guards.
- No race outcome is used and no boat number has a special correction.

Kiryu3 result:
- FastClip total 6.855 sec (resolve 3.484 + download 3.371).
- v13 seed 14.025 sec. This currently includes nested v11→v12→v13 repeated validation work and is a future optimization target.
- tracker ~6.98 sec.
- core ~=27.9 sec, narrowly inside ideal <=30 sec.
- v13 kept direction-consistent rows and caught boat6's false opposite-direction NCC track, then rescued it.
- tracker `accepted=true`.
- ALL SIX HIGH.
- fallback fractions: 1 0.0, 2 0.0, 3 0.0, 4 0.0, 5 .261, 6 .478.
- median NCC: 1 .969, 2 .874, 3 .918, 4 .880, 5 .953, 6 .978.
- all +0.5/+1.0/+1.5 centers remained on-frame; no prior boat6 off-frame pathology.

Blind exhibition-only SES for Kiryu3 is now locked by CI output (DO NOT look up race result yet):
- 1: relative +1.5 -278.763, rank6, SES -3
- 2: -131.514, rank5, SES -1
- 3: +103.982, rank2, SES +1
- 4: +92.109, rank3, SES +1
- 5: -5.510, rank4, SES 0
- 6: +199.697, rank1, SES +2
These are exhibition judgements only; do not tune from race outcome.

## Current validation state
v13 has ONE accepted independent third-sample run (Kiryu3). It is NOT live-ready yet. Freeze v13 while regression-testing it unchanged on the two prior known samples:
1. 2026-09-10 Kiryu12, order `1,2,3,4,5,6`.
2. 2026-09-09 Kiryu12, order `1,2,4,5,6,3`.
Do not modify v13 between these regression runs. Inspect actual JSON/logs, not workflow green alone.

If v13 passes both unchanged with sane geometry, preferably add a fourth independent sample from the already captured 2026-09-10 Kiryu6 or Kiryu9 before production wiring. Derive entry order only from pre-race video/contact sheet; do not inspect results.

## Historical blind acquisition source
`.github/workflows/blind-validate-kiryu-20260910-batch.yml`, run `34579347851`:
- race3 artifact `10191092541`
- race6 artifact `10191134655`
- race9 artifact `10191176757`
Results for 9/10 Kiryu 3/6/9 have not been looked up in this SES research thread. Preserve that blindness.

## Production/live wrapper
`run_exhibition_ses_live_local.py` is still old (seed v1 + tracker v3). Do NOT update until unchanged v13 (or later) generalizes sufficiently. Once validated, wire validated seed + tracker v5 stride2 + `exhibition_tracking_v5.json`, then perform a real self-hosted end-to-end live-style run.

## Performance optimization after correctness
v13 seed time ~14 sec is inflated because v13 invokes v12, which invokes v11, then v13 reevaluates persistence/direction. If v13 regression succeeds, refactor into a single-pass production seed implementation while preserving identical logic/outputs, then benchmark. Do not trade away quality gates for speed.

## Validation / live-ready milestone
Before notifying user as complete:
- multiple independent September samples, including varied entry order
- automatic acquisition + automatic seed + tracker only; no manual seed edits or race-specific offsets
- tracker accepted with sane identity/geometry; fail-closed behavior retained
- core post-video pipeline ideally <=30 sec, <=60 sec maximum
- `run_exhibition_ses_live_local.py` updated to validated pipeline
- at least one end-to-end self-hosted live-style validation succeeds
- ideally expand toward 10+ samples before treating SES as stable/predictive
SES remains an attack/head-support feature candidate, not a direct finishing-order rank.

## Immediate next actions
1. Run UNCHANGED v13 on 2026-09-10 Kiryu12 standard order and inspect quality/geometry.
2. Without changing v13, run it on 2026-09-09 Kiryu12 `1,2,4,5,6,3` and inspect quality/geometry.
3. If both pass, validate one additional independent 9/10 Kiryu6/9 sample using entry order derived only from video.
4. Only then consider wrapper integration and one self-hosted end-to-end live-style validation.
5. Update this handoff after every meaningful result/design change.
