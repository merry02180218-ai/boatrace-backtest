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

## 最終実装 2026-09-15
- `run_1head_v351_live_finalize.py` commit=`0fb5a4e0139c2cf87aaf978738277420121ffbf6`。
- finalizer CI commit=`fc970a5a23a65807766efa0b85639c9e39f7cfd2`。
- finalizer CI Run=`34928441122` success / Job=`104251395344` / Artifact ID=`10379909511` / digest=`sha256:a9eb4fbf1e019f2641ca8fca3df9bb08f411a707c71fd684bce7ffde6e0e1a02`。
- BOATCAST probeをparsed tkz/stt/orig payload返却へ更新 commit=`cc912d1940bc2149bb3ad84cbdf18782f1611f1c`。
- 正式v332/v345 exhibition semanticsをLIVEに適用する `run_1head_v351_live_exhibition_gate.py` commit=`7092c53e9a8d2b4939a4ed179967522ad49ee9b7`。
- 共有prediction cache builder `prepare_1head_v351_live_cache.py` commit=`49efc893210263d0235359e98d96df472e0588e4`。
- rolling PREをtarget前日までのSeptember completed outcomes許可へ変更 commit=`4a78ee92409ceffdba75d2b34fe725d9b15c535c`。同日結果は時刻証明できないため保守的に除外。
- 共有cache workflow `.github/workflows/prepare-1head-v351-live-cache-20260915.yml` commit=`97b92455df3b3ed040644e6dc3916bef941a33d7`。
- watcherを `展示ready → exact exhibition gate → v351 opponentCore g2=.45/g3=1.00 → HYBRID 3点 → immutable PASS/DROP` に直結 commit=`eccbbe52642a62b4c460616a89490fe0cde9e7bf`。
- watcherはshared cache欠落時にBETを作らずfail-closeする。
- result/payout guardとchronology_guardはfinalizerまで保持。

## v351 cached live core timing
- benchmark Run=`34927249888` success / Job=`104247789036` / Artifact ID=`10380650284`。
- 20,000 iterations mean=`0.026297ms`, p95=`0.027051ms`。

## 検証状態
- finalizer単体 contract はGREEN: Run=`34928441122`。
- rolling PRE Run=`34928773352` / Job=`104252395285` は記録時点で `in_progress`。fetch PRE inputs step実行中。
- rolling PRE成功後に workflow_run でshared cache生成が起動する設計。
- そのshared cache artifact生成成功を確認するまでは「本番E2E検証完了」とは呼ばない。

## 重要な残存境界
- PREはSeptember completed outcomesをtarget前日まで学習する。
- 現時点のv308/v317/v318 shared prediction cache本体は既存frozen causal historyを利用するため、September outcome rolling retrainをHEAD/SECOND/THIRD全体へ完全反映する追加改修は未完。ここを未完のまま「9月学習完全対応」とは表現しない。
- 次の再開点: rolling PRE Run 34928773352完了確認 → shared cache workflow Run/Artifact確認 → HEAD/SECOND/THIRDにもSeptember prior-day historyを入れるday-aware/pseudo-month rolling fitへ更新 → watcher E2EをGREENにする。
