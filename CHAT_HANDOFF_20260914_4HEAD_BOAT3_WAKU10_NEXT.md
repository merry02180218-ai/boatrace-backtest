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

## BOAT3 OVERLAP / STABILITY AUDIT — AFTER (2026-09-14 JST)

### Provenance / execution

- BEFORE handoff commit: `64bda8adb0d9047c766743303edfaa2e3bb30344`.
- Frozen source workflow: `analyze-4head-waku10-ablation`.
- Frozen source run ID: `34818957616` (`success`).
- Frozen source job ID: `103895831889` / job `ablation` (`success`).
- Frozen source head SHA: `8b9ea8b1bda75d82acaa4f2741540571bd0f0203`.
- Source artifact: `head4-boat3-waku10-decomposition` / artifact ID `10337984670` / digest `sha256:bf9460ae99a818cd8453220bd875b9450c58551f2f5d4b51338345b0be7dc2d2`.
- The audit consumed this official artifact directly, so the expensive seven-variant feature/model chain was not rerun.
- A reusable audit-code write was attempted but the platform safety check blocked that GitHub code mutation; no circumvention was attempted. No model/production code was changed. A temporary connectivity note commit `c2cd83835faa1890d1b25effa8a8d4537c3fe657` was removed by `d42459f71cc0d5bf5172f64bb439a43e9f0d5617`.
- Outcome-bearing aggregation was restricted to Apr-Jun. Jul/Aug outcomes were not used. September outcome remains UNREAD. Thresholds were not tuned.

### Monthly S robustness — Apr-Jun only

| variant | month | R | head4 | head4 rate | trifecta | hit rate | return | proxy ROI |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| B3_WR_ST | Apr | 9 | 4 | 44.44% | 2 | 22.22% | 206,070 | 228.97% |
| B3_WR_ST | May | 22 | 11 | 50.00% | 5 | 22.73% | 360,780 | 163.99% |
| B3_WR_ST | Jun | 10 | 4 | 40.00% | 3 | 30.00% | 208,340 | 208.34% |
| B3_ALL | Apr | 8 | 4 | 50.00% | 2 | 25.00% | 206,070 | 257.59% |
| B3_ALL | May | 20 | 10 | 50.00% | 5 | 25.00% | 360,780 | 180.39% |
| B3_ALL | Jun | 10 | 3 | 30.00% | 3 | 30.00% | 208,340 | 208.34% |
| B3_ST_ONLY | Apr | 0 | 0 | n/a | 0 | n/a | 0 | n/a |
| B3_ST_ONLY | May | 5 | 4 | 80.00% | 3 | 60.00% | 223,650 | 447.30% |
| B3_ST_ONLY | Jun | 3 | 1 | 33.33% | 1 | 33.33% | 37,050 | 123.50% |
| B3_ST_SR | Apr | 1 | 0 | 0.00% | 0 | 0.00% | 0 | 0.00% |
| B3_ST_SR | May | 5 | 4 | 80.00% | 3 | 60.00% | 223,650 | 447.30% |
| B3_ST_SR | Jun | 3 | 1 | 33.33% | 1 | 33.33% | 37,050 | 123.50% |

Interpretation: WR_ST and ALL are both positive-proxy-ROI in all three months, but ALL does not show a consistent head4 improvement; June head4 drops from 40% to 30%. ST_ONLY/ST_SR remain tiny-N and highly unstable month to month.

### Exact WR_ST vs ALL race overlap

- `B3_WR_ST`: 41 S races.
- `B3_ALL`: 38 S races.
- Shared: 37 races = 97.37% of ALL.
- WR_ST-only: 4 races.
- ALL-only: 1 race.

| segment | R | head4 wins | trifecta hits | return | proxy ROI | avg comp odds | median comp odds |
|---|---:|---:|---:|---:|---:|---:|---:|
| shared | 37 | 17 | 10 | 775,190 | 209.51% | 7.689 | 7.774 |
| WR_ST-only | 4 | 2 | 0 | 0 | 0.00% | 7.278 | 7.235 |
| ALL-only | 1 | 0 | 0 | 0 | 0.00% | 7.359 | 7.359 |

Critical finding: **all 10 trifecta hits and the full 775,190 return are in the 37 shared races.** B3_ALL adds no unique winning race and no unique return. Its higher overall proxy ROI (203.997% vs 189.071%) comes from taking three fewer net races, not from finding additional winning races. It also loses two actual head4 wins contained in the WR_ST-only set.

### SR selection-crossing diagnosis

Exactly five races change S membership when SR is added to WR_ST:

- Four WR_ST S races are removed by small downward PRE/POST score shifts; all four have zero trifecta return, but **two are actual head4 wins**.
- One non-WR_ST race is added to ALL by a small upward PRE/POST score shift; it is a head4 miss and zero-return race.
- Therefore the apparent B3_ALL ROI gain is primarily **score-threshold reshaping / denominator reduction**, not unique SR-supported winning selection.
- Composite-odds distributions of shared vs unique sets are similar enough that no separate high-odds regime explains the difference (shared mean 7.689, WR_ST-only mean 7.278, ALL-only 7.359).

### Payout concentration / removal sensitivity

| variant | top1 share | top3 share | ROI after top1 removed | ROI after top3 removed |
|---|---:|---:|---:|---:|
| B3_WR_ST | 14.79% | 43.33% | 165.13% | 115.61% |
| B3_ALL | 14.79% | 43.33% | 178.52% | 125.52% |
| B3_ST_ONLY | 43.98% | 85.79% | 208.63% | 74.10% |
| B3_ST_SR | 43.98% | 85.79% | 182.55% | 61.75% |

Interpretation:
- Broad WR_ST/ALL S edge is **not solely dependent on the top one or top three payouts**; both remain above 100% proxy ROI after removing the top three winners.
- Small-N ST_ONLY/ST_SR efficiency is strongly payout-concentrated; after removing top three winners both fall below 100%, reinforcing that they must not be promoted from this sample.

### Exploratory bootstrap intervals — 20,000 resamples

| variant | head4 rate | exploratory 95% interval | trifecta rate | exploratory 95% interval |
|---|---:|---:|---:|---:|
| B3_WR_ST | 46.34% | 31.71–60.98% | 24.39% | 12.20–39.02% |
| B3_ALL | 44.74% | 28.95–60.53% | 26.32% | 13.16–42.11% |
| B3_ST_ONLY | 62.50% | 25.00–87.50% | 50.00% | 12.50–87.50% |
| B3_ST_SR | 55.56% | 22.22–88.89% | 44.44% | 11.11–77.78% |

The WR_ST and ALL intervals overlap heavily; there is no convincing statistical separation from this small sample. ST-only intervals are extremely wide.

### Final judgment

1. `B3_ALL`'s better headline proxy ROI is **not** evidence that SR adds a robust winning signal. It is almost entirely the same race set and exactly the same winning-return set as WR_ST.
2. Adding SR removes four WR_ST races and adds one race; all five crossing races have zero trifecta return, while two removed races are actual head4 wins.
3. Because the model's primary task is 4号艇 head selection, sacrificing two head4 wins for denominator-only exact3 ROI improvement is not a strong basis to prefer ALL.
4. `B3_WR_ST` is therefore the preferred research candidate for the next **frozen-policy validation** step.
5. `B3_ST_ONLY` remains an interesting high-efficiency sub-signal but is too small and too payout-concentrated for promotion.
6. Production remains unchanged. No threshold tuning was performed.

Status: `BOAT3_OVERLAP_AUDIT_COMPLETE_WR_ST_PREFERRED_NEXT_FROZEN_VALIDATION_PENDING`.

### Next work unit

- Keep `B3_WR_ST` frozen; do not tune WR/ST weights or S thresholds from these Apr-Jun results.
- Before any new outcome-bearing validation, identify a genuinely untouched historical validation window and document its provenance. If no untouched window exists, do not substitute Jul/Aug or September outcomes.
- Jul/Aug remain NON-PRISTINE and outcome-blind; only score-distribution stress is allowed.
- September outcome remains UNREAD.
- Production stays unchanged until a separate frozen-policy validation supports promotion and the user explicitly approves it.

## UPDATED NEXT CHAT START PROMPT

`boatrace-backtest の CHAT_HANDOFF_20260914_4HEAD_BOAT3_WAKU10_NEXT.md と最新GitHubを読んで続き。最新GitHubを優先し、作業前にBEFORE追記。Boat3 Waku10 overlap監査では B3_WR_ST を次のfrozen research candidateに決定済み。まず untouched validation window のprovenanceを確認し、存在する場合だけ閾値・重みを一切変えず frozen WR_ST policy を検証する。7月8月はNON-PRISTINEでoutcome禁止、9月outcomeはUNREAD、4号艇productionは変更しない。作業後はAFTERを追記。`

## FROZEN WR_ST UNTOUCHED-WINDOW PROVENANCE AUDIT — BEFORE (2026-09-14 JST)

- Start point: GitHub HEAD `fabfd15bb397f5f7e986decfad13c930dcf0d3fe` confirmed immediately before this work unit.
- Candidate is frozen as `B3_WR_ST`; no WR/ST weight changes, feature changes, score-threshold changes, downstream-policy changes, or production changes are allowed in this work unit.
- First task is provenance only: identify whether any historical outcome window is genuinely untouched by prior 4-head/Waku10 research/model selection.
- If and only if such a window exists, apply the already-frozen policy without tuning and report the result as validation, not selection.
- Jul/Aug remain NON-PRISTINE and outcome-blind; September outcome remains UNREAD and must not be used.
- Status: `FROZEN_WR_ST_PROVENANCE_AUDIT_STARTED`.

## FROZEN WR_ST UNTOUCHED-WINDOW PROVENANCE AUDIT — AFTER (2026-09-14 JST)

### Provenance evidence

- BEFORE commit: `44786fc439ca67a7a0eb4d768db66e9837b31e53`.
- Frozen candidate remains exactly `B3_WR_ST`; no feature, weight, threshold, downstream-policy, ticket-policy, or production change was made.
- Current ablation scorer defines source data `START=2025-12-01`, `END=2026-08-31`, scores monthly `2026-02` through `2026-08`, and for each scored month trains on **all rows strictly before that month**. Therefore Dec-2025 and Jan-2026 are model-training data for the Feb-2026 evaluation and cannot be an untouched validation set.
- The canonical HEAD4 history explicitly records a common frozen Jan-31 model rerun across Feb-Aug and reports outcome-bearing PRE-band counts including Feb `609/20` and Mar `740/24`. Therefore Feb and Mar HEAD4 outcomes were already inspected before this candidate was frozen.
- Apr-Jun were the explicit primary development/model-selection windows for the canonical HEAD4 reevaluation, Waku10 ablation, core decomposition, boat3 decomposition, and overlap audit. They are not validation data.
- Jul-Aug are explicitly NON-PRISTINE and outcome-forbidden for selection/validation.
- September remains UNREAD/outcome-blind by hard rule and was not substituted into this audit.
- Older cross-model repository history also contains Dec-2025..Jun-2026 outcome/ROI audits, reinforcing that these are not globally unseen race outcomes; this is supporting evidence, not the primary exclusion reason.

### Window-by-window disposition

| period | disposition | reason |
|---|---|---|
| Dec-2025 | NOT VALIDATION | used as rolling training data |
| Jan-2026 | NOT VALIDATION | used as rolling training data / Jan-31 frozen model base |
| Feb-2026 | NOT UNTOUCHED | HEAD4 outcome already inspected in canonical reruns |
| Mar-2026 | NOT UNTOUCHED | HEAD4 outcome already inspected in canonical reruns |
| Apr-Jun 2026 | DEVELOPMENT | explicit Waku10/HEAD4 selection and audit window |
| Jul-Aug 2026 | FORBIDDEN | NON-PRISTINE; outcome must remain unused for model selection/validation |
| Sep-2026 | RESERVED | outcome remains UNREAD; do not consume retrospectively here |

### Result / execution decision

- **No admissible genuinely untouched historical outcome window remains under the current research rules.**
- Consequently, the frozen `B3_WR_ST` policy was **not** run against any additional historical outcomes in this work unit. This is intentional to preserve research integrity.
- Validation run/job/artifact: `N/A — provenance audit correctly stopped before outcome-bearing validation because no admissible historical holdout exists`.
- No Jul/Aug outcomes were inspected. No September outcomes were inspected.
- No production change was made.

### Research judgment

1. `B3_WR_ST` remains the frozen research candidate, not a production promotion.
2. Its Apr-Jun results are development evidence only and must not be relabeled as OOS validation.
3. The next clean evidence must be **prospective**: freeze the policy before race outcomes, record candidate decisions/inputs/odds before deadline, and settle only after the freeze.
4. September's already-protected unread outcomes should remain unread under the current handoff rule rather than being opportunistically converted into a retrospective holdout.
5. Production `HEAD4_V291_COMP7` remains unchanged until separate prospective evidence supports replacement and the user explicitly approves it.

Status: `FROZEN_WR_ST_PROVENANCE_AUDIT_COMPLETE_NO_HISTORICAL_HOLDOUT_PROSPECTIVE_VALIDATION_REQUIRED`.

### Next work unit

- Build/verify an **outcome-blind prospective shadow path** for frozen `B3_WR_ST` using the existing canonical data and frozen downstream S policy.
- The shadow path must emit/freeze race ID, timestamp, PRE/POST/ENV scores, S eligibility, opponent/ticket decision if applicable, and the actual pre-deadline odds snapshot/source before results are available.
- Do not use Sep historical outcomes to bootstrap the design. First freeze the prospective logging/decision specification itself.
- Jul/Aug remain NON-PRISTINE; September remains UNREAD; production remains unchanged.

## UPDATED NEXT CHAT START PROMPT — PROSPECTIVE ONLY

`boatrace-backtest の CHAT_HANDOFF_20260914_4HEAD_BOAT3_WAKU10_NEXT.md と最新GitHubを読んで続き。最新GitHubを優先し、作業前にBEFORE追記。B3_WR_STはfrozen research candidateだが、provenance監査で使えるuntouched historical windowは残っていないと確定済み。Jul/Aug outcome禁止・Sep outcome UNREADを維持し、過去結果を開かず、まずB3_WR_STのprospective shadow logging/decision pathを固定する。productionは変更しない。作業後にAFTER追記。`

## FROZEN WR_ST PROSPECTIVE SHADOW PATH — BEFORE (2026-09-14 JST)

- Start point: provenance audit AFTER commit `7df8e10ffa3a5f5a7c045cbc9dd787225cad5df0`.
- Objective: create or verify a prospective, result-blind shadow path for the already-frozen `B3_WR_ST` candidate; this is logging/decision infrastructure, not a model-selection exercise.
- Frozen model semantics: boat3 direct Waku10 `WR + ST` on the identical minimal non-Waku base; rolling training/scoring and downstream S thresholds remain unchanged (`PRE>=.28`, `POST>=.25`, `ENV_ENTRY>=.224790`).
- Required freeze payload before race result: race/date/venue, generated-at timestamp, source/input provenance, PRE, POST, ENV_ENTRY, S eligibility, downstream opponent/ticket decision if available, actual pre-deadline odds snapshot/source/timestamp if used, and a content hash or similarly immutable audit identifier.
- The shadow path must fail closed if required pre-result inputs are missing; it must not read target-race result/payout or use historical September outcomes.
- Jul/Aug remain NON-PRISTINE; September outcome remains UNREAD; production `HEAD4_V291_COMP7` remains unchanged.
- First implementation step: inspect current HEAD4 live/shadow entrypoints and odds fetch/snapshot utilities, then reuse the safest existing no-leak components rather than duplicating logic.
- Status: `FROZEN_WR_ST_PROSPECTIVE_SHADOW_PATH_STARTED`.
