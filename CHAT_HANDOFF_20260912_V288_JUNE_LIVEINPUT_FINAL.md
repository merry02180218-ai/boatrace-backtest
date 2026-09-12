# CHAT HANDOFF — 2026-09-12

Repository: `merry02180218-ai/boatrace-backtest`

## Source-of-truth rules

- Always inspect the latest GitHub `main` before predictions, model changes, backtests, or production decisions.
- If old memory / prior chat / handoff conflicts with current repository code or newer committed results, **latest GitHub wins**.
- Never use target-day race result, payout, or post-deadline information in PRE/LIVE decisions.
- Missing current inputs must fail closed. Do not guess or default missing exhibition/ST/original-exhibition/odds/Waku inputs.
- July/August 2026 are NON-PRISTINE and must not be treated as clean holdout evidence.
- September 2026 is intended as pristine, outcome-blind production evidence; do not tune rules from September outcomes if preserving that holdout.

---

# 1. Current 3-head model lineage / adopted v288 context

The currently important 3号艇 production lineage in this handoff is v288.

Historical adopted v288 performance under corrected route semantics:

- 100 races
- 56 hits
- hit rate 56.00%
- stake ¥1,000,000
- payout ¥1,743,810
- profit +¥743,810
- ROI 174.381%

Production-compatible leakage-free PRE replay before September:

- 94 races
- 52 hits
- hit rate 55.319%
- stake ¥940,000
- payout ¥1,622,070
- profit +¥682,070
- ROI 172.561%

Route breakdown on that replay:

- S: 55R / 33 hits / ROI 184.062%
- A: 21R / 10 hits / ROI 149.162%
- B: 18R / 9 hits / ROI 164.717%

Proof run / marker previously established:

- run `34560827602`
- marker `V288_OPERATIONAL_PRE_REPLAY_OK`

LIVE route parity proof:

- run `34560454539`
- marker `V288_LIVE_ROUTE_PARITY_OK cases=32`

## v288 corrected route semantics

Precedence is **S -> A -> B -> NO_BET**.

S requires v243 pass plus:

- `c_b3_minus_b4_waku_st <= 0.4999999999999999`
- `c_b3_minus_b4_st >= -0.6`
- `c_b3_meetst <= 0.861111111111111`

A is an independent rescue and does **not** require v243 pass. It requires PRE S+A and v242 buyable plus:

- `c_b3_minus_b4_st >= 0.6`
- `c_wall12_weak <= 0.24875`

B is an independent rescue and does **not** require v243 pass. It requires PRE S+A and v242 buyable plus:

- `c_b3_minus_b2_motor >= 0.22388571428571424`
- `c_b3_inside_nst <= -0.0714285714285712`

September frozen history cutoff:

- `2026-08-31`

September score thresholds:

- S 70th percentile = `3.290592837278`
- A 20th percentile = `-4.79847489663985`

No current-day/month internal percentile is allowed.

---

# 2. Waku10 / PRE input policy

Policy:

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

Relevant commits from the v288 production input work:

- `302ed4978c423cc741aa26f6fd583df2b1ff0e45` — historical direct BOATCAST fallback
- `14ff3b9e79f012abb7d808425feaa8ab30277125` — production Waku fallback
- `642bd2778854c62e8de50f69fc0fa6ebc360dc54` — verifier

Prior production handoff:

- `CHAT_HANDOFF_20260911_3HEAD_V288_PRODUCTION.md`

---

# 3. September pristine result status already observed

Sep 1–11 final production-rule retrospective:

- artifact `v288-sep1-11-production-replay-final`
- run `34669018555`
- marker `V288_SEP1_11_REPLAY_OK`
- PRE candidates: 9
- final BET: 2
- hits: 0
- stake ¥20,000
- payout ¥0
- profit -¥20,000
- ROI 0%

Bets were:

- 2026-09-06 蒲郡3R — route A — actual result 1-3-6
- 2026-09-09 びわこ2R — route S — actual result 2-1-6

Do **not** tune v288 from these September outcomes if the pristine holdout principle is being preserved.

---

# 4. June 2026 operational-process replay — final corrected result

The June task was a full operational-process replay for `2026-06-01..2026-06-30`, freezing the month to information available through May 31.

June fixed configuration:

- history cutoff `2026-05-31`
- bias start `2026-05-01`
- S threshold `2.941228852972743`
- A threshold `-4.868019039818082`

Important caveat:

- v288 rules were finalized later, so June is **operational-process replay**, not pristine model-selection evidence.

## Key implementation files

- `build_3head_v288_operational_month_day.py`
- `replay_v288_operational_day.py`
- `prepare_v288_historical_pre_input.py`
- `aggregate_v288_june_operational_repair.py`
- `aggregate_v288_june_liveinput_fixed.py`

Important historical commits during June replay repair:

- `9cda9b2b5f921175f3e8aee8c9493144402c8a2f` — initial June day build
- `470f7a22333931010ecfc9c8db3d1a4f9e59ccfe` — zero-PRE fast path
- `6fd5e8b3b0116da0b2ec50fecdf8cd7b7640f964` — pair nonfinite historical training guard
- `e5108b938e347e4d532fa40abc6705dbd7682545` — replay helper allowing non-Sep cutoff
- `f379315f084ec76d7a4df78a3484d0014b9342de` — official BOAT RACE racelist fallback work
- `5af47ca6588dc7f6d31906590edf74961a5801ea` — parallel Waku recovery
- `7f211595fc2e9b2d8b7df64657e620f2ddb368cb` — June repair aggregator
- `e5dba6b534b9acdb2652347ce1168bb5f39e6a51` — replay June v288 candidates with repaired LIVE inputs
- `eef2b381f7acdf96904818e1afb01d1b93341a0d` — auto-aggregate corrected June LIVE replay

## Why the first June result was wrong

Initial June processing made the 18 PRE candidates look like they were all NO_BET. That was not a valid model conclusion; LIVE-input reconstruction was incomplete.

The corrected LIVE-input replay was then run for the 18 PRE-candidate days using the frozen May-31 model cache and repaired historical LIVE inputs.

Replay workflow:

- `.github/workflows/replay-june-v288-liveinput-fixed.yml`
- replay run `34689337291`
- all 18 replay matrix jobs completed successfully

Aggregate workflow:

- `.github/workflows/aggregate-june-v288-liveinput-fixed.yml`
- aggregate run `34691540904`
- aggregate job `103547539466`
- status: SUCCESS
- final artifact: `v288-june-liveinput-fixed-final`
- artifact ID `10296859515`
- final marker: `V288_JUNE_LIVEINPUT_FIXED_OK`

## Corrected June final metrics

This is the final result to use going forward instead of the old “18 candidates -> 0 bets” interpretation.

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

- 2026-06-06: 1 BET, S route, miss, -¥10,000
- 2026-06-12: 1 BET, A route, hit, payout ¥30,720, +¥20,720

## Gate pass counts among 15 LIVE-evaluable candidates

- v242_buyable: 12/15
- v243_pass: 5/15
- S_condition: 4/15
- A_condition: 3/15
- B_condition: 0/15

## Genuine NO_BET reason breakdown

- `v242_not_buyable`: 3
- `v243_pass_but_S_fail_no_rescue`: 4
- `v243_fail_no_A_or_B_rescue`: 6

Total genuine NO_BET = 13.

## Remaining input errors

Three PRE candidates could still not be evaluated as valid LIVE decisions:

1. original exhibition unavailable — BOATCAST 403 for 2026-06-05 candidate
2. original exhibition unavailable — BOATCAST 403 for 2026-06-14 candidate
3. archived odds incomplete 0/120 — 2026-06-17 candidate

Therefore the **clean evaluable population is 15**, not 18.

## Odds caveat

The repair used official BOAT RACE closing 3連単 odds archive where legacy od3 was unavailable.

These are closing snapshots, **not exact historical purchase-time fills**. Thus the exact payout return under a true historical purchase-time odds snapshot can differ slightly. The decision logic itself remained result-blind.

Target-day results/payouts were joined only after decisions were frozen.

---

# 5. June 17 historical PRE recovery details

June 17 originally failed because archived race cards were absent from the earlier source path even though racing definitely took place.

Official BOAT RACE `/owpc/pc/race/racelist` historical page was validated as a PRE-safe card-recovery source because the code reads only the racelist/card fields and does not request result or payout endpoints.

Recovered card fields include registration/grade/name/branch, F/L, nationwide/local rates, motor/boat rates, and historical meeting ST slots that are strictly before the target date.

Current target-day meeting history slots are excluded.

The June 17 PRE source fallback chain became:

1. BoatraceCSV archived race cards
2. Kyoteibiyori historical PRE
3. BOAT RACE official racelist for cards only

Then Waku10 uses validated BOATCAST direct fallback.

Audit flags include `result_endpoint_requested=False` and `payout_endpoint_requested=False`.

---

# 6. Critical interpretation of June result

The corrected June result is positive:

- 2 bets
- 1 hit
- ROI 153.6%

But sample size is **only 2 bets**, so do not claim the model is proven from June alone.

What June does show:

- the original 18 -> 0 bet conclusion was an input-reconstruction artifact, not true v288 behavior;
- with repaired LIVE inputs, v288 did place bets under operational rules;
- the observed corrected June result is profitable, but statistically weak due to tiny bet count;
- B route did not fire at all in the 15 LIVE-evaluable June candidates.

Use the corrected artifact/run above as the June source of truth.

---

# 7. Operational / safety rules that must carry into next chat

- Before doing anything, fetch latest `main` and inspect relevant new commits/workflows because multiple chats may have modified the repo after this handoff.
- Do not rely only on this handoff if GitHub has newer files.
- Never rerun an old failed job expecting it to use newer source code; old Actions reruns generally use the old commit. Trigger a new run on latest code when source fixes matter.
- Keep PRE strictly result-blind.
- Results, payouts and finishing order can only be joined after decision freeze.
- Historical repair sources must not request result/payout endpoints during input construction.
- Missing LIVE inputs cause exclusion/error, not guessed values.
- July/August are NON-PRISTINE.
- September should remain pristine if possible.

---

# 8. What the next chat should do first

Start by saying roughly:

`boatrace-backtest の CHAT_HANDOFF_20260912_V288_JUNE_LIVEINPUT_FINAL.md と最新GitHubを読んで続き。最新GitHubを最優先して。`

Then the next chat should:

1. fetch latest `main` and recent commits;
2. inspect whether newer v309/v310 or other model/audit work has superseded any v288-specific implementation/rules;
3. preserve the corrected June final metric as the June v288 operational result unless a newer committed audit explicitly supersedes it;
4. inspect the newest Actions results before making any new performance claim;
5. continue whichever current model-development task is newest in GitHub, while retaining all leakage/fail-closed/pristine constraints above.

---

# 9. Compact current-state summary

- v288 June operational replay is now repaired and aggregated successfully.
- Correct June result: **18 PRE -> 15 evaluable -> 13 genuine NO_BET -> 2 BET -> 1 HIT -> ROI 153.6%**.
- Final corrected June artifact: `v288-june-liveinput-fixed-final`, artifact ID `10296859515`, run `34691540904`.
- Do not use the earlier “18 candidates, 0 BET” result anymore.
- Latest GitHub at the time of the next chat must still be checked first, especially because newer v309/v310 work may exist beyond the v288 June replay covered here.
