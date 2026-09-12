# CHAT HANDOFF — 2026-09-12 FINAL

Repository: `merry02180218-ai/boatrace-backtest`

This is the primary handoff for the next chat. **Always inspect the actual latest GitHub `main` and newest Actions before doing any work. If this file conflicts with a newer commit/result, newer GitHub wins.**

---

# 0. Mandatory rules / source of truth

- Always inspect latest GitHub `main` before predictions, model changes, backtests, audits, or production decisions.
- Never calculate a LIVE prediction from chat memory alone. Use the actual current code and current inputs.
- Never use target-day result, payout, finishing order, or post-deadline information in PRE/LIVE decisions.
- Results/payouts may only be joined after the prediction/tickets are frozen.
- Missing current inputs fail closed. Do not guess/default exhibition, ST, original exhibition, odds, Waku, or other required LIVE inputs.
- July/August 2026 are **NON-PRISTINE**. They have been repeatedly inspected/used in model development.
- Dec2025-Jun2026 has also been used heavily for feature/rule discovery. Treat it as historical/model-selection evidence, not pristine future validation.
- September 2026 is intended as pristine outcome-blind production evidence. Do not tune rules from September outcomes if preserving the holdout.
- Multiple chats may write this repository. Before editing any file, fetch the latest version/SHA again.
- Do not rerun an old failed Actions job expecting it to use newer code; an old rerun generally checks out the old commit. Trigger a new run from latest source when a source fix matters.

## ROI / staking definition

- Exactly ¥10,000 total stake per selected/settled race.
- Dutch allocation inverse to odds.
- 100-yen units, Hamilton/largest-remainder rounding, total exactly ¥10,000.
- Zero-stake tickets are not purchased.
- Composite odds: `O_combined = 1 / sum(1/o_i)`; this is a value feature, not realized ROI.
- Realized ROI = total payout / total settled stake.
- Losing race payout = 0 and profit = -¥10,000.
- Canonical historical rounding reference: `analyze_v205_3head_operational_replay.py::round_dutch`.

---

# 1. Current 3号艇 production lineage: v288

The important current 3-head production lineage in this handoff is **v288**. Older v249/v243/v242 material remains ancestry/context, but do not revert to an older top-level operating description unless the newest GitHub explicitly does so.

## Historical adopted v288 performance under corrected route semantics

- 100 races
- 56 hits
- hit rate 56.00%
- stake ¥1,000,000
- payout ¥1,743,810
- profit +¥743,810
- ROI **174.381%**

## Production-compatible leakage-free PRE replay before September

- 94 races
- 52 hits
- hit rate 55.319%
- stake ¥940,000
- payout ¥1,622,070
- profit +¥682,070
- ROI **172.561%**

Route breakdown:

- S: 55R / 33 hits / ROI 184.062%
- A: 21R / 10 hits / ROI 149.162%
- B: 18R / 9 hits / ROI 164.717%

Proof:

- run `34560827602`
- marker `V288_OPERATIONAL_PRE_REPLAY_OK`

LIVE route parity:

- run `34560454539`
- marker `V288_LIVE_ROUTE_PARITY_OK cases=32`

## v288 corrected route semantics

Precedence: **S -> A -> B -> NO_BET**.

### S route

Requires v243 pass plus:

- `c_b3_minus_b4_waku_st <= 0.4999999999999999`
- `c_b3_minus_b4_st >= -0.6`
- `c_b3_meetst <= 0.861111111111111`

### A route

Independent rescue; **does not require v243 pass**. Requires PRE S+A and v242 buyable plus:

- `c_b3_minus_b4_st >= 0.6`
- `c_wall12_weak <= 0.24875`

### B route

Independent rescue; **does not require v243 pass**. Requires PRE S+A and v242 buyable plus:

- `c_b3_minus_b2_motor >= 0.22388571428571424`
- `c_b3_inside_nst <= -0.0714285714285712`

## September production freeze

History cutoff:

- `2026-08-31`

Score thresholds:

- S 70th percentile = `3.290592837278`
- A 20th percentile = `-4.79847489663985`

Do not compute thresholds from the current day/month.

---

# 2. PRE / Waku10 input policy

Current policy:

1. Primary current-day PRE Waku10-equivalent source: Kyoteibiyori.
2. If exact row cannot be built, use the historically/overlap-validated direct BOATCAST Waku10 parser/fetch.
3. If both fail, exclude the race.
4. Never invent/default Waku values.

Historical verifier 2026-09-11:

- run `34583558321`
- 144/144 PRE rows
- 132 Kyoteibiyori
- 12 BOATCAST fallback
- 0 excluded

Relevant commits:

- `302ed4978c423cc741aa26f6fd583df2b1ff0e45` — historical direct BOATCAST fallback
- `14ff3b9e79f012abb7d808425feaa8ab30277125` — production Waku fallback
- `642bd2778854c62e8de50f69fc0fa6ebc360dc54` — verifier

Prior production handoff:

- `CHAT_HANDOFF_20260911_3HEAD_V288_PRODUCTION.md`

---

# 3. September pristine production evidence already observed

Sep 1–11 final production-rule retrospective:

- run `34669018555`
- artifact `v288-sep1-11-production-replay-final`
- marker `V288_SEP1_11_REPLAY_OK`
- PRE candidates: 9
- final BET: 2
- hits: 0
- stake ¥20,000
- payout ¥0
- profit -¥20,000
- ROI 0%

Bets:

- 2026-09-06 蒲郡3R — route A — actual 1-3-6
- 2026-09-09 びわこ2R — route S — actual 2-1-6

**Do not tune v288 from these September outcomes if September is being preserved as the pristine holdout.**

---

# 4. June 2026 operational-process replay

Task: full operational-process replay for `2026-06-01..2026-06-30`, with the month frozen to information available through 2026-05-31.

Configuration:

- history cutoff `2026-05-31`
- bias start `2026-05-01`
- S threshold `2.941228852972743`
- A threshold `-4.868019039818082`

Important caveat:

- v288 rules were finalized later. June is an **operational-process replay**, not pristine model-selection evidence.

Key files:

- `build_3head_v288_operational_month_day.py`
- `replay_v288_operational_day.py`
- `prepare_v288_historical_pre_input.py`
- `aggregate_v288_june_operational_repair.py`
- `aggregate_v288_june_liveinput_fixed.py`

Important repair commits:

- `9cda9b2b5f921175f3e8aee8c9493144402c8a2f` — initial June day build
- `470f7a22333931010ecfc9c8db3d1a4f9e59ccfe` — zero-PRE fast path
- `6fd5e8b3b0116da0b2ec50fecdf8cd7b7640f964` — pair nonfinite historical-training guard
- `e5108b938e347e4d532fa40abc6705dbd7682545` — replay helper allowing non-Sep cutoff
- `f379315f084ec76d7a4df78a3484d0014b9342de` — official BOAT RACE racelist fallback
- `5af47ca6588dc7f6d31906590edf74961a5801ea` — parallel Waku recovery
- `7f211595fc2e9b2d8b7df64657e620f2ddb368cb` — June repair aggregator
- `e5dba6b534b9acdb2652347ce1168bb5f39e6a51` — replay June v288 candidates with repaired LIVE inputs
- `eef2b381f7acdf96904818e1afb01d1b93341a0d` — auto-aggregate corrected June LIVE replay
- `868168a86a047e6e553c00e97b6024cb4bf49c5f` — strict 30-day PRE/input-coverage aggregate

---

# 5. June decision-level SOURCE OF TRUTH: repaired LIVE-input replay

The initial June processing made the 18 PRE candidates appear to be all NO_BET. That was **not a valid model conclusion**; historical LIVE-input reconstruction was incomplete.

A repaired LIVE-input replay was then run for the 18 PRE-candidate days using the frozen May-31 model cache and corrected historical LIVE inputs.

Replay workflow:

- `.github/workflows/replay-june-v288-liveinput-fixed.yml`
- run `34689337291`
- all 18 matrix jobs: SUCCESS

Aggregate workflow:

- `.github/workflows/aggregate-june-v288-liveinput-fixed.yml`
- run `34691540904`
- aggregate job `103547539466`
- status SUCCESS
- final artifact `v288-june-liveinput-fixed-final`
- artifact ID `10296859515`
- marker `V288_JUNE_LIVEINPUT_FIXED_OK`

## Correct June decision metrics — use these going forward

- PRE candidates: **18**
- LIVE evaluable: **15**
- input / decision errors: **3**
- genuine NO_BET: **13**
- BET: **2**
- hits: **1**
- hit rate among bets: **50.0%**
- stake: **¥20,000**
- payout: **¥30,720**
- profit: **+¥10,720**
- ROI: **153.60%**
- max drawdown: **¥10,000**

Route result:

- A: 1 bet / 1 hit / stake ¥10,000 / payout ¥30,720 / profit +¥20,720 / ROI 307.2%
- S: 1 bet / 0 hits / stake ¥10,000 / payout ¥0 / profit -¥10,000 / ROI 0%
- B: 0 bets

Daily bets:

- 2026-06-06: S route, miss, -¥10,000
- 2026-06-12: A route, hit, payout ¥30,720, +¥20,720

Gate pass counts among the 15 LIVE-evaluable candidates:

- `v242_buyable`: 12/15
- `v243_pass`: 5/15
- `S_condition`: 4/15
- `A_condition`: 3/15
- `B_condition`: 0/15

Genuine NO_BET reasons:

- `v242_not_buyable`: 3
- `v243_pass_but_S_fail_no_rescue`: 4
- `v243_fail_no_A_or_B_rescue`: 6

Remaining input errors:

1. 2026-06-05 — original exhibition unavailable, BOATCAST 403
2. 2026-06-14 — original exhibition unavailable, BOATCAST 403
3. 2026-06-17 — archived odds incomplete 0/120

Odds caveat:

- Official BOAT RACE closing 3連単 odds archive was used where legacy od3 was unavailable.
- Closing odds are a closing snapshot, not guaranteed exact historical purchase-time fill.
- Decision logic remained result-blind; results/payouts were joined only after decision freeze.

Because there were only **2 actual bets**, ROI 153.6% is positive but statistically weak. Do not claim June alone proves the model.

---

# 6. IMPORTANT: later 30-day aggregate with 0 BET does NOT supersede corrected LIVE replay

A later-timestamp workflow exists:

- commit `868168a86a047e6e553c00e97b6024cb4bf49c5f`
- workflow `.github/workflows/aggregate-june-v288-operational-repair.yml`
- run `34692240958`
- job `103549437550`
- status SUCCESS
- artifact `v288-june-operational-replay-final-repaired`
- artifact ID `10298185378`
- marker `V288_JUNE_30DAY_REPAIR_OK`

It reports:

- PRE candidates 18
- BET 0
- hits 0

**Do not treat that 0-BET output as the final June decision result.** It aggregates the original 29 day artifacts plus the repaired June-17 day artifact, i.e. the pre-LIVE-input-correction operational artifacts. It is useful for strict 30-day PRE/input coverage, but not the corrected decision-level BET/ROI result.

Therefore:

- **PRE/input coverage source:** run `34692240958` is valid/useful.
- **June LIVE decision/BET/ROI source of truth:** run `34691540904` remains authoritative: **18 PRE -> 15 LIVE evaluable -> 13 genuine NO_BET -> 2 BET -> 1 hit -> ROI 153.6%**.

This distinction is critical. A next chat must not choose the later run merely because its timestamp is newer.

---

# 7. June 17 PRE recovery

June 17 originally failed because archived race cards were absent from the earlier source even though racing took place.

The official BOAT RACE historical `/owpc/pc/race/racelist` page was validated as a PRE-safe card-recovery source. The recovery code reads racelist/card fields only and does not request result/payout endpoints.

Fallback chain:

1. BoatraceCSV archived race cards
2. Kyoteibiyori historical PRE
3. BOAT RACE official racelist for cards only
4. Waku10 then uses validated BOATCAST direct fallback when needed

June 17 strict coverage from the later 30-day audit:

- source `boatrace_official_racelist_fallback`
- cards 156
- complete 156
- fallback 156
- excluded 0

Recovered fields include registration/grade/name/branch, F/L, nationwide/local rates, motor/boat rates, and historical meeting ST slots strictly before target date. Current target-day meeting-history slots are excluded.

Audit intent includes:

- `result_endpoint_requested=False`
- `payout_endpoint_requested=False`

---

# 8. 1号艇 latest research: v309 audit

Latest completed diagnostic found before this handoff:

- commit `8afb4c85b1e60c478294524a115dee5783736c5d`
- file `summary_v309_1head_opponent_zero_base_audit.md`

The frozen race selection is the v308 selected set of **345 races**; v309 is an opponent-ranking diagnostic, not a retune of the head-selection race set.

Current opponent benchmark referenced by v309:

- v300 augmented SECOND L2=3
- conditional THIRD L2=.1
- TOP2XTOP2 alpha=.60

Overall diagnostics:

- races: 345
- 1-head wins: 290/345 = **84.06%**
- exact 3-ticket hits: 132/345 = **38.26%**

On the 290 races where boat 1 actually won:

- actual SECOND rank TOP1: 43.79%
- actual SECOND rank TOP2: 71.72%
- actual SECOND rank TOP3: 87.93%

Given actual SECOND, actual THIRD rank:

- TOP1: 41.38%
- TOP2: 72.76%
- TOP3: 91.03%

Head-win error classes:

- `EXACT3_HIT`: 132 = 45.52%
- `SECOND_OUTSIDE_TOP2`: 82 = 28.28%
- `THIRD_OUTSIDE_TOP2_GIVEN_ACTUAL2`: 51 = 17.59%
- `COMBINATION_POLICY_OR_ORDER`: 25 = 8.62%

Monthly diagnostics:

- Feb: R63, head51, exact3 36.51%, second TOP2 72.55%, third TOP2 76.47%
- Mar: R16, head15, exact3 43.75%, second TOP2 66.67%, third TOP2 66.67%
- Apr: R53, head48, exact3 52.83%, second TOP2 79.17%, third TOP2 85.42%
- May: R121, head101, exact3 38.02%, second TOP2 74.26%, third TOP2 67.33%
- Jun: R92, head75, exact3 30.43%, second TOP2 64.00%, third TOP2 70.67%

By actual SECOND boat:

- boat 2: R114, SECOND TOP1 67.54%, TOP2 98.25%, exact3 68.42%
- boat 3: R89, TOP1 47.19%, TOP2 84.27%, exact3 48.31%
- boat 4: R42, TOP1 16.67%, TOP2 35.71%, exact3 16.67%
- boat 5: R32, TOP1 3.12%, TOP2 18.75%, exact3 12.50%
- boat 6: R13, TOP1 0%, TOP2 0%, exact3 0%

Main v309 finding:

**The SECOND opponent model strongly under-ranks outer boats 4/5/6.** This motivated v310.

---

# 9. 1号艇 v310 latest status — FAILED, next repair target

Files/workflow:

- `run_v310_1head_opponent_headrisk_second.py`
- `.github/workflows/research-20260912-v310-opponent-headrisk-second.yml`
- implementation commit lineage includes `d0fe19895e94a691e7275229d779ea8eaeb2471b`
- workflow commit `5171a253f662896283ae49db49a5df552a0a790d`
- Actions run `34691636653`
- job `103547804312`

Purpose:

- keep v308’s frozen 345-race 1-head selected set;
- rebuild SECOND ranking using causal 3-head/4-head attack probabilities;
- specifically address v309’s poor ranking of outer boats 4/5/6;
- add result-blind monthly walk-forward p3/p4 head-risk signals;
- keep THIRD at the current v300 conditional model (L2=.1) so improvements are mainly attributable to SECOND.

Configurations intended:

- BASE: SECOND L2=3.0
- `HEADRISK_L2_1`
- `HEADRISK_L2_3`
- `HEADRISK_L2_10`
- `HEADRISK_L2_30`

Intended evaluation:

- SECOND TOP1/TOP2/TOP3 on 1-head wins
- exact 3-ticket rate on frozen 345 races

Intended outputs:

- `analysis_v310_1head_opponent_headrisk_second_configs.csv`
- `analysis_v310_1head_opponent_headrisk_second_best_by_second.csv`
- `analysis_v310_1head_opponent_headrisk_second_best_monthly.csv`
- `analysis_v310_1head_opponent_headrisk_second_best_race.csv`
- `summary_v310_1head_opponent_headrisk_second.md`

## Actual current status

Run `34691636653` **FAILED**. No v310 summary/result should be treated as available yet.

Exact failure:

`RuntimeError: missing causal head-risk probabilities`

First reported missing race IDs are 10 races from 2025-11-01:

- `202511010101`
- `202511010102`
- `202511010103`
- `202511010104`
- `202511010105`
- `202511010106`
- `202511010107`
- `202511010108`
- `202511010109`
- `202511010110`

The run had already built/recovered substantial historical data and then failed in `add_headrisk()` because the causal p3/p4 probability map did not cover those early target rows.

### Next work for v310

1. Fetch latest `main` first; another chat may already have fixed it.
2. If not fixed, inspect the v310 causal probability construction window / earliest history coverage.
3. Repair the missing early-race p3/p4 coverage **without using target-race outcomes** and without backfilling with post-target information.
4. Preserve fail-closed semantics rather than silently inventing probabilities.
5. Trigger a new Actions run from the fixed latest commit; do not merely rerun the old failed job if code changes.
6. Inspect the generated summary/config comparisons before deciding whether v310 beats the v300/v309 opponent benchmark.
7. Do not use July/August as pristine validation; September outcomes remain unread for this research unless explicitly changing the validation policy.

---

# 10. 1号艇 / 4号艇 / 5号艇 general continuity

1号艇 has active v309/v310 research beyond the older legacy operational description. Therefore the next chat must inspect newest main before assuming Legacy PRE -> v109 S-only -> v162 Top7 is still the final current description.

4号艇 and 5号艇 model families also exist in the repository. Their exact current rules/results have changed across prior chats. **Do not reconstruct them from old memory. Fetch their latest handoff/code/results from main before using them.**

---

# 11. What the next chat should do first

Recommended opening message:

`boatrace-backtest の CHAT_HANDOFF_20260912_V288_JUNE_LIVEINPUT_FINAL.md と最新GitHubを読んで続き。最新GitHubを最優先して、v310の失敗状況と最新Actionsも確認してから再開して。`

Then:

1. fetch latest `main` / recent commits;
2. inspect newest Actions, especially whether v310 has since been fixed/re-run;
3. treat June decision result as `34691540904` = 2 BET / 1 hit / ROI 153.6%, not the later uncorrected 0-BET aggregate;
4. preserve all result-blind / fail-closed / contamination rules above;
5. continue the newest model-development task present in GitHub.

---

# 12. Compact current-state summary

- **3-head:** v288 production lineage; corrected route semantics S -> A -> B -> NO_BET.
- **June v288 final decision source:** run `34691540904`, **18 PRE -> 15 evaluable -> 13 genuine NO_BET -> 2 BET -> 1 hit -> ROI 153.6%**.
- **Later June 0-BET run `34692240958`:** valid for PRE/input coverage only; it uses pre-LIVE-correction artifacts and does **not** supersede the repaired decision result.
- **June17 PRE:** recovered 156/156 via official racelist fallback, no result/payout endpoint use.
- **September v288 Sep1-11:** 2 BET / 0 hits / ROI 0%; do not tune on this if preserving pristine holdout.
- **1-head v309:** completed diagnostic; biggest opponent issue is SECOND under-ranking boats 4/5/6.
- **1-head v310:** run `34691636653` failed because causal head-risk probabilities are missing for early 2025-11-01 race IDs; fix/re-run is the immediate open task unless newer GitHub already resolves it.
- **July/August:** NON-PRISTINE.
- **Always read latest GitHub first.**
