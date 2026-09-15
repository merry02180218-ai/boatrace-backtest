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
- 4号艇/3号艇側の既存LIVE資産を再利用するが、1号艇はユーザーの実運用知見に合わせて監視時間を短縮する。
- 実運用学習はユーザー承認により9月も利用可能。ただし対象レースの判定時点より前に確定済みの結果だけを許可し、対象レース自身・未来レースは絶対に学習へ入れない chronology guard を必須とする。
- historical regressionのSeptember UNREAD sentinelは変更しない。LIVE系だけ明確に分離する。

## 自動直前判定タイミング — 2026-09-15 ユーザー確定
- 対象レースの展示は通常締切約15分前に公開され、遅くとも約10分前には公開されるという実運用知見を採用する。
- 1号艇LIVE watcherは30分前から重い処理を開始しない。
- 締切20分超前: `WAIT`。展示/モデル重処理は行わない。
- 第1取得窓: 締切約15分前。
- 未公開なら第2取得窓: 締切約12分前。
- さらに未公開なら最終取得窓: 締切約10分前。
- 展示を取得できた最初の窓で即v351直前判定し、PASS/DROPをimmutableに確定する。PASS時のみ3連単3点を生成する。
- 同じレースを判定済みなら以後のscheduled runでは再計算しない。
- 締切10分前付近でも必要展示が揃わなければ取得異常としてfail-closeし、買い目を捏造しない。
- 対象は朝にfreezeしたS/A/B候補だけ。全場全Rを5分ごとに重く再計算しない。
- 日次の学習/履歴/モデル準備はキャッシュ化し、LIVE watcherでは締切・展示公開確認を軽く行い、必要なレースだけキャッシュ済みv351を実行する。

## 次の実装地点
1. 1号艇日次キャッシュを作成し、S/A/B candidate manifest、モデル/履歴、production profile、chronology cutoff metadataを保存する。
2. 1号艇LIVE watcherを作り、候補ごとの公式締切を解決する。
3. `>20m WAIT / ~15m TRY1 / ~12m TRY2 / ~10m TRY3-final` の状態遷移を実装する。
4. TRY窓だけBOATCAST展示/ST/originalを取得し、6艇 completenessを確認する。
5. readyなら正式v351 → PASS/DROP → PASSなら3点。未ready最終窓はERROR_NO_BET。
6. race_code単位のfinal artifactで二重判定を防止する。
7. 実際のActions Run/Job/Artifactでend-to-endを確認し、このhandoffへ結果を追記する。
