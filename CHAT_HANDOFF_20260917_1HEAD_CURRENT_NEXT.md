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


## BEFORE — 2026-09-18 Run 35302023710 final確認 / 441セル解析
- ユーザー指示: Run 35302023710 / audit Job 105468495136 の結果確認から継続。
- 最新確認時点: prepare/base-third/third/second は success、audit は step「441-cell joint ROI audit」in_progress。開始後数分で、直前成功Run 35298138766 のaudit所要約21分と比較して正常範囲。
- Run 35298138766 / audit Job 105456877514 / Artifact 10529736068 は修正後コードで success、AUDIT_OK=true。production cell 276/241/131、race SHA / ticket SHA完全一致。
- 35298138766 head 379190b... -> 最新Run head 28cc9dc... の差分は3号艇研究ファイルのみで、1号艇 joint ROI workflow/scriptは変更なし。
- これからやること: 最新Run完了を確認しつつ、成功Artifactの summary.csv / monthly.csv / result.json から raw best、Feb-Jun dev、Jul-Aug support、月別、平均的中オッズ、隣接plateau安定性を解析。sentinelは弱めない。9/17 result/payout UNREAD維持。自動production昇格はしない。


## AFTER — 441セル成功Artifact解析（Run 35298138766を先行解析）
- 直前成功Run 35298138766 / audit Job 105456877514 / Artifact 10529736068 を展開。AUDIT_OK=true、productionは 276R / HEAD241 / exact3 131 / ROI 104.3357%、race SHA=08eb... / ticket SHA=2163... 完全一致。
- raw best: HEAD=.790 / MASS=.425 / env_w=.05 / q=.70、77R / exact3 44 / ROI 129.0043%。Feb-Jun 69R ROI 130.87%、Jul-Aug 8R ROI 112.92%。sampleが小さいためraw best単独では昇格不可。
- 「devとsupport両方ROI>=100%」は441セル中7セルのみ。すべて HEAD=.790 かつ q=.70。
- その中で最大母数の安定候補: HEAD=.790 / MASS=.375 / env_w=.05 / q=.70。165R / HEAD140 (84.85%) / exact3 80 (48.48%) / ROI 112.5051%、平均的中オッズ約6.96倍。Feb-Jun 137R ROI 114.21%、Jul-Aug 28R ROI 104.17%。
- この候補の月別ROI: Feb 144.89 / Mar 99.23 / Apr 142.53 / May 83.10 / Jun 118.38 / Jul 112.96 / Aug 100.00%。productionは Jul 78.94 / Aug 87.06%。
- overallの1-step隣接plateauは候補周辺24セルすべてROI>=100.70%、平均108.11%。ただしJul-Aug supportだけを見ると周辺平均87.94%、100%超は24セル中1セルで、support安定性はまだ弱い。よってproduction自動昇格はしない。
- パラメータ傾向: HEADは.790が平均ROI最高、MASSは.425がraw ROI最高だが母数減、env_q=.70が平均ROI最高、env_wは.05がわずかに優位。
- 最新Run 35302023710 はまだaudit in_progress。前回head 379190b... -> 最新head 28cc9dc... で1号艇gridコード差分なし。ただしcache比較ではslim元データは完全一致、second cacheも完全一致だが、base-third/third予測値に最大約1e-3の微小な再学習差があり、一部順位も変動するため、最新Runのsentinel通過を最終確定条件とする。
- 9/17 result/payoutは未使用・UNREAD維持。
- 次の再開地点: Run 35302023710 / Job 105468495136 がcompletedになったら final artifactを回収し、上記数値との一致/差分を確認。sentinelが通れば robust候補(.790,.375,.05,.70)をproduction昇格せず、追加のsupport/paired監査候補として扱う。


## BEFORE — 2026-09-18 1号艇LIVE運用ルール変更
- ユーザー決定:
  - 基本候補 = HEAD >= .790 / opponent mass >= .375 / exhibition env_w=.05 / q=.70
  - 注目レース = HEAD >= .790 / opponent mass >= .425 / exhibition env_w=.05 / q=.70
- ticket=v320 HYBRID alpha=.70 3点、opponent core G2=.45/G3=1.00、v345 attackCore weightsは変更しない。
- 過去の正式v351 276R sentinelと履歴再現コードは凍結維持する。既存 PROFILE_NAME / PRODUCTION_EXPECTED_* を上書きして過去監査を壊さず、LIVE_OPERATION_* / WATCH_* を別定義して実運用のみ切り替える。
- 既存2026-09-18 daily cacheはp_head/opp_mass等の因果ベース値自体は再利用可能な設計にし、finalize/gateで新運用条件を適用する。
- 9/17 result/payout UNREAD、chronology guard維持。


## AFTER — 2026-09-18 1号艇LIVE運用ルール変更 完了
- ユーザー決定を実装:
  - BASIC: HEAD>=.790 / opponent mass>=.375 / env_w=.05 / q=.70
  - WATCH（注目）: HEAD>=.790 / opponent mass>=.425 / env_w=.05 / q=.70
- 過去正式v351の `HEAD_CUTOFF=.78 / MASS=.375 / env_w=.10 / q=.65` と 276/241/131 sentinelは履歴再現用として凍結維持。過去監査を壊していない。
- `onehead_production_profile.py` に `LIVE_OPERATION_*` と `WATCH_*` を追加。commit `0ccd14df777a19c8c2a272a7d7f5424e3a203f04`。
- `prepare_1head_v351_live_cache.py` はLIVE HEAD cutoff=.790を使用。commit `44c45f3e93a0fc495612d8f9140e82cf4e29af00`。
- `run_1head_v351_live_exhibition_gate.py` はLIVE env_w=.05 / q=.70を使用。commit `d6444a955d089c2e76dd8b24abeba13d3e0f66bf`。
- `run_1head_v351_live_finalize.py` はBASIC/WATCHを判定し、`attention_level` と `watch_pass` を出力。既存daily cache（historical base profile）も再利用可能。commit `07f45eb2db1456401158f98354831a420ecfe69c`。
- daily cache各race JSONへ `operating_pre_class = WATCH_PRE / BASIC_PRE / NON_CANDIDATE` を追加。commit `9b319603ccc11543570d607326084e8589acf4dd`。
- ticket=v320 HYBRID alpha=.70 3点、opponent core G2=.45/G3=1.00、attackCore weightsは変更なし。
- 既存2026-09-18 cache値を新しい事前閾値へ読み替えると:
  - WATCH_PRE: 平和島12R (.80106/.48589), びわこ7R (.80156/.42809), 福岡7R (.80293/.48411)
  - BASIC_PRE: 鳴門9R (.81101/.41645)
  - DROP（HEAD不足）: 丸亀11R (.78232/.44548)
  - ただし最終PASS/WATCHは新 q=.70 / env_w=.05 の展示gate通過が必要。旧q=.65での直前結果は新ルールの最終結果として流用しない。
- 9/17 result/payout UNREAD、chronology guard維持。
- Run 35302023710 / audit Job 105468495136 はこの記録時点もin_progress。これは旧production sentinel確認用Runであり、今回のLIVE運用変更とは分離する。
- BEFORE handoff commit: `cab1067583c19e50dd82d60cc528b7a933d0fd80`。


## BEFORE — 2026-09-18 3号艇「壁」リスク独立監査
- ユーザー指示: HEADモデルで3号艇の壁役が十分加味されているか、鳴門9Rのような「3が遅く4が攻める」ケースを踏まえて研究する。
- 現行v308には `attack23_*`、`v298_wall2_*_vs_attack34`、`v298_inner23_*_vs4` など間接的な内壁/攻撃特徴はあるが、**3号艇対4号艇を単独で評価する wall3 特徴は明示的にない**。v307 causal interactionも主に1対2。
- 今回は現行LIVE基本セル `HEAD=.790 / MASS=.375 / env_w=.05 / q=.70` を固定し、ticket v320 3点・opponentCore G2=.45/G3=1.00も固定。
- まず同一165R母集団に対して、3対4の事前壁特徴と展示後壁特徴を別々に付与し、
  1) 弱壁帯で実際に1頭率/3点ROIが悪化するか、
  2) targeted DROPで母数をなるべく維持しながらROI/頭率を改善できるか、
  3) Feb-Jun dev / Jul-Aug support / 月別で再現するか
  を監査する。
- 展示後候補は corrected ST / 展示 / 直線 / original avg の3号艇−4号艇差、特に `ST3 << ST4` と4号艇攻撃力の組合せを重視。鳴門9R型の専用 `WALL3_RISK` を想定。
- HEAD学習へ当日展示を直接混ぜない。展示はpost-ranking/final gateのみ。事前壁特徴を試す場合もPRE/strictly-prior情報のみ。
- 2026-09-17 result/payout UNREADを維持。9/18 LIVE結果も研究へ混ぜない。
- production/LIVE設定はこの監査では変更しない。良い結果が出ても自動昇格しない。


## BEFORE — 2026-09-18 びわこ7R 直前判定
- ユーザー指示: 「びわこ7Rの直前判定して」。
- 対象 race_code=`202609181107`。事前値は HEAD=.8015607255 / opponent mass=.4280898422 で、新運用では WATCH_PRE（HEAD>=.790, mass>=.425）。
- 現在時刻確認: 2026-09-18 12:59 JST。直前判定は既存LIVE workflow `.github/workflows/chat-live-1head-v351-request.yml` を使い、daily cache -> deadline -> exhibition probe -> 新LIVE gate（env_w=.05 / q=.70）-> finalize の順で実施する。
- 2026-09-18結果/払戻は使用しない。2026-09-17結果/払戻もUNREAD維持。
- 同時にv352 wall3 risk audit Run 35305095666を継続監視する。


## BEFORE — びわこ7R LIVE展示未公開の再試行修正
- 初回LIVE Run 35305252945 / Job 105476026971 は daily base resolve 成功後、`Deadline exhibition and v351 final` で failure。
- ログ上は13:00:14 JSTから4回probeを行い約1分後にexit 1。公式BOAT RACE びわこ7R直前情報でも13:02 JST時点で展示タイム/ST展示が未掲載。締切予定は13:17。
- 判定ロジックのDROPではなく展示未公開。結果/払戻は未使用。
- これから: LIVE workflowのartifact uploadを `if: always()` にし、deadline/window/exhibition_errorも失敗時に残す。その後、展示公開後に同raceを再発火して新LIVE gateで最終判定する。


## AFTER — 2026-09-18 びわこ7R 直前判定
- race_code=`202609181107`
- 初回 Run 35305252945 / Job 105476026971 は展示未公開でprobe 4回後 failure。公式でも13:02時点では展示未掲載。判定ロジックのDROPではない。
- failure時のdebug artifactを残すよう LIVE workflowを補強。commit `9bb93dbe3377a6b849e781f662ac5d7c80c197ba`。
- 再試行 commit `8d5ff6f245baf594ce06caed07c38dd41c3aab7f`。
- 再試行 Run `35305544461` / Job `105476877677` completed success。
- Artifact `10530454019` name `live-v351-final-202609181107`。
- deadline 13:17 JST / evaluated 13:05:45 JST / 約12.13分前。
- 現行LIVE最終: **PASS / WATCH**。
  - HEAD=.8015607255
  - opponent mass=.4280898422
  - head_exhibition_pass=true
  - BASIC threshold .790/.375, WATCH mass .425
  - env_w=.05 / q=.70
  - tickets: `1-3-5 / 1-3-2 / 1-2-3`
- 展示:
  - 展示タイム: 1=6.73, 2=6.79, 3=6.80, 4=6.71, 5=6.77, 6=6.82
  - ST展示: 1=-.04, 2=.02, 3=.12, 4=.02, 5=.09, 6=.04
  - corrected ST: 3=0.0 / 4=0.6
  - corrected EX: 3=.2 / 4=1.0
  - corrected straight: 3=.2 / 4=.4
  - corrected orig_avg: 3=.4667 / 4=.6
- v352 wall3候補式を参考にした**未昇格の診断値**では、
  - ST wall gap (3-4)=-.6
  - EX wall gap=-.8
  - straight wall gap=-.2
  - avg wall gap≈-.133
  - exhibition wall score≈-.47
  - attack4 score≈.63
  → 「3が弱く4が攻められる」鳴門9R型のwall3警戒ケースに該当し得る。これは現行判定をまだ上書きしない。v352歴史監査の結果待ち。
- result/payout used=false / chronology_guard=true。9/17結果払戻UNREAD維持。
- 次: v352 wall3 risk audit Run 35305095666 を最後まで確認し、こうしたケースを落とすと165R母集団のHEAD率/3点ROIが改善するかを判断する。


## AFTER — v352 3号艇wall3リスク独立監査
- Run `35305095666` / audit Job `105477488167` completed success。
- Artifact `10532605117` name `v352-wall3-risk-35305095666`。
- production sentinelは 276/241/131 + race SHA / ticket SHA 完全一致、AUDIT_OK=true。9月結果未読、production変更なし。
- BASIC baseline (.790/.375/.05/.70): 165R / HEAD 140=84.85% / exact3 80=48.48% / ROI 112.51%。
- WATCH baseline (.790/.425/.05/.70): 77R / HEAD 67=87.01% / exact3 44=57.14% / ROI 129.00%。
- 重要所見: corrected STの3-4差で「weak」帯は BASIC 40R / HEAD 35=87.5% と頭は高いのに exact3 15=37.5% / ROI 76.5%。WATCHでも weak 23R / HEAD 20=86.96% / exact3 11=47.83% / ROI 85.94%。
- 一方 strong帯は BASIC 41R ROI 163.17%、WATCH 14R ROI 229.29%。very_strongも高ROI。
- よって wall3 は単純な「1頭DROP」より、**1は残るが2/3着相手順位がズレる問題**として扱う価値が高い。
- 強いwall filterはROIを上げるが母数を大きく削り、BASICではHEAD率自体は改善しないものも多い。例 EX_ST_GAP_GT_0: 89R / HEAD82.02% / ROI131.01%。
- 母数80%以上維持の自動選定候補 EX_SCORE_GT_-0.30 は143R / ROI112.21%でbaseline112.51%を上回らず、単純DROPの昇格根拠は弱い。
- 結論: wall3はHEAD gateの追加より、相手選び（SECOND/THIRD rerank）研究を優先。

## BEFORE — v353 wall3連動 3点買い目rerank研究
- ユーザー指摘: 「こうなると買い目も変わるんじゃない？」
- 現行v351相手選びは opponent attackCore で各艇を個別にtiltするが、**3号艇と4号艇の相対壁関係を直接使っていない**。
- v352所見に基づき、現行BASIC/WATCH母集団とHEAD gateは固定したまま、3点買い目だけを研究する。
- 展示wall risk（主に corrected ST3-ST4、wall score、4号艇attack score）に応じて、4号艇のSECOND/THIRD確率を上げ、3号艇を下げるsoft rerankをgrid探索する。
- 3点固定、HEAD/mass/env gate固定、opponentCore既存補正を先に適用。その上にwall3 overlayを加える。
- 評価は all / Feb-Jun dev / Jul-Aug support / 月別、exact3、ROI、買い目変更数、baselineからのgain/lossを確認。
- 9月結果は読まない。production/LIVEは研究完了まで変更しない。


## v353 wall3連動3点買い目rerank — 実装/発火
- 実装commit `7b9a783a62c4381f08e8a478e89683d58702217d`: `run_v353_1head_wall3_ticket_rerank.py`。
- workflow commit `e01c97ad8736d80d4bd0f9fd90c5b8f5182e8469`: `.github/workflows/v353-1head-wall3-ticket-rerank.yml`。
- Run `35310326328` 発火済み。
- 既存 opponentCore 補正後に、wall3 riskに応じて4号艇をsoft boost / 3号艇をsoft demote。SECOND/THIRD別gamma、4号艇attackCore閾値、risk定義（ST / wall score / combo）をgrid探索。
- 3点固定。BASIC/WATCH gate固定。HEAD判定は変更しない。
- びわこ7Rのように「現行3点すべて4なし・3中心」なのに3<4展示となるケースが、wall-aware rerankでどう変わるかを研究対象とする。


## AFTER — v353 wall3連動3点買い目rerank 初回監査
- Run `35310326328` completed success / audit Job `105492805563` / Artifact `10534735142`。
- AUDIT_OK=true / September outcomes unread / production unchanged。
- BASIC baseline 165R / exact3 80 / ROI 112.505%。best BASICは ST / attack4>=.60 / g2=.5 / g3=2.0 だが、80的中のままROI 113.010%（+0.51pp）、変更19R。的中改善なし。
- WATCH baseline 77R / exact3 44 / ROI 129.004%。
- raw best WATCH: SCORE / attack4>=.60 / g2=3.0 / g3=.5
  - 77R / exact3 47 (+3) / ROI 141.818% (+12.81pp)
  - Feb-Jun 69R: 39 -> 42 hits / ROI 130.870% -> 145.169%
  - Jul-Aug 8R: 5 -> 5 hits / ROI 112.917%（不変）
  - 買い目変更12R。race-level比較では +hit 3R / -hit 0R。
  - gain例: 202604102412 actual 1-4-2、202604202408 actual 1-2-4、202606032008 actual 1-4-3 を新たに拾う。
- 近傍にも改善帯あり。SCORE/attack4=.60 では g2=1.5～3.0、g3=0～.5 に 46～47 hits / ROI約139.5～141.8%のplateauがある。
- 解釈: wall3補正はBASIC全体より、MASS>=.425のWATCHで相手rerankとして効いている可能性が高い。
- ただしsupport 8Rで増分0のため、raw bestを即LIVE昇格しない。

## BEFORE — v354 WATCH wall3 ticket robustness audit
- v353 raw bestの過学習を確認するため、WATCH専用候補群を月別・近傍・paired gain/lossで追加監査する。
- 主対象: SCORE / attack4>=.60、g2=1.5/2.0/3.0、g3=0/.5/1.0 とbaseline。
- 既存v353 Artifactのrace_predictionsを使用し、Feb-Augの各月について3点的中、払戻ROI、買い目変更数、gain/lossを再計算。
- devの月別最低値、改善月数、Jul/Aug個別、近傍plateauを確認。単一raw bestではなく運用に耐える簡潔な候補があるかを見る。
- 2026-09結果/払戻は読まない。production/LIVEは未変更。


## AFTER — v354 WATCH wall3 ticket robustness
- Run `35314731622` / Job `105503844822` completed success / Artifact `10533694328`。
- fixed dev-selected = `SCORE / attack4>=.60 / g2=3.0 / g3=.5`。
- WATCH 77R: 44 -> 47 hits、ROI 129.004% -> 141.818%、変更12R、gain 3 / loss 0。
- Feb-Jun: 39 -> 42 hits、ROI 130.870% -> 145.169%。
- Jul-Aug: 5 -> 5 hits、ROI 112.917%据え置き。
- fixed candidate月別:
  - Feb 3/5 ROI128.0%（baseline同じ）
  - Mar 4/6 ROI180.0%（同じ）
  - Apr 12/16 ROI181.04%（baseline10/16 ROI149.17%、+2 hits）
  - May 12/28 ROI82.26%（同じ）
  - Jun 11/14 ROI221.19%（baseline10/14 ROI187.14%、+1 hit）
  - Jul 0/3 ROI0%（同じ）
  - Aug 5/5 ROI180.67%（同じ）
- LOMO: 各dev月を外して残り4か月で候補選定。5か月すべてdelta_hits>=0、合計+1 hit。April holdoutのみ+1、他0。JuneはROI -3.33ppだがhit数不変。
- 近傍9候補でも g2=1.5～3.0 / g3=0～.5 に 46～47 hitsの改善plateau。単点だけの偶然ではない。
- ただしsupportは8Rしかなく増分0。production即昇格ではなく、次にBASIC全体へ「WATCHだけwall3 rerank / BASIC-onlyは従来」の合成監査を行う。

## BEFORE — v355 BASIC全母数維持 + WATCH-only wall3 ticket overlay
- 目的: BASIC 165Rを1Rも削らず、WATCH subset 77Rだけv354 fixed candidateの買い目rerankを適用。
- BASIC-only 88Rは現行3点のまま。WATCH 77Rだけ `SCORE / attack4>=.60 / g2=3.0 / g3=.5`。
- 期待上は WATCHでgain3/loss0のため、BASIC全体 exact3 80 -> 83、stake不変。これをartifactから再構成して厳密監査する。
- all / Feb-Jun / Jul-Aug / 月別ROI、買い目変更数、gain/loss、race identityを確認。
- レース数とHEAD gateは一切変更しない。9月結果未読、production/LIVEは監査完了まで変更しない。


## v355初回 failure — WATCH定義差を検出
- Run `35314956926` / Job `105504520058` failure。
- 原因: v353の独立WATCHセル77Rは MASS=.425母集団で exhibition thresholdを再較正した研究セル。一方、現行LIVEのWATCHは共通BASIC gate通過後に `opp_mass>=.425` をラベル付けするため、必ずBASIC subsetになる。
- artifact比較では独立WATCH77RとBASIC165Rの共通は73R、独立WATCH側に4R非共通。
- v355が `WATCH not subset of BASIC` でfailしたのは正しい検知。sentinel/条件を緩めて通さない。
- これから: v337 candidate baseの `opp_mass` を用いてBASIC165R内から **現行LIVE定義のWATCH subset** を再構成し、そのsubsetだけwall3 rerankを適用するようv355を修正。
- 必要cacheはv353 Runのprepare/second/base-third/third artifactsを利用。HEAD/exhibition gateは再計算せず、既存BASIC165R identityを固定してmassラベルだけ復元する。


## AFTER — v355 現行LIVE定義 WATCH-only wall3 overlay
- 軽量修正版 Run `35315563674` / Job `105506340941` completed success / Artifact `10535930081`。
- 現行LIVEと同じ定義で、BASIC165Rの共通展示gate通過後に `opp_mass>=.425` を付けると operational WATCH = **73R**。
- WATCH73Rだけ `SCORE / attack4>=.60 / g2=3.0 / g3=.5` のwall3相手rerankを適用、BASIC-onlyは従来3点のまま。
- 全165Rを1Rも削らず:
  - baseline 80/165 / return 55,690 / profit +6,190 / ROI 112.505%
  - overlay 83/165 / return 58,650 / profit +9,150 / ROI **118.485%**
  - +3 hits / return +2,960 / ROI +5.98pp
- Feb-Jun 137R: 66 -> 69 hits / ROI 114.209% -> **121.411%**。
- Jul-Aug 28R: 14 -> 14 hits / ROI **104.167%据え置き**。
- 買い目変更は10Rのみ、gain 3 / loss 0。
- gain:
  - 202604102412 actual 1-4-2
  - 202604202408 actual 1-2-4
  - 202606032008 actual 1-4-3
- 月別はApr 20->22 hits / ROI142.53->157.98%、Jun 16->17 / 118.38->132.83%。他月は完全据え置き。
- September outcomes unread / production unchanged / AUDIT_OK=true。
- 結論: レース数を減らさず、WATCHだけ相手買い目を壁3連動で補正する形が現時点で最も有望。ただしJul-Aug増分0のため、即production置換ではなくLIVE shadow出力で前向き確認する。

## BEFORE — LIVE wall3 shadow tickets
- 現行 `tickets` は変更しない。
- WATCH/PASS時だけ、v355候補 `SCORE / attack4>=.60 / SECOND g2=3.0 / THIRD g3=.5` を同じp2/pc + opponentCore補正後に追加適用し、`wall3_shadow_tickets` として併記する。
- riskは corrected 3-vs-4 の exhibition score（EX .20 / ST .40 / straight .25 / orig avg .15）で、attack4_score>=.60 かつ wall score<0 の時だけ発動。
- outputへ shadow profile / applied / risk / wall score / attack4 score / shadow tickets を追加。
- 既存status / attention_level / tickets / historical production sentinelは変更しない。
- 9/17および9/18結果払戻は使わない。


## AFTER — LIVE wall3 shadow tickets 実装・回帰完了
- shadow profile constants commit `ccd707022a1448bfb3df434306d4c1998f02d910`。
- LIVE finalizer shadow出力 commit `f402e3ee8c567893ccd0777115267084ad720188`。
- 既存 `tickets` / status / attention_level / WATCH判定は変更していない。WATCH/PASS時のみ研究用 `wall3_shadow_*` を追加。
- shadow設定:
  - profile `1HEAD_WATCH_WALL3_TICKET_SHADOW_V355_SCORE_A406_G2_300_G3_050`
  - attack4 >= .60
  - wall score weights EX=.20 / ST=.40 / straight=.25 / orig_avg=.15
  - risk=max(0,-wall_score)
  - SECOND g2=3.0 / THIRD g3=.5
- saved pre-race びわこ7Rで回帰:
  - regression script commit `6bd75dab70edc580f845629c8932df23d3c37c2c`
  - workflow commit `c2bf9ee0d89c5072def5428db46eca646dc8adec`
  - Run `35315958216` / Job `105507538521` success
  - Artifact `10535710397`
  - AUDIT_OK=true / result_or_payout_used=false
  - official ticketsは完全不変: `1-3-5 / 1-3-2 / 1-2-3`
  - wall3 shadow: `1-4-5 / 1-4-3 / 1-2-4`
  - wall_score=-.47 / attack4_score=.63 / risk=.47 / shadow applied=true
- したがって、今後のLIVE「判別して」では従来の正式3点に加えて、WATCHでwall3リスクが発火した場合はshadow3点も同じfinal JSONから取得可能。
- まだproduction ticket置換はしていない。forward evidenceを貯めるまでは research-only。
- September 9/17 outcomes UNREAD、9/18結果/払戻もこの研究・回帰では未使用。
- 次の再開地点: 次回WATCH LIVE判定で official tickets と wall3_shadow_tickets を併記し、前向きサンプルを蓄積。別研究としては operational WATCH73Rに対する周辺設定の追加paired監査/forward promotion条件設計が可能。


## BEFORE — 2026-09-18 WATCH wall3買い目 正式LIVE採用
- ユーザー明示指示: 「正式採用でいいよ」。
- 採用対象はv355で監査済みの **WATCH-only wall3 ticket rerank**。HEAD/BASIC/WATCHのレース選定条件は変更しない。
- 現行LIVE定義:
  - BASIC: HEAD>=.790 / mass>=.375 / env_w=.05 / q=.70
  - WATCH: BASIC通過かつ mass>=.425
- WATCH/PASSかつ wall3条件発火時:
  - attack4_score>=.60
  - wall score = .20*(EX3-EX4)+.40*(ST3-ST4)+.25*(straight3-straight4)+.15*(origavg3-origavg4)
  - risk=max(0,-wall_score)
  - SECOND: 4を exp(3.0*risk) boost、3を同量demote
  - THIRD: 4を exp(.5*risk) boost、3を同量demote
  - 3点HYBRID alpha=.70を再生成し、これを正式 `tickets` とする。
- BASIC-only、WATCHでもwall risk非発火時は従来3点を維持。
- v355監査: 165Rを削らず 80→83 exact3、ROI112.505→118.485%、gain3/loss0、Jul-Aug不変。
- historical production constants / 276R sentinelは凍結維持。今回の変更はLIVE ticket policy昇格のみ。
- 出力には旧3点も `pre_wall3_tickets` として残し、監査可能性を維持する。
- びわこ7R保存済み直前データで正式採用後の回帰を実施し、正式ticketsが `1-4-5 / 1-4-3 / 1-2-4` へ変わること、結果払戻未使用を確認する。


## AFTER — WATCH wall3買い目 正式LIVE採用完了
- ユーザー許可によりv355 wall3 ticket rerankを正式LIVE採用。
- profile commit `e875f00b7152019e425ab399dbb09a2763d06572`
  - `WALL3_LIVE_TICKET_PROFILE_NAME = 1HEAD_WATCH_WALL3_TICKET_V355_SCORE_A406_G2_300_G3_050`
  - `WALL3_LIVE_TICKET_PROMOTED = True`
  - historical production constants / 276R sentinel値は変更なし。
- finalizer commit `8d0bbdcd75803b6393136dcffc96d3a0fda08573`
  - WATCH/PASSかつwall3 risk発火時は補正後3点を正式 `tickets` に採用。
  - 補正前3点は `pre_wall3_tickets` に保持。
  - `ticket_profile`, `wall3_ticket_promoted`, `wall3_ticket_applied` を追加。
  - BASIC-onlyおよびwall3 risk非発火は従来買い目を維持。
- v356期待値更新 commit `18d63a8d14330738a95e90c55ae376e59feecc6c`。
  - 旧期待値のRun `35316655193` failureは正式採用でticketsが変わったため想定どおり。
  - 更新後 Run `35316692936` / Job `105509780027` success / Artifact `10534928066`。
  - びわこ7R保存済み直前入力:
    - pre-wall3: `1-3-5 / 1-3-2 / 1-2-3`
    - 正式tickets: **`1-4-5 / 1-4-3 / 1-2-4`**
    - wall3 applied=true / risk=.47 / result_or_payout_used=false / AUDIT_OK=true。
- 最終二重回帰:
  - script commit `31add391786b95a2e338010e4acae12f791455e4`
  - workflow commit `992cc0a6b3703e8447dc9d19ea8116e93bb90dd7`
  - Run `35316919281` / Job `105510479216` success / Artifact `10534987269`
  - `historical_production_constants_frozen=true`, `AUDIT_OK=true`
  - びわこ7R WATCH: wall3適用、正式3点=`1-4-5 / 1-4-3 / 1-2-4`
  - 鳴門9R BASIC: wall3非適用、従来3点=`1-2-5 / 1-2-4 / 1-5-2` を維持
  - September outcomes unread / result_or_payout_used=false。
- 採用根拠 v355:
  - BASIC全165R維持
  - exact3 80→83
  - ROI 112.505%→118.485%
  - gain3 / loss0
  - Jul-Aug 14/28・ROI104.167%据え置き。
- 今後のLIVE「判別して」では、WATCHでwall3条件が発火した場合は補正後3点が**正式買い目**として返る。shadow扱いではない。
- 次の再開地点: 次回LIVE判定から正式wall3 ticket profileを通常運用。必要ならforward実績を別途蓄積して再監査。


## BEFORE — v358 展示後・汎用買い目rerank研究
- ユーザー指摘: 「展示後に買い目変わるパターンこれ以外に結構ありそう」。
- 現状:
  - v351 opponentCore は各艇の展示強弱を個別tiltする。
  - v355正式採用wall3は 3号艇内壁 vs 4号艇攻撃 の相対関係だけを追加補正する。
- 研究仮説: 買い目変更に効くのはwall3固有ではなく、**隣接コースの内壁/外攻め関係全般**と、場合によっては全艇の展示総合順位の追加rerank。
- HEAD/BASIC/WATCH選定は固定、3点固定、レース数は一切減らさない。既存正式wall3も比較対象として残す。
- 研究overlay:
  1) GLOBAL: corrected EX/ST/straight/orig_avg の総合scoreを全2〜6号艇でcenterし、SECOND/THIRDを追加tilt。
  2) ADJACENT: (2,3),(3,4),(4,5),(5,6) の各隣接pairで、外艇scoreが内艇を上回り、外艇attack scoreが閾値以上なら outer boost / inner demote。
  3) ADJACENT_ST: 上記をST差中心で実施。
  4) GLOBAL+ADJACENT: 個別総合順位と隣接圧力を合成。
- 評価:
  - BASIC165R全件
  - operational WATCH subset（BASIC通過後mass>=.425）
  - all / Feb-Jun / Jul-Aug / 月別
  - exact3、ROI、変更R、gain/loss
  - 現正式v355との差分
  - どのadjacent pairが何R変更を起こしたか
- 過学習対策: 単一点raw bestではなく、近傍plateau・月別・LOMOを後段で監査。
- 2026-09結果/払戻は読まない。現正式LIVE wall3はこの研究中も維持し、自動置換しない。


## AFTER — v358 汎用展示後rerank 初回有効結果
- チャット表示がフリーズしたがGitHub作業は継続。Run `35317736874` が先に completed success。
- Artifact `10536741516` name `v358-generic-exhibition-rerank-35317736874`。
- 基準は正式採用済み wall3 ticket profile:
  - 165R / HEAD140 / exact3 **83** / ROI **118.485%** / profit +9,150円。
- dev選択best:
  - family=`EXTRA_ADJ`
  - scope=`WATCH_ONLY`
  - attack_min=.60（.50も同成績）
  - SECOND g2=.50 / THIRD g3=.50
  - 165R維持 / exact3 **84** / ROI **120.848%** / profit +10,320円
  - Feb-Jun 137R: 69 -> **70 hits** / ROI 121.411% -> **124.258%**
  - Jul-Aug 28R: 14 hits / ROI 104.167% **完全据え置き**
  - 買い目変更12R / gain 1 / loss 0
- gainは `202605141610`, actual `1-2-6`:
  - 現正式: `1-2-3 / 1-2-4 / 1-3-2`
  - generic adjacent: `1-2-3 / 1-2-6 / 1-3-2`
- 変更trigger集計（重複あり）: 2>3=5R / 4>5=3R / 5>6=5R。
- 改善はあるが +1 hit のみで、現wall3ほど強い差ではない。単純GLOBAL全艇tiltはgain/lossが相殺しやすく、現時点では隣接pair補正の方が有望。
- 一部ALL_BASIC設定はsupportで改善するが、supportを選定に使わないため採用根拠にはしない。
- September outcomes unread / production unchanged / AUDIT_OK=true。
- 最新並列cache保存版 Run `35318855846` は同一ロジックの速度改善・再現確認用として継続中。

## BEFORE — v359 汎用adjacent rerank robustness
- v358の +1 hit / loss0 が偶然か確認する。
- 最新cache保存版artifactが出たら全config race predictionsを使い、
  - 月別
  - dev LOMO
  - attack_min .50/.60近傍
  - g2=.5周辺 / g3=.25/.5周辺
  - pair別寄与
  - gain/loss
を監査する。
- Jul-Augはsupportのみで選定に使わない。
- 正式wall3 profileは維持し、汎用adjacentは自動昇格しない。


## AFTER — 2026-09-18 平和島12R LIVE直前判定
- ユーザー指示: 「1号艇モデルの平和島12Rの直前判定して」。
- race_code=`202609180412`。LIVE request更新commit `864aabada1647b194a9e0232314ef3b99060af1d`。
- chat-live Run `35319697557` completed success / Artifact `10536382992` name `live-v351-final-202609180412`。
- 締切 16:40 JST / evaluated 16:31:02 JST / 約9.46分前。
- 事前値: HEAD=.8010601806 / opponent mass=.4858903563。現行LIVE BASIC(.790/.375/.05/.70)およびWATCH mass(.425)の事前条件は満たす。
- 展示取得: EX 1=6.86,2=6.79,3=6.74,4=6.72,5=6.78,6=6.67。ST展示 1=.08,2=.12,3=.03,4=.06,5=.25,6=.23。
- original: 1号艇 一周37.20 / まわり足5.50 / 直線7.40。
- venue-aware exhibition gate: `head_exhibition_pass=false` / attack_core=.26 / threshold=.5010533623。
- 最終判定: **DROP / 見送り**。tickets=[]。WATCH用wall3 ticket補正は、展示gate DROPのため非適用。
- result_or_payout_used=false / chronology_guard=true。2026-09-18結果払戻未使用、2026-09-17結果払戻UNREAD維持。
- 補足: このチャットではLIVE発火を先に行い、作業前handoff追記を先行できなかった。未実施を実施済みとして記録しない。


## BEFORE — v360 展示後rerank 母集団拡大研究
- ユーザー指示: 「母集団が少なすぎるから165Rから拡大してやってみれば」。
- 方針: 現正式LIVEの165Rは変更せず、研究母集団だけ段階的に拡大して展示後rerankの一般性を検証する。
- 目的: wall3 / adjacent補正が165R固有の偶然ではなく、より広い1頭候補でも再現するかを見る。
- 比較候補:
  1) 現BASIC 165R（基準）
  2) HEAD>=.790でmass条件を緩めた拡大母集団
  3) HEAD>=.780系のより広い母集団
  4) formal production 276R identity相当
- 各母集団でレース選定は固定し、3点固定。展示後に買い目だけrerankする。
- 評価: exact3 / ROI / gain-loss / 月別 / Feb-Jun / Jul-Aug / pair別寄与 / 変更R。
- 選定はdevのみ、Jul-Augはsupport扱い。2026-09結果/払戻は読まない。
- 現正式wall3 ticket profileは維持し、この拡大研究から自動昇格しない。


## v360高速版 初回failureと修正開始
- Run `35321221764` / Job `105523920554` failure。
- 原因: preview prefetch高速化で `v337.PRELOAD` を参照したが、`run_v337_1head_head_cutoff_volume as v337` のimport漏れ。
- データ/研究ロジック/母集団条件の問題ではなくNameError。rerunせずコード修正してfresh Runを発火する。
- 修正はimport追加のみ。研究条件は 165/236/269/313/276R の5母集団比較を維持。


## v360 拡大母集団Run failure — 評価部dict参照バグ
- Run `35320996193` failure / Artifact `10537748051`。
- Run `35321326920` failure / Artifact `10537094730`。
- 共通原因: `baseline_rows()` はrace rowをdict化して返すが、`evaluate()` 内で `rr.actual_combo`, `rr.base_tickets` 等の属性参照をしていたため `AttributeError: 'dict' object has no attribute 'actual_combo'`。
- 重要: 5母集団の選定・展示特徴再構築・opponentCore構築までは通過しており、母集団定義やデータ取得のfailureではない。
- 修正方針: `rr['...']` へ統一。研究条件・母集団・パラメータは一切変更しない。fresh Runで再監査。


## v360 修正版2回目failure — dict属性参照の残存2箇所
- Run `35323403108` / Job `105530825105` failure / Artifact `10538226681`。
- 前回の `rr.actual_combo` は修正され、その先へ進行。
- 新しいfailure: `evaluate()` の出力recordで `rr.base_tickets`（および同じ行群に `rr.opp_mass`）が残っていた。
- 母集団選定・展示再構築・opponent map構築は再び正常通過。
- 今回は `rr.` 属性参照を全件検索して、Series用 `rr.get(...)` 以外をゼロ化する。
- 同時に重い前半完了時点の `prepared_rows.pkl` をartifactへ保存。以後後半failureなら重い前半を再計算せずresume可能にする。


## AFTER — v360 母集団拡大 展示後rerank監査
- 最終成功 Run `35324836153` / Job `105535377393` / Artifact `10539401122` / head `16cbc8f91f451091c27a2d404a681586beac6af0`。
- Artifactに `prepared_rows.pkl`, `expanded_exhibition_features.csv`, `race_predictions.csv`, `summary.csv`, `monthly.csv`, `generalization.csv`, `result.json` を保存。以後は重い展示再取得なしで追加研究可能。
- 母集団baseline:
  - LIVE165: 165R / 80 hit / ROI112.51%
  - H078_M375: 236R / 113 hit / ROI107.75%
  - H0775_M375: 269R / 128 hit / ROI106.59%
  - H0775_M350: 313R / 142 hit / ROI102.31%
  - PROD276: 276R / 131 hit / ROI104.34%
- fixed generic rerank (.60 / g2=.5 / g3=.5) generalization:
  - `5>6 / MASS425`: 全5母集団で +1 hit / loss0、mean ROI +1.63pp。ただしgainは全母集団共通の同一race `202605141610` (actual 1-2-6) 1件で、独立再現ではない。
  - `4>5 / ALL`: 全5母集団で +1 hit / loss0、mean ROI +1.79pp。ただしgainは全母集団共通の `202608030402` (actual 1-3-5) 1件で、Jul-Aug support由来。
  - `3>4 / MASS425` のgeneric弱補正は不安定/悪化。これは正式wall3 (g2=3.0 / g3=.5 / WATCH-only) と設定が異なるので、正式wall3否定ではない。
- 重複しない追加帯:
  - LIVE165外の +71R: 5>6 MASS425は±0
  - 次の +33R: ±0
  - さらにmass .350-.375の +44R: 5>6 MASS425は±0
  - ただし `5>6 / ALL` はこの外側44Rで新規gain `202607091004` actual 1-2-6 を1件追加。opp_mass=.373437。
- `5>6 / ALL` 313R全体では gain2 / loss1。lossは `202603120604` actual 1-2-5、gainは `202605141610` と `202607091004`。
- 結論: 母集団拡大により、5→6補正は高mass限定だけでなく低mass側にも別gainが存在することを確認。ただし固定設定ではlossも出るので閾値/強度の再探索が必要。
- September outcomes unread / production unchanged / AUDIT_OK=true。

## BEFORE — v361 313R expanded adjacent grid
- v360成功artifactの `prepared_rows.pkl` を再利用し、展示再構築・モデル再学習は行わない。
- 313R母集団を主研究面とし、165/236/269/276Rにも同じ選定候補を横展開して一般性を確認。
- 主対象: `5>6`, `4>5`。比較で `2>3`, generic `3>4` も保持。
- grid候補:
  - attack outer score min .40/.50/.60/.70/.80
  - pair score gap min 0/.10/.20/.30
  - mass scope ALL/.350/.375/.400/.425/.450
  - SECOND gamma .25/.5/1.0/1.5/2.0/3.0
  - THIRD gamma .25/.5/1.0/1.5
- 選定はFeb-Jun devのみ。Jul-Aug supportは選定に使わない。
- 目的は unique gainを増やしつつ lossを抑え、特に165R外の追加148Rでも新規gainが出る設定を探す。
- 現正式wall3/LIVE設定は変更しない。2026-09結果払戻は読まない。


## v361 初回failure — payout union不足
- Run `35327996597` / Job `105545490129` failure。
- grid本体は313R DEV探索まで通過。後段で全universeへ同一bestを横展開する際、payout辞書を313Rだけから作っていたため、PROD276側にのみ存在する `202602250509` で KeyError。
- 修正: payout/cache対象を5母集団のrace unionへ拡張。研究パラメータ・選定条件は変更しない。
- なおprepared rowsを使った独立ローカルexact3再現では有望候補:
  - pair 5>6 / basis ST
  - outer score>=.60
  - ST gap>=.30（.40も同じplateau）
  - mass制限なし
  - SECOND g2=0 / THIRD g3=.75
  - 313R: 142 -> 147 hits / gain5 / loss0
  - DEV: 116 -> 118 / gain2 / loss0
  - SUPPORT: 26 -> 29 / gain3 / loss0
  - 165R: 80 -> 84、236R:113->117、269R:128->132、276R:131->136
- GitHub正式監査でROI/LOMOを確定するまでproduction変更なし。


## AFTER — v361 expanded adjacent grid
- 修正版 Run `35328290547` / Job `105546435242` completed success / Artifact `10539299417` / head `502be1be4b0e693ba2a8cfd78300bce7cb06b653`。
- payout prefetch 166日すべて取得、September outcomes unread、AUDIT_OK=true。
- 313R baseline: 142 hit / return 96,070 / ROI 102.31%。
- DEV-only正式選択 best:
  - pair=`5>6`
  - basis=`ST`
  - 6号艇 exhibition composite score >= .60
  - ST6-ST5 >= .50
  - mass >= .375
  - SECOND g2=0 / THIRD g3=.75
- strict best:
  - DEV 247R: 116 -> **118** / return 79,120 -> 82,420 / ROI 106.77% -> **111.23%** / gain2 loss0
  - SUPPORT 66R: 26 -> **27** / return 16,950 -> 17,810 / ROI85.61% -> **89.95%** / gain1 loss0
  - ALL313: 142 -> **145** / return 96,070 -> 100,230 / ROI102.31% -> **106.74%** / gain3 loss0
- 同一strictを各母集団へ横展開:
  - 165R: 80->83 / ROI112.51->120.91 / gain3 loss0
  - 236R: 113->116 / ROI107.75->113.63 / gain3 loss0
  - 269R: 128->131 / ROI106.59->111.75 / gain3 loss0
  - 313R: 142->145 / ROI102.31->106.74 / gain3 loss0
  - PROD276: 131->135 / ROI104.34->110.25 / gain4 loss0
- LOMO: Feb-Jun 5 holdout月すべて delta_hits>=0、合計+1。Jun holdoutのみ+1、他0。
- dev上ではstrictと同率のplateauが広い。
  - mass制限なし / ST gap>=.50: DEVは同じ118 hit/ROI111.23%、support +2、313R 146 hit / ROI108.56% / gain4 loss0。
  - mass制限なし / ST gap>=.30 or .40: DEVは同じ118 hit/ROI111.23%、support 26->29 / ROI103.08%、313R 142->147 / ROI**109.51%** / gain5 loss0。
- broad plateauの5 unique gains（313R）: `202605141610`, `202606131912` (DEV) + `202607080801`, `202607091004`, `202608112101` (SUPPORT)。loss0。
- 注意: broad設定の選択にsupportを使ってはいないが、strictとのdev同率plateau内のどれを採るかはdevだけでは一意に決まらない。supportで広い側が良く見えるため、即昇格ではなくcombined監査を実施する。

## BEFORE — v362 formal wall3 + 5>6 ST combined overlay audit
- 現正式LIVE165 wall3 baseline（83/165、ROI118.485%、gain3/loss0）をprepared rowsから完全再現する。
- その上に5>6 STを順次適用し、相互干渉を監査する。
- 比較:
  1) STRICT: score6>=.60 / ST6-ST5>=.50 / mass>=.375 / g2=0 / g3=.75
  2) BROAD50: score6>=.60 / ST gap>=.50 / mass制限なし / g2=0 / g3=.75
  3) BROAD40: score6>=.60 / ST gap>=.40 / mass制限なし / g2=0 / g3=.75
- LIVE165について official wall3 baselineとの差分 exact3/ROI/gain/loss/月別/変更raceを算出。
- 5→6の拡大母集団単独成績はv361を根拠にし、combinedのproduction候補評価は現LIVE165に限定する。
- 9月結果払戻は読まない。productionはcombined監査完了まで変更しない。


## AFTER — v362 formal wall3 + 5>6 ST combined audit
- Run `35328786125` / Job `105548027749` completed success / Artifact `10540352040` / head `e3002bbc7455612d036b7dcc1ce5f84ea8d5bfa9`。
- official wall3 sentinelをprepared rowsから完全再現:
  - 165R / 83 hit / return 58,650 / profit +9,150 / ROI **118.485%**
  - DEV 69/137 ROI121.41%、SUPPORT 14/28 ROI104.17%。
- wall3後に5>6 STを追加:
  - STRICT (score6>=.60, ST6-ST5>=.50, mass>=.375, g2=0,g3=.75)
    - 86/165 / return 62,810 / profit +13,310 / ROI **126.889%**
    - wall3比 +3 hits / +8.40pp / gain3 loss0
    - DEV 71/137 ROI129.44%、SUPPORT 15/28 ROI114.40%
  - BROAD50 (mass制限なし) はLIVE165自体がmass>=.375なのでSTRICTと完全同一。
  - BROAD40 (score6>=.60, ST gap>=.40, mass制限なし, g2=0,g3=.75)
    - **87/165** / return **63,700** / profit **+14,200** / ROI **128.687%**
    - wall3比 **+4 hits / +10.20pp / gain4 loss0**
    - DEV 71/137 / return53,200 / ROI129.44%（wall3比+2 hit）
    - SUPPORT 16/28 / return10,500 / ROI**125.00%**（wall3比+2 hit）
- BROAD40の追加gain（wall3比）:
  - `202605141610` actual 1-2-6, ST gap .8
  - `202606131912` actual 1-2-6, ST gap .6
  - `202607080801` actual 1-3-6, ST gap .4
  - `202608112101` actual 1-2-6, ST gap 1.0
  - loss 0。
- 月別: Feb/Mar/Apr変更なし、May +1、Jun +1、Jul +1、Aug +1。改善月がdevとsupportに分散。
- v361 broad plateauでも ST gap .30/.40 はDEV完全同一、313R 147/313・ROI109.51%・gain5/loss0。単一点cutoff依存ではない。
- ただしBROAD40をsupport結果を見て選ぶと選定リークになるため、現時点ではproduction自動昇格しない。

## BEFORE — 5>6 ST LIVE shadow導入
- 現正式 `tickets`（wall3込み）は変更しない。
- PASSレースに対し、wall3適用後のp2/pcへ5>6 ST BROAD40を追加した `five6_shadow_tickets` を研究用に出力する。
- 条件: score6>=.60 / corrected ST6-ST5>=.40 / SECOND g2=0 / THIRD g3=.75。
- 現LIVE PASSはmass>=.375なので別mass gateは不要。
- 出力に profile / eligible / applied / st_gap / score6 / shadow tickets / research_only を追加。
- 既存wall3正式tickets、HEAD/BASIC/WATCH判定、historical production sentinelは変更しない。
- September outcomesは読まない。


## AFTER — 5>6 ST LIVE shadow導入完了
- profile commit `8671e6d57c5cb2249e5db3c50c6a55e23249a609`
  - `FIVE6_SHADOW_PROFILE_NAME = 1HEAD_5TO6_ST_SHADOW_V361_SCORE6_060_STGAP040_G2_000_G3_075`
  - score6>=.60 / ST6-ST5>=.40 / SECOND g2=0 / THIRD g3=.75。
- finalizer commit `63d5023ca1e4b52063dfdb1fc4aa698970d14084`
  - official wall3適用後のp2/pcを再構成し、その後に5>6 shadowを適用。
  - 新規出力: `five6_shadow_profile`, `five6_shadow_eligible`, `five6_shadow_applied`, `five6_shadow_score6`, `five6_shadow_st_gap_6_minus_5`, `five6_shadow_tickets`, `five6_shadow_research_only=true`。
  - 正式 `tickets` / `ticket_profile` は変更なし。
- 既存v356 LIVE回帰:
  - Run `35329105346` / Job `105549046425` success / Artifact `10540292732`。
  - びわこ7R保存済み直前入力で official tickets は引き続き `1-4-5 / 1-4-3 / 1-2-4`。
  - five6 shadowは score6=.49 / ST6-ST5=.20 のため applied=false、shadow ticketsも正式3点と同じ。
  - result_or_payout_used=false / AUDIT_OK=true。
- v362 combined監査の有望値:
  - official wall3 83/165 ROI118.485%
  - +5>6 STRICT -> 86/165 ROI126.889%, gain3/loss0
  - +5>6 BROAD40 -> 87/165 ROI128.687%, gain4/loss0
- 現時点で5>6はshadowのみ。正式production/LIVE ticketsへは未昇格。
- 今後の「判別して」では、正式wall3 ticketsに加え、5>6 shadowが発火した場合はshadow3点も確認可能。
- September outcomes unread / production historical sentinel unchanged。


## BEFORE — v363 5>6 ST 近傍robustness / 正式採用判定
- ユーザー指示: 「お願いします」。
- 目的: v361/v362で有望だった5→6 ST補正を正式採用前に近傍監査し、単一点cutoff依存・support選定依存を排除する。
- prepared source: v360 Artifact `10539401122` の `prepared_rows.pkl`。展示再取得/再学習なし。
- 基準:
  - expanded 313R baseline
  - current LIVE165 official wall3 baseline = 83/165, return 58,650, ROI118.485%
- 近傍grid:
  - score6 min .50/.55/.60/.65/.70
  - ST6-ST5 min .30/.35/.40/.45/.50/.55
  - THIRD gamma .50/.625/.75/.875/1.00
  - SECOND gamma 0/.25
  - mass min .35/.375/.40/.425（313R用。LIVE165は既に>=.375）
- 選定はFeb-Jun DEVのみ。Jul-Aug SUPPORTは選定に使わない。
- 評価:
  1) 313R dev/all/support
  2) current LIVE165でwall3適用後に重ねたcombined成績
  3) 月別
  4) DEV LOMO
  5) 近傍plateau（同等hit/loss0の設定数と閾値幅）
  6) disjoint bandsで165R外に独立gainが残るか
- promotion候補条件: DEV loss=0、SUPPORT loss=0、LOMO全月非悪化、近傍plateauあり、combined LIVE165でwall3比改善。
- 2026-09結果/払戻は読まない。現正式wall3は維持、v363完了までは5→6正式昇格しない。
