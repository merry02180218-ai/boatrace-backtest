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
- 目標は `raw schema score -> schema補正（必要なら場補正） -> corrected HEAD p -> 共通cutoff 0.78`。
- 補正は同じ評価対象自身の結果で後付けしない。September 2026結果はUNREAD維持。production v351条件は変更しない。

## schema別補正 OOF生成 — 実行結果
- 実装 commit `3f9a650b4a89d56d4b1327d1ab20ed4df77b5150`: `audit_v351_schema_calibration.py`。
- workflow commit `fbfb00e2a9b00033bc5aab21532987caad486d2a`: `.github/workflows/audit-v351-schema-calibration.yml`。
- Actions Run `34971467223` / Job `104388520815` / conclusion `success`。
- Artifact `10397660673` / name `audit-v351-schema-calibration` / digest `sha256:a1338e9df5693a52ca0e13d902ed3831028a9fc9fb11d47c092b4201d5fd7ed4`。
- schema map: JCD01=`half+turn+straight`; JCD13/JCD18=`lap+turn`; JCD19=`turn+straight`; JCD02/05/12/15=`base`; その他の対象場は主に`lap+turn+straight`。
- READY/OOF: `lap+turn+straight` READY207/raw OOF177/cal OOF172。`lap+turn` READY48/raw OOF18/cal OOF13。`half+turn+straight` READY18/raw OOF0。`turn+straight` READY5/raw OOF0。`base` READY10/raw OOF0。
- chronological logistic calibration後 cutoff0.78: `lap+turn+straight` 172R / 頭148 = 86.05% / exact3 69 = 40.12%。ただしcalibrationがほぼ全172Rを0.78以上へ押し上げるため、選別力改善とは言えずproduction採用しない。
- `lap+turn` はcal OOF13のうち corrected>=0.78 が1Rのみで、その1Rは頭外れ・exact3外れ。単純logistic補正では復活できない。
- `half+turn+straight`、`turn+straight`、`base` はraw OOF自体が0のため、このRunでは補正値を決定不能。結果を見た後付け補正は禁止。
- 結論: 今回の単純schema_p→logistic補正をproductionへ入れない。`lap+turn` はscore方向/特徴意味の再設計が必要。半周ラップ・展示タイム中心schemaはまず専用chronological OOF生成が必要。
- production v351は変更なし。September 2026結果UNREAD維持。
- 次の再開地点: `half+turn+straight` / `turn+straight` / `base` 用に、各schemaの利用可能特徴からHEAD raw OOFを時系列生成する専用監査を作る。同時に`lap+turn`は単純校正ではなく特徴方向を含む専用HEADモデルを検証し、共通cutoff0.78へ変換できるか比較する。
