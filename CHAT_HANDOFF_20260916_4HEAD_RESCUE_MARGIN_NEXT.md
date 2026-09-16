# CHAT HANDOFF — 2026-09-16 — 4HEAD RESCUE + CLOSE-MARGIN NEXT

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール
- 4号艇production ticket policyは `HEAD4_V291_COMP7_THIRD010`。
- 頭判定S layerは従来 `HEAD4_V291_COMP7` と同じPRE>=0.28 / POST>=0.25 / ENV_ENTRY>=0.224790。
- frozen opponentはv283: SECOND `PLAYER_START` / conditional THIRD `COND_BASE` / `TOP2XTOP2` / alpha2=.60。
- v96禁止。締切前公式oddsのみ。comp>=7。10,000円Dutch。fail closed。
- 2026年9月のレース結果/outcomeは絶対に読まない。`UNREAD`維持。
- closing odds評価はretrospective diagnosticのみ。formal prospective ROI=`NOT_COMPUTABLE`。
- 作業前後にこの引き継ぎへBEFORE/AFTERを追記し、Run/Job/Artifact/commit SHAを正確に残す。

## 確定監査要約
- fixed candidate Apr-Jun: 86R / 35頭 / 40.6977%。Jul-Aug: 78R / 35頭 / 44.8718%。Apr-Aug: 164R / 70頭。
- base4 Apr-Aug: 656 tickets / 29 hits / ROI 129.71%。
- THIRD gap0.10: Apr-Jun ROI 153.11% / 19 hits、Jul-Aug 115.35% / 16 hits、Apr-Aug 817 tickets / 35 hits / ROI 135.13%。
- 月別 THIRD0.10: Apr 211.89%, May 120.36%, Jun 138.48%, Jul 141.72%, Aug 75.96%。
- SECOND0.20 Apr-Aug ROI 122.63%、COMBINED 126.14%。rank4 gap24 0.05/0.06はdevelopment期間で救済0件のためREJECT。
- THIRD close-margin audit Run `35074469211` / Job `104723453680` / Artifact `10437831280`。
- strict comparison source Run `35089336519` / Job `104771656556` / Artifact `10443723290`。
- fixed gap audit Run `35119432005` / Job `104873127479` / Artifact `10456963422`。

## THIRD0.10 production semantics
- SECONDは従来どおりv283上位2艇。
- 各SECOND候補 `s` ごとに conditional THIRD を順位付け。
- `P3(rank2|s) - P3(rank3|s) <= 0.10`（inclusive）のとき、そのSECOND枝だけTHIRD rank3を追加。
- frozen base Top4を必ず保持し、追加対象だけ重複除去して足す。
- production ticket数は4〜6点。
- SECOND rescue/rank4 rescueは採用しない。

## BEFORE — 2026-09-17 USER APPROVED PRODUCTION PROMOTION
ユーザーが `3着候補の僅差補正（差0.10以下）は本採用でいい` と明示承認。
- shadow案を撤回し、THIRD0.10をproduction ticket policyへ昇格する。
- 9月outcome/resultsは読まずsynthetic/pre-resultだけで実装確認する。

## AFTER — THIRD0.10 production implementation
実装済み。
- runner `run_4head_v291_third010_live.py` commit `376c636839af499821244ca660e382a43a16d644`
- verifier `verify_4head_v291_third010_live.py` commit `760800671596c87334877217e1683223aa7a7879`
- validation workflow `.github/workflows/validate-4head-v291-third010-live.yml` commit `695dab0796fc79fa6c27e1bff7f0d1ac33099287`
- September outcome/results=`UNREAD`。

## BEFORE — 2026-09-17 THIRD010 SIX-MONTH BACKTEST
ユーザー依頼: production `HEAD4_V291_COMP7_THIRD010` を半年バックテスト1回。
- 9月outcome/resultsは絶対に読まず `UNREAD` 維持。
- 既存の確定済み履歴データ/研究コードを再利用し、THIRD0.10 semanticsを固定して6か月集計する専用 `workflow_dispatch` を追加する。
- 月別/全体のrace数、ticket数、hit、stake、payout、profit、ROIをartifactへ出す。closing oddsを使う場合はretrospective diagnosticと明記し、formal prospective ROIとは扱わない。

## AFTER — 2026-09-17 SIX-MONTH WORKFLOW READY
- script: `backtest_4head_v291_third010_sixmonth.py`
- script commit: `b4c64870d2e3fbbcf754e8287ba3293c343eaace`
- workflow: `.github/workflows/backtest-4head-v291-third010-sixmonth.yml`
- workflow commit: `cb6077647dc916a75159c38f64a319aadce30ee8`
- workflow is `workflow_dispatch` only and uploads artifact `head4-third010-sixmonth`.
- window is fixed to 2026-03-01..2026-08-31; September is not read.
- IMPORTANT fail-closed guard: current strict source reconstruction was previously audited Apr-Aug. The new runner requires all six months Mar-Aug and will FAIL rather than mislabel five months as six if March is not supplied by the frozen reconstruction path. If it fails on this guard, next work is to extend the frozen candidate reconstruction to March without touching September, then rerun.
- Run/Job/Artifact: pending manual dispatch; do not claim success before observed.

## BEFORE — 2026-09-17 SIX-MONTH FAILURE RECOVERY
Observed Run `35121865532` / Job `104881369251` failed closed because reconstructed source contains Apr-Aug only; March is missing.
User instructed: fix any other concerns and continue.
Plan before code changes:
1. inspect the dedicated six-month script/workflow and frozen reconstruction source rather than merely bypassing the month guard;
2. extend the same frozen candidate/model reconstruction to March 2026 without reading September;
3. audit for additional risks: accidental September reads, inconsistent month windows, changed model semantics, look-ahead/result leakage in candidate selection, closing-odds labeling, variable 4-6 ticket staking/composite-odds handling, and incomplete artifact-on-failure behavior;
4. keep fail-closed guards for all six months and production semantics;
5. commit fixes, update this handoff AFTER, then dispatch only when a valid workflow path exists and report exact Run/Job/Artifact.
September outcome/results remains `UNREAD`.

Status: `THIRD010_SIX_MONTH_RECOVERY_IN_PROGRESS`
