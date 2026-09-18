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
