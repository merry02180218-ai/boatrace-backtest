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

# BEFORE — 次の作業: HEAD × opponent mass × 直前判定の合成ROIグリッド探索
ユーザー指示（2026-09-17）:
「頭確率とopponent mass判定、直前判定でそれぞれ値変えて一番合成オッズROIが良くなるとこを探したい」→実施許可済み。

## 目的
現行productionを中心に3軸を同時に振り、単独軸最適化ではなく相互作用込みで、historicalの合成オッズROIが高く、かつ周辺条件でも崩れにくい安定帯を探す。

## 探索方針
- HEAD cutoff: 現行 .780 周辺を細かく探索（初期候補 .775/.7775/.780/.7825/.785/.7875/.790。既存コード/過去監査の再利用可能範囲を確認して必要なら拡張）。
- opponent mass min: 現行 .375 周辺（初期候補 .350/.3625/.375/.3875/.400/.4125/.425）。
- 直前判定: 現行 exhibition `v332_ATTACK_ENV_SOFT_V345_ATTACKCORE` の env_w=.10 / q=.65 を中心に、既存semanticsを壊さず env_w と q の近傍を探索する。まず既存実装・過去監査で有効だった値を確認してグリッドを確定する。
- ticketは現行v320 HYBRID基本3点を固定。THIRD close-margin 4点化は混ぜない。
- opponent core G2=.45/G3=1.00は固定し、今回の探索軸にしない。

## 評価指標
各組み合わせで最低限:
- R / HEAD hits & rate / exact3 hits & rate
- tickets / stake / return / profit / ROI
- 合成オッズ（可能なら race-level combined odds と全体要約）
- 月別 R / hit / stake / return / ROI
- 最大DDまたは時系列収支の安定性指標
- 現行productionとの差分
- ROI最高点だけでなく、その周辺セルのROI・R数が維持される安定帯を確認

## ガード
- 2026-09-17 result/payoutはhard reject、UNREAD維持。
- formal productionセル (.780,.375,env_w=.10,q=.65) は既知baseline 276R / HEAD241 / exact3 131 を再現できることをsentinelにする。
- race/ticket identityを可能な限り既存production定数で照合。
- payout欠損は前監査同様、BoatraceCSV primary + historical official fallback、9/17以降は禁止。
- Jul-Augのnon-pristine性は明示し、ROI最大一点をそのままproduction昇格しない。

## 次の実作業
1. 最新のHEAD/opponent/exhibition監査コードを検索して再利用可能な部品を特定。
2. グリッド監査script/workflowを実装。
3. Actions発火。
4. 完了後、Run/Job/Artifact、全グリッド上位と安定帯、production比較を本handoffへAFTER追記。
