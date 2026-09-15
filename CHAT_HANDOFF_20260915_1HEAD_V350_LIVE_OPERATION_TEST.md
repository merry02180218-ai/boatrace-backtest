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
- `run_1head_v351_live_window.py` commit=`de0c85473390ae511d0f7c140edfc0fcdc5391ae`。
- `probe_1head_v351_boatcast_exhibition.py` commit=`3b717ce430aef4b7bc6d094967deeb8ea480248c`。
- `.github/workflows/auto-live-1head-v351-window.yml` commit=`cb89eaab7d6a3eb2b2b6a18e39abf60b6ca337f5`、再trigger=`f91d76412762686089b610c81b9094e7227a65ea`。
- `.github/workflows/auto-live-1head-v351-exhibition-20260915.yml` commit=`de0ad59accd5fac384333602e85dfc35967d0ca7`。

## v351 cached live core timing
- benchmark Run=`34927249888` success / Job=`104247789036` / Artifact ID=`10380650284`。
- 20,000 iterations: mean=`0.026297ms`, median=`0.025979ms`, p95=`0.027051ms`, max=`0.123647ms`。
- process wall=`1.73s`, max RSS=`165132KB`。
- この計測はcache準備後のopponentCore→SECOND/THIRD→HYBRID 3点生成部分。ネットワーク/重い履歴準備は含まない。

## 作業開始 2026-09-15 — 最終完成
- ユーザー指示「完成させて」により、ready展示→正式HEAD final cutoff .78→PASS/DROP→PASSのみ3点をwatcherへ直結する。
- 日次cacheを前提にし、LIVE raceごとの重い再学習は禁止。
- T-15/T-12/T-10/T-5、T-5未ready ERROR_NO_BET、result/payout禁止、immutable finalを維持。
- September learningはchronology-safe cutoffのみ。target/future resultは読まない。
- CIでscorer contractとwatcher接続を通し、Run/Job/Artifact/commitを完了後追記する。
