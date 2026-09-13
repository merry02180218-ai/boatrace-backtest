# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **CANONICAL WAKU10 HEAD4 PRISTINE RE-EVALUATION COMPLETE**

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
Work-start plan was to rebuild the HEAD4 chain from corrected canonical Waku10 without reusing stale intermediate CSVs, keeping production unchanged and using Apr-Jun as the pristine development comparison window.

Implementation/run lineage:
- New audit workflow: `.github/workflows/reevaluate-head4-canonical-waku10.yml`.
- Workflow creation commit: `612abd96a4d7e5a06569588905f2405ee2b770d8`.
- Trigger commit: `2e4d4afe2f45e0d3b4ef50c227ca7e6dc2761500`.
- Rebuilt in one CI job in this order: `v250 -> v93 -> v264 -> v267 -> v271 -> candidate v273 LIVE mapping`.
- Run `34783210177`, Job `103793867409`: **SUCCESS**.
- Artifact `head4-canonical-waku10-pristine-reevaluation`, ID `10325184553`, SHA256 `1c29e9e8e2bfc720f18800f08b4d9bbe8e14e9fe68bffd421cc92be8e7563be0`.

Corrected Apr-Jun results using archived historical odds proxy (10,000 JPY/race; NOT immutable contemporaneous LIVE odds):
- S:
  - Apr: 15R, 3 heads (20.00%), 1 trifecta hit (6.67%), ROI 62.88%.
  - May: 33R, 17 heads (51.52%), 6 hits (18.18%), ROI 137.84%.
  - Jun: 24R, 9 heads (37.50%), 3 hits (12.50%), ROI 80.95%.
  - Aggregate: 72R, 29 heads (40.28%), 10 hits (13.89%), return 743,470 JPY on 720,000 JPY, proxy ROI 103.26%.
- A (OOF development semantics, outside S, PRE>=.18, POST>=.18, OOF A_SCORE>=.28):
  - Apr: 21R, 9 heads (42.86%), 2 hits (9.52%), ROI 72.38%.
  - May: 18R, 5 heads (27.78%), 1 hit (5.56%), ROI 51.72%.
  - Jun: 17R, 7 heads (41.18%), 2 hits (11.76%), ROI 100.76%.
  - Aggregate: 56R, 21 heads (37.50%), 5 hits (8.93%), return 416,390 JPY on 560,000 JPY, proxy ROI 74.36%.
- S+A aggregate:
  - Apr: 36R, 12 heads (33.33%), 3 hits (8.33%), ROI 68.42%.
  - May: 51R, 22 heads (43.14%), 7 hits (13.73%), ROI 107.45%.
  - Jun: 41R, 16 heads (39.02%), 5 hits (12.20%), ROI 89.16%.
  - Aggregate: 128R, 50 heads (39.06%), 15 hits (11.72%), return 1,159,860 JPY on 1,280,000 JPY, proxy ROI **90.61%**.

A-score LIVE mapping changed materially under canonical Waku10:
- Current production `A_SCORE_LIVE`: `0.2710428764008591`.
- Rebuilt canonical candidate threshold: `0.2826475979692089`.
- Canonical reference universe: 173R, frozen OOF-selected 57R = 32.95%; mapped selected 57R exactly.
- Month reference counts: Apr 57R/21 selected, May 65R/19 selected, Jun 51R/17 selected.
- Mapping itself is outcome-blind; July/August labels and September labels are not used.

Decision / limitations:
- The old pre-canonical headline that S+A produced ~131% proxy ROI over 100 races does **not** survive this full canonical rebuild.
- Corrected canonical S+A proxy ROI is 90.61%; A-only is 74.36%; S-only is 103.26% aggregate but loses in Apr and Jun.
- Therefore the current A layer is not supported by the corrected Apr-Jun archived-odds development evidence.
- However this audit is still retrospective and uses archived historical odds proxy, not immutable contemporaneous LIVE pre-deadline odds; it is NOT formal OOS profitability evidence.
- Do NOT alter production automatically from this audit alone. `HEAD4_V291_COMP7` remains unchanged pending a separately frozen, outcome-blind canonical replacement decision and prospective validation.
- July/August remain NON-PRISTINE and did not select/tune any threshold here. September outcomes remain prohibited for tuning/model selection.

## Exact restart point
1. Treat all old sparse-public-Waku10 HEAD4 development profitability claims as superseded by the canonical rebuild where they conflict.
2. Next research should isolate whether to retire/rebuild the A layer using only corrected canonical pre-Jul data and a pre-declared outcome-blind procedure; do not tune from Jul/Aug/Sep outcomes.
3. Preserve current production until a replacement policy is explicitly frozen before outcome inspection and then validated prospectively with immutable pre-deadline 120/120 odds.
