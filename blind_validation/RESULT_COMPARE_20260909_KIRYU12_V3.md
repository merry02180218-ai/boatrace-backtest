# 2026-09-09 桐生12R — SES v3 blind validation comparison

## Blind lock

The SES judgment was committed before reading the race result.

- SES lock commit: `1bd4aac71e5957c5e8f020b5f8c25343bc8e42b2`
- Exhibition entry order observed: `1-2-4-5-6-3`
- Native video size: `1920x1080`
- Slit anchor: `111.0 sec`
- Tracker accepted: `true`
- Leakage guard at lock time: `PRE_RACE_VIDEO_ONLY; RESULT NOT READ BEFORE THIS LOCK`

### Locked SES v3

| Boat | Relative forward @ +1.5s (px) | Stretch rank | SES v3 |
|---:|---:|---:|---:|
| 1 | +9.670 | 1 | +1 |
| 2 | +4.313 | 3 | 0 |
| 3 | +9.606 | 2 | +1 |
| 4 | -7.415 | 5 | -1 |
| 5 | -18.710 | 6 | -2 |
| 6 | +2.536 | 4 | 0 |

## Result joined only after lock

Official result:

- Finish: `3-5-4`
- Winning method: `まくり`
- Race ST: 1=.18, 2=.17, 3=.10, 4=.10, 5=.19, 6=.12
- Trifecta payout: 65,730 yen

## Interpretation

This first blind case is directionally positive for the **3-head attack signal**: boat 3 was locked as the second-best post-slit extension with SES +1, then won by makuri. It is **not** a clean confirmation of the full six-boat finishing order: boat 5 was locked weakest (SES -2) but finished second, and boat 4 was SES -1 but finished third.

Therefore SES should currently be treated as an attack/head-support feature, not as a direct finishing-order rank. One race is far too small for statistical conclusions.

## Important tracking correction discovered

The earlier v3 failure was not evidence that boat 1 was inherently untrackable. The manual seed coordinates had been measured on a rendered `1600x900` preview and were mistakenly applied directly to the native `1920x1080` video. Scaling the seeds to native coordinates produced an accepted run with substitutions: 1=9, 2=0, 3=0, 4=2, 5=0, 6=0 (limit 11).

Future tooling must record/normalize seed coordinate space before tracking, otherwise preview scaling can silently corrupt SES.
