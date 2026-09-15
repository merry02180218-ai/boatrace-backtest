# 1号艇 v351 手動LIVE 引き継ぎ — 2026-09-15

## 最重要ルール
- 最新GitHubを最優先。
- 1号艇LIVE productionは v351。production gate/finalizerの条件は勝手に変更しない。
- LIVE判定でレース結果・払戻を使用しない。`result_or_payout_used=False` / `chronology_guard=True` を維持。
- GitHub作業は必ず、この引き継ぎへ作業前の予定を記録してから開始し、作業後に結果・commit SHA・Run/Job/Artifact ID・結論・次の再開地点を追記する。

## 現在の運用方針
- 1号艇v351の自動cron/controllerは停止済み。
- ユーザーが判別を要求した時だけ取得・判定する手動LIVE方式。

## 完了済み — 完全任意レース対応
- オンデマンドbase生成script: `bc9c7d4f1628a5c0b09a491b7ba4213dbdc5648b`
- manual workflow fallback接続: `ef18e95d6de8ff4a301e96a196c9d6e1fcae53ed`
- PRE候補外・shared cache外でも同日のrace_cardsからcausal baseを生成可能。

## 作業前記録 — Chat起動用request bridge
ユーザー指示: 「それでお願い。明記して」

### 問題
- 現在のChat側GitHub接続では新規workflow_dispatchを直接開始できない。
- workflow_dispatchだけでは、ユーザーの判別要求からChatがactual LIVE処理を開始できない。

### これから行うこと
1. Chatから利用可能なGitHub file create/updateをLIVE要求の入口にする。
2. 専用request pathへの変更だけで起動するworkflowを追加する。
3. request内のrace_codeを読み、既存v351処理へ渡す。
4. 通常push全般では起動せず、専用request pathだけに限定する。
5. 定期cron/controllerは復活させない。ユーザー要求時だけ起動する。
6. 結果・払戻は使用せず、締切後はfail-closeする。
7. 完了後、実装commit SHA・検証Run/Job/Artifact ID・結論・次の再開地点を追記する。
8. 今後の判別要求は request commit → Actions起動確認 → Run監視 → Artifact回収 → BUY/DROPと買い目返却までを一連のLIVE作業とする。
