# 1号艇 v350 実運用テスト 2026-09-15

## 現行production
- `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- SECOND g2=.45 / THIRD g3=1.00。
- historical production regression sentinelは維持し、LIVE実運用とは分離する。

## historical production監査
- Run=`34900768805` success。
- Artifact=`v351-1head-production-regression` / ID=`10371394695`。
- PASS=276 / HEAD=241 / EXACT3=131。
- historical auditでは `SEPTEMBER_OUTCOMES_READ=false`。

## PRE S/A/B
- 固定Top15を廃止し、`S>=.82 / A=.80-.82 / B=.78-.80 / <.78対象外`。
- 2026-09-15 result-blind PRE run=`34924389688` success。
- Artifact=`v351-1head-live-pre-sab-20260915` / ID=`10379049041`。
- 17候補: S=5 / A=4 / B=8。

## 自動直前判定タイミング — ユーザー最終確定
- 締切20分超前: WAIT。
- T-15以下: TRY1。
- 未公開ならT-12以下: TRY2。
- 未公開ならT-10以下: TRY3。
- T-10ではエラーにしない。
- **T-5以下をFINAL TRYとし、ここでも必要展示が揃わなければ `ERROR_NO_BET` をimmutable確定する。**
- 展示取得できた最初のTRYでv351判定へ進み、PASS/DROPを確定。PASS時のみ3連単3点。
- race_code単位のfinal artifactが存在すれば再処理しない。

## 実装開始 2026-09-15
- 既存 `fetch_boatrace_deadline.py` を締切ソースとして再利用する。result/payout endpointは使わない。
- 既存3号艇LIVEのBOATCAST direct parserと、1号艇 `run_v326_1head_ticketaware_exhibition.py` の `raw_completeness/corrected_direct` を再利用可能と確認。
- 新規1号艇window helperで `WAIT / TRY15 / TRY12 / TRY10 / FINAL5 / EXPIRED` を決定する。
- FINAL5では展示取得を最後に1回試し、未readyならERROR_NO_BET。TRY15/12/10の未readyはWAIT_RETRY。
- GitHub schedule自体は5分粒度なので、各scheduled invocationがその時点のremaining minutesから該当windowを判定する。12分窓を必ず時刻ぴったりに踏む保証はしないが、15分以下では毎回展示取得を試すため、公開後最初のrunで確定する。
- push CIで境界テストを行う。
