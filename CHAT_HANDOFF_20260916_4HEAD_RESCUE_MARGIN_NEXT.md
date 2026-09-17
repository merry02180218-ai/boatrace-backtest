# CHAT HANDOFF — 2026-09-16 — 4HEAD RESCUE + CLOSE-MARGIN NEXT

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール
- production ticket policy `HEAD4_V291_COMP7_THIRD010`; PRE>=.28 / POST>=.25 / ENV_ENTRY>=.224790; frozen v283; THIRD gap<=.10; comp>=7; JPY10,000 Dutch; v96 prohibited; fail closed.
- September 2026 outcome/results are never read: `UNREAD`.
- closing odds are retrospective diagnostic only; formal prospective ROI=`NOT_COMPUTABLE`。

## 確定監査要約
- fixed candidate Apr-Jun 86R/35 head4; Jul-Aug 78R/35; Apr-Aug 164R/70.
- THIRD0.10 old flat-100yen retrospective: Apr-Aug 817 tickets / 35 hits / ROI 135.13%.

## SIX-MONTH SUCCESS
- Run `35129089769`, Job `104905317906`, Artifact `10461260375` SUCCESS.
- Mar-Aug 191 candidates / 953 tickets / 55 BET / 136 PASS / 7 BET hits / ROI 146.8327% closing-odds diagnostic.

## RAW HIT RECONCILIATION — SUCCESS
- Run `35131504476`, Job `104913379223`, Artifact `10461493300` SUCCESS.
- Apr-Aug THIRD0.10 exactly reproduces 164R / 817 tickets / 35 raw hits.
- comp>=7 retains only 5 of those 35 raw hits; 30 correct raw hits are PASS-discarded.
- monthly raw -> BET hits: Apr 8->4, May 7->0, Jun 4->1, Jul 11->0, Aug 5->0.
- Therefore ticket generation is intact; the discrepancy is caused by the comp>=7 market filter.

## COMP THRESHOLD SWEEP — SUCCESS
- Run `35135508327`, Job `104926754630`, Artifact `10463204774` SUCCESS.
- frozen v283 + THIRD0.10 fixed; only composite-odds cutoff varied.
- Apr-Jun ROI: no-filter 149.0%, 6.00 246.9%, 6.25 266.5%, 6.50 293.4%, 6.75 262.5%, 7.00 255.4%.
- Jul-Aug holdout ROI: no-filter 86.4% (16/78 hits), 6.00 23.0% (1/27), 6.25 23.0% (1/27), 6.50/6.75/7.00 0%.
- Simple lowering of comp cutoff does not robustly increase profitable BET races; comp filter strongly discards Jul-Aug winners.
- Production comp>=7 remains unchanged.

## BEFORE — RENEWED HEAD-PROBABILITY RESEARCH
- User explicitly requested another study of 4号艇 head probability.
- Objective: revisit head-probability selection as a way to increase BET races without changing frozen v283 + THIRD0.10 opponent/ticket semantics yet.
- First reproduce the exact current fixed candidate population and identify the actual head-probability score/fields used by the current model; do not substitute a guessed probability definition.
- Re-sweep head-probability thresholds and report candidate R, head4 R/rate, raw THIRD0.10 ticket hits, and closing-odds retrospective ROI where applicable.
- Primary split remains Apr-Jun development vs Jul-Aug independent holdout; Apr-Aug overall is secondary.
- Compare against the previously observed head-probability research, but require exact reproduction before using old thresholds as conclusions.
- Keep production unchanged during research. v96 prohibited. September remains `UNREAD`.

Status: `HEAD_PROBABILITY_RESEARCH_PREPARING`
