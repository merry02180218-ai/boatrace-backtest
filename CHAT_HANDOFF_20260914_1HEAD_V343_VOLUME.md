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
