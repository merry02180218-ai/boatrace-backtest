# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## READ THIS FIRST — authoritative current 1-head state
Latest GitHub wins over old chat memory and stale handoff text.

Mandatory pattern: **handoff update -> work -> result append -> next work handoff update**.
Before every work unit/code change/restart record: current position, exact next work, success criteria, failure fallback. After every work unit record: actual work, commit SHA(s), Actions Run ID/status, metrics/results, exact next resume point.

---

# 1. Frozen production stack — DO NOT ALTER
- HEAD v308
- SECOND v317 `OUTER_L2_1`
- THIRD v318 `DROPSTART_T0.1`
- 3-ticket policy v320 `HYBRID alpha=.70`
- exactly 3 trifecta tickets per selected race
- composite odds = `1 / (1/o1 + 1/o2 + 1/o3)`

Frozen regression: **345 selected / 290 boat1 wins / 139 exact3**.
v308: q=.980, opponent mass >=.375, head cutoff 0.8073405637.

Guardrails:
- Jul/Aug 2026 = NON-PRISTINE/reference-only; never tune/promote on them.
- September outcomes = UNREAD.
- no same/later-race result, payout, future/backfill contamination.
- month M trains strictly on `<M`.
- same-race exhibition is post-PRE only.
- missing current exhibition inputs fail closed for any feature that requires them.
- do not modify v308/v317/v318/v320/v323.

---

# 2. Important completed work

v321 Jul/Aug reference: Run 34750719803, 55R / 45 head / 21 exact3.
v322 composite odds: Run 34753932483 success; no BUY cutoff promoted.
v323 production adapter: Run 34757079269 success; frozen 345/290/139 preserved; September unread.
v324 corrected odds audit: Run 34762939723 success; composite >=3.0 unsupported.

Exhibition source audit:
- tkz `data/previews/tkz/YYYY/MM/DD.csv`
- stt `data/previews/stt/YYYY/MM/DD.csv`
- original `data/previews/original_exhibition/YYYY/MM/DD.csv`
- audited transform `backtest_v51_lane_corrected_tickets.py::corrected_direct`
- ST lane bias uses prior days only.
- neutral 0.5 defaults cannot be treated as proof that a raw metric existed.

---

# 3. Work Unit 5B — v325 boat1-only exhibition postfilter — COMPLETE / NOT PROMOTED

Commits/runs:
- c971d14dac4ebd1bea5f0b73535bd74b7cfe242b — initial script
- d395c77dfdf2b83335b006f85046ec13f507da94 — workflow
- Run 34764216379 exposed missing-source eligibility issue
- 3c4a21e184b1ec0e9e4220a412ed600a4130b810 — failure recorded before correction
- 68bf07bbd783c7082d6e21dd1917c01e1da3800e — fail-closed correction
- corrected Run **34764329333** success, job 103742497228, artifact 10319838860

Final v325:
- 345R / 139 exact3 / 290 head
- frozen `one_turn >= 0.800000`
- Feb-Apr 13/33=39.39%
- May 17/35=48.57%
- Jun PASS 8/25=32.00%; SKIP 24/67=35.82%; baseline 32/92=34.78%
- FORWARD_SUPPORTED=False
- Jul/Aug not opened for v325.

---

# 4. Work Unit 5C — v326 ticket-aware exhibition postfilter — COMPLETE / NOT PROMOTED

Purpose: compare exhibition quality of SECOND/THIRD boats actually covered by the frozen v320 tickets against uncovered opponents.

Implementation/workflow:
- `ee2ca7b155b9a2e1d4559c4e98210bc6cc5d9b55` — initial v326 script
- `64433735827c63971badaff7be2652c8a25586e2` — workflow
- first Run **34766023220** failed `KeyError: 6`; recorded before fix in `27655a5830841815ac38f02723419996713d6f`.
- strict correction `bfeba1b91f5a2b7314ad0de819c81e0c7d934df3`; Run **34766151983** success.
- semantic readiness audit recorded `7fe36555e2a7657957a67235275ead76360880b7`.
- feature-specific readiness correction `749d298354f46e2bfa5e8e8e7e19c2f9fd6211cf`.

Final v326 Actions:
- Run **34766426083** SUCCESS, job **103748102108**, artifact **10320837179**.
- 345R / 139 exact3 / 290 head unchanged.
- frozen `sec_st_mean_margin <= -0.600000`.
- discovery 8/22=36.36%; May 14/29=48.28%; June PASS 8/25=32.00%; June baseline 32/92=34.78%.
- FORWARD_SUPPORTED=False.
- Jul/Aug unopened for v326; September unread.

---

# 5. Work Unit 5D — v327 PRE-confidence + exhibition source audit — COMPLETE

Safe PRE confidence sources audited:
- v308 race-level `p_head`, `opp_mass`.
- v317 causal SECOND `p2[boat]`.
- v318 causal conditional THIRD `pc[(second,third)]`.
- v320 causal pair probabilities and frozen HYBRID ordering.
- v323 reproduces same live sequence before settlement.

Frozen v327 PRE feature set:
`p_head`, `opp_mass`, `second_top1_prob`, `second_top2_mass`, `second_margin12`, `third_top1_mean_for_top2_second`, `third_top1_min_for_top2_second`, `ticket_prob1`, `ticket_prob2`, `ticket_prob3`, `ticket_mass3`, `ticket_gap34`, `ticket_entropy20`.

Excluded: odds/composite odds, result/payout before feature freeze, same-race exhibition inside PRE block, Jul/Aug/September outcome-derived fields, `meet_*`, future/backfill.

Source audit + implementation plan commit:
- **`faecfa0245698b8859ea803fad4f51c9de765c2f`**

---

# 6. Work Unit 5E — v327 IMPLEMENTATION — COMPLETE / NOT PROMOTED

Files/commits:
- `run_v327_1head_preconf_exhibition.py`
- implementation commit **`d3869f12d53038d558a3cf73843e4f15a755b016`**
- workflow `.github/workflows/v327-1head-preconf-exhibition.yml`
- workflow commit **`351adaf0b6a76eeff050619caec18f8d28d60fe3`**

Actions:
- Run **34766775614** — SUCCESS
- Job **103749028093** — SUCCESS
- Artifact `v327-1head-preconf-exhibition`
- Artifact ID **10320494086**
- artifact SHA256 `b78274f7af191d3208010f9bce99d8d840c9d0a05298d2b4ccb351ba453c92b9`

Identity/causality:
- exact frozen reconciliation **345 / 290 head / 139 exact3**.
- exact frozen HYBRID ticket strings were asserted during PRE-confidence reconstruction.
- Jul/Aug were not opened for v327.
- September outcomes remain unread.

Frozen v327 candidate from Feb-Apr discovery + May validation:
- kind: `pre_ex`
- PRE: **`opp_mass >= 0.416322574702382`**
- exhibition confirmation: **`third_orig_mean_margin >= -0.37777777777777793`**
- discovery Feb-Apr: **18/42 = 42.86% exact3**, head 34/42=80.95%
- May validation: **28/56 = 50.00% exact3**, head 49/56=87.50%

One-shot June forward check:
- baseline: **32/92 = 34.78% exact3**, head 75/92=81.52%
- PASS: **13/39 = 33.33% exact3**, head 31/39=79.49%
- SKIP: **19/53 = 35.85% exact3**, head 44/53=83.02%
- **FORWARD_SUPPORTED=False**

Conclusion:
- v327 PRE-confidence + exhibition postfilter did NOT generalize chronologically.
- It is NOT promoted.
- The PASS layer actually underperformed June baseline and SKIP group.
- Per predeclared guardrail, do not open Jul/Aug for v327 and do not build production BUY logic from it.
- v325/v326/v327 together show that selective postfiltering is not currently solving the exact3 ceiling robustly.

---

# 7. Work Unit 6A — v328 ticket-selection error audit — COMPLETE

Implementation:
- script `run_v328_1head_ticket_error_audit.py`
- script commit **bab1896a23393f0b564f741cf0332fb20f74922b**
- workflow `.github/workflows/v328-1head-ticket-error-audit.yml`
- workflow commit **9418247f6bc40534881b03586b9019443da45a52**

Actions:
- Run **34767480326** — SUCCESS
- Job **103750928927** — SUCCESS
- Artifact `v328-1head-ticket-error-audit`
- Artifact ID **10321143424**
- artifact SHA256 `ad41a0084632207b45debcb10b52da6bd8e8a2c25386e9cdfa7c83be9b43f89e`

Identity/causality:
- frozen reconciliation **345 selected / 290 head / 139 exact3**.
- Jul/Aug not inspected for v328.
- September outcomes unread.
- p2 / pc / HYBRID alpha=.70 rebuilt causally and frozen top-3 ticket identity verified.

Results by period:

FEB-APR:
- R=132, head=114 (86.36%), exact3=58 (43.94%)
- SECOND top1/top2 on head wins: 45 (39.47%) / 84 (73.68%)
- conditional THIRD top1/top2 on head wins: 50 (43.86%) / 89 (78.07%)
- HYBRID ordered-pair oracle coverage top3/top4/top5/top6: 58 (50.88%) / 65 (57.02%) / 71 (62.28%) / 80 (70.18%)
- misses: HEAD_LOSS 18; SECOND_NOT_COVERED 30; SECOND_COVERED_THIRD_MISS 26

MAY:
- R=121, head=101 (83.47%), exact3=49 (40.50%)
- SECOND top1/top2: 52 (51.49%) / 76 (75.25%)
- conditional THIRD top1/top2: 37 (36.63%) / 69 (68.32%)
- HYBRID top3/top4/top5/top6: 49 (48.51%) / 59 (58.42%) / 67 (66.34%) / 70 (69.31%)
- misses: HEAD_LOSS 20; SECOND_NOT_COVERED 24; SECOND_COVERED_THIRD_MISS 28

JUNE:
- R=92, head=75 (81.52%), exact3=32 (34.78%)
- SECOND top1/top2: 32 (42.67%) / 51 (68.00%)
- conditional THIRD top1/top2: 30 (40.00%) / 53 (70.67%)
- HYBRID top3/top4/top5/top6: 32 (42.67%) / 39 (52.00%) / 41 (54.67%) / 47 (62.67%)
- misses: HEAD_LOSS 17; SECOND_NOT_COVERED 23; SECOND_COVERED_THIRD_MISS 20

ALL:
- R=345, head=290 (84.06%), exact3=139 (40.29%)
- SECOND top1/top2: 129 (44.48%) / 211 (72.76%)
- conditional THIRD top1/top2: 117 (40.34%) / 211 (72.76%)
- HYBRID top3/top4/top5/top6: 139 (47.93%) / 163 (56.21%) / 179 (61.72%) / 197 (67.93%)
- misses: HEAD_LOSS 55 (15.94% of all selected); SECOND_NOT_COVERED 77 (22.32%); SECOND_COVERED_THIRD_MISS 74 (21.45%); HIT 139 (40.29%).

Conclusion:
- no single miss class dominates overwhelmingly; SECOND coverage and THIRD/pair coverage are nearly equally important.
- June deterioration is broad: head rate, SECOND top2, conditional THIRD top2, and HYBRID pair coverage all decline together.
- the 3-ticket allocation ceiling is material: among head-hit races, top3 pair coverage is only 47.93% overall and 42.67% in June, while top6 rises to 67.93% overall and 62.67% in June.
- therefore the next research target should NOT be another narrow PRE-only filter. The next post-v328 work should focus on improving the post-PRE/straight-before-start judgement using richer exhibition logic, and only then revisit ticket allocation if needed.

---

# 8. Next work to perform AFTER reporting v328 to the user
User explicitly requested that each version be reported before proceeding to the next version.

Next direction requested by user:
- rebuild the 1-head final judgement by borrowing the **3-head and 4-head models' pre-race exhibition judgement mechanism** rather than extending v327's simple filter.
- inspect latest GitHub code/handoffs for 3-head and 4-head direct-before-start logic first.
- reproduce their handling of exhibition time, exhibition ST, original exhibition, course/lane adjustment, prior-race adjusted exhibition, and fail-closed availability checks as applicable.
- keep the frozen PRE production stack v308/v317/v318/v320 unchanged; the new logic is a downstream exhibition-stage judgement layer only unless a later predeclared experiment says otherwise.

Success criteria for the next work unit:
- identify the exact current 3-head/4-head direct-before-start scoring architecture from latest GitHub.
- write a source-audited 1-head adaptation plan before code.
- preserve result blindness and all Jul/Aug/September guardrails.

Failure fallback:
- if 3-head and 4-head implementations differ materially, document both and select components only after source/causality audit; do not blend them ad hoc.

---

# 9. Exact next resume point
**STOP here until v328 is reported to the user. After that, audit the latest 3-head and 4-head exhibition-stage judgement implementations and design the 1-head adaptation. Do not start a v329 implementation before that source audit is recorded in this handoff.**
