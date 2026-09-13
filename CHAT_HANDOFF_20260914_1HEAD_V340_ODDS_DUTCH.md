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

## 完了後に追記するもの
- 実装commit / workflow commit
- GitHub Actions Run / Job / Artifact ID
- 実測結果
- オッズ欠損があればその件数と扱い
- 結論と次の再開地点
