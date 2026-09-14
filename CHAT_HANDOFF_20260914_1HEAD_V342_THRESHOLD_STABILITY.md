# 1号艇モデル 引き継ぎ — v342 combined-odds skip閾値安定性監査

作成日: 2026-09-14
repo: merry02180218-ai/boatrace-backtest

## 作業開始記録
- 前回完了: `CHAT_HANDOFF_20260914_1HEAD_V341_ROBUSTNESS.md`
- 正式production本体は変更しない: `1HEAD_PRODUCTION_20260914_HEAD078`
  - HEAD/PRE cutoff = 0.78
  - exhibition = v332 ATTACK_ENV_SOFT, env_w=0.1, q=0.65
  - SECOND = v317 OUTER_L2_1
  - THIRD = v318 DROPSTART_T0.1
  - ticket ranking = v320 HYBRID alpha=.70
- production identity = 276R / head 241 / exact3(top3) 119 / SHA256 `89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73`
- Jul/AugはNON-PRISTINE。
- Sep outcomesはUNREAD。今回も読まない。

## v341からの確定事項
- Feb-Jun pristine-only adaptive: 26R / 9hit / +54,060円 / ROI 120.7923%
- v340改善の全差分 +243,630円はskip243Rで回避した損失と一致。
- expand 7Rの追加的中・追加利益は0。
- よって購入後段の本命は「combined oddsが閾値未満なら見送り」の単純ルール。

## v342でやること
- v340固定race-level artifactだけを使用。
- top3 combined odds閾値 2.7 / 2.8 / 2.9 / 3.0 / 3.1 / 3.2 / 3.3 を比較。
- 主評価: Feb-Jun pristine-onlyのbought_R / hits / profit / ROI / 月別安定性。
- Jul/Aug込みは補助評価のみ。
- 正式productionは監査完了まで変更しない。

## 実装
- script commit: `bed3028ea46f91f7cb9d260db39ecaebe1155ef1`
- workflow commit: `2a67a87b30b4a1dd1604bad19c5074b1f79b9992`
- script: `run_v342_1head_skip_threshold_stability.py`
- workflow: `.github/workflows/v342-1head-skip-threshold-stability.yml`
- top-level `name:` は置いていない。

## Actions — 完了
- Run `34804207503`: SUCCESS
- audit Job `103852724255`: SUCCESS
- Artifact `10332352437`: `v342-1head-skip-threshold-stability`
- artifact digest: `sha256:86c1268b16fc43f237143f594653ec4eb4cd7556877fa820aff8e13db85f6fb3`
- production identity guard: PASS 276R / head241 / exact3(top3)119
- `SEPTEMBER_OUTCOMES_READ=false`

## v342 正式結果

### Feb-Jun pristine-only
| threshold | bought_R | hits | profit | ROI |
|---:|---:|---:|---:|---:|
| 2.7 | 45 | 16 | +66,790円 | 114.8422% |
| 2.8 | 39 | 16 | **+126,790円** | 132.5103% |
| 2.9 | 32 | 13 | +112,090円 | **135.0281%** |
| 3.0 | 26 | 9 | +54,060円 | 120.7923% |
| 3.1 | 21 | 6 | +11,370円 | 105.4143% |
| 3.2 | 18 | 6 | +41,370円 | 122.9833% |
| 3.3 | 16 | 5 | +29,420円 | 118.3875% |

- ROI最大は2.9 = 135.0281%。
- 利益額最大は2.8 = +126,790円。
- 2.8は2.9より7R多く買い、的中も3件多い。
- 3.0は2.8・2.9の双方にaggregateで明確に劣後する。

### Feb-Aug（Jul/AugはNON-PRISTINEなので補助評価）
| threshold | bought_R | hits | profit | ROI |
|---:|---:|---:|---:|---:|
| 2.7 | 55 | 18 | +33,990円 | 106.1800% |
| 2.8 | 48 | 18 | +103,990円 | 121.6646% |
| 2.9 | 39 | 15 | **+109,290円** | **128.0231%** |
| 3.0 | 33 | 11 | +51,260円 | 115.5333% |
| 3.1 | 28 | 8 | +8,570円 | 103.0607% |
| 3.2 | 23 | 7 | +27,250円 | 111.8478% |
| 3.3 | 20 | 6 | +25,300円 | 112.6500% |

補助評価では2.9が利益額・ROIとも最大。ただしJul/AugはNON-PRISTINEのため、production判断の主根拠にはしない。

## 月別 pristine 安定性

### threshold 2.8
- Feb: 4R / 1hit / -5,440円 / ROI 86.40%
- Mar: 6R / 3hit / +40,110円 / ROI 166.85%
- Apr: 9R / 5hit / +64,740円 / ROI 171.93%
- May: 6R / 1hit / -31,510円 / ROI 47.48%
- Jun: 14R / 6hit / +58,890円 / ROI 142.06%

### threshold 2.9
- Feb: 4R / 1hit / -5,440円 / ROI 86.40%
- Mar: 4R / 2hit / +32,210円 / ROI 180.53%
- Apr: 8R / 4hit / +46,430円 / ROI 158.04%
- May: 4R / 0hit / -40,000円 / ROI 0%
- Jun: 12R / 6hit / +78,890円 / ROI 165.74%

### threshold 3.0
- Feb: 4R / 1hit / -5,440円 / ROI 86.40%
- Mar: 3R / 1hit / +12,780円 / ROI 142.60%
- Apr: 5R / 3hit / +46,530円 / ROI 193.06%
- May: 4R / 0hit / -40,000円 / ROI 0%
- Jun: 10R / 4hit / +40,190円 / ROI 140.19%

## 解釈
1. 3.0は局所的最適ではない。2.8/2.9へ下げる方がpristineで明確に改善する。
2. 2.9は総合ROI最大だが、32Rとサンプルがやや小さく、Mayは0/4で-40,000円。
3. 2.8はROI差が2.9より2.52pt低いだけで、39R/16hit、利益+126,790円とvolume・利益額が最大。Mayにも1hitが残り、2.9より下方耐性が少し良い。
4. したがって現時点の「実運用候補」は2.8を第一候補、2.9を高ROI候補とする。
5. ただし同じFeb-Junデータ上で閾値選択をしているため、ここだけで正式productionへ昇格はしない。

## 正式productionの扱い
- 1号艇予測本体は引き続き `HEAD .78 / v332 q=.65 / v317 / v318 / v320` を維持。
- 購入後段はまだ正式変更しない。
- v340のexpandロジックは追加価値0のため、今後の主軸候補から外す。
- 次の検証対象は単純な `top3 combined odds >= threshold の時だけ1万円Dutch`。

## 次の再開地点 — v343
1. threshold 2.75 / 2.80 / 2.85 / 2.90 / 2.95 の細粒度比較。
2. Feb-Jun pristineで leave-one-month-out を実施し、1か月ずつ除外しても2.8/2.9帯が優位か確認。
3. 月別最悪損益・最悪ROI・購入R数を含むrobust scoreを作り、単純総ROIだけで選ばない。
4. 2.8がfine sweep/LOMOでも優位なら、購入後段のproduction候補として固定する。
5. Jul/AugはNON-PRISTINEの補助確認だけに使う。
6. 2026年9月 outcomes は引き続きUNREADを厳守する。

`SEPTEMBER_OUTCOMES_READ=false`
