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


## USER REQUEST — 2026-09-18 — leakage audit alongside 120R replay
User explicitly requested a **リーク監査** together with the independent 120R replay.

### BEFORE — leakage audit scope
Audit the frozen 120R research candidate on four separate dimensions:
1. **Outcome leakage**: verify no result / finishing-order / payout / hit fields enter the selection rule or upstream score features for the same race.
2. **Temporal leakage**: verify model/state inputs used for `head_prob` and `opponent_mass` are trained/frozen only on data available before the scored race; check any rolling/aggregate feature construction for same-day/future contamination.
3. **Market timing leakage**: identify whether `composite_odds` uses closing/final odds and therefore is retrospective-only; distinguish this from result leakage. Any production/live implementation must replace it with a timestamped pre-deadline odds snapshot or explicitly remain diagnostic-only.
4. **Selection / research leakage**: document that Apr-Aug was used to select/tune the 120R thresholds, so Apr-Aug ROI is NON-PRISTINE and cannot be treated as an independent holdout. September outcomes remain UNREAD and are the untouched future test.

Required outputs:
- source/provenance map for `head_prob`, `opponent_mass`, `composite_odds`;
- forbidden-column scan and same-row dependency checks;
- training cutoff / artifact cutoff checks;
- explicit PASS / WARN / FAIL per leakage class;
- independent 120R membership replay and parity hash;
- no production change.

Status: `HEAD4_120R_REPLAY_PLUS_LEAKAGE_AUDIT_START`


## LEAKAGE AUDIT — interim verified evidence while Actions replay runs
### Existing dynamic head-probability leakage audit
- Workflow Run: `35234326600`
- Job: `105246227265`
- Conclusion: SUCCESS
- Artifact: `10503431028` / `head4-boatracecsv-leakage-audit`
- Artifact digest: `sha256:a51cb2320691ca816f4eac9852027cb6b62aca64f44514a53273ad0516ee02a9`
- Current `audit_4head_boatracecsv_headprob_leakage.py` blob SHA is exactly unchanged from that run:
  `24b5a2e7748d50707dd6882577eddb5ef2d3451b`
- Dynamic result:
  - Apr-Jun training rows: 13,221 / boat4 wins 1,276
  - Jul-Aug model-validation rows: 9,610 / boat4 wins 964
  - features: 78 race-card-only model inputs
  - Jul-Aug AUC: **0.727090**
  - shuffled-target negative-control AUC mean: **0.503484**
  - September: UNREAD
- Interpretation: no evidence that same-race outcome labels are leaking into the `head_prob` feature matrix.

### Static/frozen-artifact causality checks completed
Frozen downstream artifact `artifacts/head4_v291_downstream_20260630.json`:
- frozen cutoff: 2026-06-30
- `jul_aug_labels_used=false`
- `september_labels_used=false`
- parity: PASS
- v283 max training date: 2026-06-29
- feature counts: POST 16 / ENV_ENTRY 25 / v283 SECOND 25 / v283 conditional THIRD 69
- no outcome/result/payout-like feature names found
- no odds-named frozen model features found

Causal source-order checks:
- motor history: current-day features are frozen before current-day results are ingested -> PASS
- player/motor priors: same-day feature rows emitted before daily results are ingested -> PASS
- exhibition ST bias history: bias is computed before same-day ST rows update history -> PASS

### Important warnings
1. **Market timing / odds proxy**
   - retrospective `composite_odds` and `current_bet` use `official_closing / closing_displayed`.
   - this is not result leakage, but it is NOT proof of an immutable pre-deadline market snapshot.
   - therefore Apr-Aug ROI remains retrospective diagnostic only.
2. **Model-selection leakage / non-pristine period**
   - Apr-Aug outcomes/ROI were used to select the 120R thresholds.
   - therefore Apr-Aug ROI is NOT an independent holdout result.
   - September remains the untouched future test.
3. **Retrospective sample-selection warning**
   - the fixed 164R reconstruction starts from historically settled rows requiring valid result / archived-odds coverage.
   - this is a coverage/sample-selection bias risk, not direct target leakage.

### Independent membership parity
- independently reconstructed 120R membership count: 120
- membership SHA256:
  `37057b43e344309e3fd06dfa1f2b519cfaad16379e92bfda51166da42834844c`
- this hash is now stored in the frozen 120R research artifact.

### Current unified audit
- script: `755993acb6a64d861433de4a4db985fe6f866bf2`
- workflow: `41fed51929861ac43daca905ff81107cf176c110`
- trigger: `9450106726151aa60d48bc773a1b82b9f411e05d`
- Actions Run: `35306188702`
- Job: `105478741668`
- current state at this handoff write: IN_PROGRESS
- 120R artifact leakage annotation commit: `6f70ac1a0871b7a480fda1cf63bce0263f2ed6cd`

Interim leakage conclusion:
- OUTCOME leakage: **PASS**
- temporal feature leakage: **PASS on audited contracts/frozen artifact**
- market timing: **WARN — closing odds proxy**
- Apr-Aug selection leakage: **PRESENT / NON-PRISTINE by design**
- September contamination: **PASS / UNREAD**
- production promotion: **BLOCKED pending unified run success + pre-deadline live implementation**

Status: `HEAD4_120R_LEAKAGE_AUDIT_RUNNING__INTERIM_PASS_WITH_WARNINGS`


## 120R CORE REPLAY — official Actions verification
The frozen 120R core replay has completed successfully while the leakage run continues.

- Run: `35305395486`
- Job: `105476437527`
- conclusion: SUCCESS
- Artifact: `10532065363` / `head4-nested-linear-high-volume`
- Artifact digest:
  `sha256:e0e68ff7befc42e011a2802b9dcf25392361346672d5255956136aa52263cd2c`
- Run head SHA: `32768422d453d7fa7ef924acb3738f922b208c8a`

Official replay confirms:
- fixed 164R population replay OK;
- base77 = 77R / ROI 141.1688%;
- preferred120 = **120R / ROI 127.7217% / 5-month floor 101.75%**;
- monthly:
  - Apr 22R / 158.1364%
  - May 28R / 133.9464%
  - Jun 21R / 111.1619%
  - Jul 31R / 126.8129%
  - Aug 18R / 101.75%
- fine-grid maximum with all five months >=100 is 121R; preferred remains 120R because it keeps the cleaner composite floor 2.5.
- selection period explicitly marked `2026-04..2026-08 NON_PRISTINE_MODEL_SELECTION`.
- September marker: UNREAD.
- production marker: unchanged.

Operational timing note:
- frozen v283 opponent features include current-race exhibition/ST/original-exhibition inputs (`cur_ex`, `cur_st`, `cur_orig_lap/turn/straight/avg` and conditional equivalents).
- Therefore the 120R rule is a **post-exhibition / last-minute decision rule**, not a pre-exhibition candidate rule.
- This is not leakage; it is a timing/availability constraint.

Status: `HEAD4_120R_CORE_REPLAY_SUCCESS__LEAKAGE_RUN_STILL_IN_PROGRESS`


## LEAKAGE AUDIT REPORT FROZEN
Dedicated report created:
- `HEAD4_120R_LEAKAGE_AUDIT_20260918.md`
- commit: `a0371c340f0fec709733d281a3e0a2105381bd6f`

Frozen audit conclusion:
- same-race outcome leakage: **PASS**
- temporal/future feature leakage: **PASS on audited code/artifact contracts**
- dynamic `head_prob` leakage/negative-control audit: **PASS**
- market timing: **WARN / NOT PROSPECTIVE** because archived `official_closing / closing_displayed` odds are a retrospective proxy
- Apr-Aug threshold-selection leakage: **PRESENT / NON-PRISTINE**
- retrospective sample-selection: **WARN**
- September contamination: **PASS / UNREAD**
- overall: `HEAD4_120R_LEAK_AUDIT_PASS_WITH_WARNINGS__RESEARCH_ONLY`

Additional operational constraint:
- `opponent_mass` uses current-race exhibition/ST/original-exhibition features, so 120R is a **post-exhibition last-minute** rule.
- For a future live-safe implementation, freeze the `head_prob` model state (feature list, imputer, scaler, coefficients) instead of refitting from an external historical source on each run; this is a reproducibility requirement, not a currently observed target leak.

Production blockers remain:
1. unified Run `35306188702` must finish successfully;
2. historical closing odds must not be treated as historical live snapshots;
3. live implementation must use immutable timestamped pre-deadline odds;
4. Apr-Aug ROI cannot be called independent holdout evidence;
5. September outcomes remain unread until the future evaluation checkpoint.

Status: `HEAD4_120R_RESEARCH_FROZEN__LEAK_AUDIT_PASS_WITH_WARNINGS__PRODUCTION_UNCHANGED`


## USER QUESTION — 2026-09-18 — can 4head pre-candidates be emitted?
Yes. The 120R rule itself is post-exhibition, but a separate broad pre-exhibition candidate layer can be built.

### BEFORE — pre-candidate design
Goal:
- emit candidates before exhibition;
- use no current-race exhibition / original-exhibition / last-minute odds;
- preserve as much recall of the frozen 120R final selections as possible;
- keep candidate volume practical enough for daily operation.

First exact pre-only parent gate, derived by removing only the exhibition-dependent filters from the audited 164R research population:
- `motor_win_diff_4v3 >= -0.0299361318939513`  (causal prior motor win-rate difference)
- `motor_2ren_diff_4v3 >= -7.08` (race-card motor 2-ren difference)
- `player4_all_win >= 0.215605` (causal prior player win rate)

Explicitly excluded from PRE candidate:
- `basic_complete`
- current exhibition time / current exhibition ST
- original exhibition
- `opponent_mass`
- `composite_odds`
- any result / payout fields

Audit objectives:
1. count all Apr-Aug pre-candidates from program-card/prior-only rows;
2. verify frozen 120R final selections are a subset;
3. calculate daily candidate distribution;
4. test optional pre-only `head_prob` tiers for smaller candidate lists while reporting final120 recall loss;
5. September outcomes remain UNREAD; production unchanged.

Status: `HEAD4_PRE_CANDIDATE_AUDIT_START`


## UNIFIED LEAKAGE RUN — FINAL
- Run: `35306188702`
- Job: `105478741668`
- conclusion: **SUCCESS**
- Artifact: `10531229990` / `head4-120r-leakage-and-replay`
- Artifact digest: `sha256:9994f3b23d8d723a6d294a48c5106ea13ecfb733e6a58e2d41b049d04c2cfcc5`
- independent membership replay: 120R
- membership SHA256: `37057b43e344309e3fd06dfa1f2b519cfaad16379e92bfda51166da42834844c`
- OUTCOME leakage: PASS
- TEMPORAL leakage: PASS
- MARKET timing: WARN closing-odds proxy
- MODEL selection: NON-PRISTINE Apr-Aug
- September: UNREAD
- production: unchanged

## PRE-CANDIDATE IMPLEMENTATION STATUS
- audit script: `472db83813a7b2f7bc64977e653512d612ab294c`
- workflow: `6539fa8adf516627439b08cbdec7c98790b4f442`
- trigger: `ee5fe25101912d6d437a7722a2228b090be61367`
- Run: `35310003505`
- Job: `105489898968`
- current status: IN_PROGRESS
- PRE wide rule uses only causal motor/player + race-card motor data and explicitly excludes current exhibition, opponent_mass, odds, result and payout.

Status: `HEAD4_PRE_CANDIDATE_RUN_IN_PROGRESS__LEAKAGE_FINAL_SUCCESS`


## PRE-CANDIDATE FAST AUDIT — official result
- Run: `35310772723`
- Job: `105492167010`
- conclusion: **SUCCESS**
- Artifact: `10533587079` / `head4-pre-candidate-fast-tiers`
- digest: `sha256:572a7b66b6d033432c33191e978d51fffd41aaae1b05dbd7b0a6e54d0bf0f27e`
- head SHA: `65e1a39c6c794a4d4cb46d73743881bca58b07f3`

### Wide pre-only parent
Uses only:
- causal motor win-rate difference
- race-card motor 2-ren difference
- causal player4 prior win rate
No current exhibition, odds, result or payout.

Result:
- 3,743 candidates / 153 calendar days
- avg **24.46R/day**
- median active day 25R
- p90 32R
- max 42R/day
- final120 captured **120/120 = 100%**
- all five months 100% recall

Conclusion:
- good as a guaranteed-recall parent universe,
- **too broad for user-facing daily candidate output**.

### Tightened pre-only tiers
95% overall recall:
- 3,555 candidates
- avg 23.24R/day
- 114/120 captured
- rule chosen by grid: `motor_win_diff_4v3 >= -0.0232551586`
- monthly recall falls to ~93.5–96.4%.

~90% overall recall:
- 3,186 candidates
- avg 20.82R/day
- 109/120 = 90.83%
- `player4_all_win >= 0.228915663`
- May/Aug recall drops to 85.71% / 83.33%.

Decision:
- raw motor/player-only PRE layer is not sufficient as the practical daily shortlist;
- use it only as a parent/fail-safe layer.
- next preferred route is the existing result-blind v250 PRE probability scorer and measure its frozen120 recall vs candidate volume.

v250 PRE recall audit:
- Run `35310957111`
- Job `105492712848`
- currently IN_PROGRESS.

Status: `HEAD4_PRE_WIDE_PARENT_100PCT_RECALL_TOO_BROAD__V250_PRE_RECALL_RUNNING`


## PRE-CANDIDATE DETAIL AUDIT — official result + practical-filter warning

### Detailed head_prob PRE audit
- Run: `35310003505`
- Job: `105489898968`
- conclusion: **SUCCESS**
- Artifact: `10533178842` / `head4-pre-candidate-for-120r`
- digest: `sha256:95ff090ac800265fb7db0145e60099d34c1cf2c96befaf83bb9b9a242ec2ff9a`
- wide parent: 3,743R / avg 24.46R/day / final120 recall 120/120.
- head_prob>=.10: 2,438R / avg 15.93R/day / 116/120 = 96.67% recall.
- head_prob>=.14: 1,770R / avg 11.57R/day / 112/120 = 93.33% recall.

### Existing v250 PRE model is NOT a good parent for frozen120
- Run: `35310957111`
- Job: `105492712848`
- conclusion: SUCCESS
- Artifact: `10533133682`
- fixed PRE>=.28: 702R / avg 4.59R/day but only 57/120 = **47.5%** recall.
- To reach 95% recall with v250 PRE alone requires PRE>=.135 -> 5,124R / avg 33.49R/day.
- Therefore v250 PRE score alone is not suitable as the 120R pre-candidate parent.

### Artifact-merge practical PRE research
Using the successful wide-pre artifact and successful leakage-audited head_prob artifact, a simple PRE-only rescue family was tested.

Clean practical rule candidate:
- first require the wide causal parent:
  - motor_win_diff_4v3 >= -0.029936...
  - motor_2ren_diff_4v3 >= -7.08
  - player4_all_win >= .215605
- then shortlist if:
  - `head_prob >= .14`
  - OR `motor_win_diff_4v3 >= .12 AND motor_2ren_diff_4v3 >= 3.0`
  - historical missing head_prob kept fail-open / NEEDS_SCORE
- result: ~1,935R / avg **12.65R/day**
- final120 captured 115/120 = **95.83%**
- monthly recall:
  - Apr 95.45%
  - May 96.43%
  - Jun 90.48%
  - Jul 100%
  - Aug 94.44%

### CRITICAL WARNING: recall alone is not enough
The 5 final120 races dropped by the practical 95.83% PRE shortlist contain:
- 2 boat4 heads
- **2 winning trifecta tickets**
- total retrospective payout 187,760 JPY
- those 5 omitted races alone retrospectively return 375.52%.

If the 120R final set is filtered by that PRE shortlist:
- 115R retained
- retrospective ROI falls from 127.72% to **116.95%**
- Jun retained subset ROI falls to ~51.49%
- Aug retained subset ROI falls to ~77.05%

Therefore the 95%-recall shortlist is **NOT approved** as a hard filter.
It can only be used as a display-priority tier unless the missed profitable races are rescued by another pre-only signal.

Specific missed winners:
- 202606192105: head_prob .0471 / motor_win_diff .0051 / motor_2ren_diff +20.1 / player4 win .2590 / payout 135,600
- 202608071409: head_prob .0928 / motor_win_diff -.0285 / motor_2ren_diff -1.6 / player4 win .2178 / payout 52,160

Next step:
- combine the leakage-audited head_prob with the existing v250 PRE score and other pre-only signals as OR-rescue;
- require preservation of historical winning final120 races / payout mass in addition to raw final120 recall;
- rerun v250 score persistence started at Run `35311685276`.

Status: `HEAD4_PRE_SHORTLIST_DISPLAY_ONLY__HARD_FILTER_REJECTED_PENDING_WINNER_RESCUE`


## PRE-DISPLAY DUAL-SCORE RESULT — 2026-09-18
The v250 PRE per-race score persistence rerun completed:
- Run `35311685276`
- Job `105494865314`
- conclusion: **SUCCESS**
- Artifact `10534055421` / `head4-v250-pre-recall-120r`
- digest `sha256:88451dbd23e0fbec29e074a307ddc8f042353d9c61b7199e74b09a4b7f277cd8`

By merging three already-successful audited artifacts:
- wide PRE parent,
- leakage-audited race-card `head_prob`,
- v250 PRE scores,

the best clean user-facing shortlist found is:

1. first require the 100%-recall wide causal parent:
   - `motor_win_diff_4v3 >= -0.029936...`
   - `motor_2ren_diff_4v3 >= -7.08`
   - `player4_all_win >= .215605`
2. DISPLAY candidate if:
   - `head_prob >= .18`
   - OR `v250_PRE >= .12`
   - historical missing head_prob is kept/flagged fail-open.

Apr-Aug historical diagnostics:
- **2,408 PRE display candidates**
- avg **15.74R/day**
- p90 active day 22R
- max 38R
- frozen final120 captured **119/120 = 99.17%**
- monthly final120 recall:
  - Apr 100%
  - May 96.43%
  - Jun 100%
  - Jul 100%
  - Aug 100%
- historical final120 trifecta ticket hits retained: **30/30**
- historical final120 payout retained: **100%**
- the only omitted final120 race is `202605132210`, which was a historical miss.
- retained 119R retrospective ROI = 128.79%, but this is outcome-exposed/non-pristine and must NOT be interpreted as validation improvement.

This is materially better than:
- v250 PRE alone: low recall at practical candidate counts;
- head_prob alone: practical cuts dropped known winning final120 races;
- 24.46R/day wide parent: 100% recall but too broad for user-facing display.

### Operational architecture decision
- **Internal monitoring parent**: wide causal 24.46R/day historical rate. This is the hard parent for post-exhibition scanning.
- **User-facing PRE shortlist**: dual-score rule above, ~15.74R/day historical rate.
- **PRE shortlist is DISPLAY PRIORITY ONLY, never a hard gate.**
- Post-exhibition 120R final scan must evaluate the full internal monitoring parent, allowing a race omitted from the PRE display to promote later.
- This prevents a pre-ranking miss from suppressing a valid last-minute BET.

Frozen research policy artifact:
- `artifacts/head4_120r_pre_display_policy_20260918.json`
- commit `056c2e579369522f32bbf030df7529ec491eb72f`

Caveats:
- Apr-Aug thresholds are outcome-exposed / NON-PRISTINE.
- v250 historical PRE is monthly walk-forward; prospective live semantics use the frozen cutoff through 2026-06-30.
- race-card head_prob must be frozen into a static inference artifact before live deployment.
- September outcomes remain UNREAD.
- production unchanged.

Status: `HEAD4_120R_PRE_DISPLAY_DUAL_SCORE_RESEARCH_FROZEN__LIVE_ARTIFACT_NEXT`


## PRE-CANDIDATE DESIGN — FINAL FOR THIS ITERATION
Dedicated design report:
- `HEAD4_120R_PRE_CANDIDATE_DESIGN_20260918.md`
- commit: `63b071bfe976c062aa4e0619efd11661a1cff16c`

Research policy artifact:
- `artifacts/head4_120r_pre_display_policy_20260918.json`
- commit: `056c2e579369522f32bbf030df7529ec491eb72f`

Current design:
- INTERNAL WATCH parent: ~24.46R/day historical, 120/120 final recall.
- USER PRE DISPLAY: wide parent AND (`head_prob>=.18 OR v250_PRE>=.12`).
  - ~15.74R/day historical
  - 119/120 final recall = 99.17%
  - monthly final recall floor 96.43%
  - historical final ticket hits retained 30/30
  - historical final payout retained 100%
- DISPLAY IS NOT A HARD GATE.
- Full watch parent must still be rescored after exhibition, so an unlisted PRE race can promote to final BET.

Local parity check for freezing race-card head_prob:
- fitting the unchanged audited model recipe on the official leakage-audit training rows (Apr-Jun, 13,221 rows / 78 features) reproduces stored audit probabilities with max abs error ~6.09e-14.
- This supports freezing a static race-card headprob inference artifact next.
- No production promotion yet.

Next resume point:
1. freeze static race-card head_prob model artifact through 2026-06-30;
2. implement research-only LIVE PRE display scanner using current race cards:
   - causal monitoring parent,
   - frozen race-card head_prob,
   - existing frozen-cutoff v250 PRE;
3. output shortlist by deadline/order;
4. keep full monitoring parent for post-exhibition 120R final scan;
5. use timestamped pre-deadline odds only at final market stage.

Status: `HEAD4_PRE_DESIGN_READY__NEXT_FREEZE_HEADPROB_AND_LIVE_SCANNER`


## USER APPROVED LIVE PRE TRIAL — 2026-09-18
User: 「まあ試してみよう」

### BEFORE / implementation state
Goal: run the new 4head 120R PRE design on **today 2026-09-18** without reading September outcomes.

Implemented:
- frozen race-card head_prob artifact:
  - `artifacts/head4_racecard_headprob_frozen_20260630.json`
  - commit `3feb7a6f64b9b0beba3d050b98351d161793f9a6`
  - fit Apr-Jun only, 13,221 rows / 78 race-card features
  - parity vs audited probabilities max abs error ~6.09e-14
- research-only LIVE PRE scanner:
  - `scan_4head_120r_pre_live.py`
  - commit `7778b1d490e5e178668592941fc5d82a1384e2ef`
- workflow:
  - `.github/workflows/trial-4head-120r-pre-live.yml`
  - commit `c52339380aa3910ed3c92f8c3ddcc94e82ecf697`

LIVE safety semantics:
- current race cards / Waku10 only for target day;
- current exhibition not used;
- current odds not used;
- race-card headprob is frozen through Jun-30;
- v250 labels frozen through Jun-30;
- wide-parent motor/player win-history state explicitly stops at Aug-31;
- no September result files are opened by the new scanner;
- display shortlist is NOT a hard gate; monitoring parent remains eligible for later post-exhibition promotion;
- production unchanged.

Next immediate action:
- trigger 2026-09-18 LIVE PRE trial;
- verify Run/Job/Artifact;
- report today's display shortlist and internal monitoring count.
Status: `HEAD4_120R_PRE_LIVE_TRIAL_READY_TO_TRIGGER`


## 2026-09-18 LIVE PRE TRIAL — corrected official result

First trial:
- Run `35314941417` SUCCESS
- but interpretation INVALID because almost all current rows hit `PARENT_MISSING_FAIL_OPEN` due player-name spacing mismatch between current API and historical cards.
- do NOT use its 179 watch / 50 display counts.

Fix:
- live parent player history keyed by **registration number** instead of display name.
- scanner commit: `50b1daa95cad6ebb13d840dea756d524ddc6bb2f`
- rerun trigger: `46602c34c62d25e8ba2971ecbeb5bd6eda4a3e41`

Corrected official run:
- Run `35317588703`
- Job `105512548374`
- conclusion: **SUCCESS**
- Artifact `10535553060`
- digest `sha256:5f6343f68b7bbabb3c661022223193ba7c37ea125268526241b0653ec2725dbf`

Corrected live PRE result for 2026-09-18:
- current universe: **180R**
- internal monitoring parent: **29R**
- user-facing PRE display: **19R**
- parent feature missing: **0R**
  - motor win prior missing 0
  - motor 2-ren missing 0
  - player prior missing 0
- September result files read: false
- current exhibition used: false
- current odds used: false
- production unchanged

Display candidates:
- 戸田6R 片岡雅裕 — head_prob .247 / v250_PRE .245
- 江戸川10R 野中一平 — .185 / .119
- 多摩川1R 竹田和哉 — .120 / .122
- 多摩川2R 若林将 — .071 / .122
- 多摩川5R 中山将 — .022 / .125
- 多摩川6R 丸野一樹 — .141 / .156
- 多摩川10R 松田大志郎 — .102 / .176
- 蒲郡4R 竹間隆晟 — .402 / .231
- びわこ5R 中野希一 — .174 / .231
- びわこ10R 谷村一哉 — .154 / .147
- びわこ12R 佐藤博亮 — .060 / .147
- 住之江4R 桑原悠 — .349 / .360
- 尼崎3R 峰重力也 — .186 / .178
- 尼崎5R 村岡賢人 — .266 / .197
- 尼崎10R 榎幸司 — .142 / .140
- 児島6R 柳内敬太 — .285 / .133
- 宮島3R 平山智加 — .299 / .229
- 宮島5R 守屋美穂 — .219 / .193
- 大村6R 上條嘉嗣 — .204 / .148

Dedicated report:
- `HEAD4_120R_PRE_LIVE_TRIAL_20260918.md`
- commit `94885918509409f2c2f9797a8af3b465a00d333f`

Operational rule remains:
- 19R display is advisory only.
- all 29 internal-watch races remain eligible for post-exhibition 120R promotion.
- next step is to persist the 29R watch list cleanly and wire the post-exhibition final scanner to it.
- final market gate must use timestamped pre-deadline odds, not historical closing odds.
- September outcomes remain UNREAD.

Status: `HEAD4_120R_PRE_LIVE_TRIAL_SUCCESS__19_DISPLAY__29_INTERNAL_WATCH`


## USER RULE UPDATE — 2026-09-18 — September may be used for LIVE learning/history
User explicitly clarified that this is an operational model and **September 2026 data may be included in learning/history updates**.

Revised causality rule for LIVE operation:
- Results from **completed prior dates**, including September dates before the target date, MAY be used for causal model/history state.
- Current target race result/payout must never be read before the decision.
- Current target-day same-race result remains prohibited.
- Do not use future races/results relative to the decision timestamp.
- Historical September data may be used for operational updating, but any retrospective performance claim must clearly state the training/evaluation overlap and must not be described as untouched holdout evidence.

This supersedes prior handoff statements that required September outcomes to remain entirely UNREAD for LIVE operation.

Immediate consequence:
- the previously noted blocker that `build_4head_player_history_live.py` and other causal history builders may read 2026-09-01..target_date-1 is **no longer a blocker**, provided they remain strictly date-causal and do not read target-day/future outcomes.
- Continue to fail closed on target-race result/payout access before decision.
- Production/live optimization may now update causal states through the previous completed day.

Status: `HEAD4_LIVE_SEPTEMBER_HISTORY_ALLOWED__TARGET_RACE_RESULT_STILL_FORBIDDEN`


## POST-EXHIBITION LIVE HARDENING — AFTER
User concern: exhibition-after decision often errors or arrives too late.

### Final finding from live tests
The computational path is fast enough. The historical failures were mostly plumbing/input problems, not model inference cost.

Fast architecture:
- once-daily causal state through prior completed day (September prior results allowed);
- pre-arm runner before exhibition;
- fetch exhibition sources in parallel;
- frozen v283 inference only;
- THIRD .10 expansion + opponent_mass;
- official odds3t and BOATCAST odds in parallel;
- 120R rule;
- fail closed before deadline safety margin.

### Measured daily-state cost
Run `35322680749`:
- daily state ~3.52 sec
- history through Sep17
- 47,520 settled prior races / 1,641 players

Run `35323003067`:
- daily state ~4.16 sec

This is a once-daily/pre-race cost.

### Bugs found/fixed
- legacy live import pulled unrelated heavy pandas chain -> decoupled: `ff201458...`
- stale legacy references after decoupling -> `5f669def...`
- tuple/string ticket mix -> `d51f0d7c...`
- BOATCAST original wrapped records -> `02af3c2c...`, test `ff0d529f...`
- BOATCAST od3 requests auto-decoding split Japanese name bytes as line breaks -> force UTF-8-sig: `5b2a504f...`
- official/BOATCAST odds were serial -> parallel first-complete source: `e131abfd...`

### Odds parser verification
Diagnostic:
- Run `35323673970` SUCCESS
- observed BOATCAST od3:
  - 8 lines
  - data=/1 header
  - 6 racer rows
  - racer name + 20 odds + 5 trailing zeros

Parser verification:
- Run `35324173389`
- Job `105533279813`
- SUCCESS
- fixture 120/120
- live 大村6R 120/120
- combo ordering fixture checked

### Successful full path benchmark — 丸亀6R
- Run `35324180062`
- Job `105533301948`
- SUCCESS
- Artifact `10538226164`
- digest `sha256:00acc48a7671f800f88adc6bf18910d8646e77aa0801d3cdc1ec555f1500e64d`

Race was not monitoring-parent -> intentionally `BENCHMARK_ONLY`.

Timing:
- start ~17:24:25
- final freeze 17:25:03.355
- configured deadline 17:34
- total runner 36.884 sec
- exhibition wait/fetch/build 33.621 sec because runner started before exhibition publication
- v283 input 0.00034 sec
- v283 inference 0.00164 sec
- odds fetch 3.174 sec

Interpretation:
- once exhibition is available, model + market path is ~3.2 sec in this test.
- v283 compute itself is ~0.002 sec.
- pre-arming before exhibition is preferable to starting after it.
- fail closed rather than wait through T-30/T-45 sec.

Benchmark values:
- head_prob .07504
- opponent_mass .41208
- composite 76.98
- linear .69316
- selected false
- target result/payout unused.

Dedicated report:
- `HEAD4_120R_POST_EXHIBITION_LIVE_HARDENING_20260918.md`
- commit `2841b127aad63a52d51169f947259fefecb7eb2a`

### Decision
- infrastructure/timing concern is substantially resolved;
- do NOT yet call production fully proven until a true monitoring-parent race runs end-to-end without benchmark override;
- production unchanged.
- user-approved September prior results may be used in causal state.
- if the race-card head_prob model itself is retrained on September labels, re-calibration/audit of the 120R threshold is required because score semantics change.

Status:
`HEAD4_120R_FAST_LASTMINUTE_INFRA_SUCCESS__TRUE_MONITORED_LIVE_NEXT`


## FAST POST-EXHIBITION LIVE HARDENING — 2026-09-18

User concern:
- post-exhibition decisions historically error or run too slowly to make the deadline.
- user explicitly clarified that September completed prior-date outcomes MAY be used for operational learning/history.

### Causal September rule
Operational LIVE now allows:
- completed prior dates, including Sep 1..target_date-1, in causal history/model state;
- NEVER target-race result/payout before decision;
- NEVER future-relative outcomes.
This supersedes the earlier blanket September-UNREAD rule for LIVE operation.

### Bottleneck found and fixed
Original daily state replay was slow because it fetched ~350 historical dates one-by-one from GitHub raw.
Replaced with local sparse checkout and local-file replay.

Measured daily-state cache:
- history through 2026-09-17
- settled races loaded: 47,520
- players: 1,641
- wall time: **4.18s** (another run 4.28s / 4.59s)
- this is intended to run once per day, not per race.

### Fast 120R last-minute path
New fast runner:
- `run_4head_120r_lastminute_fast.py`
- skips the heavy POST/ENV/A full chain for the 120R research/live rule;
- uses only:
  1. current race card + Waku10,
  2. daily causal player/ST state through previous day,
  3. current exhibition/direct-info sources,
  4. frozen v283 SECOND/conditional THIRD inference,
  5. opponent_mass,
  6. pre-deadline trifecta odds,
  7. frozen 120R selection rule.

Reliability additions present in latest runner:
- exhibition polling/retry;
- 4s request timeout;
- exhibition fail-closed safety margin: 75s before deadline;
- odds polling/retry;
- official BOAT RACE + BOATCAST odds are fetched in parallel;
- first complete 120-combo source wins;
- odds fail-closed safety margin: 45s before deadline;
- unavailable data => `NO_BET_DATA_NOT_READY`, never stale/incomplete BET;
- target result/payout never read.

### Actual pre-deadline benchmark
Official schedule: Gamagori 6R deadline 17:48 JST.
Run:
- `35326011735`
- Job: `105539098237`
- conclusion: SUCCESS
- Artifact: `10538984321`
- digest: `sha256:7adcb4b75c29c2ec48cd20a28a2706e0fbd69857f74f6b98b193f99960182c3e`
- run head SHA: `265921a616b239fcc27ee08af5dd90184de52518`

Timing:
- daily state: **4.18s**
- fast last-minute runner wall: **5.18s**
- exhibition fetch + build: **0.521s**
- v283 input build: **0.00033s**
- v283 inference: **0.00168s**
- odds fetch: **4.238s**
- decision timestamp: **17:46:22.302 JST**
- deadline: **17:48:00 JST**
- completed about **97.7s before deadline**

Important failure/fallback evidence:
- official BOAT RACE odds source timed out at 4s;
- BOATCAST parallel odds source succeeded in the same first polling round;
- `fallback_used=true`;
- `odds_attempts=1`;
- exhibition attempts=1.
This demonstrates the fallback path actually works under a real official-source timeout.

The benchmark race was not in the 29R internal parent, so its semantic output was `BENCHMARK_ONLY`; however the full exhibition/v283/odds timing path is identical to a monitored race. No betting decision was promoted from this benchmark.

### Workflow-start overhead
The one-off GitHub Actions test was created at ~17:45:37 and decision completed 17:46:22, about 45s end-to-end including:
- runner allocation,
- checkout/setup,
- package install,
- sparse historical checkout,
- daily state generation,
- final 5.18s decision.

For real operation, daily state and PRE inputs should be prepared once in the morning so per-race workflow does not repeat history checkout/cache creation.

### Current confidence / remaining work
- Core inference speed: PASS.
- Live predeadline fetch + inference: PASS.
- Official odds timeout fallback: PASS.
- Missing-data fail-closed: PASS.
- Target-result causality: PASS by code contract.
- Remaining hardening:
  1. bundle daily state into the morning PRE artifact;
  2. remove sparse history checkout from per-race runs;
  3. trim per-race dependencies to lower Actions startup;
  4. run the same actual-deadline test on one of today's true 29R monitoring-parent races when its exhibition is available.
- Future monitored candidates from today's 29R still upcoming at this point include e.g. Marugame 10R, Omura 6R, Gamagori 11R; display/watch status must be taken from the corrected PRE artifact.

Status: `HEAD4_120R_FAST_LASTMINUTE_PREDEADLINE_PASS__5P18S_CORE__CACHE_PREWARM_NEXT`


## FAST LAST-MINUTE RELIABILITY — FINAL UPDATE
Dedicated report:
- `HEAD4_120R_LASTMINUTE_RELIABILITY_20260918.md`
- commit `b31b717b418f6cc7b1452ae5453cc6ed57577f23`

Latest hardening commits:
- daily-state motor history: `23038945472ac21b9e7ab7460e232d0ddb9e28c0`
- PRE scanner accepts causal daily state through previous day: `294a07147f0e4e906dfb8c2fee2695e4c41bee1a`
- morning PRE workflow prewarms daily state: `1b587bf55c5def4336a5062e279335859913d1bb`
- fast runner odds-timeout + final safety guard: `60fafc4c237fa236e296fb062b88513cdbc7fdc2`
- prewarmed benchmark workflow: `00b5d1587c462c4a771fc640c6cb60d670e4024f`
- final rerun trigger: `a487d3aabba5050b8dfc8151b12a460d4d807fb1`

Latest actual-deadline prewarmed benchmark:
- Run `35326922081`
- Job `105542003899`
- conclusion SUCCESS
- Artifact `10539536100`
- digest `sha256:d08db8e50ed642d6686efd7fea8678e0f49616b1a6da84dc33b940dbafff645c`
- Marugame 7R deadline 18:02
- decision time 17:56:37.326
- last-minute runner wall **3.43s**
- exhibition **0.754s**
- v283 build+inference ~**0.0021s**
- odds **1.882s**
- Actions create -> decision about **21s**
- official odds source timed out at 1.5s; BOATCAST fallback succeeded
- final decision safety guard = 60s
- missing data remains fail-closed NO_BET.

Operational conclusion:
- the major historical latency problem is no longer model computation;
- PRE/day-state should be prepared once in the morning;
- per-race final path is now lightweight and has demonstrated actual pre-deadline completion twice;
- one test used a non-parent benchmark race, so a true monitored-parent live semantic BET/PASS example is still useful, but the technical path is identical.

September operational rule remains:
- completed prior September dates may be used causally;
- target-race result/payout and future-relative outcomes remain forbidden.

Status: `HEAD4_120R_FAST_LASTMINUTE_HARDENED__3P43S_CORE__21S_ACTIONS_E2E`


## ADDITIONAL LIVE SPEED EVIDENCE — Gamagori 7R
Additional actual-live benchmark after the reliability hardening:

- Run: `35327673270`
- Job: `105544450846`
- conclusion: **SUCCESS**
- Artifact: `10539547449`
- digest: `sha256:f3f82cfe358f5e15c1bdc025d8a1c860a6e769fd7b0c357b1493cae09d8f4b25`
- run head SHA: `12cf45287bd3673bff852e007a5b27297f52ac6b`
- benchmark target: 2026-09-18 Gamagori 7R
- official scheduled deadline: 18:17 JST
- decision timestamp: 18:05:43.826 JST
- headroom: ~676 sec / ~11m16s

Measured:
- daily causal state through Sep17: **4.63s wall**
- fast runner wall: **2.51s**
- runner internal total: **2.2298s**
- exhibition fetch/build: **0.5697s**
- v283 input build: sub-ms
- v283 inference: ~0.0018s
- odds fetch: **1.6230s**
- exhibition attempts: 1
- odds attempts: 1
- BOATCAST odds fallback used successfully

Benchmark semantics:
- target was not an internal monitoring-parent race, so output was intentionally `PERFORMANCE_BENCHMARK_ONLY`;
- the frozen 120R formula itself evaluated selected=true:
  - head_prob .11713
  - opponent_mass .55126
  - composite 7.6373
  - base77=true
  - linear score .94402
- no target result/payout was used.

Operational conclusion remains:
- computational latency is no longer the limiting factor;
- prewarm daily state in morning PRE workflow;
- typical post-exhibition model+market path demonstrated at ~2.2–5.2s in live tests;
- one-off Actions startup can add tens of seconds, but prewarmed workflow demonstrated ~21s create-to-decision;
- fail-closed guards prevent betting on stale/incomplete data or with insufficient deadline headroom.
- completed prior September dates are allowed in causal state; target-race/future outcomes remain forbidden.

Status: `HEAD4_120R_LASTMINUTE_SPEED_CONFIRMED__2P23S_ADDITIONAL_LIVE_BENCHMARK`


## BEFORE WORK — strict monitored fast-live workflow (2026-09-18 18:10 JST)
- Resume point: fast last-minute path has already passed actual predeadline latency/fallback benchmarks, including Run 35327673270 / Job 105544450846 / Artifact 10539547449.
- The only remaining live-semantic gap is one true internal `monitoring_parent=1` race completing the strict path to BET/PASS without `--allow-unmonitored-benchmark`.
- Corrected PRE Artifact 10535553060 / Run 35317588703 contains 29 internal monitoring-parent races for 2026-09-18. Current upcoming true parents include Marugame 10R (JCD15, deadline 19:39), Omura 6R (JCD24, deadline 19:56), and Gamagori 11R (JCD07, deadline 20:15).
- Build a reusable strict live workflow that consumes the frozen corrected PRE artifact and prewarmed causal daily-state artifact, rejects non-parent races, runs `run_4head_120r_lastminute_fast.py` without benchmark override, and uploads the full decision JSON/log.
- First smoke target: Marugame 10R. Because current time is well before exhibition, an immediate run is expected to fail closed as `NO_BET_DATA_NOT_READY`; that is a safety-path check, not the final BET/PASS proof.
- Preserve causal rule: prior completed Sep dates through Sep17 allowed; target-race result/payout/future outcomes forbidden. Production/research thresholds unchanged.


## AFTER WORK — strict monitored workflow created and fail-closed smoke passed
- New reusable workflow: `.github/workflows/live-4head-120r-true-monitor.yml`
  - workflow commit: `409960bbadaccb6c0a7fce9fd9607ecca72884a8`
  - accepts target/date/deadline and frozen PRE/state artifact identifiers by workflow_dispatch;
  - push trigger file: `.github/triggers/live-4head-120r-true-monitor.json`;
  - downloads corrected PRE + prewarmed daily state dynamically with `gh run download`;
  - runs `run_4head_120r_lastminute_fast.py` **without** `--allow-unmonitored-benchmark`;
  - contract asserts `monitoring_parent=true`, target result unused, payout unused, and decision is BET/PASS/NO_BET_DATA_NOT_READY.
- Initial trigger commit: `4f091f3efde1a9f371ab101f2df4c7b491d91883`.
- Strict monitored smoke target: 2026-09-18 Marugame 10R, official deadline 19:39 JST.
- Run: `35328561014`
- Job/check: `105547310818`
- conclusion: **SUCCESS**
- Artifact: `10539639044`
- Output:
  - race_code `202609181510`
  - `monitoring_parent=true`
  - head_prob `0.1011314922400658`
  - decision `NO_BET_DATA_NOT_READY`
  - not_ready_stage `EXHIBITION`
  - attempts 10 / elapsed ~31.3s
  - strict runner wall ~31.67s (intentional pre-exhibition polling window)
  - target_race_result_used=false
  - payout_used=false
  - contract check: `STRICT_MONITOR_CONTRACT_OK`
- Interpretation: strict internal-parent gating and fail-closed behavior are now proven on a true monitoring-parent race. This is **not yet** the final BET/PASS proof because the run was intentionally early (18:15 JST) and exhibition data was not published.
- Earliest remaining true-parent final candidates today from corrected PRE:
  1. Marugame 10R — deadline 19:39 JST
  2. Omura 6R — deadline 19:56 JST
  3. Gamagori 11R — deadline 20:15 JST
- Next resume point: rerun the same strict workflow once exhibition is available for one of those races; no code change should be needed. A successful complete-data run must end in semantic BET or PASS while retaining `monitoring_parent=true` and no target result/payout access.

Status: `HEAD4_120R_STRICT_MONITOR_GATE_AND_FAILCLOSED_PASS__FINAL_BET_PASS_PENDING_EXHIBITION`


## BEFORE WORK — true-parent complete-data benchmark while waiting for next live exhibition (2026-09-18 18:19 JST)
- Full corrected PRE artifact was unpacked and all 29 monitoring-parent rows inspected, including the 10 WATCH_ONLY hidden rows.
- There is no earlier remaining true parent before Marugame 10R. Upcoming order remains Marugame 10R 19:39, Omura 6R 19:56, Gamagori 11R 20:15.
- Since the prospective BET/PASS proof cannot exist before exhibition publication, use the otherwise idle interval to close a separate technical gap: run a **completed true monitoring-parent race** through the complete exhibition -> v283 -> odds -> frozen 120R path in `--performance-benchmark` mode.
- This benchmark must still reject non-parent rows, must not read target result/payout, and is explicitly not prospective / not a profitability proof. Its purpose is only to prove that a real `monitoring_parent=true` row can traverse complete current-data inputs and produce the internal selected/PASS state without the unmonitored override.
- Use Gamagori 4R (race_code 202609180704, monitoring_parent=true, head_prob ~0.4021) as the benchmark target because Gamagori current-source availability has already been demonstrated today.


## AFTER WORK — completed true-parent benchmark limitation identified
- Added benchmark workflow `.github/workflows/benchmark-4head-120r-true-parent-complete.yml` at commit `b4d9ac7b7ff90ff23ba4beb1cbfe5e47efac81e3`.
- Trigger commit: `552d0a07be252330e3356d274757f06f029d39ff`.
- Target: Gamagori 4R, a real corrected-PRE `monitoring_parent=true` row (race_code 202609180704).
- Run: `35329141795`
- Job: `105549161759`
- Artifact: `10540630528`
- Run conclusion: failure only because the benchmark intentionally required a complete current odds snapshot.
- What succeeded:
  - strict parent gate: `monitoring_parent=true`
  - exhibition fetch/build succeeded in ~0.712s
  - no target result/payout access
- What failed:
  - post-race trifecta odds are no longer available from either live source;
  - official source timed out and BOATCAST od3 returned status-not-ready/lines=2;
  - runner correctly ended `NO_BET_DATA_NOT_READY` at ODDS after ~15.1s rather than fabricating/staling odds.
- Important conclusion: a completed race cannot be used to manufacture the missing complete-data proof. This preserves the integrity of the prospective audit. The final real proof must be collected on an upcoming race while its pre-deadline odds/exhibition are live.
- At 18:19 JST all 29 internal parent rows were inspected; no earlier remaining true-parent race exists before Marugame 10R 19:39. Next are Omura 6R 19:56 and Gamagori 11R 20:15.
- Next required action is unchanged: execute the strict monitored workflow on Marugame 10R after exhibition publication and before the official deadline.

Status: `HEAD4_120R_POSTRACE_ODDS_NOT_RETAINED__PROSPECTIVE_TRUE_PARENT_PROOF_REQUIRED`


## BEFORE WORK — keep strict monitored job alive until exhibition or safety cutoff
- User approved changing the Marugame 10R live behavior so a 19:22 start does not stop after only ~30 seconds when exhibition is still unpublished.
- Change the reusable strict monitored workflow so one invocation keeps polling exhibition until either:
  1. complete exhibition data becomes available, then immediately continue v283 -> odds -> BET/PASS; or
  2. deadline headroom reaches the existing exhibition safety cutoff (75 seconds), then fail closed as NO_BET_DATA_NOT_READY.
- Keep 2-second exhibition polling, existing odds/final safety guards, strict monitoring_parent gating, and result/payout prohibition.
- Increase workflow timeout so the runner can remain alive across the full pre-deadline window.
- Update the scheduled 19:22 automation instructions to require this persistent-wait behavior.


## AFTER WORK — strict monitored workflow now waits until exhibition or safety cutoff
- Updated `.github/workflows/live-4head-120r-true-monitor.yml`.
- Commit: `fedaae1095990940b395acf33c1b20f85f74af23`.
- Workflow timeout increased from 10 to 25 minutes.
- One invocation now uses:
  - exhibition polling interval: 2s
  - exhibition safety cutoff: 75s before deadline
  - max exhibition wait: 1800s (therefore the safety cutoff, not a 30s timer, controls normal stopping)
  - odds safety cutoff: 45s
  - max odds wait: 15s
  - final decision safety cutoff: 60s
- For Marugame 10R starting at 19:22 and deadline 19:39, the job will remain alive if exhibition is not yet published. It will continue polling until exhibition becomes complete, then immediately run v283 -> opponent_mass -> live odds -> frozen 120R decision.
- If exhibition still is not complete by the 75-second safety boundary, it will fail closed as `NO_BET_DATA_NOT_READY`; it will not force a late/stale bet.
- The scheduled 19:22 task instructions were also updated to require this persistent-wait behavior.
- Strict parent gate and result/payout prohibition remain unchanged.

Status: `HEAD4_120R_STRICT_MONITOR_PERSIST_UNTIL_EXHIBITION_OR_75S_CUTOFF`


## BEFORE WORK — 4HEAD formal wall3 head-gate/rotation audit (2026-09-18)
- User approved testing the 1HEAD formal 3-vs-4 wall concept on the current 4HEAD model.
- Freeze the current 4HEAD 120R nested-linear rule and current v283 tickets. Do not retrain head_prob, opponent models, or change production/LIVE.
- Reuse the exact 1HEAD formal same-day wall semantics from `run_v352_1head_wall3_risk_audit.exhibition_wall`:
  - wall_score = .20*(EX3-EX4)+.40*(ST3-ST4)+.25*(straight3-straight4)+.15*(origavg3-origavg4)
  - negative wall_score means lane 3 is weaker than lane 4 / lane 4 has a more open attack path;
  - attack4_score uses the same component weights on boat 4.
- Historical audit population stays Apr-Aug 2026 only; September outcomes/results/payouts remain UNREAD.
- Baseline must exactly reproduce the frozen 120R research profile:
  - preserve the 77R base;
  - extra gate comp>=2.5 and head_prob + 1.50*opponent_mass >= .82;
  - expected 120R and previously recorded ROI/monthly profile.
- Primary new family is a **volume-preserving rotation of only the extra layer**, never removing the frozen 77R base:
  - quality_wall = head_prob + 1.50*opponent_mass + open_beta*max(0,-wall_score)*I(attack4>=A4) - block_beta*max(0,wall_score)
  - search nearby quality/comp thresholds and beta strengths;
  - target 115-125R, prefer ~120R, keep all base77.
- Report: R, changes vs base120, head4 rate, exact3 hits, retrospective ROI, Apr-Jun vs Jul-Aug, every month, monthly ROI floor, wall-score strata.
- Selection preference: higher monthly ROI floor first, then overall ROI/head4 rate, with smaller set churn and R closer to 120.
- This is retrospective research, not production proof. No automatic promotion even if improved.


## INTERIM — formal wall3 audit first result / fine rescue follow-up
- Official successful audit:
  - Run `35334723879`
  - Job `105566807656`
  - Artifact `10541624968`
  - head `1bc801f5f27e5bcbc5b178864546093a5b1f4496`
  - SUCCESS / AUDIT_OK / September outcomes unread.
- Frozen 120R reproduced exactly: 120R / head4 53 (44.17%) / exact3 30 / retrospective ROI 127.7217% / monthly floor 101.75%.
- Formal wall available for 144/164 research-universe races.
- Critical directional finding:
  - positive/strong wall3 is **not** a useful 4-head DROP signal. BASE120 wall_score>=.20 was 10R / head4 60% / exact3 50% / retrospective ROI 351.02%; penalizing positive wall generally worsened results.
  - therefore do NOT use the 1HEAD concept symmetrically as a strong-wall 4-head veto.
- Pure open-wall rescue at the **same frozen 120R thresholds** is promising:
  - keep every existing 120R;
  - comp>=2.5 / base quality threshold .82 unchanged;
  - add only `0.10 * max(0,-wall_score)` to extra-layer quality;
  - no attack4 minimum, no block penalty.
  - Result: **123R**, head4 **56/123 = 45.53%**, exact3 **31**, ROI **132.4943%**.
  - This is exactly +3 races vs base120, and all 3 added races were 4-head wins; one was an exact3 hit.
  - Added races: 202604251508, 202605110811, 202605181406. All are Apr-May development; Jul-Aug set is unchanged, so this is promising but not support-validated.
- A dev-selected 120R rotation (comp floor 2.7 + open beta .1) improved Apr-Jun but reduced Aug ROI to 91.76%; reject as current preference because it sacrifices the all-month >=100 property.
- Next follow-up: fine-grid **expansion-only** audit around open beta .025-.20 and nearby thresholds. Existing 120R must never be removed. Measure rescue-set stability/plateau and whether any Jul-Aug open-wall rescues can be added without breaking ROI/monthly floor.
- Production/LIVE unchanged.


## AFTER — 4HEAD wall3 formal + fine expansion audit complete
- Formal audit success:
  - Run `35334723879`
  - Job `105566807656`
  - Artifact `10541624968`
  - workflow head `1bc801f5f27e5bcbc5b178864546093a5b1f4496`
  - 8,820 grid cells / 2,681 eligible near-120 cells.
- Fine expansion-only audit success:
  - Run `35335191819`
  - Job `105568291313`
  - Artifact `10542531161`
  - workflow head `0a47a76f85d45563e64ee97bed079e08a7c2b49e`
  - 4,536 fine cells / 100 unique rescue sets / 180 non-deteriorating cells.
- Baseline reproduced exactly: 120R / head4 53 = 44.17% / exact3 30 / ROI 127.7217% / monthly floor 101.75%.
- Directional result:
  - **Strong/positive wall3 must NOT be used as a 4-head veto.** BASE120 wall_score>=.20 was 10R / head4 60% / exact3 50% / ROI 351.02%; block penalties generally worsened the portfolio.
  - **Weak/open wall3 is promising only as a one-way PASS rescue.**
- Clean canonical overlay that leaves the frozen 120R untouched:
  - current base quality = head_prob + 1.50*opponent_mass;
  - only for a current PASS: `wall_open=max(0,-wall_score)`;
  - shadow quality = base quality + **0.10*wall_open**;
  - require comp>=2.5 and shadow quality>=.82;
  - no block penalty; no attack4 minimum.
- Historical effect for that pure overlay:
  - base 120R stays intact;
  - +3 rescued races => **123R**;
  - head4 53 -> **56** (all 3 added races were 4-head wins);
  - exact3 30 -> **31**;
  - ROI 127.7217% -> **132.4943%**;
  - monthly floor stays **101.75%**.
- Rescue races:
  - 202604251508: quality .79358 / wall -.27 / 4-head / exact3 hit / payout-if-bet 97,020;
  - 202605110811: quality .81140 / wall -.64 / 4-head / exact3 miss;
  - 202605181406: quality .80636 / wall -.76 / 4-head / exact3 miss.
- Fine-grid robustness:
  - the exact 3-race rescue set reappeared in **110 nearby parameter cells**;
  - therefore it is not a one-cell threshold accident.
  - however all 3 rescues are Apr-May development; **Jul-Aug support added_R=0** for this clean profile.
  - support-expanding wall settings generally lowered August / total ROI; no evidence supports production promotion yet.
- Research conclusion:
  - wall3 is usable for 4HEAD, but in the opposite operational role from a symmetric gate:
    - do not DROP 4 because lane3 looks strong;
    - allow a **weak-lane3 open-path rescue shadow** for current PASS races.
  - keep current official BET/PASS unchanged until forward evidence exists.
- Next implementation: expose this canonical open-wall rescue as a research-only field in the fast last-minute JSON, with `production_applied=false`. No betting decision changes.
- September outcomes remain unread by these audits; production unchanged.

Status: `HEAD4_WALL3_OPEN_RESCUE_PROMISING__123R_SHADOW_ONLY__NO_SUPPORT_RESCUES`


## AFTER — wall3 open-rescue LIVE shadow implemented (research-only)
- Fast runner commit: `5068b5358640146553248d8ffd24705b70275306`.
- New output field: `wall3_open_shadow`.
- Canonical shadow profile:
  - `HEAD4_WALL3_OPEN_RESCUE_SHADOW_V1_BETA010_Q082_COMP250`
  - wall_score uses the exact formal 1HEAD weights EX .20 / ST .40 / straight .25 / orig_avg .15 for lane3-lane4;
  - open_risk = max(0,-wall_score);
  - base_quality = head_prob + 1.50*opponent_mass;
  - shadow_quality = base_quality + .10*open_risk;
  - only current PASS is eligible;
  - would_rescue when comp>=2.5 and shadow_quality>=.82.
- This field is explicitly `research_only=true` and `production_applied=false`; official selected/BET/PASS logic is untouched.
- Contract test workflow commit: `4db4eae6ca13ae1f3cc53aa3aa4999a9d700ee94`.
- Test Run `35335467918` / Job `105569167818`: **SUCCESS**.
  - weak lane3 synthetic case => shadow rescue true;
  - already-selected official BET => shadow rescue false;
  - strong lane3 => no veto/no rescue;
  - compile and production-applied=false assertions passed.
- Fine audit source:
  - Run `35335191819` / Artifact `10542531161`;
  - exact 3-race rescue set reproduced across 110 nearby parameter cells;
  - support_added_R=0, so keep shadow-only until forward evidence.
- No production thresholds, tickets, monitoring parent, or live decision semantics changed.

Status: `HEAD4_WALL3_OPEN_RESCUE_SHADOW_LIVE_READY__OFFICIAL_DECISION_UNCHANGED`


## INCIDENT / BEFORE — Marugame 10R scheduled task did not launch strict GitHub run; recover with Omura 6R
- Scheduled task last_run_time was 2026-09-18 19:24:04 JST, but no trigger-file mutation / strict GitHub Actions Run / Artifact was created for Marugame 10R.
- Therefore Marugame 10R has **no valid prospective final BET/PASS judgment**. Deadline 19:39 JST has passed; do not reconstruct it post hoc and do not read target result/payout to pretend a live decision.
- Root operational issue: the scheduled chat task executed, but it did not perform the GitHub trigger mutation required by the push-triggered workflow.
- Immediate recovery target: Omura 6R (JCD24), deadline 19:56 JST, already confirmed as a corrected-PRE monitoring_parent=true race.
- Trigger the existing strict monitored workflow directly by updating `.github/triggers/live-4head-120r-true-monitor.json`.
- Keep persistent exhibition polling / fail-closed safety cutoffs. Do not use benchmark override. Results/payout remain unread.


## AFTER — Marugame scheduler incident root fix: GitHub-native watchdog
- The prior ChatGPT one-time automation was not sufficient: it executed its prompt but did not mutate the trigger file, so Marugame 10R never got a strict GitHub Run.
- Root operational fix is now implemented **inside GitHub Actions**, so the final live launch no longer depends on a ChatGPT scheduled task.
- Added watchlist:
  - `.github/live/head4_120r_watchlist.json`
  - initial remaining target: Gamagori 11R, deadline 20:15 JST, watch window begins 20 minutes before deadline.
  - commit `e86f4e184da776fcdba962c6e17fa72c7f0be185`.
- Added workflow:
  - `.github/workflows/live-4head-120r-watchdog.yml`
  - GitHub cron every 5 minutes + workflow_dispatch + push trigger;
  - reads JST watchlist;
  - enters a target only during [deadline-20min, deadline-75sec);
  - once inside the window, starts the strict monitored runner and keeps polling exhibition every 2s;
  - same fail-closed safety cutoffs (exhibition 75s / odds 45s / final 60s);
  - checks existing target-named artifact to suppress duplicate completed decisions;
  - workflow-level concurrency prevents parallel duplicate watchdog decisions.
  - commit `be9bedf9b5f1f9663e2e27a7c03e7962885620bb`.
- Immediate validation:
  - Run `35336187123`
  - Job `105571450311`
  - SUCCESS
  - at 19:44:39 JST it correctly logged `WATCHDOG_NO_TARGET window` because Gamagori 11R's 20-minute window had not yet opened.
- This fixes the specific Marugame failure mode: no external chat reminder is needed to mutate a GitHub trigger at the right moment.
- Omura 6R recovery remains separately running from direct trigger Run `35335946046`.

Status: `HEAD4_LIVE_TRIGGER_ROOT_FIXED_GITHUB_NATIVE_WATCHDOG`


## WATCHDOG PRESSURE REDUCTION — 2026-09-18
- User correctly raised concern that a 5-minute 24h cron would create excessive Actions churn.
- Repository visibility confirmed **public**. Standard GitHub-hosted Actions minutes are therefore not billed, but run-count/queue/history pressure still matters.
- Watchdog cadence reduced:
  - from every 5 minutes, 24h = 288 scheduled runs/day;
  - to every 15 minutes during 09:00-21:59 JST only = at most 52 scheduled runs/day.
- No-target path is now minimal:
  - it reads the small watchlist through GitHub API before checkout;
  - actions/checkout, setup-python, dependency install, artifact download, and strict runner execute only when an actual target is inside its watch window.
- Target watch window widened from 20m to 35m so 15-minute cadence still leaves substantial pre-deadline headroom even in the worst alignment.
- Commits:
  - 7117a0ef388e70e025fb00e02ed2cbfeaa7754e4 — low-pressure schedule + no-target fast path
  - 0b4df4aba516b7d744b8c7a5a3fdaf39c2a93b0a — 35-minute watch window
- Rationale: preserve live reliability while reducing routine watchdog Actions creation by ~82% versus the initial 5-minute/24h design.

Status: HEAD4_WATCHDOG_LOW_PRESSURE_15MIN_DAYTIME_ONLY


## BEFORE — 4HEAD expanded-universe volume research (2026-09-18)
- User explicitly wants more final BET races than the current 120R line.
- Target is no longer limited to the fixed 164R research candidate; investigate expansion from the 100%-recall wide PRE parent.
- September 2026 target outcomes/results/payouts remain unread; historical research window stays Apr-Aug 2026.
- Preserve the existing frozen 120R membership as a mandatory base. New work is expansion-only unless explicitly reported otherwise.
- Stage 1 (lightweight): start from the wide causal parent:
  - motor_win_diff_4v3 >= -0.0299361318939513
  - motor_2ren_diff_4v3 >= -7.08
  - player4_all_win >= .215605
  - no current-result/payout fields in selection.
- Relax only the post-exhibition structural gates that created the old 164R:
  - st4_adv_inside around the frozen -0.60 boundary;
  - orig4_adv_inside around the frozen -0.057777... boundary;
  - keep basic_complete and required exhibition availability fail-closed.
- Goal of Stage 1: identify simple expanded post-exhibition pools around 250–600R with usable 4-head rate and stable monthly coverage, while proving the old 164R / frozen120 are subsets.
- Stage 2: on a selected expanded pool only, rerun frozen v283 SECOND/conditional THIRD, 4–6 tickets, opponent_mass, archived closing-odds retrospective diagnostics and nested final selection.
- Search final expansion targets around 180 / 200 / 220 / 250R while preserving all existing 120R.
- Rank candidates by: monthly ROI floor, overall ROI, head4 rate, then higher volume. Do not promote a profile merely from Apr-Aug hindsight.
- Existing wall3 shadow remains research-only and is not used to define the broad pool initially.
- Production/LIVE remains unchanged until separate approval.

Status: HEAD4_EXPANDED_UNIVERSE_VOLUME_RESEARCH_START


## AFTER — 4HEAD expanded-universe volume research (2026-09-18)
User requested trying to increase final BET volume beyond the frozen 120R line.

### Stage 1 — label-independent structural expansion
Implementation:
- `audit_4head_expanded_pool_stage1.py`
- script commits: `fccbd1a0a048f633076ed1d9211ddfbba0b47220`, local-mirror update `eecca4adf8548e1098ae852740143b691cf2bb9c`
- workflow commit: `623ebcbc3e632d2b85960de101e3b18c3918fff7`

Runs:
- first Run `35337572466` / Job `105575864985`: FAILURE because the initial assumed 250–650 structural pool did not exist.
- diagnostic fix commit: `47af824c3b19fb22979d00e04f359384ed097144`.
- successful Run `35337846162` / Job `105576723385`.
- Artifact `10544200764` / `head4-expanded-pool-stage1`.

Result:
- wide causal PRE parent: **262R**
- full structural data ready: **235R**
- frozen old164 reproduced exactly: **164R / 70 heads**
- largest simple expansion-only structural pool while retaining all 164R: **226R**
- chosen purely by target count (head outcomes NOT used):
  - `st4_adv_inside >= -0.80`
  - `orig4_adv_inside >= -0.35`
- selected pool: **226R / 87 heads = 38.50%**
- old164 recall: **164/164**
- monthly pool count: Apr33 / May51 / Jun37 / Jul59 / Aug46
- September outcomes read: false.

### Stage 2 — frozen v283 + archived official-odds expansion search
Implementation:
- `audit_4head_expanded_pool_stage2_v283.py`
- initial commit `5e725e724f25d76df04400ff3dcae0ca7a8e05ab`
- workflow `1df8e84278c3743318d0436cb7efa89d2f2c80b3`
- frozen headprob-artifact reuse:
  - script `9ba895189565268cae0ce9e534b509fc2d17c833`
  - workflow `60badb598e84f1ebc53d0ebf5608c8b0b16e9c09`
- first Stage2 runs failed on missing historical closing odds outside old164:
  - Run `35338111527` / Job `105577566689`: FAILURE
  - Run `35338685737` / Job `105579387897`: FAILURE
- failure was NOT v283-feature coverage. Example missing odds row `202607211502` was outside old164.
- corrected fail-closed semantics:
  - old164 missing odds => hard failure;
  - only expanded-outside-old164 rows without verified closing odds are excluded from ROI research.
  - fix commit `0884ca290e106e0b5494b04332a912945d59ea9e`.

Successful official Stage2:
- Run `35339005302`
- Job `105580381798`
- Artifact `10543978730` / `head4-expanded-pool-stage2`
- SUCCESS / `HEAD4_EXPANDED_POOL_STAGE2_OK`.
- 226R pool -> **208R with verified official closing odds**.
- 18 rows excluded fail-closed for missing closing odds; **all are outside old164**.
- old164/120 coverage remains intact.
- frozen120 parity exactly reproduced:
  - 120R
  - 53 heads = 44.17%
  - exact3 30
  - retrospective ROI 127.7217%
  - monthly floor 101.75%.
- grid cells: **38,808**.

### Dev-only selected larger-volume profiles
These profile choices use Apr-Jun outcomes for ranking; Jul-Aug is report-only for that ranking. Note Jul-Aug is historically research-exposed elsewhere, so this is not a pristine holdout.

Approx 160 target:
- **157R** (+37)
- rule for additions:
  - comp >= 1.5
  - quality `head_prob + 1.50*opponent_mass >= .775`
  - head_prob >= .16
  - opponent_mass >= .375
  - ST >= -.80
  - ORIG >= -.35
- all ROI 120.69%
- Jul-Aug ROI 98.98%
- monthly floor 83.25% (Aug).

Approx 180 target:
- **171R**
- all ROI 110.20%
- Jul-Aug ROI 92.42%
- monthly floor 67.83%
- clearly weaker.

Approx 200 target:
- **193R**
- all ROI 116.53%
- Jul-Aug ROI 98.55%
- monthly floor 67.83%
- not attractive for current preference.

### Apr-Aug NON-PRISTINE frontier diagnostics
These rows use all five months for diagnostic constraints and therefore are NOT prospective proof.

1. **134R conservative expansion**
- +14 vs base120; all 14 additions are outside old164.
- rule:
  - comp >= 3.0
  - quality >= .90
  - head_prob >= .12
  - opponent_mass >= .40
  - ST >= -.80
  - ORIG >= -.35
- 57 heads / 134 = 42.54%
- exact3 33
- ROI **128.32%**
- monthly floor **101.75%**
- monthly ROI: Apr151.26 / May125.75 / Jun132.14 / Jul126.62 / Aug101.75.
- This is the maximum volume found that both keeps every month >=100 and keeps overall ROI >= frozen120 ROI.

2. **151R all-month-positive expansion**
- +31; all 31 additions are outside old164 for this profile.
- rule:
  - comp >= 2.5
  - quality >= .825
  - head_prob floor 0
  - opponent_mass >= .20
  - ST >= -.80
  - ORIG >= -.35
- ROI **115.85%**
- Jul-Aug ROI **111.57%**
- monthly floor **101.75%**
- monthly ROI: Apr124.25 / May114.36 / Jun117.98 / Jul116.35 / Aug101.75.
- More volume, but aggregate ROI gives up ~11.9pt versus frozen120.

3. **156R higher-volume / ROI-preserving diagnostic**
- +36
- rule:
  - comp >= 3.5
  - quality >= .75
  - head_prob >= .16
  - opponent_mass >= .30
  - ST >= -.80
  - ORIG >= -.35
- 65 heads / 156 = 41.67%
- exact3 37
- ROI **128.59%**
- Jul-Aug ROI **115.05%**
- monthly floor **91.58%**
- monthly ROI: Apr177.97 / May109.63 / Jun141.85 / Jul125.71 / Aug91.58.
- This is the maximum volume found with overall ROI >= frozen120 and monthly floor >=90.

4. **162R volume-forward diagnostic**
- +42
- rule:
  - comp >= 2.75
  - quality >= .75
  - head_prob >= .16
  - opponent_mass >= .30
  - ST >= -.80
  - ORIG >= -.35
- ROI **125.67%**
- Jul-Aug ROI **113.28%**
- monthly floor **91.58%**
- monthly ROI: Apr164.79 / May111.57 / Jun136.96 / Jul122.92 / Aug91.58.
- 56 nearby grid cells in the 150–162R range still satisfy ROI>=125 and monthly floor>=85, so the general 150–160 expansion shape is not a one-cell accident.
- Still NON-PRISTINE and not approved for official BET.

### Main conclusion
- Expanding the old structural universe works, but the verified historical ceiling is much lower than 250 because:
  - wide causal parent is only 262R;
  - full exhibition structure ready is 235R;
  - simple old164-preserving structural pool max is 226R;
  - verified official closing odds exist for 208R.
- **150–162R is the useful next frontier.**
- 180–200R profiles materially weaken monthly stability / support ROI.
- For user's stated preference to increase buys without destroying ROI:
  - conservative: 134R;
  - balanced higher-volume research target: **150–156R**;
  - volume-forward shadow target: **162R**.
- To reach ~1.5–2 final BET/day historically, the PRE parent itself must be relaxed beyond the current 100%-recall wide parent; that is a separate new research layer and should not be conflated with the validated 150–162R expansion.
- No production/LIVE decision changed in this work.
- September outcomes remain unread.

Status: `HEAD4_EXPANDED_UNIVERSE_SUCCESS__150_162R_FRONTIER_PROMISING__PRODUCTION_UNCHANGED`


## BEFORE — promote ROI-focused 156R expansion to operational candidate (2026-09-18)
User explicitly chose: 「ROI重視拡張にしようか」 => adopt the 156R ROI-focused expansion as the next operational 4HEAD line.

Important parity correction discovered before promotion:
- Historical frozen120/156 research was evaluated inside structural post-exhibition gates.
- Current fast LIVE `decide()` applies the 120 formula across every wide monitoring-parent race and does not explicitly re-check:
  - old164 ST gate `st4_adv_inside >= -0.60`
  - old164 ORIG gate `orig4_adv_inside >= -0.057777777777777706`.
- Therefore promotion must NOT simply append the 156 extra thresholds to the existing `decide()`; first restore exact structural semantics so LIVE matches historical membership.

Frozen operational candidate semantics to implement:
1. Compute from current exhibition:
   - `st4_adv_inside = mean(cur_st[1],cur_st[2],cur_st[3]) - cur_st[4]`
   - `orig4_adv_inside = cur_orig_avg[4] - mean(cur_orig_avg[1],cur_orig_avg[2],cur_orig_avg[3])`
2. Historical base120:
   - old164_struct = ST>=-0.60 AND ORIG>=-0.057777777777777706
   - within old164_struct apply frozen 77R + 120R nested-linear logic exactly.
3. ROI-focused expansion:
   - preserve every base120 selection;
   - add current PASS when:
     - comp >= 3.5
     - quality = head_prob + 1.50*opponent_mass >= .75
     - head_prob >= .16
     - opponent_mass >= .30
     - ST >= -.80
     - ORIG >= -.35.
4. Output both `base120_selected` and `expanded156_selected`; official BET/PASS follows expanded156.
5. Keep wall3 open rescue research-only and non-applied.
6. Freeze a JSON policy artifact and run independent historical parity/contract checks before treating LIVE as ready.
7. No target-race result or payout may be read during LIVE decisions.

Historical NON-PRISTINE reference for this chosen line:
- 156R / 65 heads (41.67%) / exact3 37
- retrospective ROI 128.59%
- Jul-Aug ROI 115.05%
- monthly floor 91.58%.
These are research diagnostics, not prospective profitability proof.

Status: HEAD4_156R_ROI_EXPANSION_PROMOTION_START


## AFTER — HEAD4 156R ROI-focused expansion promoted to LIVE decision profile
User approved the ROI-focused expansion. The operational last-minute 4HEAD decision now uses:
`HEAD4_156R_ROI_EXPANSION_V1`.

### Frozen policy
- Policy artifact: `artifacts/head4_156r_roi_expansion_20260918.json`
- commit: `0f30deb84aaecefbb3e1d1dd1c01f32e07697405`
- Historical NON-PRISTINE reference:
  - 156R / 65 heads = 41.67%
  - exact3 37
  - retrospective ROI 128.59%
  - Jul-Aug ROI 115.05%
  - monthly floor 91.58%.

### Critical LIVE parity correction
Before promotion, the fast 120R runner applied the 120 formula over the full wide monitoring parent but did not explicitly re-check the old historical structural ST/ORIG gates. That could allow a LIVE race outside the historical old164 structure to satisfy the 120 formula.

Promotion fixes this mismatch:
- current structural features are now computed exactly as research:
  - `st4_adv_inside = mean(cur_st[1:3]) - cur_st[4]`
  - `orig4_adv_inside = cur_orig_avg[4] - mean(cur_orig_avg[1:3])`
- all current original-exhibition values must be numeric before a final decision; incomplete original data fails closed / continues polling.
- base120 is now selected only inside:
  - ST >= -0.60
  - ORIG >= -0.057777777777777706.
- 156R expansion then adds a base120 PASS iff:
  - comp >= 3.5
  - quality = head_prob + 1.50*opponent_mass >= .75
  - head_prob >= .16
  - opponent_mass >= .30
  - ST >= -.80
  - ORIG >= -.35.
- every historical base120 selection is preserved by construction.
- wall3 open rescue remains research-only and does not change the official decision.

LIVE runner commit:
- `af0d1d67dbd0cea22db85be678881c223853d25f`
- compatibility filename remains `run_4head_120r_lastminute_fast.py`, but output `profile` identifies the active 156R policy.
- output now includes:
  - `base120_selected`
  - `expanded156_added`
  - `expanded156_selected`
  - `old164_struct`
  - `st4_adv_inside`
  - `orig4_adv_inside`
  - `selection_policy_artifact`.
- official BET/PASS follows `expanded156_selected`.

### Independent verification
- parity script: `audit_4head_156r_policy_parity.py`
- script commit: `13a020bbf57510a3da62d5078ebb2fbb221c5a4f`
- test workflow commit: `2554542de5637629b45915baf782a41c376393a9`
- Run `35341234767`
- Job `105587361122`
- Artifact `10545292057` / `head4-156r-policy-parity`
- conclusion: **SUCCESS**
- verified:
  1. exact historical 156R grid row: 156R / +36 / 65 heads / 37 exact3 / ROI ~128.59 / support ROI ~115.05 / monthly floor ~91.58;
  2. old164 + base120 formula => base120 selected;
  3. outside old164 but within relaxed 156 structure => expansion add;
  4. comp<3.5 => no expansion;
  5. old120 formula alone does NOT select when both historical structures fail;
  6. runner compiles successfully.

### Operational status
- Wide PRE monitoring parent remains unchanged and is sufficient for this 156R line.
- Existing strict/watchdog workflows automatically consume the updated runner on main.
- No result/payout is used before a LIVE decision.
- September target-race outcome remains unread by selection.
- Historical Apr-Aug ROI is NON-PRISTINE and not prospective proof.

Status: `HEAD4_156R_ROI_EXPANSION_LIVE_READY__PARITY_VERIFIED`


## AFTER — GitHub Issue notification for 4HEAD BET enabled
User selected GitHub notification for successful last-minute BET decisions.

Implementation:
- notifier script: `notify_head4_bet_github_issue.py`
  - initial commit `a88310793a3564a6083099d73e3354b7fa1ef5dc`
  - dry-run test support `755a54e259b90f35ff715638d45a75e05395c127`
- behavior:
  - only `decision == BET` creates an Issue;
  - PASS / NO_BET_DATA_NOT_READY produce no Issue;
  - deterministic title: `[4HEAD BET] YYYYMMDD JCDxx nR`;
  - exact-title dedupe prevents duplicate notification for the same race;
  - Issue is assigned to the repository owner so normal GitHub assigned-Issue notifications can surface it;
  - body contains venue/race, deadline, active 156R profile, head_prob, opponent_mass, composite_odds, base120/expanded156 flags, ST/ORIG advantages, ticket list and live odds, decision timestamp, odds source, and confirms target result/payout unused.
- strict monitor workflow:
  - adds `issues: write`;
  - calls notifier after contract check;
  - commit `04af733bba177c5df71e9dd880a58000bb03a62a`.
- GitHub-native watchdog workflow:
  - adds `issues: write`;
  - calls notifier only when an actual target job ran;
  - commit `f6baf73deb76a514e301adeff0aeab2cba471410`.
- watchdog workflow syntax/runtime validation:
  - Run `35343805368`
  - Job `105595567198`
  - SUCCESS.
- dedicated notifier contract test:
  - workflow `.github/workflows/test-head4-bet-github-notify.yml`
  - commit `dbaa2279fee6fa7511b1dfdf883e6e46c82b9f3c`
  - Run `35343870070`
  - Job `105595774368`
  - SUCCESS
  - verified PASS skips notification;
  - verified BET builds full Issue payload in dry-run;
  - no synthetic test Issue was created, avoiding notification spam.

Operational note:
- Actual GitHub app/email/push delivery depends on the user's GitHub notification settings for assigned Issues/repository activity.
- No external webhook or ChatGPT automation is required for the BET notification path.

Status: `HEAD4_BET_GITHUB_ISSUE_NOTIFICATION_READY`


## BEFORE — switch 4HEAD BET notification to direct @mention
User requested changing GitHub BET notification so GitHub Mobile can use Direct mentions rather than relying on Assigned Issues.

Verified repository owner:
- login: `merry02180218-ai`
- type: User
Therefore a body mention `@merry02180218-ai` is a valid direct user mention target.

Implementation plan:
1. Keep existing Issue assignment as a secondary notification path.
2. Add `@merry02180218-ai` as the first line of every BET Issue body.
3. PASS / NO_BET_DATA_NOT_READY remain no-notification.
4. Exact-title duplicate suppression remains unchanged.
5. Update notifier contract test to assert the mention appears in the BET dry-run payload.
6. Do not create a synthetic real Issue during testing.

Status: HEAD4_BET_DIRECT_MENTION_NOTIFICATION_START


## AFTER — 4HEAD BET notifications now use direct @mention
- Repository owner verified as user `merry02180218-ai`.
- BET Issue body now begins with:
  - `@merry02180218-ai`
- Existing assignment to the same user remains as a secondary path.
- PASS / NO_BET_DATA_NOT_READY still create no Issue.
- Duplicate suppression remains unchanged.
- notifier update commit:
  - `173efb9f31f885eba706c84cf8ef2853ea206dbb`
- test assertion update commit:
  - `c59096aa46d2985a2a8891de21873c6c911ca2f8`
- validation:
  - Run `35349787016`
  - Job `105614895160`
  - SUCCESS
  - BET dry-run payload contains `@merry02180218-ai`;
  - PASS path still skips notification;
  - no synthetic real Issue was created.

Operational guidance:
- In GitHub Mobile, enable **Direct mentions / ダイレクトメンション** push notifications.
- Assigned-Issue notification is no longer required for the primary BET alert path.

Status: `HEAD4_BET_DIRECT_MENTION_NOTIFICATION_READY`


## BEFORE — 4HEAD exact-volume head-rate optimization under ROI constraint
User asks whether 4-head hit rate can be increased while keeping ROI and race count around the current 156R line.

Research objective:
1. Hold final race count exactly at 156R first.
2. Require overall retrospective ROI >= current 156R ROI (128.5865%).
3. Maximize 4-head rate within the existing 38,808 Stage2 threshold cells.
4. Separately test stronger robustness constraints:
   - monthly ROI floor >= current 91.575%;
   - support Jul-Aug ROI >= current 115.0453%.
5. Report whether higher head rate is possible only by sacrificing month/support stability.
6. If exact-threshold family cannot improve robustly, proceed to swap/re-ranking research rather than simply lowering/raising a single threshold.
7. September target outcomes remain unread; this is Apr-Aug NON-PRISTINE retrospective research only.
8. Production/LIVE 156R policy remains unchanged until separately approved.

Preliminary local diagnostic before formal audit:
- current156: 156R / 65 heads = 41.67% / exact3 37 / ROI 128.59 / support ROI 115.05 / monthly floor 91.58.
- an exact156 alternative exists with 69 heads = 44.23%, exact3 38, ROI 129.64%, but monthly floor only 76.31% and support ROI 113.79%.
- under exact156 + ROI>=current + monthly_floor>=current, only the current membership-equivalent cells remain; no head-rate gain.
This must now be reproduced in a committed audit.

Status: HEAD4_156R_HEADRATE_ROI_CONSTRAINED_RESEARCH_START


## AFTER — exact-156 head-rate optimization under ROI constraint
Goal: raise 4-head hit rate while keeping the current 156R volume and at least the current overall retrospective ROI.

### Audit 1 — existing Stage2 threshold family
- script: `audit_4head_156r_headrate_roi_frontier.py`
- script commit: `1685c062da9d10be1f8f8a86c4d75510b7e93995`
- workflow: `.github/workflows/audit-4head-156r-headrate-roi-frontier.yml`
- workflow commit: `accc271c3f3de6fe2c38a5916f90966576405f14`
- Run `35350987322`
- Job `105618801877`
- Artifact `10549923633` / `head4-156r-headrate-roi-frontier`
- SUCCESS.

Current156 reference:
- 156R / 65 heads = 41.67%
- exact3 37
- ROI 128.5865%
- support Jul-Aug ROI 115.0453%
- monthly floor 91.575%.

Existing-grid exact156 + ROI>=current:
- 25 cells.
- best head-rate cell:
  - 156R / 69 heads = **44.23%**
  - exact3 38
  - ROI **129.64%**
  - head-rate gain +2.56pp / +4 heads
  - support ROI 113.79% (-1.26pp)
  - monthly floor **76.31%** (-15.26pp).
- therefore exact count + overall ROI can be preserved while raising head rate, but only by materially worsening month stability within this family.
- exact156 + ROI>=current + monthly floor>=current: only current-membership-equivalent cells; **no head-rate gain**.
- exact156 + ROI>=current + support ROI>=current: likewise no head-rate gain.
- near 150–162 with ROI>=current and monthly floor>=current:
  - best head-rate is 150R / 64 heads = 42.67% / ROI129.73%;
  - this drops 6 races, so it does not meet exact-volume user intent.

### Audit 2 — re-rank only the 36-race expansion layer
Frozen base120 is preserved exactly. Only the 36 additional races are re-selected. Search expands the quality weight from fixed
`head_prob + 1.50*opponent_mass`
to
`head_prob + beta*opponent_mass`
with beta .50..2.50 plus comp/head/mass/ST/ORIG thresholds.

- script: `audit_4head_156r_expansion_rerank.py`
- script commit: `64a2d88807a071b30c17ae3bef2b101cfaf41e9c`
- workflow: `.github/workflows/audit-4head-156r-expansion-rerank.yml`
- workflow commit: `642a667aa3ef2994d70a86d7c00b2ce85374d692`
- Run `35351343313`
- Job `105619960509`
- Artifact `10549914403` / `head4-156r-expansion-rerank`
- SUCCESS.

Best exact156 with overall ROI>=current:
- beta 1.25
- quality cut .55
- comp >=1.5 (same membership through comp 2.25 plateau)
- head_prob >=.16
- mass >=.20
- ST >=-.50
- ORIG >=-.35
- total: **156R / 70 heads = 44.87%**
- exact3 **39**
- ROI **139.97%**
- head-rate gain **+3.21pp / +5 heads**
- exact3 +2
- ROI +11.38pp
- Jul-Aug ROI **112.09%**
- monthly floor **79.63%** (August)
- month ROI:
  - Apr 252.51
  - May 116.03
  - Jun 141.85
  - Jul 129.05
  - Aug 79.63.
- development Apr-Jun: 89R / 35 heads =39.33% / ROI160.96.
- support Jul-Aug: 67R /35 heads=52.24% / ROI112.09.

Robustness finding:
- exact156 + ROI>=current + monthly floor>=current had only 2 cells, both current membership-equivalent:
  - 65 heads / 41.67%
  - no head-rate improvement.
- even relaxing monthly floor to >=85 produced no head-rate-improving exact156 cell.
- at monthly floor >=80, best available:
  - 156R / 66 heads = **42.31%**
  - exact3 37
  - ROI **136.91%**
  - monthly floor **83.25%**
  - support ROI **106.83%**.
- Thus simple threshold/re-ranking features show a clear trade-off:
  - higher head rate and higher aggregate ROI are achievable at exact 156R;
  - preserving current month-floor/support stability at the same time is not achieved.

### Conclusion
- Literal user objective (same 156R + overall ROI not lower + higher head rate): **YES**, retrospectively.
- Current best discovered: 44.87% head rate vs 41.67%, ROI139.97% vs128.59%, same156R.
- But this alternative weakens August/monthly floor to79.63 and support ROI to112.09.
- If monthly stability is also treated as a hard constraint, current156 remains the frontier under the tested feature family.
- Production/LIVE remains `HEAD4_156R_ROI_EXPANSION_V1`; no automatic promotion from this NON-PRISTINE research.
- September target outcomes remain unread.

Status: `HEAD4_156R_HEADRATE_CAN_IMPROVE_WITH_STABILITY_TRADEOFF__PRODUCTION_UNCHANGED`


## BEFORE — exact156 swap optimization for head rate + monthly stability
User approved the next research step after the exact156 rerank frontier.

Objective:
- keep frozen base120 unchanged;
- keep total selected races exactly 156R;
- start from the 44.87% / ROI139.97% alternative concept, but repair the weak August/month-floor behavior by swapping expansion-layer races;
- target head-rate near 44% while restoring monthly floor toward >=90%;
- require overall ROI >= current production156 ROI 128.5865%;
- inspect support Jul-Aug ROI as a secondary robustness metric.

Method:
1. Operate only on the 88 verified non-base120 candidates in the frozen Stage2 208R odds-covered universe.
2. Expansion layer size remains exactly 36R.
3. Build causal predecision ranking scores from head_prob, opponent_mass, composite_odds, ST and ORIG only.
4. Search score weights and choose exactly top36, rather than requiring one rectangular threshold box.
5. Report:
   - max head-rate under exact156 + ROI>=current;
   - max head-rate additionally requiring monthly floor >=85 / >=90 / >=current;
   - support ROI constraints;
   - development-first variants selected using Apr-Jun metrics, with Jul-Aug only reported afterward.
6. September outcomes remain unread.
7. NON-PRISTINE Apr-Aug retrospective audit only.
8. Production/LIVE remains unchanged unless separately approved after robustness review.

Status: HEAD4_156R_SWAP_OPTIMIZATION_START


## AFTER — exact156 causal swap optimization completed
User approved replacing weak expansion-layer races while keeping total volume at 156R.

### Implementation / validation
- initial broad score-search script:
  - `audit_4head_156r_swap_score_search.py`
  - commit `d5f0f868a6b4b6505a4c16d661fceb453834bfc2`
- initial broad workflow:
  - `.github/workflows/audit-4head-156r-swap-score-search.yml`
  - commit `a8abc00e0d033215bd9f48bd2ffe483afda811bc`
  - Run `35358441813` was computationally heavy and remained in-progress during the chat.
- focused fast search:
  - `audit_4head_156r_swap_score_fast.py`
  - vectorized commit `fade6106dc4485918ea7643e0c752366421bbf69`
- workflow:
  - `.github/workflows/audit-4head-156r-swap-score-fast.yml`
  - workflow commit `35f5f0d90db00302e4e03c84d848d75c33c90c60`
- final formal validation:
  - Run `35360824382`
  - Job `105651366180`
  - Artifact `10553214378` / `head4-156r-swap-score-fast`
  - SUCCESS
  - `AUDIT_OK=true`
  - `SEPTEMBER_OUTCOMES_READ=false`
  - `PRODUCTION_CHANGED=false`
  - selection scores use no race outcomes; search evaluation itself is NON-PRISTINE Apr-Aug retrospective.

### Search design
- frozen base120 remains unchanged.
- expansion layer remains exactly 36R => total exactly 156R.
- 88 non-base120 verified-odds candidates considered.
- per-race ranking uses only causal/predecision features:
  - head_prob
  - opponent_mass
  - ST advantage
  - ORIG advantage
  - market confidence derived from composite_odds
  - balance rank between head_prob and opponent_mass
- 3,600 weight cells x 13 eligibility profiles.
- 10,314 unique exact156 memberships evaluated.
- 1,869 memberships preserved overall ROI >= current156.

### Current156 reference
- 156R
- 65 heads / **41.67%**
- exact3 37
- ROI **128.5865%**
- support Jul-Aug ROI **115.0453%**
- monthly floor **91.575%**.

### Best aggregate ROI-preserving head-rate set
- 156R
- 71 heads / **45.51%**
- exact3 39
- ROI **131.19%**
- monthly floor **76.31%**
- support ROI **112.09%**.
This improves head rate strongly but materially weakens August/month stability.

### With monthly floor >=80%
Best:
- 156R
- 69 heads / **44.23%**
- exact3 **40**
- ROI **134.00%**
- support ROI **117.85%**
- monthly floor **83.25%**
- monthly ROI:
  - Apr177.97
  - May120.45
  - Jun150.45
  - Jul136.41
  - Aug83.25.
This is the strongest balanced head-rate improvement found in the tested score family.

### With monthly floor >=85%
Best:
- 156R
- 66 heads / **42.31%**
- exact3 38
- ROI **138.91%**
- support ROI **115.05%**
- monthly floor **87.21%**
- monthly ROI:
  - Apr216.44
  - May118.76
  - Jun141.85
  - Jul128.64
  - Aug87.21.

### With monthly floor >=90%
Only one ROI-preserving membership survived and it did **not improve head rate**:
- 156R
- 65 heads / **41.67%**
- exact3 37
- ROI **128.59%**
- monthly floor **91.575%**
- support ROI **113.28%**.
The same is true at the current floor >=91.575%.

### Conclusion
- The exact156 swap idea works if some monthly-floor relaxation is accepted.
- Clear frontier:
  - floor ~83% => head rate 44.23%, ROI134.00%, exact3 40.
  - floor ~87% => head rate 42.31%, ROI138.91%, exact3 38.
  - floor >=90% => no head-rate gain over current 41.67%.
- Therefore the user target of ~44% head rate + exact156 + ROI>=current + monthly floor around90% is **not achieved with the currently tested causal feature family**.
- To break this frontier, the next research should add genuinely new discriminatory features rather than further threshold tuning, e.g. expanded-universe wall3/open-path variables, motor/exhibition interaction, or attack-style features.
- LIVE/production remains `HEAD4_156R_ROI_EXPANSION_V1`; no promotion was made.
- September target outcomes remain unread.

Status: `HEAD4_156R_SWAP_FRONTIER_CONFIRMED__NEW_FEATURES_REQUIRED__PRODUCTION_UNCHANGED`


## BEFORE — expanded-universe wall3 / exhibition / motor exact156 research
User said to continue after the exact156 swap frontier showed that existing features cannot reach ~44% head rate while keeping monthly-floor ROI around 90%.

Objective:
- keep frozen base120 unchanged;
- keep total selection exactly 156R;
- enrich the 88 expansion candidates with genuinely new causal/post-exhibition features;
- first add the already-audited 1HEAD wall3 semantics to the full Stage2 odds-covered 208R universe;
- reuse expanded Stage1 motor/exhibition features where available;
- search exact36 expansion memberships using only predecision/current-exhibition features;
- primary target: head4 rate >=44% with overall ROI >= current156 128.5865%, monthly floor >=90% if achievable;
- secondary target: determine the best frontier if the 90% floor remains unreachable.

New candidate features to inspect:
- wall_score / open_risk / block_risk;
- attack4_score;
- ex_wall_gap, st_wall_gap, straight_wall_gap, avg_wall_gap;
- motor_win_diff_4v3, motor_2ren_diff_4v3;
- existing st4_adv_inside / orig4_adv_inside;
- head_prob, opponent_mass, composite_odds.

Research discipline:
1. September outcomes remain UNREAD.
2. Production/LIVE remains `HEAD4_156R_ROI_EXPANSION_V1`.
3. No promotion without a separate parity/robustness audit.
4. Apr-Aug search remains NON-PRISTINE and is not prospective proof.
5. Selection scores themselves may use only information available by the last-minute decision point; outcomes/payouts are evaluation-only.

Status: HEAD4_156R_EXPANDED_FEATURE_RESEARCH_START
