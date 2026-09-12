# v305 1HEAD leakage audit

- Development only; production unchanged.
- Jul/Aug NON-PRISTINE; September outcomes unread.
- Same frozen opponent eligibility and exact monthly selected counts as v303/v304.
- Meeting-derived transfer fields are fail-closed as unsafe because historical race-card snapshots are not intraday-versioned.

## Feature provenance audit
- Transferred TURN_FORM/STMOTOR features inventoried: **114**.
- Meeting-derived / operationally unproven features: **9**.

## Results
|config|R|head hits|head rate|delta|worst month|
|---|---:|---:|---:|---:|---:|
|V304_FULL|204|181|88.73%|+7.35pt|68.63%|
|STRICT_TURN_FORM|204|168|82.35%|+0.98pt|78.38%|
|STRICT_TURN_FORM_STMOTOR|204|168|82.35%|+0.98pt|72.22%|
|BASE|204|166|81.37%|+0.00pt|78.38%|

## Strict-safe monthly audit
|month|R|hits|head rate|
|---|---:|---:|---:|
|2026-02|18|13|72.22%|
|2026-03|29|24|82.76%|
|2026-04|37|31|83.78%|
|2026-05|69|59|85.51%|
|2026-06|51|41|80.39%|

## Decision
- FULL v304: **181/204 = 88.73%**.
- STRICT no-meeting transfer: **168/204 = 82.35%**.
- Removing operationally unproven meeting-derived transfer fields changes head rate by **-6.37pt**.
- If STRICT retains most of the gain, the late-month decline is more consistent with distribution/season drift than direct meeting-field leakage. If STRICT collapses, v304 gain must be treated as contaminated until those fields are reconstructed causally.
