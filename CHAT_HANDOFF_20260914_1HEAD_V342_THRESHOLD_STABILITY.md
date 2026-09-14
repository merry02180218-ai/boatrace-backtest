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

## Actions
- Run `34804207503`
- audit Job `103852724255`
- 現在: IN_PROGRESS（2026-09-14 12:55 JST時点）

## 途中再計算（正式値はCI完走後に確定）
Feb-Jun pristine-only:
- 2.7: 45R / 16hit / +66,790円 / ROI 114.8422%
- 2.8: 39R / 16hit / +126,790円 / ROI 132.5103%
- 2.9: 32R / 13hit / +112,090円 / ROI 135.0281%
- 3.0: 26R / 9hit / +54,060円 / ROI 120.7923%
- 3.1: 21R / 6hit / +11,370円 / ROI 105.4143%
- 3.2: 18R / 6hit / +41,370円 / ROI 122.9833%
- 3.3: 16R / 5hit / +29,420円 / ROI 118.3875%

暫定では2.9が総合ROI最大、2.8が利益額最大。ただし月別ブレがあるためCI結果と月別安定性を見てから判断する。

## 次の再開地点
1. Run `34804207503` のconclusion確認。
2. Artifact回収。
3. 月別安定性を含めて2.8 / 2.9 / 3.0を比較。
4. 完了結果を本ファイルへ追記。
5. `SEPTEMBER_OUTCOMES_READ=false` を明記。
