# 1号艇 v350 実運用テスト 2026-09-15

## 現行production
- `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- SECOND g2=.45 / THIRD g3=1.00。
- historical production regression sentinelは維持し、LIVE実運用とは分離する。

## historical production監査
- Run=`34900768805` success。
- Artifact=`v351-1head-production-regression` / ID=`10371394695`。
- PASS=276 / HEAD=241 / EXACT3=131。
- Feb-Jun pristine=107/220、Jul-Aug support-only=24/56。
- historical auditでは `SEPTEMBER_OUTCOMES_READ=false` を維持する。

## operational backtest
- Run=`34900892661` success。
- Artifact=`v351-1head-operational-backtest` / ID=`10371468748`。
- 展示後ローカル計算 mean=0.170026ms/race、median=0.080386ms、p95=0.398716ms。
- 重いのは共有前処理/学習側であり、直前の1R判定自体は十分軽い。

## PRE S/A/B
- 固定Top15を廃止し、`S>=.82 / A=.80-.82 / B=.78-.80 / <.78対象外` を実運用候補とする。
- 2026-09-15 result-blind PRE run=`34924389688` success。
- Artifact=`v351-1head-live-pre-sab-20260915` / ID=`10379049041`。
- 17候補: S=5 / A=4 / B=8。
- historical v352 band auditはproduction p_head帯の監査であり、legacy_pre_p閾値の正式校正とは別物。この点は混同しない。

## 2026-09-15 v351 自動直前判定 LIVE試行 — 作業開始
- S/A/B候補から展示公開を自動検知し、正式v351でPASS/DROP、PASSなら3連単3点まで自動生成する。
- 実運用学習はユーザー承認により9月も利用可能。ただし対象レースの判定時点より前に確定済みの結果だけを許可し、対象レース自身・未来レースは絶対に学習へ入れない chronology guard を必須とする。
- historical regressionのSeptember UNREAD sentinelは変更しない。LIVE系だけ明確に分離する。

## 自動直前判定タイミング — ユーザー最終確定
- 対象レースの展示は通常締切約15分前に公開される前提で、30分前から重い処理を開始しない。
- 締切20分超前: `WAIT`。
- 第1取得窓: 締切15分前以下。
- 未公開なら第2取得窓: 締切12分前以下。
- さらに未公開なら第3取得窓: 締切10分前以下。
- **ユーザー修正: 締切10分前ではエラーにしない。締切5分前まで待つ。**
- 最終取得窓: 締切5分前以下。ここで必要展示が揃わなければ `ERROR_NO_BET` としてimmutableに確定する。
- 展示を取得できた最初の窓で即v351直前判定し、PASS/DROPをimmutableに確定する。PASS時のみ3連単3点を生成する。
- 同じレースを判定済みなら以後のscheduled runでは再計算しない。
- 対象は朝にfreezeしたS/A/B候補だけ。日次学習/履歴/モデル準備はキャッシュ化する。

## 今回の実装作業
1. T-15/T-12/T-10/T-5の状態判定を独立helperとして実装する。
2. T-5より前の展示未公開はWAIT扱い、T-5以降の展示未取得だけERROR_NO_BETとする。
3. official deadlineと現在JSTからremaining secondsを計算し、target date parityを検証する。
4. watcherは既存final artifactがあるrace_codeを再処理しない。
5. BOATCAST展示取得はresult/payout endpointを一切使わない。
6. push時にpy_compileとタイミング境界テストを実行し、CI-greenを確認する。
