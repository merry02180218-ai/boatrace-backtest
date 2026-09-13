# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **CANONICAL WAKU10 HEAD4 PRISTINE RE-EVALUATION STARTED**

## Frozen production
Production remains unchanged (`HEAD4_V291_COMP7`). July/August 2026 remain NON-PRISTINE; September remains outcome-blind for tuning/model selection.

## Permanent canonical Waku10 fix — COMPLETE
- Canonical materialization workflow: `.github/workflows/materialize-canonical-waku10.yml`.
- Retry Run `34778943467`, Job `103782266148`: SUCCESS.
- Canonical data commit: `fbf863c8d2b91d1232c60cdd55374b4e0d33dd8d`.
- Coverage: 100% every month 2025-12 through 2026-08.
- Artifact ID `10324971412`, SHA256 `5fc79e7d91424024176b3066cf2f81f0506e9dfe03bcdc5a72a8501f7146e530`.
- Shared rows loader prefers repository-local canonical `data/programs/waku10/...`.

## Canonical 7/18->7/19 re-audit — COMPLETE
- Run `34780264422`, Job `103785870696`: SUCCESS.
- Artifact `head4-jul18-19-primitives`, ID `10325316297`, SHA256 `bc43dae403b4838bd349528811e22cd478047b9db0d81036f9838ca1e4f23659`.
- Rich Waku10 schema is populated on both days; schema additions/removals = 0/0.
- Corrected 7/18 -> 7/19 changes: legacy_score4 36.381158 -> 36.283451 (-0.097707), resistance12 .720583 -> .699611 (-.020972), wall3_weak .208704 -> .195410 (-.013294), past_win4 .098148 -> .093866 (-.004282).
- Therefore the old huge 7/19 discontinuity was caused by sparse public Waku10 lineage and is INVALID for model/regime decisions.

## Canonical Feb-Aug reruns — COMPLETE
- Common frozen Jan-31 model: Run `34781257580`, Job `103788567081`: SUCCESS.
  - Artifact ID `10325587160`, SHA256 `3032d71a7bf7c7f08abc417c94478215e6192cb7fc8994ca2d334d627b154b32`.
  - PRE .03-.05: Feb 609/20=3.28%, Mar 740/24=3.24%, Apr 743/12=1.62%, May 817/24=2.94%, Jun 716/29=4.05%, Jul 872/27=3.10% NON-PRISTINE, Aug 843/29=3.44% NON-PRISTINE.
- Rolling fit cutoff rerun: Run `34781279884`, Job `103788629685`: SUCCESS.
- Regime drift rerun: Run `34781297306`, Job `103788675802`: SUCCESS.
- Production unchanged.

## Fixed August / training-only Waku10 audit — COMPLETE
- Run `34782285223`, Job `103791354620`: SUCCESS.
- Artifact `head4-fixed-aug-training-waku10`, ID `10325805350`, SHA256 `415b21de088d96f7d0c3cb209a13eab6d75e9beb5394e7df0393031121e328b1`.
- August target matrix hash fixed and reused exactly: `29019abd13ed3673901aeb21cf9f1138dafd713bf416a6264f327bc8e85bbc59`.
- Canonical-training model: PRE mean .10042, median .08335, PRE .03-.05 = 843R / 29 wins = 3.44%.
- Public-only-training model: PRE mean .01297, median .00587, PRE .03-.05 = 233R / 54 wins = 23.18%.
- PRE .03-.05 overlap = 0R; mean absolute PRE shift = .08746; max shift = .40360.
- Public-only historical Waku10 coverage currently observed for Dec-Jan = 0/62 days, 0 rows.
- Conclusion: August raw target data is not the cause of the old anomaly; missing training-period Waku10 changed the learned score scale/coefficients.

## CURRENT WORK-START RECORD — written BEFORE implementation/run
Goal: re-evaluate HEAD4 from scratch on corrected canonical Waku10, prioritizing truly PRISTINE Feb-Jun 2026 evidence and treating Jul-Aug only as descriptive NON-PRISTINE checks.

Exact plan:
1. Keep production `HEAD4_V291_COMP7` unchanged during the entire reevaluation.
2. Use canonical restored Waku10 for every historical read. Do not reuse pre-canonical backtest conclusions for model decisions.
3. Reconstruct/evaluate the current HEAD4 production decision chain on Feb-Jun PRISTINE data: PRE, POST, ENV/A logic, opponent selection, v291 Top4/composite-odds market logic where verified historical closing odds exist.
4. Report race count, bet count, hit count/rate, payout/ROI under the current 10,000 JPY/race Dutch definition whenever verified closing 120/120 trifecta odds are available; otherwise mark ROI unavailable rather than substitute/fabricate odds.
5. Re-evaluate score/threshold stability by month and aggregate Feb-Jun. Include production S/A eligibility counts and performance, not only PRE .03-.05 research bands.
6. Use July/August only as NON-PRISTINE descriptive stress checks. They must not drive threshold/feature/model selection.
7. Compare current production model against any immediately adjacent/frozen candidate versions only if those versions can be reconstructed outcome-blind from prior pristine rules. No new tuning on Jul/Aug/Sep outcomes.
8. September remains outcome-blind and must not be used for tuning/model selection.
9. Run via GitHub Actions, inspect logs/artifacts, and automatically fix/re-run audit errors.
10. AFTER completion, update this handoff with exact Run/Job/Artifact IDs/hashes, Feb-Jun results, Jul-Aug descriptive checks, conclusions, whether production should remain unchanged, and exact restart point.

## Restart protection
If interrupted, resume from canonical-Waku10 HEAD4 pristine reevaluation. The next decision must be based on Feb-Jun PRISTINE evidence, not on the old sparse-public-Waku10 results.
