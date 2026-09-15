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
- BOATCAST probe parsed payload commit=`cc912d1940bc2149bb3ad84cbdf18782f1611f1c`。
- exhibition gate commit=`7092c53e9a8d2b4939a4ed179967522ad49ee9b7`。
- shared cache builder commit=`49efc893210263d0235359e98d96df472e0588e4`。
- rolling PRE commit=`4a78ee92409ceffdba75d2b34fe725d9b15c535c`。
- shared cache workflow commit=`97b92455df3b3ed040644e6dc3916bef941a33d7`。
- watcher exact final connection commit=`eccbbe52642a62b4c460616a89490fe0cde9e7bf`。

## v351 cached live core timing
- benchmark Run=`34927249888` success / Job=`104247789036` / Artifact ID=`10380650284`。
- 20,000 iterations mean=`0.026297ms`, p95=`0.027051ms`。

## 作業開始 2026-09-15 — September rolling完全対応
- ユーザー指示「お願いします」を受け、未完だったHEAD v308 / SECOND v317 / THIRD v318のSeptember prior-day rolling学習を完成させる。
- まず rolling PRE Run 34928773352 の完了状態を確認する。
- 最新のv308/v317/v318 training/apply経路を読み、既存productionのFeb-Aug historical sentinelを変更せず、LIVE cache側だけtarget前日までのcompleted September outcomesを追加する。
- 同日結果は確定時刻を証明できない限り使わない。target race自身/未来raceは絶対に学習へ入れない。
- shared cache生成→watcher exact gate/finalizerまでCI/E2Eを確認する。
- 完了後、Run/Job/Artifact/commitと実測時間、残存境界をこのhandoffへ追記する。
