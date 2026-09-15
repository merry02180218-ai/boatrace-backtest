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

## 復活51R 閾値・schema監査 — 既知結果
- 元Artifact `10390159767`（Run `34955947116` / Job `104337913699`）。
- RECOVERED_ONLY READY 51R、OOF scoreあり18R。
- 高score側 >=0.78 は9R / 頭4 / 44.44% / exact3 0。
- 低score側 <=0.66 は5R / 頭5 / 100% / exact3 3 / 60.00%。ただし5Rだけなのでproduction採用禁止。
- 復活OOF18Rは全て `lap+turn` schema。JCD18=13 OOF、JCD13=5 OOF、JCD12=0 OOF。
- 問題はcutoffだけでなくlap+turnで既存schema_pの校正方向がずれている可能性。

## schema別補正 OOF生成 — 作業前記録
- ユーザー指示により、`lap+turn` だけでなく `half+turn+straight`（半周ラップ場）と、オリジナル展示項目が無い/展示タイム中心の場も同じ考え方で補正可能か試す。
- まず最新schema mapと監査コードを確認し、各schemaについて結果を未来参照しないchronological OOFを生成できる実装にする。
- 目標は `raw schema score -> schema補正（必要なら場補正） -> corrected HEAD p -> 共通cutoff 0.78`。
- 補正は同じ評価対象自身の結果で後付けしない。月外/時系列foldまたはvenue holdoutで検証する。
- September 2026結果はUNREAD維持。production v351条件はこの試験では変更しない。
- 出力予定: schema別 READY/OOF/補正式・corrected cutoff0.78の対象R/頭率/exact3率、場別holdout、比較CSV。
