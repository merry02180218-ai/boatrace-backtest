# CHAT HANDOFF — 2026-09-15 — 4HEAD ENV / V283 JUL-AUG OVERRIDE

## RULE OVERRIDE / USER APPROVAL

- 2026-09-15 JST: ユーザーから、4号艇モデルについて **2026年7月・8月は使用してよい** と明示承認あり。
- したがって、この作業単位以降は7月・8月の結果・履歴更新を、当日入力再現・履歴状態更新・検証に使用可とする。
- 旧 `CHAT_HANDOFF_20260914_4HEAD_BOAT3_WAKU10_NEXT.md` の「Jul/Aug outcome禁止」は、この作業単位では上記ユーザー承認で上書きする。
- 2026年9月の結果は引き続き **UNREAD / outcome-blind** を維持する。9月結果を入力補完・選択・閾値調整・検証に使わない。
- 4号艇production `HEAD4_V291_COMP7` はユーザーの明示承認なしに変更しない。
- 実投票・購入処理は追加しない。研究・再現・shadow入力監査に限定する。

## BEFORE — ENV 21項目 + v283 6艇×25項目 現在日取得・再現監査

- 作業開始時 latest main HEAD: `e11e75b9bcfd5f14cd586939b8a2bc91544d96b9`。
- 前作業の状態: `HEAD4_B3_WR_ST_SHADOW_V1` のcurrent-day source contractまでは完成。POST 7項目は取得系統がほぼ確定。残件はENV 21項目とv283 6艇×25項目の現在日取得・同一意味論再現。
- v283の既知系統: `v282.prep()` → `v279.build_source()` → `v270.prepare()` / `v274` / `v278`。当日展示6項目は `tkz / stt / original_exhibition` から生成。
- 重要な残件だった `pref_pl_*` 等の履歴系は、v221で日Dの特徴を凍結してから日D結果を履歴へ入れる因果的更新。今回から7月・8月結果を履歴状態更新に使えるため、9月時点までの状態再現可能性を再監査する。
- ENVは frozen 21 primitives の各生成元を `直接取得 / 決定的派生 / 過去状態 / 未解決` に分類する。
- v283は frozen SECOND 25 features を同じ分類で6艇分確認し、7・8月を含む履歴更新で9月当日まで再現できるか確認する。
- 9月 outcomeは絶対に読まない。production変更なし。閾値・重みの再調整なし。

Status: `ENV_V283_JULAUG_ALLOWED_AUDIT_STARTED`
