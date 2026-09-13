# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **HEAD4 WAKU10 ABLATION AUDIT STARTED**

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

## Canonical Waku10 full HEAD4 pristine re-evaluation — COMPLETE
- Workflow: `.github/workflows/reevaluate-head4-canonical-waku10.yml`.
- Run `34783210177`, Job `103793867409`: SUCCESS.
- Artifact `head4-canonical-waku10-pristine-reevaluation`, ID `10325184553`, SHA256 `1c29e9e8e2bfc720f18800f08b4d9bbe8e14e9fe68bffd421cc92be8e7563be0`.
- Corrected Apr-Jun archived-odds proxy results:
  - S: 72R, 29 heads, 10 trifecta hits, ROI 103.26%.
  - A: 56R, 21 heads, 5 hits, ROI 74.36%.
  - S+A: 128R, 50 heads, 15 hits, ROI 90.61%.
- Rebuilt canonical A_SCORE_LIVE candidate threshold: `0.2826475979692089` vs current production `0.2710428764008591`.
- Old pre-canonical ~131% S+A claim does not survive corrected rebuild.
- Production remains unchanged.

## CURRENT WORK-START RECORD — Waku10 ablation audit
Goal: determine whether HEAD4 performs better with no Waku10-derived signal, or only a subset, under the same corrected canonical data and causal evaluation conditions.

Pre-declared comparison before implementation:
1. Keep production `HEAD4_V291_COMP7` unchanged throughout.
2. Use the same canonical raw source, same date splits, same labels, same archived-odds proxy rules, and same causal/OoF semantics across variants.
3. Primary selection/evaluation window: Apr-Jun 2026 only. July/August remain NON-PRISTINE descriptive stress checks only; September outcomes prohibited.
4. Compare at minimum:
   - `FULL_WAKU10`: current corrected canonical feature set.
   - `NO_WAKU10`: remove direct Waku10-derived inputs and composites whose construction materially depends on Waku10 (`waku_wr`, `waku_st`, `waku_sr`, `past10/past_win`, plus dependent `resistance12`, `wall3_weak`, and Waku10-dependent legacy components rather than silently zero-imputing them).
   - `CORE_WAKU10`: retain only stable direct frame statistics needed for a minimal signal test, while excluding past10 and higher-order Waku10 composites; exact feature membership must be written into the audit output before outcome summaries are interpreted.
5. Do not compare a missing-data model against a complete-data model. Every variant must be explicitly trained/rebuilt from the same canonical rows with its own fixed feature definition.
6. Report by month and Apr-Jun aggregate: S/A/S+A race counts, 4-head hit rate, trifecta hit rate, archived-odds proxy ROI where available, and score calibration/distribution.
7. Any variant ranking is exploratory retrospective evidence only. Do not alter production from this audit alone.
8. Run via GitHub Actions; inspect logs/artifacts; auto-fix and rerun failures.
9. AFTER completion, update this handoff with exact feature definitions, commits, Run/Job/Artifact IDs/hashes, Apr-Jun results, Jul-Aug descriptive stress checks, interpretation, and exact restart point.

## Restart protection
If interrupted, resume from the Waku10 ablation audit above. Do not use Jul/Aug/Sep outcomes to choose features or thresholds. Production stays `HEAD4_V291_COMP7` until a separately frozen prospective replacement policy is validated.
