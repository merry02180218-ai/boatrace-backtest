# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **SEASONAL YEAR-OVER-YEAR AUDIT IN PROGRESS**

## Frozen production
Production remains unchanged. S PRE >= 0.28; A PRE >= 0.18; frozen downstream rules remain in force. July/August 2026 remain NON-PRISTINE; September remains outcome-blind for tuning.

## Prior completed findings
- Common frozen-scale: Feb-Jun 2026 PRE .03-.05 head rate 3.67%; July 6.97%; August 23.18% (July/Aug NON-PRISTINE).
- Outcome-independent drift audit: July PRE<.01 28.48%, August 68.90% under Jan-31 frozen model; largest August shifts were `inner12_resistance`, `wall3_weak`, `racer4`, `past_win4`, `hist_st_edge_4v3`.
- Rolling fit-cutoff diagnostic: even a Jun-30 fit gives August PRE<.01 77.83%, while a Jul-31 diagnostic fit recenters August to 7.40%. This means July contains structural information needed to adapt, but does not yet distinguish genuine seasonal/regime change from a data/feature boundary.
- Primary rolling-fit CI: Run `34773603328`, Job `103767543705`, Artifact `10322079757`.

## 2026-09-14 seasonal year-over-year audit work-start record
Written BEFORE implementation after the user asked whether the July shift could relate to the summer / second-half seasonal regime.

Exact plan:
1. Keep production unchanged and keep the audit outcome-blind: do not use target race wins/losses to rank or select a seasonal explanation.
2. Use the same causal feature-generation path behind v250 / the completed drift audit.
3. Compare May, June, July, and August feature/population distributions year-over-year wherever source coverage exists.
4. The public BoatraceCSV realtime result tree currently exposes 2025 and 2026, not 2024. Therefore primary comparable years will be 2025 and 2026 unless another verified causal source for 2024 is found; do not fabricate 2024.
5. Focus on the five strongest shifted PRE inputs: `inner12_resistance`, `wall3_weak`, `racer4`, `past_win4`, `hist_st_edge_4v3`.
6. For each year/month, report row count, mean, median, std, zero/default share, missing/non-finite share, and selected quantiles.
7. Quantify the June->July and July->August jump within each year using standardized mean difference / KS where possible. The key question is whether 2025 also shows a July-boundary move in the same direction and comparable magnitude.
8. Also report causal-history / source availability proxies so a 2026-only missing/default boundary can be separated from a recurring summer pattern.
9. Do not use July/August 2026 outcomes to tune thresholds, select rescue rules, select features, or change production.
10. Run CI and upload artifacts.
11. After completion update this same handoff with implementation commits, CI Run/Job/Artifact IDs, exact findings, limitations, interpretation, and next restart point.
