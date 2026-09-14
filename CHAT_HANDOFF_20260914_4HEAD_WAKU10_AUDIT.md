# CHAT HANDOFF — 2026-09-14 — 4HEAD WAKU10 COMPARISON AUDIT

## BEFORE WORK

- Scope: 4号艇モデルのみ。
- Resume point: 前チャットで進めていた **Waku10比較監査**。
- Productionは変更しない。現行4号艇production policyを固定したまま、Waku10情報の寄与を比較監査する。
- GitHub mainには `analyze_4head_waku10_ablation_20260914.py` と `.github/workflows/analyze-4head-waku10-ablation.yml` が存在することを確認。
- 比較variant:
  - `FULL_WAKU10`: 現行full feature側
  - `NO_WAKU10`: Waku10由来/関連featureを外した側
  - `CORE_WAKU10`: 艇3/艇4の `waku_wr / waku_st / waku_sr` を直接入れる側
- downstreamは v264 -> v267 -> v271 -> v273 artifact freeze の同一chainを通す。
- 主比較windowは **2026-04〜06のみ**。7月・8月はNON-PRISTINEなので、outcomeを使った選定は禁止。workflowでも7/8月はscore distribution stressだけを見る。
- 9月outcomeはこの監査に使わない。
- S/A thresholdは固定: S PRE>=.28, POST>=.25, ENV_ENTRY>=.224790; Aは非Sかつ PRE>=.18, POST>=.18, A_SCORE>=.28。
- archived oddsを使うROIはretrospective proxyであり、immutable contemporaneous LIVE oddsとは扱わない。

## THIS WORK

1. Waku10 ablation workflow/codeの比較定義とguardを監査。
2. 最新workflow run/commit状態を確認し、比較結果が既に出ていれば取得する。
3. FULL / NO / COREをApr-Jun同一policyで比較し、Waku10の実寄与を判定する。
4. 監査完了後、このhandoffに結果・採否・次作業を追記する。

## RECOVERY WORK — BEFORE

- Failed run recovered: Waku10 guards and common opponent-context build completed, then the three-variant downstream step failed before summary/artifact upload.
- Confirmed failure point: FULL_WAKU10 completed its variant scoring and v264 stage, then v267 raised `RuntimeError: no settled rows available for v267`.
- Therefore there is not yet a valid FULL/NO/CORE comparison result to interpret.
- This repair is plumbing-only: do not relax/tune model thresholds, do not alter production, and do not use Jul/Aug outcomes or any September outcomes.
- Immediate work unit:
  1. inspect v267 input contract and the ablation workflow handoff between v264 and v267;
  2. fix settlement-row propagation so v267 receives the intended Apr-Jun settled rows under the same frozen policy;
  3. rerun FULL_WAKU10 / NO_WAKU10 / CORE_WAKU10 through the identical downstream chain;
  4. recover Apr-Jun race count, 4-head rate, trifecta hit rate and retrospective proxy ROI plus any configured score-distribution stress output;
  5. append the exact fix, run id, results, decision, and next step here after completion.

## RECOVERY ITERATION 2 — BEFORE

- Official rerun with both v267/v271 normalization fixes identified as Actions run `34788716350`; it still failed in the three-variant downstream step before summary/artifact upload.
- The previous normalization fix was therefore insufficient. Do not guess at Waku10 performance from this failure.
- Next repair is diagnostic-first and plumbing-only: persist selector/order/actual/odds settlement counts even on failure, upload diagnostics on failed runs, then use the observed zero/mismatch stage to repair the exact input contract.
- No threshold, feature ranking, ticket rule, production rule, Jul/Aug outcome usage, or September outcome usage may change in this iteration.
- After diagnostics identify the mismatch, rerun the same FULL/NO/CORE chain and only then collect Apr-Jun comparison results.

Status: RECOVERY_ITERATION_2_BEFORE_RECORDED
