# 1号艇 v351 現状引き継ぎ — 2026-09-17

Repo: `merry02180218-ai/boatrace-backtest`

## 最重要ルール / ユーザー運用方針
- 最新GitHub + 本handoffを、古いチャット/記憶より必ず優先する。
- 作業開始前に「これからやること」、完了後に結果・commit SHA・Actions Run/Job/Artifact・結論・次の再開地点を本handoffへ記録する。
- 失敗時は logs / artifact / existing code / commit履歴を先に確認し、盲目的にrerunしない。
- 未確認の完了/成功を断言しない。
- 自動LIVEより、ユーザーが「判別して」と言った時の手動取得/判定を優先。
- HEAD学習特徴へ展示を直接追加しない。展示は post-ranking / ticket-rescue / live final correction のみ。

## September結果の扱い
- retrospective評価に限り 2026-09-01〜09-16 の結果・払戻は読み取り許可済み。
- **2026-09-17当日結果・払戻は絶対に読まない。UNREAD維持。**

## 現行production
`1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- HEAD v308 cutoff=.78
- opponent mass min=.375
- SECOND v317_OUTER_L2_1
- THIRD v318_DROPSTART_T0.1
- ticket v320_HYBRID alpha=.70 基本3点
- exhibition v332_ATTACK_ENV_SOFT_V345_ATTACKCORE env_w=.10 / q=.65
- opponent core G2=.45 / G3=1.00
- formal baseline 276R / HEAD 241=87.32% / exact3 131=47.46%

## THIRD close-margin監査 完了
Run 35221732112 / Job 105206482047 / Artifact 10498887442 / head eeb7e8a020e1f0c725a10770bc01db334a8a24e6
AUDIT_OK=true / sentinel 276/241/131 / 9/17 result,payout unused.
BASE: 131 hits, stake 82800, return 86390, profit +3590, ROI 104.34%.
.05: expanded 92, hits 136 (+5), stake 92000, return 92180, profit +180, ROI 100.20%.
.10: expanded 162, hits 142 (+11), stake 99000, return 98290, profit -710, ROI 99.28%.
.15: expanded 210, hits 145 (+14), stake 103800, return 103680, profit -120, ROI 99.88%.
結論: close-margin単独4点化は的中率を上げるがBASE 3点のROIを下回るため未昇格。

---

# BEFORE — HEAD × opponent mass × 直前判定の合成ROIグリッド探索
ユーザー指示: 「頭確率とopponent mass判定、直前判定でそれぞれ値変えて一番合成オッズROIが良くなるとこを探したい」実施許可済み。

## 探索仕様
- HEAD cutoff: .775/.7775/.780/.7825/.785/.7875/.790
- opponent mass min: .350/.3625/.375/.3875/.400/.4125/.425
- exhibition env_w: .05/.10/.15
- exhibition q: .60/.65/.70
- 計441セル。
- ticket=v320 HYBRID基本3点固定。close-margin 4点化は混ぜない。
- opponent core G2=.45/G3=1.00固定。
- productionセル (.780,.375,.10,.65) は 276R / HEAD241 / exact3 131 を必須sentinel。
- 2026-09-17 result/payout hard reject、UNREAD維持。

## 進捗 / 障害
- manifest Run 35234365735 / Job 105246363819 は成功。
- 実計算workflowを追加したが Run 35236067163 / Job 105252175139 は依存関係installで失敗。
- ログ確認結果: repo直下に存在しない `requirements.txt` を `pip install -r requirements.txt` していたのが原因。モデル/441セル計算には未到達。

## 2026-09-18 00:10 JST 修正
- 既存の正常稼働 `v351-1head-third-close-margin-audit.yml` を確認し、同じ依存関係 `numpy pandas scipy scikit-learn==1.6.1 requests beautifulsoup4 lxml` の直接install方式へ変更。
- runnerも既存監査に合わせ `ubuntu-24.04`。
- 失敗時にも result/summary とartifactを可能な範囲で残すよう `if: always()` を追加。
- 修正commit: `53b1a4f9b8bdcb9c6f202ba96dfef5e5552687c7`
- **次の再開地点:** `.github/workflows/v351-1head-joint-roi-grid.yml` を手動発火し、fresh Runのaudit jobを確認。成功ならArtifactの `summary.csv/monthly.csv/result.json` を回収し、441セルのraw best + 周辺安定帯 + production比較を監査する。失敗ならログから次の原因を特定し、盲目的rerunしない。

## BEFORE — Run 35238661088 failure fix
- Run 35238661088 / Job 105261103198 logs verified: dependency install succeeded, then `cache_v321_julaug_nonpristine_head.csv` missing in `v337.load_candidate_base()`.
- これからやること: 正常監査と同じ v321 prepare/second/base-third/third cache pipelineをjoint ROI workflowへ追加し、audit jobへ全cacheをdownloadしてから441-cell scriptを実行する。9/17 result/payout UNREAD guardは維持。
