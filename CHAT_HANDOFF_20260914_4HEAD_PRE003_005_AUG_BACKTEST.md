# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **JULY 2026 DAY-LEVEL PIPELINE BOUNDARY AUDIT IN PROGRESS**

## Frozen production
Production remains unchanged. S PRE >= 0.28; A PRE >= 0.18; frozen downstream rules remain in force. July/August 2026 remain NON-PRISTINE; September remains outcome-blind for tuning.

## Prior completed findings
- Common frozen-scale: Feb-Jun 2026 PRE .03-.05 head rate 3.67%; July 6.97%; August 23.18% (July/Aug NON-PRISTINE).
- Outcome-independent drift audit: July PRE<.01 28.48%, August 68.90% under Jan-31 frozen model.
- Rolling fit-cutoff diagnostic: even Jun-30 fit gives August PRE<.01 77.83%; Jul-31 diagnostic fit recenters August to 7.40%.
- Seasonal YoY audit: 2025 has almost no June->July feature shift, while 2026 has large shifts. `motor_hist_keys_end` is 0 through June 2026 then 1590 in July/August. CI Run `34774806390`, Job `103770858036`, Artifact `10323355651`.

## 2026-09-14 day-level July boundary audit work-start record
Written BEFORE implementation after user approved tracing the exact July transition.

Exact plan:
1. Keep production unchanged and keep this audit outcome-blind. Do not load target race wins/losses for ranking, diagnosis, or selection.
2. Inspect `backtest_v3.ingest_motor`, its upstream `data/programs/motor_history/YYYY/MM/DD.csv` source availability, and the causal order used by the v250 feature replay.
3. Replay late June through early/mid July 2026 day-by-day with sufficient warm-up and record, before each target day is scored: `motor_hist_keys`, number of motor-history rows available that day, preview-cache size, race-card rows, generated feature rows.
4. Identify the exact first date where motor-history data becomes available and the exact first scoring date where that newly ingested history can affect features (respecting causal order: score first, then ingest current day for tomorrow).
5. On each day, summarize the main shifted PRE inputs: `inner12_resistance`, `wall3_weak`, `past_win4`, `racer4`, `hist_st_edge_4v3`, plus `legacy_score4`, including mean/median/zero share and selected quantiles.
6. Where possible, score PRE with a fixed pre-boundary frozen model so daily PRE distribution/bin shares can be compared without refitting. Primary question: does the PRE collapse start on/near the first motor-history-effective scoring date, or does it begin independently?
7. Inspect whether the shifted non-motor features directly/indirectly depend on `mhist` or instead reflect separate history/default logic changing at the same time.
8. If motor-history onset and PRE/feature shift dates do not align, do not force causality; report the mismatch and trace the next source boundary.
9. July/August 2026 remain NON-PRISTINE and cannot select production thresholds/features/rescue rules. September outcomes remain unavailable for tuning/model selection until predictions are frozen.
10. Run CI and upload a day-level audit artifact.
11. AFTER completion, update this handoff with implementation commits, CI Run/Job/Artifact IDs/hash, exact first transition dates, daily findings, limitations, interpretation, and next restart point.

## Restart protection
If interrupted, resume from this work-start record. Do not change production before completing the lineage audit.
