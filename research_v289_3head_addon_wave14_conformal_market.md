# v289 3号艇 add-on — Wave 14 conformal market gating

- v288 **94R fixed**, final NO_BET only
- deterministic pre-deadline market-structure ticket choice, then conformal selective gating
- prior-month-only walk-forward Feb-Aug; chronological fit/calibration split
- exact 10,000-yen Dutch; required current feature missing => fail closed
- Jul/Aug NON-PRISTINE; September outcomes unused

## Methods
|method|alpha|R|hits|hit rate|ROI|profit|min month|red|max DD|overlap|combined R|combined ROI|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|conformal_market_density|0.05|99|4|4.04%|33.74%|-656,020|0.00%|4|673,920|0|193|101.35%|
|conformal_market_density|0.10|99|4|4.04%|33.74%|-656,020|0.00%|4|673,920|0|193|101.35%|
|conformal_market_efficiency|0.05|99|4|4.04%|33.74%|-656,020|0.00%|4|673,920|0|193|101.35%|
|conformal_market_efficiency|0.10|99|4|4.04%|33.74%|-656,020|0.00%|4|673,920|0|193|101.35%|
|conformal_market_density|0.30|60|1|1.67%|13.44%|-519,360|0.00%|5|530,000|0|154|110.57%|
|conformal_market_efficiency|0.30|60|1|1.67%|13.44%|-519,360|0.00%|5|530,000|0|154|110.57%|
|conformal_market_density|0.20|69|1|1.45%|11.69%|-609,360|0.00%|5|620,000|0|163|104.46%|
|conformal_market_efficiency|0.20|69|1|1.45%|11.69%|-609,360|0.00%|5|620,000|0|163|104.46%|

## Decision
**NO_ADOPTION_WAVE14**
