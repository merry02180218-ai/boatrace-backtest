# 1号艇 v350 実運用テスト 2026-09-15

## 現行production
- `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- SECOND g2=.45 / THIRD g3=1.00。
- historical production regression sentinelは維持し、LIVE実運用とは分離する。

## historical production監査
- Run=`34900768805` success / Artifact ID=`10371394695`。
- PASS=276 / HEAD=241 / EXACT3=131。

## 自動直前判定タイミング
- >T-15 WAIT、T-15/T-12/T-10で展示取得を試行、T-10ではerrorにしない。
- T-5 FINAL5。必要展示未取得なら immutable `ERROR_NO_BET`。
- 展示取得できた最初のTRYでv351判定。final artifact済raceは再処理しない。

## 実装済み
- finalizer `0fb5a4e0139c2cf87aaf978738277420121ffbf6`。
- finalizer CI Run=`34928441122` success / Job=`104251395344` / Artifact=`10379909511`。
- BOATCAST parsed probe `cc912d1940bc2149bb3ad84cbdf18782f1611f1c`。
- exhibition gate `7092c53e9a8d2b4939a4ed179967522ad49ee9b7`。
- shared cache builder `49efc893210263d0235359e98d96df472e0588e4`。
- shared cache workflow `97b92455df3b3ed040644e6dc3916bef941a33d7`。
- watcher exact final connection `eccbbe52642a62b4c460616a89490fe0cde9e7bf`。

## timing
- benchmark Run=`34927249888` success / Job=`104247789036` / Artifact=`10380650284`。
- 20,000 iterations mean=`0.026297ms`, p95=`0.027051ms`。

## September rolling監査 2026-09-15
- rolling PRE Run=`34928773352` はsuccessしたが、Job logを再監査すると `training_max_date=2026-08-31`, `SEPTEMBER_OUTCOMES_READ=false`, `september_training_rows=0` だった。
- 原因は `analyze_v108_1head_preselection_training.csv` 自体に2026-09のfeature/outcome rowが存在しないこと。従って前回の「September rolling対応」という表現は実データ上は未成立。
- HEAD v308 / SECOND v317 / THIRD v318の既存cacheもSep feature/outcome rowを持たないため、結果ラベルだけ追加しても再学習できない。
- 安全修正として `.github/workflows/v350-1head-live-operation-20260915.yml` を更新し、target>=9/2なのにSeptember training rowが0なら `SEPTEMBER_ROLLING_SOURCE_MISSING` でfail-closeするようにした。現行workflow SHA=`8f648cb971d31a950da8a7d63b9aeb2d7f658158`。
- これにより「9月を学習した」と偽ってAug-onlyモデルを実運用する経路は閉じた。

## 残る唯一のブロッカー
- 9/1〜target前日のPRE feature + outcomeを、当時利用可能だった入力だけで再構築するSeptember training-source builderが必要。
- そのsourceを作った後、v308/v317/v318とv332 exhibition trainingをprior-day cutoffで再fitし、shared cacheへ保存してwatcher E2Eを通す。
- 同日結果は確定時刻を証明できない限り不使用。target/未来raceは不使用。
