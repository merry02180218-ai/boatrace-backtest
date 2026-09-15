# 1号艇 v351 手動LIVE 引き継ぎ — 2026-09-15

## 最重要ルール
- 最新GitHubを最優先。
- 1号艇LIVE productionは v351。production gate/finalizerの条件は勝手に変更しない。
- LIVE判定でレース結果・払戻を使用しない。`result_or_payout_used=False` / `chronology_guard=True` を維持。
- GitHub作業は必ず、この引き継ぎへ作業前の予定を記録してから開始し、作業後に結果・commit SHA・Run/Job/Artifact ID・結論・次の再開地点を追記する。

## 現在の運用方針
- 1号艇v351の直前自動controllerは停止。ユーザー判別要求時だけ展示後判定。

## Chat起動用request bridge
- workflow: `.github/workflows/chat-live-1head-v351-request.yml`
- request path: `live_requests/1head_v351.txt`
- trigger確認 Run `34962132626` / Job `104357944028`。

## 2026-09-15 蒲郡12R actual LIVE — 失敗記録
- race_code `202609150712`
- Run `34962990778` / Job `104360757399`
- shared base欠損からLIVE中にv321全量prepareへ入り10分timeout。Artifactなし、BUY/DROP未判定。

## 03:00 JST 当日全量base + PRE候補化 — 作業前記録
- 毎日03:00 JSTに当日全場・全Rの展示前causal baseを一括生成。
- 同時に当日1号艇PRE候補を全場・全R横断で抽出。
- LIVEでは対象JSON取得後、deadline -> exhibition -> v351 gate -> finalizerのみ。
- base欠損時は重い再構築をせずBASE_NOT_READYでfail-close。
- v351 production条件、result_or_payout_used=False、chronology_guard=Trueを維持。

## 03:00 JST 当日全量base + PRE候補化 — 実装結果
- 作業前handoff commit: `3cb27591beeedfed5dba40dd65dd18fc17381804`。
- LIVE bridge高速fail-close化 commit: `2592874f23254a1bdc8220ebdec8ec06021c1784`。
- 03:00 JST daily workflow追加 commit: `f4eff2a8a534c819521cde7113b770386454d254`。
- 全R cache対応 commit: `55de6538561ac8b7df36e5bdae738636c7ddae37`。
- production v351 gate/finalizer条件は変更なし。結果・払戻利用なし。

## 復活51R 閾値再監査 — 作業前記録
- schema-correct rebuildで `RECOVERED_ONLY READY=51 / OOF=18 / cutoff0.78=9R / 頭4R=44.44%` だった群を対象に、閾値を0.78固定ではなく再探索する。
- 同一chronological OOFのスコアを使い、51R群だけについて複数cutoffで「対象R数・頭数・頭率・exact3数・exact3率」を比較する。
- 小標本なので、単純な最高率だけでなく最低母数も併記し、productionへ勝手に反映しない。
- September 2026結果は研究入力として読まず、既存の監査用chronological OOF範囲だけを使用する。

## 復活51R 閾値再監査 — 結果
- 作業前handoff commit: `546457fe354a20cdf4eb552f89f7ef0a142b85ff`。
- 元データは schema-correct chronological OOF Artifact `10390159767`（Run `34955947116` / Job `104337913699`）。新規結果読込なし。
- RECOVERED_ONLYは READY 51Rだが、chronological OOF score (`schema_p`) が存在するのは18R。
- 高いscoreを採る通常の `schema_p >= cutoff` は改善しなかった。
  - >=0.70: 13R / 頭5 / 38.46% / exact3 0
  - >=0.75: 11R / 頭5 / 45.45% / exact3 0
  - >=0.78: 9R / 頭4 / 44.44% / exact3 0
  - >=0.80: 8R / 頭4 / 50.00% / exact3 0
  - >=0.82: 6R / 頭2 / 33.33% / exact3 0
  - >=0.85: 3R / 頭1 / 33.33% / exact3 0
  - >=0.89: 1R / 頭0 / 0% / exact3 0
- むしろこの復活OOF18Rではscoreが低い側に頭的中が集中している。
  - <=0.55: 3R / 頭3 / 100% / exact3 2 (66.67%)
  - <=0.56: 4R / 頭4 / 100% / exact3 2 (50.00%)
  - <=0.66: 5R / 頭5 / 100% / exact3 3 (60.00%)
  - <=0.70: 5R / 頭5 / 100% / exact3 3 (60.00%)
  - <=0.72: 6R / 頭5 / 83.33% / exact3 3 (50.00%)
  - <=0.78: 9R / 頭6 / 66.67% / exact3 3 (33.33%)
- 結論: 復活51Rに既存と同じ「高scoreほど良い」閾値を再設定するだけでは救えない。OOF18Rではscore方向が逆転しており、schema_pの校正/特徴意味が旧model_ready群と異なる可能性が高い。
- `<=0.66` の5/5は非常に目立つが5Rだけなのでproduction採用禁止。これは候補仮説として別fold/追加OOFで再検証する。
- 次の再開地点: 復活51Rを一括閾値探索ではなく、`schema/jcd` とscore方向・校正を分解し、なぜ高score側が外れるかを監査する。必要なら復活群専用calibrationをchronologicalに再学習してOOF再評価する。
- 今回は既存Artifact再解析のみのため新規Actions Run/Job/Artifactは無し。production設定変更なし。
