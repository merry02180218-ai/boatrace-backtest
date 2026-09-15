# 1号艇 v350 実運用テスト 2026-09-15

## 現行production
- `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- SECOND g2=.45 / THIRD g3=1.00。
- historical production regression sentinelは維持し、LIVE実運用とは分離する。

## historical production監査
- Run=`34900768805` success / Artifact ID=`10371394695`。
- PASS=276 / HEAD=241 / EXACT3=131。
- historical auditでは `SEPTEMBER_OUTCOMES_READ=false`。

## PRE S/A/B
- `S>=.82 / A=.80-.82 / B=.78-.80 / <.78対象外`。
- 2026-09-15 PRE run=`34924389688` / Artifact ID=`10379049041`。
- 17候補: S=5 / A=4 / B=8。

## 自動直前判定タイミング — ユーザー最終確定
- >T-15はWAIT（>T-20は完全休止の運用意図）。
- T-15以下 TRY15 / T-12以下 TRY12 / T-10以下 TRY10。
- T-10ではエラーにしない。
- T-5以下 FINAL5。ここでも必要展示が揃わなければ `ERROR_NO_BET` をimmutable確定。
- 展示取得できた最初のTRYでv351判定へ進む。final artifactがあるrace_codeは再処理しない。

## 実装済み 2026-09-15
- `run_1head_v351_live_window.py` を新規実装。commit=`de0c85473390ae511d0f7c140edfc0fcdc5391ae`。
  - remaining timeから `WAIT / TRY15 / TRY12 / TRY10 / FINAL5 / EXPIRED` を決定。
  - T-10は `final_fail_close_if_not_ready=false`、T-5はtrue。
  - result/payout used=falseを明示。
- `probe_1head_v351_boatcast_exhibition.py` を新規実装。commit=`3b717ce430aef4b7bc6d094967deeb8ea480248c`。
  - BOATCAST tkz/stt/originalだけを取得。
  - 既存3号艇parserと1号艇v326 raw_completenessを再利用。
  - tkz/stt/orig turn/straight/avgの6艇完全性を検査。
  - result/payout endpointは使用しない。
- `.github/workflows/auto-live-1head-v351-window.yml` を新規実装、境界テストを追加。commit=`cb89eaab7d6a3eb2b2b6a18e39abf60b6ca337f5`、再trigger commit=`f91d76412762686089b610c81b9094e7227a65ea`。
- `.github/workflows/auto-live-1head-v351-exhibition-20260915.yml` を新規実装。commit=`de0ad59accd5fac384333602e85dfc35967d0ca7`。
  - 既存PRE Artifact ID 10379049041から17 S/A/B候補だけmatrix化。
  - 5分scheduleで候補ごとのofficial deadlineを取得。
  - final artifactがあればskip。
  - TRY窓だけBOATCAST展示をprobe。
  - FINAL5未readyのみ `live-v351-final-<race_code>` ERROR_NO_BET artifactを作る。
  - 展示ready時は `EXHIBITION_READY_FOR_V351` transient artifactとし、まだBET/DROPを捏造しない。

## 重要: 現在の完成境界
- **T-5 fail-closeを含む締切window + BOATCAST展示自動取得/完全性判定までは実装済み。**
- **展示ready後の正式v351 HEAD/SECOND/THIRD計算と3点生成はまだ接続していない。** readyをfinal扱いしないことで誤BETを防いでいる。
- 次の再開地点は、日次v351 cacheを作り、ready artifactを正式v351 scorerへ接続すること。
- September rolling learningはLIVE cache側で chronology-safe cutoffを実装する。historical regressionのSeptember UNREADは変更しない。
