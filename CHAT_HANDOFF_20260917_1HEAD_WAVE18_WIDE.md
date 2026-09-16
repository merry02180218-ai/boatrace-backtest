# 1号艇 v351 Wave18 広域再検証 引き継ぎ — 2026-09-17

## 絶対ルール
- September 2026 結果・払戻は `UNREAD` 維持。研究は `race_code < 20260901` hard guard。
- production profile は `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100` のまま。
- production基準: 最終購入276R / 1号艇1着241=87.32% / 3連単3点131=47.46%。
- 展示をHEAD学習特徴へ直接追加しない。post-ranking / ticket-rescue研究のみ。
- 本番変更は独立検証で安定したプラスを確認するまで行わない。

## Wave16 AFTER
- Run `35117299447` / Job `104865855255` / success。
- Artifact `10456373385`, SHA256 `d0353af6e81cee90d50c8b6186c483423ab7ee391f590fe370b4c5d3dcaa1e20`。
- 2〜4月frozen選択は 2優勢→4、3優勢→4。
- Wave15探索ルール 3優勢→5 は May 4/7=57.1%、June 6/11=54.5%、May+June 10/18=55.6%。Juneの6的中はすべてTHIRD。
- 2優勢→4 は May 58.3% から June 22.2%へ崩れ不安定。
- 結論: 一括採用なし。3優勢→5のTHIRD rescueを次段階へ。production変更なし。September UNREAD。

## Wave17 AFTER
- Run `35121544745` / Job `104880297105` / success。
- Artifact `10457559499`。
- 対象は opponent mass `[.350,.375)`、main schema、BOAT3_STRONGER `CLEAR>=0.50`。
- Feb-AprでSECOND partnerと3点固定replacement slotを選択し、May-Junへ完全freeze。
- May-Jun frozen 25R: baseline 5/25、fixed3 7/25、Rescue 2 / Damage 0 / Net +2。
- 月別も May +1、June +1。
- ただし276R productionを直接変更した検証ではなく、production cutoff未満の救済・拡張研究。production変更なし。September UNREAD。

## Wave18 BEFORE — ユーザー承認済み
ユーザー指示: 「広く再検証して」

### これからやること
1. Wave17のルールを結果を見て変更せず固定する。
2. Wave10で構築した historical `[.350,.375)` 母集団のうち、利用可能な全月を対象に月別・場別・schema別・強度差bucket別へ広げて再検証する。
3. Feb-Aprは discovery として明示的に分離し、May以降を holdout として集計する。利用可能ならJul/Augも含める。
4. Wave17でfreezeした SECOND partner / replacement slot をそのまま使い、baseline / candidate / fixed3 rescue / damage / net を測る。
5. 3優勢→5が特定月・特定場だけの偶然でないか、対象数と分布を確認する。
6. September 2026 outcomes/payoutsは絶対に読まない。`race_code < 20260901` hard guardを維持する。
7. 完了後、commit SHA / Run / Job / Artifact / 月別・場別・schema別結果 / production採否 / 次研究地点をAFTER追記する。

## 現時点のproduction採否
- Wave17ルールはまだ研究段階。production変更なし。
