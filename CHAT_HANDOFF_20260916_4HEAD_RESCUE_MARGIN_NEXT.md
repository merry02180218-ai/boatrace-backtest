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
- Artifact upload step succeeded structurally but no files existed because failure occurred before output creation.

## AFTER — FAILURE 2 FIX
- `audit_4head_86r_v283_closing_odds.py` now accepts explicit `start,end` in `source_rows`, defaults remain Apr-Aug for legacy audit, and September odds access is explicitly blocked. commit `eeeb77f6fa8005940b0c9f7f1314a23c0b0866af`.
- `analyze_4head_v283_second_margin_rescue.py` now passes the requested window into `source_rows` and asserts exact source/replay coverage and 5 opponent rows per race. commit `2be97348806833f5d506d165dcb26aa91db9011b`.
- September outcome/results remains `UNREAD`.

## FAILURE 3 — Run 35126729027
- Run `35126729027`, Job `104897492664`.
- six-month candidate/v283 reconstruction succeeded: `HEAD4_FROZEN_INDEPENDENT_REPLAY_OK 2026-03-01 2026-08-31 191`.
- failure was post-computation guard `MONTH_SUMMARY_INCOMPLETE`.
- root cause: `str.match(r'2026-\\d\\d')` also matched aggregate label `2026-03..08`, adding an unwanted seventh period to the integrity set.

## AFTER — FAILURE 3 FIX
- `backtest_4head_v291_third010_sixmonth.py` fixed at commit `81261c5bf703fd9c4dd866dfd46c2ed56bce33dc`.
- monthly integrity now selects periods by exact `REQUIRED` membership, so aggregate `2026-03..08` cannot contaminate the six-month check.
- `race_detail.csv` and `summary.csv` are now persisted before the final integrity guard so a future late-stage failure still leaves diagnostics for Artifact upload.
- candidate/model/ticket/market semantics were not changed.
- September 2026 outcomes/results remains `UNREAD`.
- Fresh workflow_dispatch on current main is required; do not accept reruns of older head SHAs as validation.

Status: `THIRD010_SIX_MONTH_FAILURE3_FIXED_NEEDS_FRESH_DISPATCH`
