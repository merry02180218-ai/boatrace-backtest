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

## 完了後に追記するもの
- Sharded実装commit / workflow commit / handoff commit
- GitHub Actions Run / 全Job / Artifact ID
- 276R odds coverageと欠損
- skip / keep3 / expand件数
- adaptiveの購入R / hit / 投資 / 払戻 / 損益 / ROI
- baseline top3全購入の同指標
- 最終点数分布 / 月別結果
- 結論と次の再開地点
- `SEPTEMBER_OUTCOMES_READ=false` の確認
