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

## September rolling source — PASS
- builder=`build_1head_september_training_source.py` commit=`5910d1ed9399f13db246d88b32d0165f1273a864`。
- workflow fix commit=`fc9ad45e30196ac9309be8278896379bb7158adc`。
- Run=`34929791569` success / Job=`104255445743` / Artifact ID=`10381361732` / digest=`sha256:7664595fa4c125dace2a0490d6c14aa5d7c6948570f877d8355a3164ceec46e8`。
- 2026-09-01〜09-14 feature_rows=2131 / valid_result_rows=2118 / head_hits=1161。
- training_max_date=`2026-09-14`、same_day_outcomes_read=false、target_or_future_rows=0、chronology_guard=true。

## 作業開始 2026-09-15 — rolling model wiring
- ユーザー指示「続けて」。
- September sourceが実データでPASSしたので、次はv308 HEAD / v317 SECOND / v318 THIRD / v332 exhibition trainingへprior-day September rowsを接続する。
- historical production sentinelは変更しない。LIVE shared cacheだけをrolling化する。
- target自身/未来raceは不使用。同日結果も不使用。
- rolling model cacheを生成し、watcherの展示→正式gate→v351 finalizer→immutable PASS/DROP/3点までE2E CIを通す。
- 完了後にcommit / Run / Job / Artifact / timingを追記する。

## 作業再開 2026-09-15 — rolling cache repair
- rolling CI Run=`34931581247` / Job=`104260715984` は failure。
- September race-card取得修正後、次の停止点は `cache_v321_julaug_nonpristine_head_full.csv.gz` 不在。
- これから frozen prepare/cache の正規生成経路を確認してworkflowへ接続する。
- 同時に誤って簡略化した `run_v323_1head_frozen_live_adapter.py` を変更前版へ復元し、September rolling処理はLIVE専用moduleへ分離する。
- base opponent mass と production SECOND/THIRD のL2/family差も監査し、chronology-safeな日付ベース学習を維持する。
- 修正後にrolling CIを再実行し、Run/Job/Artifactまで確認してからshared cache→watcher E2Eへ進む。

## 作業開始 2026-09-15 — PRE artifact path repair
- 最新 failure Run=`34932940149` / Job=`104264780075` を確認。v321 canonical prepareは成功し、rolling工程で `FileNotFoundError: /tmp/pre/race_cards.csv`。
- PRE Artifact ID=`10379049041` の実体を確認し、race cardsは `/tmp/pre/live_pre/race_cards.csv`、waku10は `/tmp/pre/live_pre/waku10.csv`、S/A/Bは `/tmp/pre/v351_live_sab/pre_candidates_sab.csv` に格納されている。
- これからworkflowの `--cards` を実Artifact構成へ修正し、CIを再実行して次の停止点まで確認する。
