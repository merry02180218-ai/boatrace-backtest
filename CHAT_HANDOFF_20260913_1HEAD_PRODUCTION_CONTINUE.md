# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## NEXT CHAT — READ THIS FIRST
This is the authoritative 1号艇 handoff. On a new chat, read this file and latest GitHub first; latest GitHub wins over old chat memory.

Immediate resume point:
- **Work Unit 5A source audit is COMPLETE.**
- **Work Unit 5B v325 implementation is STARTING.**
- Resume by creating `run_v325_1head_exhibition_postfilter.py` exactly as specified below, then its workflow, run Actions, inspect logs/results, and append results here.
- Do NOT repeat source-audit work unless latest GitHub has materially changed.
- Do NOT alter frozen PRE stack v308/v317/v318/v320.
- September outcomes must remain unread.

## Mandatory operating rule
Before every work unit/code change/restart, update this handoff first with:
1. current position,
2. exact work about to be done,
3. success criteria,
4. failure fallback.

After each work unit append:
1. what was actually done,
2. commit SHA(s),
3. Actions Run ID(s)/status,
4. metrics/results,
5. exact next resume point.

Fixed operating pattern: **handoff update -> work -> result append -> next work**.
If interrupted, resume from the first unfinished item here. Never guess from memory.

---

# 1. Frozen production stack

**PRE / same-day result-blind stack**
1. HEAD: **v308**
2. SECOND: **v317 `OUTER_L2_1`**
3. THIRD: **v318 `DROPSTART_T0.1`**
4. 3-ticket policy: **v320 `HYBRID alpha=.70`**
5. Exactly **3 trifecta tickets per selected race**
6. Live/current three odds -> composite odds:
   `1 / (1/o1 + 1/o2 + 1/o3)`

Development regression that must not drift:
- selected races: **345**
- boat1 wins: **290/345 = 84.06%**
- exact3 hits: **139/345 = 40.29%**

v308 frozen selection point:
- `q=.980`
- opponent mass >= `.375`
- frozen head cutoff used by v323: **0.8073405637**

Important correction:
- v308 was code-audited and is a **true PRE model**.
- Do NOT reinterpret it as exhibition-after model.
- Current-race exhibition belongs only in the new post-PRE filter being developed as v325.

Causality guardrails:
- Jul/Aug 2026 = **NON-PRISTINE/reference-only**. Never tune/promote on them.
- September outcomes = **UNREAD**.
- `meet_*` forbidden unless separately causal-audited; current 1-head frozen path excludes it.
- no same/later-race result, payout, future/backfill contamination.
- month M trains strictly on `< M`.
- missing p3/p4 never future-backfilled.

Mandatory causal cache family from opponent research:
- `cache_v313_1head_opponent_pre.csv.gz`
- `cache_v313_1head_opponent_p3.csv.gz`
- `cache_v313_1head_opponent_p4.csv.gz`
- `CACHE_V313_1HEAD_OPPONENT_CAUSAL.md`

---

# 2. Frozen model research results

- v309 clean base: exact3 132/345 = 38.26%; SECOND TOP2 71.72%
- v310 causal p3/p4: SECOND TOP2 72.07%; exact3 133/345
- v311 DROP_START: SECOND TOP2 72.41%; exact3 136/345 = 39.42%
- v312 outer gate: SECOND TOP2 73.10%; outer456 28.74%; exact3 136/345
- v314 role split: unstable; not promoted
- v315 pairwise SECOND: SECOND TOP2 72.76%; exact3 133/345
- v316 multiclass SECOND: SECOND TOP2 72.76%; exact3 136/345
- v317 winner `OUTER_L2_1`: SECOND TOP2 72.76%; outer456 28.74%; exact3 137/345 = 39.71%
- v318 winner `DROPSTART_T0.1`: THIRD TOP2 72.76%; exact3 137/345 = 39.71%
- v319 direct ordered-pair: weaker; exact3 134/345 = 38.84%
- v320 winner `HYBRID alpha=.70`: exact3 **139/345 = 40.29%**, exactly 3 tickets/race

Useful implementation locations already identified:
- v308 base/head: `run_v308_1head_volume_opponent_joint.py`
- v317: `run_v317_1head_opponent_error_features.py`, reuse `add_engineered(...,'OUTER')`
- v318: `run_v318_1head_opponent_third_rebuild.py`, reuse `pc_predict(...,.1,'DROP_START')`
- v320: `run_v299_1head_trifecta3_policy_search.py` pair probability + `HYBRID`; `analysis_v320_1head_exact3_ticket_policy_best_race.csv`
- current result-blind row generation helpers exist in v300 family.

---

# 3. v321 Jul/Aug NON-PRISTINE reference

v321 was completed as reference-only.

Main run:
- Run **34750719803**
- research computation succeeded; final in-workflow repository push failed only due non-fast-forward and outputs were subsequently committed manually.

Reference results:
- Jul+Aug selected: **55R**
- boat1 wins: **45/55 = 81.82%**
- exact3: **21/55 = 38.18%**
- July: 13R, head 11/13 = 84.62%, exact3 3/13 = 23.08%
- August: 42R, head 34/42 = 80.95%, exact3 18/42 = 42.86%

Relevant scripts:
- `run_v321_1head_julaug_prepare.py`
- `run_v321_1head_julaug_second.py`
- `run_v321_1head_julaug_base_third.py`
- `run_v321_1head_julaug_third.py`
- `run_v321_1head_julaug_score.py`
- workflow `.github/workflows/v321-1head-julaug-nonpristine.yml`

Important v321 implementation detail:
- `build_head_selection` reconstructs frozen v308 absolute head cutoff from development data and applies it to target months.
- Full causal head frame had to be persisted for v323 live fit.

Related production-fix commits:
- `db3407f03d6199453195ee00c0a313493b5e1b6d` — persist full v321 causal head frame
- `ffb0acab9f7c4355349a36da041706082d318bb8` — v323 train head from full causal cache
- `6aaa178499f5a9f1bad6342dee9d783025719959` — require full v321 head cache in workflow

---

# 4. v322 composite-odds backtest on development cohort

Files:
- `run_v322_1head_composite_odds_backtest.py`
- `.github/workflows/v322-1head-composite-odds.yml`

Run:
- **34753932483** — completed / success

Development diagnostics:
- R=345
- exact3 H=139
- complete odds=339
- missing odds=6
- evaluable hits=136
- composite-return ROI=91.27%

Threshold diagnostics (development reuse only; NOT for promotion):
- ALL: R339 H136 hit40.12% ROI91.27%
- >=1.5: R338 H136 hit40.24% ROI91.54%
- >=2.0: R336 H135 hit40.18% ROI91.63%
- >=2.5: R320 H129 hit40.31% ROI94.10%
- >=3.0: R293 H116 hit39.59% ROI93.91%
- >=3.5: R251 H96 hit38.25% ROI91.65%
- >=4.0: R216 H78 hit36.11% ROI88.38%
- >=5.0: R153 H48 hit31.37% ROI80.30%
- >=6.0: R116 H33 hit28.45% ROI78.84%
- >=8.0: R67 H17 hit25.37% ROI84.80%
- >=10.0: R48 H10 hit20.83% ROI78.53%

Guardrail:
- do not promote BUY cutoff from v322 because it reuses development outcomes.
- missing odds must remain fail-closed/explicit in live operation.

---

# 5. v323 production adapter — COMPLETE

Purpose:
Backtest-aligned live flow:
**current result-blind data -> v308 -> v317 -> v318 -> v320 exact3 tickets -> current 3T odds -> composite odds**.

Files:
- `run_v323_1head_live.py` / committed v323 live adapter code
- dedicated v323 workflow

Key commits:
- `8bbd01ce7535fcb6c376db03d9a157cd41421ca4` — define v323 work unit
- `ad1bfb7053ec6ff6fa05b718e848b2fd79b22f08` — add frozen 1-head live adapter
- `1aff55971adde1bacf5c771dc08539018a2d9853` — add v323 frozen live workflow
- `01e3c016ac198c5261e62f0394c163c39a8d96b7` — record OOF/full-cache fix before changes
- `db3407f...`, `ffb0acab...`, `6aaa1784...` fixes listed above

Verified main success:
- Actions Run **34757079269** — success
- frozen regression remained **345 / 290 / 139**
- hcut **0.8073405637**
- September results were not read

2026-09-13 production scoring example:
- 175 current races available
- v308 selected 2
- Hamamatsu 4R: tickets `1-2-3 / 1-2-4 / 1-3-2`, odds 5.0 / 6.6 / 6.9, composite **2.014**
- Fukuoka 1R: tickets `1-2-4 / 1-2-3 / 1-4-2`, odds 4.8 / 6.7 / 5.2, composite **1.819**

No BUY cutoff was frozen. Live status remains fail-safe when no validated BUY criterion exists.

---

# 6. v324 Jul/Aug composite-odds threshold audit — COMPLETE

User hypothesis tested: if exact3 ~40%, perhaps composite odds >=3.0 should be attractive.

Files:
- `run_v324_1head_julaug_composite_odds.py`
- `.github/workflows/v324-1head-julaug-composite-odds.yml`

Commits:
- `7346141821c540c3dc72563393ee0e44ae5ce6db`
- `c0ef06d56065f928fa5099e35bcfd824c9c0bf53`
- `8307774bda882110cf7f761faab15b21bad687d4`

Runs:
- first `34762913278` failed due historical odds lookup interface mismatch
- corrected **34762939723** — completed / success
- job `103738822011`
- artifact `v324-1head-julaug-composite-odds`, artifact ID `10318928652`
- reconciliation: **55 selected / 21 exact3 / 55 complete odds / 0 missing**

July:
|rule|R|H|hit rate|ROI|
|---|---:|---:|---:|---:|
|ALL|13|3|23.08%|46.61%|
|>=2.5|4|1|25.00%|66.06%|
|>=2.7|1|0|0.00%|0.00%|
|>=3.0|1|0|0.00%|0.00%|

August:
|rule|R|H|hit rate|ROI|
|---|---:|---:|---:|---:|
|ALL|42|18|42.86%|97.74%
|>=2.5|18|5|27.78%|82.41%
|>=2.7|16|4|25.00%|76.52%
|>=3.0|9|1|11.11%|41.25%
|>=3.2|7|1|14.29%|53.04%
|>=3.5|6|1|16.67%|61.88%

Jul+Aug:
|rule|R|H|hit rate|ROI|
|---|---:|---:|---:|---:|
|ALL|55|21|38.18%|85.66%
|>=2.5|22|6|27.27%|79.44%
|>=2.7|17|4|23.53%|72.02%
|>=3.0|10|1|10.00%|37.13%
|>=3.2|7|1|14.29%|53.04%
|>=3.5|6|1|16.67%|61.88%

Conclusion:
- composite >=3.0 is **not supported** by Jul/Aug reference.
- higher composite odds coincided with much lower exact3 hit probability.
- do NOT freeze/promote any odds-only BUY cutoff from this evidence.

---

# 7. User's current strategic decision

User concluded:
- To make the 3-ticket economics work, exact3 hit rate likely needs to be pushed toward **50%+**.
- New direction: build a **same-race exhibition/post-PRE decision layer** using exhibition time and original exhibition to PASS/SKIP races.

Correct architecture:
**v308 PRE -> v317 SECOND -> v318 THIRD -> v320 3 tickets -> exhibition-time postfilter PASS/SKIP -> current odds/composite odds -> BUY logic later**

The postfilter must never feed same-race exhibition fields backward into v308/v317/v318/v320.

---

# 8. Work Unit 5 / 5A — v325 exhibition postfilter

## Source audit — COMPLETE

Confirmed result-blind historical/live exhibition sources:
- historical official exhibition time: `data/previews/tkz/YYYY/MM/DD.csv`
- historical start exhibition + exhibition course: `data/previews/stt/YYYY/MM/DD.csv`
- historical original exhibition: `data/previews/original_exhibition/YYYY/MM/DD.csv`
- historical ledger/model code: `analyze_v108_1head_feasibility.py`
- historical output: `analysis_v108_1head_feasibility.csv`
- live result-blind builder already exists: `build_4head_v283_current_exhibition_live.py`

Live v283 builder uses:
- official BOAT RACE beforeinfo display time
- BOATCAST start display
- BOATCAST original exhibition
- prior-only ST lane-bias correction
- no result/payout/odds endpoint for feature building

It emits per boat:
- `cur_ex`
- `cur_st`
- `cur_orig_lap`
- `cur_orig_turn`
- `cur_orig_straight`
- `cur_orig_avg`

v108 historical relative/derived fields include:
- `one_ex`
- `one_st`
- `one_lap`
- `one_turn`
- `one_straight`
- `one_orig_avg`
- `one_direct`
- `one_score`
- `threat2..6`
- `margin2`, `margin3`, `margin23`, `margin_all`
- `st_margin2`, `st_margin3`, `st_margin23`
- `ex_margin23`
- `turn_margin23`
- `straight_margin23`

Historical coverage from v108:
- frozen races: **45,404**
- changed-entry excluded: **357**
- feature errors: **0**
- tkz coverage: **92.8%**
- stt coverage: **92.8%**
- original exhibition coverage: **88.5%**

v108 source timing was audited as feature-freeze-before-settlement.

Architectural evidence from old v123:
- old 1-head model used exhibition-only skip layer without adding new races after exhibition.
- development selected `ex_margin23 >= -0.235`.
- old Jun-Aug holdout 7-ticket hit rate improved **56.2% -> 58.2%** and head rate 81.8% -> 83.6%.
- This threshold must **NOT** be reused for v325; it only proves the architecture can work.

Source-audit handoff commits:
- `9556a0f65cd63efedb64be9e079d3550879cfeb2` — initial Work Unit 5 pre-exhibition-filter research record
- `aed49b849f2f030ab350b2393ccc11f77a69f777` — Work Unit 5A implementation specification after audit

## v325 implementation — STARTING (Work Unit 5B)

Current position:
- Work Unit 5A source audit is complete.
- No newer v325 implementation/workflow was found on the latest default branch before starting.
- Frozen PRE stack remains v308/v317/v318/v320; September outcomes remain unread.

Exact work about to be done:
1. Create `run_v325_1head_exhibition_postfilter.py`.
2. Reconcile frozen v320 identity at exactly 345 races / 139 exact3 hits before filtering.
3. Join/reconstruct same-race historical exhibition features using audited v108/v283-compatible sources only.
4. Quantify `has_tkz`, `has_stt`, `has_orig` coverage and fail closed for missing inputs.
5. Use Feb-Apr discovery, May validation/freeze, Jun one-shot forward check; no Jul/Aug outcome inspection until candidate is frozen.
6. Test interpretable 1-D lower-tail skip gates plus one small regularized logistic PASS model on predeclared exhibition features only.
7. Freeze the development candidate before one-time Jul/Aug NON-PRISTINE reference evaluation.
8. Add `.github/workflows/v325-1head-exhibition-postfilter.yml`, run Actions, inspect logs/artifact, then record all results here.

Success criteria:
- v320 identity unchanged at 345/139.
- explicit exhibition coverage/missingness.
- no September results/payout reads.
- no changes to v308/v317/v318/v320.
- chronological May/Jun validation reported.
- Jul/Aug evaluated only after freeze and never used to retune.
- target >=50% exact3 PASS rate with useful retained R; no production promotion unless forward evidence supports it.

Failure fallback:
- If `analysis_v108_1head_feasibility.csv` is unusable, rebuild a separate result-blind historical exhibition dataset from existing `tkz/stt/original_exhibition` snapshots using audited transforms.
- On any implementation/Actions failure, append the exact failure and intended fix to this handoff before changing code.

Create new file:
### `run_v325_1head_exhibition_postfilter.py`

Required behavior:
1. Read frozen v320 development cohort `analysis_v320_1head_exact3_ticket_policy_best_race.csv`.
2. Reconcile exactly **345R / 139 exact3** before any filtering.
3. Join by `race_code` to historical same-race exhibition ledger from v108 and/or safely reconstruct from historical `tkz/stt/original_exhibition` snapshots if needed.
4. Quantify join coverage and missingness explicitly (`has_tkz`, `has_stt`, `has_orig`).
5. Fail closed for missing exhibition inputs; never future-impute or use post-race backfill.
6. Use exhibition data only as post-PRE filter.
7. Use interpretable relative features first; no broad combinatorial search.
8. If ticket-aware opponent features are possible from safe historical primitives, derive them; otherwise defer them instead of unsafe reconstruction.

### Predeclared research split
Use only Feb-Jun development evidence to discover/freeze:
- Feb-Apr: discovery
- May: validation/freeze
- Jun: one-shot chronological forward check
- **Do not inspect Jul/Aug filter outcomes until candidate spec is frozen.**

Test at minimum:
- simple one-dimensional lower-tail skip gates on predeclared exhibition-relative features
- a small regularized logistic PASS score using only predeclared exhibition features
- avoid random CV; use chronological validation

Primary goal:
- exact3 PASS hit rate **>=50%** with useful retained R

For every candidate report:
- retained R
- exact3 H/rate
- head H/rate
- skipped R exact3 H/rate
- month-by-month stability
- coverage/missingness
- if historical odds complete, diagnostic composite-odds ROI, but do not tune model on odds

Candidate promotion within development:
- reaching 50% in discovery alone is insufficient.
- candidate must hold >=50% or show credible/stable lift in May/Jun chronological forward checks.

Only after candidate is frozen from Feb-Jun:
- evaluate once on Jul/Aug v321 **55R / 21 exact3**.
- Jul/Aug result is reference-only.
- do not retune threshold/model from Jul/Aug.

Then add:
### `.github/workflows/v325-1head-exhibition-postfilter.yml`

Workflow must:
- run audit/reconciliation
- produce dataset + candidate table + summary
- upload artifact
- expose clear logs for retained R / exact3 / head / monthly stability
- never read September result/payout

v325 success criteria:
- v320 identity unchanged 345/139
- exhibition join coverage explicit
- no September outcomes
- no modification to v308/v317/v318/v320
- chronological validation reported
- Jul/Aug only after candidate freeze
- target >=50% exact3, but no production claim unless forward evidence supports it

If v108 CSV in GitHub is empty/truncated or cannot be directly consumed:
- do NOT abandon v325.
- build a separate safe historical exhibition dataset from the existing `tkz/stt/original_exhibition` snapshots using the same audited transforms from `analyze_v108_1head_feasibility.py` / `build_4head_v283_current_exhibition_live.py`.
- freeze all exhibition features before any settlement labels are attached.

---

# 9. Automation/task state

User requested duplicate 1-head monitoring tasks be stopped and replaced by one continuation monitor.
- old duplicate 1-head automation tasks were disabled.
- one hourly condition-watch task titled **`1号艇 継続監視`** was created.
- its purpose is to detect stopped 1-head progress and resume from latest handoff/GitHub, while respecting the handoff-before-work rule.

Do not create more duplicate 1-head monitor tasks unless user explicitly asks.

---

# 10. Exact next action in next chat

1. Read this file + latest GitHub.
2. Verify no newer v325 implementation already landed.
3. If Work Unit 5B has not started, **before code change**, append a short Work Unit 5B line stating implementation is starting and success criteria above still apply.
4. If Work Unit 5B is already marked STARTING, continue directly with `run_v325_1head_exhibition_postfilter.py`.
5. If historical v108 CSV cannot be consumed, safely rebuild the exhibition feature dataset from `tkz/stt/original_exhibition` using audited v108/v283 transforms.
6. Create/run `.github/workflows/v325-1head-exhibition-postfilter.yml`.
7. Trigger Actions and verify actual Run ID/status/logs/artifact.
8. On any failure: append intended fix to this handoff before changing code.
9. On success: append development split metrics, frozen candidate rule/model, Jul/Aug reference, commits, Run ID, artifact ID, and exact production-next step.

**Do not stop at a status report. The next chat should actually implement and run v325.**