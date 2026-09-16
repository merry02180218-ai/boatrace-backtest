# 1号艇 v351 Wave17 引き継ぎ

## BEFORE — 2026-09-17

### 再開元
- `CHAT_HANDOFF_20260915_1HEAD_MANUAL_LIVE.md` と最新mainを確認済み。
- Wave16 Run `35117299447` / Job `104865855255` は success。
- Artifact `10456373385` (`wave16-temporal-stability`) まで確認済み。
- Wave16では Wave15仮説 `BOAT3_STRONGER -> boat5` が May 4/7=57.1%, June 6/11=54.5% と残り、特に June は boat5 の該当6件が全てTHIRDだった。

### これからやること
1. Wave17として `BOAT3_STRONGER` / `CLEAR_>=0.50` 時の boat5 を「3着救済候補」として監査する。
2. 結果依存でルールを作らない。Feb-Aprを発見/選択側、May/Juneをfrozen検証側として扱う。
3. 現行HYBRID 3点をbaselineとし、3着5号艇を入れる場合の rescue / damage / net を明示する。
4. 可能なら3点固定の置換監査と、追加券としての救済上限を分けて出す。baselineを壊さず追加するケースと、3点固定で1枚置換するケースを混同しない。
5. 現行production 276R基準との関係を明示する。Wave10以降の `[0.350,0.375)` は現行 opponent-mass cutoff `.375` 未満の研究帯なので、276R既存購入内の単純置換なのか、購入対象拡張なのかを必ず区別する。
6. September 2026 outcomes/payouts は絶対に読まない。`race_code < 20260901` hard guard、`SEPTEMBER_OUTCOMES_USED False` を維持。
7. HEAD学習特徴へ展示を直接追加しない。post-ranking / ticket-rescue研究のみ。
8. productionは検証完了まで変更しない。

### 現行production基準
- profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- HEAD cutoff `.78`
- opponent mass cutoff `.375`
- final purchases 276R
- boat1 win 241/276 = 87.32%
- exact trifecta 3-ticket hit 131/276 = 47.46%

### 次の記録
Wave17完了後、このファイルへ AFTER として commit SHA / Actions Run / Job / Artifact / 対象R / baseline / rescue / damage / net / production採否 / 次の再開地点を追記する。
