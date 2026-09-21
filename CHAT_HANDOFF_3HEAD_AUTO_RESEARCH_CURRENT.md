# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research version: `v289-addon-wave1`
- decision: **NO_ADOPTION_WAVE1**
- v288 production is unchanged; baseline replay assertion is 94R / 52 hits / payout 1,622,070 yen.
- July/August are NON-PRISTINE. September outcomes were not loaded or used.
- Candidate universe is only v288 final NO_BET among operational PRE S/A and v242-buyable races.

## Wave-1 result
- candidate pool: 178 races
- best tested variant: `return_rank@0.45`
- best add-on: 84R / 15 hits / ROI 54.92% / profit -378,700 yen
- combined: 178R / ROI 117.04%

## Methods tested / dead ends retained
- `residual_hit`: prior-reject outcome effect ranking over pre-race safe features.
- `exhibition_upgrade`: current exhibition/ST/original-exhibition family only.
- `return_rank`: prior-reject realized-return ranking trained only on prior months.
- `attack_style_split`: separate stretch-vs-turn regimes, then outcome ranking.
- `orthogonal_consensus`: residual + exhibition + return independent-score consensus.
- `ev_calibrated`: residual hit score plus current composite odds, alpha chosen on prior months only.

## Real-operation audit
- all scoring inputs are columns already present before settlement in the canonical v243/v288 audit artifact;
- decisions use only prior-month outcomes for fitting; current test-month result/payout enters settlement only;
- missing features are median-imputed from prior training; production promotion must replace any required-current missingness with fail-closed gates;
- overlap with v288 baseline is zero by construction;
- no production workflow/model was changed.

## Next restart point
- If no wave-1 variant passes, next research must change the information/ticket family rather than loosen v288 thresholds.
- Priority next: opponent/ticket re-ranking on NO_BETs, PRE-B/new-population research with full leak audit, and venue/field archetype residual models.
- Before any promotion, build live shadow scorer with fail-closed source checks and exact 10,000-yen Dutch.

## Generated artifacts
- `research_v289_3head_addon.json`
- `research_v289_3head_addon.md`



## 2026-09-21 — dual head integration / CORE native replay failure handoff

### User intent / current priority
- Continue 3号艇 dual-head production integration before any new head-gate search.
- Formal intended architecture remains:
  - CORE = existing v288 head/route semantics, native v242 opponent selection, variable 5–10 tickets, 10,000-yen Dutch.
  - EXPANDED = independent A+.60 head model, V221 Top6 + protected SECOND4 threshold .50, exact six tickets.
  - overlap => CORE only; never double-buy.
- Goal now is integrated February ROI: CORE native replay + EXPANDED settlement + UNION 40R.
- User asked whether v288 had previously been found to leak. Current conclusion: no known audit established that v288 itself was invalidated by future-result leakage. Historical issues were Waku10 restoration/parity, NON-PRISTINE Jul/Aug, reproducibility, and workflow implementation failures. Do not overstate this as proof that leakage is impossible; continue strict causal audit.

### Frozen dual-head results already verified
- Run 35589996777, research-3head-v288-a60-overlap-strength, SUCCESS:
  - Feb v288 CORE 8R / 6 boat3 wins = 75.0%.
  - A+.60 ONLY 32R / 12 boat3 wins = 37.5%.
  - BOTH 0.
  - UNION 40R / 18 boat3 wins = 45.0%.
- Run 35592696984 / Job 106310400578, research-3head-dual-head-feb-integration, SUCCESS:
  - CORE 8, EXPANDED 32, overlap 0, union 40.
  - CORE head wins 6, EXPANDED head wins 12, union head wins 18.
  - EXPANDED protected-six opponent capture: 6/12 = 50%; swaps 13.
  - Policy guards: threshold_tuning=false, sep2026_used=false, membership_frozen_before_settlement=true.
- Do not confuse head wins with trifecta hits. Older summary Feb 8R/5 was native trifecta hits, while current exact CORE head audit is 8R/6 heads.

### Native CORE February replay design
- Inspected build_3head_v288_operational_month_day.py:
  - freezes evaluation month at month-first;
  - history cutoff must equal day before month-first;
  - target-day result/payout unavailable during PRE/cache build;
  - training rows filtered strictly before month-first;
  - pair/head models built causally;
  - target day can use PRE cards/Waku only;
  - cache records target_result_or_payout_used=False.
- For February use:
  - month-first 2026-02-01
  - month-next 2026-03-01
  - history-cutoff 2026-01-31
  - bias-start currently 2025-10-01.
- Inspected replay_v288_operational_day.py:
  - validates real history_cutoff and leakage guard;
  - adapts only replay_v288_historical_day.py's September metadata guard through a temporary cache copy;
  - underlying decision logic remains unchanged;
  - output summary is relabeled 3HEAD_V288_OPERATIONAL_MONTH_REPLAY.
- Inspected replay_v288_historical_day.py previously:
  - native pair ordering v242.safe_order;
  - v242.choose_n gives variable 5–10 tickets;
  - native v288 S/A/B route;
  - prod.dutch with 10,000-yen bank;
  - decisions/tickets frozen before payout/results are read;
  - closing od3 odds used for settlement.
- Therefore this is the preferred CORE ROI path; do not approximate CORE with protected-six.

### Workflow created
- Created .github/workflows/research-3head-dual-feb-core-native-replay.yml.
- Initial commit: 727eb3a3e562dd48d35a3cffdfab9124ea156967.
- Immediate pre-dispatch audit found a faulty static September grep that self-matched its own pattern; removed before intended dispatch.
- Fix commit: 6ae2e20d8b5bfbf7e64910c38187d00aee3442c2.
- Handoff note commit before runs: d3e6fa78dd795702a7de269012ef941deb20acf9.
- Workflow behavior:
  1. compile preflight;
  2. download frozen canonical v243 artifact from Run 34383567078 / artifact name v243-3head-expand-feature-audit;
  3. reconstruct exact Feb CORE membership using verify_v288_operational_pre_replay logic;
  4. assert exactly 8 CORE races;
  5. resolve only their dates;
  6. for each date run prepare_v288_historical_pre_input.py;
  7. build_3head_v288_operational_month_day.py with Feb frozen cutoff and --force-full-cache;
  8. replay_v288_operational_day.py using native v288 downstream;
  9. aggregate native bets/hits/stake/payout/ROI.
- --force-full-cache is intentional: fully model the target dates even if original daily PRE scan is empty; replay still applies native v288 decision logic.
- Before workflow creation/update, checked no literal backslash-n corruption. The old recurring literal \n bug is not the cause of the current failure.

### Current failure — MUST FIX FIRST IN NEXT CHAT
Two manual dispatches failed:
1. Run 35598923684 / Job 106330124958 / head SHA d3e6fa78dd795702a7de269012ef941deb20acf9 — FAILURE.
2. Run 35598989431 / Job 106330335995 / head SHA 15960d3d980f8e6289ae235c5462957c2cb9bb6c — FAILURE.
Both fail at the same point during Native v288 replay preparation/build:
FileNotFoundError:
  analysis_v234_waku10_reconstruction_coverage.csv
No final replay artifacts were produced; upload-artifact warned no matching files.
This is a dependency/materialization failure, NOT evidence of model leakage.
Do not fire again until this dependency is located/restored and the whole workflow is preflight-audited.

### Immediate next debugging steps
1. Locate where analysis_v234_waku10_reconstruction_coverage.csv is normally produced/downloaded.
   - Search repo/workflows/scripts for v234 reconstruction coverage.
   - analyze_v234_3head_waku10_restored_replay.py is imported by build_3head_v288_operational_month_day.py and its COV constant is read with pd.read_csv(pre.COV).
2. Determine canonical artifact/run containing this file; prefer an existing proven artifact rather than regenerating with potentially different semantics.
3. Add an explicit workflow step to download/copy that exact frozen coverage CSV before Native v288 replay.
4. Before dispatch:
   - fetch final workflow text;
   - py_compile every invoked Python file;
   - inspect for literal backslash-n contamination;
   - verify exact filenames/artifact names;
   - verify Feb cutoff 2026-01-31;
   - verify no target-day results/payout are loaded before decisions freeze;
   - ensure September 2026 outcomes remain UNREAD;
   - inspect shell heredocs/indentation and all dependency files.
5. User explicitly wants errors investigated thoroughly before another fire. Do not merely patch one line and ask them to fire; inspect downstream dependencies too.
6. After CORE native replay SUCCESS, inspect exact 8 race rows and compare against expected CORE membership. Then implement EXPANDED 32R settlement.
7. EXPANDED staking must not be tuned on already-seen February outcomes. Preferred inherited rule is native prod.dutch over the frozen protected exact-six using official closing odds / 10,000 yen, only if confirmed consistent with prior frozen convention. Document this as inherited/frozen, not optimized on Feb.
8. Final integrated output should separately report CORE, EXPANDED, UNION: races, head wins, trifecta hits, stake, payout, profit, ROI, monthly/route details, overlap, and leakage-policy markers.

### Important user expectations
- Japanese responses.
- Work before/after must be recorded in handoff.
- Never say a workflow fired/completed without Run/Job evidence.
- User manually dispatches workflows.
- Next error: inspect thoroughly, not repeated trial-and-error.
- Keep September 2026 results UNREAD for this research.


## 2026-09-21 — CORE native replay dependency repair START
- Resumed from commit b6f773816bf5c7b8773fd53c31bf9ea45f666e36.
- Before redispatch, audited the full current workflow plus prepare/build/replay scripts.
- Found the current v234 step unsafe/inconsistent: it generated/checked v234 coverage and then overwrote it twice from canonical_waku10_coverage.csv; build_3head_v288_operational_month_day.py also needs v234.local_rows(), so coverage CSV alone is insufficient.
- Repair plan frozen before dispatch: download the proven v233 backfill artifact from Run 34324515336, call only analyze_v234_3head_waku10_restored_replay.reconstruct() to materialize BOTH data/audit/v234_waku10/restored and analysis_v234_waku10_reconstruction_coverage.csv, assert all 62 frozen-history days 2025-12-01..2026-01-31 are non-missing/nonzero, then proceed. Do not run v234 model replay and do not overwrite its coverage with another schema.
- September 2026 outcomes remain UNREAD. No dispatch until workflow text and downstream dependencies are rechecked.


## 2026-09-21 — CORE native February replay COMPLETE
- Workflow: research-3head-dual-feb-core-native-replay
- Run 35607152183 / Job 106356931047 / Artifact 10645188056 / head SHA be2abaa97b96206980d140857cbc3f0cf6b4328a.
- SUCCESS end-to-end. Preflight, v243 frozen source, exact v234 materialization, CORE date resolution, native v288 replay, aggregation and artifact upload all succeeded.
- v234 reconstruction audit: 274 coverage rows total; frozen-history 2025-12-01..2026-01-31 = 62/62 days, 2511 rows, no missing/zero-day assertion failure.
- Frozen February CORE membership = 8 race codes across 7 dates: 202602150404, 202602071007, 202602191910, 202602161108, 202602171911, 202602120606, 202602270507, 202602171607.
- Native replay aggregate: rows=7, BET=3, hits=1, stake=30,000 yen, payout=33,840 yen, ROI=112.8%.
- Important: frozen membership is 8 races but native replay output contains 7 rows and only 3 BETs. Therefore this run validates that the native operational pipeline can reproduce a positive-ROI subset, but it is NOT an 8/8 identity proof. Before using this as final evidence for dual-model adoption, audit the missing CORE race and the five non-BET/missing decisions against frozen CORE membership.
- September 2026 outcomes remained UNREAD throughout this audit.
- Next resume point: inspect Artifact 10645188056/core_native_feb_replay.csv and per-day summaries to map all 8 frozen CORE codes to native replay status; explain 8 -> 7 rows -> 3 BETs, then compare against A+.60 EXPANDED/OVERLAP without changing production v288.


## 2026-09-21 — CORE native replay identity audit
- Inspected Artifact 10645188056 in detail. The prior aggregate ROI 112.8% MUST NOT be treated as an 8R CORE validation.
- Frozen CORE codes: 202602150404, 202602071007, 202602191910, 202602161108, 202602171911, 202602120606, 202602270507, 202602171607.
- Native operational replay rows actually produced: 202602150806, 202602160712, 202602171607, 202602071602, 202602120601, 202602270807, 202602191910.
- Exact overlap is only 2/8 frozen CORE races: 202602171607 and 202602191910. Therefore 6/8 frozen CORE identities were NOT reproduced by native PRE selection. The 7-row aggregate is mostly different races from the same dates.
- 2026-02-16 native candidate 202602160712 was ERROR_NO_BET because archived pre-race tkz/stt were missing. Genuine NO_BETs: 202602150806, 202602071602, 202602270807. Native BETs: 202602171607 (hit, +23,840), 202602120601 (miss), 202602191910 (miss).
- This means the positive aggregate ROI is not valid evidence for frozen CORE itself; it is only the native v288 output on the seven CORE dates.
- Next required work: build an identity diagnostic that exports frozen CORE membership and each date's native pre_scan/daily_manifest, then explains why each of the 6 non-overlap frozen CORE codes fails to appear (feature reconstruction/source drift vs PRE grade/threshold vs missing input). Do not compare A+.60/OVERLAP or adopt based on ROI until this is resolved.
