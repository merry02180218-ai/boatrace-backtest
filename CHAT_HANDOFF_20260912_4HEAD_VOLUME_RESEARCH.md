# CHAT HANDOFF — 2026-09-12 — 4号艇モデル件数拡張研究

Updated: 2026-09-12 JST
Repository: `merry02180218-ai/boatrace-backtest`
Scope: 4号艇モデル / BET件数を増やしつつ強度を維持する研究

## 1. ユーザー要求

- 現行4号艇モデルはBET数が少なすぎるため増やしたい。
- 現在の強さ・月別安定性をできるだけ維持する。
- Top4固定である必要はない。可変点数を許可。
- 自動研究する。
- 研究だけで終わらせず、実運用できる形まで落とす。
- 研究内容・採用/不採用理由をhandoffに残す。

## 2. 絶対ルール

現行production lineageは `HEAD4_V291_COMP7`。

S:
- PRE >= 0.28
- POST >= 0.25
- ENV_ENTRY >= 0.224790

Opponent:
- SECOND = PLAYER_START / L2=10
- conditional THIRD = COND_BASE / L2=0.3
- v283 TOP2XTOP2 prefix / alpha2=0.60
- v96 production signal禁止

現行ticket:
- Top4
- composite >= 7.0
- 1R 10,000円 inverse-odds Dutch / 100円Hamilton

Data discipline:
- 2026-07/08 outcome = NON-PRISTINE。threshold/model/rescue選定に使用禁止。
- 2026-09 outcome = outcome-blind。研究・fit・model selectionに使用禁止。
- LIVEではofficial pre-deadline 3連単120/120 snapshot必須。
- 新研究はv291履歴を書き換えず、新versionとしてfreezeする。

## 3. 現行BASE開発成績

Apr-Jun archived odds proxy / v283 Top4 / composite>=7:

- Apr: 11R / ROI 524.96%
- May: 9R / ROI 177.91%
- Jun: 8R / ROI 166.46%
- total: 28R / ROI 310.98%

これはretrospective development evidenceであり正式prospective OOSではない。

## 4. 研究方針

強い28Rを壊さず、まず `BASE PASS` レースだけに追加BET routeを作る。

重要:
- BASE BETのticket/stake/decisionはimmutable。
- 追加route単体のROIも検証する。
- BASE利益で赤字追加BETを隠さない。
- 可変Nは許可するが、resultを見てNを選ばない。
- LIVEで同じ入力から再現できる rule だけを候補にする。

## 5. Research A — odds-only volume rescue

Files:
- `analyze_4head_v291_volume_rescue.py`
- `.github/workflows/research-4head-v291-volume-rescue.yml`
- `summary_4head_v291_volume_rescue.md`
- `analysis_4head_v291_volume_rescue_*.csv`
- `head4_v291_volume_rescue_candidate.json`

Method:
- BASE = N4 / comp>=7 immutable。
- BASE PASSだけを対象。
- FIXED N=2..12 + floor、またはADAPT maxN + floor。
- floor未達なら本当にPASS。v288の「N2 forced fallback」は使わない。
- Apr-Jun only hard guard。
- S+A / S separately。
- LOMO selection-procedure check。

Result:
- S+A selected search cell: FIXED N4 / floor 5.5
- combined: 45R (+17) / ROI 220.29% / monthly floor 151.93%
- しかし追加17R単体 ROI = 70.91%
- S-only: NO_SAFE_CANDIDATE

Decision:
**REJECT**。
追加分単体が負けており、BASE利益で見かけ上プラスになっているだけ。

## 6. Research B — frozen v273 A-layer + variable N standalone rescue

Files:
- `analyze_4head_v291_a_rescue_standalone.py`
- `.github/workflows/research-4head-v291-a-rescue-standalone.yml`
- `summary_4head_v291_a_rescue_standalone.md`
- `analysis_4head_v291_a_rescue_standalone*.csv`
- `head4_v291_a_rescue_candidate.json`

Method:
- existing BASE bets excluded。
- frozen v273 A-layerのBASE-PASS racesだけ。
- FIXED / ADAPT variable N + composite floor。
- 追加route単独で各月黒字になるguard。
- LOMO。

Result:
- `NO_STANDALONE_SAFE_CANDIDATE`
- Apr/May/Jun LOMOすべて `NO_TRAIN_CANDIDATE`

Decision:
**REJECT**。

Also note:
- historical v272 A layer was profitable aggregate under legacy ticketing, but April LOMO weakness existed。
- final A_SCORE LIVE scale mapping is not formally frozen, so Aは即production投入不可。

## 7. Top4固定解除の実装準備

Added:
- `head4_v291_full_pair_order.py`

Purpose:
- frozen v283 TOP2XTOP2 first 4を完全維持。
- 5位以降は同じalpha2=0.60 joint orderのremaining pairsをappend。
- full 20 unique pair orderを返せる。
- Top4 prefix parityをassert。
- fitting/outcome/v96なし。

これにより新policyではN=2..20の可変ticketがLIVEで可能になる。

## 8. 重大なleakage audit finding

`analysis_v283_4head_conditional_pair_order.csv` は opponent model評価用で、boat 4が実際に勝ったhistorical rowsを中心に構成されている。

Frozen S+A selected rowsがApr-Junで約40なのは、100 candidatesのうちboat4-head winsが約40だから。

したがってこのCSVを100候補のconfidence tableとして直接joinすると、**winner=4 outcome-conditioned selection leakage** になる。

禁止:
- outcome-conditioned v283 CSVの「行が存在するか」をconfidence featureとして使うこと。

Safe route:
- v287 already has `test_long_for_portfolio()` and month-walk-forward inference for **all portfolio races regardless of eventual winner**。
- confidence researchは必ずこのall-candidate inference pathを使う。

## 9. Research C — v283 confidence + variable N（進行中）

Files:
- `analyze_4head_v291_confidence_volume_rescue.py`
- `.github/workflows/research-4head-v291-confidence-volume.yml`

Safety design:
- 100/100 S+A candidatesをv287 pathでoutcome-independent month-walk-forward inference。
- v283 outcome-conditioned CSVはconfidence sourceとして使わない。
- Apr-Jun only。
- no v96 / no Jul-Aug / no Sep outcomes。
- BASE immutable / rescue only。

Live-computable confidence inputs:
- p2 top1/top2 ratio
- p2 top2 mass
- frozen alpha=.60 joint model mass in prefix N
- joint normalized entropy
- conditional THIRD concentration

Candidate policy families:
- P2 confidence gate + fixed N + comp floor
- joint-mass Top4 concentration gate + fixed N + comp floor
- joint-entropy gate + fixed N + comp floor
- model-mass target variable N + comp floor

Promotion guard:
- rescue-only positive aggregate
- rescue-only every month positive
- minimum monthly support
- combined monthly floor protection
- LOMO held-out rescue positive in every month
- S-only evaluated separately for immediate operational possibility

Status at this handoff revision:
**CI/result pending; do not promote before persisted result + LOMO review.**

## 10. Downstream LIVE artifact blocker

The <=2026-06-30 downstream artifact freeze CI run `34696728655` failed closed.

Failure:
- `v283 conditional THIRD June parity failed max_abs=9.04380706659e-05`

Important:
- Jul/Aug labels used = false
- September labels used = false
- v96 production signal used = false
- blocker is parity/reproduction, not leakage

Therefore even if Research C finds a strong policy, do **not** call the full LIVE route production-ready until this parity blocker is resolved or an audited tolerance/order-parity justification is frozen.

## 11. Production completion checklist for any promoted volume policy

1. research candidate passes rescue-only + monthly + LOMO guards
2. assign a NEW policy version (do not mutate v291 history)
3. frozen <=2026-06-30 downstream inference artifact passes parity audit
4. full 20 v283 order verifier passes and Top4 prefix exactly equals old v291
5. ticket selector runs from p2/conditional-third + official odds only
6. official pre-deadline 120/120 trifecta odds snapshot mandatory
7. BASE decision evaluated first and retained unchanged
8. rescue only if BASE PASS
9. exact 10,000 JPY Dutch / 100 JPY Hamilton
10. persist audit before result acquisition
11. missing/stale/late odds => ERROR_NO_BET
12. prospective checkpoint only after operational freeze

## 12. Next action

First read latest GitHub because other branches may have advanced.
Then:
- inspect `summary_4head_v291_confidence_volume_rescue.md`
- inspect confidence workflow result and LOMO
- if FAIL: reject and move to a new head-expansion layer rather than loosening odds blindly
- if PASS: freeze new policy version, fix downstream artifact parity, add LIVE selector + CI + audit and perform no-outcome dry run.
