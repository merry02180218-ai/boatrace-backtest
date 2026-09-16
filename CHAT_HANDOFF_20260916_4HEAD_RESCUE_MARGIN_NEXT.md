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

## SIX-MONTH RECOVERY HISTORY
First run `35121865532` / Job `104881369251` failed because candidate reconstruction supplied Apr-Aug only.
Recovery commits extended causal reconstruction to March and repaired the backtest to replay actual production market semantics (comp>=7 + JPY10,000 Dutch), not flat 100 yen/ticket.

## FAILURE 2 — Run 35125191625
- Run `35125191625`, Job `104892400132`, head SHA `74e9d0a8d6785a9f3dbefebd9a93bcb2f1c28e41`.
- candidate reconstruction itself succeeded: `HEAD4_FROZEN_INDEPENDENT_REPLAY_OK 2026-03-01 2026-08-31 191`.
- failure occurred later because `audit_4head_86r_v283_closing_odds.source_rows()` still hard-filtered its V93 feature source to Apr-Aug. Thus v283 replay discarded March and the final six-month guard correctly stopped with available Apr-Aug only.

## AFTER — FAILURE 2 FIX
- `audit_4head_86r_v283_closing_odds.py` explicit start/end commit `eeeb77f6fa8005940b0c9f7f1314a23c0b0866af`.
- `analyze_4head_v283_second_margin_rescue.py` passes requested window and asserts replay coverage commit `2be97348806833f5d506d165dcb26aa91db9011b`.

## FAILURE 3 / FIX
- Run `35126729027`, Job `104897492664`: reconstruction 191R succeeded; late guard `MONTH_SUMMARY_INCOMPLETE` failed because aggregate label matched loose month regex.
- fixed `backtest_4head_v291_third010_sixmonth.py` commit `81261c5bf703fd9c4dd866dfd46c2ed56bce33dc` with exact REQUIRED membership and pre-guard CSV persistence.

## SUCCESS RUN
- fresh Run `35129089769`, Job `104905317906`, head `2ec7575bb0b508f1ce848edd12aeaee1b4fcfabe`, Artifact `10461260375` SUCCESS.
- artifact summary: Mar-Aug 191 candidates / all 191 closing-odds covered / 55 BET / 136 PASS / 953 candidate tickets / 7 BET hits / JPY550,000 stake / JPY807,580 payout / ROI 146.8327%.
- monthly BET-hit summary: Mar 10BET/2hit, Apr 7/4, May 8/0, Jun 7/1, Jul 16/0, Aug 7/0.
- IMPORTANT: artifact `hit` is defined only after `bet=True`; PASS races are forced hit=0. Therefore this 7 cannot be compared directly to the old Apr-Aug THIRD0.10 35 ticket hits.

## BEFORE — 191R TICKET-HIT RECONCILIATION
- Reconcile every Mar-Aug candidate independently of comp>=7: head4, THIRD0.10 ticket containment, BET/PASS, and closing-odds market filter.
- Apr-Aug must be compared on the same population/definition with the historical 817 tickets / 35 hits; identify whether discrepancy comes from ticket generation, candidate reconstruction, or comp>=7 filtering.
- Quantify how many correct ticket hits are discarded by PASS, by month, especially May/Jul/Aug.
- Do not read September outcomes. Keep `UNREAD`.

Status: `AUDITING_191R_RAW_TICKET_HITS_VS_MARKET_FILTER`
