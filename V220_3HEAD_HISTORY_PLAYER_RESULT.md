# v220 3-head prior-exhibition + player-trait result

Source workflow run: `34255214361`  
Source commit: `12c615be360cd12162d6433d11a4d38ff74ffe56`  
Artifact: `v220-3head-history-player` id `10067758302`  
Artifact digest: `sha256:523c3dc0d808440d617c012c9513004f861c92de7afe3c2a055e2a1519c191ba`

## Guard / protocol

- Evaluation is 2025-12 through 2026-06 only.
- 2026-07/08 are hard excluded from training, tuning and evaluation.
- Strict monthly prior-only refit.
- Prior exhibition/original exhibition is frozen before current-day result ingestion.
- Same-day earlier races are deliberately excluded in this conservative daily freeze.
- Historical odds are settlement-only.
- ROI diagnostic uses fixed v166 Top10 plus exact 10,000-yen Hamilton Dutch.
- Selection volume is matched to the BASE p3>=0.30 monthly counts. No new threshold is tuned.

## Aggregate result

|variant|R|AUC|Brier|LogLoss|selected R|selected 3-head|Top10 ROI|profit|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|BASE|31,219|0.6420|0.10567|0.36192|493|34.48%|78.5%|-1,040,540|
|BASE+PRIOR1|31,219|0.6524|0.10526|0.36004|493|35.50%|78.8%|-1,032,100|
|BASE+PRIOR12|31,219|0.6560|0.10502|0.35916|493|38.74%|82.3%|-858,350|
|BASE+ALL_HISTORY|31,219|0.6561|0.10503|0.35917|493|37.93%|80.4%|-955,140|
|BASE+PLAYER|31,219|0.6788|0.10428|0.35492|493|42.60%|79.6%|-979,900|
|BASE+ALL|31,219|0.6837|0.10407|0.35378|493|41.78%|76.6%|-1,130,770|

## Robustness of volume-matched Top10 settlement

Computed from the workflow prediction artifact after the run; top-profit races are removed only as a robustness diagnostic.

|variant|ROI|max DD|ROI rm1|ROI rm3|ROI rm5|
|---|---:|---:|---:|---:|---:|
|BASE|78.50%|1,058,480|75.33%|71.43%|68.55%|
|BASE+PRIOR1|78.76%|1,063,830|75.61%|72.12%|69.26%|
|BASE+PRIOR12|82.34%|948,610|80.52%|77.15%|75.02%|
|BASE+ALL_HISTORY|80.39%|1,023,090|78.57%|75.75%|73.62%|
|BASE+PLAYER|79.63%|1,089,960|78.44%|76.20%|74.13%|
|BASE+ALL|76.59%|1,186,890|75.45%|73.26%|71.45%|

## Main findings

1. Player traits are the strongest head-discrimination addition. `BASE+PLAYER` raises aggregate AUC from 0.6420 to 0.6788 and selected 3-head rate from 34.48% to 42.60%. It improves AUC in all seven evaluation months; Brier improves in six of seven months.
2. Prior exhibition history is useful. Prior1 alone is modest; prior1+prior2 is clearly stronger. `BASE+PRIOR12` raises selected 3-head rate to 38.74% and gives the best Top10 ROI in this audit at 82.34%, while also reducing max drawdown versus BASE.
3. Combining every history/player feature gives the best aggregate AUC/Brier (`BASE+ALL`, AUC 0.6837 / Brier 0.10407), but ROI falls to 76.59%. Better head discrimination alone does not guarantee better trifecta value.
4. `BASE+PLAYER` has the highest selected head rate but lower conditional Top10 coverage than BASE, so some of the head-model gain is lost in the opponent-ranking / payout layer. This is a key next diagnostic.
5. No v220 variant reaches 100% realized ROI. None is production-adopted from this audit.

## Next step

Keep v166 as the baseline opponent ranker, but audit its conditional Top10 coverage specifically on the races newly selected by `BASE+PLAYER` and `BASE+PRIOR12`. Then test a two-stage head model: player-trait head discrimination plus prior1/prior2 exhibition as a separate state/condition feature, without blindly pooling every history feature. Continue to keep Jul/Aug isolated and use Sep+ immutable live odds for prospective value validation.
