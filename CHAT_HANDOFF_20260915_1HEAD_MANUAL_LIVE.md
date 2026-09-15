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

## 専用schema HEAD OOF — 再実行結果
- 実装 commit `5daed9e991bfcc1de1a56ae3557ffe9f8fab085a`、バグ修正 commit `f0c8aeaa6196748b334d3a12e23233c662e96a0c`、再trigger commit `5330e0ae6f4659a1a4984d11b2d126f9da0de736`。
- Run `34979361041` / Job `104415303329` / Artifact `10401475091` / success。
- lap+turn: READY48 / OOF43 / best cutoff .82 / 25R / HEAD20=80.0% / exact3 10=40.0%。JCD13 11R HEAD81.82%、JCD18 14R HEAD78.57%。
- half+turn+straight: READY18 / OOF13 / 13R / HEAD11=84.62% / exact3 3=23.08%。
- base: READY10 / OOF3 / 3R / HEAD3=100% / exact3 2=66.67%。小標本。
- turn+straight: READY5 / OOF0。評価不能。
- lap+turn+straight benchmark: READY207 / OOF202 / 202R / HEAD172=85.15% / exact3 79=39.11%。
- September 2026結果UNREAD維持。

## schema正式昇格 + 3連単研究 — 作業前記録 2026-09-15
- ユーザー承認: `turn+straight` 以外を正式production対象へ入れる。
- 正式対象: `lap+turn+straight`, `lap+turn`, `half+turn+straight`, `base`。`turn+straight` は保留/非production。
- `base` はOOF3Rしかないため低標本フラグを維持。
- 3連単相手選びはHEAD的中レースを母集団として、`EXACT3_HIT / ORDER_MISS / OPPONENT_PAIR_MISS` に分解し、現行 `G2=.45/G3=1.00` の改善箇所を特定する。
- September 2026結果はUNREAD維持。

## 3連単原因分解 workflow 再発火 — 作業前記録 2026-09-15
- 初回追加: research commit `13caab319e109080b4fcb89578f9ad90aa817f8c` / workflow commit `ef9821fda7fc5cb01a80cbd53f52997240f60f50`。
- 初回pushでは目的の `analyze-v351-schema-exact3-errors` が発火していないことを確認済み。別workflowのRunを目的Runと誤認しない。
- workflowファイルを通常contents APIで安全に更新して明示的にpush再トリガーし、対象workflow名・Run ID・Job IDを確認する。
- 完走後はArtifactとログを確認し、原因分解結果をhandoffへ追記する。September 2026 UNREAD、production変更なし。
