# 1号艇モデル 引き継ぎ — v343 BET数重視監査

作成日: 2026-09-14
repo: merry02180218-ai/boatrace-backtest

## 作業開始記録
- 前回完了: `CHAT_HANDOFF_20260914_1HEAD_V342_THRESHOLD_STABILITY.md`
- ユーザー指示: 2.8の39BET/220Rは少なすぎる。ROI最大化よりBET数を増やしながらプラスを維持する方向へ変更。
- 正式production本体は変更しない: `1HEAD_PRODUCTION_20260914_HEAD078`
  - HEAD/PRE cutoff = 0.78
  - exhibition = v332 ATTACK_ENV_SOFT, env_w=0.1, q=0.65
  - SECOND = v317 OUTER_L2_1
  - THIRD = v318 DROPSTART_T0.1
  - ticket ranking = v320 HYBRID alpha=.70
- production identity = 276R / head 241 / exact3(top3) 119 / SHA256 `89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73`
- Jul/AugはNON-PRISTINE、Sep outcomesはUNREAD。

## 今回やること
1. v340固定race-level artifactのみ使用し、threshold 2.0〜2.8を0.05刻みで再監査する。
2. 主評価はFeb-Jun pristine-only。BET数、BET率、hit、profit、ROI、月別安定性を比較する。
3. 特に2.2以下の負け帯と2.3〜2.6の勝ち帯をcombined-odds binで分解する。
4. 目標はBET数80〜120R程度まで増やしながらROI 110%以上。ただしデータが支持しなければ無理に条件を作らない。
5. leave-one-month-outで閾値の耐性を確認し、単純総ROIだけで選ばない。
6. 正式productionは監査だけで変更しない。
7. `SEPTEMBER_OUTCOMES_READ=false` を厳守する。

## 実装
- script: `run_v343_1head_volume_first_audit.py`
- workflow: `.github/workflows/v343-1head-volume-first-audit.yml`
- workflowはtop-level `name:` なし。
- handoff開始commit: `e4aa9787e00c6a114a563833f80ed5173262723b`
- script commit: `fdac49e0768003f10cba9b6b5a27f13e5f091796`
- workflow commit: `d47adf11b5255b2bde12c01dc3be454736c7a974`

## Actions — 完了
- Run `34807923316`: SUCCESS
- audit Job `103863332180`: SUCCESS
- Artifact `10333921090`: `v343-1head-volume-first-audit`
- artifact digest: `sha256:866c0ea99c4476ac7b6c6ef20e64436ba88b09f30a37458019ae7cc05ce871df`
- production identity guard: PASS = 276R / head241 / exact3(top3)119
- `SEPTEMBER_OUTCOMES_READ=false`

## v343 正式結果 — Feb-Jun pristine-only

| threshold | BET R | hit | profit | ROI |
|---:|---:|---:|---:|---:|
| 2.00 | 137 | 46 | -161,450円 | 88.22% |
| 2.10 | 119 | 41 | -83,810円 | 92.96% |
| 2.20 | 102 | 36 | -21,770円 | 97.87% |
| 2.25 | 90 | 30 | -35,920円 | 96.01% |
| 2.30 | 80 | 29 | +41,540円 | 105.19% |
| 2.35 | 73 | 26 | +41,630円 | 105.70% |
| 2.40 | 68 | 25 | +68,030円 | 110.00% |
| 2.45 | 64 | 24 | +84,030円 | 113.13% |
| 2.50 | 57 | 21 | +80,480円 | 114.12% |
| 2.55 | 54 | 21 | +110,480円 | 120.46% |
| 2.60 | 52 | 20 | +104,960円 | 120.18% |
| 2.65 | 51 | 20 | +114,960円 | 122.54% |
| 2.70 | 45 | 16 | +66,790円 | 114.84% |
| 2.75 | 42 | 16 | +96,790円 | 123.05% |
| 2.80 | 39 | 16 | +126,790円 | 132.51% |

## 目標判定
- 80〜120BETかつROI 110%以上を満たす単純combined-odds閾値は存在しない。
- ROI 105%以上で最大BET数: threshold 2.30 = 80R / 29hit / +41,540円 / ROI 105.19%。
- ROI 110%以上で最大BET数: threshold 2.40 = 68R / 25hit / +68,030円 / ROI 110.00%。
- したがってBET数80以上を維持しつつROI110%以上へ上げるには、単純閾値だけでは不足。2.2〜2.4周辺の悪いレースを事前情報で選別する二段階filterが必要。

## odds帯別 — Feb-Jun pristine
- <2.0: 83R / 48hit / +7,420円 / ROI100.89%
- 2.0-2.1: 18R / 5hit / -77,640円 / ROI56.87%
- 2.1-2.2: 17R / 5hit / -62,040円 / ROI63.51%
- 2.2-2.3: 22R / 7hit / -63,310円 / ROI71.22%
- 2.3-2.4: 12R / 4hit / -26,490円 / ROI77.93%
- 2.4-2.5: 11R / 4hit / -12,450円 / ROI88.68%
- 2.5-2.6: 5R / 1hit / -24,480円 / ROI51.04%
- 2.6-2.7: 7R / 4hit / +38,170円 / ROI154.53%
- 2.7-2.8: 6R / 0hit / -60,000円 / ROI0%
- 2.8-3.0: 13R / 7hit / +72,730円 / ROI155.95%
- 3.0-3.5: 15R / 6hit / +42,760円 / ROI128.51%
- 3.5-4.0: 5R / 1hit / -15,440円 / ROI69.12%
- >=4.0: 6R / 2hit / +26,740円 / ROI144.57%

### 重要解釈
- combined oddsと収益は単調ではない。2.7-2.8が0/6なのに2.6-2.7と2.8-3.0は強い。
- よって閾値をさらに細かく弄るだけでは過学習化しやすい。
- 2.2〜2.4帯だけを機械的に全除外するとBET数が減るので、次はその帯の当たり/外れを事前特徴量で分けるべき。

## LOMO
- threshold 2.30 worst LOMO = ROI95.74%, profit -25,960円（Apr除外）。
- threshold 2.40 worst LOMO = ROI96.18%, profit -19,470円（Apr除外）。
- threshold 2.55は全LOMOでROI105%以上、worst=105.25%だが54BETでvolume不足。
- threshold 2.65は全LOMOでROI106%以上、worst=106.80%だが51BETでvolume不足。
- 高volume帯はまだ月依存が残る。

## 月別の弱点
- 2.30: May 21R / 5hit / -86,640円 / ROI58.74%。
- 2.40: May 14R / 2hit / -87,010円 / ROI37.85%。
- 低閾値化でBET数を増やすとMayの負けレースを大量に拾うのが主な問題。

## Jul/Aug補助
- threshold 2.30: 104R / ROI99.57%（NON-PRISTINE込み）。
- threshold 2.40: 89R / ROI103.20%。
- threshold 2.55: 69R / ROI111.78%。
- threshold 2.60: 66R / ROI112.99%。
- Jul/AugはNON-PRISTINEのためproduction選定根拠にはしない。

## 正式productionの扱い
- 予測本体は `HEAD .78 / v332 q=.65 / v317 / v318 / v320` のまま。
- 購入後段もまだ正式productionへ昇格しない。
- v343の結論は「BET数80以上・ROI110%以上は単純combined閾値だけでは達成できない」。

## 次の再開地点 — v344
1. threshold 2.20または2.30を広い入口として使う。
2. 主に2.2〜2.5帯の当たり/外れを、結果を使わない事前特徴量で比較する。
3. 候補特徴量: HEAD score/margin、SECOND/THIRD score gap、展示系score、top1/top2/top3 odds形状、ticket odds spread/concentration、rank gap。
4. 80BET以上をなるべく維持し、ROI110%以上へ持ち上げる単純二段階filterを探索する。
5. 月別・LOMOで再評価し、Mayだけを狙い撃ちする条件は採用しない。
6. Jul/Augは補助、Sep outcomesはUNREADを継続。

`SEPTEMBER_OUTCOMES_READ=false`
