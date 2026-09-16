# CHAT HANDOFF — 2026-09-16 — 4HEAD RESCUE + CLOSE-MARGIN NEXT

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール
- production ticket policy `HEAD4_V291_COMP7_THIRD010`; PRE>=.28 / POST>=.25 / ENV_ENTRY>=.224790; frozen v283; THIRD gap<=.10; comp>=7; JPY10,000 Dutch; v96 prohibited; fail closed.
- September 2026 outcome/results are never read: `UNREAD`.
- closing odds are retrospective diagnostic only; formal prospective ROI=`NOT_COMPUTABLE`。

## 確定監査要約
- fixed candidate Apr-Jun 86R/35 head4; Jul-Aug 78R/35; Apr-Aug 164R/70.
- THIRD0.10 old flat-100yen retrospective: Apr-Aug 817 tickets / 35 hits / ROI 135.13%.

## Production implementation
- runner `run_4head_v291_third010_live.py` commit `376c636839af499821244ca660e382a43a16d644`
- verifier `verify_4head_v291_third010_live.py` commit `760800671596c87334877217e1683223aa7a7879`

## SIX-MONTH SUCCESS
- Run `35129089769`, Job `104905317906`, head `2ec7575bb0b508f1ce848edd12aeaee1b4fcfabe`, Artifact `10461260375` SUCCESS.
- Mar-Aug 191 candidates / 953 tickets / 55 BET / 136 PASS / 7 BET hits / ROI 146.8327% closing-odds diagnostic.
- artifact `hit` is BET-only, so it is not comparable directly to historical raw ticket hits.

## RECONCILIATION FINDING
- Mar-Aug = 191R / 953 tickets.
- March = 27R / 136 tickets, therefore Apr-Aug = 164R / 817 tickets exactly.
- This exactly matches historical THIRD0.10 ticket count, so candidate population and ticket expansion count are not the source of the apparent discrepancy.

## BEFORE — RAW HIT RECONCILIATION EXECUTION
- Added `audit_4head_third010_raw_hit_reconcile.py` commit `cceab3bcc94a1a3a3fbc2f8725e5ef1b03aaa53e`.
- Added workflow `.github/workflows/audit-4head-third010-raw-hit-reconcile.yml` commit `1b116cb687a58ad0002014c26d7dc454c1b5d3b5`.
- Audit computes raw THIRD0.10 ticket containment independently of BET, then BET hit and PASS-discarded correct hit by month.
- Hard guard requires Apr-Aug exactly 164R / 817 tickets / 35 raw hits. Any mismatch fails closed.
- September remains `UNREAD`.
- Next action: fresh manual dispatch of `audit-4head-third010-raw-hit-reconcile`, then inspect exact discarded-hit races and comp odds.

Status: `RAW_HIT_RECONCILE_READY_FOR_FRESH_DISPATCH`
