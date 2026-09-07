# 3号艇モデル 現行本番運用ルール — v165 -> v166

Updated: 2026-09-08 JST
Status: CANONICAL / PRODUCTION

## 現行の3号艇本番パイプライン

3号艇モデルの現行本番運用は、以下で固定する。

1. **v165 3-head probability model** で全対象レースを評価する。
2. **`p3head >= 0.30` のレースだけを本番候補として採用する。**
3. 候補レースでは **v166 direct ordered-pair model** を使い、3号艇頭固定の2着・3着候補を順位付けする。
4. 相手は `[1,2,4,5,6]` から作る順序付き20通りを対象とする。
5. **v166 の Top10 を本番買い目とする。**
6. v166 の direct-pair blend は **lambda = 1.00** を採用する。
7. レース結果・払戻・締切後情報を見てから候補選択や買い目順位を変更してはならない。
8. 買い目は結果確認前に freeze する。

Canonical shorthand:

> **v165 p3head >= 30% -> v166 direct pair lambda=1.00 -> Top10**

## 検証上の現行基準

Jun-Aug retrospective production baseline:

- candidates: 270R
- 3号艇頭率: 38.52%
- 3連単的中率: 29.26%
- 3号艇頭時 Top10 coverage: 75.96%
- equal-stake ROI: 103.2%
- monthly ROI: Jun 91.2% / Jul 116.3% / Aug 100.9%

この基準を現行 production baseline とする。

## v107 structural PRE との関係

`predict_v107_*_official_fullscan.py` 系の 3号艇まくり / まくり差し構造ゲートは、過去の構造スキャン・観察用途として残っているが、**現行の3号艇本番候補選定ルールではない**。

したがって、現在の運用で「3号艇モデルの事前候補を出す」と言われた場合、v107構造PREを本番候補として代用してはならない。必ず **v165 p3head >= 0.30** を候補ゲートとして使う。

v107を使う場合は、明示的に「旧構造PRE」「参考スキャン」「観察用」と表示し、本番候補と混同しない。

## 運用時の注意

- 事前候補抽出と最終買い目作成は、必ず実際の現行GitHubコードを通して計算する。
- assistantの推察だけで p3head、BUY/SKIP、Top10 を作らない。
- 現行ルールと古いチャット/古いhand-offが競合した場合、このファイルおよび最新commitを優先する。
- 3号艇が展示進入で3コースを外れた場合は entry gate により除外する。
- 同一レースの結果・払戻・締切後オッズは予測側に入れない。

## Supersedes

3号艇 production に関して、古い handoff に残っている v98/v99/v100 role shadow や v107 structural PRE の記述は、**本番候補選定ルールとしては superseded**。

現行 production は一貫して:

**v165 p3head >= 30% -> v166 Top10**
