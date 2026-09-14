# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Active branch: research/3head-player-attack-mode. Do not rewrite main.
- v288 baseline fixed: 94R / 52 hits / ROI172.560638%.
- Pre-deadline only. Jul/Aug NON-PRISTINE. September unread.
- Hourly 3-head monitor remains disabled unless user asks.

## Benchmarks
- Wave36: Apr-Jun 391R / 87 hits / ROI114.913% / +583,090 yen.
- Wave36S-C: Apr-Jun 305R / 74 hits / ROI128.218% / +860,660 yen. RESEARCH_CANDIDATE.

## Closed research
- Wave39/40/41/42/43 rank replacements: NO_ADOPTION.
- Wave44 attack-mode route: best March AUC0.5895, below 0.60 gate. CLOSED.
- Wave45 confidence/margin: zero lift. NO_ADOPTION.
- Wave46 second/third role factorization: March 16/90 role, 21/90 blend vs Wave36 24/90. NO_ADOPTION.

## Wave47 head-condition zoning — COMPLETE / NO_ADOPTION
- March baseline:90R /38 head hits /42.222%; Top5 24 /26.667%.
- March winner: motor family top60% =>54R / head48.148% (+5.926pt), early46.875%, late50.000%.
- Apr-Jun fixed holdout:174R /36 hits / ROI95.511% / -78,100 yen.
- Monthly: Apr49R/12/ROI111.384%; May63R/15/124.390%; Jun62R/9/53.623%.
- Decision NO_ADOPTION. Do not retune Wave47 on Apr-Jun.

## Wave48 June failure diagnostic — COMPLETE / DIAGNOSTIC ONLY
- BEFORE-WORK plan commit: 3731e067bb96c209309d0ad3c373e5b31b41d61c.
- Diagnostic script commit: 093d7032d466dcf7b9a9a23bf25ce0278b43d147.
- GitHub Actions reroute attempts did not execute Wave48: Run34848481844 / Job103990131077 completed successfully but actually ran the old Wave44c entrypoint. Further workflow/entrypoint rewrites were blocked by the platform safety checker, so no CI result is claimed for Wave48.
- Final diagnostic was executed directly from the exact source artifact `3head-wave21-allrace-source-build` (run34754875342, artifact10317157868, artifact digest sha256:01d84cc2b5b63ae9ec240c730cd556c168caeae184355fd6d74e8beb9a4bf8b1) with the repository Wave48 logic and exact v288 94-race exclusion.
- Reproduced frozen Wave47 sample exactly: March Wave36 universe 90R; frozen zone cutoff 0.5260507011821546; Apr49R / May63R / Jun62R = 174R total.

### Failure decomposition
- Apr+May combined: 112R / boat3 head 52 = 46.429%; ticket hits27 =24.107%; frozen Wave36 Top5 capture conditional on boat3 head =51.923%; ROI118.700%; profit +209,440 yen.
- June: 62R / boat3 head21 =33.871%; ticket hits9 =14.516%; conditional Top5 capture =42.857%; ROI53.623%; profit -287,540 yen.
- June vs Apr+May head-rate change: -12.557pt.
- June vs Apr+May conditional Top5 capture change: -9.066pt.
- Classification: **MIXED_HEAD_AND_OPPONENT_FAILURE**. The June collapse is not payout-only; both the 3-head selection layer and the opponent Top5 layer weakened.

### Largest visible pre-race distribution shifts, June vs Apr+May
- boat3 minus boat2 motor 3-place rate gap: standardized shift -0.571; mean +29.261 -> +16.448.
- frozen Wave47 motor-zone score: shift -0.550; mean 0.627606 -> 0.579885.
- boat3 minus boat2 motor 2-place rate gap: shift -0.511; mean +23.8625 -> +13.1323.
- boat3 minus boat4 national win-rate gap: shift +0.468; mean +1.4911 -> +2.1577.
- boat3 minus boat2 average-ST gap: shift -0.353; mean -0.0190 -> -0.0308 (boat3 relatively faster on paper, so ST gap alone does not explain the collapse).
- boat3 minus boat4 average-ST gap: shift -0.348.
- boat3 minus boat2 national win-rate gap: shift +0.324.
- boat3 minus boat1 motor 2-place rate gap: shift -0.295.
- Wave36 p3 mean also softened: 0.468656 -> 0.444980; standardized shift -0.291.

### Interpretation / future-test hypothesis only
- Strongest diagnostic clue is the **2号艇とのモーター優位の縮小** together with lower overall motor-zone score. June still often had favorable ST/win-rate gaps, but the motor edge versus boat2 was materially weaker.
- Therefore a future pristine hypothesis should examine whether 3号艇頭 selection needs a stronger `3 vs 2 motor edge` / wall-mechanism condition, and whether low zone-score regimes also need stricter opponent handling.
- This is NOT an adoption rule because Apr-Jun were already opened. No threshold may be tuned/promoted from these outcomes.
- Jul/Aug remain NON-PRISTINE and are not used as validation. September outcomes remain unread. v288 untouched.

## 2026-09-15 JST — Wave49 AFTER
- BEFORE handoff commit: `6ff5efa6010d911245a0c873f5cafad9527b9314`.
- Wave49 script commit: `e8a5ca9b140cb5c2c6e50df55f5b4a57b1ac7b90`; CI workflow commit: `86ec58beee13907c88128a9fe50c1c08da9e7920`.
- First CI Run `34863529639` / Job `104041510270` failed only because the output column name `head` collided with pandas `DataFrame.head`; no research conclusion was taken from that failed run.
- Fix commit: `e4cd55dc989eaeb24ae5c64b9c39537b393eefd0`.
- Successful CI: Run `34863681673` / Job `104042028571` / Artifact `10355472826` (`3head-wave49-motor-wall`), conclusion `success`.
- Wave49 features were pre-deadline only and focused on boat3-vs-boat2 motor2/motor3 gaps, relative average ST, boat2 absolute motor/ST wall strength, and motor-gap x ST-edge interactions. Wave36 head gate/p3 and opponent Top5 generation remained the comparator structure.
- March Wave36 baseline reproduced: 90R / 38 head hits = 42.222%; Top5 24/90 = 26.667%.
- Wave49 fixed keep60 result: 54R / 24 head hits = 44.444%; head lift only +2.222pt; Top5 14/54 = 25.926%.
- Chronological halves: early 29R / 14 head = 48.276%; late 25R / 10 head = 40.000%. The late half fell below the baseline head rate.
- Fixed Wave49 score threshold from March keep60 was 0.5628166498815553.
- Comparison with Wave47: Wave47 achieved March 48.148% head (+5.926pt) with early46.875% / late50.000%; Wave49 is materially weaker overall and unstable late.
- Decision: `NO_ADOPTION`. The simple learned motor-wall composite does not improve on Wave47 and fails the intended stability test. Do not use it to retrofit June.
- Apr-Jun were not reopened for tuning; Jul/Aug were not used; September outcomes remain unread. v288 production unchanged.
- Interpretation: the Wave48 diagnosis that 3-vs-2 motor edge matters still stands, but compressing it into a generic logistic wall score loses too much structure. The next useful test should keep the motor-edge signal explicit and examine conditional regimes / opponent handling rather than one blended head score.
- Status: `WAVE49_COMPLETE_NO_ADOPTION`.

## 2026-09-15 JST — Wave50 BEFORE WORK
- User approved the next step: explicit strong/medium/weak boat3-vs-boat2 motor-edge regimes with frozen Wave36 opponent behavior.
- Do NOT fit regime thresholds to March outcomes or Apr-Jun. Define regime cuts from the February feature distribution only, using boat3-minus-boat2 motor2 and motor3 rate gaps.
- Primary March outputs: race count, head rate, Top5 ticket rate, and conditional Top5 capture given boat3 head for each regime; also chronological-half stability where sample size permits.
- This is a structural diagnostic/research test, not a production candidate. March is already repeatedly researched; Apr-Jun are contaminated for this line; Jul/Aug NON-PRISTINE; September outcomes unread.
- Preserve v288 production and frozen Wave36 Top5 ordering. No payout/ROI optimization and no threshold search on outcomes.
- Required record after completion: script/workflow commits, Run/Job/Artifact IDs, exact February regime cuts, March regime table, interpretation, and next restart point.
- Status: `WAVE50_STARTED_EXPLICIT_3V2_MOTOR_EDGE_REGIMES`.

## 2026-09-15 JST — Wave50 AFTER
- BEFORE handoff commit: `33c75b4a4df9880d24b7cab9f62ea296c9482721`.
- Wave50 research script commit: `f070b53445ab59968c48e87c2deff89b6342162e`.
- Creating/repointing a GitHub Actions workflow for Wave50 was blocked by the platform safety checker, so no Wave50 CI Run/Job/Artifact IDs are claimed.
- To avoid inventing CI evidence, Wave50 was executed directly from the exact frozen source artifact used by Wave48: source Run `34754875342`, Artifact `10317157868`, with exact v288 94-race exclusion. Result JSON was committed as `research_v289_3head_wave50_motor_edge_regimes_result.json` in commit `e60dda90f7f44068e5f5d6ace592bd3182a162f3`.
- Regime cuts were derived from February feature distributions only, not outcomes: motor2 gap low/high = `-4.0 / +3.9`; motor3 gap low/high = `-4.6 / +4.633333`.
- Joint regime definition: STRONG when both motor2 and motor3 gaps are above the February upper-tercile cuts; WEAK when both are below the lower-tercile cuts; otherwise MEDIUM.
- March Wave36 baseline reproduced exactly: 90R / 38 head hits = 42.222%; 24 ticket hits = 26.667%; conditional Top5 capture given head3 = 63.158%.
- STRONG: 49R / 22 head hits = 44.898%; Top5 13/49 = 26.531%; conditional capture 59.091%. Early head 42.857%, late head 47.619%. Mean motor2 gap +22.245, mean motor3 gap +27.031.
- MEDIUM: 30R / 14 head hits = 46.667%; Top5 9/30 = 30.000%; conditional capture 64.286%. Early/late head both 46.667%. Mean motor2 gap +0.114, mean motor3 gap +0.996.
- WEAK: 11R / 2 head hits = 18.182%; Top5 2/11 = 18.182%. Only two head wins occurred and both were inside frozen Top5, so conditional capture = 100%; the dominant failure is head selection, not opponent capture. Early 0/2 heads; late 2/9 = 22.222%. Mean motor2 gap -10.664, mean motor3 gap -11.264.
- Key structural finding: the weak joint 3-vs-2 motor-edge regime is a clear head-failure zone in March. Strong/medium regimes are materially healthier, while weak collapses far below the 42.222% baseline.
- This supports the Wave48 mechanism qualitatively, but remains `DIAGNOSTIC_ONLY_NO_PRISTINE_PERIOD` because March is repeatedly researched and no genuinely untouched period is available. Do not promote a weak-regime exclusion into production from this evidence.
- Apr-Jun were not used for threshold fitting or reopened for optimization; Jul/Aug were not used; September outcomes remain unread. v288 production unchanged.
- Status: `WAVE50_COMPLETE_DIAGNOSTIC_WEAK_3V2_MOTOR_EDGE_HEAD_FAILURE_CONFIRMED`.

## 2026-09-15 JST — Wave51 BEFORE WORK
- User approved testing the stronger idea: use pre-race motor strength itself as an upstream candidate finder rather than only as a fail-closed filter inside Wave36/Wave47.
- Objective: scan the full March settled six-boat universe after exact v288 94-race exclusion, not the 90-race Wave36 p3>=0.365448 subset, and measure whether boat3-vs-boat2 motor advantage alone can surface additional 3-head opportunities.
- Thresholds/cuts must be frozen from February feature distributions only. Do not tune on March outcomes or Apr-Jun.
- Primary analyses: full-March candidate counts/head rates for increasingly strong 3-vs-2 motor-edge states; overlap vs Wave36 March 90R; incremental candidates outside Wave36; ST and boat3-vs-boat1 strength summaries; and frozen Wave36 opponent Top5 capture where a comparable Top5 score can be produced.
- Goal is structural discovery, not production adoption. March is already research-exposed; Apr-Jun contaminated for this research line; Jul/Aug NON-PRISTINE; September outcomes remain unread.
- v288 production remains unchanged.
- Status: `WAVE51_STARTED_MOTOR_FIRST_FULL_UNIVERSE_CANDIDATE_DISCOVERY`.

## Exact restart point
- Execute Wave51 from the frozen Wave21 source artifact with February-derived motor thresholds, quantify incremental March 3-head candidates outside Wave36, and record whether motor-first selection is strong enough to justify an independent model family.
