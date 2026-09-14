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

## 2026-09-15 JST — Wave49 BEFORE WORK
- User approved proceeding from the Wave48 diagnosis.
- Objective: build a genuinely new pre-deadline 3-head selection test around the structure `boat3 vs boat2 motor edge + boat2 wall strength + relative ST`, rather than a post-hoc single cutoff on June.
- Preserve v288 production unchanged and keep Wave36 opponent Top5 logic frozen for the first head-layer test unless the experiment explicitly separates a second opponent-layer diagnostic.
- Do not tune any threshold from Apr-Jun outcomes. Apr-Jun may be used only as already-open diagnostic reference; Jul/Aug remain NON-PRISTINE; September outcomes remain unread.
- Prefer parameterization learned from earlier untouched/training periods (Feb -> March OOS) and evaluate March first. Any Apr-Jun readout must be labeled contaminated/diagnostic only, not adoption evidence.
- Required reporting: exact feature construction, March sample/head-rate/Top5 capture and chronological halves, any comparator versus Wave47/Wave36, exact Run/Job/Artifact IDs if CI is used, commit SHAs, and a strict adoption status.
- Status: `WAVE49_STARTED_BOAT3_VS_BOAT2_MOTOR_WALL_STRUCTURE`.

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

## Exact restart point
1. Preserve Wave48 diagnosis and Wave47 as the stronger research comparator; keep v288 production unchanged.
2. Next experiment should avoid another generic blended classifier. Test an explicit conditional structure such as strong/medium/weak 3-vs-2 motor-edge regimes combined with frozen opponent behavior, with all cut definitions derived without Apr-Jun outcome fitting.
3. March can only be treated as repeated research/OOS evidence now; Apr-Jun contaminated for this line, Jul/Aug NON-PRISTINE, September outcomes unread. Any future adoption requires a genuinely untouched period.
