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

## BEFORE — COMP THRESHOLD SWEEP
- Next audit will sweep composite-odds cutoffs without changing candidate or THIRD0.10 ticket semantics.
- Primary cutoffs: 6.0 / 6.25 / 6.5 / 6.75 / 7.0, plus no-filter diagnostic baseline.
- Report BET R, hits, stake, payout, ROI, retained raw hits and discarded raw hits.
- Split Apr-Jun development vs Jul-Aug independent holdout, plus monthly detail and Apr-Aug total.
- JPY10,000 Dutch / 100-yen units; official closing odds are retrospective diagnostic only.
- Production comp>=7 is NOT changed by this audit. Any adoption requires holdout evidence after the sweep.
- September remains `UNREAD`.

Status: `COMP_THRESHOLD_SWEEP_PREPARING`
