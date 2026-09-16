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

### New production runner
- file: `run_4head_v291_third010_live.py`
- commit: `376c636839af499821244ca660e382a43a16d644`
- policy name: `HEAD4_V291_COMP7_THIRD010`
- 旧 `run_20260911_4head_v291_live.py` をfrozen base helperとして再利用し、S gate / p2 / cond parser / official pre-deadline odds / audit persistenceは変更していない。
- base v283 Top4を先に生成し、Top2 SECOND各枝についてTHIRD rank2-rank3 gap<=0.10ならrank3を追加。
- 4〜6点の可変ticketに対応してcomposite oddsを再計算。
- BET時は全ticketを対象に10,000円Dutch、全stake正数・100円単位・合計10,000円を強制。
- comp>=7 inclusive、v96=false、result/payout未使用を維持。

### Offline synthetic verifier
- file: `verify_4head_v291_third010_live.py`
- commit: `760800671596c87334877217e1683223aa7a7879`
- 検証内容: 非発火時4点、両SECOND枝発火時6点、base Top4保持、gap exactly 0.10 inclusive、可変Nでcomp exactly 7 BET、10,000円/100円単位、below7 PASS、S gate NO_BET、v96禁止。
- race result/outcomeは参照しない。

### Validation workflow
- file: `.github/workflows/validate-4head-v291-third010-live.yml`
- commit: `695dab0796fc79fa6c27e1bff7f0d1ac33099287`
- `workflow_dispatch` only。多重/自動発火なし。
- 現在のGitHub connectorにはworkflow_dispatch起動actionが無いため、このチャットからRunはまだ発火していない。Run/Job/Artifact IDは未発行。発火していないものを成功扱いしない。

### Production status
- 本採用判断は確定。production ticket policyは `HEAD4_V291_COMP7_THIRD010`。
- ただし新verifierのGitHub Actions実行確認だけ未完了。workflowを1回手動発火後、Run/Jobを確認して最終CI記録する。
- 既存のfull post-exhibition automation自体は以前から未完成なので、今回の変更はproduction market/ticket entrypointの正式版として追加したもの。旧4点runnerを新規運用で使わないこと。
- September outcome/results=`UNREAD`。

## BEFORE — 2026-09-17 THIRD010 SIX-MONTH BACKTEST
ユーザー依頼: production `HEAD4_V291_COMP7_THIRD010` を半年バックテスト1回。
- 9月outcome/resultsは絶対に読まず `UNREAD` 維持。
- 既存の確定済み履歴データ/研究コードを再利用し、THIRD0.10 semanticsを固定して6か月集計する専用 `workflow_dispatch` を追加する。
- 月別/全体のrace数、ticket数、hit、stake、payout、profit、ROIをartifactへ出す。closing oddsを使う場合はretrospective diagnosticと明記し、formal prospective ROIとは扱わない。
- workflow作成後に正しいActions直リンクをユーザーへ渡し、手動発火後にRun/Job/Artifactを監査する。

Status: `THIRD010_SIX_MONTH_WORKFLOW_BUILDING`
