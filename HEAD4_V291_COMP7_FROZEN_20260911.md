# HEAD4_V291 COMP7 FROZEN — 2026-09-11

## Purpose
Freeze the 4-head betting overlay selected after the v289/v290 composite-odds diagnostics, before any September outcome-based evaluation of this policy.

This file supersedes the old v268/v273 **ticket construction** (v96-order / variable-N / target composite 10.5) for the v291 prospective branch only. It does **not** change the frozen S/A head-selection semantics.

July/August 2026 remain NON-PRISTINE and are excluded from tuning/rescue. September outcomes must not be used to change this policy before the prospective checkpoint.

## Frozen head selection

### S layer — unchanged v268
- PRE >= 0.28
- POST >= 0.25
- ENV_ENTRY >= 0.224790

### A layer — unchanged v273 semantics
Only outside S:
- PRE >= 0.18
- POST >= 0.18
- A_SCORE >= 0.28 on the frozen v271/v272 OOF semantics

Priority:
1. Evaluate S first.
2. If S, classify S only.
3. A applies only outside S.
4. Never stake both S and A on the same race.
5. Report S, A, S+A separately.

Important: the final LIVE A_SCORE scale mapping is still required before A can enter formal prospective use. The v291 odds/ticket overlay is frozen independently of that remaining A-score operationalization.

## Frozen independent opponent model
Use the v282/v283 independent opponent branch only.

- SECOND: independent PLAYER_START listwise model, L2=10.
- THIRD: conditional P(third | candidate second, pre-result context), COND_BASE, L2=0.3.
- Pair ordering: v283 TOP2XTOP2 structural policy.
- alpha2 = 0.60.
- Head fixed to boat 4.
- v96 is benchmark/history only. It must not enter features, candidate restriction, ranking, blending, tiebreaking, or fallback.

## Frozen ticket / market rule
For every eligible S/A race, using one immutable pre-deadline trifecta odds snapshot:

1. Generate the frozen v283 4-x-y pair order.
2. Take exactly the first **4 tickets**. No variable N.
3. Read the four contemporaneous trifecta odds from the immutable snapshot.
4. Compute composite odds:

   `COMPOSITE = 1 / sum(1 / odds_i)` over the four tickets.

5. BET only if **COMPOSITE >= 7.000000**.
6. If COMPOSITE < 7.0: PASS, stake 0.
7. If BET: total stake is exactly **10,000 JPY**.
8. Allocate by inverse-odds Dutch weighting in **100-JPY units**, using Hamilton/largest-remainder rounding so the total is exactly 10,000 JPY.
9. Result miss: payout 0 / profit -10,000 JPY.
10. Once the pre-deadline snapshot has produced BET/PASS and stakes, do not revise the decision using later odds or race results.

Boundary rule is inclusive: **7.000000 qualifies**.

## Required snapshot integrity
Formal prospective/OOS evidence requires an immutable pre-deadline record containing at minimum:

- race_code
- layer (S or A)
- snapshot timestamp with timezone
- official race deadline / close timestamp when available
- ordered Top4 tickets
- odds for each Top4 ticket
- computed composite odds
- BET/PASS decision
- exact stake per ticket
- policy version `HEAD4_V291_COMP7`
- source identifier / retrieval metadata sufficient to audit the snapshot

A snapshot obtained or modified after the deadline cannot count as formal prospective evidence.
Archived/closing odds may be retained for comparison but must not replace the frozen live snapshot.

## Development evidence used for candidate choice
Retrospective Apr-Jun proxy, archived odds, v283 Top4 fixed:

- Unfiltered: 100R, ROI 126.12%.
- Composite >= 6.0: 40R, head rate 50.0%, hit rate 25.0%, ROI 233.33%, max DD 77,280 JPY, min-month ROI 110.97%.
- Composite >= 7.0: 28R, head rate 64.3%, hit rate 32.1%, ROI 310.98%, max DD 60,000 JPY, max losing streak 6, min-month ROI 166.46%.
- Composite >= 8.0: 21R, head rate 71.4%, hit rate 38.1%, ROI 380.01%, max DD 70,000 JPY, max losing streak 7, min-month ROI 174.80%.

The 7.0 candidate was chosen as the risk/coverage balance rather than the highest same-sample ROI.

v289 LOMO diagnostic (not formal OOS):
- Hold Apr: floor 6.0 selected on other two months -> hold ROI 339.68%.
- Hold May: floor 6.0 -> 202.45%.
- Hold Jun: floor 7.0 -> 166.46%.
- Combined LOMO ROI 259.26%.

All historical ROI figures above use archived odds and remain development evidence only.

## Prospective lock
From this freeze onward, do not change any of the following because of September outcomes:

- S thresholds
- A selection semantics
- opponent-model family / coefficients chosen by the frozen v282/v283 procedure
- TOP2XTOP2 ordering
- alpha2=0.60
- Top4 ticket count
- composite formula
- composite minimum 7.0
- 10,000-JPY race stake
- 100-JPY Hamilton Dutch allocation
- S/A priority
- PASS behavior

If a future branch tests another threshold/model, it must receive a new version and must not rewrite v291 history.

## Prospective reporting
For every eligible frozen S/A signal after operational readiness, persist both BET and PASS rows. For BET rows report and aggregate:

- eligible signals / BETs / PASSes
- S, A, S+A counts
- 4-head wins / head rate
- trifecta hits / hit rate
- total stake / return / profit / ROI
- actual pre-deadline composite odds
- max drawdown
- longest losing streak
- snapshot age to deadline
- missing/invalid odds incidents

Do not silently drop an eligible race because the result was a miss or because odds later changed.

## Formal OOS start condition
The v291 **betting overlay is frozen now**.

- S-layer formal prospective tracking may begin once the complete live v283 opponent inference and immutable pre-deadline odds capture are operational.
- A-layer formal prospective tracking begins only after the final through-2026-06-30 A_SCORE LIVE model + outcome-blind OOF-semantics mapping is persisted and frozen, and only for races occurring after that operational A freeze.

## Freeze anchor
Repository main observed immediately before creating this freeze:
`dbd3cd2890e4a5d231b5bd82536dd67069f9cfab`

Freeze date: **2026-09-11 JST**.

## Status
**HEAD4_V291_COMP7 is FROZEN as the prospective 4-head market/ticket policy.**
It is not a claim of prospective profitability. Formal OOS performance starts only from immutable pre-deadline operation after the relevant live components are ready.
