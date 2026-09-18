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

## AFTER — cache pipeline修正完了
- workflow commit: `0f8c666e3100d119636048d8784afc505e34e681`。
- `prepare -> second/base-third/third -> audit` の依存関係を追加し、正常稼働close-margin監査と同じ4種cacheをauditへdownloadする構成に修正。
- auditは全cache生成成功後のみ441セルを開始。結果表示/artifactは `if: always()` 維持。
- 2026-09-17 result/payoutを読む処理は追加していない。UNREAD維持。
- 次の再開地点: fresh workflow_dispatch -> 各Job確認 -> audit完了ならartifact回収、sentinel 276/241/131確認、ROI/安定帯解析。

## BEFORE — Run 35290276441 sentinel access fix
- Run 35290276441: prepare/second/base-third/third success, audit Job 105433770003 failed at final production sentinel.
- 原因: pandas Series `p.head` が列 `head` ではなく method を返し `int(p.head)` で TypeError。これから bracket access `p['head']` 等へ修正し、sentinel自体は緩めず 276/241/131 を必須維持する。

## AFTER — sentinel access fix
- 修正commit `6bd95e5603858abf69697642e4161f9fc6f1a998`。
- `p.R/p.head/p.exact3` を `p['R']/p['head']/p['exact3']` に変更。276/241/131 sentinel条件そのものは変更なし。
- 次: fresh workflow_dispatch。成功時はproduction sentinel/ROIと441セル上位・周辺安定帯を回収。9/17 result/payout UNREAD維持。

## BEFORE — Run 35294726696 production identity repair
- Run 35294726696 / audit Job 105446582746: cache jobs all success; production cell got 276/241/129, expected 276/241/131, sentinel correctly stopped.
- Code comparison confirmed joint grid order was wrong: it applied v332 fit/filter first and v345 attack-core after selection. Formal production does `build_exhibition -> apply_v345_attack_core -> eval_cut(v332 fit/filter) -> v351 opponentCore ticket rerank`.
- これからやること: broad universeは HEAD min=.75 を保持して massだけ.35へ拡張し、各massごとに v345 attack-coreを先に適用、その後 custom env CFGでproduction-equivalent evalを行う。production cellは race/ticket identityまで正式v351と一致させる。sentinelは緩めない。9/17結果/払戻UNREAD維持。

## AFTER — production-order repair
- 修正commit `5d6743ce2c4bf2d4512e7fe29fa11d624b4d716e`。
- 原因確定: joint gridが `v332 fit/filter -> v345 attackCore` の逆順だった。正式v351と同じ `mass universe -> v345 attackCore -> HEAD/env v332 filter -> v351 opponentCore tickets` に変更。
- broad universeはmassのみ.35へ拡張し、v337のHEAD floor=.75を保持。productionセルの学習母集団を変えない。
- production sentinelを 276/241/131 に加え race SHA / ticket SHA まで正式profileと一致必須へ強化。sentinel緩和なし。
- 次: fresh workflow_dispatch。成功後artifact回収、441セルraw ROIと安定帯を監査。9/17 result/payout UNREAD維持。

# 2026-09-18 CHAT END HANDOFF — 次チャットはここから

## このチャットで確定したこと
- 441セル joint ROI監査の production再現ズレを調査・修正した。
- Run 35294726696 / audit Job 105446582746 は production cell が 276R / HEAD241 / exact3 129 となり、期待131に対して `PRODUCTION_SENTINEL_DRIFT` で停止。sentinelは正しく機能。
- 原因は joint grid の処理順。旧コードは HEAD/MASS絞り -> v332 fit/filter -> v345 attackCore だったが、正式v351は build_exhibition -> v345 attackCore -> v337/v332 exhibition filter -> v351 opponentCore ticket rerank。
- 修正commit `5d6743ce2c4bf2d4512e7fe29fa11d624b4d716e`。broad universeは opponent massのみ.35へ拡張し、v337 HEAD floor=.75を維持。productionセルの学習母集団を変えない。
- production sentinelは 276/241/131 に加え race identity SHA / ticket identity SHA まで正式profileと完全一致必須。絶対にsentinelを弱めて通さない。
- 修正前後handoff commits: BEFORE `b68559710aca47fda70a8618ed26a9f850968be7`, AFTER `379190b2715f359493aeb9a75453cc84d0467c38`。

## 441セル監査 — 最新状態
Workflow: `.github/workflows/v351-1head-joint-roi-grid.yml`
最新Run: `35302023710`
URL: https://github.com/merry02180218-ai/boatrace-backtest/actions/runs/35302023710
Run head SHA: `28cc9dcfb375fd8e01a04ba1e4fcaa3e5ac9101f` (message: fix: parse R-suffixed race number in broad50)
handoff記録時点: **in_progress**
Jobs:
- prepare `105466461575`: success
- base-third `105467483200`: success
- third `105467483222`: success
- second `105467483225`: success
- audit `105468495136`: in_progress
重要: ユーザーは「441セル監査がエラー」と言ったが、GitHub確認時点では最新Runはエラー終了ではなくaudit実行中。1つ前のRun `35298138766` は全Jobs success。次チャットではまず最新Run 35302023710 の最終status/log/artifactを確認すること。失敗ならログを読んで原因修正、成功ならartifactを回収してproduction sentinelと441セル結果を詳細監査。

### 441セル探索仕様
HEAD: .775/.7775/.780/.7825/.785/.7875/.790
MASS: .350/.3625/.375/.3875/.400/.4125/.425
ENV_W: .05/.10/.15
ENV_Q: .60/.65/.70
計441セル。
固定: ticket v320 HYBRID alpha=.70 3点、opponent core G2=.45/G3=1.00。close-margin 4点化は混ぜない。
production cell=.78/.375/.10/.65。
正式 baseline: 276R / HEAD241 / exact3 131 / stake 82,800 / return 86,390 / profit +3,590 / ROI 104.34%。
正式 race SHA: `08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd`
正式 ticket SHA: `21631473d2a8b82f4fe93d18f8292d777837c26a47c408917fd8b722d1898cd7`
Feb-Jun: 220R / exact3 107。Jul-Aug: 56R / exact3 24, NON_PRISTINE_SUPPORT_ONLY。
最終評価ではraw ROIだけでなく、月別、Feb-Jun dev、Jul-Aug support、平均的中オッズ、隣接セル/plateau安定性も見る。孤立最高値だけでproduction昇格しない。自動昇格禁止。

## 本日 2026-09-18 1号艇LIVE
Daily cache Run `35257663423` success / Artifact `10512844501` name `v351-1head-live-cache-20260918`。
metadata candidate_R=180 は summary bugで、pre_candidates.csvが全180R NON_CANDIDATEになっている。各race JSON自体は有効。production条件 HEAD>=.78 & mass>=.375 で実質5候補:
1. 平和島12R `202609180412`: HEAD .8010601806 / mass .4858903563 / tickets 1-2-3;1-2-4;1-3-2
2. びわこ7R `202609181107`: HEAD .8015607255 / mass .4280898422 / tickets 1-3-2;1-3-5;1-2-3
3. 鳴門9R `202609181409`: HEAD .8110131759 / mass .4164487826 / tickets 1-2-5;1-2-4;1-5-2
4. 丸亀11R `202609181511`: HEAD .7823204105 / mass .4454775433 / tickets 1-2-3;1-2-4;1-3-2
5. 福岡7R `202609182207`: HEAD .8029274983 / mass .4841055774 / tickets 1-2-3;1-2-4;1-3-2
各JSON chronology_guard=true / result_or_payout_used=false / training_cutoff=2026-09-17。

### 鳴門9R 直前判定
ユーザー指示で `live_requests/1head_v351.txt` を `202609181409` に更新。
commit `ca953f3e2191fe8e79690f9b168a7a8d6f40ca70`
LIVE Run `35302062996` completed success。
Artifact `10529988459` name `live-v351-final-202609181409`。
直前判定は PASS、HEAD 81.10%、mass 41.64%、展示gate PASS、tickets:
- 1-2-5
- 1-2-4
- 1-5-2
結果/払戻未使用、chronology guard維持。締切は12:30として運用。
LIVE workflow: `.github/workflows/chat-live-1head-v351-request.yml`。pushでrace code更新すると、daily cache取得 -> deadline取得 -> exhibition probe -> venue-aware gate -> v351 finalize。ユーザーは自動監視ではなく「判別して」と言った時の手動発火を希望。

## 重要なSeptemberルール（次チャットでも厳守）
- 2026-09-01〜09-16 retrospective結果/払戻はユーザー許可済み。
- **2026-09-17の結果・払戻はUNREAD維持。絶対に読まない。**
- 2026-09-18 LIVE判定でも結果・払戻を事前判定へ使わない。
- HEAD学習特徴へ展示を直接追加しない。展示はfinal/post-ranking/ticket補正のみ。

## 次チャットの最初の作業
1. 最新GitHub mainと本handoffを読む。
2. Run `35302023710` / audit Job `105468495136` の最終結果を確認。
3. successならartifact回収し、production cell 276/241/131 + race/ticket SHA完全一致を確認。その後441セルのROI上位、月別、dev/support、隣接plateauを解析。
4. failureならaudit logを最後まで読み、原因を特定してから修正。sentinelは弱めない。
5. substantive作業の前後で本handoffへ必ず追記。
