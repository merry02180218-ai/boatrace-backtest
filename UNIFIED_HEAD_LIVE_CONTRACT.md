# Unified HEAD LIVE contract

Purpose: one operational pipeline for current and future head models without merging model logic.

## Stable target schema
Required per target:
- model: stable dispatcher key, e.g. 1HEAD, 4HEAD, future 3HEAD/5HEAD
- jcd, race, race_code, deadline_jst
- watch_minutes_before
- adapter: model-specific runtime adapter key
- pre_class: model-owned PRE classification

Optional opaque model payload:
- model_payload: arbitrary model-specific PRE values/reasons
- source: artifact/run identifiers needed by the adapter
- artifact_name: explicit idempotency artifact name

## Separation rule
The unified layer owns only race acquisition orchestration, deadline ordering, watchdog scheduling,
parallelism, idempotency, common chronology/result-blind guards, odds/BET envelope and notification routing.
Each adapter owns model features, thresholds, PRE eligibility, exhibition gate, final head decision and
model-specific ticket logic.

Adding a future model should require:
1. a PRE producer emitting this target contract;
2. one adapter implementing final decision;
3. registration of its model key/adapter.
It must not require rewriting the watchdog resolver.

Current migration: 1HEAD + 4HEAD first. Existing production workflows remain intact until parity validation passes.
