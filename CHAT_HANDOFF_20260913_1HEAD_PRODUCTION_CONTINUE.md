# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## READ THIS FIRST — authoritative current 1-head state
Latest GitHub wins over old chat memory/stale handoff text.
Mandatory pattern: **handoff update -> work -> result append -> next work handoff update**.
Before every work unit/code change/restart record current position, exact work, success criteria, failure fallback. After every work unit record actual work, commit SHA(s), Actions Run ID/status, metrics/results, exact next resume point.

# 1. Frozen production stack — DO NOT ALTER
- HEAD v308
- SECOND v317 `OUTER_L2_1`
- THIRD v318 `DROPSTART_T0.1`
- 3-ticket policy v320 `HYBRID alpha=.70`
- exactly 3 trifecta tickets per selected race
- frozen regression **345 selected / 290 boat1 wins / 139 exact3**
- v308 q=.980, opponent mass>=.375, head cutoff=0.8073405637
- v308 is true PRE; same-race exhibition is post-PRE only.
- composite odds = `1/(1/o1+1/o2+1/o3)`.

Guardrails:
- Jul/Aug 2026 = NON-PRISTINE/reference-only; never tune/promote on them.
- September outcomes = UNREAD.
- no same/later-race result, payout, future/backfill contamination.
- month M trains strictly on `<M`.
- missing current exhibition inputs fail closed for any feature/route requiring them.
- no `meet_*` unless separately audited.
- neutral 0.5 defaults are not proof raw metric existed.
- do not modify v308/v317/v318/v320/v323.

# 2. Frozen research through v324
- v309 exact3 132/345; v310 133/345; v311 136/345; v312 136/345.
- v314 role split unstable; v315 133/345; v316 136/345; v317 137/345; v318 137/345; v319 134/345.
- v320 `HYBRID alpha=.70`: **139/345=40.29%**.
- v321 Jul/Aug NON-PRISTINE: Run 34750719803; 55R/head45/exact3 21.
- v322 composite odds Run 34753932483; ROI91.27%; no cutoff promoted.
- v323 production adapter Run 34757079269; frozen 345/290/139.
- v324 corrected Jul/Aug odds audit Run 34762939723; 55R/21 exact3, ROI85.66%; odds-only cutoff unsupported.

# 3. Exhibition source audit
Historical result-blind sources:
- `data/previews/tkz/YYYY/MM/DD.csv`
- `data/previews/stt/YYYY/MM/DD.csv`
- `data/previews/original_exhibition/YYYY/MM/DD.csv`
- transform `backtest_v51_lane_corrected_tickets.py::corrected_direct`
- ST lane bias learned only from prior dates.
- readiness uses raw completeness, never neutral 0.5 as proof.

# 4. v325-v328
- v325 Run 34764329333: June PASS 8/25=32.00%, unsupported.
- v326 Run 34766426083: June PASS 8/25=32.00%, unsupported.
- v327 Run 34766775614: June PASS 13/39=33.33%, unsupported.
- v328 Run 34767480326: ticket-error audit; broad June deterioration; no single miss class dominated.

# 5. v329 multistage exhibition judgement — COMPLETE / REPORTED
Architecture transferred from 3-head/4-head: frozen PRE -> multiple current-exhibition dimensions -> POST core + opponent/environment stage -> S/A/B routes -> fail-closed readiness.
Implementation `c21b058773138c7a9148e4b3a05b68474a741621`; workflow `b69b2ac9b078604ee6eb056e8afd44900efd70d3`; retrigger `71a46a174563d97b98630042bbb74eeec5dc2976`.
Run **34771215699** SUCCESS, Job **103761044413**, Artifact **10322321569**.
Frozen config attack_q=.55, turn_q=.55, env_q=.60, bcore_q=.90, benv_q=.40.
Thresholds attack=.6453333333, turn=.5980000000, env=-.2966666667, bcore=.8973333333, benv=-.3766666667.
Feb-Apr PASS 25R/12 exact3=48.00%, head22/25=88.00%.
May PASS 24R/10=41.67%, head21/24=87.50%.
June baseline 92R/32=34.78%, head75/92=81.52%.
June PASS **17R/8=47.06%, head16/17=94.12%**; SKIP75R/24=32.00%.
June S14R/8=57.14%, A3R/0, B0R. Criterion said PROMOTE=True, but selectivity was flagged.

# 6. v330 extended v329 robustness/volume — COMPLETE / REPORTED
Pre-work `c8a9b5d961e66ce0902789857a55d4cec6b72736`; implementation `7c63e199f2e8fc02e87f38b2d0150dcd42176759`; workflow `e9df21bc1d714a0c2bea24de5aa7e285eaa510c5`.
Run **34772689488** SUCCESS, Job **103765047806**, Artifact **10322487241**, SHA256 `d7506a5984ff6f5e096766f66f97240c918c4c9df72d8a9c2abbf6270b2fcfac`.
Jul/Aug base **55R/head45/exact3 21**. Fixed-v329 Feb-Jun PASS **66R/head59/exact3 30**.
July PASS4/13, exact3 1/4=25%, head3/4=75%; August PASS6/42, exact3 1/6=16.67%, head2/6=33.33%.
Jul+Aug PASS **10/55=18.18%**, exact3 **2/10=20%**, head **5/10=50%**; SKIP exact3 19/45=42.22%, head40/45=88.89%.
Feb-Jun PASS fraction 19.13%; Jul-Aug 18.18%: selectivity structurally stable around 18-19%, but direction is not robust in NON-PRISTINE stress reference.
Conclusion: do not deploy v329 as production-ready and do not blindly relax thresholds.
Result handoff commit `6537cbc7f8be77d7ee53bd9e65d0635d8a70012c`.

# 7. Work Unit 7A — v331 component/route stability diagnostic — ABOUT TO IMPLEMENT
Current position: v330 showed that fixed v329 preserves roughly the same PASS fraction but the PASS/SKIP performance direction reverses in Jul/Aug reference. Need diagnose whether this comes from head-core metrics, environment/opponent metric, route composition, or threshold distribution shift before any redesign.

Exact work:
1. Reuse v329 Feb-Jun dataset and v330 Jul/Aug reconstructed feature dataset; no new outcome source and no September outcomes.
2. Keep v329 formulas/thresholds frozen. Do NOT tune Jul/Aug.
3. For each period (Feb-Apr, May, June, July, August, Jul+Aug), measure baseline and feature strata for `attack_core`, `turn_core`, `env_pair`, `best_core` using the already-frozen v329 thresholds.
4. Measure each boolean gate separately: attack>=threshold, turn>=threshold, env>=threshold, bcore>=threshold, benv>=threshold, and intersections. Report R/head/exact3 and lift vs period baseline.
5. Measure S/A/B route performance and route composition, including head-loss concentration.
6. Compare feature distributions by period (count/mean/median/q25/q75 and threshold pass fraction) to identify covariate/distribution shift separately from outcome association.
7. Produce a diagnostic conclusion only. v331 must NOT promote a model or change production.

Success criteria:
- frozen Feb-Jun identity remains 345/head290/exact3 139;
- Jul/Aug identity remains 55/head45/exact3 21;
- no threshold is learned from Jul/Aug;
- output clearly identifies which components remain directionally useful in June and which fail/reverse in Jul/Aug reference;
- enough evidence to predeclare one v332 redesign without blind threshold search.

Failure fallback:
- if v330 feature artifact is unavailable in-repo, deterministically rebuild Jul/Aug features with the exact v330 causal procedure;
- if any identity/readiness reconciliation drifts, fail closed and record the mismatch before correction;
- never inspect September outcomes.

Exact next resume point:
- implement `run_v331_1head_component_stability.py` and workflow, run Actions, record result in this handoff, then report v331 once before starting v332.