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

## Wave18 AFTER
- Workflow: `wave18-wide-revalidation`。
- implementation commit: `0d3a65b51f99670cb0f82e79d1e8cc5c24d957c2`。
- workflow/head commit: `74e9d0a8d6785a9f3dbefebd9a93bcb2f1c28e41`。
- Run `35125138250` / Job `104892212739` / `success`。
- Artifact `10458594916`, SHA256 `f35892def32a056677a371421844af3d0cac5a074050266db843ac2b5db9b4ff`。
- Artifact実データを回収して確認。利用可能月は `202602,202603,202604,202605,202606`。Jul/Augは今回のWave10母集団には存在せず、holdoutはMay/Juneのみ。
- frozen policy: `CHOSEN_SECOND=3`, `CHOSEN_REPLACE_SLOT=2`, candidate=`1-3-5`。Feb-Aprのみでfreeze。
- holdout May-Jun 25R: baseline `5/25=20.0%` → fixed3 `7/25=28.0%`、Rescue `2` / Damage `0` / Net `+2`。24Rでoverride。
- 月別: May 11R baseline2→fixed3 3、Rescue1/Damage0/Net+1。June 14R baseline3→fixed3 4、Rescue1/Damage0/Net+1。
- schema別: `lap+turn` 6R baseline1→fixed3 2、Net+1。`lap+turn+straight` 19R baseline4→fixed3 5、Net+1。両schemaでプラス。
- strength bucket別: `[0.75,1.0)` 6R baseline2→fixed3 3、Net+1。`[1.5,inf)` 5R baseline1→fixed3 2、Net+1。`[-inf,0.75)` と `[1.0,1.5)` はNet0。Damageは全bucket 0。
- 場別: JCD13で3R baseline0→fixed3 1、Net+1。JCD24で2R baseline0→fixed3 1、Net+1。他場はNet0。特定1場だけのプラスではないが、各場サンプルは小さい。
- discovery側も April 5RでNet+1、Feb/MarはNet0。holdout May/Juneが各+1で連続したため、現時点では再現方向は維持。
- `SEPTEMBER_OUTCOMES_USED=False` / `HEAD_EXHIBITION_DIRECT_FEATURE=False` / `PRODUCTION_CHANGED=False` を確認。
- 重要: この検証は opponent mass `[.350,.375)` のproduction cutoff未満拡張帯。現行276R productionの3点を直接改善した検証ではない。よってproduction profileは変更しない。
- 結論: Wave17の `BOAT3_STRONGER -> 1-3-5 THIRD rescue / slot2 replacement` はMay/June holdoutで Damage 0 のNet+2を維持し、両schemaでも各+1。研究候補としてKEEP。ただしholdout 25R・救済2件のみで本採用には不足。
- 次の再開地点: Wave19でこの固定ルールを `[.350,.375)` の「追加購入候補」として評価し、対象25R全購入ではなく、strength bucket等の事前条件で発火を絞った場合の購入R数・的中増分・必要オッズ/損益分岐を検証する。結果を見て閾値を後付けせず、候補条件はdiscovery/holdoutを分離する。SeptemberはUNREAD維持。

## 現時点のproduction採否
- Wave17/18ルールは研究候補としてKEEP。
- production変更なし。
