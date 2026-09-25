# CHAT_HANDOFF — 1HEAD current-day acquisition + LIVE bridge
Updated: 2026-09-25 JST
Repo: merry02180218-ai/boatrace-backtest
Branch: main

## User intent
Bring 1HEAD LIVE operation to the same operational interface as the accepted 4HEAD LIVE flow, while preserving 1HEAD-specific formal model logic.

Current user instruction:
- first validate manually; do NOT restore an automatic schedule yet;
- one daily run should acquire today's race cards, build causal D-1 state/cache, audit leakage, and emit broad WATCH targets;
- final race processing should acquire exhibition, make the formal final head decision, generate tickets/allocation, fetch official pre-deadline odds, and notify only on BET;
- settled prior September dates are allowed in LIVE causal state; target-day result/payout is forbidden before decision.

## 2026-09-25 current-day audit
Original implementation commit:
- 20dfc868e520ad9c83c2bed5049ad1c95888f50d
- live: add unified 1HEAD day acquisition and causal audit

Manual Run:
- Run 36124801250
- Job 108038330608
- Artifact 10859279916
- Artifact name: 1head-current-day-audit-20260925

Core audit result:
- today's cards: 144R
- causal all-race cache: 144R
- WATCH: 11R
- history_end: 2026-09-24
- target-day results used: false
- payouts used: false
- chronology guard: true

The workflow's overall conclusion was FAILURE only because its final static grep matched the grep command itself. All acquisition/cache/leakage-audit steps and artifact upload were SUCCESS.

Fix:
- commit 9fc47376b06eb9c8eb452ae1985dc32e3cab391c
- replaces the self-matching grep preflight and adds explicit PH / relaxed-expansion production assertions.
- new watchlist schema marks PRE band:
  - FORMAL_LIVE
  - PLAYER_HISTORY_BAND
  - HEAD_VOLUME_BAND

2026-09-25 WATCH distribution from the valid audit artifact:
- FORMAL_LIVE (HEAD >= .790): 4R
- PLAYER_HISTORY_BAND (.780 <= HEAD < .790): 2R
- HEAD_VOLUME_BAND (.750 <= HEAD < .780): 5R

For the two PH-band races, causal D-1 registration-number PLAYER_HISTORY gave:
- 202609252112: b1 recent_p2 = .566667 -> PH threshold .533333... passes
- 202609252212: b1 recent_p2 = .433333 -> PH threshold fails

## Formal head lanes preserved in LIVE
Do not collapse these into one threshold.

1. FORMAL_LIVE
- HEAD >= .790
- opponent mass >= .375
- standard v332 exhibition gate: env_w=.05 / q=.70

2. PLAYER_HISTORY_EXPANSION
- formally adopted 2026-09-24
- .780 <= HEAD < .790
- opponent mass >= .375
- b1_pl_recent_p2 >= .533333333333
- standard v332 exhibition gate .05/.70
- production profile constants in onehead_production_profile.py

3. HEAD_VOLUME_EXPANSION
- formally adopted 2026-09-25
- .750 <= HEAD < .780
- opponent mass >= .375
- relaxed v332 exhibition gate env_w=.10 / q=.65
- final env_pair <= -.34
- env_pair exact formula:
  .30*sec_ex_mean_margin + .30*sec_st_mean_margin
  + .20*third_turn_mean_margin + .20*third_straight_mean_margin

Pickup / opponent-pickup flags remain tags inside the relaxed expansion; they do not replace the formal HYBRID ticket policy.

## New LIVE final-decision bridge
Commit:
- 63850a5e99f6b95501da39ee0b9973dd829cbcf8
File:
- run_1head_current_day_live_decision.py

Purpose:
- consume the audited daily artifact + current exhibition;
- rebuild exact standard and relaxed exhibition gates;
- compute causal b1 recent_p2 from the D-1 daily state, registration-number keyed;
- select exactly one of FORMAL_LIVE / PLAYER_HISTORY_EXPANSION / HEAD_VOLUME_EXPANSION / DROP;
- reuse run_1head_v351_live_finalize.py as the single existing opponent/ticket-policy implementation;
- for an already-promoted expansion lane, bridge its head gate into the old .790-only finalizer solely so the existing opponent/HYBRID logic runs, then restore the actual HEAD probability in the emitted decision.

Error observability hardening:
- a6696600eb35c496965518461d3ac27edee62abd
- existing-finalizer stdout/stderr are exposed if bridge execution fails.

Strict pre-deadline market hardening:
- 23ddf2fb822eb2aec8df00d1da67aab4efe3968f
- fail closed if deadline has already expired before odds fetch;
- official odds fetched_at_jst is checked again after fetch;
- odds timestamp >= deadline is rejected and cannot become BET.

## BET notification
Commit:
- 7868e879a71bba0525082a57fcdfaea22afc10f2
File:
- notify_head1_bet_github_issue.py

Behavior:
- notify only when decision == BET;
- GitHub Issue dedupe by exact race title;
- includes lane, HEAD, opponent mass, b1 recent_p2, env_pair, tickets, odds, allocation and estimated payout;
- target result/payout must remain unused.

## Manual current-day monitor
Commit:
- 2aed8e96ff5bf55da5a810c115cbce5fd614dd01
Workflow:
- .github/workflows/live-1head-current-day-monitor.yml

Important:
- workflow_dispatch only;
- NO schedule enabled;
- consumes 1head-current-day-audit-YYYYMMDD artifact directly;
- validates target membership and causal state;
- acquires deadline and exhibition;
- final states:
  - BET
  - PASS
  - NO_BET_DATA_NOT_READY
- BET/PASS use canonical artifact name;
- NOT_READY uses retry/diagnostic artifact name;
- only BET invokes notification;
- allocation is 5,000 yen total, 100-yen units, inverse-odds Dutch over the formal selected tickets.

Self-matching safety guard fix:
- 36b1f2995e043f7cbc7990d09d2171076a506742

## Contract tests
Workflow:
- .github/workflows/test-1head-current-day-live-contract.yml

Relevant commits:
- cd899c6b4dc990fb5dabc0edcef3203cdf6eb78f initial contract
- 3fba8aebf6b9a6af22e26d89906c0282080fd7e3 self-match fix
- 03edfbd97d1980f4b0121ed88410414f2af0a579 bridge + notification coverage
- e6d78d8e070f6d2a76a4d656c707f35d5d3b636 exact production profile in bridge test
- c505de731db4a397bd5f1128c37fb48930ce3e4d strict pre-deadline odds guard test

Green runs:
- 36126850704 SUCCESS
- 36126854374 SUCCESS
- 36127199380 SUCCESS
- 36127350628 SUCCESS
- 36127372755 SUCCESS (latest strengthened contract)

Latest strengthened Run 36127372755 verifies:
- Python syntax
- monitor/audit workflow YAML
- all three promoted head lanes
- 5,000 yen Dutch allocation
- expired deadline rejected
- post-deadline odds timestamp rejected
- existing v351 finalizer bridge
- BET notification dry-run
- no target result/payout source in final LIVE decision path

## Current exact status / next step
Production wiring and contract tests are GREEN.
The 9/25 daily artifact is valid despite the old workflow's false-positive final preflight failure.
Automatic 1HEAD scheduling remains intentionally disabled.

Next step is a manual real pre-race invocation of:
- live-1head-current-day-monitor
for a WATCH target with exhibition/odds still available before its official deadline.

Do not claim full real-market LIVE validation until such a workflow_dispatch run reaches one of:
- BET with official pre-deadline odds and 5,000-yen allocation;
- PASS after valid exhibition;
- NO_BET_DATA_NOT_READY fail-closed.

After one real active-race validation, only then consider wiring an automatic watchdog/schedule, and only if the user explicitly asks to restore automation.
