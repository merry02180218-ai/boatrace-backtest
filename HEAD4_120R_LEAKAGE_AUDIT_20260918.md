# HEAD4 120R Leak Audit — 2026-09-18

## Scope
Frozen research candidate:
`HEAD4_RESEARCH_NESTED_LINEAR_120R_20260918`

Preferred rule:
- preserve the frozen 77R research base;
- add a race when:
  - `composite_odds >= 2.5`
  - `head_prob + 1.50 * opponent_mass >= 0.82`

This audit explicitly separates:
1. same-race outcome leakage,
2. temporal/future-feature leakage,
3. market-timing leakage,
4. model-selection leakage,
5. retrospective sample-selection bias.

September 2026 outcomes remain **UNREAD**.

---

## Executive conclusion

| Class | Verdict | Meaning |
|---|---|---|
| Same-race outcome leakage | **PASS** | No result / payout / finishing-order field is used directly by the 120R membership rule. |
| Temporal feature leakage | **PASS on audited code/artifact contracts** | Frozen downstream models stop at 2026-06-30; causal prior builders freeze same-day inputs before ingesting results. |
| head_prob target leakage | **PASS** | Existing dynamic leakage audit passed; shuffled-target negative control is near random. |
| Market timing | **WARN / NOT PROSPECTIVE** | Historical `composite_odds` and `current_bet` use official closing-displayed odds rather than immutable historical pre-deadline snapshots. |
| Apr-Aug model-selection leakage | **PRESENT / NON-PRISTINE** | Apr-Aug outcomes/ROI were used to select the 120R threshold, so Apr-Aug ROI is development evidence, not independent holdout evidence. |
| Retrospective sample selection | **WARN** | The 164R reconstruction comes from settled rows with valid result and archived-odds coverage. |
| September contamination | **PASS** | September outcome/result paths remain blocked and unread. |

Overall:
`RESEARCH_REPLAY_PASS__PRODUCTION_BLOCKED_BY_NONPRISTINE_SELECTION_AND_CLOSING_ODDS_PROXY`

---

## 1. Independent membership parity

The 120R membership formula was independently re-expressed without importing the threshold-search script.

Independent result:
- fixed research population: 164R
- base profile: 77R
- preferred profile: **120R**
- membership SHA256:
  `37057b43e344309e3fd06dfa1f2b519cfaad16379e92bfda51166da42834844c`

This hash has been added to the frozen research artifact.

Core Actions replay:
- Run: `35305395486`
- Job: `105476437527`
- conclusion: **SUCCESS**
- Artifact: `10532065363`
- digest: `sha256:e0e68ff7befc42e011a2802b9dcf25392361346672d5255956136aa52263cd2c`

Official core replay:
- 120R
- retrospective ROI: 127.7217%
- monthly floor: 101.75%
- Apr: 22R / 158.14%
- May: 28R / 133.95%
- Jun: 21R / 111.16%
- Jul: 31R / 126.81%
- Aug: 18R / 101.75%

These are **NON-PRISTINE model-selection metrics**, not prospective ROI.

---

## 2. head_prob leakage audit

Exact current leakage-audit source blob:
`24b5a2e7748d50707dd6882577eddb5ef2d3451b`

It is unchanged from the successful dynamic audit:
- Run: `35234326600`
- Job: `105246227265`
- Artifact: `10503431028`
- digest: `sha256:a51cb2320691ca816f4eac9852027cb6b62aca64f44514a53273ad0516ee02a9`

Dynamic results:
- Apr-Jun model training rows: 13,221
- Apr-Jun boat-4 wins: 1,276
- Jul-Aug model-validation rows: 9,610
- Jul-Aug boat-4 wins: 964
- model feature count: 78
- Jul-Aug AUC: **0.727090**
- shuffled-target negative-control mean AUC: **0.503484**

Code contract:
- features are taken from race-card rows;
- outcomes are used to create the `head4` target only;
- feature availability is selected using Apr-Jun training rows only;
- imputer/scaler/model are fit on Apr-Jun only;
- Jul-Aug is predict-only inside the head-probability model itself.

Important distinction:
- Jul-Aug is model-OOS for the `head_prob` model;
- but the final 120R **rule thresholds were later selected using Apr-Aug ROI**, so the 120R strategy as a whole is not OOS on Jul-Aug.

---

## 3. Frozen opponent / downstream artifact

Artifact:
`artifacts/head4_v291_downstream_20260630.json`

Verified metadata:
- frozen training cutoff: **2026-06-30**
- Jul-Aug labels used: **false**
- September labels used: **false**
- artifact parity: **PASS**
- v283 max training date: **2026-06-29**

Frozen feature counts:
- POST: 16
- ENV_ENTRY: 25
- v283 SECOND: 25
- v283 conditional THIRD: 69

Feature-name audit:
- outcome/result/payout-like frozen feature names: **0**
- odds-named frozen model features: **0**
- v96 production signal: prohibited / false

Therefore `opponent_mass` does not directly consume the current race's outcome.

---

## 4. Causal prior-source ordering

### Motor history
`build_motor_features()` emits the entire current day's feature rows **before**
reading that day's result file and updating motor history.

Verdict: **PASS**

### Player / motor prior history
`build_prior_features()` records same-day prior features **before**
ingesting the day's results.

Verdict: **PASS**

### Exhibition ST correction history
The historical ST bias is computed first; the current day's ST rows update that
history only after feature construction.

Verdict: **PASS**

---

## 5. Current-race information timing

v283 opponent inference intentionally contains current-race exhibition information.

Examples:
- `cur_ex`
- `cur_st`
- `cur_orig_lap`
- `cur_orig_turn`
- `cur_orig_straight`
- `cur_orig_avg`
- conditional THIRD equivalents and relative-to-boat4 terms

This is **not future leakage** because these are available after exhibition and
before the race. It does mean:

> The 120R policy is a **post-exhibition / last-minute rule**, not an early pre-race candidate rule.

A live implementation must fail closed if these inputs are not yet available.

---

## 6. Market-timing warning

Historical odds source explicitly filters:
- `source_type == official_closing`
- `snapshot_type == closing_displayed`

Therefore the retrospective `composite_odds` and historical `current_bet`
do **not** prove that the exact odds were available at the time a real bet
decision had to be submitted.

This is not result leakage, but it is a form of market-time look-ahead / proxy mismatch.

Production requirement:
- use an immutable, timestamped, **pre-deadline** official odds snapshot;
- persist snapshot time, decision time, and deadline;
- fail closed if any snapshot is after the deadline;
- do not claim historical closing-odds ROI as formal prospective ROI.

Formal prospective ROI remains:
`NOT_COMPUTABLE`

---

## 7. Apr-Aug selection leakage

The 120R threshold was selected after examining Apr-Aug retrospective economics.

Therefore:
- Apr-Aug cannot be called an untouched holdout;
- the 127.72% ROI is a model-selection result;
- all-month >=100% is also a model-selection result;
- parameter-neighborhood robustness reduces single-cell overfit concern, but does not restore holdout status.

The untouched future test is still September because September outcomes remain unread.

---

## 8. Retrospective sample-selection warning

The fixed 164R reconstruction starts from historical rows that can be settled and
that have valid results / archived-odds coverage.

This does not inject the winner into the membership formula, but it may make the
historical evaluated universe narrower than the exact live universe.

Before promotion, the live candidate builder should be tested on **all eligible
pre-result races**, with missing odds/results handled by explicit fail-closed
coverage accounting rather than silently disappearing from the denominator.

---

## 9. Promotion status

### Allowed
- keep 120R as a frozen research candidate;
- prepare a live-safe scorer using pre-result and post-exhibition inputs;
- use timestamped pre-deadline odds;
- prospectively log every eligible race and every fail-closed exclusion.

### Not allowed yet
- treating Apr-Aug ROI as OOS/prospective proof;
- using archived closing odds as if they were historical live snapshots;
- promoting to production solely from the 120R retrospective numbers;
- reading September outcomes to retune before the prospective checkpoint.

Current production remains unchanged.

---

## Current unified audit run
- Script commit: `755993acb6a64d861433de4a4db985fe6f866bf2`
- Workflow commit: `41fed51929861ac43daca905ff81107cf176c110`
- Trigger commit: `9450106726151aa60d48bc773a1b82b9f411e05d`
- Run: `35306188702`
- Job: `105478741668`

The unified run is an additional end-to-end reproduction guard. Its completion
is required before any production promotion, but the leak classification above
is already supported by the frozen artifact/code contracts and the prior
successful dynamic head-probability leakage audit.

## Status
`HEAD4_120R_LEAK_AUDIT_PASS_WITH_WARNINGS__RESEARCH_ONLY`

- September: **UNREAD**
- Production: **unchanged**
