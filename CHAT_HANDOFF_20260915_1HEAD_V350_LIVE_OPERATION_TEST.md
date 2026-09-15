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
- `run_1head_v351_live_finalize.py` commit=`0fb5a4e0139c2cf87aaf978738277420121ffbf6`。
- `.github/workflows/test-1head-v351-live-finalizer.yml` commit=`fc970a5a23a65807766efa0b85639c9e39f7cfd2`。

## v351 cached live core timing
- benchmark Run=`34927249888` success / Job=`104247789036` / Artifact ID=`10380650284`。
- 20,000 iterations: mean=`0.026297ms`, median=`0.025979ms`, p95=`0.027051ms`, max=`0.123647ms`。
- process wall=`1.73s`, max RSS=`165132KB`。

## 作業開始 2026-09-15 — 最終完成（継続）
- ユーザー指示「完成させて」。
- 既存watcherは展示readyで止まるため、ready→正式v351最終判定→immutable PASS/DROP/3点へ接続する。
- 既存v323 LIVE routeとv337/v332/v326の正式 exhibition semanticsを再利用し、仮の判定は作らない。
- raceごとの重い再学習は禁止。共有cache/事前計算を利用する。
- T-15/T-12/T-10/T-5、T-5未ready ERROR_NO_BET、result/payout禁止、immutable finalを維持。
- September学習はtargetより前に確定した結果だけ。厳密な同日確定時刻を証明できない場合はprior-day cutoffへfail-closeする。
- CIでfinalizer contractとwatcher接続を通し、Run/Job/Artifact/commitを完了後追記する。
