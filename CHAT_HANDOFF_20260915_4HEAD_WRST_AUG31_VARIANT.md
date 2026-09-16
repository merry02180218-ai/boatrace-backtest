# CHAT HANDOFF — 2026-09-15 — 4HEAD WR_ST AUG31 HISTORY VARIANT

## CURRENT RULES
- 2026年7月・8月結果は学習・検証に使用可。
- 2026年9月結果は `UNREAD` 維持。
- production `HEAD4_V291_COMP7` は変更しない。

## KEY AUDITED STATE
- 4-head fixed candidate: Apr-Jun 86R / 35頭 / 40.6977%; Jul-Aug 78R / 35頭 / 44.8718%。
- frozen opponent v283: SECOND `PLAYER_START`, conditional THIRD `COND_BASE`, `TOP2XTOP2`, alpha2=.60, Top4 exactly 4 tickets。v96禁止。
- final closing-odds audit Run `35060311090` / Job `104679045711` / Artifact `10432272637`: success, coverage 164/164, Apr-Aug ROI 129.71%。
- Apr-Jun ROI 167.73%、Jul-Aug ROI 87.79%。4頭時capture 51.43%→31.43%。
- retrospective diagnosticのみ。formal prospective ROI=`NOT_COMPUTABLE`。Sep `UNREAD`、production unchanged。

## BEFORE — v283 opponent miss decomposition
- ユーザー指示「お願いします」。4号艇が実際に頭だった70Rへ実着2着/3着を付け、v283の失敗を厳密分解する。
- `SECOND miss` / `THIRD miss` / `pair-ranking miss` をApr-Jun vs Jul-Aug、月別で分離する。
- frozen v283のスコアリング・候補条件・productionは変更しない。v96禁止。Sep `UNREAD`。
- BEFORE handoff commit `579ec0ff1673919c0bc9a9a7e76b7ce2d60a910b`。

## AFTER / READY — v283 opponent miss decomposition implementation
- 新規 `analyze_4head_v283_miss_decomposition.py` commit `15c0f5d1dc59270d5f3e33ede3eded8167c9d6d7`。
- 164Rから4号艇実頭70Rだけを診断し、実2着/3着、SECOND Top2、actual-second条件のTHIRD Top2、最終Top4を保存する。
- miss_stageは `SECOND_MISS` → `THIRD_MISS` → `PAIR_RANK_MISS` → `CAPTURE` の順で排他的に分類。
- TOP2XTOP2ではSECONDとconditional THIRDの双方がTop2なら原理上4組poolに入るため、PAIR_RANK_MISSが出るなら実装/parity異常の検知にもなる。
- 手動workflow `.github/workflows/analyze-4head-v283-miss-decomposition.yml` commit `f8a454e4e6a78962c8057cf8194c2ae01d6fcb5d`。`workflow_dispatch` onlyで多重発火なし。
- 出力: `/tmp/head4_v283_miss_decomp/head4_70r_miss_detail.csv`, `miss_summary.csv`, `meta.json`。
- 次: workflowを1回手動発火し、Run/Job/ArtifactとApr-Jun vs Jul-AugのSECOND/THIRD miss件数を確定する。
- production `HEAD4_V291_COMP7` / frozen v283 unchanged。formal prospective ROI=`NOT_COMPUTABLE`。September outcome/results `UNREAD`。

Status: `HEAD4_V283_OPPONENT_MISS_DECOMPOSITION_READY_TO_RUN`
