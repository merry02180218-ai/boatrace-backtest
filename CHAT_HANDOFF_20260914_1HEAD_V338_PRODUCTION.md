# 1号艇モデル 引き継ぎ — v338 HEAD 0.78 正式production

作成日: 2026-09-14
repo: merry02180218-ai/boatrace-backtest

## 2026-09-14 今回の作業開始記録（v339）
- 作業開始時のGitHub最新HEAD: `c9b07cf97f79669c75dec8c1e86bdea1d74a47cf`
- 正式productionは変更しない: `1HEAD_PRODUCTION_20260914_HEAD078`
  - HEAD/PRE cutoff = `0.78`
  - exhibition = v332 `ATTACK_ENV_SOFT`, env_w=0.1, q=0.65
  - SECOND = v317 `OUTER_L2_1`
  - THIRD = v318 `DROPSTART_T0.1`
  - 3-ticket = v320 `HYBRID alpha=.70`
- September 2026 outcomesは `UNREAD` を厳守。今回も結果ファイルを開かず、学習・評価・選別に使用しない。
- 今回やること:
  1. v338 production identityを基準に、0.78周辺のHEAD cutoff局所安定性をrace-levelで検証する。
  2. 主対象は `0.785 / 0.7825 / 0.7800 / 0.7775 / 0.7750`。0.78はcontrolとして必ず同一性を確認する。
  3. 各cutoffについてR数・head・exact3・0.78との差分・incremental quality・月別/場別の偏りを比較する。
  4. 7月・8月はNON-PRISTINEとして扱う。小標本の後付け除外はしない。
  5. 正式productionは研究結果だけでは黙って変更しない。0.78 identityが再現できなければ研究を停止しidentity修復を優先する。
  6. 完了後に実測結果、commit、Actions Run/Job/Artifact ID、結論、次の再開地点をこの引き継ぎへ追記する。

## 次チャットで最初にやること
1. このファイルと最新GitHubを読む。競合時は最新GitHubを優先する。
2. 9月2026のレース結果は引き続きUNREADのまま維持する。
3. 正式production `1HEAD_PRODUCTION_20260914_HEAD078` を基準に、精度・回収率改善研究を継続する。
4. 作業開始前に、この引き継ぎへ「今回やること」を追記し、作業完了後に実測結果・commit・Actions Run/Job/Artifact ID・結論・次の再開地点を追記する。
5. 正式productionの同一性が再現できない場合は比較研究を止め、先にidentityを修復する。

## 正式採用 production
ユーザー指示により v337 HEAD cutoff 0.78 を一旦正式採用し、v338でproduction regressionを固定した。

- profile: `1HEAD_PRODUCTION_20260914_HEAD078`
- HEAD/PRE cutoff: `0.78`
- exhibition: v332 `ATTACK_ENV_SOFT`, env_w=0.1, q=0.65
- SECOND: v317 `OUTER_L2_1`
- THIRD: v318 `DROPSTART_T0.1`
- 3-ticket policy: v320 `HYBRID alpha=.70`
- September outcomes: UNREAD

## v338 正式回帰結果
GitHub Actions Run: `34785538304`
HEAD SHA: `1407ed8e8cf3116bb259f4c232c1a0bb021008c7`

Jobs:
- prepare `103800223191` SUCCESS
- base-third `103801013695` SUCCESS
- second `103801013713` SUCCESS
- third `103801013796` SUCCESS
- regression `103801729238` SUCCESS

Final Artifact:
- `10327021622`
- name: `v338-1head-production-078-regression`

Regression output:
- PRE R = 1114
- final PASS R = 276
- head = 241 / 276 = 87.32%
- exact3 = 119 / 276 = 43.12%
- pass identity SHA256 = `89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73`

旧anchorも同時に再現:
- R=96
- head=83
- exact3=45
- anchor SHA256=`8c97e8ae4ef7f444ad82ce91f6e8b6483c57181cce3ccdb56593863a533241fc`
- canonical overlay rows=400

0.78で旧anchorから追加された180R:
- head 158/180 = 87.78%
- exact3 74/180 = 41.11%

場偏り:
- top venue share = 10.51%
- venue HHI = 0.0650

月別頭的中率の確認値:
- Feb 86.96%
- Mar 90.63%
- Apr 85.42%
- May 84.38%
- Jun 88.68%
- Jul 90.48%
- Aug 88.57%

特定月・単一場だけで成績が作られている形は現時点では見られない。

## 0.78採用までの比較
旧production anchor cutoff 0.8073405637:
- 96R / 月13.7R
- head 86.46%
- exact3 46.88%

v336 exhibition-q緩和:
- q=.50: 138R / head86.96% / exact3 44.93%
- q=.40: 164R / head85.98% / exact3 43.29%
- q=.35: 176R / head84.66% / exact3 43.18%
- q=.30: 192R / head85.94% / exact3 41.15%
- q=.25: 207R / head85.99% / exact3 39.61%

v337 HEAD-cutoff緩和（exhibition q=.65固定）:
- .8073405637: 96R / head86.46% / exact3 46.88%
- .80: 129R / head84.50% / exact3 41.09%
- .79: 187R / head85.56% / exact3 42.25%
- .78: 276R / head87.32% / exact3 43.12%
- .77: 363R / head84.30% / exact3 41.87%
- .75: 604R / head82.95% / exact3 39.07%

`.78`は件数を約39.4R/月まで増やしながら頭率87.32%を維持し、追加180R自体も頭87.78%。一方`.77`で悪化するため、0.78付近に局所的な良い帯が存在する可能性がある。

## v337 identity修復の重要事項
最初のv337 Run `34779669216` はanchor 88/76/43となり失敗した。
原因はWaku10ではなく、v337がcurrent exhibition sourceを広く再取得した際、STT/original exhibitionの一時的な欠損でcanonical rowsのsource completenessが崩れたこと。

missing canonical PASS 8 races:
- 202602241701
- 202604072407
- 202605050801
- 202605051012
- 202605052302
- 202606141601
- 202606160604
- 202607071001

修復commit: `fc5f4ad7523dc30abf879db7b98ac9c2d759e292`
canonical v332 exhibition overlayを入れ、anchor aggregateとrace_code setの両方をhard gate化。
修復後Run `34782769446` / audit Job `103794355983` / Artifact `10325922020` SUCCESS。

## Waku10監査結論
現在の1号艇HEAD/PREにおいてWaku10はリークではない。
Waku10のみを原因とする:
- changed input rows = 0
- changed p_head rows = 0
- cutoff crossings = 0
- PRE additions/removals = 0
- downstream v332 identity changes = 0

一度96→97になった件はWaku10ではなく、診断コードのtraining split bugだった。
誤ってFeb-Jul評価時にAugustをtrainingへ含めていた。
修正commit: `02b4b8d54823c4a7071ebf8cf620ad0c287a8e03`
修正後は96/83/45を完全再現。

## 研究上のルール
- 2026年7月・8月はNON-PRISTINE（開発・調整に使用済み）として扱う。
- 2026年9月outcomesは完全UNREADを維持する。
- 予想・判定・改良前に必ず実GitHubコード/データを確認する。
- 古いチャット記憶とGitHubが競合した場合は最新GitHub優先。
- 正式productionを研究中に黙って変更しない。
- production identity/regressionが崩れた場合、先に修復してから研究を再開する。

## 次の研究候補
正式production 0.78は固定したまま改善研究を進める。
優先候補:
- 0.78周辺の局所安定性検証（0.785 / 0.7825 / 0.780 / 0.7775等）。ただし正式productionは0.78のまま。
- 追加180Rの失敗レースを、結果リークしない特徴設計で分類し、頭率をさらに改善できるか。
- exact3 43.12%を上げるSECOND/THIRD/3-ticket側の改善。HEAD 0.78を壊さないこと。
- 1レース1万円Dutch・合成オッズ基準のROI評価を正式production 276Rに適用する。
- 場別・月別・季節別・レース番号帯などの安定性を確認する。ただし小標本の後付け除外は採用しない。
- 新規候補はproduction 0.78とのrace-level差分、incremental quality、月別安定性を必ず提示する。

## 次チャット用開始文
`boatrace-backtest の CHAT_HANDOFF_20260914_1HEAD_V338_PRODUCTION.md と最新GitHubを読んで、1号艇モデルの続きから進めて。最新GitHubを優先し、正式productionはHEAD cutoff 0.78 / v332 q=.65。9月結果はUNREADのまま。作業前後に引き継ぎを更新して。`
