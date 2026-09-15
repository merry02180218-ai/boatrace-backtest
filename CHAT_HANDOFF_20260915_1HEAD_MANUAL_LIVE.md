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

## 03:00 JST 当日全量base + PRE候補化 — 実装結果
- 作業前handoff commit: `3cb27591beeedfed5dba40dd65dd18fc17381804`。
- LIVE bridge高速fail-close化 commit: `2592874f23254a1bdc8220ebdec8ec06021c1784`。
- 03:00 JST daily workflow追加 commit: `f4eff2a8a534c819521cde7113b770386454d254`。
- 全R cache対応 commit: `55de6538561ac8b7df36e5bdae738636c7ddae37`。
- production v351 gate/finalizer条件は変更なし。結果・払戻利用なし。

## 復活51R 閾値再監査 — 結果
- 作業前handoff commit: `546457fe354a20cdf4eb552f89f7ef0a142b85ff`。
- 元データは schema-correct chronological OOF Artifact `10390159767`（Run `34955947116` / Job `104337913699`）。新規結果読込なし。
- RECOVERED_ONLY READY 51R、OOF scoreあり18R。
- 高score側 >=0.78 は9R / 頭4 / 44.44% / exact3 0。
- 低score側 <=0.66 は5R / 頭5 / 100% / exact3 3 / 60.00%。ただし5Rだけなのでproduction採用禁止。

## 復活51R schema/jcd・score方向監査 — 結果
- 同じArtifact `10390159767` の18 OOFをrace単位まで分解。新規結果読込なし。
- 復活51Rの内訳は JCD12=3R（OOF 0）、JCD13=22R（OOF 5）、JCD18=26R（OOF 13）。復活OOF18Rは全て `lap+turn` schema。
- JCD18 OOF13R: 頭9/13=69.23%、exact3 2/13=15.38%。JCD13 OOF5R: 頭1/5=20.00%、exact3 1/5=20.00%。JCD12はOOF 0で評価不能。
- `schema_p <=0.66` の5Rは JCD18が4R/頭4/exact3 2、JCD13が1R/頭1/exact3 1。したがって低score側の好成績は単一場だけの偶然ではないが、JCD13は1Rしかなく独立な場再現とは言えない。
- `schema_p >=0.66` 側13Rは頭5/13、exact3 0/13。高scoreほど弱い現象はexact3でも明瞭。
- 18Rの頭的中10Rの平均schema_pは約0.678、頭外れ8Rは約0.811。復活lap+turn群ではschema_pがHEAD安全度として逆方向に働いている。
- 特徴平均では、頭的中側は `one_ex` / `one_lap` / `one_turn` がむしろ低く、`uncovered_lap_dominance` と `uncovered_turn_dominance` がより負側。つまりこの復活schemaでは、旧schemaで「1号艇展示優位」として学習した方向と、lap+turnだけの欠損schemaでの相対値の意味がずれている可能性が高い。
- `<=0.66` 5Rは全頭かつexact3 3/5だが、閾値としてproductionへ採用しない。18 OOFしかなく、特にJCD13/JCD18しかOOFがないため過学習リスクが高い。
- 結論: 問題は単なるcutoff値ではなく、復活群が全て `lap+turn` schemaで、既存schema_pの校正方向が旧model_ready群と一致していないこと。復活51Rを救うなら「schema_p反転閾値」を直接採用するより、lap+turn専用calibration/HEADモデルをchronological OOFで作り直すのが正道。
- 次の再開地点: `lap+turn` 専用で、JCD13/JCD18を場情報込み/無しの両方でchronological recalibrationし、LOMO（月外）またはvenue holdoutで方向逆転が再現するか検証する。母数が足りなければ復活群はproduction除外維持。
- 今回は既存Artifactの詳細再解析のみで新規Actions Run/Job/Artifactなし。production変更なし。
