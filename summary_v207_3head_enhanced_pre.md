# v207 enhanced 3-head PRE — strict July select / August untouched

**SHADOW検証。productionは変更しない。PREは監視候補のみで、正式判定は展示後 v165 p3head>=30% -> v166 Top10。**

## Leak audit
- `analysis_3attack_rows.csv` generator computes target-day features before reading outcomes.
- prior exhibition / prior straight / prior display / prior turn and motor history are inserted into cache only after each day, so target day cannot enter its own PRE features.
- reconstructed rows: June 4388, July 4772, August 4776; unmatched 392; waku sources {'boatracecsv_saved': 44, 'boatcast_direct': 47, 'missing': 1}; missing dates ['2026-06-17'].

## July-only model selection -> frozen August test
|tier|July-selected model|cut|July watch|July recall|July precision|Aug watch|Aug recall|Aug precision|
|---:|---|---:|---:|---:|---:|---:|---:|---:|
|10%|base+prior_ex|0.147502|478 (10.0%)|74.7%|13.6%|507 (10.6%)|80.9%|17.6%|
|8%|base+prior_ex|0.280323|382 (8.0%)|69.0%|15.7%|421 (8.8%)|77.3%|20.2%|
|7%|base+all_audited|0.424000|334 (7.0%)|66.7%|17.4%|418 (8.8%)|75.5%|19.9%|

### All feature-set diagnostics (August is report-only, never used for selection)
|model|tier|July recall|July watch|Aug recall|Aug watch|selected on July|
|---|---:|---:|---:|---:|---:|---|
|base|10%|71.3%|10.0%|81.8%|10.9%||
|base|8%|65.5%|8.0%|78.2%|8.7%||
|base|7%|63.2%|7.0%|73.6%|7.7%||
|base+tactics|10%|70.1%|10.0%|82.7%|12.5%||
|base+tactics|8%|67.8%|8.0%|80.0%|10.5%||
|base+tactics|7%|63.2%|7.0%|74.5%|9.3%||
|base+prior_ex|10%|74.7%|10.0%|80.9%|10.6%|YES|
|base+prior_ex|8%|69.0%|8.0%|77.3%|8.8%|YES|
|base+prior_ex|7%|65.5%|7.0%|74.5%|8.0%||
|base+all_audited|10%|72.4%|10.0%|81.8%|12.0%||
|base+all_audited|8%|67.8%|8.0%|78.2%|9.6%||
|base+all_audited|7%|66.7%|7.0%|75.5%|8.8%|YES|

## August untouched operational replay — BoatraceCSV od3 only

¥10,000/race, inverse-odds Dutch, 100-yen units. Same source/method for every row.

|PRE rule|settled R|Top10 hit|avg composite|cost|return|ROI|zero-stake-ticket races|
|---|---:|---:|---:|---:|---:|---:|---:|
|v191_cut_0.072608|93|32.3%|3.739|¥930,000|¥909,810|**97.8%**|0|
|v207_10pct_base+prior_ex|88|33.0%|3.687|¥880,000|¥837,090|**95.1%**|0|
|v207_8pct_base+prior_ex|84|34.5%|3.604|¥840,000|¥837,090|**99.7%**|0|
|v207_7pct_base+all_audited|82|34.1%|3.660|¥820,000|¥800,850|**97.7%**|0|

## PICK UP subset inside each PRE rule
|PRE rule|PICK UP R|hit|ROI|
|---|---:|---:|---:|
|v191_cut_0.072608|9|22.2%|76.4%|
|v207_10pct_base+prior_ex|9|22.2%|76.4%|
|v207_8pct_base+prior_ex|9|22.2%|76.4%|
|v207_7pct_base+all_audited|9|22.2%|76.4%|

## Decision rule
- Feature-set choice and cut are locked using July only. August is untouched evaluation only.
- A better August number is not enough to production-adopt; this remains SHADOW until an additional future period confirms it.
- Do not compare these od3 ROI values directly with official-closing-odds v202/v205 as if they had the same odds provenance.
