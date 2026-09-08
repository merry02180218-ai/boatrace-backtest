# v210 3-head PRE ensemble — SHADOW

**Goal: predict eventual v165 p3head>=30% using PRE-safe data with fewer exhibition checks.**

- Protocol: June train -> July ensemble/cut selection -> exact same raw-score cut on August.
- August is report-only and already inspected historically; do not call this pristine OOS adoption evidence.
- rows: June 4388, July 4772, August 4776; unmatched 392; missing dates ['2026-06-17'].

## July-selected ensemble, frozen August
|target|ensemble|raw cut|July watch|July recall|July precision|Aug watch|Aug recall|Aug precision|
|---:|---|---:|---:|---:|---:|---:|---:|---:|
|8%|prior_plus_base|0.301497|382 (8.0%)|67.8%|15.4%|424 (8.9%)|77.3%|20.0%|
|10%|prior_plus_base|0.167737|478 (10.0%)|74.7%|13.6%|520 (10.9%)|82.7%|17.5%|
|12%|mean|0.122123|573 (12.0%)|78.2%|11.9%|652 (13.7%)|84.5%|14.3%|

## August operational settlement (od3, ¥10,000 Dutch)
|rule|settled R|Top10 hit|avg composite|return|ROI|
|---|---:|---:|---:|---:|---:|
|v210_8pct_prior_plus_base|84|34.5%|3.604|¥837,090|**99.7%**|
|v210_10pct_prior_plus_base|90|32.2%|3.699|¥837,090|**93.0%**|
|v210_12pct_mean|92|32.6%|3.719|¥909,810|**98.9%**|

## Previously missed profitable races audit
|rule|race|score|cut|PRE watch|formal v165 pass|
|---|---|---:|---:|---|---|
|v210_8pct_prior_plus_base|202608112308|0.001503|0.301497|NO|1|
|v210_8pct_prior_plus_base|202608210409|0.006008|0.301497|NO|1|
|v210_10pct_prior_plus_base|202608112308|0.001503|0.167737|NO|1|
|v210_10pct_prior_plus_base|202608210409|0.006008|0.167737|NO|1|
|v210_12pct_mean|202608112308|0.001643|0.122123|NO|1|
|v210_12pct_mean|202608210409|0.006566|0.122123|NO|1|

## Decision
- Production remains unchanged. v210 is SHADOW only.
- Prefer the smallest target rate that materially preserves v165-pass recall and does not worsen operational return concentration.
