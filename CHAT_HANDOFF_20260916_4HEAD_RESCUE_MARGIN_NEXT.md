# CHAT HANDOFF — 2026-09-16 — 4HEAD RESCUE + CLOSE-MARGIN NEXT

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール
- production ticket policy `HEAD4_V291_COMP7_THIRD010`; PRE>=.28 / POST>=.25 / ENV_ENTRY>=.224790; frozen v283; THIRD gap<=.10; comp>=7; JPY10,000 Dutch; v96 prohibited; fail closed.
- September 2026 outcome/results are never read: `UNREAD`.
- closing odds are retrospective diagnostic only; formal prospective ROI=`NOT_COMPUTABLE`。

## 確定監査要約
- fixed candidate Apr-Jun 86R/35 head4; Jul-Aug 78R/35; Apr-Aug 164R/70.
- THIRD0.10 old flat-100yen retrospective: Apr-Aug 817 tickets / 35 hits / ROI 135.13%.

## RAW HIT / COMP 要約
- RAW HIT Run `35131504476`: Apr-Aug 164R / 817 tickets / 35 raw hits; comp>=7 retains 5, discards 30.
- COMP SWEEP Run `35135508327`: Apr-Jun no-filter ROI 149.0%, comp7 255.4%; Jul-Aug no-filter 86.4%, comp7 0%. Simple comp lowering rejected.

## RENEWED HEAD-PROBABILITY — FIRST RUN
- BoatraceCSV public race-card data. Run `35232199824`, Job `105238910701`, Artifact `10501603555`, SUCCESS.
- Apr-Jun 13,221R / head4 1,276; Jul-Aug 9,610R / head4 964; 78 fields.

## STRICT LEAKAGE AUDIT — SUCCESS
- Run `35234326600`, Job `105246227265`, Artifact `10503431028`, head `5ac632922a71e633d1ebb54080bc80442f2e0fe3`, SUCCESS.
- Corrected feature availability selection uses Apr-Jun training rows ONLY. Imputation/scaling/model fit also Apr-Jun only; Jul-Aug predict only.
- 78 fields remained usable. No train/validation race-key duplication. Result-derived fields forbidden from model matrix. September access blocked.
- Jul-Aug untouched validation AUC `0.727090`.
- 10 shuffled-target negative controls average AUC `0.503484`, collapsing to chance as expected.
- Corrected threshold results unchanged from first run: cut .30 => Apr-Jun 405R/150 head4=37.04%, Jul-Aug 369R/145=39.30%; .35 => 217/87=40.09%, 203/93=45.81%; .40 => 110/45=40.91%, 114/58=50.88%.
- Conclusion: no obvious future/result leakage detected by implemented checks; head probability is suitable for downstream retrospective research. This is not a mathematical proof of zero leakage; field-timing semantics remain a continuing audit concern.
- Production unchanged. September `UNREAD`.

## BEFORE — HEAD PROBABILITY × CURRENT 164R × THIRD0.10 × COMPOSITE ODDS
- User requested continuation after leakage audit.
- Next objective: attach corrected BoatraceCSV head probability to exact frozen 164 current candidates and evaluate whether it can rescue profitable PASS races while preserving current BETs.
- Reproduce exact Apr-Jun 86R/35 head4 and Jul-Aug 78R/35 head4 via frozen candidate builder.
- Recompute corrected head probability deterministically using Apr-Jun all-race training only; merge by 12-digit race_code.
- Keep v283 + THIRD0.10 ticket semantics frozen and verify ticket reproduction guard: Apr-Aug 817 tickets / 35 raw hits.
- Obtain retrospective closing odds with existing audited helper; compute composite odds and JPY10,000 Dutch payout exactly as current research semantics.
- Baseline = current comp>=7 BETs unchanged.
- Rescue only current PASS (`comp<7`) using 2D grid: head probability cut .20-.45 and optional composite lower bound 0/5.5/6.0/6.25/6.5/6.75. Report Apr-Jun development and Jul-Aug untouched validation separately.
- Metrics: total BET R, added rescue R, head4 R/rate, ticket hits, stake, payout, profit, ROI, and delta vs baseline.
- Do not select a production change from Apr-Aug aggregate alone; robustness on Jul-Aug is mandatory evidence.
- Production remains unchanged until explicit approval. v96 prohibited. September remains `UNREAD`.

Status: `HEADPROB_PASS_RESCUE_ROI_INTEGRATION_PREPARING`


## AFTER — HEAD PROBABILITY × CURRENT 164R × THIRD0.10 × COMPOSITE ODDS
- Workflow `.github/workflows/audit-4head-headprob-pass-rescue.yml` Run `35238737384`, Job `105261364738`, Artifact `10505011547`, head `474377dca21094c8cc6781a31b496cf573bc75cf`, SUCCESS.
- Reproduction guards passed: fixed 164R / 70 head4; THIRD0.10 817 tickets / 35 raw hits.
- Head-probability-only PASS rescue did not produce a robust profitable Jul-Aug validation rule. Best visible broad rescue reference was head_prob>=.21 with no composite-odds lower bound: 72 BET R / 15 hits / ROI 86.40%.
- Therefore simple head-probability-only rescue is not adopted. Current production remains unchanged.
- September remains `UNREAD`.

## BEFORE — JOINT HEAD PROBABILITY × OPPONENT MASS × PRE-RACE/LAST-MINUTE GATE GRID
- User approved continuation.
- Objective: vary head probability, opponent-mass/ticket-structure confidence, and pre-race/last-minute gate values jointly, then find robust regions for JPY10,000 Dutch composite-odds ROI rather than optimizing head probability alone.
- Preserve exact frozen 164R population and v283 + THIRD0.10 ticket semantics first; do not alter production during research.
- Development/validation split remains Apr-Jun vs Jul-Aug. Do not select from Apr-Aug aggregate alone.
- Evaluate BET count, added races, raw hits, stake, payout, profit, ROI, monthly stability, and sensitivity around neighboring threshold cells.
- Prefer plateau/robust regions over a single isolated maximum cell.
- September 2026 outcomes/results remain strictly `UNREAD`; v96 prohibited; closing odds retrospective diagnostic only.

Status: `JOINT_HEADPROB_OPPONENT_MASS_LASTMINUTE_GRID_PREPARING`


## AFTER — JOINT HEAD PROBABILITY × OPPONENT MASS × LAST-MINUTE GRID
- Run `35290923983`, Job `105433371006`, Artifact `10526661988`, head `b4039f9921c0ab38cceec7f8a800968fea228bfe`, SUCCESS.
- Reproduction guards passed: 164R / 70 head4 / 817 tickets / 35 raw hits.
- Robust criterion (Apr-Jun ROI>=100 AND Jul-Aug ROI>=100 AND Jul-Aug added rescue >=5) found `0` cells.
- Therefore no joint rescue rule is adopted from this grid. Production unchanged. September `UNREAD`.

## BEFORE — ABLATION / BOTTLENECK ANALYSIS
- User approved continuation.
- Next objective: do not stop at robust=0; isolate which gate is destroying validation ROI.
- Compare head-probability only, opponent-mass only, last-minute/original-exhibition only, and all pairwise combinations against the same current comp>=7 baseline.
- Also rank near-miss cells from the full joint grid, including ROI below 100, to quantify the trade-off between added rescue count and validation ROI.
- Report Apr-Jun and Jul-Aug separately, plus monthly Jul/Aug stability where useful.
- Keep exact 164R / THIRD0.10 / JPY10,000 Dutch semantics. No production change. September `UNREAD`.

Status: `JOINT_GRID_ABLATION_PREPARING`
