# HEAD4 120R Last-Minute Reliability / Latency Audit — 2026-09-18

## User concern
Post-exhibition decisions had historically failed or completed too late to be usable.

This audit rebuilt the 120R final-stage path around:
- once-per-day causal state preparation,
- current exhibition fetch,
- frozen v283 opponent inference,
- parallel odds sources,
- fail-closed deadline guards.

September prior completed dates are allowed in LIVE operational state. Target-race result/payout remains prohibited before decision.

## Final architecture

### Morning / PRE phase
Prepare once:
- current race cards / Waku10,
- PRE candidate list,
- causal player/motor/ST state through target_date-1.

The morning PRE workflow now supports bundling the daily state into its artifact.

### Last-minute phase
Per race:
1. load cached PRE + daily state,
2. fetch current exhibition data,
3. build v283 opponent inputs,
4. infer SECOND / conditional THIRD,
5. compute ticket set and opponent_mass,
6. fetch trifecta odds from official BOAT RACE and BOATCAST in parallel,
7. apply the frozen 120R rule,
8. fail closed if data is not ready or final headroom is too small.

The heavy POST/ENV/A full production chain is intentionally not used by the 120R fast path.

## Safety / reliability guards
- request timeout: 4s exhibition
- odds source timeout: 1.5s each attempt
- exhibition polling safety threshold: 75s before deadline
- odds polling safety threshold: 45s before deadline
- final decision safety threshold: 60s before deadline
- missing/incomplete data -> `NO_BET_DATA_NOT_READY`
- target-race result/payout endpoints are not used
- official odds and BOATCAST odds are independent sources
- first usable complete 120-combo snapshot can be used; official timeout does not block BOATCAST fallback

## Causal daily state
Local sparse historical checkout replaced hundreds of serial raw-GitHub requests.

Measured:
- history end: 2026-09-17
- settled races: 47,520
- players: 1,641
- state generation: about 4.2s
- state generation is a morning task, not per-race work

Daily state now includes:
- player history,
- motor history,
- ST lane bias.

## Actual-deadline benchmark #1 — Gamagori 6R
Official deadline: 17:48 JST.

Run:
- Run `35326011735`
- Job `105539098237`
- Artifact `10538984321`
- digest `sha256:7adcb4b75c29c2ec48cd20a28a2706e0fbd69857f74f6b98b193f99960182c3e`

Measured:
- daily state: 4.18s
- exhibition fetch/build: 0.521s
- v283 input build: 0.00033s
- v283 inference: 0.00168s
- odds fetch: 4.238s
- last-minute runner wall: 5.18s
- decision timestamp: 17:46:22.302 JST
- deadline: 17:48:00 JST
- headroom: ~97.7s

Important reliability event:
- official BOAT RACE odds timed out at 4s,
- BOATCAST odds succeeded,
- `fallback_used=true`,
- odds attempts=1,
- exhibition attempts=1.

The race was outside the internal parent, so semantic output was `BENCHMARK_ONLY`, but the full data/fetch/inference timing path was exercised.

## Prewarmed benchmark #2 — Marugame 7R
The per-race workflow reused:
- the PRE artifact,
- the daily-state artifact,
and skipped historical checkout/state generation.

Run:
- Run `35326922081`
- Job `105542003899`
- Artifact `10539536100`
- digest `sha256:d08db8e50ed642d6686efd7fea8678e0f49616b1a6da84dc33b940dbafff645c`

Official deadline: 18:02 JST.

Measured after odds-timeout tuning:
- exhibition fetch/build: **0.754s**
- v283 input build: **0.00033s**
- v283 inference: **0.00177s**
- odds fetch: **1.882s**
- fast runner wall: **3.43s**
- decision timestamp: **17:56:37.326 JST**
- deadline: **18:02:00 JST**
- headroom: ~322.7s

Workflow creation -> decision was about **21s end-to-end**.

Again:
- official odds timed out at 1.5s,
- BOATCAST succeeded in the same polling attempt,
- `odds_attempts=1`,
- `exhibition_attempts=1`.

## Interpretation

### What is now fast
Model computation itself is effectively negligible:
- v283 input+inference is around 2 milliseconds.

Network fetch dominates:
- exhibition <1s in these tests,
- odds ~1.9s after timeout tuning.

### What previously made it slow
1. rebuilding historical state every race,
2. serial raw-GitHub history fetches,
3. waiting 4s on a slow official odds source despite a usable fallback,
4. running the heavier full downstream chain for a rule that does not need it.

Those have been removed or isolated.

## Operational recommendation
Use:
- morning PRE/state preparation once,
- prewarmed per-race fast runner,
- start the last-minute job as soon as exhibition is expected/available,
- never wait inside the 60s final safety margin.

If neither odds source is complete, or exhibition is incomplete, the system should explicitly return NO_BET rather than attempt a late/stale decision.

## September policy
LIVE operational history may include completed September dates through target_date-1.

Still prohibited before decision:
- target-race result,
- target-race payout,
- future outcomes relative to the decision timestamp.

The historical 120R research ROI remains a separate research metric; updating operational state with September data does not retroactively make that ROI prospective.

## Status
`HEAD4_120R_LASTMINUTE_RELIABILITY_PASS__PREWARMED_3P43S__END_TO_END_ABOUT_21S`

Production promotion is still separate; this report validates speed/fail-safe behavior, not prospective profitability.
