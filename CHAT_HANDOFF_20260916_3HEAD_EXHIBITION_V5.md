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

## 2026-09-17 合成オッズROI監査 INVALID AFTER
- Run `35131305385` SUCCESS / Job `104912706361` / Artifact `10460683745`。
- ただし対象が v288 production 実BET 94Rではなく、Apr-Jun の3号艇頭評価母集団 1521Rだったため採否判断から除外。
- 608.65% -> 610.34% は production ROI 比較として無効。production unchanged。

## 2026-09-17 exact v288 94R ROI再監査 BEFORE
ユーザー確認: v288で実際に買う94Rだけを対象に再監査する。
これからやること:
1. v288 production の実BET 94Rを既存production実装/監査成果物から完全再現し、まず R=94 / hits=52 / ROI=172.560638% をassertする。
2. 94Rの既存3点買い目・合成オッズ資金配分を変更せず再現する。
3. その94Rだけに、rank3-rank4 score差 <= 0.075 の場合だけrank4を4点目として追加する。
4. 1R投資10,000円固定、v288と同一の逆オッズDutch + 100円Hamiltonで現行3点 vs 条件付き4点を比較する。
5. baseline再現assertに失敗した場合はROI比較を出さず、原因修正を優先する。
6. September outcomesは絶対に読まない。July/AugustはNON-PRISTINE。productionは変更しない。

## 次の再開地点
exact v288 94R portfolio source特定 → baseline 94R/52hits/172.560638% assert → 0.075条件付き4点ROI監査 → Actions結果 → AFTER追記。
