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

## schema別補正 OOF生成 — 実行結果
- 実装 commit `3f9a650b4a89d56d4b1327d1ab20ed4df77b5150`。
- workflow commit `fbfb00e2a9b00033bc5aab21532987caad486d2a`。
- Run `34971467223` / Job `104388520815` / Artifact `10397660673` / success。
- `lap+turn+straight` READY207/raw OOF177/cal OOF172。`lap+turn` READY48/raw OOF18/cal OOF13。`half+turn+straight` READY18/raw OOF0。`turn+straight` READY5/raw OOF0。`base` READY10/raw OOF0。
- 単純logistic補正はproduction不採用。production v351変更なし。September 2026結果UNREAD維持。

## 専用schema HEAD OOF — 作業前記録 2026-09-15
- 対象: `lap+turn`, `half+turn+straight`, `turn+straight`, `base`。完全schema `lap+turn+straight` は比較基準として保持。
- 時系列順で過去データだけを学習する dedicated HEAD OOF を生成する。September 2026結果は学習・評価ともUNREAD維持。
- この監査中はproduction v351 gate/finalizerを変更しない。

## 専用schema HEAD OOF — 初回Run不具合
- 実装 commit `5daed9e991bfcc1de1a56ae3557ffe9f8fab085a` / workflow commit `413073ddef549876ef6392f269c493339324ccdd`。
- Run `34974696665` / Job `104399364790`。GitHub Job表示はsuccessだが、`Dedicated schema HEAD OOF sweep` 内で `b.head` が pandas Series.head メソッドと衝突し TypeError。Artifact `10398039072` は途中生成物のみ。
- このRunは研究結果として無効。production変更なし。

## 専用schema HEAD OOF — 再実行 作業前記録 2026-09-15
- ユーザー指示「再実行して」により、上記 `b.head` 衝突を `b['head']` 等の明示的キー参照へ修正する。
- 修正commitで同workflowをpush起動し、完走後にRun/Job/Artifactとschema別BEST・venue/JCD結果を確認する。
- 途中生成Artifact `10398039072` の数値は採用しない。
- September 2026結果UNREAD、production v351変更なしを維持する。
