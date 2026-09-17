# CHAT HANDOFF — 2026-09-16 — 4HEAD RESCUE + CLOSE-MARGIN NEXT

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール
- production ticket policy `HEAD4_V291_COMP7_THIRD010`; PRE>=.28 / POST>=.25 / ENV_ENTRY>=.224790; frozen v283; THIRD gap<=.10; comp>=7; JPY10,000 Dutch; v96 prohibited; fail closed.
- September 2026 outcome/results are never read: `UNREAD`.
- closing odds are retrospective diagnostic only; formal prospective ROI=`NOT_COMPUTABLE`。

## 確定監査要約
- fixed candidate Apr-Jun 86R/35 head4; Jul-Aug 78R/35; Apr-Aug 164R/70.
- THIRD0.10 old flat-100yen retrospective: Apr-Aug 817 tickets / 35 hits / ROI 135.13%.

## SIX-MONTH SUCCESS
- Run `35129089769`, Job `104905317906`, Artifact `10461260375` SUCCESS.
- Mar-Aug 191 candidates / 953 tickets / 55 BET / 136 PASS / 7 BET hits / ROI 146.8327% closing-odds diagnostic.

## RAW HIT RECONCILIATION — SUCCESS
- Run `35131504476`, Job `104913379223`, Artifact `10461493300` SUCCESS.
- Apr-Aug THIRD0.10 exactly reproduces 164R / 817 tickets / 35 raw hits.
- comp>=7 retains only 5 of those 35 raw hits; 30 correct raw hits are PASS-discarded.
- monthly raw -> BET hits: Apr 8->4, May 7->0, Jun 4->1, Jul 11->0, Aug 5->0.
- Therefore ticket generation is intact; the discrepancy is caused by the comp>=7 market filter.

## COMP THRESHOLD SWEEP — SUCCESS
- Run `35135508327`, Job `104926754630`, Artifact `10463204774` SUCCESS.
- frozen v283 + THIRD0.10 fixed; only composite-odds cutoff varied.
- Apr-Jun ROI: no-filter 149.0%, 6.00 246.9%, 6.25 266.5%, 6.50 293.4%, 6.75 262.5%, 7.00 255.4%.
- Jul-Aug holdout ROI: no-filter 86.4% (16/78 hits), 6.00 23.0% (1/27), 6.25 23.0% (1/27), 6.50/6.75/7.00 0%.
- Simple lowering of comp cutoff does not robustly increase profitable BET races; comp filter strongly discards Jul-Aug winners.
- Production comp>=7 remains unchanged.

## RENEWED HEAD-PROBABILITY RESEARCH — FIRST RUN SUCCESS
- Data source: BoatraceCSV public CSV (`https://boatracecsv.github.io/data`), race-card pre-race fields.
- Run `35232199824`, Job `105238910701`, Artifact `10501603555`, head `70448954df69f915c94af95628327c056a06d5da`, SUCCESS.
- Apr-Jun training rows 13,221 / head4 1,276; Jul-Aug unused validation rows 9,610 / head4 964; 78 usable fields.
- Examples: cut .30 => Apr-Jun 405R / head4 37.04%, Jul-Aug 369R / 39.30%; cut .35 => 217R / 40.09%, 203R / 45.81%; cut .40 => 110R / 40.91%, 114R / 50.88%.
- September remained UNREAD and production unchanged.
- IMPORTANT: this first run is NOT yet certified leakage-free. Feature availability filtering was calculated from Apr-Aug combined rows, so the Jul-Aug validation period influenced only which columns were considered sufficiently non-missing. Labels were not used in that selection, but strict temporal isolation requires correction and re-audit.

## BEFORE — STRICT LEAKAGE AUDIT
- User explicitly requested a leakage audit before using the renewed head probability.
- Audit must be stricter than the first run and use Japanese reporting where practical.
- Required checks:
  1. Select usable fields from Apr-Jun training rows ONLY; Jul-Aug must not influence field selection, imputation, scaling, fitting, threshold choice, or any learned preprocessing.
  2. Audit all selected BoatraceCSV race-card field names and exclude any field whose timing cannot be proven pre-race / pre-decision. Results may be used ONLY to create the target label after race-key matching.
  3. Re-run Apr-Jun -> Jul-Aug untouched validation with the corrected pipeline and compare the full head-probability threshold curve against Run 35232199824.
  4. Add shuffled-target negative-control test. With training labels randomized, validation discrimination / high-probability head rates must collapse toward chance; otherwise flag possible leakage or structural bug.
  5. Add date/race-key integrity checks: no duplicate race keys across train/validation, no September access, no target/result-derived column in model matrix.
  6. Save field list, audit flags, corrected threshold sweep, and negative-control summary as artifact.
- Do NOT change production based on this audit alone. v96 prohibited. September remains `UNREAD`.

Status: `HEAD_PROBABILITY_STRICT_LEAKAGE_AUDIT_PREPARING`
