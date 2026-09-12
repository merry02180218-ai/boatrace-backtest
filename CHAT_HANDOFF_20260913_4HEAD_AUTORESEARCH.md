# CHAT HANDOFF — 2026-09-13 — 4号艇自動研究

Updated: 2026-09-13 JST
Repository: `merry02180218-ai/boatrace-backtest`
Scope: 4号艇 v291 volume expansion / LIVE operationalization.

## Immutable production baseline / newly adopted ticket policy

Base entry model remains `HEAD4_V291_COMP7`. Do not mutate its race-entry logic in place.

- PRE >= 0.28
- POST >= 0.25
- ENV_ENTRY >= 0.224790
- frozen v283 opponent order
- Top4 + composite >= 7.0 entry identity
- ¥10,000/race inverse-odds Dutch / ¥100 Hamilton rounding

### FORMAL USER DECISION — 2026-09-13

The variable-ticket policy **`composite odds floor = 4.0 / maxN = 16` is formally adopted** for 4号艇 operation.

Interpretation:
- keep the frozen v291 29-race entry identities / entry logic;
- for a v291 BET race, use the frozen v283 ranked trifecta order;
- expand ticket count from N=4 up to at most N=16;
- choose the largest N whose composite odds remain >= 4.0;
- keep total race bank exactly ¥10,000 using inverse-odds Dutch + ¥100 Hamilton rounding;
- this is a separately versioned ticket-allocation policy; do not rewrite historical v291 evidence.

Apr–Jun evidence for the formally adopted policy:
- R = 29
- ROI = 188.83%
- hit rate = 44.83%
- average N = 9.97
- minimum monthly ROI = 143.52%

Why maxN=16 is preferred operationally over maxN=20:
- extending beyond 16 did not improve the observed ROI/hit result in the completed grid while adding ticket count/exposure complexity;
- therefore cap at 16.

July/August 2026 remain NON-PRISTINE. September 2026 outcomes are outcome-blind and prohibited for fitting, calibration, rule selection or evaluation. v96 is prohibited from production logic.

## Exact A-LIVE audit and recovery

Audit run `34704536525` proved the old OOF-A identity set was not identical to frozen A-LIVE.

- exact frozen A-LIVE: 47R
- old OOF A curves: 47R
- overlap: 44R
- added vs old: 3R
- dropped vs old: 3R
- missing exact identities before recovery:
  - `202604190703`
  - `202604272402`
  - `202606130609`

Therefore old v288 OOF-A ROI is rejected as production evidence.

Recovery implementation uses immutable official closing 3T odds plus frozen v291/v283 ordering logic. Successful workflow run `34708490537` completed the recovery and research pipeline.

Final audit state:
- exact A-LIVE = 47R
- complete all-N curve coverage = 47/47
- `audit_4head_v291_a_live_curve_recovery.json.status == PASS`
- `audit_4head_v291_a_live_identity.json.status == PASS_EXACT_CURVES_AVAILABLE`
- `missing_curve_R == 0`
- Jul/Aug outcomes used = false
- September outcomes used = false
- v96 used = false

Persisted exact research input:
- `analysis_v291_4head_composite_odds_alln_exactalive.csv`

## Added-race rescue result — REJECT

The exact 47R A-LIVE target-composite/additional-race rescue completed after recovery.

Output:
- `head4_v291_a_targetcomp_rescue_candidate.json`
- `summary_4head_v291_a_targetcomp_rescue.md`

Decision: **REJECT**.

Reason:
- no standalone-safe added-race candidate passed the required stability/LOMO gates;
- v291 base profit must not be used to hide a losing rescue route;
- production entry set remains unchanged.

## CI reproducibility finding

Combined workflow run `34709042736` failed while regenerating the frozen downstream artifact before variable-N research.

Failure:
- v283 conditional THIRD June parity max absolute drift = `9.04380706659e-05`
- fail-closed parity guard blocked the run.

This was not a variable-N model failure. The guard was NOT relaxed. Persisted exact 47/47 curves from successful run `34708490537` remain the research input.

Isolated workflow:
- `.github/workflows/research-4head-v291-base-variable-n.yml`

## Immutable-base variable-N research

Goal: improve hit coverage without changing the 29 v291 race identities or the ¥10,000 per-race bank.

Development/evaluation universe:
- April–June 2026 only;
- July/August excluded as NON-PRISTINE;
- September outcomes excluded;
- no v96.

Corrected isolated CI run `34709643396`: **SUCCESS**.

Baseline N=4:
- ROI 300.26%
- hit rate 31.03%

Important neighborhood results:
- floor 5.0 / maxN 6: ROI 213.48%, hit 34.48%, avg N 5.72, monthly ROI floor 140.37%
- floor 4.0 / maxN 12: ROI 180.07%, hit 41.38%, monthly ROI floor 122.51%
- **floor 4.0 / maxN 16: ROI 188.83%, hit 44.83%, avg N 9.97, monthly ROI floor 143.52% — FORMALLY ADOPTED 2026-09-13**
- floor 3.0 / maxN 16: ROI 172.41%, hit 51.72%, monthly ROI floor 136.40%

Historical corrected LOMO selections remain research evidence and are not rewritten after the user's explicit operational choice:
- Apr holdout: training selected floor=4.0/maxN=16; holdout ROI 239.63%, hit 58.33%
- May holdout: training selected floor=5.0/maxN=6; holdout ROI 140.37%, hit 22.22%
- Jun holdout: training selected floor=4.0/maxN=12; holdout ROI 122.51%, hit 25.00%

## LIVE A / pre-deadline trifecta odds — IMPORTANT RECOVERY

Do **not** claim that pre-deadline 3連単 odds acquisition is unavailable. The repository already contains a result-free official live odds fetcher:

- script: `fetch_live_trifecta_odds.py`
- workflow: `.github/workflows/live-trifecta-odds-smoketest.yml`
- official source: `https://www.boatrace.jp/owpc/pc/race/odds3t`
- fetches only the official odds3t page; result/payout endpoints are explicitly deny-listed;
- validates the exact full set of 120 ordered trifecta combinations before a snapshot is usable;
- writes timestamped immutable raw HTML + CSV + metadata JSON;
- metadata records JST request/fetch timestamps, source URL, hash, parsed count and `usable_for_betting`;
- live operation is designed to run repeatedly until the intended purchase-time snapshot and then freeze that timestamped file.

Historical chat/work log also identifies the earlier 3号艇 implementation as `v218 SHADOW`, with snapshots under `live_freeze/v218_3head/` and commit `76cac219`; this historical reference should be verified from GitHub history before reusing exact old paths, but it confirms that deadline-time odds acquisition was previously part of the LIVE architecture.

### LIVE A status

Frozen A-LIVE is operationally available through `HEAD4_V273_A_LIVE_QMAP` and `head4_v273_a_live_inference.py`.

Priority/semantics:
- S has priority.
- A is evaluated only outside S.
- S gate remains PRE>=0.28 / POST>=0.25 / ENV_ENTRY>=0.224790.
- A gate remains PRE>=0.18 / POST>=0.18 plus frozen outcome-blind mapped `A_SCORE_LIVE` threshold from the artifact trained through 2026-06-30.
- added-race A-LIVE rescue remains REJECTED; the A score/tier may be used, but it does not authorize bypassing v291 market entry.

## 2026-09-13 S/A variable-N LIVE implementation — COMPLETE / CI PASS

Implemented:
- `run_4head_v291_varn_live.py`
- `verify_4head_v291_varn_live.py`
- `.github/workflows/validate-4head-v291-varn-live.yml`

New policy ID:
- `HEAD4_V291_COMP7_VARN_F4_N16`

Exact prospective chain implemented:

`frozen PRE/POST/ENV_ENTRY + frozen A features -> S priority / A outside S -> frozen v283 full 4-x-y order -> official pre-deadline odds3t 120-way snapshot -> original v291 Top4 composite >= 7.0 entry gate -> largest N=4..16 with composite >=4.0 -> exact ¥10,000 Dutch / ¥100 Hamilton -> append audit before result`

Important invariants verified:
- v291 Top4 entry logic is preserved exactly; variable-N does not create new races by itself.
- full v283 ordering must have 20 unique 4-head combinations.
- first four combinations must exactly equal legacy frozen v283 Top4.
- S priority and A-only-outside-S semantics are preserved.
- A uses the frozen inference-only artifact; no LIVE `.fit()`.
- official odds fetch remains result-free and requires exactly 120 combinations.
- deadline is checked before/after odds fetch and immediately before decision persistence.
- Top4 composite <7 => PASS even if wider-N market conditions might look attractive.
- Top4 composite >=7 => select largest N <=16 whose composite >=4.0.
- every BET uses exactly ¥10,000; stakes are positive ¥100 multiples and sum exactly ¥10,000.
- missing/late/incomplete input => fail closed `ERROR_NO_BET`.
- no Jul/Aug fitting/tuning; no September outcomes/results/payouts used.

CI history:
- first validation run `34710678134`: runner/economics verifier itself printed `VERIFY_4HEAD_V291_VARN_LIVE_OK`, but workflow failed because a naive grep guard falsely matched the explanatory comment text `result/payout` in the source. This was **not a model or LIVE-logic failure**.
- guard-only fix commit: `d61da6b328827d3b5d221c31c159bdae5174549e`.
- corrected validation run `34711859515`: **SUCCESS**.

Decision:
- **S/A LIVE market/ticket runner is now implementation-complete and CI-validated.**
- The adopted `floor=4.0/maxN=16` rule is wired after the immutable v291 Top4>=7 entry gate.
- A-LIVE can now produce a formal layer classification and, when the same immutable v291 market entry gate passes, a real pre-deadline variable-N ticket set with exact ¥10,000 Dutch stakes.

Operational limitation still remaining:
- the generalized daily PRE workflow exists, but a one-click fully automated scheduler from PRE candidate detection through exhibition-time POST/ENV_ENTRY/A-feature/v283-input generation into this new S/A market runner is still a separate integration task.
- Until that orchestration is completed, the new runner requires a correctly frozen pre-result input JSON containing PRE/POST/ENV_ENTRY, v283 `p2`/`cond`, and the 17 A feature keys.

## Decision / current status

1. v291 race-entry logic remains frozen.
2. `floor=4.0/maxN=16` is formally adopted and implemented as `HEAD4_V291_COMP7_VARN_F4_N16`.
3. A-LIVE score/tier inference is operational and now connected to the same pre-deadline v291/variable-N market runner.
4. A-LIVE added-race rescue remains REJECTED.
5. Existing official pre-deadline odds acquisition is reused; post-deadline/closing odds are never a LIVE fallback.
6. Corrected CI run `34711859515` is SUCCESS.
7. September remains outcome-blind; only pre-result operational generation is allowed.

## Next restart point

1. Complete orchestration after daily PRE: for PRE candidates, fetch exhibition/current data when available and generate frozen POST / ENV_ENTRY / the 17 A features / v283 p2+conditional-third inputs without refitting.
2. Feed the resulting immutable pre-result JSON directly into `run_4head_v291_varn_live.py` before deadline.
3. Persist/freeze input manifest, source timestamps/hashes, odds snapshot metadata, layer classification, selected N and stakes together.
4. Run September outcome-blind shadow executions only; never join current-month results/payouts for tuning or validation.
5. If orchestration CI fails, repair only operational plumbing/parity; do not lower gates or alter model/ticket rules.

Do not use July/August outcomes or any September result/payout labels for further rule selection. Do not relax frozen-artifact parity guards merely to force CI green.
