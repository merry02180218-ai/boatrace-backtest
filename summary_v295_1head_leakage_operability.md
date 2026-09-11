# v295 1HEAD leakage + operability audit

- Research only. v294 is NOT production-approved by this audit.
- Jul/Aug are not used for selection/evaluation; September outcomes are not read.
- The suspicious v294 99% tail is decomposed by source family and month.

## 1. Historical race-card slot leakage audit

For explicit day labels (day1..day7), a true pre-race snapshot must have no values in the current-day or future-day meeting slots.

|month|labelled R|current/future nonempty|current result|current ST|future day|
|---|---:|---:|---:|---:|---:|
|2026-02|0|0|0|0|0|
|2026-03|0|0|0|0|0|
|2026-04|0|0|0|0|0|
|2026-05|3146|1029|1029|1029|0|
|2026-06|2880|0|0|0|0|

- Total structurally contaminated rows: **1029**.

## 2. Ablation feature counts
|variant|features|
|---|---:|
|HGB_STATIC6|83|
|HGB_STATIC9|125|
|HGB_STATIC9_PLAYER|196|
|HGB_FULL_PRE|524|

## 3. Monthly OOF-tail precision

OOF_q selectors are preferred for diagnosis because a global p_cal cutoff can disappear in a later month.

|variant|month|selector|R|head rate|cut|
|---|---|---|---:|---:|---:|
|HGB_FULL_PRE|2026-02|OOF_q0.900|350|99.43%|0.9756|
|HGB_FULL_PRE|2026-02|OOF_q0.950|41|100.00%|0.9872|
|HGB_FULL_PRE|2026-02|OOF_q0.975|1|100.00%|0.9902|
|HGB_FULL_PRE|2026-03|OOF_q0.900|402|99.75%|0.9774|
|HGB_FULL_PRE|2026-03|OOF_q0.950|238|99.58%|0.9881|
|HGB_FULL_PRE|2026-03|OOF_q0.975|114|100.00%|0.9906|
|HGB_FULL_PRE|2026-04|OOF_q0.900|404|99.50%|0.9782|
|HGB_FULL_PRE|2026-04|OOF_q0.950|131|100.00%|0.9900|
|HGB_FULL_PRE|2026-04|OOF_q0.975|4|100.00%|0.9922|
|HGB_FULL_PRE|2026-05|OOF_q0.900|220|93.18%|0.9741|
|HGB_FULL_PRE|2026-05|OOF_q0.950|73|97.26%|0.9875|
|HGB_FULL_PRE|2026-05|OOF_q0.975|13|100.00%|0.9898|
|HGB_FULL_PRE|2026-06|OOF_q0.900|48|77.08%|0.9251|
|HGB_FULL_PRE|2026-06|OOF_q0.950|1|100.00%|0.9561|
|HGB_FULL_PRE|2026-06|OOF_q0.975|0|-|0.9618|
|HGB_STATIC6|2026-02|OOF_q0.900|211|76.30%|0.7550|
|HGB_STATIC6|2026-02|OOF_q0.950|68|83.82%|0.7879|
|HGB_STATIC6|2026-02|OOF_q0.975|27|88.89%|0.8114|
|HGB_STATIC6|2026-03|OOF_q0.900|344|81.10%|0.7568|
|HGB_STATIC6|2026-03|OOF_q0.950|130|81.54%|0.7901|
|HGB_STATIC6|2026-03|OOF_q0.975|56|87.50%|0.8132|
|HGB_STATIC6|2026-04|OOF_q0.900|398|82.16%|0.7515|
|HGB_STATIC6|2026-04|OOF_q0.950|163|84.66%|0.7833|
|HGB_STATIC6|2026-04|OOF_q0.975|62|88.71%|0.8081|
|HGB_STATIC6|2026-05|OOF_q0.900|388|78.35%|0.7547|
|HGB_STATIC6|2026-05|OOF_q0.950|138|82.61%|0.7856|
|HGB_STATIC6|2026-05|OOF_q0.975|40|92.50%|0.8091|
|HGB_STATIC6|2026-06|OOF_q0.900|466|78.97%|0.7544|
|HGB_STATIC6|2026-06|OOF_q0.950|210|81.90%|0.7841|
|HGB_STATIC6|2026-06|OOF_q0.975|99|82.83%|0.8062|
|HGB_STATIC9|2026-02|OOF_q0.900|355|99.44%|0.9803|
|HGB_STATIC9|2026-02|OOF_q0.950|11|100.00%|0.9913|
|HGB_STATIC9|2026-02|OOF_q0.975|0|-|0.9936|
|HGB_STATIC9|2026-03|OOF_q0.900|421|99.29%|0.9796|
|HGB_STATIC9|2026-03|OOF_q0.950|309|99.68%|0.9911|
|HGB_STATIC9|2026-03|OOF_q0.975|255|100.00%|0.9930|
|HGB_STATIC9|2026-04|OOF_q0.900|438|99.32%|0.9796|
|HGB_STATIC9|2026-04|OOF_q0.950|271|100.00%|0.9923|
|HGB_STATIC9|2026-04|OOF_q0.975|158|100.00%|0.9946|
|HGB_STATIC9|2026-05|OOF_q0.900|223|92.38%|0.9750|
|HGB_STATIC9|2026-05|OOF_q0.950|80|95.00%|0.9898|
|HGB_STATIC9|2026-05|OOF_q0.975|6|100.00%|0.9927|
|HGB_STATIC9|2026-06|OOF_q0.900|75|76.00%|0.9176|
|HGB_STATIC9|2026-06|OOF_q0.950|0|-|0.9551|
|HGB_STATIC9|2026-06|OOF_q0.975|0|-|0.9627|
|HGB_STATIC9_PLAYER|2026-02|OOF_q0.900|347|99.42%|0.9780|
|HGB_STATIC9_PLAYER|2026-02|OOF_q0.950|120|100.00%|0.9883|
|HGB_STATIC9_PLAYER|2026-02|OOF_q0.975|33|100.00%|0.9908|
|HGB_STATIC9_PLAYER|2026-03|OOF_q0.900|390|99.49%|0.9787|
|HGB_STATIC9_PLAYER|2026-03|OOF_q0.950|197|100.00%|0.9894|
|HGB_STATIC9_PLAYER|2026-03|OOF_q0.975|62|100.00%|0.9918|
|HGB_STATIC9_PLAYER|2026-04|OOF_q0.900|420|99.29%|0.9794|
|HGB_STATIC9_PLAYER|2026-04|OOF_q0.950|202|100.00%|0.9909|
|HGB_STATIC9_PLAYER|2026-04|OOF_q0.975|92|100.00%|0.9930|
|HGB_STATIC9_PLAYER|2026-05|OOF_q0.900|213|94.37%|0.9753|
|HGB_STATIC9_PLAYER|2026-05|OOF_q0.950|94|97.87%|0.9884|
|HGB_STATIC9_PLAYER|2026-05|OOF_q0.975|41|97.56%|0.9909|
|HGB_STATIC9_PLAYER|2026-06|OOF_q0.900|31|77.42%|0.9269|
|HGB_STATIC9_PLAYER|2026-06|OOF_q0.950|0|-|0.9584|
|HGB_STATIC9_PLAYER|2026-06|OOF_q0.975|0|-|0.9645|

## 4. Top univariate signals
|feature|coverage|direction-free AUC|mean head|mean loss|
|---|---:|---:|---:|---:|
|rel_meet_win_1vavg|100.0%|0.8161|0.1799|-0.0728|
|rel_meet_win_1vbest|100.0%|0.7981|-0.0065|-0.3468|
|attack23_meet_win|100.0%|0.7854|-0.1108|0.2017|
|b1_meet_win|100.0%|0.7848|0.3122|0.0928|
|rel_meet_win_1v2|100.0%|0.7666|0.1808|-0.0902|
|rel_meet_win_1v3|100.0%|0.7651|0.1790|-0.0901|
|rel_meet_win_1v4|100.0%|0.7540|0.1799|-0.0763|
|rel_meet_win_1v5|100.0%|0.7422|0.1805|-0.0592|
|rel_meet_win_1v6|100.0%|0.7262|0.1792|-0.0479|
|rel_meet_p2_1vavg|100.0%|0.7084|0.1771|-0.0265|
|rel_meet_p2_1vbest|100.0%|0.6944|-0.1116|-0.3484|
|b1_meet_p2|100.0%|0.6882|0.4718|0.2860|
|rel_wr_1vbest|100.0%|0.6845|-0.1013|-0.2506|
|attack23_meet_p2|100.0%|0.6785|-0.0324|0.1856|
|b1_wr|100.0%|0.6740|0.5750|0.4445|
|rel_wr_1vavg|100.0%|0.6720|0.1244|-0.0020|
|b1_pl_all_win|100.0%|0.6703|0.1739|0.1318|
|rel_pl_all_p2_1vbest|100.0%|0.6690|-0.0557|-0.1250|
|rel_pl_all_win_1vavg|100.0%|0.6683|0.0382|-0.0039|
|rel_pl_all_win_1vbest|100.0%|0.6674|-0.0423|-0.0924|
|rel_meet_p2_1v3|100.0%|0.6668|0.1636|-0.0455|
|b1_pl_all_p2|100.0%|0.6661|0.3317|0.2724|
|rel_meet_p2_1v4|100.0%|0.6638|0.1765|-0.0362|
|attack23_wr|100.0%|0.6627|-0.0043|0.1389|
|rel_meet_p2_1v2|100.0%|0.6604|0.1559|-0.0459|
|rel_pl_all_p2_1vavg|100.0%|0.6602|0.0579|-0.0008|
|rel_pl_frame_win_1vavg|100.0%|0.6597|0.3748|0.2850|
|rel_grade_1vbest|100.0%|0.6595|-0.1232|-0.3080|
|rel_grade_1vavg|100.0%|0.6582|0.1461|0.0009|
|rel_pl_frame_win_1vbest|100.0%|0.6573|0.2875|0.1937|

## 5. Operability assessment

- `HGB_STATIC6`: immediately reproducible from the morning race-card only; no stateful preview history is required.
- `HGB_STATIC9`: also morning-available if the meeting-slot audit is clean; it adds prior-meeting ST/results from the race-card.
- `HGB_STATIC9_PLAYER`: operationally reproducible, but requires a maintained prior-day player-result state.
- `HGB_FULL_PRE`: operationally reproducible only with maintained prior-exhibition state (`tkz/original exhibition`). It is more complex and must not be promoted if simpler families retain the precision.
- A fixed `p_cal>=0.98` rule is operationally rejected if it fails to produce selections every evaluation month. Prefer a frozen OOF-derived policy with explicit no-bet behavior and minimum monthly volume.
- Production adoption requires a result-blind live scorer, immutable model artifact, source-availability checks, and prospective September logging before outcomes are inspected.

## Decision rule
- If current/future slot leakage is nonzero, discard any family using meeting-slot features and rebuild.
- If only FULL_PRE creates the extreme tail, treat v294 as complexity-sensitive and require an independent prospective replay before use.
- If STATIC6/STATIC9 also retain >=90% monthly tail precision with useful R, prioritize the simplest reproducible family for production.
