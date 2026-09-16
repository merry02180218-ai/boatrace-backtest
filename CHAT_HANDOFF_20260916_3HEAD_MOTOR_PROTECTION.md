# 3号艇 v288 展示補正 Motor Protection 引き継ぎ

Date: 2026-09-16
Branch: `research/3head-player-attack-mode`

## 既存OFF gate AFTER
- implementation `ecffb441008fe944faf0c0c083f9ba998567015a`
- workflow `49163da4726d206686cefa730f63e723dfef9d19`
- Run `35065912592` SUCCESS / Job `104696025937`
- Artifact `10434665644` / SHA256 `4e3df5c1613ebf932d5cd61e4d318e80674b385743acd53e54251d1c4717724d`
- discovery best .55/.20/gap0 は Apr-Jun 5 blocked / 5 lost / net 0。
- gap>=.01 + weak exhibition advantage の一部候補は Apr-Jun aggregate +2 だが、validationを見て選択してはいけないため未freeze。
- production v288 unchanged / September outcomes UNREAD。

## Motor Protection BEFORE
これから行うこと:
1. v288 baseline順位を基本的に保護する。
2. 展示補正でtop3に入るpairと押し出されるpairについて、事前の `モーター2連対率` / `モーター3連対率` のpair加重強度差を算出する。
3. `base_gap`、`ex_adv`、`st_adv`、`swap_adj_adv`、motor advantage を組み合わせ、展示根拠が弱く、かつ元pairのモーター根拠を覆せない時だけ補正OFFにする。
4. Februaryは同月fitなので参考のみ。**Marchのみをrule discovery**に使い、候補を固定して Apr/May/Jun を月別に独立評価する。
5. Apr-Junでは `broken_blocked / rescues_lost / net_off` を月別に必ず出す。Jul-AugはNON-PRISTINE参考のみ。
6. 大規模gridは避け、実運用可能な単純ruleだけを探索する。
7. exact v288 exclusion維持。September 2026 outcomesは絶対に読まず `UNREAD`。productionは変更しない。

## 完了条件
- 実装commit
- fresh Actions Run/Job SUCCESS
- Artifact ID/SHA256確認
- March discovery ruleとApr/May/Jun月別結果確認
- 安定しなければfreezeしない
- AFTERを本ファイルへ追記して次の再開地点を明記
