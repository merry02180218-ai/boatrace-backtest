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

### LIVE A status / next operational requirement

Frozen A-LIVE itself is exact 47R and its historical all-N audit is complete. The added-race A-LIVE rescue remains REJECTED; A-LIVE may still be used as the LIVE score/tier layer, but it must not silently add races outside the frozen v291 entry policy without a separately validated rule.

For current LIVE operation, wire the existing `fetch_live_trifecta_odds.py` snapshot into the 4号艇 v291 BET path so that the formally adopted `floor=4.0/maxN=16` N-selection and ¥10,000 Dutch stakes are computed from an actual **pre-deadline timestamped odds snapshot**. Never substitute official closing odds for a live purchase-time decision.

Fail closed if:
- snapshot has fewer/more than exactly 120 valid combinations;
- snapshot timestamp is not suitable for the intended purchase time;
- odds snapshot is missing;
- any result/payout-derived information is present.

## Decision / current status

1. v291 race-entry logic remains frozen.
2. `floor=4.0/maxN=16` is now the formally adopted variable-ticket policy.
3. A-LIVE added-race rescue remains REJECTED.
4. Existing official pre-deadline odds acquisition code has been rediscovered and must be reused for LIVE operationalization.
5. September remains outcome-blind; only label-free operational shadow generation is allowed.

## Next restart point

1. Inspect current 4号艇 LIVE workflow (`.github/workflows/live-4head-v291-pre-daily.yml` and downstream scripts) and connect `fetch_live_trifecta_odds.py` at purchase-time.
2. Generate N=4..16 composite-odds curve from that timestamped snapshot in frozen v283 ranked order.
3. Select largest N with composite >= 4.0; fail closed if none/invalid.
4. Produce exact ¥10,000 Hamilton Dutch stakes and freeze the decision artifact together with the odds snapshot timestamp/hash.
5. Run a September **outcome-blind** operational shadow test only; do not join results or payouts.
6. Record implementation, CI run IDs, operational failures/successes and any adoption/rejection reason in this handoff.

Do not use July/August outcomes or any September result/payout labels for further rule selection. Do not relax frozen-artifact parity guards merely to force CI green.
