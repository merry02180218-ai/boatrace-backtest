# CHAT HANDOFF — 2026-09-14 — 4HEAD BOAT3 WAKU10 NEXT

## PURPOSE

次チャットで4号艇モデルのWaku10研究をそのまま再開するための正式引き継ぎ。古いチャット記憶より最新GitHubを優先すること。

## HARD RULES

- 作業前に必ずこの引き継ぎファイルへ `BEFORE` を追記してから実装・検証を開始する。
- 作業完了後に必ず同じ引き継ぎファイルへ `AFTER` を追記し、commit/run/job/artifact/結果/判断/次工程を残す。
- 4号艇productionはユーザーの明示承認なしに変更しない。
- 2026年7月・8月は NON-PRISTINE。outcomeをモデル選択・閾値調整に使用禁止。score-distribution stressのみ可。
- 2026年9月outcomeは UNREAD / outcome-blindを維持し、研究・選定に使用禁止。
- archived odds ROIは retrospective proxy。LIVE締切前オッズそのものとは扱わない。
- 重い共通処理は可能な限りキャッシュして再利用する。ただし特徴量・学習窓・閾値・downstream policyを変えない。

## PREVIOUS HANDOFF

詳細履歴は `CHAT_HANDOFF_20260914_4HEAD_WAKU10_AUDIT.md` を参照。

完成済みCORE decompositionでは、Apr-Jun S層で `B3_ONLY` が 38R / head4 44.74% / trifecta 26.32% / proxy ROI 203.997%、`WR_ST` が50R / trifecta 18.0% / ROI 141.012%。boat4 direct Waku10単独はほぼSを作れず、boat3側が主因と判断した。

## BOAT3 DIRECT-WAKU10 DECOMPOSITION — AFTER

Official valid run:
- workflow: `analyze-4head-waku10-ablation`
- run ID: `34818957616`
- head SHA: `8b9ea8b1bda75d82acaa4f2741540571bd0f0203`
- conclusion: `success`
- artifact: `head4-boat3-waku10-decomposition`
- artifact ID: `10337984670`
- digest: `sha256:bf9460ae99a818cd8453220bd875b9450c58551f2f5d4b51338345b0be7dc2d2`

This is the first valid boat3 decomposition run. Earlier run `34815749150` used the old workflow loop and must NOT be used as boat3 selection evidence.

### Implementation/caching

- Common invariant feature dataset is built once and cached as pickle via `--data-cache`; subsequent variants reuse it.
- Cache implementation commit: `23e354a8ac6f6bd92322653228b601695f0c828b`.
- Workflow correction/cached seven-variant run + explicit Apr-Jun filter commit: `8b9ea8b1bda75d82acaa4f2741540571bd0f0203`.
- Valid variants: `B3_WR_ONLY`, `B3_ST_ONLY`, `B3_SR_ONLY`, `B3_WR_ST`, `B3_WR_SR`, `B3_ST_SR`, `B3_ALL`.
- Apr-Jun is explicitly filtered before S/A/S+A outcome aggregation.
- Jul/Aug are separate score-stress only; September outcomes remain unused.

### Apr-Jun S primary results

| variant | R | head4 | head4 rate | trifecta | hit rate | proxy ROI | avg comp odds |
|---|---:|---:|---:|---:|---:|---:|---:|
| B3_WR_ONLY | 30 | 12 | 40.00% | 6 | 20.00% | 143.187% | 7.4899 |
| B3_ST_ONLY | 8 | 5 | 62.50% | 4 | 50.00% | 325.875% | 7.4403 |
| B3_SR_ONLY | 6 | 2 | 33.33% | 1 | 16.67% | 75.400% | 7.0107 |
| B3_WR_ST | 41 | 19 | 46.34% | 10 | 24.39% | 189.071% | 7.6489 |
| B3_WR_SR | 31 | 12 | 38.71% | 7 | 22.58% | 163.023% | 7.4577 |
| B3_ST_SR | 9 | 5 | 55.56% | 4 | 44.44% | 289.667% | 7.6248 |
| B3_ALL | 38 | 17 | 44.74% | 10 | 26.32% | 203.997% | 7.6803 |

### Apr-Jun S+A secondary results

| variant | R | head4 rate | trifecta hit rate | proxy ROI |
|---|---:|---:|---:|---:|
| B3_WR_ONLY | 97 | 38.14% | 10.31% | 71.988% |
| B3_ST_ONLY | 47 | 42.55% | 17.02% | 117.806% |
| B3_SR_ONLY | 42 | 35.71% | 11.90% | 82.733% |
| B3_WR_ST | 111 | 37.84% | 10.81% | 79.338% |
| B3_WR_SR | 103 | 37.86% | 10.68% | 74.959% |
| B3_ST_SR | 51 | 39.22% | 15.69% | 108.567% |
| B3_ALL | 111 | 37.84% | 10.81% | 79.338% |

### Current interpretation

1. Boat3 `ST` is the strongest single direct Waku10 signal, but `B3_ST_ONLY` S=8R is too small to promote directly.
2. `SR_ONLY` is weak and sub-100% S proxy ROI. SR is not useful as a standalone primary signal.
3. `B3_WR_ST` gives the best broad sample balance: 41 S races, head4 46.34%, trifecta 24.39%, proxy ROI 189.07%.
4. `B3_ALL` has slightly fewer S races (38) but 26.32% trifecta hit and 203.997% proxy ROI. It adds SR to WR+ST; the apparent improvement may be selection reshaping rather than stable SR value and needs overlap/stability analysis.
5. `B3_ST_SR` and `B3_ST_ONLY` have excellent efficiency but tiny N; treat them as high-efficiency small-sample signals, not production winners.
6. A/S+A performance is materially weaker for broad WR_ST/B3_ALL than their S layer, suggesting the edge is concentrated in the highest-score S tail. Do not expand A merely because S looks strong.
7. No production change has been made.

## NEXT WORK UNIT — BEFORE MUST BE APPENDED FIRST

Primary next task: **race-level overlap + monthly robustness audit of B3_WR_ST vs B3_ALL vs B3_ST_ONLY/B3_ST_SR** before considering any production promotion.

Do not tune new thresholds yet. First determine whether the attractive ROI is robust or driven by a small set of overlapping high-payout races.

Required analyses on Apr-Jun only:
- monthly S metrics for Apr / May / Jun separately for `B3_WR_ST`, `B3_ALL`, `B3_ST_ONLY`, `B3_ST_SR`;
- exact race-level S overlap between `B3_WR_ST` and `B3_ALL`;
- races unique to WR_ST and unique to B3_ALL;
- head4 wins / trifecta hits / return contribution for shared vs unique sets;
- payout concentration: top 1 / top 3 winning races contribution to total return and ROI sensitivity with those removed;
- compare composite-odds distribution for shared/unique sets;
- identify whether adding boat3 SR mostly removes bad WR_ST races, adds good races, or simply shifts score ranking;
- if practical, bootstrap or simple resampling confidence intervals for S head4/trifecta rates, clearly labeled exploratory due small N.

Jul/Aug: score-distribution stress only, no outcome inspection. Sep: outcome unread. Production unchanged.

If the overlap/stability audit shows B3_ALL advantage is payout-concentrated or unstable, prefer the simpler `B3_WR_ST` research candidate. If B3_ALL shows consistent monthly/unique-set improvement not dependent on one or two payouts, then B3_ALL remains the leading candidate for the next frozen-policy validation step.

Status: `BOAT3_DECOMPOSITION_COMPLETE_NEXT_OVERLAP_AUDIT_PENDING`

## NEXT CHAT START PROMPT

`boatrace-backtest の CHAT_HANDOFF_20260914_4HEAD_BOAT3_WAKU10_NEXT.md と最新GitHubを読んで、4号艇Waku10研究の続きから進めて。最新GitHubを優先。まず作業前に引き継ぎへBEFORE追記してから、B3_WR_ST vs B3_ALLを中心にApr-Junのrace-level overlap・月別安定性・払戻集中度を監査して。7月8月はNON-PRISTINEでoutcome禁止、9月outcomeはUNREAD、productionは変更しない。重い共通処理はキャッシュ再利用して。`

## BOAT3 OVERLAP / STABILITY AUDIT — BEFORE (2026-09-14 JST)

- Start point: latest GitHub HEAD `40a2abab108e732e11a6627aa523da47e7200b4d` confirmed before this work unit.
- Scope: Apr-Jun only for outcome-bearing analysis; audit `B3_WR_ST`, `B3_ALL`, `B3_ST_ONLY`, `B3_ST_SR` S-layer selections at exact race level.
- Required outputs: month-by-month S metrics, WR_ST↔ALL shared/unique race sets, shared/unique head4/trifecta/return contribution, top-1/top-3 payout concentration and removal sensitivity, composite-odds distributions, SR effect diagnosis, and exploratory resampling intervals where practical.
- Guardrails: Jul/Aug remain NON-PRISTINE outcome-blind (score-distribution stress only); Sep outcome remains UNREAD; no threshold tuning; no production change.
- Implementation rule: reuse the existing invariant cache/data path and preserve the existing feature/training/policy definitions.
- Status: `BOAT3_OVERLAP_AUDIT_STARTED`.
