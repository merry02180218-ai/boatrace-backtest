# CHAT_HANDOFF — 1HEAD opponent PH/Waku10 + HYBRID inclusion
Updated: 2026-09-24 JST
Repo: merry02180218-ai/boatrace-backtest
Branch: main

## Purpose / user intent

Continue improving the 1号艇 model's exact trifecta opponent selection using PLAYERHistory and Waku10, but **do not replace the current HYBRID ticket policy wholesale**.

The user's explicit preference is:

- keep the current formal HYBRID model,
- include PLAYERHistory / Waku10 as additional information inside the existing HYBRID logic,
- inspect many individual features in detail,
- distinguish 2着 and 3着 usefulness where possible,
- prioritize stability over clever runner optimizations after repeated workflow errors,
- do not promote anything to production until it proves out and the user explicitly adopts it.

The current research objective is opponent/ticket selection only. Head selection is frozen.

---

## Formal 1HEAD baseline / production context

Formal 1HEAD production is v351-based with PLAYER_HISTORY head expansion already formally adopted.

Formal PLAYER_HISTORY expansion commit:
- `9b7c18fd7b7c37041c686d0b6a22ab04a58427c4`
- message: `prod: formally adopt 1head PLAYER_HISTORY expansion`

Profile:
- `PLAYER_HISTORY_EXPANSION_PROMOTED=True`
- profile: `1HEAD_PH_EXPANSION_20260924_H078_M375_RECENTP2_0533333`
- head min .780, max .790
- opponent mass min .375
- expansion feature: `b1_pl_recent_p2`
- threshold: .533333333333

Formal combined 194R baseline:
- 194R
- 168 heads
- 102 exact3 hits
- exact3 hit rate = 102 / 194 = 52.5773%
- head hit rate = 168 / 194 = 86.60%
- exact3 conversion among head hits = 102 / 168 = 60.71%
- stake 58,200 yen
- return 73,700 yen
- profit 15,500 yen
- ROI 126.6323%

Exact3 audit:
- Run 35887740644
- Job 107272109209
- Artifact 10762898864

PH expansion subgroup:
- 29R
- 28 heads
- 15 exact3
- ROI 114.9425%

Formal LIVE165:
- 165R
- 140 heads
- 87 exact3
- ROI 128.6869%

Existing formal ticket generation:
```python
p2, pc = v365.formal_post_five6(r0)
prob = v299.pair_prob(p2, pc, prod.TICKET_ALPHA)
formal = v299.STRATEGIES["HYBRID"](p2, pc, prob)[:3]
```

Current ticket stake remains:
- 3 tickets
- 100 yen each
- 300 yen / race

No production change has been made by the opponent PH/Waku research in this handoff.

---

## Data / causality constraints

PLAYERHistory shared feature base:
- all_win
- all_p2
- frame_win
- frame_p2
- recent_p2
for boats 1–6, 30 base PH fields total.

Canonical PH state:
- starts 2025-10-01
- target-day snapshot is frozen before same-day results
- registration-number keyed
- same-day outcome leakage prohibited

Waku10 canonical:
- `data/shared_historical/waku10_boatcast/2026/MM/DD/JJ_RR.txt`
- historical reconstruction / semantic parity / leakage audits were already completed in prior shared-feature research.

Development split used in this opponent research:
- DEV: 2026-02 through 2026-06
- SUPPORT / HoldOUT: 2026-07 and 2026-08
- September outcomes remain unread for this research.

Important:
- do not use Sep outcomes in research.
- do not use result/payout as model inputs.
- support outcomes must not be used to tune a new rule before that rule is frozen.
- old Jul-Aug evaluations already exist for older rejected variants, but any new fine-grained rule must still be developed on DEV first.

---

## Main files

Research script:
- `research_1head_opponent_player_waku_v1.py`

Workflow:
- `.github/workflows/research-1head-opponent-ph-waku.yml`

Supporting PH file:
- `run_1head_player_history_expansion.py`

Formal HYBRID implementation:
- `run_v299_1head_trifecta3_policy_search.py`

Relevant v299 functions:
- `pair_prob`
- `hybrid_order`
- `STRATEGIES["HYBRID"]`

Formal post-five6 source:
- `run_v365_1head_exact3_hit_push.py`

Frozen prepared input:
- v360 prepared artifact ID `10539401122`

---

## Current HYBRID structure — verified

`run_v299_1head_trifecta3_policy_search.py`:

```python
def hybrid_order(p2,pc,prob):
    ordinary=joint_order(prob)
    first=ordinary[0]
    s=first[0]
    same=[x for x in ordinary if x[0]==s and x!=first]
    other=[x for x in ordinary if x[0]!=s]
    pre=[first]
    if same:
        pre.append(same[0])
    if other:
        pre.append(other[0])
    ...
```

Meaning of the first 3 HYBRID tickets:
1. global top ordered pair
2. another pair with the **same 2nd-place boat** as ticket 1
3. best pair with a **different 2nd-place boat**

This is crucial. A simple global top-3 pair ranking is NOT equivalent to HYBRID.

---

# Research history leading into this chat

## DEV opponent membership model

Commit:
- `406e4d99dcd1aad8cedf7d11d07f0e21629ec6da`
- `research: freeze DEV opponent PH Waku10 reranker`

Run:
- 35895574038
- Job 107298537425
- Artifact 10766209024

Model:
- median impute
- StandardScaler
- LogisticRegression C=.25
- max_iter 2000
- class_weight balanced
- DEV-only `actual_opponent` membership target
- 41 usable PH/Waku features

Top coefficients included:
- `pl_frame_p2` +0.41431
- `waku__w10_b2_pastwin` -0.35141
- `waku__w10_rel4_b2_pastwin` -0.31689
- `waku__w10_b4_wr` -0.30387
- `pl_all_p2` +0.28509
- `waku__w10_rel4_b3_sr` -0.27947
- `waku__w10_b6_pastwin` -0.27925
- `waku__w10_b6_sr` -0.25896
- `waku__w10_b5_pastwin` -0.23617
- `waku__w10_b3_st` +0.18323
- `pl_frame_win` +0.12772
- `pl_recent_p2` +0.09388

DEV signal means also showed:
- `pl_frame_p2` delta +0.08881
- `pl_recent_p2` +0.06994
- `pl_all_p2` +0.06675

This membership model is useful as a signal source, but it treats opponents unordered; it does not inherently separate 2着 and 3着 roles.

---

## Wholesale replacement was rejected

Commit:
- `adb8ff07b58dca82400b98f779c740e9f5b07727`

Run:
- 35896414240
- Job 107301321783

Jul-Aug 46R:
formal HYBRID:
- 22 / 46 = 47.8261%
- return 13,930
- stake 13,800
- ROI 100.942%

PH/Waku wholesale replacement:
- 12 / 46 = 26.087%
- ROI 48.8406%
- rescued 0
- lost 10

Conclusion:
- never replace current HYBRID wholesale with PH/Waku ranking.

---

## Overlay order diagnostic

Commit:
- `8349b1cf6d8cf56be810f97622a36a568c042c9e`

Run:
- 35898123660
- Job 107307078761
- Artifact 10767144946

Kept formal 3-ticket membership and only changed priority/order.
PH/Waku changed priority in 217/236R.
No hit-rate change by design.

---

## One-ticket replacement scan was rejected

DEV scan commit:
- `41a1c1c7180512ea21706556ae18f18d6f7c2d05`

Run:
- 35900237078
- Job 107314226894

DEV best apparent threshold:
- gap .20
- 33 swaps
- old hits 1
- new hits 6
- net +5

Frozen Jul-Aug validation:
- commit `cd3c2b288ea095a369ab252651737bf7a2ad3661`
- Run 35916614151
- Job 107369597213

HoldOUT:
- swap_R 8
- formal 22/46 = 47.8261%
- overlay 21/46 = 45.6522%
- ROI 94.4928%
- rescued 0
- lost 1

Conclusion:
- rejected.

---

## Feature-family replacement ablation was also bad

Run:
- 35952219693
- Job 107482979613

Families:
- PH_P2
- WAKU_PASTWIN
- WAKU_ST
- WAKU_WR

All were negative as **replacement** signals at q=.70–.95.
This reinforced the user's instruction:
- do not swap out the formal model,
- include only useful information inside HYBRID.

---

# Work done in THIS CHAT

## 1. Resumed Run 35960491622 and fixed metadata/name-shadowing errors

Run 35960491622 failed:
- Job 107507803692
- Artifact 10792735079

Research itself had already completed enough to print:
`DEV_HYBRID_INCLUDED_BLEND`
- w=.05: 83 / 190 = 43.6842%
- w=.10: 86 / 190 = 45.2632%
- w=.15: 87 / 190 = 45.7895%
- w=.20: 85 / 190 = 44.7368%
- w=.25: 85 / 190 = 44.7368%
- w=.30: 85 / 190 = 44.7368%

Failure:
- final metadata referenced undefined `df`
- prior helper naming had also shadowed merged DataFrame variable `z`

Root cause history:
- merged DataFrame is `z`
- a z-score helper had also been named `z()`
- then metadata was changed to `df`, but `df` did not exist

Fix:
- preserve merged DataFrame variable `z`
- rename score helper to `zscore_map()`
- metadata reads from `z`

Commit:
- `c9b1ce955ecca53f77d7391d0beee055db9bbaa2`
- message: `fix: preserve merged dataframe and rename blend zscore helper`

Run:
- 35961169322
- Job 107509857890
- Artifact 10792875963
- SUCCESS

Meta:
- parent_R 236
- dev_R 190
- support_R 46
- support outcomes not used for selection
- Sep outcomes unread
- production unchanged
- PH missing 0
- Waku columns 52
- model features 41

Important warning:
the .15 = 87/190 result above was later shown NOT to be a valid “HYBRID-preserving” implementation and must NOT be used as a candidate result.

---

## 2. Added explicit zero-weight parity test

The user wanted the PH/Waku information included inside current HYBRID, not a new policy.

Added w=0.00 and direct race-by-race comparison:
- current formal HYBRID tickets
vs
- zero-weight blend tickets

Commit:
- `77ba07b2c1926626a5989ff485687d5cef9c1902`

First run:
- 35961885680
- failed due an indentation error on the newly inserted `for wgt` line.

Fix:
- commit `49df3ce9ee119c6229d5ec709d0ba3030879b08a`
- message: `fix: correct parity loop indentation`

Run:
- 35962481317
- Job 107513832838
- Artifact 10793151266
- SUCCESS

Critical result:
- zero-weight blend parity with real HYBRID = only **40 / 190R**
- zero-weight simple blend hits = 82 / 190 = 43.1579%

Conclusion:
- the earlier blend was NOT actually preserving HYBRID.
- w=.15 = 87/190 cannot be interpreted as “current HYBRID + PH/Waku”.
- discard that implementation for adoption purposes.

This parity audit was essential and corrected the research direction.

---

## 3. Inspected real HYBRID logic and rebuilt the inclusion correctly

After the parity failure, `run_v299_1head_trifecta3_policy_search.py` was inspected.

Verified:
- HYBRID does not choose the global top 3 pairs.
- its first three positions intentionally enforce the:
  - first pair
  - same-second pair
  - other-second pair
  structure described above.

A new structure-preserving scan was added:
- keep `v299.hybrid_order()`
- PH/Waku only perturbs the ordered pair ranking fed into HYBRID
- separate bonus for second boat `w2`
- separate bonus for third boat `w3`
- scan both over:
  - 0.00
  - 0.05
  - 0.10
  - 0.15
  - 0.20
- zero/zero must reproduce formal HYBRID exactly

Commit:
- `e75b065ba861544287ee8e84016680b015f1f470`
- message: `research: preserve HYBRID structure with separate second third bonuses`

Run:
- 35963288142
- Job 107516262962
- Artifact 10793446263
- SUCCESS

### Critical parity result

`w2=0.00 / w3=0.00`
- R 190
- hits 98
- exact3 rate 51.5789%
- parity_R **190 / 190**

This is the first implementation in this research that correctly deserves the description:
**“current HYBRID with PH/Waku included”**

### Structure-preserved DEV scan results

Baseline:
- w2=0 / w3=0: 98/190 = 51.5789%

Best observed:
- w2=0 / w3=.05: 100/190 = 52.6316%
- w2=.05 / w3=.05: 100/190 = 52.6316%
- w2=.10 / w3=.05: 100/190 = 52.6316%

Other relevant:
- w2=.05 / w3=0: 98/190
- w2=.10 / w3=0: 98/190
- w2=.15 / w3=0: 97/190
- w2=.20 / w3=0: 97/190
- w3=.10 or larger generally fell back to 97–98 hits depending on w2.

Interpretation:
- most apparent value comes from a **small third-place-side bonus**
- changing second-place side adds little or no obvious value in this coarse scan
- `w3=.05` produced +2 hits on DEV
- this is still not enough evidence to promote; must identify which features create the improvement and test stability.

---

## 4. Started fine-grained individual 3着 feature scan

User said:
- “色々特徴量あるから細かく見て”

So a feature-level scan was added, keeping the proven structure-preserved HYBRID.

Intent:
- focus on third-place bonus first because coarse w2/w3 scan suggests the gain is on the 3着 side.
- test every PH / Waku feature individually.
- standardize each feature within a race across candidate boats.
- test both signs:
  - higher is better
  - lower is better
- scan weights:
  - .02
  - .05
  - .08
  - .10
  - .15
- count:
  - exact3 hits
  - hit-rate
  - changed races
  - delta vs formal DEV baseline 98 hits

Added commit:
- `80df4fb55e4575c246e14b4702cd7834148febc0`
- message: `research: scan individual PH Waku third-place bonuses inside HYBRID`

Run:
- **35964246394**
- Job **107519205996**
- Artifact **10792929213**
- **FAILED**

The earlier structure-preserved section still ran and again printed the same valid 190/190 parity results before the failure.

### Exact current failure / next-chat starting point

Trace:
```
AttributeError: 'float' object has no attribute 'columns'
research_1head_opponent_player_waku_v1.py line 236
feature_cols=[x for x in q.columns if ...]
```

Root cause is already identified:

At line 46:
```python
q = pd.DataFrame(rows)
```

But later at line 184:
```python
for q in (.70,.75,.80,.85,.90,.95):
```

The quantile loop overwrites the DataFrame variable `q` with a float.
By the time the new fine feature scan reaches:
```python
q.columns
```
`q` is the last float quantile, causing the error.

### Immediate next fix

Rename the quantile loop variable, for example:
```python
for quantile in (.70,.75,.80,.85,.90,.95):
    t = float(g.gap.quantile(quantile))
    ...
    rows.append({
        ...
        "q": quantile,
        ...
    })
```

Do NOT rename the DataFrame `q` unless doing a careful wider cleanup; the minimal safe fix is to stop shadowing it in the quantile loop.

After editing, inspect the relevant lines before re-firing.

Then rerun the same workflow and collect:
- `DEV_THIRD_FEATURE_FINE_TOP`
- `dev_third_feature_fine_scan.csv`

No fine-feature result exists yet because Run 35964246394 failed before that scan executed.

---

# Repeated error lessons from this research

There were several avoidable Python name / formatting errors in this branch of work:

1. `z` DataFrame shadowed by helper `z()`
2. metadata changed to non-existent `df`
3. indentation error after insertion of parity loop
4. now `q` DataFrame shadowed by quantile loop float

Before next fire:
- inspect the entire touched block, not just the single error line.
- especially search for reused short variable names:
  - q
  - z
  - df
  - d
- avoid helper/function names that collide with active DataFrames.
- run a syntax/static sanity inspection after edits.

The user explicitly complained about repeated errors, so stability is more important than micro-optimizing workflow runtime.

---

# Workflow speed work / runner caveats

The user asked for speed-up.

Safe changes retained:
- dependency step skips install if imports are already available.
- prepared v360 pickle cache logic remains.

An attempted BoatraceCSV cache using raw `git` was unsafe on the self-hosted runner because `git` was not on PATH.
That optimization was reverted.

Commit restoring stable checkout:
- `7917f97060873f1962e7c3558c1f1d69338e878b`
- message: `fix: restore checkout for BoatraceCSV on runner`

Current safe approach:
- continue using `actions/checkout@v4` for BoatraceCSV.

Future safe speed improvement:
- precompute the PH/Waku feature matrix once into an artifact/cache and make feature scans operate on that local table.
- consolidate many feature/weight tests into one Python run.
- do not reintroduce runner-specific raw git assumptions without checking executable availability.

---

# Current research conclusions

1. **Do not replace formal HYBRID.**
   Wholesale PH/Waku replacement was dramatically worse.

2. **Do not trust the old “blend” numbers.**
   The simple blend only matched HYBRID 40/190 at weight zero.

3. **Structure-preserved implementation is now verified.**
   w2=0 / w3=0 matches formal HYBRID 190/190.

4. **Current DEV baseline in the verified structure-preserved sample is 98/190 = 51.58%.**

5. **A small third-place PH/Waku bonus looks mildly positive.**
   w3=.05 reached 100/190 = 52.63%, +2 hits.

6. **Second-place bonus has not shown meaningful gain yet.**
   w2 0–.10 with w3=0 stayed 98/190; larger w2 worsened.

7. **Next research should identify which individual 3着 features are responsible.**
   Do not open/tune SUPPORT for the new feature-level rule until a DEV candidate is frozen.

8. PLAYERHistory P2 fields remain promising general signals:
   - frame_p2
   - all_p2
   - recent_p2
   But the new fine scan must establish whether they help specifically in the 3着 role inside HYBRID.

9. Waku10 signals have mixed directions by boat/field.
   Treat each individually rather than one broad “Waku score”.

10. No production change has been made from this opponent-selection research.

---

# Suggested next research sequence

## Step 1 — fix current failed fine scan
Rename the line-184 quantile loop variable `q` -> `quantile`.
Inspect surrounding source and rerun.

## Step 2 — inspect top individual 3着 features on DEV
Collect the best:
- feature
- sign
- w3
- R
- hits
- delta_hits
- changed_R

Prefer candidates that:
- improve hits,
- only change a sensible number of races,
- are not extremely brittle to one weight.

## Step 3 — monthly stability
For the best few features, show Feb/Mar/Apr/May/Jun separately.
Do not choose based only on total 190R.

## Step 4 — combine only a small number of stable features
Possible structure:
```
HYBRID base ordered-pair score
+ alpha2 * second-feature score
+ alpha3 * third-feature score
```
But current evidence says focus on alpha3 first.

## Step 5 — separate second vs third labels if needed
The existing membership model target is `actual_opponent`, unordered.
A more principled next model can create:
- `actual_second`
- `actual_third`
and fit/score them separately.
This is likely superior to one generic opponent score because HYBRID has distinct second/third structure.

## Step 6 — freeze candidate on DEV
Only after the exact rule is frozen:
- evaluate Jul-Aug SUPPORT once
- compare to formal HYBRID on the same races
- then consider the exact formal 194R population / payout ROI if causally valid.

## Step 7 — production promotion only after explicit user instruction
No automatic promotion.

---

# Important user preferences for next chat

- Answer in Japanese.
- Be operational and concise.
- If user says `続けて`, actually inspect/fix/run rather than only explain.
- If user says `エラー`, inspect the log first before editing.
- If user says `終わった？`, verify the run before saying it is done.
- Report exact Run / Job / Artifact / Commit IDs.
- Do not claim success until GitHub says SUCCESS.
- Do not claim a model is “HYBRID included” unless zero-weight parity is exact.
- Avoid repeated workflow errors; inspect surrounding code before rerun.
- Keep Sep research outcomes unread.
- Keep formal production unchanged unless the user explicitly adopts a new result.

---

# Resume sentence for next chat

Read:
- `CHAT_HANDOFF_20260924_1HEAD_OPPONENT_PH_WAKU_HYBRID_CURRENT.md`
- latest `main`
- `research_1head_opponent_player_waku_v1.py`

Then resume from:
**Run 35964246394 / Job 107519205996 failure. Rename the quantile loop variable `q` so it does not overwrite the boat feature DataFrame, rerun the fine-grained third-place PH/Waku scan, and inspect `DEV_THIRD_FEATURE_FINE_TOP`. Keep HYBRID structure fixed and September outcomes unread.**
