# CHAT HANDOFF — 2026-09-16 — 4HEAD RESCUE + CLOSE-MARGIN NEXT

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール
- 4号艇productionは作業開始時点で `HEAD4_V291_COMP7`。
- frozen opponentはv283: SECOND `PLAYER_START` / conditional THIRD `COND_BASE` / `TOP2XTOP2` / alpha2=.60。
- v96禁止。
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

## THIRD0.10 の正確な意味
- SECONDは従来どおりv283の上位2艇。
- 各SECOND候補 `s` ごとに conditional THIRD を順位付け。
- `P3(rank2|s) - P3(rank3|s) <= 0.10` のとき、そのSECOND枝だけTHIRD rank3を追加。
- それ以外は従来のTHIRD Top2。
- frozen base Top4を必ず保持し、追加対象だけ重複除去して足す。
- SECOND rescue/rank4 rescueは本採用しない。

## BEFORE — 2026-09-17 USER APPROVED PRODUCTION PROMOTION
ユーザーが `3着候補の僅差補正（差0.10以下）は本採用でいい` と明示承認。

次の作業:
1. `THIRD gap0.10` をshadowではなく4号艇production ticket policyへ正式昇格する。
2. 頭判定 `HEAD4_V291_COMP7` のPRE/POST/ENV_ENTRY閾値、v283 SECOND、alpha2=.60、comp>=7、締切前公式odds、10,000円Dutch、fail-closed、v96禁止は維持する。
3. 変更するのはv283 ticket expansionのみ。base Top4に、上記THIRD rank3 close-margin追加を行う。
4. ticket数が4固定ではなく4〜6点になり得るため、composite odds / Dutch / verifierの4点固定仮定を安全に可変点数対応へ変更する。全買い目を購入し、合計10,000円・100円単位を維持する。
5. 9月outcome/resultsは一切読まない。テストはsynthetic/pre-result入力のみで行う。
6. 実装後にコード差分・verifierを確認し、commit SHAとテスト結果をAFTERへ記録する。

Status: `THIRD010_PRODUCTION_PROMOTION_APPROVED_IN_PROGRESS`
