# Chat handoff — canonical current state

Updated: 2026-09-09 (JST)
Repository: `merry02180218-ai/boatrace-backtest`
Default branch: `main`

## Mandatory next-chat startup
1. Read `CHAT_HANDOFF_CURRENT.md` first.
2. Then inspect actual latest repo files/commits/results through GitHub before any prediction, judgment, backtest conclusion, or model change.
3. Latest GitHub file/commit supersedes older chat/memory when they conflict.
4. Never calculate a LIVE prediction from memory alone. Run the actual current program with current inputs.
5. Freeze prediction/tickets before result/payout/post-deadline information.

## Current 1-head production
Canonical production is newer than the old 2026-09-05 handoff:
**Legacy PRE -> v109 S-only -> v162 Top7**.
- v109 BUY only S: p109 >= .72.
- v162 direct ordered-pair lambda=1.00 ranks all 20 `1-s-t` pairs; present Top7.
- v110 lambda=.50 role-factorized is old opponent model.
- Do not revert to the old v109+v110 production description.

## Current 3-head production baseline
Canonical: `V166_3HEAD_PRODUCTION_RULE.md` plus newer audit files.
- Current exhibition required.
- Target boat 3 must exhibit course 3.
- v165 computes p3head using current-race exhibition/direct margins and prior-safe features.
- Production head gate: `p3head >= 0.30`.
- v166 direct ordered-pair model, opponents `[1,2,4,5,6]`, lambda=1.00, originally Top10.
- v165 is NOT a pre-exhibition score.

## PRE status — important
PRE is operationally needed because exhibition/original exhibition is only available around 15 minutes before deadline and all-race manual final review is impractical.
However, PRE hard filtering has been shown to remove profitable v165 races.

v191 clean PRE:
- cut .072608
- July watch 13.6%, v165-formal recall 85.1%
- August watch 14.2%, recall 85.5%

v205 August operational replay:
- NO PRE -> v165 -> v166 Top10: 109R, hit 30.28%, avg composite 4.584, cost 1,090,000, return 1,173,880, ROI **107.7%**, profit **+83,880**
- v191 PRE -> v165 -> v166: 93R, ROI **97.8%**, profit -20,190

PRE-dropped August audit:
- 16 dropped production races
- 3 hits
- cost 160,000
- return 264,070
- ROI **165.0%**
- profit **+104,070**
Key dropped hits included:
- `202608112308`: PRE ~0.0010, v165 p3head 31.08%, hit 3-1-4, composite ~12.365, return 129,690
- `202608210409`: PRE ~0.0087, v165 p3head 33.21%, hit 3-2-5, composite ~11.571, return 114,580
This proves PRE must not be assumed to be a value filter.

v207/v208 enhanced 8% PRE:
- August PRE watch 421R = 8.8%
- v165 formal recall 85/110 = 77.3%
- settled FINAL 84R
- Top10 hit 29/84 = 34.5%
- avg composite 3.604
- ROI **99.7%**, profit -2,910

v210 PRE ensemble:
- 8% style: August 424R = 8.9%, v165 recall 77.3%, settled 84R, ROI 99.7%
- 10% style: 520R = 10.9%, recall 82.7%, ROI 93.0%
- 12% style: 652R = 13.7%, recall 84.5%, ROI 98.9%
- The important 8/11 and 8/21 dropped winners were NOT rescued by v210.

Operational conclusion on PRE:
- PRE cannot simply be removed because of the ~15-minute deadline constraint.
- Do NOT adopt a new PRE hard gate from repeatedly inspected August data.
- Treat PRE redesign as workload reduction / attention prioritization; protect against dropping exhibition-improvement races.
- Current production PRE is not automatically replaced by v207/v210 shadow work.

## NEW ROI DEFINITION — mandatory for current ROI work
User explicitly changed ROI definition.
- Total stake fixed at **10,000 yen per selected race**.
- Selected tickets are Dutch/equal-return allocated using odds.
- Composite odds: `O_combined = 1 / sum(1/o_i)`.
- Ideal continuous stake: `10000*(1/o_i)/sum(1/o_j)`.
- Actual stakes use 100-yen units and total exactly 10,000; current implementation uses Hamilton/largest-remainder rounding.
- Historical ROI = total realized return / (settled selected races * 10,000) * 100.
- Average composite odds is NOT ROI.
- Same-race odds must be available pre-deadline for LIVE decisions; closing odds are only for historical settlement/audit unless they were truly available at decision time.
- User allowed BoatraceCSV od3 and corrected official closing to be treated as one unified historical odds series for replay aggregation, with source retained for audit.

## v166 / opponent-points re-evaluation under new ROI
User correctly noted that fixed Top10 may be structurally poor under the new ROI because adding weak tickets lowers composite odds.

v211 fixed-points test, July/August:
- Top10: July 98.7%, August 107.7%
- Top6: July **107.0%**, August **122.8%**
- August fixed points: Top4 120.1%, Top6 122.8%, Top8 113.7%, Top10 107.7%, Top12 106.4%, Top15 100.5%
Do NOT adopt Top6 from these two inspected months alone.

v212 variable 4/6/8/10 using p3head + opponent concentration:
- July ROI **109.7%**
- August ROI **117.5%**, profit +191,080, avg points 6.88
- August allocation: 4pt 37R, 6pt 25R, 8pt 9R, 10pt 38R

v213 older-period stress test, Dec-2025..Jun-2026, 486R:
- Top4 ROI 74.6%
- Top6 76.1%
- Top8 77.8%
- Top10 78.2%
- v212 variable 78.9%, avg 6.96 points
Thus fixed Top6 does NOT generalize to the older period. v212 slightly beats Top10 but remains <100%.

v214 cumulative TopN probability-mass rule failed to find a useful variable-points rule and fell back to Top10.

## Overfit audit
v215 strict monthly walk-forward:
- each month uses only prior months to choose opponent lambda/points, then evaluates the next month once
- Jan-Aug 575R aggregate ROI **94.0%**, profit -343,830
Important decomposition:
- Dec-Jun: 3-head rate 34.77%, v166 Top10 conditional coverage 81.66%, trifecta hit 28.40%, ROI **78.2%**
- Jul-Aug: 3-head rate 37.24%, Top10 coverage 76.71%, trifecta hit 28.57%, ROI **103.7%**
Thus Jul-Aug ROI improvement was NOT caused by materially better trifecta hit rate; odds/payout regime is a major driver.

## ROI regime audit v216
Key conclusion: Jul-Aug profitability is highly dependent on a few high-return hits.
- Jul-Aug normal ROI 103.7%, profit +72,680
- remove single largest-profit race -> ROI **89.9%**, profit -196,320
- remove top 3 -> ROI 77.9%
- remove top 5 -> ROI 68.9%
Largest hit:
- `202607010608`, p3head ~.302, composite ~26.703, hit 3-5-4, return ~279,000, profit +269,000
High composite odds >=7:
- Dec-Jun: 63R, hit 6.3%, ROI 70.9%
- Jul-Aug: 34R, hit 14.7%, ROI 210.6%
So do NOT claim v165/v166 became sustainably profitable based on Jul-Aug.

## v217 low-p/high-composite expectation audit
Tested the hypothesis that p3head .30-.35 plus high composite odds is a reusable value region.
Pre-Jul Dec-Jun results did NOT reproduce it:
- comp>=3: 148R, hit 14.2%, ROI 67.8%
- comp>=4: 101R, hit 6.9%, ROI 54.2%
- comp>=5: 79R, hit 7.6%, ROI 63.9%
- comp>=7: 50R, hit 4.0%, ROI 53.5%
Chronological Dec-Feb -> Mar-Jun was worse; rolling prior-only threshold selection aggregate ROI about 49.8%.
Jul-Aug looked extremely strong in the same region but is already inspected and is NOT pristine validation.
Conclusion: reject the simplistic `p3head .30-.35 + high composite odds = value` rule.

## Important new insight: point count should react to current odds
User pointed out correctly that under the new ROI, buying many tickets when composite odds is already low naturally destroys expected ROI.
Therefore the next opponent/betting design should NOT be:
`choose Top10 first -> inspect resulting composite odds`.
Instead investigate:
`v166 ranking -> obtain CURRENT pre-deadline odds -> calculate Top4/5/6/... composite odds -> decide how far to expand tickets based on probability/value -> Dutch 10,000 yen`.
The exact rule is NOT validated yet. Do not invent/adopt a minimum composite-odds cutoff without walk-forward validation.

## LIVE current-odds redesign — NEXT TASK
The user agreed to change actual operation to:
**PRE workload screen -> exhibition/original exhibition -> v165 -> v166 ranking -> fetch CURRENT 3T odds at that moment -> variable ticket count/value decision -> 10,000-yen Dutch stakes -> freeze tickets**.

Current LIVE script `predict_v192_3head_live_manual.py` intentionally does not read target-race odds/result/payout. It currently stops at v165/v166 ranking.
The next task is to build a SHADOW LIVE extension (do not silently overwrite production) that:
1. takes current exhibition/original exhibition inputs,
2. runs actual v165,
3. if p3head>=.30, runs v166 full 20-pair ranking,
4. obtains current pre-deadline 3連単 odds for that race,
5. calculates composite odds for TopN candidates (ideally N=4..15 or 20),
6. calculates exact 10,000-yen Dutch/Hamilton stakes,
7. reports a shadow variable-points/value view,
8. freezes selected odds timestamp and tickets before result.

Important: current-race odds ARE allowed for this new LIVE betting decision only if they are actually fetched before deadline. They must never be substituted by closing/result-known odds when reconstructing a historical pre-deadline decision.

Before implementing, inspect latest repo for existing official/BoatraceCSV odds fetchers and reuse the safest implementation. Historical archive scripts/workflows exist for od3/official odds, but LIVE current-odds fetching still needs to be wired into the 3-head LIVE path.

## No-leak / entry rules
- Target 3 must exhibit course 3 or exclude.
- Current exhibition, exhibition ST, original exhibition and current pre-race conditions are allowed at FINAL.
- Result/payout/post-race course are forbidden before freeze.
- Current pre-deadline odds may be used in the newly agreed betting/value stage, but record timestamp/source.
- Do not use final/deadline odds as if they were the earlier live snapshot.

## Other models
4-corner and 5-head information exists in repo but exact current versions/rules MUST be re-fetched before asserting or using them. Do not rely on the old 2026-09-05 handoff for their current production state.

## Next chat recommended opening
User can say:
`boatrace-backtest の CHAT_HANDOFF_CURRENT.md と最新GitHubを読んで続き。3号艇のLIVEを、展示後v165→v166→その時点の3連単オッズ取得→可変点数→1万円Dutchまで実装するところから再開して。`

Then immediately inspect latest GitHub before acting.
