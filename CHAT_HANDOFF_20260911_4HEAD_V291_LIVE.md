# Chat handoff — 4-head v291 LIVE continuation

Updated: 2026-09-11 JST
Repository: `merry02180218-ai/boatrace-backtest`
Default branch: `main`

## Mandatory next-chat startup
1. Read this file first.
2. Then inspect the actual latest GitHub files/commits/results before any prediction, model judgment, backtest conclusion, or code change.
3. If this handoff conflicts with a newer GitHub commit/file, **newer GitHub wins**.
4. Do not calculate LIVE predictions from chat memory alone.
5. 2026-07 and 2026-08 remain **NON-PRISTINE / potentially overfit** and must not be used to rescue/tune the current 4-head prospective policy.
6. September outcomes must not be inspected/used to tune the frozen v291 policy before prospective operation is ready.

---

# Current user goal

Make the new **4号艇頭 model** actually usable in daily LIVE operation.

The desired end-to-end LIVE chain is:

**4-head S/A eligibility -> frozen independent v283 opponent ranking -> Top4 tickets -> immutable pre-deadline trifecta odds snapshot -> composite odds >= 7.0 BET / <7.0 PASS -> exact 10,000-yen Dutch stakes -> persist audit row before result**

Current status at end of this chat:
- The **v291 market/ticket policy is frozen**.
- Historical Apr-Jun diagnostics are complete.
- The user asked: `実運用出来る？`.
- Answer after checking latest GitHub: **rules/policy are ready, but the full one-click LIVE pipeline is not yet completely operational**.
- User then asked to proceed with implementation.
- Work had just begun inspecting the latest GitHub when the user requested this handoff file.

Therefore the next chat should **continue the LIVE operationalization**, not restart model research.

---

# Frozen prospective market/ticket policy: HEAD4_V291_COMP7

Canonical freeze file:
- `HEAD4_V291_COMP7_FROZEN_20260911.md`

This is the currently frozen prospective 4-head betting overlay.

## S layer — unchanged v268
- PRE >= 0.28
- POST >= 0.25
- ENV_ENTRY >= 0.224790

Canonical source:
- `HEAD4_V268_FROZEN_20260910.md`

## A layer — unchanged v273 semantics
Only outside S:
- PRE >= 0.18
- POST >= 0.18
- A_SCORE >= 0.28 on the frozen v271/v272 OOF semantics

Priority:
1. S first.
2. If S, classify S only.
3. A only outside S.
4. Never stake S+A twice on the same race.
5. Report S / A / S+A separately.

Canonical source:
- `HEAD4_V273_ARANK_FROZEN_20260910.md`

### Critical A-layer operational gap
The final LIVE A_SCORE artifact is **still required** before A can count as formal prospective operation.

Required artifact characteristics:
- trained only through **2026-06-30**
- Jul/Aug excluded from fitting/calibration/tuning
- September outcomes not read
- preserve the v271/v272 OOF `A_SCORE >= 0.28` semantics via an **outcome-blind scale mapping** to the final LIVE model
- persist feature order, imputer/scaler, coefficients, model metadata, mapping method, mapped threshold
- freeze it before using future race outcomes

Do **not** simply apply literal `.28` to an unrelated final-model raw probability unless the mapping proves equivalence.

---

# Frozen independent opponent model

Use **v282/v283 independent opponent branch only**.

## SECOND
- independent `PLAYER_START` listwise model
- L2 = 10

## THIRD
- conditional model `P(third=t | candidate second=s, pre-result context)`
- family: `COND_BASE`
- L2 = 0.3

## Pair ordering
- v283 `TOP2XTOP2`
- `alpha2 = 0.60`
- head fixed to boat 4

## v96 prohibition
v96 is benchmark/history only.
It must never be used as:
- feature
- prior score
- candidate restriction
- Top4 restriction
- blend
- tiebreak
- fallback
- ranking signal

The new opponent model must remain completely independent from v96.

---

# Frozen v291 ticket / market rule

For every eligible S/A race, using **one immutable pre-deadline trifecta odds snapshot**:

1. Generate frozen v283 4-x-y ordered pair ranking.
2. Take exactly **Top4** tickets.
3. Read current trifecta odds for those 4 tickets.
4. Compute:

   `COMPOSITE = 1 / sum(1 / odds_i)`

5. If `COMPOSITE >= 7.000000` -> **BET**.
6. If `COMPOSITE < 7.0` -> **PASS**.
7. No variable N in v291.
8. BET race total stake = exactly **10,000 JPY**.
9. Allocate inverse to odds in 100-yen units using Hamilton/largest-remainder rounding.
10. Stake sum must equal exactly 10,000 JPY.
11. Miss payout = 0, profit = -10,000 JPY.
12. Once the pre-deadline snapshot produced BET/PASS and stakes, never revise from later odds/results.

Boundary is inclusive: **7.000000 qualifies**.

---

# Required LIVE snapshot integrity

Formal prospective/OOS tracking requires a persisted pre-deadline row with at least:
- race_code
- layer: S or A
- snapshot timestamp including timezone
- official deadline/close timestamp when available
- ordered Top4 tickets
- odds for each Top4 ticket
- composite odds
- BET/PASS
- exact stake per ticket
- total stake
- policy version `HEAD4_V291_COMP7`
- odds/data source identifier or retrieval metadata
- missing/invalid odds status if applicable

Persist **PASS rows too**. Never silently discard an eligible signal because it later loses or because odds move.

Archived/closing odds may be used for retrospective comparison but do not count as formal prospective pre-deadline evidence.

---

# ROI / staking definition — mandatory

Current canonical ROI semantics:
- exactly 10,000 yen total stake per BET race
- inverse-odds Dutch
- 100-yen units
- Hamilton/largest-remainder rounding
- zero-stake tickets are not purchased
- losing race payout = 0
- losing race profit = -10,000 yen
- realized ROI = total payout / total settled stake * 100
- composite odds is a value/market feature, **not ROI**

Canonical Dutch ancestry/reference:
- `analyze_v205_3head_operational_replay.py::round_dutch`

---

# Research path completed in this chat

## v282 — conditional THIRD breakthrough
Independent architecture:
- SECOND fixed `PLAYER_START`, L2=10
- conditional THIRD `P(third | candidate second)`
- pair probability based on P2 and conditional P3
- no v96 input

Apr-Jun ALL87:
- SECOND Top1/Top2 = 41.4 / 60.9%
- conditional THIRD Top1/Top2 = 40.2 / 69.0%
- pair Top2/Top4/Top6/Top10 = 34.5 / 44.8 / 57.5 / 67.8%

S+A40:
- pair Top2/Top4/Top6/Top10 = 25.0 / 35.0 / 50.0 / 65.0%

This established the conditional THIRD design as the strong independent baseline.

## v283 — pair-order improvement, current independent baseline
Did not retrain v282 probabilities.
Tested structural pair orderings on frozen probabilities.

Frozen:
- mode `TOP2XTOP2`
- alpha2 = 0.60

Apr-Jun ALL87:
- Top2 34.5%
- Top4 51.7%
- Top6 59.8%
- Top10 69.0%

S+A40:
- Top2 25.0%
- Top4 45.0%
- Top6 52.5%
- Top10 65.0%

This is the current opponent-order baseline used by v291.

## v284 — candidate SECOND inner/outer regime split
Tried separate conditional THIRD regimes for candidate second:
- inner {1,2,3}
- outer {5,6}

Frozen choice from tune:
- `COND_COMPACT`, L2=.3 for both regimes
- `TOP2XTOP2`, alpha2=.60

Apr-Jun ALL87:
- Top2 32.2%
- Top4 44.8%
- Top6 58.6%
- Top10 73.6%

S+A40:
- Top2 22.5%
- Top4 35.0%
- Top6 55.0%
- Top10 75.0%

Decision:
- **Do not promote v284 as opponent baseline**.
- It helped wider TopN but worsened small-N, which matters for the new market overlay.
- Retain v282/v283.

---

# Historical 10,000-yen Dutch ticket economics tested in this chat

## v285 — fixed Top4/6/8/10 economics
Applied exact 10k Dutch and counted 4-head losses correctly as -10k.

S+A 100R:

### v283
- Top4: 18 hits, +261,210 yen, **ROI 126.12%**
- Top6: ROI 98.31%
- Top8: ROI 90.67%
- Top10: ROI 83.32%

### v284
- Top4: ROI 93.48%
- Top6: ROI 104.10%
- Top8: ROI 100.17%
- Top10: 30 hits, +49,890 yen, **ROI 104.99%**

v284 Top10 monthly:
- Apr 110.13%
- May 103.76%
- Jun 101.63%

Important split:
- A was the profit engine.
- v283 Top4 A: **ROI 156.76%**.
- v283 Top4 S: about **98.95%**.

Interpretation:
- aggressive/high-return historical candidate: v283 Top4
- wider/stabler retrospective candidate: v284 Top10

## v286 — variable N from model probability concentration
Used SECOND probability concentration to choose N=4/6/8/10 without result/odds-based fitting.

Result:
- v283 variable N ROI 91.74%
- v284 variable N ROI 100.96%

Decision:
- Reject this variable-N method.
- Probability concentration of SECOND alone did not beat fixed v283 Top4.

## v287 — inherited target composite odds 10.5
Tested current odds with old-style "choose N closest to composite 10.5".

Result:
- v283 4/6/8/10 variable: avg N about 4.04, ROI **120.91%**
- v283 2..10 or 2..20: avg N about 2.40, ROI **103.39%**
- v284 variants were worse

The 4/6/8/10 rule chose:
- 4 tickets: 98R
- 6 tickets: 2R
- 8/10: 0R

Decision:
- inherited `target composite=10.5` does not fit the new v283 order.
- Do not use it for v291.

## v288 — composite-odds band / floor diagnostics
Workflow run recorded in this chat:
- run `34530786126` successful

v288 verified v283 fixed Top4 exactly:
- return 1,261,210 yen
- ROI **126.12%**

Exploratory floor rule: choose largest N while composite remains >= floor.
Best simple floor still failed to beat fixed Top4:
- floor 8, avg N 2.64, ROI about 108.27%

But the major discovery was that **Top4 composite odds itself was informative about race quality**.
Examples from Apr-Jun diagnostics:
- Top4 composite 8-10: very high retrospective ROI
- Top5 composite 6-8: very high retrospective ROI

This motivated fixing Top4 and using composite as a BET/PASS filter rather than as a variable-N target.

## v289 — Top4 composite odds as single market filter
Kept v283 Top4 fixed; filtered only by Top4 composite odds.

Apr-Jun S+A 100R reference:
- unfiltered Top4: ROI **126.12%**
- composite >=4: ROI about **147.94%**
- >=5: **198.26%**
- >=6: **233.33%**
- >=7: **310.98%**
- >=8: **380.01%**

For composite >=8:
- 21R
- head4 rate 71.4%
- trifecta hit rate 38.1%
- monthly ROI all >100 in Apr/May/Jun

LOMO diagnostic across Apr-Jun was also strong, but this remains retrospective/model-selection evidence, not formal OOS.

## v290 — risk audit of composite floors 6/7/8
Compared only three candidates, with S/A split, monthly, venue, maximum drawdown, and losing streak.

### >=6
- 40R
- head4 50.0%
- hit 25.0%
- ROI 233.33%
- max DD 77,280 yen
- max losing streak 7

### >=7
- **28R**
- head4 **64.3%**
- hit **32.1%**
- ROI **310.98%**
- max DD **60,000 yen**
- max losing streak **6**
- monthly ROI:
  - Apr 524.96%
  - May 177.91%
  - Jun 166.46%
- A: 18R, ROI about **323.49%**
- S: 10R, ROI about **288.47%**

### >=8
- 21R
- head4 71.4%
- hit 38.1%
- ROI 380.01%
- max DD 70,000 yen
- max losing streak 7

Decision:
- choose **7.0**, not because it had highest same-sample ROI, but because it gave the best risk/coverage compromise.
- Do not add venue exclusions from v290; that would be further same-sample overfitting.

---

# v291 freeze decision

User agreed to freeze the practical candidate:

**S/A eligibility -> v283 opponent model -> fixed Top4 -> composite >=7 -> 10,000-yen Dutch**

Canonical file:
- `HEAD4_V291_COMP7_FROZEN_20260911.md`

Development Apr-Jun evidence written into that file:
- unfiltered: 100R, ROI 126.12%
- comp >=6: 40R, ROI 233.33%, max DD 77,280, min-month ROI 110.97%
- comp >=7: 28R, ROI 310.98%, max DD 60,000, max losing streak 6, min-month ROI 166.46%
- comp >=8: 21R, ROI 380.01%, max DD 70,000, max losing streak 7, min-month ROI 174.80%

**These are retrospective archived-odds development figures, not promised live profitability.**

---

# Current operational readiness — important

At the end of this chat, the user asked whether it can be used in actual operation.

Correct answer after checking `HEAD4_V291_COMP7_FROZEN_20260911.md`:

## Policy/rules
**YES — frozen and defined.**

## Fully automated one-click LIVE use
**NOT YET fully complete.**

The freeze file explicitly states:
- S-layer formal prospective tracking may start only once the complete live v283 opponent inference and immutable pre-deadline odds capture are operational.
- A-layer formal prospective tracking starts only after the final through-2026-06-30 A_SCORE LIVE model + outcome-blind OOF-semantics mapping is persisted/frozen.

So do not tell the user "fully operational" until both required paths are actually implemented and tested.

---

# NEXT TASK — continue here

The user said `お願いします` after being told the LIVE pipeline still needed completion.

The next chat should execute, in this order:

## 1. Inspect latest repository before coding
Read:
- `HEAD4_V291_COMP7_FROZEN_20260911.md`
- `HEAD4_V268_FROZEN_20260910.md`
- `HEAD4_V273_ARANK_FROZEN_20260910.md`
- v282/v283 scripts/workflows/results
- any already-created v291 runner/policy JSON/test files on latest main
- current live/current-day data acquisition utilities
- current odds acquisition/snapshot utilities

Do not assume from this handoff that a v291 runner is complete; verify actual main.

## 2. Finish S-layer LIVE end-to-end first
Need one reproducible command/workflow that, for a current race:
1. reads only available pre-result current data
2. evaluates v268 S eligibility
3. runs frozen v283 opponent inference
4. returns ordered Top4 `4-x-y`
5. obtains/captures current pre-deadline trifecta odds
6. persists immutable odds snapshot + timestamp/source metadata
7. computes Top4 composite
8. BET if >=7.0, PASS otherwise
9. for BET, returns exact four Dutch stakes totaling 10,000 yen in 100-yen units
10. persists decision before result

Output should clearly include:
- race
- S status
- ordered Top4
- each current odds
- composite odds
- BET/PASS
- each stake
- total 10,000 yen
- snapshot timestamp
- source
- policy `HEAD4_V291_COMP7`

## 3. Build/freeze final A_SCORE LIVE artifact
Use actual v271/v272 code to reconstruct the exact OOF semantics.
Then:
- train final allowed model only through 2026-06-30
- exclude Jul/Aug
- do not inspect September outcomes
- map OOF .28 semantics outcome-blind to final score scale
- freeze artifact + metadata
- add deterministic inference test

Only after this may A enter formal prospective operation.

## 4. Connect A to same v291 market/ticket runner
S priority remains mandatory.
If S passes S criteria -> S only.
Else evaluate A.
Then use same v283 Top4 / comp>=7 / 10k Dutch chain.

## 5. Add pre-result integrity tests
Minimum tests:
- no result/payout columns available to inference path
- no post-deadline odds accepted for formal snapshot
- exactly four tickets in v291
- head always boat4
- no v96 feature/ranking/fallback
- composite boundary 7.0 inclusive
- composite <7 PASS with stake 0
- BET stake exactly 10,000
- each stake multiple of 100
- PASS rows persisted
- S+A never double-staked

## 6. Only then declare "実運用可能"
A successful historical workflow is not sufficient.
Need the actual current-race pre-deadline chain to run successfully.

---

# What NOT to do next

- Do not reopen v284 as the primary opponent model.
- Do not retune composite 7.0 from September results.
- Do not optimize venue exclusions from the Apr-Jun audit.
- Do not reuse old v96 ranking in any way.
- Do not use Jul/Aug as pristine validation or tuning rescue.
- Do not call archived/closing odds a live immutable snapshot.
- Do not use a raw final-model A probability threshold of .28 without preserving the OOF score semantics.
- Do not change Top4 to variable N and still call it v291.
- Any changed threshold/model/ticket rule needs a new version.

---

# Recommended next-chat prompt

`boatrace-backtest の CHAT_HANDOFF_20260911_4HEAD_V291_LIVE.md と最新GitHubを読んで続き。4号艇v291は S/A -> 独立v283 -> Top4固定 -> 合成オッズ7.0以上 -> 1万円Dutch で凍結済み。まず最新mainを確認して、SのLIVE相手推論＋締切前オッズsnapshot＋BET/PASS＋4点Dutchを実運用可能にし、その後A_SCORE LIVE artifactを6/30までのデータだけで固定してAも接続して。7月8月はNON-PRISTINE、9月結果は使わない。`
