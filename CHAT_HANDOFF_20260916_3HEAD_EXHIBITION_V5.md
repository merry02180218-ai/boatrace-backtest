# boatrace-backtest 3号艇モデル 引き継ぎ — Exhibition v5 / ticket-rescue

Repo: `merry02180218-ai/boatrace-backtest`
Branch: `research/3head-player-attack-mode`
Date: 2026-09-16〜17

## 最重要ルール
1. 最新GitHubと本引き継ぎを優先。
2. 作業前後に、予定・結果・commit SHA・Actions Run/Job/Artifact ID・結論・次の再開地点を記録。
3. September 2026 race outcomes は絶対に読まない。`UNREAD`維持。
4. production は v288 のまま変更しない。94R / 52 hits / ROI 172.560638%。
5. July/August 2026 は NON-PRISTINE。
6. 研究入力は締切前情報のみ。実際の決まり手を入力に使わない。
7. exact v288 94-race exclusion を維持。

## close-margin 4点目 AFTER
- Run `35126822479` SUCCESS / Job `104897800812` / Artifact `10459817578`
- script commit `259b267d20ad9658542c6319486af8948681451f`
- March only で margin を選択し `0.075` をfreeze。
- March: 192/472 -> 231/472 (+39), add 422。
- April: 154/414 -> 180/414 (+26), add 377。
- May: 212/563 -> 258/563 (+46), add 485。
- June: 195/544 -> 243/544 (+48), add 488。
- July/August NON-PRISTINE。September UNREAD。production unchanged。

## 2026-09-17 合成オッズROI監査 BEFORE
ユーザー確認: ROIは単純均等買いではなく、既存v288と同じ合成オッズ基準で評価する。
これからやること:
1. v288でROI 172.560638%を算出した既存の合成オッズ/資金配分定義をGitHubから特定する。
2. その定義を変更せず、既存3点と margin<=0.075 の4点化を比較する。
3. Marchは選択月、Apr-Junはfreeze OOS、Jul-AugはNON-PRISTINE参考のみ。
4. 月別の合成オッズ、投資、払戻、ROI差を出す。追加4点目単体の均等買いROIでは採否しない。
5. September outcomesは絶対に読まない。production v288は変更しない。

## 次の再開地点
v288合成オッズROI実装の特定 → ROI監査script/workflow実装 → Actions発火 → 結果をAFTER追記。
