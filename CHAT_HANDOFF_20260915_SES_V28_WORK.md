# SES v28 work handoff — 2026-09-15

## BEFORE WORK

Latest authoritative SES handoff and GitHub were re-read before changing code.

Current verified state:
- v27 commit: `9881ee756934d80bec2618425791a8ec8c941ee9`
- v27 regression run: `34962761028`
- all four technical cases failed closed at Track v27.
- Kiryu3 log ends with `FAIL_CLOSED: no feasible joint six-boat assignment`.
- No race results were read; September SES blindness is preserved.

Work starting now:
1. Do not loosen NCC/fallback/motion/geometry acceptance thresholds.
2. Replace only v27's leave-one-out fleet predictor with a more camera-compatible result-blind leave-one-out affine fleet transform when the five reference boats have sufficient 2D rank/conditioning; otherwise fall back to the exact v27 similarity predictor.
3. Keep candidate generation, six-boat mutual exclusion, immutable reverse-motion corridor, fail-closed behavior, and all quality thresholds unchanged.
4. Run the same four-case technical matrix on the Japan self-hosted runner.
5. Inspect physical trajectories/acceptance, not CI green alone.
6. Do not wire production/live wrapper unless one unchanged combination passes the matrix sanely.

Next code candidate: `track_exhibition_boats_v28.py`.
