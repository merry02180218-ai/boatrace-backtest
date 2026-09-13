# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## Mandatory operating rule
**Before starting any work, write the intended next work into this handoff file first.**
If the chat/tool execution stops midway, the next session must read this file + latest GitHub and resume the unfinished item automatically. Do not wait for the user to repeat the instruction.

## User correction / actual target
Make the frozen 1-head stack genuinely usable in production while preserving the established backtest logic. This is NOT a generic 10,000-yen Dutch allocator.

Final operational output must be:
**frozen 1-head selection -> v317 SECOND -> v318 THIRD -> v320 HYBRID alpha=.70 exactly 3 tickets -> current trifecta odds for those 3 tickets -> composite odds `1/(1/o1+1/o2+1/o3)` -> BUY/SKIP output.**

## Important source audit correction (2026-09-13)
The earlier tentative assumption that v308 itself requires same-race exhibition/close-time information was checked against source and is **not correct**.

- `analyze_v294_1head_verified_prepost_research.freeze_true_pre()` builds PRE from scheduled race cards and strictly prior-day player history; its PRE universe explicitly has **no actual-entry/current-exhibition gate**.
- v305 classifies prior player history and prior-day exhibition history as safe, current card grade/wr/local/nst/motor as safe, and removes operationally unproven `meet_*` snapshot features.
- v307 explicitly replaces unsafe meeting-snapshot signal with causal prior-day features only and forbids `meet_*`.
- v308 starts from that `freeze_true_pre()` path, adds only v305-safe transfer features + v307 causal features, and asserts no `meet_*` enters the safe feature set.

Therefore, to match the backtest, **do not invent a separate post-exhibition v308 gate. v308 is the PRE head selector.** Same-race exhibition may later be researched as a separate prospective overlay, but it must not be inserted into the frozen v308 production path without a new causal backtest.

## Confirmed frozen research state
- head model: **v308**
- selected operating point: **q=0.980, opponent mass>=0.375**
- development cohort: **345R**
- head hits: **290/345 = 84.06%**
- v308-era exact3: 132/345 = 38.26%
- frozen opponent stack after later causal research:
  - SECOND **v317 OUTER_L2_1**
  - THIRD **v318 DROPSTART_T0.1**
  - tickets **v320 HYBRID alpha=.70**, exactly 3/race
- v320 development exact3: **139/345 = 40.29%**
- Jul/Aug 2026 are NON-PRISTINE/reference-only
- September outcomes remain unread/outcome-blind
- v321 Jul/Aug reference validation is complete and cannot tune/promote the model

## Backtest-alignment priority
User instruction: **progress so real production matches the established backtest result/logic.** Production convenience must not redefine the model. The historical reference to preserve is v308 q=.980 + opponent mass>=.375 producing 345R / 290 head hits, followed by the frozen v317/v318/v320 opponent stack.

## Do not do
- Do not tune on Jul/Aug.
- Do not read September outcomes.
- Do not invent a replacement model.
- Do not turn this into 10,000-yen Dutch allocation.
- Do not insert same-race exhibition/close-time fields into v308 merely because they are available LIVE.
- Do not silently use Legacy PRE in place of v308.
- Do not stop merely because one workflow fails when technical continuation is clear.
- Do not claim production readiness until current-input execution and historical alignment both pass.

## Completed in this continuation
- Source-level feature-boundary audit completed before production code changes.
- Result: v308 is PRE-safe by design; the previous post-exhibition-v308 assumption was corrected before implementation.
- v308 reference re-confirmed from committed summary: q=.980 + mass>=.375 => 345R / 290 head hits = 84.06%.
- v320 exact-3 race file confirmed: 345 rows, HYBRID alpha=.70, 139 exact3 hits.
- Existing result-free official live 3連単 odds fetcher `fetch_live_trifecta_odds.py` confirmed reusable; it requests odds3t only and validates 120 combinations.
- **v322 completed successfully.** GitHub Actions run **34753932483** / artifact **10316354325**.
- v322 frozen assertions passed: **345 races / 290 head wins / 139 exact3 hits**.
- Historical 3-ticket closing-odds coverage: **339/345 = 98.26%**.
- Evaluable overall: **339R / 136 hits = 40.12% / ROI 91.27%** under the notional composite-odds accounting convention.
- Descriptive threshold diagnostics: >=2.5 gave 114R / ROI 100.12%, >=3.0 gave 59R / ROI 100.80%, but these are reused Feb-Jun development evidence and are **not promoted** as LIVE cutoffs.

## NEXT CONCRETE ACTION — current-date frozen production adapter (written before code change)
1. Locate the exact reusable v308 feature/model path plus v321 frozen v317/v318/v320 scoring components already in repo.
2. Inspect current result-blind 2026-09-13 input layout and any existing PRE diagnostic workflow/artifact source. Do not read September outcomes.
3. Implement the smallest adapter that scores current scheduled races with **v308 semantics**, using only scheduled/static and strictly prior-day information; forbid `meet_*` and same-race exhibition/result/payout fields.
4. Derive/freeze the production v308 score cutoff and opponent-mass gate exactly from the historical frozen path; no retuning on Jul/Aug/September.
5. Assert historical alignment before using the adapter for current races: same frozen development selector must remain 345R / 290 head hits.
6. Feed only current v308-qualified races into frozen v317 SECOND + v318 THIRD + v320 HYBRID alpha=.70 exactly 3 tickets.
7. Fetch current odds only for those three tickets, compute composite odds, and output race / v308 score / mass / 3 tickets / each odds / composite odds / BUY-SKIP status. Until a prospective BUY cutoff is legitimately frozen, BUY-SKIP must be fail-safe and must not silently use the descriptive v322 threshold grid.
8. Create/modify the dedicated GitHub Actions workflow, then verify a real run ID, inspect logs/artifacts, and fix technical failures. Before each fix/restart, update this handoff first.

## ACTIVE WORK ITEM — 2026-09-13 production adapter restart
Stopped continuation was detected after v322. Resume now with **inspection only before implementation**: inspect the existing 3-head/4-head LIVE workflows and their invoked scripts, identify the exact v308/v317/v318/v320 reusable functions and result-blind current-card source, then implement the minimum 1-head adapter without changing frozen model logic. Before any subsequent fix/restart, record that intended change here first. Historical 345R/290 head hits and 139/345 exact3 are mandatory regression assertions; Jul/Aug remain NON-PRISTINE, September outcomes unread, `meet_*` forbidden.

## WORK UNIT 2026-09-13-1 — written BEFORE execution
Current position: handoff + monitoring are restored; production adapter is still unfinished.

Do now:
1. Search latest main branch for the exact v308 implementation and the v317/v318/v320/v321/v322 scripts/workflows by filename/function/commit references.
2. Inspect the current result-blind 2026-09-13 input workflow and reusable live odds fetcher.
3. Determine the minimum files/functions required for a production adapter while preserving exact regression assertions 345 selected / 290 head wins / 139 exact3.
4. BEFORE creating or editing production code, append a WORK UNIT 2 entry naming the exact files to add/change and the exact regression/current-run success criteria.

Success for this work unit: exact implementation locations and reusable functions are identified from latest GitHub; no model code is changed yet. If interrupted, resume from item 1 above.

## WORK UNIT 2026-09-13-2 — v323 frozen LIVE adapter — written BEFORE implementation
Work Unit 1 is complete. Exact implementation locations were identified:
- v308 head path: `run_v308_1head_volume_opponent_joint.py` + `analyze_v294_1head_verified_prepost_research.py` + v296/v303/v305/v307 helpers.
- frozen SECOND: `run_v317_1head_opponent_error_features.py::add_engineered(...,'OUTER')` with `run_v311_1head_opponent_second_family_autoresearch.py::p2_predict_explicit(...,1.0,None,{'START'})`.
- frozen THIRD: `run_v318_1head_opponent_third_rebuild.py::pc_predict(...,.1,'DROP_START')`.
- frozen 3-ticket policy: v320 semantics using `run_v299_1head_trifecta3_policy_search.py` HYBRID + alpha=.70.
- official result-free odds source: `fetch_live_trifecta_odds.py`.
- current 2026-09-13 result-blind card source: artifact **10302229729**, path `current_input/v288/20260913/race_cards.csv`.

### Files to add/change now
1. ADD `run_v323_1head_frozen_live_adapter.py`.
2. ADD `.github/workflows/live-1head-v323-20260913.yml`.
3. Do not modify frozen v308/v317/v318/v320 research scripts unless a technical incompatibility is proven; adapt around them.

### v323 causal/live contract
- Training/history may use chronologically prior labeled data through 2026-08-31, but Jul/Aug remain NON-PRISTINE and are never used to tune q, mass cutoff, strategy, alpha, or BUY threshold.
- **No September result or payout endpoint/file may be requested or read.** For Sep1-target history, player result state is not advanced from outcomes. The target row is inference-only.
- Same-race exhibition/current actual-entry must not enter v308.
- `meet_*` is forbidden in fitted head/opponent features and suffixes.
- v308 absolute `hcut` must be derived only from committed `analysis_v308_1head_volume_opponent_joint_pred.csv` at q=.98; opponent mass cutoff remains exactly .375.
- Current base opponent mass must be rebuilt for month `2026-09` with v300 BASE SECOND L2=10/non-aug + BASE THIRD L2=.3/non-aug, not by calling v303.opponent_mass which is hard-wired to Feb-Jun.
- Current frozen SECOND/THIRD are trained only on months `< 2026-09`; current Sep13 rows are inference-only.
- Missing current p3/p4 head-risk inputs must use the existing v310 zero-sentinel + availability-flag behavior; no future backfill.
- v320 outputs exactly 3 unique `1-x-y` tickets with HYBRID alpha=.70.
- Current odds must come only from official `odds3t`; incomplete 120-combination snapshot fails closed.
- Composite odds = `1/(1/o1+1/o2+1/o3)`.
- No reused v322 threshold is promoted. Output status must remain fail-safe, e.g. `SKIP_NO_FROZEN_ODDS_CUTOFF`, until a prospective BUY cutoff is explicitly frozen later.

### Mandatory regression/current-run success criteria
A. Before current scoring, v323 must assert the committed frozen development artifacts still equal:
- 345 selected races;
- 290 boat-1 wins;
- 139 v320 exact3 hits;
- strategy HYBRID, alpha=.70, exactly 3 unique boat-1-head tickets/race.

B. Current 2026-09-13 execution must:
- read no September outcomes/payouts;
- score all usable scheduled races with v308-compatible PRE features;
- output `race_code, venue, race, p_head, hcut, opp_mass, selected`;
- for every selected race output exactly 3 frozen tickets;
- when complete odds are available, output each ticket odds + composite odds;
- output fail-safe BUY/SKIP status without inventing a cutoff.

C. Dedicated GitHub Actions workflow must actually run. Record a real Run ID and inspect job status/logs/artifact. If it fails, BEFORE changing code/workflow append the exact intended fix as WORK UNIT 3 (or later) here, then fix and rerun.

If interrupted now: resume by creating `run_v323_1head_frozen_live_adapter.py` first, then its workflow. Do not redo research or change the frozen model.
