# 1号艇モデル 引き継ぎ — v340 合成オッズ可変点数 + 1万円Dutch

作成日: 2026-09-14
repo: merry02180218-ai/boatrace-backtest

## 作業開始記録
- 作業開始時HEAD: `a6235b45907a5ba90faa7f5ee1c74685c018469c`
- 正式productionは変更しない: `1HEAD_PRODUCTION_20260914_HEAD078`
  - HEAD/PRE cutoff = `0.78`
  - exhibition = v332 `ATTACK_ENV_SOFT`, env_w=0.1, q=0.65
  - SECOND = v317 `OUTER_L2_1`
  - THIRD = v318 `DROPSTART_T0.1`
  - ticket ranking = v320 `HYBRID alpha=.70`
- production identity: PASS 276R / head 241 / exact3(top3) 119 / SHA256 `89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73`
- 2026年7月・8月はNON-PRISTINE。
- 2026年9月outcomesはUNREADを厳守し、今回も一切読まない。

## 今回やること
正式production 276Rを固定し、締切時3連単オッズだけで買い方を後段評価する。

ユーザー指定ルール:
1. 現行top3の合成オッズが3.0未満なら買わない。
2. 3.0以上4.0未満なら現行top3のまま。
3. 4.0以上ならv320 HYBRID alpha=.70の次順位買い目を順番に追加し、合成オッズを3.0に近づける。
4. 次の1点を加えると合成オッズが3.0未満になる場合は追加せず、その直前の点数を採用する。
5. 購入レースは総額10,000円。各買い目はDutch配分し、実購入を想定して100円単位へ丸める。
6. 実際のBOAT RACE公式「締切時3連単オッズ」を使用する。払戻結果からのオッズ逆算はしない。

## 検証項目
- 276Rに対する締切時オッズ取得coverage
- top3合成オッズ分布
- 3.0未満の見送りR数
- 4.0以上から点数追加したR数と最終点数分布
- 購入R数 / 的中R数 / 的中率
- 総投資 / 総払戻 / 損益 / ROI
- 100円丸めDutchの実額結果
- 現行top3を全購入した場合との比較
- 月別結果
- production自体は今回のROI結果だけで変更しない

## v340 初回Actions結果
- Run `34788421547`。
- prepare / second / base-third / third はSUCCESS。
- 最終auditは、BOAT RACE公式締切時オッズを276R逐次取得している途中でGitHub Actions実行時間上限に到達しCANCELLED。
- ログ上は250/276Rまで取得済みで、残り26Rのところで停止。
- モデル計算エラーではなく、公式オッズ取得を1ジョブに直列集中させた構成上のタイムアウト。
- 最終ROIは未確定のため推測値を採用しない。

## 2026-09-14 v340 Sharded Repair 開始記録
ユーザー承認により、初回タイムアウトを解消するためActions構成を分割する。

### 修正方針
1. 正式production 276Rとv320全買い目順位を1回だけ準備してArtifact化。
2. 276Rの公式締切3連単オッズ取得を6 shardへ決定論的に分割し、6つのGitHub Actions matrix jobで並列取得。
3. 各shardを個別Artifactとして保存し、1 shard失敗時も全276Rを取り直さない構成にする。
4. 全shard成功後にaggregate jobで結合し、ユーザー指定の合成オッズルール・1万円Dutchを計算。
5. baseline top3全購入と同一coverageで比較し、月別・点数分布・ROIをArtifactへ保存。
6. production設定自体は変更しない。
7. 2026年9月outcomesは一切読まずUNREADを維持する。

### Sharded実装
- `run_v340_prepare_rankings.py`
- `run_v340_odds_shard.py`
- `run_v340_aggregate_shards.py`
- `.github/workflows/v340-1head-adaptive-odds-dutch-sharded.yml`
- workflow構成: prepare → odds matrix shard[0..5] → aggregate
- v338成功済みRun `34785538304` の固定中間Artifactを再利用し、Jul/Aug cache再構築時間も省略する。

## v340 Sharded Repair 完了記録

### 実装・起動commit
- `7cb3ca0e382af208c4e69eca404c60d87fea1e5c` — sharded odds fetch helper
- `fd8f440d221529f082ddb59662d771e9b5e47fe0` — prepare rankings helper
- `5f93a1e3b82aefa7fac5bf729f16237575cb9b7a` — sharded aggregate
- `9e2e57f843dfc892d5ab3977d976e6c16ebbd626` — sharded workflow
- `efa28013a93f5cccdfefa189352b762a561819c1` — repair plan handoff
- `4b29e5d2acd241ae8404fbd02262d0b18b547bf9` — push trigger for final sharded audit

### GitHub Actions
- Workflow: `v340 1-head adaptive odds Dutch sharded`
- Run: `34796402852`
- HEAD: `4b29e5d2acd241ae8404fbd02262d0b18b547bf9`
- conclusion: SUCCESS
- prepare Job: `103830241175`
- odds shard Jobs:
  - shard0: `103834132143`
  - shard1: `103834132079`
  - shard2: `103834132077`
  - shard3: `103834132159`
  - shard4: `103834132221`
  - shard5: `103834132115`
- aggregate Job: `103835466114`
- all jobs SUCCESS

### Artifacts
- final: `10329904344` — `v340-1head-adaptive-odds-dutch-sharded`
- prepared rankings: `10330656182`
- shard0: `10329564703`
- shard1: `10330810260`
- shard2: `10330651756`
- shard3: `10329684566`
- shard4: `10330273057`
- shard5: `10330357729`

### Production identity / guard
- selected R = 276
- head = 241
- exact3(top3) = 119
- identity SHA256 = `89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73`
- BOAT RACE公式締切3連単オッズ coverage = 276/276
- missing = 0
- `SEPTEMBER_OUTCOMES_READ=false`

### ユーザー指定adaptive policy 結果
- skip = 243R
- keep3 = 26R
- expand = 7R
- bought = 33R
- hits = 11R
- hit rate = 33.3333%
- total stake = 330,000円
- total return = 381,260円
- profit = +51,260円
- ROI = 115.5333%
- 平均最終合成オッズ = 3.4127
- 中央値最終合成オッズ = 3.3291

### Baseline: top3を276Rすべて購入
- R = 276
- hits = 119
- hit rate = 43.1159%
- total stake = 2,760,000円
- total return = 2,567,630円
- profit = -192,370円
- ROI = 93.0301%

### 最終点数分布（購入33R）
- 3点: 29R
- 4点: 2R
- 5点: 1R
- 6点: 1R

### 月別 adaptive 結果
- 2026-02: 4R / 1hit / stake 40,000 / return 34,560 / profit -5,440 / ROI 86.40%
- 2026-03: 3R / 1hit / stake 30,000 / return 42,780 / profit +12,780 / ROI 142.60%
- 2026-04: 5R / 3hit / stake 50,000 / return 96,530 / profit +46,530 / ROI 193.06%
- 2026-05: 4R / 0hit / stake 40,000 / return 0 / profit -40,000 / ROI 0.00%
- 2026-06: 10R / 4hit / stake 100,000 / return 140,190 / profit +40,190 / ROI 140.19%
- 2026-07: 2R / 0hit / stake 20,000 / return 0 / profit -20,000 / ROI 0.00%（NON-PRISTINE）
- 2026-08: 5R / 2hit / stake 50,000 / return 67,200 / profit +17,200 / ROI 134.40%（NON-PRISTINE）

### 結論
- ユーザー指定の「top3合成オッズ3倍未満は見送り、4倍以上は3倍を割らない範囲で買い目追加」は、この固定276R検証ではbaseline top3全購入を大きく改善した。
- ROI: 93.03% → 115.53%（+22.50pt）
- 損益: -192,370円 → +51,260円（+243,630円改善）
- 投資対象を276Rから33Rへ大幅に絞るため、主な改善源は低合成オッズレースの見送り。
- expandは7Rのみで、最終33Rのうち29Rは3点のまま。点数追加は補助的役割。
- Jul/AugはNON-PRISTINEなので、正式production変更の根拠には単独で使わない。
- 正式production `HEAD cutoff .78 / v332 q=.65 / v317 / v318 / v320` は変更しない。
- 9月outcomesはUNREADのまま維持した。

### 次の再開地点
1. v340 adaptive policyを正式productionの「購入後段ルール候補」として扱う。
2. 必要ならFeb-Jun pristineだけのROIを別集計して、Jul/Aug非pristineを除外した堅牢性を確認する。
3. skip/keep3/expand別の的中・損益寄与、特にexpand 7Rの純粋な増分効果を監査する。
4. 合成オッズ閾値 3.0 / 4.0 を固定production選定とは分離して近傍感度検証する。
5. 2026年9月outcomesは引き続きUNREAD。
