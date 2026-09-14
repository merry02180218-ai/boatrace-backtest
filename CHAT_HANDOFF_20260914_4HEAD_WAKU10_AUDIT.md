# CHAT HANDOFF — 2026-09-14 — 4HEAD WAKU10 COMPARISON AUDIT

## BEFORE WORK

- Scope: 4号艇モデルのみ。
- Resume point: 前チャットで進めていた **Waku10比較監査**。
- Productionは変更しない。現行4号艇production policyを固定したまま、Waku10情報の寄与を比較監査する。
- GitHub mainには `analyze_4head_waku10_ablation_20260914.py` と `.github/workflows/analyze-4head-waku10-ablation.yml` が存在することを確認。
- 比較variant: FULL_WAKU10 / NO_WAKU10 / CORE_WAKU10。
- downstreamは v264 -> v267 -> v271 -> v273 artifact freeze の同一chain。
- 主比較windowは2026-04〜06のみ。7月・8月はNON-PRISTINEなのでoutcomeを使った選定は禁止。9月outcomeも使わない。
- S/A threshold固定: S PRE>=.28, POST>=.25, ENV_ENTRY>=.224790; Aは非Sかつ PRE>=.18, POST>=.18, A_SCORE>=.28。
- archived odds ROIはretrospective proxy。

## RECOVERY SUMMARY

- v267/v271 settlement key normalizationを実施。
- zero-selector variantを異常ではなく0Rとして扱うようv267を修正。ただしselector>0でsettlement=0はfail-closed維持。
- 最終修正commit: `81da7e34d3f62ac10a6eeab28b638fa1988d0551`。

## AFTER WORK — WAKU10 ABLATION COMPLETE

- Official successful run: `34803857919` / job `103851724750` / conclusion `success`。
- FULL / NO / COREの3variant、Apr-Jun summary、artifact uploadまで全step success。
- Artifact: `head4-waku10-ablation` id `10332802959`。
- Apr-Jun ALL S:
  - FULL_WAKU10: 72R, head4 29/72=40.28%, trifecta 10/72=13.89%, proxy ROI 103.26%.
  - NO_WAKU10: 0R. Fixed S条件を突破する候補なし。
  - CORE_WAKU10: 57R, head4 19/57=33.33%, trifecta 9/57=15.79%, proxy ROI 123.69%.
- Apr-Jun ALL A:
  - FULL: 56R, trifecta 5, proxy ROI 74.36%.
  - NO: 14R, trifecta 2, proxy ROI 93.54%.
  - CORE: 67R, trifecta 6, proxy ROI 70.20%.
- Apr-Jun ALL S+A:
  - FULL: 128R, head4 50/128=39.06%, trifecta 15/128=11.72%, proxy ROI 90.61%.
  - NO: 14R, head4 6/14=42.86%, trifecta 2/14=14.29%, proxy ROI 93.54%.
  - CORE: 124R, head4 47/124=37.90%, trifecta 15/124=12.10%, proxy ROI 94.79%.
- Interpretation: Waku10 information is materially important to creating S-strength signals because NO produces 0 S races. CORE has the best S-layer efficiency of the three in this retrospective Apr-Jun audit, while FULL has higher head4 win rate but lower trifecta hit rate/ROI than CORE at S.
- Methodological caveat: FULL vs NO is confounded because NO removes several related/non-direct features; CORE vs NO is the cleaner direct incremental comparison. Therefore do not declare individual Waku10 fields causal yet.
- Jul/Aug remain NON-PRISTINE and are used only for score-distribution stress; September outcomes remain unused.
- Production remains unchanged.

## CORE DECOMPOSITION — BEFORE

Next work unit is a clean decomposition inside CORE_WAKU10, keeping the same non-Waku base and changing only direct Waku10 fields. No production/threshold/ticket changes.

Planned variants:
1. BASE = current NO_WAKU10 minimal base.
2. B3_ONLY = BASE + boat3 `waku_wr / waku_st / waku_sr`.
3. B4_ONLY = BASE + boat4 `waku_wr / waku_st / waku_sr`.
4. WR_ONLY = BASE + boat3/4 `waku_wr`.
5. ST_ONLY = BASE + boat3/4 `waku_st`.
6. SR_ONLY = BASE + boat3/4 `waku_sr`.
7. WR_ST = BASE + boat3/4 `waku_wr + waku_st`.
8. WR_SR = BASE + boat3/4 `waku_wr + waku_sr`.
9. ST_SR = BASE + boat3/4 `waku_st + waku_sr`.
10. CORE_ALL = BASE + boat3/4 all six direct Waku10 fields.

Evaluation:
- identical rolling training/scoring and frozen downstream policy;
- model selection evidence only Apr-Jun 2026;
- compare S first: R, head4 rate, trifecta hit rate, proxy ROI, avg composite odds;
- A/S+A secondary;
- Jul/Aug score distribution only; no outcomes;
- September outcomes unused;
- production unchanged until explicit user approval.

## CORE DECOMPOSITION — AFTER

- Official successful run: `34808568480` / job `103865187359` / conclusion `success`.
- Head SHA: `514c4a61103dba105816886c674f753e17c34f3e`.
- Artifact: `head4-waku10-core-decomposition`, id `10335502943`, digest `sha256:a8bf915fa953128d104d0e440f1db09957fa78255ecdc4003b2fe3ee3564d2d4`.
- All workflow steps succeeded, including direct decomposition, Apr-Jun summary, and artifact upload.
- Audit JSON confirms: `production_modified=false`, selection window=`Apr-Jun 2026 only`, Jul-Aug=`score distributions only; outcomes unused`, `september_outcomes_used=false`, archived odds ROI is retrospective proxy.

### Apr-Jun S-layer results

- NO_WAKU10: 0R.
- B3_ONLY: 38R, head4 17/38=44.74%, trifecta 10/38=26.32%, proxy ROI 203.997%, avg comp odds 7.6803.
- B4_ONLY: 1R, head4 0%, trifecta 0%, proxy ROI 0%.
- WR_ONLY: 27R, head4 8/27=29.63%, trifecta 4/27=14.81%, proxy ROI 108.622%, avg comp odds 7.6310.
- ST_ONLY: 13R, head4 6/13=46.15%, trifecta 5/13=38.46%, proxy ROI 284.054%, avg comp odds 7.5747.
- SR_ONLY: 14R, head4 3/14=21.43%, trifecta 2/14=14.29%, proxy ROI 80.314%, avg comp odds 7.5493.
- WR_ST: 50R, head4 17/50=34.00%, trifecta 9/50=18.00%, proxy ROI 141.012%, avg comp odds 7.8973.
- WR_SR: 50R, head4 15/50=30.00%, trifecta 7/50=14.00%, proxy ROI 110.670%, avg comp odds 7.4631.
- ST_SR: 18R, head4 6/18=33.33%, trifecta 4/18=22.22%, proxy ROI 143.367%, avg comp odds 7.8911.
- CORE_WAKU10: 57R, head4 19/57=33.33%, trifecta 9/57=15.79%, proxy ROI 123.695%, avg comp odds 7.7255.

### Apr-Jun A and S+A secondary checks

- B3_ONLY S+A: 111R, head4 42/111=37.84%, trifecta 12/111=10.81%, proxy ROI 79.34%.
- ST_ONLY S+A: 67R, head4 27/67=40.30%, trifecta 9/67=13.43%, proxy ROI 98.84%.
- WR_ST S+A: 121R, head4 47/121=38.84%, trifecta 14/121=11.57%, proxy ROI 89.44%.
- CORE_WAKU10 S+A: 124R, head4 47/124=37.90%, trifecta 15/124=12.10%, proxy ROI 94.79%.
- NO_WAKU10 S+A: 14R, head4 6/14=42.86%, trifecta 2/14=14.29%, proxy ROI 93.54%.

### Interpretation

1. The dominant direct Waku10 information is on **boat3**, not boat4. B3_ONLY creates 38 S races with strong head4 and trifecta performance, while B4_ONLY creates only 1 S race.
2. By field type, **ST is the strongest single signal** in this sample: ST_ONLY has the best S head4 rate, trifecta hit rate, and proxy ROI, but only 13 races, so it is too small to crown as production choice by itself.
3. **WR_ST is the best broader two-field candidate**: 50 S races, 18% trifecta hit rate, 141.0% proxy ROI. It gives much better sample size than ST_ONLY while outperforming CORE_ALL on S trifecta efficiency/ROI.
4. SR is weak alone. SR_ONLY has sub-100% S proxy ROI and low head4 rate. Adding SR to WR or ST does not beat WR_ST on the primary S balance.
5. CORE_ALL increases S volume to 57R but dilutes S efficiency versus WR_ST. This suggests SR and/or boat4 direct fields mainly broaden the score tail rather than improve the highest-quality S set.
6. B3_ONLY is especially notable: 38R, 44.7% head4, 26.3% trifecta, 204.0% proxy ROI. Because it bundles WR/ST/SR on boat3, the next clean test should decompose **boat3-only WR vs ST vs SR and pairwise combinations** to determine whether B3 strength is mostly ST-driven or requires boat3 interactions.
7. Jul/Aug remain NON-PRISTINE: only score-distribution stress was reviewed; no Jul/Aug outcomes were used for selection.
8. September outcomes remain unread/unused.
9. Production remains unchanged.

### Current research ranking

- Tier 1: `B3_ONLY`, `WR_ST`.
- High-efficiency / small-N signal: `ST_ONLY`.
- Secondary: `CORE_WAKU10`, `ST_SR`, `WR_SR`, `WR_ONLY`.
- Weak: `SR_ONLY`, `B4_ONLY`, `NO_WAKU10`.

### Next work unit

Before any production change, run a **boat3 direct-Waku10 decomposition** on the same base and same Apr-Jun-only selection window:
- B3_WR_ONLY
- B3_ST_ONLY
- B3_SR_ONLY
- B3_WR_ST
- B3_WR_SR
- B3_ST_SR
- B3_ALL (= current B3_ONLY)

Keep downstream policy frozen. Jul/Aug score stress only, Sep outcome blind, production unchanged.

Status: CORE_DECOMPOSITION_COMPLETE

## BOAT3 DIRECT-WAKU10 DECOMPOSITION — BEFORE

- Start the next research unit exactly from the completed CORE decomposition above.
- Objective: determine whether the strong `B3_ONLY` result is mainly driven by boat3 ST, boat3 WR, boat3 SR, or a boat3-only interaction.
- Variants on the identical minimal non-Waku base: `B3_WR_ONLY`, `B3_ST_ONLY`, `B3_SR_ONLY`, `B3_WR_ST`, `B3_WR_SR`, `B3_ST_SR`, `B3_ALL`.
- Keep rolling training/scoring, v264 -> v267 -> v271 -> v273 downstream chain, S/A thresholds, opponent/ticket policy, and archived-odds ROI calculation frozen.
- Primary selection evidence: Apr-Jun 2026 S layer (R, head4 rate, trifecta hit rate, proxy ROI, avg composite odds), with A/S+A secondary.
- Jul/Aug 2026 remain NON-PRISTINE and may be used only for score-distribution stress; their outcomes are forbidden for selection.
- September 2026 outcomes remain unread/unused.
- Production remains unchanged. No production promotion from this work unit without explicit approval.

Status: BOAT3_DECOMPOSITION_BEFORE_RECORDED

## BOAT3 WORKFLOW/CACHE CORRECTION — BEFORE

- Audit found that commit `0e150b6dae669fa25c709646b716cf0b37d933d5` added the boat3 variants to the Python scorer, but `.github/workflows/analyze-4head-waku10-ablation.yml` still loops the prior 10 CORE-decomposition variants. Therefore run `34815749150` is not a valid boat3-decomposition run even if it completes; do not use it as boat3 selection evidence.
- Correct the workflow to run exactly: `B3_WR_ONLY B3_ST_ONLY B3_SR_ONLY B3_WR_ST B3_WR_SR B3_ST_SR B3_ALL`.
- Correct the summary logic so selection metrics explicitly filter `month` to `2026-04`, `2026-05`, `2026-06` before S/A/S+A aggregation. Jul/Aug outcomes remain forbidden and are only used in the separate score-stress table.
- Performance optimization requested by user: the expensive common feature dataset produced by `build_data()` is invariant across variants, so build it once per workflow run and persist it as a local pickle cache on the runner; all boat3 variants then load that cache. This must not alter feature values, train/test windows, model settings, thresholds, downstream chain, or results.
- September outcomes remain unread/unused and production remains unchanged.

Status: BOAT3_WORKFLOW_CACHE_CORRECTION_BEFORE_RECORDED

## BOAT3 WORKFLOW/CACHE CORRECTION — AFTER

- BEFORE was recorded before code/workflow changes.
- Common-feature caching implemented in `analyze_4head_waku10_ablation_20260914.py` via `--data-cache`; first variant builds/writes the invariant feature frame, subsequent variants use `pd.read_pickle` on the same runner. Commit: `23e354a8ac6f6bd92322653228b601695f0c828b`.
- Workflow corrected to execute exactly the seven boat3 variants and pass a shared cache path: `B3_WR_ONLY B3_ST_ONLY B3_SR_ONLY B3_WR_ST B3_WR_SR B3_ST_SR B3_ALL`.
- Workflow summary now explicitly filters Apr-Jun (`2026-04/05/06`) before S/A/S+A outcome aggregation; Jul/Aug remain separate score-distribution stress only.
- Output/artifact names changed to boat3-specific names to avoid confusing this run with the completed CORE decomposition.
- Workflow correction/cache commit: `8b9ea8b1bda75d82acaa4f2741540571bd0f0203`.
- The earlier run `34815749150` is explicitly invalid for boat3 selection because it used the old workflow variant loop; ignore its outcome metrics for this research question.
- Production remains unchanged; September outcomes remain unread/unused.

Status: BOAT3_WORKFLOW_CACHE_CORRECTION_COMPLETE
