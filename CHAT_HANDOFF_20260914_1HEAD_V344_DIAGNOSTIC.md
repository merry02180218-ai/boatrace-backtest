# 1号艇モデル 引き継ぎ — v344 事前特徴量診断

作成日: 2026-09-14
repo: merry02180218-ai/boatrace-backtest

## 作業開始記録
- 前回完了: `CHAT_HANDOFF_20260914_1HEAD_V343_VOLUME.md`
- v343結論: 単純combined odds閾値では、Feb-Jun pristineで80BET以上かつROI110%以上を同時達成できない。
- 正式production本体は変更しない: `1HEAD_PRODUCTION_20260914_HEAD078`
- Jul/AugはNON-PRISTINE、Sep outcomesはUNREAD。

## 今回やること
1. 2.20〜2.50帯を中心に、結果を使わない事前特徴量と的中・払戻結果の関連を後方診断する。
2. 主評価はFeb-Jun pristine-only。Jul/Augは補助ストレス確認のみ。
3. 候補特徴量: p_head、opp_mass、展示由来のattack_core/env_pair、top3個別オッズ、odds spread/concentration。
4. 目的はBET数を減らす条件を直接採用することではなく、v343でvolumeを増やした際にどの特徴群が弱いレースと関連しているかを特定すること。
5. leave-one-month-outで関連の方向が維持されるか確認し、特定月依存の特徴は採用候補にしない。
6. 正式productionは監査だけで変更しない。
7. `SEPTEMBER_OUTCOMES_READ=false` を厳守する。
