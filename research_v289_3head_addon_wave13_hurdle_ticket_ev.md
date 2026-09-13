# v289 3号艇 add-on — Wave 13 hurdle ticket EV

- v288 **94R fixed**, final NO_BET only
- new candidate generator: P(ticket hit) × conditional payout, with independent direct-value agreement
- exact 10,000-yen Dutch; prior-month-only walk-forward Feb-Aug
- required current feature missing => fail closed
- Jul/Aug NON-PRISTINE; September outcomes unused

## Methods
|method|frac|R|hits|hit rate|ROI|profit|min month|red|max DD|overlap|combined R|combined ROI|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|hurdle_ticket_ev_consensus|0.40|4|1|25.00%|58.65%|-16,540|0.00%|2|20,000|0|98|167.91%|
|hurdle_ticket_ev_consensus|0.30|2|0|0.00%|0.00%|-20,000|0.00%|2|20,000|0|96|168.97%|
|hurdle_ticket_ev_consensus|0.10|1|0|0.00%|0.00%|-10,000|0.00%|1|10,000|0|95|170.74%|
|hurdle_ticket_ev_consensus|0.20|1|0|0.00%|0.00%|-10,000|0.00%|1|10,000|0|95|170.74%|

## Decision
**NO_ADOPTION_WAVE13**
