# CHAT HANDOFF — HEAD4 PRE 0.03-0.05 RESEARCH

Status: **SEASONAL YEAR-OVER-YEAR AUDIT COMPLETE**

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

## Implementation
- analysis: `analyze_4head_seasonal_yoy_20260914.py`
- workflow: `.github/workflows/analyze-4head-seasonal-yoy.yml`
- analysis commit: `c683c494c6c3b36d8245ad91bb0a4a0dc5fe5ab7`
- workflow commit: `53217e894804729f10c80fcfca257084b419cd7f`

Method:
- outcome-blind feature replay; target race results/wins are never loaded
- years compared: 2025 and 2026
- months: May, June, July, August
- features: `inner12_resistance`, `wall3_weak`, `racer4`, `past_win4`, `hist_st_edge_4v3`
- month summaries: row counts, missing/zero shares, mean/median/std/quantiles
- within-year June->July and July->August comparisons using SMD and KS
- causal-history/source availability proxies recorded
- production unchanged.

## CI
- workflow: `analyze-4head-seasonal-yoy`
- Run ID `34774806390`
- Job ID `103770858036`
- head SHA `53217e894804729f10c80fcfca257084b419cd7f`
- conclusion: SUCCESS
- syntax PASS
- analysis PASS
- guard audit PASS
- artifact upload PASS
- artifact name `head4-seasonal-yoy`
- artifact ID `10323355651`
- artifact zip SHA256 `cb9560c4ebfe024221e917add8a48943d2700f05c69fd8e49db9f737b219b918`

## Exact source / feature coverage
| year | month | days | days_with_cards | days_with_features | card_rows | feature_rows | motor_hist_keys_end | preview_cache_keys_end |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2025|5|31|29|29|4759|4759|0|3566|
|2025|6|30|30|30|4731|4731|0|6826|
|2025|7|31|31|31|5072|5072|0|9928|
|2025|8|31|31|31|4968|4968|0|12200|
|2026|5|31|31|31|4832|4832|0|5108|
|2026|6|30|29|29|4488|4488|0|8029|
|2026|7|31|31|31|4920|4920|1590|11023|
|2026|8|31|31|31|4920|4920|1590|13153|

Critical observation: `motor_hist_keys_end` is 0 throughout 2025 and also May/June 2026, then abruptly becomes 1590 in July 2026 and remains there in August. This is a clear 2026-only data/history availability boundary and does not look like a recurring summer effect.

## June -> July feature jumps
|year|feature|SMD|KS|mean Jun|mean Jul|
|---:|---|---:|---:|---:|---:|
|2025|inner12_resistance|-0.210|0.085|0.246|0.232|
|2025|wall3_weak|-0.004|0.018|0.712|0.711|
|2025|racer4|-0.002|0.012|0.420|0.419|
|2025|past_win4|0.000|0.000|0.000|0.000|
|2025|hist_st_edge_4v3|-0.004|0.018|0.279|0.278|
|2026|inner12_resistance|+1.030|0.412|0.243|0.430|
|2026|wall3_weak|-0.931|0.395|0.712|0.495|
|2026|racer4|-0.058|0.035|0.430|0.415|
|2026|past_win4|+0.672|0.237|0.000|0.040|
|2026|hist_st_edge_4v3|-0.011|0.040|0.281|0.278|

## July -> August feature jumps
|year|feature|SMD|KS|mean Jul|mean Aug|
|---:|---|---:|---:|---:|---:|
|2025|inner12_resistance|+0.081|0.031|0.232|0.237|
|2025|wall3_weak|+0.006|0.009|0.711|0.712|
|2025|racer4|+0.076|0.037|0.419|0.439|
|2025|past_win4|0.000|0.000|0.000|0.000|
|2025|hist_st_edge_4v3|+0.006|0.009|0.278|0.280|
|2026|inner12_resistance|+1.421|0.574|0.430|0.705|
|2026|wall3_weak|-1.161|0.554|0.495|0.196|
|2026|racer4|+0.066|0.035|0.415|0.432|
|2026|past_win4|+0.602|0.340|0.040|0.100|
|2026|hist_st_edge_4v3|+0.034|0.087|0.278|0.288|

## Main interpretation
The hypothesis that the observed 2026 July/August shift is primarily a normal recurring summer/second-half seasonal transition is NOT supported by this year-over-year feature audit.

Why:
1. 2025 shows almost no June->July movement in four of the five focal features and only a small `inner12_resistance` change (-0.210 SMD), while 2026 shows very large June->July shifts in `inner12_resistance` (+1.030), `wall3_weak` (-0.931), and `past_win4` (+0.672).
2. 2025 July->August is also essentially stable, while 2026 continues shifting strongly (`inner12_resistance` +1.421, `wall3_weak` -1.161, `past_win4` +0.602).
3. Most importantly, a source/history proxy (`motor_hist_keys_end`) jumps from 0 through June 2026 to 1590 in July 2026, whereas it stays 0 throughout the comparable 2025 months. This is a concrete 2026-only pipeline/data-availability boundary.

This does NOT prove motor-history availability is the sole cause of the PRE collapse/recentering, because the largest drift features are not all motor-history fields. It does, however, materially strengthen the pipeline/data-boundary hypothesis over a generic seasonal explanation.

## Limitations
- Verified public realtime coverage used here exposes 2025 and 2026, not 2024, so 2024 was not fabricated.
- This audit measures feature distributions and source/history proxies only; it does not establish causal attribution from the July motor-history boundary to each shifted feature.
- July/August 2026 remain NON-PRISTINE and cannot select production changes.
- Production remains unchanged.

## Restart point
Next safest audit:
1. Trace exactly why `motor_hist_keys_end` switches from 0 to 1590 at the July 2026 boundary.
2. Inspect `backtest_v3.ingest_motor`, its upstream source path/date coverage, and any date-gated fallback/default logic.
3. Trace whether `inner12_resistance`, `wall3_weak`, `past_win4`, and `legacy_score4` indirectly depend on motor/history or on another source that changes at the same boundary.
4. Compare raw primitive availability on late June vs early July 2026 day-by-day to identify the exact first transition date.
5. Re-run a corrected causal replay with the boundary source held consistent across months, comparing score distributions only first.
6. Do not change production until lineage/corrected replay is documented.
7. September outcomes remain unavailable for tuning/model selection until predictions are frozen.

Before next implementation, append the exact work plan here. After completion append commits, CI IDs, findings, limitations, and next restart point.
