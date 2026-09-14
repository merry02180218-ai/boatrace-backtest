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

Status: CORE_DECOMPOSITION_BEFORE_RECORDED
