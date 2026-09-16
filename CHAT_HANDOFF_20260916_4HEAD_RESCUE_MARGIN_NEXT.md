# CHAT HANDOFF — 2026-09-16 — 4HEAD RESCUE + CLOSE-MARGIN NEXT

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール
- 4号艇productionは `HEAD4_V291_COMP7`。研究中は変更しない。
- frozen opponentはv283: SECOND `PLAYER_START` / conditional THIRD `COND_BASE` / `TOP2XTOP2` / alpha2=.60 / exactly Top4=4点。
- v96禁止。
- 2026年9月のレース結果/outcomeは絶対に読まない。`UNREAD`維持。
- Jul/Aug 2026結果は使用可。
- closing odds評価はretrospective diagnosticのみ。formal prospective ROI=`NOT_COMPUTABLE`。
- 作業前後にこの引き継ぎへBEFORE/AFTERを追記し、Run/Job/Artifact/commit SHAを正確に残す。
- Actionsの多重発火を避ける。新規研究workflowは`workflow_dispatch` onlyを基本とする。

## 確定済み母集団/成績
- fixed candidate Apr-Jun: 86R / 35頭 / 40.6977%。
- Jul-Aug: 78R / 35頭 / 44.8718%。
- Apr-Aug: 164R / 70頭。
- closing odds final audit Run `35060311090` / Job `104679045711` / Artifact `10432272637`。
- Apr-Jun ROI 167.73%、Jul-Aug 87.79%、Apr-Aug 129.71%。retrospective only。
- 4号艇頭率はJul-Augで悪化していないため、ROI低下の主因は相手capture。

## v283 miss decomposition
Run `35061928492` / Job `104683888325` / Artifact `10432044277`, success, marker `HEAD4_V283_MISS_DECOMPOSITION_OK`。
- Apr-Jun actual 4-head 35R: HIT 18, SECOND miss 14, THIRD miss 3, pair-rank miss 0。SECOND-pass conditional THIRD capture 18/21=85.71%。
- Jul-Aug actual 4-head 35R: HIT 11, SECOND miss 16, THIRD miss 8, pair-rank miss 0。SECOND-pass conditional THIRD capture 11/19=57.89%。
- July: actual head4 24、SECOND miss 11、SECOND-pass 13、HIT 6、THIRD miss 7。conditional THIRD capture 6/13=46.15%。
- August: SECOND-pass 6、HIT 5、THIRD miss 1。conditional THIRD capture 5/6=83.33%。
- pair-ranking missは0。alpha2/joint pair rankは観測上の主因ではない。

## July conditional THIRD diagnostic
- 初回 Run `35063523492` / Job `104688743645` はlist/DataFrame型ミスで失敗。
- fix commit `e2081cb81991a25c10847ee6e8ec0a2f65b98e25`。
- 修正版 Run `35065837875` / Job `104695793974` / Artifact `10434471836`: success。
- marker `HEAD4_V283_JULY_COND_THIRD_MISS_ANALYSIS_OK`。
- July THIRD miss 7Rのactual-third rank: rank3=6R、rank4=1R。大半がTop2境界型。
- Apr-Jun conditional THIRD capture 85.71%、July 46.15%、August 83.33%。July固有の崩れ。

## ユーザーの最新研究方針
ユーザー提案: 「救済条件調べると同時に僅差なら買い目増やすってのはどう？」
両方を同時に比較する。
1. 条件付き救済: actual rank3になりやすい条件を特徴量で救済し、4点維持を狙う。
2. 僅差時買い目追加: conditional THIRDのrank2-rank3が僅差なら3位も採用し、元Top2を残したまま原則4点→6点へ増やす。
3. 併用も比較。
4. 現行4点 / 救済4点 / 僅差6点 / 併用を比較。
5. 閾値はJulyだけへ後付けしない。Apr-Junを開発側、Jul-Augをholdout確認側にする。
6. 最終評価は追加的中だけでなく、追加投資・払戻・profit・retrospective closing-odds ROIまで見る。

## 実装済み — 次に回す研究
- BEFOREは旧handoff `CHAT_HANDOFF_20260915_4HEAD_WRST_AUG31_VARIANT.md` にcommit `202413cc03ed8758b8f5d41576690177fe1aca00` で記録済み。
- 新規script `analyze_4head_v283_rescue_close_margin.py` commit `efa4e159811107bc6b64943ed9532f4b9cc58b10`。
- 新規workflow `.github/workflows/analyze-4head-v283-rescue-close-margin.yml` commit `568e1289c13bc175ca1a0b13a0a48bf194891ff0`。
- workflowは`workflow_dispatch` only。
- gap scan候補: 0.01/0.02/0.03/0.04/0.05/0.075/0.10。
- Apr-Junだけで閾値を選び、Jul-Aug/July/Augustへholdout適用する設計。
- 最初のrunはcapture/発火数/追加点数構造を確認する。正確なclosing-odds ROIはpair-level odds replayを追加して次段で評価する。

## 次の再開地点
1. 最新GitHubを読む。
2. `analyze-4head-v283-rescue-close-margin` workflowを1回実行する。connectorでfresh workflow_dispatchできなければユーザーにworkflowリンクから1回だけ実行してもらう。古いrunのrerunで新commitを使ったふりをしない。
3. Run/Job/Artifact/logを確認し、Apr-Junで選ばれたgap閾値とJul-Aug holdoutの救済数/発火数を確定する。
4. その後、pair-level official closing oddsを使って現行4点 vs 僅差時6点の追加投資/払戻/profit/ROIを厳密比較する。
5. 同時にCOND_BASE feature contributionから「4点維持の条件付き救済」を作り、holdoutで比較する。
6. 結果をこのhandoffへAFTER追記する。

Status: `READY_TO_RUN_HEAD4_V283_RESCUE_CLOSE_MARGIN_SCAN`
