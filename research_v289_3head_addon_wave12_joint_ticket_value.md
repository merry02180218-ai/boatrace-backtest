# v289 3号艇 add-on — Wave 12 joint ticket-value policy

- v288 **94R fixed**, final NO_BET only
- learned race+ticket expected value across Top2..Top10 / target-composite-odds configurations
- chooses at most one exact-10,000-yen-Dutch ticket structure per race
- prior-month-only walk-forward Feb-Aug; current required feature missing => fail closed
- Jul/Aug NON-PRISTINE; September outcomes unused

## Methods
|method|frac|R|hits|hit rate|ROI|profit|min month|red|max DD|overlap|combined R|combined ROI|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|joint_ticket_value_rf|0.40|75|21|28.00%|65.73%|-257,010|0.00%|7|281,230|0|169|125.15%|
|joint_ticket_value_rf|0.25|47|11|23.40%|57.14%|-201,450|0.00%|6|236,730|0|141|134.09%|
|joint_ticket_value_rf|0.15|11|2|18.18%|52.11%|-52,680|0.00%|6|61,940|0|105|159.94%|

## Decision
**NO_ADOPTION_WAVE12**
