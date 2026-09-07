# v165/v166 3-head research

Goal: rebuild the 3-head strategy using the production 1-head architecture as reference.

- v165: monthly walk-forward probability that boat 3 wins.
- v166: direct ordered-pair ranking for 3-s-t tickets, only after v165 and explicit pair schema are validated.
- Holdout: Jun, Jul, Aug 2026, each month trained only on earlier dates.
- No current-race result/payout/final odds may enter features.
- Existing 3-makuri / 3-makuri-zashi structural scores remain candidate explanatory features when explicitly available.
- Do not fabricate lane-3 data by copying lane-1 fields. If the current source lacks explicit lane-3 features, stop and report schema requirements.

Primary evaluation:
1. 3-head probability calibration / AUC / Brier.
2. Thresholded head rate and race count by month.
3. After head model is acceptable: 7-ticket conditional coverage, full 7-ticket hit rate, ROI.
4. Compare monthly stability against the existing 3-makuri and 3-makuri-zashi operation.
