# CHAT HANDOFF — 2026-09-16 — 4HEAD RESCUE + CLOSE-MARGIN NEXT

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール
- production ticket policy `HEAD4_V291_COMP7_THIRD010`; PRE>=.28 / POST>=.25 / ENV_ENTRY>=.224790; frozen v283; THIRD gap<=.10; comp>=7; JPY10,000 Dutch; v96 prohibited; fail closed.
- September 2026 outcome/results are never read: `UNREAD`.
- closing odds are retrospective diagnostic only; formal prospective ROI=`NOT_COMPUTABLE`.
- work BEFORE/AFTER and exact Run/Job/Artifact/commit IDs must be recorded.

## 確定監査要約
- fixed candidate Apr-Jun 86R/35 head4; Jul-Aug 78R/35; Apr-Aug 164R/70.
- THIRD0.10 retrospective old 100-yen-per-ticket diagnostic: Apr-Aug 817 tickets / 35 hits / ROI 135.13%; monthly Apr 211.89, May 120.36, Jun 138.48, Jul 141.72, Aug 75.96%.
- THIRD close-margin Run `35074469211` Job `104723453680` Artifact `10437831280`.
- strict comparison Run `35089336519` Job `104771656556` Artifact `10443723290`.
- fixed gap Run `35119432005` Job `104873127479` Artifact `10456963422`.

## THIRD0.10 production semantics
SECOND top2; per SECOND branch conditional THIRD rank2-rank3 gap<=.10 adds rank3; frozen v283 base Top4 preserved; 4-6 unique tickets.

## Production implementation
- runner `run_4head_v291_third010_live.py` commit `376c636839af499821244ca660e382a43a16d644`
- verifier `verify_4head_v291_third010_live.py` commit `760800671596c87334877217e1683223aa7a7879`
- workflow `.github/workflows/validate-4head-v291-third010-live.yml` commit `695dab0796fc79fa6c27e1bff7f0d1ac33099287`

## BEFORE — 2026-09-17 SIX-MONTH FAILURE RECOVERY
Run `35121865532` / Job `104881369251` failed closed because source reconstruction supplied Apr-Aug only. User requested fixing this and any other concerns, then continuing. September remains UNREAD.

## AFTER — 2026-09-17 SIX-MONTH RECOVERY FIXES READY
Root cause fixed without weakening the six-month guard.
- `analyze_4head_b4_minus_b3_motor_full_universe.py`: `settle_all(months=...)` explicit window + September block. commit `d68409f1bb5e55e489122aaf03029d047327d562`.
- `analyze_4head_headrate_3ren_player_st.py`: prior-only feature rows now record from 2026-03-01 while history remains causal from 2025-10-01; Apr-Aug semantics unchanged. commit `09746760545a39eb101985768ef9f858b437a94a`.
- `analyze_4head_exhibition_original_trainonly.py`: exhibition reconstruction records wanted March rows using same prior ST-bias history; September blocked. commit `7642e0bde4a43279819af00f4f84b4463f93690c`.
- `audit_4head_86r_independent.py`: `rebuild(start,end)` supports Mar-Aug; legacy Apr-Aug call retains exact 86/35 + 78/35 assertions. commit `08246d0f98fd947c7a1eacaaa4731d82bf3008fc`.
- `analyze_4head_v283_second_margin_rescue.py`: `build(start,end)` passes explicit frozen replay window and blocks September. commit `16fd1d50c9d83a954481500244aaa3020c8aed92`.
- `backtest_4head_v291_third010_sixmonth.py`: commit `240dacae08f2aa7c6bc625bfdc57f9ab0eea0fd3`.

Additional concern found and fixed: the first six-month script was NOT replaying the actual production market policy; it staked a flat 100 yen per candidate ticket and omitted comp>=7. The repaired script now verifies tickets exactly against `run_4head_v291_third010_live.production_tickets`, computes variable-N composite odds, applies comp>=7 inclusive, and for BET races uses the exact production JPY10,000 Dutch allocator. It reports candidate_R/covered_R/bet_R/pass_R/hits/stake/payout/profit/ROI. Closing odds remain explicitly retrospective diagnostic only; formal prospective ROI remains NOT_COMPUTABLE.

Other guards now present: exact six months Mar-Aug required; production policy/THIRD gap/comp cut/bank drift guard; exact ticket-semantics equality guard; all selected odds must be present/positive; Dutch total must equal JPY10,000; v96=false metadata; September end-date block; complete month-summary assertion. Workflow already uploads artifact with `if: always()`.

Fresh validation/backtest run is still required. Do NOT claim success until a new run on commit `240daca...` or later is observed. Direct workflow dispatch is not exposed by the connector, so next action is one manual `workflow_dispatch` of `.github/workflows/backtest-4head-v291-third010-sixmonth.yml`, then inspect Run/Job/Artifact and append final AFTER results.

Status: `THIRD010_SIX_MONTH_FIXED_AWAITING_FRESH_DISPATCH`
