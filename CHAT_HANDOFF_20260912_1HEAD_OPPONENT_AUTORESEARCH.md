# CHAT_HANDOFF_20260912_1HEAD_OPPONENT_AUTORESEARCH

## Fixed rules
1号艇頭モデルv308を固定し、相手選び SECOND / THIRD / ordered-pair / exact-3-ticket を自動研究する。最新GitHub優先。
- Fixed cohort **345 races**, boat1 head hits **290/345=84.06%**. Boat1 losses remain misses in exact denominator.
- Jul/Aug 2026 **NON-PRISTINE**; September outcomes **unread/outcome-blind**.
- `meet_*` forbidden unless separately causal-audited. No same/later-race result, end-of-day aggregate, post-race exhibition, payout/result or future-contaminated predictor.
- Month M trains only before M. Missing p3/p4 never future-backfilled.
- Every opponent experiment asserts **345R / 290 head hits**.

## v313 cache-first mandatory
Use committed causal cache only; do not silently rebuild heavy history:
- `cache_v313_1head_opponent_pre.csv.gz` 35,462 rows / 580 cols
- `cache_v313_1head_opponent_p3.csv.gz` 21,692 races
- `cache_v313_1head_opponent_p4.csv.gz` 22,271 races
- manifest `CACHE_V313_1HEAD_OPPONENT_CAUSAL.md`, commit `326b9a3c73af383b31ed799fa00f7e762cce9988`.

## Benchmarks and completed SECOND research
v309 clean base: exact3 **132/345=38.26%**, SECOND TOP2 **71.72%**, conditional THIRD TOP2 **72.76%**. SECOND TOP2 by actual boat: 2=98.25, 3=84.27, 4=35.71, 5=18.75, 6=0%. Main bottleneck was outer SECOND.

v310 causal p3/p4: best SECOND TOP2 72.07%, exact3 133/345; small auxiliary gain.

v311 DROP_START: SECOND TOP2 72.41%, outer456 26.44%, exact3 136/345=39.42%, worst month 60%; development-only.

v312 outer gate, result `6d7a2a31d079547885b68cfece3a1a2de22f1211`: SECOND TOP2 **73.10%**, outer456 **28.74%**, exact3 136/345. Boat4 improved to 47.62%, boat5 15.62%, boat6 0%; sparse/unstable.

v314 role split, result `d07beaa35c8bd4f62beb391e1cc877189cc34d21`: boat TOP2 2=94.74,3=75.28,4=45.24,5=25.00,6=7.69%; sacrificed inner boats, unstable, no promotion.

v315 pairwise, result `2419b4e2887b47a6d64f9a4e2339ce1c15b760e1`: SECOND TOP2 72.76%, outer 27.59%, exact3 133/345; weak.

v316 multiclass, result `56fa0eba373f9a512ce68634beaaf91346add9d7`: SECOND TOP2 72.76%, outer 27.59%, exact3 136/345, worst month 66.67%; stable but weak, 5/6 unresolved.

v317 error-driven causal features: best OUTER_L2_1 SECOND TOP2 **72.76%**, outer456 **28.74%**, exact3 **137/345=39.71%**, worst month 66.67%. SECOND declared sufficiently saturated.

## v318 completed — conditional THIRD rebuild
Summary `summary_v318_1head_opponent_third_rebuild.md`; result commit `39f84acadb9dc03fe68dba427795485e93548bba`.
- Frozen **345R / 290 head hits** confirmed.
- SECOND fixed to v317 OUTER_L2_1.
- Baseline THIRD TOP2 **72.76%**, exact3 **137/345=39.71%**.
- Best **DROPSTART_T0.1**: THIRD TOP2 **72.76%**, TOP1 **40.34%**, TOP3 **92.07%**, exact3 **137/345=39.71%**, worst-month THIRD TOP2 **68.32%**.
- Monthly THIRD TOP2: Feb 74.51, Mar 73.33, Apr 83.33, May 68.32, Jun 70.67%.
Decision: no material THIRD gain. Per automatic branch rules, move to direct 20 ordered `(second,third)` pair modeling.

## v319 completed — direct ordered-pair model
Files:
- `run_v319_1head_opponent_ordered_pair.py`
- `.github/workflows/research-20260913-v319-ordered-pair.yml`
Implementation commit **`38da1f80650533866e34a58eb61bc9342459e87c`**; workflow commit **`f0534370337e8ad292a2d1dd4c23ae08d25d920e`**; grouping fix **`e7626463c00bd923be319c0c680f42d306726e54`**.

Initial run **`34731843060`** failed because `train_group==1` reduced each 20-pair race to the actual-SECOND 4-row block. This was fixed by using that flag only to identify eligible valid 1-x-y race codes and then restoring all 20 ordered-pair rows, with fail-closed 20-row/one-positive assertions.

Restart run **`34733175916`** completed successfully.
- Fixed **345R / 290 head hits** confirmed.
- Best **ALL_P0.3**: pair TOP1 **21.38%**, TOP2 **34.14%**, TOP3 **46.21%**, TOP5 **60.69%**.
- exact3 **134/345=38.84%**; worst-month pair TOP3 **36.00%**.
- Monthly pair TOP3: Feb 45.10, Mar 46.67, Apr 58.33, May 48.51, Jun 36.00%.
- Factorized v317 SECOND + v318 THIRD reference remains stronger at **137/345=39.71%**.
Decision: direct ordered-pair did not materially improve and is not retained as ranking reference. Keep factorized v317+v318 and move to exact-3-ticket policy optimization.

## v320 completed — exact-3-ticket policy optimization
Files:
- `run_v320_1head_exact3_ticket_policy.py`
- `.github/workflows/research-20260913-v320-exact3-ticket.yml`
Implementation commit **`b54ec0574380e42b24c778aaff8e0295b0efe6b9`**; workflow commit **`2c0745d75322cb52080f8d910fce5fe797c555c5`**; result commit **`76ce4ce563c8e73a57b71f7ac687057ba5807a19`**.

Actions run **`34737004683`** completed successfully and committed `summary_v320_1head_exact3_ticket_policy.md`.
- Frozen **345R / 290 head hits** confirmed; exactly 3 tickets on every race, no denominator shrinkage.
- Ranking reference remained factorized **v317 OUTER SECOND + v318 DROPSTART_T0.1 THIRD**.
- Baseline `TOP2XTOP2 alpha=.60`: **137/345=39.71%**, worst month **33.33%**.
- Best development policy `HYBRID alpha=.70`: **139/345=40.29%**, delta **+0.58pt**, worst month **34.78%**.
- Monthly best: Feb 34.92%, Mar 50.00%, Apr 52.83%, May 40.50%, Jun 34.78%.
- Jul/Aug were not evaluated as pristine and September outcomes remained unread.
Decision: freeze **HYBRID alpha=.70** as the current development winner for ticket ordering, but treat the +2-hit gain as development evidence only, not prospective validation. Do not continue ticket-order micro-tuning without a new causal hypothesis.

## Automatic branch sequence
1. SECOND family/gating/role/pairwise/multiclass/error-feature research v311-v317 — completed; saturated.
2. v318 conditional THIRD rebuild — completed, flat.
3. v319 direct 20 ordered `(second,third)` pair model — completed; **134/345**, weaker than factorized **137/345**.
4. Factorized v317+v318 retained as stronger ranking reference.
5. v320 exactly-3-ticket policy optimization — completed; development best **HYBRID alpha=.70, 139/345=40.29%**.
6. Current state is an intentional research boundary: freeze the development winner and wait for genuinely prospective evidence or an explicitly defined new causal hypothesis. Do not invent another micro-tuning branch from reused Feb-Jun outcomes.
7. Suspicious large gain -> immediate leakage/causal audit.

## Required metrics
- exact3 on full 345 denominator
- SECOND TOP1/TOP2/TOP3 when factorized branch is evaluated
- conditional THIRD TOP1/TOP2/TOP3 when factorized branch is evaluated
- direct pair TOP1/TOP2/TOP3/TOP5 for ordered-pair branch
- exact-3-ticket policy full-cohort hits/rate, monthly breakdown and worst month
- delta vs clean/factorized reference.

## Self-continuing rule
A failed/flat experiment is diagnostic evidence, not a stopping condition. If research is stopped and the next leak-safe branch is clear, implement/start it automatically and update this handoff. Do not merely report stopped state. For any new workflow, verify an actual Actions run ID and status after creation. v320 is complete and the defined branch sequence has reached its intentional boundary; do not start another ticket-order micro-tune unless a new causal hypothesis is explicitly defined. Keep Jul/Aug NON-PRISTINE and September outcomes unread.