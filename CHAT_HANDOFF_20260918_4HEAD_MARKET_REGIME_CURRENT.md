# CHAT HANDOFF — 2026-09-18 — 4HEAD HEADPROB / MARKET REGIME CURRENT

Repo: `merry02180218-ai/boatrace-backtest`

## 再開時の最優先
- 最新GitHub/mainを最優先。古いチャット・古い引き継ぎと競合したら最新mainを採用。
- September 2026 の結果・払戻は絶対に読まない。常に `UNREAD`。
- production は明示承認なしに変更しない。
- v96 prohibited。
- closing odds は retrospective diagnostic only。formal prospective ROI = `NOT_COMPUTABLE`。
- 作業前後に必ずこの引き継ぎへ BEFORE / AFTER を追記する。

## 現行production
Policy: `HEAD4_V291_COMP7_THIRD010`
- PRE >= 0.28 inclusive
- POST >= 0.25 inclusive
- ENV_ENTRY >= 0.224790 inclusive
- frozen opponent v283
  - SECOND `PLAYER_START`
  - conditional THIRD `COND_BASE`
  - pair mode `TOP2XTOP2`
  - alpha2=.60
- THIRD close margin: gap <= .10
- tickets 4–6; base v283 Top4 preserved
- composite odds >= 7.0 => BET
- JPY10,000 Dutch / 100-yen units
- production runner: `run_4head_v291_third010_live.py`
- production remains unchanged.

## 固定候補再現
`audit_4head_86r_independent.py`
- WIN=-0.0299361318939513
- REN2=-7.080000000000001
- PLAYER=.215605
- ST=-0.6000000000000001
- ORIG=-0.057777777777777706
Population:
- Apr-Jun 86R / 35 head4
- Jul-Aug 78R / 35 head4
- Apr-Aug 164R / 70 head4

## THIRD0.10
`analyze_4head_v283_second_margin_rescue.py`
- frozen v283 Top4から開始。
- SECOND top2各枝で conditional THIRD rank2-rank3 gap <= .10 のときrank3を追加。
- 4–6 tickets。base Top4維持。
- Apr-Aug 817 tickets / 35 raw hits。
Old flat-100/ticket Apr-Aug ROI 135.13%.

## six-month production reconstruction
Run `35129089769`, Job `104905317906`, Artifact `10461260375`, SUCCESS.
Mar-Aug: 191 candidates / 953 tickets / 55 BET / 7 BET hits / stake ¥550,000 / payout ¥807,580 / profit +¥257,580 / retrospective ROI 146.8327%.

## RAW HIT / comp filter
Run `35131504476`, Job `104913379223`, Artifact `10461493300`, SUCCESS.
Apr-Aug 35 raw winning-ticket races; comp>=7 retained only 5 and discarded 30.

Comp sweep Run `35135508327`, Job `104926754630`, Artifact `10463204774`, SUCCESS.
- no filter: Apr-Jun 149.0%, Jul-Aug 86.4%
- comp 6.00: 246.9%, 23.0%
- comp 6.25: 266.5%, 23.0%
- comp 6.50: 293.4%, 0%
- comp 6.75: 262.5%, 0%
- comp 7.00: 255.4%, 0%
Simple lowering rejected.

## renewed BoatraceCSV head probability
Source: BoatraceCSV public data.
First run `35232199824`, Job `105238910701`, Artifact `10501603555`, SUCCESS.
- Apr-Jun all-race train 13,221R / head4 1,276
- Jul-Aug model-training-unseen validation 9,610R / head4 964
- 78 learning fields.

Strict leakage audit:
Run `35234326600`, Job `105246227265`, Artifact `10503431028`, SUCCESS.
- usable fields selected using Apr-Jun training rows only.
- imputation/scaling/logistic model fit Apr-Jun only.
- Jul-Aug predict only.
- validation AUC 0.727090.
- 10 shuffled-target controls mean AUC 0.503484.
- implemented checks found no obvious future/result leakage; not proof of absolute zero leakage.
- corrected cut examples:
  - .30: Apr-Jun 405/150=37.04%; Jul-Aug 369/145=39.30%
  - .35: 217/87=40.09%; 203/93=45.81%
  - .40: 110/45=40.91%; 114/58=50.88%.

## head-probability PASS rescue
Run `35238737384`, Job `105261364738`, Artifact `10505011547`, SUCCESS.
- exact 164R / 70 head4 / 817 tickets / 35 raw hits reproduced.
- head-probability-only rescue did not produce robust profitable Jul-Aug rule.
- broad reference head_prob>=.21/no comp lower bound: 72 BET R / 15 hits / ROI 86.40%.
- rejected; production unchanged.

## head probability × opponent mass × last-minute/original-exhibition joint grid
Script: `audit_4head_joint_headprob_opponentmass_lastminute.py`
Workflow: `.github/workflows/audit-4head-joint-headprob-opponentmass-lastminute.yml`
Run `35290923983`, Job `105433371006`, Artifact `10526661988`, SUCCESS.
- fixed 164R / 70 head4 / 817 tickets / 35 hits.
- robust criterion: Apr-Jun ROI>=100 AND Jul-Aug ROI>=100 AND Jul-Aug added rescue>=5.
- robust cells = 0.
Important caveat: third dimension named last-minute but currently uses `orig4_adv_inside` (original-exhibition advantage), NOT literal production POST/ENV_ENTRY thresholds. If exact last-minute threshold research is needed, reconstruct POST/ENV_ENTRY scores separately.

Opponent mass definition:
- all 20 (second,third) pairs among 1,2,3,5,6.
- score = exp(.60*log(p2[s]) + .40*log(pc[(s,t)])).
- normalize over 20.
- opponent_mass = normalized mass covered by production tickets.

## ablation / bottleneck
Script `audit_4head_joint_grid_ablation.py`
Workflow `.github/workflows/audit-4head-joint-grid-ablation.yml`
Run `35294996618`, Job `105445615892`, Artifact `10528471677`, SUCCESS.
Best per ablation:
- MASS only >=.30: Apr-Jun 86 BET /64 added /19 hits / ROI 148.9953%; Jul-Aug 75 BET /52 added /16 hits / ROI 89.9027%.
- MASS+LAST same best.
- ALL head>=.20,mass>=.30: Apr-Jun 150.5444%; Jul-Aug 88.8729%.
- HEAD only >=.20: Apr-Jun 150.5444%; Jul-Aug 85.2205%.
Conclusion: head probability / original-exhibition gate did not fix validation; opponent mass best but still <100%.

## Jul-Aug ROI collapse attribution — key finding
Script: `audit_4head_julaug_roi_collapse_attribution.py`
Workflow: `.github/workflows/audit-4head-julaug-roi-collapse-attribution.yml`
Run `35298033779`, Job `105454524498`, Artifact `10528619280`, head `b68559710aca47fda70a8618ed26a9f850968be7`, SUCCESS.

Funnel:
- Apr-Jun ALL: 86R / head4 35 (40.70%) / 19 ticket hits / ROI 148.9953%.
- Apr-Jun comp>=7: 22R / 5 hits / ROI 255.40%.
- Apr-Jun comp<7: 64R / 14 hits / ROI 112.4188%.
- Jul-Aug ALL: 78R / head4 35 (44.87%) / 16 ticket hits / ROI 86.4449%.
- Jul-Aug comp>=7: 23R / head4 only 3 / 0 ticket hits / ROI 0%.
- Jul-Aug comp<7: 55R / head4 32 / 16 ticket hits / ROI 122.5945%.

Distribution:
- Apr-Jun hit composite odds median 6.1571; 5/19 hits had comp>=7; winning ticket average odds 34.49.
- Jul-Aug hit composite odds median 4.0428; 0/16 hits had comp>=7; winning ticket average odds 28.04.
- Jul-Aug misses composite odds median 5.404; 23 misses had comp>=7.
Interpretation:
- 4号艇頭判定自体は悪化していない（head4 rate actually rose 40.7% -> 44.9%）。
- collapse occurs downstream: comp>=7 market filter reversed sign in Jul-Aug.
- all 16 Jul-Aug ticket hits were in comp<7; that side alone ROI 122.59%.
- Need distinguish structural/regime shift from sample/month variance before changing production.

## CURRENT RUN — MARKET REGIME / STRUCTURE SHIFT
User said `発火した` and then requested full handoff for next chat.

Script:
`audit_4head_market_regime_structure_shift.py`
commit `537b7e4b2c42749c5eb0b09f26bf9a21bf8a12ce`

Workflow:
`.github/workflows/audit-4head-market-regime-structure-shift.yml`
commit `46b0d55b7764b3fb9f30f0cae1056ab9c18c01ce`

Purpose:
- explain why high composite-odds side worked Apr-Jun but failed Jul-Aug.
- compare pre-result observables: head_prob, opponent_mass, orig4_adv_inside, tickets, composite odds.
- split July and August separately.
- fine composite-odds bands.
- monotonic LOW/HIGH composite-odds sweep at 0.25 increments.
- no automatic production promotion.

### VERIFIED CURRENT STATUS
Run `35302541048`
- status: `in_progress`
- event: workflow_dispatch
- run number: 1
- run started: 2026-09-18T03:15:45Z
- head SHA: `ca953f3e2191fe8e79690f9b168a7a8d6f40ca70`
- IMPORTANT: this head is newer than the workflow creation because main also contains later live work; run display head message is `live: judge Naruto 9R 20260918`.
- Run URL: https://github.com/merry02180218-ai/boatrace-backtest/actions/runs/35302541048
- Job/Artifact not yet recorded here because run was still in progress at handoff creation.
- Next chat MUST first check Run 35302541048 completion, then fetch Job logs + Artifact and record AFTER results here.
- Expected outputs:
  - `structure_summary.csv`
  - `fine_comp_bands.csv`
  - `monotonic_comp_sweep.csv`
  - `observable_correlations.csv`
  - `race_detail.csv`

## NEXT DECISION PATH
1. First check Run `35302541048`.
2. If SUCCESS, parse July and August separately:
   - comp<7 vs comp>=7 head4 rate/hit rate/ROI
   - head_prob/opponent_mass/orig advantage distribution
   - fine comp bands
   - LOW/HIGH monotonicity.
3. Determine whether Jul-Aug high-comp collapse is:
   - persistent in both Jul and Aug,
   - concentrated in one month,
   - associated with weaker head probability/opponent mass/exhibition structure,
   - or likely small-sample/regime noise.
4. Do NOT simply invert comp rule from retrospective results.
5. If observable structure explains the split, design a pre-result conditional market gate and validate Apr-Jun vs Jul-Aug robustness.
6. If not, next faithful research should investigate true production POST/ENV_ENTRY threshold scores; current prior 3D grid only varied `orig4_adv_inside`.
7. September remains `UNREAD`. Production unchanged until explicit user approval.

## GitHub connector / operating notes
- Prefer direct Actions API run checks or enough run-list results; do not claim missing run from truncated list.
- User may manually fire workflows; after `発火した`, verify exact run.
- Always give exact Run/Job/Artifact/commit IDs when available.
- Never claim success before verified.


## BEFORE — 2026-09-18 12:22 JST — Run 35302541048 result confirmation / continuation
- User requested continuation from Run `35302541048`.
- Re-read this handoff and latest main-visible project state before continuing.
- Verified Run `35302541048` Job `105467993604` is still `in_progress`.
- Current executing step: `市場構造シフト分解`; artifact not yet created.
- Plan after SUCCESS:
  1. fetch job logs and artifact,
  2. parse July/August separately,
  3. compare comp<7 vs comp>=7 head4/hit/ROI,
  4. inspect head_prob / opponent_mass / orig4_adv_inside distributions,
  5. inspect fine comp bands and LOW/HIGH monotonic sweep,
  6. classify persistent-vs-month-specific-vs-observable-structure-vs-sample-noise,
  7. only if justified, design the next pre-result conditional gate.
- September 2026 results remain `UNREAD`; production remains unchanged.


## BEFORE — 2026-09-18 — production S-score overlay on 164R research candidate
- Market-regime Run `35302541048` remains in progress, so continuation is not blocked on its official artifact.
- Important population distinction confirmed from GitHub history:
  - 164R (Apr-Jun 86R / Jul-Aug 78R) is the independently audited **head-rate research candidate**.
  - production S itself is still frozen `PRE>=.28 / POST>=.25 / ENV_ENTRY>=.224790`.
  - therefore the 164R set must not be called the production candidate population.
- Local reconstruction of the current market-regime audit from prior verified race_detail shows:
  - Jul and Aug both have zero ticket hits on comp>=7 (July 16R, August 7R), so the reversal is not July-only.
  - head_prob does not deteriorate materially on the high-comp side.
  - opponent_mass shifts materially lower on Jul-Aug high-comp, while orig4 advantage does not explain the collapse.
  - simple comp<7 inversion is not monthly robust because August comp<7 ROI remains below 100%.
- Next diagnostic: overlay the exact frozen production PRE/POST/ENV_ENTRY scores onto the same 164R research population without changing any thresholds.
- Implementation added:
  - `audit_4head_research_candidate_production_s_overlay.py` commit `9102c4c543b5fb031bb981e2f20e9ca923dc4751`
  - workflow commit `5ae95d325844b3a0cc0221c04185bb5a799f0194`
- The overlay audit:
  1. fits only the frozen PRE state through 2026-06-30 and parity-checks June lineage,
  2. uses the persisted frozen POST/ENV_ENTRY artifact through 2026-06-30,
  3. reconstructs Apr-Aug pre-result features,
  4. applies only the existing frozen S cuts,
  5. reports whether the bad Jul-Aug comp>=7 research races would already have failed production S before the result,
  6. never retunes thresholds and never promotes a rule from this diagnostic.
- September 2026 outcomes remain `UNREAD`; v96 remains prohibited; production unchanged.

Status: `PRODUCTION_S_OVERLAY_READY_TO_RUN`


## AFTER — Run 35302541048 market-regime / structure-shift attribution
- Workflow Run `35302541048`: **SUCCESS**
- Job `105467993604`: **SUCCESS**
- Artifact `10531205819`: `head4-market-regime-structure-shift`
- Run head SHA: `ca953f3e2191fe8e79690f9b168a7a8d6f40ca70`
- Official marker: `4号艇_市場構造シフト分解_OK`
- Reproduction marker: `HEAD4_FROZEN_INDEPENDENT_REPLAY_OK ... 164`
- Official artifact exactly matches the prior equivalent reconstruction used while the run was still executing.

### Core result
- Apr-Jun comp>=7: 22R / head4 8 (36.36%) / ticket hits 5 (22.73%) / retrospective ROI 255.40%.
- Jul-Aug comp>=7: 23R / head4 3 (13.04%) / ticket hits 0 / retrospective ROI 0%.
- July comp>=7: 16R / head4 3 / hits 0 / ROI 0%.
- August comp>=7: 7R / head4 0 / hits 0 / ROI 0%.
- Therefore the high-composite collapse is persistent across both July and August, not a July-only concentration.

### Observable shift
- high-comp mean head probability: Apr-Jun 0.19236 -> Jul-Aug 0.20692. Head probability did **not** deteriorate.
- high-comp mean opponent mass: Apr-Jun 0.43042 -> Jul-Aug 0.37496. This is the largest clear observable structural shift among the monitored variables.
- high-comp mean original-exhibition advantage: Apr-Jun 0.20758 -> Jul-Aug 0.31594. This does not explain the collapse.
- high-comp mean composite odds: Apr-Jun 13.1086 -> Jul-Aug 10.4323.
- ticket count is nearly unchanged: 4.73 -> 4.83.
- correlations on 164R: head_prob vs comp `-0.4424`; opponent_mass vs ticket_count `+0.6227`; opponent_mass vs comp only `-0.0955`.

### Composite-band / monotonicity result
- Every Jul-Aug band at comp>=7 had zero ticket hits.
- But simple inversion to LOW comp is not monthly robust:
  - Jul comp<7: 31R / 11 hits / ROI 158.43%.
  - Aug comp<7: 24R / 5 hits / ROI 76.31%.
- Across LOW cuts 6.5-8.5, Jul-Aug pooled ROI can exceed 100 for a range, but August remains below 100 throughout the useful neighborhood.
- Jul-Aug HIGH side never reaches ROI 100 in the monotonic sweep; best HIGH-side pooled point is comp>=3.0 at ROI 83.56%.
- Conclusion: there is strong retrospective evidence that the market filter's sign changed in Jul-Aug, but **no robust single composite-odds inversion/cut is justified**.

### Interpretation / decision
- The evidence is consistent with a downstream opponent/ticket-coverage regime shift, especially lower `opponent_mass`, rather than deterioration of 4-head probability.
- This is diagnostic evidence, not proof of a stable future regime gate. Sample sizes are small (22 vs 23 high-comp races).
- No production threshold or market gate is changed from this run.
- Formal prospective ROI remains `NOT_COMPUTABLE`; closing odds remain retrospective diagnostic only.
- September 2026 outcomes remain `UNREAD`; v96 remains prohibited.

### Continuation already prepared
- Exact frozen production S-score overlay on the 164R **research-candidate** population has been implemented and trigger commit created:
  - script commit `9102c4c543b5fb031bb981e2f20e9ca923dc4751`
  - workflow commit `5ae95d325844b3a0cc0221c04185bb5a799f0194`
  - BEFORE handoff commit `93b39ca2c0a082b38fa039530b41b4359c42172c`
  - trigger commit `2729eb0f50eb7bd8311e83d43acca8e3f68641b8`
- Goal of next run: determine whether Jul-Aug comp>=7 research races already fail frozen production `PRE>=.28 / POST>=.25 / ENV_ENTRY>=.224790` before results. Thresholds remain fixed; this is overlay/diagnostic only.

Status: `MARKET_REGIME_COMPLETE__PRODUCTION_S_OVERLAY_TRIGGERED`


## USER PRIORITY — 2026-09-18 — volume preservation first
- User preference: **できるだけ買うレース数は減らさず、ROIを上げたい**.
- Research objective is therefore changed from pure ROI maximization to a volume-preserving Pareto objective.
- Priority order:
  1. avoid reducing total BET race count where possible;
  2. if removal is unavoidable, minimize removed current BET races;
  3. replace removed weak races with stronger PASS-race rescues when possible;
  4. only then optimize retrospective ROI;
  5. prefer broad/neighboring parameter plateaus and monthly stability over an isolated maximum.
- Do not promote a rule merely because aggregate Apr-Aug ROI is high.
- Apr-Jun remains development / Jul-Aug remains fixed retrospective validation for research.
- September outcomes remain UNREAD; production unchanged until explicit approval.

### Immediate research design
1. **Expansion-only ceiling**: keep every current comp>=7 BET and add rescue races. This tests whether ROI can improve without removing a single race.
2. **Minimal-removal rotation**: if expansion-only cannot restore ROI, drop the smallest possible weak subset of current BETs and replace them with stronger PASS races using only pre-result observables.
3. Candidate observables stay simple: head_prob, opponent_mass, composite_odds; original-exhibition is not prioritized because prior ablation showed weak validation benefit.
4. Report, for every candidate:
   - current BET kept / removed,
   - rescue BET added,
   - final BET R and volume ratio,
   - Apr-Jun ROI,
   - Jul-Aug ROI,
   - Jul and Aug separately,
   - monthly minimum ROI,
   - neighboring-threshold stability.
5. Explicitly determine the **minimum number/share of current BETs that must be removed** before Jul-Aug retrospective ROI can reach >=100 while keeping final race count near or above baseline.

Status: `VOLUME_PRESERVING_ROTATION_RESEARCH_START`


## VOLUME-PRESERVING ROI RESEARCH — interim exact replay from official Run 35302541048 artifact
User priority: reduce BET race count as little as possible, but raise ROI.

### 1) Expansion-only ceiling
- Keep every current comp>=7 BET and only add rescue races.
- Across the audited rescue grid, Jul-Aug retrospective ROI cannot reach 100%.
- Best Jul-Aug expansion-only point is approximately:
  - final 55R
  - ROI 88.89%
  - rescue: head_prob>=0.20 / opponent_mass>=0.375 / no lower comp cut
- Conclusion: **zero-removal expansion is insufficient**. Some current high-comp BET replacement is necessary if the goal is ROI>=100 in Jul-Aug.

### 2) Minimum-removal hindsight attribution
These are Jul-Aug outcome-aware diagnostics only; NOT eligible for direct promotion.
- Pooled Jul-Aug ROI>=100 while final R>=current 23R:
  - minimum current BET removals: 6/23
  - rescue additions: 26
  - final 43R
  - ROI ~101.27%
  - but August remains only ~59.87%, so monthly stability fails.
- Requiring both July and August ROI>=100 while final Jul-Aug R>=23:
  - minimum current BET removals: 18/23
  - rescue additions: 30
  - final 35R
  - Jul ROI ~113.10%
  - Aug ROI ~100.76%
  - pooled Jul-Aug ROI ~108.52%
- Interpretation: total race count can be preserved/increased, but the old high-comp portfolio itself would need substantial rotation. A tiny prune is not enough for both months.

### 3) New Apr-Aug NON-PRISTINE model-selection candidate
Because Jul/Aug are already research-exposed, a NEW candidate may use Apr-Aug for model selection while keeping September fully UNREAD.
Selection constraints:
- Apr-Jun final R >= current 22
- Jul-Aug final R >= current 23
- total final R >= current 45
- overall retrospective ROI > current 124.8622%
- maximize 5-month minimum ROI first, then overall ROI, then R

Balanced selected rule from the exact 164R replay:
- KEEP current BET only when `opponent_mass >= 0.425`
- ADD current PASS when:
  - `head_prob >= 0.22`
  - `opponent_mass >= 0.375`
  - `composite_odds >= 3.0`
- no additional drop-head-probability condition

Balanced result:
- current baseline: 45R / retrospective ROI 124.86% / monthly floor 0%
- balanced candidate: **77R / retrospective ROI 141.17% / monthly floor 85.80%**
- Apr-Jun: 53R / ROI 133.49%
- Jul-Aug: 24R / ROI 158.12%
Monthly:
- Apr: 15R / ROI 197.63%
- May: 20R / ROI 88.81%
- Jun: 18R / ROI 129.69%
- Jul: 16R / ROI 194.29%
- Aug: 8R / ROI 85.80%
This candidate improves both total race volume and aggregate ROI, and removes the 0%-ROI months, but still has May/Aug below 100. Therefore it is a **research candidate**, not production proof.

Neighborhood evidence around selected point:
- selected neighborhood uses drop_mass .40/.425/.45, rescue_head .20/.22/.24, rescue_mass .35/.375/.40, rescue comp 0/3/3.5.
- multiple neighboring cells remain above current overall ROI with >=45R; the selected cell is chosen for the best 5-month ROI floor under the no-volume-reduction constraints.
- further reproducibility/Actions audit is required before any promotion.

### GitHub implementation
- volume-preserving rotation audit script: `6f5398d5788bb4a1f9a78fc82a99c0755d600d41`
- workflow: `237558a54fba1cea072d0c104d5295f01f505330`
- trigger: `a1b4c01b6dcdbbb18c02afe18e946407cef1033c`
- balanced selection audit script: `b05fa95145c2edb6b7fd876cb72481407aef8313`
- balanced workflow: `75bac232a1a3def4a6b4a25fa8a43b93a31b9b7c`
- balanced trigger: `1f68f9d95ec0ce77cf4e863366df07ac7cd679d9`

### Guardrails
- All figures above use archived/closing odds retrospective diagnostics only.
- Formal prospective ROI remains NOT_COMPUTABLE.
- September 2026 outcomes/results remain UNREAD.
- Production remains unchanged pending reproducibility audit and explicit promotion decision.

Status: `VOLUME_ROI_BALANCED_CANDIDATE_TRIGGERED`


## USER UPDATE — 2026-09-18 — increase race count beyond 77R
User explicitly wants **more races than the current 77R balanced candidate** while still raising/maintaining ROI.

### BEFORE
Objective for this continuation:
1. treat 77R as the previous balanced reference, not the target ceiling;
2. explore higher-volume frontiers around 90R / 100R / 110R / 120R;
3. require overall Apr-Aug retrospective ROI to remain above the current baseline 124.8622%;
4. prefer candidates with stronger 5-month ROI floor and neighboring-threshold support;
5. quantify the volume-vs-stability tradeoff rather than maximize one metric only;
6. keep September 2026 outcomes/results strictly UNREAD;
7. do not change production without explicit user approval and a successful reproducibility audit.

Status: `HIGHER_VOLUME_FRONTIER_RESEARCH_START`


## HIGHER-VOLUME CONTINUATION — 2026-09-18 AFTER
User asked to increase race count beyond the 77R balanced candidate.

### A. Re-rotation higher-volume frontier
A finer Apr-Aug NON-PRISTINE search was added for 100R+ profiles.
Primary search constraint:
- final R >= 100
- overall Apr-Aug retrospective ROI > current baseline 124.8622%
- 5-month minimum ROI >=75%
- maximize overall ROI, then volume

Current exact replay candidate:
- **110R**
- retrospective ROI **141.32%**
- 5-month floor **77.05%**
- removed current BET 17R / added rescue 82R
- rule:
  - keep current unless BOTH opponent_mass < .400 and head_prob < .26
  - add current PASS when head_prob >= .22 / opponent_mass >= .325 / composite_odds >= 2.5
- monthly:
  - Apr 19R / 318.96%
  - May 23R / 77.22%
  - Jun 20R / 150.15%
  - Jul 31R / 109.57%
  - Aug 17R / 77.05%
- local neighborhood around this point contains multiple 100R+ / baseline-beating / floor>=75 cells, so this is not an isolated single cell.

GitHub:
- BEFORE handoff: `a56861adb51b014ed893d09fccffcbfeacd5f791`
- audit script: `31d0c108c3c7ab8dffbb3dd27a27539d3d35dcee`
- workflow: `0304f91c03c48a0b51be54e73ca5e5f5c9790c82`
- trigger: `ede7968a321d4f8ea4b9442d11b4f56395295ee5`

### B. Preferred interpretation of user's request: nested expansion from the 77R candidate
Because the user asked for **more races**, not necessarily replacement of the 77R set, a second audit was added that NEVER removes a race from the 77R balanced candidate and only adds races outside it.

Base 77R is preserved exactly:
- current BET kept when opponent_mass >= .425
- current PASS added when head_prob >= .22 / opponent_mass >= .375 / composite_odds >= 3.0

#### Stable nested profile
- preserve all 77R
- add 16R -> **93R**
- retrospective ROI **128.65%**
- 5-month floor **79.83%**
- extra gate: head_prob >= .20 / opponent_mass >= .375 / composite_odds >= 2.5
- monthly exact local replay:
  - Apr 16R / 185.28%
  - May 22R / 80.73%
  - Jun 20R / 116.72%
  - Jul 23R / 170.92%
  - Aug 12R / 79.83%
- This is the maximum-R nested profile found while retaining overall ROI above current 124.8622% and every month >=75%.

#### High-volume nested profile
- preserve all 77R
- add 33R -> **110R**
- retrospective ROI **137.24%**
- 5-month floor **72.77%**
- extra gate: head_prob >= .23 / opponent_mass >= .2625 / composite_odds >= 2.5
- monthly exact local replay:
  - Apr 18R / 282.78%
  - May 24R / 74.00%
  - Jun 19R / 158.05%
  - Jul 31R / 126.37%
  - Aug 18R / 72.77%
- neighboring extra_mass .25/.2625/.275 around this gate gives very similar 110-111R behavior, so the point is not purely isolated.
- This profile is more faithful to the user's request because **none of the 77R candidate races are removed**.

GitHub:
- nested audit script: `97147b60862eb63ed63b899b1abbda2006325305`
- workflow: `2fcfa34ec028a5400976b97855beafa9264391b3`
- trigger: `617887e3302d28c94866f666d987e53104e8c32e`

### Current research preference
- Stability-first expansion: **93R nested**
- Volume-first expansion: **110R nested**
- Re-rotation 110R has slightly higher ROI/floor than nested 110R but changes/removes some of the original 77R choices.
- Given the user's stated preference to increase race count, the **nested family is preferred conceptually** unless later reproducibility evidence rejects it.

### Guardrails / status
- All ROI here is retrospective closing-odds diagnostic.
- Formal prospective ROI: NOT_COMPUTABLE.
- September 2026 outcomes/results remain **UNREAD**.
- Production remains unchanged.
- Both new Actions workflows have been trigger-committed; run IDs/artifacts must still be verified before any promotion.

Status: `HIGHER_VOLUME_NESTED_AUDITS_TRIGGERED__AWAIT_RUN_VERIFICATION`


## USER CONTINUATION — 2026-09-18 — target 110–130R with better monthly floor
User approved continuation and wants still more race volume.

### BEFORE
New research target:
- preserve the full 77R balanced candidate;
- add races only (nested expansion);
- focus on 110–130R;
- overall Apr-Aug retrospective ROI must stay above current baseline 124.8622%;
- explicitly search for a rule where **every Apr-Aug month remains >=100% retrospective ROI** if possible;
- prefer a simple smooth quality score using existing pre-result observables over another brittle rectangular threshold;
- September 2026 outcomes/results remain UNREAD;
- production remains unchanged.

Planned simple score family:
`quality = head_prob + weight * opponent_mass`,
combined with a minimum composite-odds floor and always OR-ed with the frozen 77R research candidate.

Status: `NESTED_LINEAR_SCORE_FRONTIER_START`


## NESTED LINEAR HIGH-VOLUME FRONTIER — 2026-09-18 AFTER
The higher-volume continuation found a materially better shape than the rectangular nested gate.

### Preferred 120R research profile
Preserve **all 77R** from the prior balanced candidate, then add races satisfying:
- `composite_odds >= 2.5`
- `head_prob + 1.50 * opponent_mass >= 0.82`

Retrospective Apr-Aug diagnostics:
- **120R**
- +43R beyond the 77R base
- overall ROI **127.7217%**
- Apr-Jun: 71R / ROI **134.7028%**
- Jul-Aug: 49R / ROI **117.6061%**
- monthly floor: **101.75%**

Monthly:
- Apr: 22R / **158.14%**
- May: 28R / **133.95%**
- Jun: 21R / **111.16%**
- Jul: 31R / **126.81%**
- Aug: 18R / **101.75%**

This is the first current high-volume nested candidate in this line that:
1. keeps every 77R base race,
2. reaches ~120R total,
3. remains above the original current-policy aggregate ROI baseline (124.8622%),
4. and has **all five Apr-Aug months >=100% retrospective ROI**.

### Frontier tradeoff
- 115R stability profile:
  - comp>=2.5
  - score `head_prob + 1.50*opponent_mass >= .83`
  - ROI **133.27%**
  - monthly floor **107.74%**
- 120R preferred:
  - score >= .82
  - ROI **127.72%**
  - monthly floor **101.75%**
- 127R volume profile:
  - comp>=2.5
  - `head_prob + 1.65*opponent_mass >= .8525`
  - ROI **128.32%**
  - monthly floor **96.39%** (Aug 96.39)
- 130R aggressive profile:
  - comp>=2.5
  - `head_prob + 1.75*opponent_mass >= .8825`
  - ROI **125.36%**
  - monthly floor **91.58%** (Aug 91.58)

Interpretation:
- 120R is the clean boundary where the research replay still keeps every month >=100.
- 127R is viable only if accepting a sub-100 August.
- 130R is too close to the aggregate baseline for the added instability.

### Fine-grid robustness
Fine search around comp 2.30–2.70, weight 1.20–1.80, score threshold .70–.95:
- maximum R with **all five months >=100** is 121R.
- the 121R max uses lower comp floor ~2.30–2.40 and is therefore less clean than the 120R comp>=2.5 profile.
- local 120R neighborhood (comp=2.5, weight 1.40–1.60, nearby thresholds):
  - 107 cells checked;
  - 55 cells have 115–125R, ROI above 124.8622%, and monthly floor >=95%;
  - 43 cells have 115–125R, ROI above 124.8622%, and all five months >=100%;
  - 6 nearby parameterizations reproduce the exact same 120R selected set.
This materially reduces concern that 120R is a one-cell threshold accident, although Apr-Aug is still fully non-pristine.

### GitHub
- BEFORE handoff: `772c0ca58465b480e1e81aeeece0ce452d4bbf65`
- linear frontier audit: `680da10cfcaad125ef61adba980268f6115bc40d`
- workflow: `a1dde6f591eabb714957e9354adc37f6cdc01f9c`
- first trigger: `1ae08ba67852b59d3e7568e43d99f8ebbdccbc16`
- frozen research-candidate JSON: `c132f8950382dee0ced6198b2054e10929f5bec0`
- rerun trigger after freeze: `32768422d453d7fa7ef924acb3738f922b208c8a`

### Decision
- **Research preference now moves from 110R nested to 120R nested-linear.**
- Do not promote to production yet.
- Next required step is independent Actions/replay verification of the frozen 120R JSON and, if it reproduces, prepare a live-safe implementation that computes the score from already-available pre-result inputs.
- Formal prospective ROI remains NOT_COMPUTABLE.
- September 2026 results remain **UNREAD**.
- Production remains unchanged.

Status: `HEAD4_120R_NESTED_LINEAR_FROZEN_RESEARCH__AWAIT_INDEPENDENT_REPLAY`
