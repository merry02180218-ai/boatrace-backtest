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
  - LIVE中の `run_v321... --stage prepare` / on-demand全量base fallbackを削除。
  - 日次cache Artifactが無い場合は即 `BASE_NOT_READY`。
  - 対象race JSON / exhibition train欠損も即fail-close。
  - 直前workflow timeoutを4分へ短縮、展示probeは10秒間隔最大4回。
- 03:00 JST daily workflow追加 commit: `f4eff2a8a534c819521cde7113b770386454d254`。
  - workflow: `.github/workflows/prepare-1head-v351-daily-0300-jst.yml`
  - schedule: `0 18 * * *` UTC = `03:00 JST`。
  - 当日rolling race_cards/PRE sourceを取得 -> v321 causal prepareを1回だけ実施 -> 全R base作成 -> `v351-1head-live-cache-YYYYMMDD` Artifactへ保存。
  - `pre_candidates.csv` / `pre_candidates_meta.json` も同Artifactへ格納。
- 全R cache対応 commit: `55de6538561ac8b7df36e5bdae738636c7ddae37`。
  - `prepare_1head_v351_live_cache.py` のdaily modeをPRE候補だけでなくcurrent head frameの全race_codeへ拡張。
  - PRE CSVがあるraceは既存PRE metadataをoverlayし、production HEAD/opponent計算は変更しない。
  - `base_source=DAILY_ALL_RACE_CACHE`。
- 重要: PRE S/A/Bは既存PRE sourceの分類をそのまま使い、勝手な新閾値は導入していない。非候補は `NON_CANDIDATE`。
- production v351 gate/finalizer条件は変更なし。結果・払戻利用なし。

### Actions検証状態
- 03:00 workflowは新規scheduleのため、現時点では初回03:00 JST実Run前。Run ID / Job ID / Artifact IDはまだ無し。
- 実装を「運用検証完了」とはまだ扱わない。
- 最初の03:00 Runで rolling PRE source が03:00時点に存在するかを必ず確認する。存在しなければ、race_cards/PRE source自体を03:00 workflow内で生成する経路へ修正する。

### 次の再開地点
1. 初回03:00 JST Runを確認し Run/Job/Artifact ID・全R cache件数・PRE候補件数・所要時間を記録。
2. 03:00時点でrolling source未準備ならsource生成をdaily workflowへ内包。
3. daily Artifact成功後、実在race requestで高速LIVEを実測し、request commitからBUY/DROP Artifactまでの秒数を記録。
4. PRE候補一覧に締切時刻を確実に付与し、締切順表示を完成させる。

## 復活51R 閾値再監査 — 作業前記録
- schema-correct rebuildで `RECOVERED_ONLY READY=51 / OOF=18 / cutoff0.78=9R / 頭4R=44.44%` だった群を対象に、閾値を0.78固定ではなく再探索する。
- 同一chronological OOFのスコアを使い、51R群だけについて複数cutoffで「対象R数・頭数・頭率・exact3数・exact3率」を比較する。
- 小標本なので、単純な最高率だけでなく最低母数も併記し、productionへ勝手に反映しない。
- 徳山・尼崎等の場偏りが閾値上昇でどう変わるかも確認する。
- September 2026結果は研究入力として読まず、既存の監査用chronological OOF範囲だけを使用する。
