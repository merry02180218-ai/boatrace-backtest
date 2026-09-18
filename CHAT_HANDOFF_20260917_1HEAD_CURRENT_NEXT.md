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


## v363 初回failure — payout union不足
- Run `35331971241` / Job `105558128284` failure。
- 原因: payout辞書を313Rだけから作成したが、disjoint band評価で別universe由来の `202607071001` を参照し KeyError。
- DEV grid / plateau選定部分は通過済み。研究ロジック自体のfailureではない。
- 修正: payout/cache対象を `LIVE165 / H078_M375 / H0775_M375 / H0775_M350` のrace unionへ拡張。
- grid・選定・LOMO条件は一切変更しない。fresh Runで再監査。


## AFTER — v363 5>6 ST 近傍robustness
- 修正版 Run `35332130748` / Job `105558625364` completed success / Artifact `10541541621` / head `ab60e13d6063ac785fb7a61ff35f9da1d407fe35`。
- grid 1,200 cells / AUDIT_OK=true / September outcomes unread / production unchanged。
- DEV zero-lossで最大改善は +2 hits。
- DEV plateauは **126 cells** と広い:
  - score6 min: .55〜.65
  - ST6-ST5 min: .30〜.55
  - SECOND g2: 0〜.25
  - THIRD g3: .75〜.875
  - mass min: .35〜.375
- raw DEV best:
  - score6>=.65 / ST gap>=.45 / g2=0 / g3=.75 / mass>=.375
  - DEV 116->118 / ROI106.77->111.23 / gain2 loss0。
- plateau center:
  - score6>=.60 / ST gap>=.45 / g2=.25 / g3=.75 / mass>=.375
  - DEV 116->118 / gain2 loss0
  - SUPPORT 26->27 / ROI85.61->89.95 / gain1 loss0
  - ALL313 142->145 / ROI102.31->106.74 / gain3 loss0。
- current formal wall3 + plateau center on LIVE165:
  - 83->**86** / return 58,650->62,810 / ROI118.485->**126.889%**
  - gain3 / loss0。
- DEV LOMO再選定では **5 holdout月すべて同じcore設定**
  - score6=.60 / ST gap=.40 / g2=0 / g3=.75 / mass=.375
  - これは現在のLIVE 5>6 shadow coreと一致。
  - Feb/Mar/Apr delta0、May +1、Jun +1、全月loss0。
- 近傍162 cells:
  - net delta_hits >=0 は **100%**
  - loss=0 は 150/162 = **92.6%**
  - dev ROI range 107.61〜111.23%、mean 109.58%。
- 現在のshadow設定 `.60/.40/g2=0/g3=.75` はDEV plateau内。313Rでmass=.35まで許す既存v361 broad40では 142->147 / ROI109.51 / gain5 loss0、うち `202607091004` はLIVE165外の独立gain。
- ただしv363のDEV-only plateau center（mass=.375）を固定したdisjoint band監査では:
  - LIVE165 +3
  - +71R: ±0
  - +33R: ±0
  - +45R: ±0
  よって自己設定した `outer_bands_have_gain` 条件のみfalse。
- promotion_checks:
  - DEV loss0=true
  - SUPPORT loss0=true
  - SUPPORT nonnegative=true
  - LIVE165 loss0=true / improves=true
  - LOMO all nonnegative=true
  - plateau>=10=true
  - neighborhood nonnegative share=1.0
  - outer_bands_have_gain=false
  - all_conditions_pass=false。
- 解釈:
  - **パラメータ安定性は強い**。current shadow coreはLOMOでも毎回再選択される。
  - ただし現LIVE gate外の追加高mass母集団では新規gainが増えておらず、拡大母集団での独立再現性はまだ限定的。
  - したがって5>6は現時点でshadow維持。正式昇格は未実施。
- 次の再開地点:
  1) forward LIVEで5>6 shadow発火例を蓄積、または
  2) current shadowを固定した追加独立期間/非重複母集団監査。


## BEFORE — 2026-09-18 5>6 ST買い目 正式LIVE採用
- ユーザー明示指示: 「正式採用でいいよ」。
- 採用対象: current wall3正式補正の後段に、5>6 ST補正を正式適用。
- 採用core:
  - score6 >= .60
  - corrected ST6-ST5 >= .40
  - SECOND g2=0
  - THIRD g3=.75
  - 現LIVE PASSはmass>=.375なので別mass gateなし。
- v363 robustness:
  - 1,200 cells、DEV plateau 126 cells
  - 近傍162 cellsのdelta_hits>=0は100%、loss0は92.6%
  - LOMO 5/5月でcore `.60/.40/g2=0/g3=.75/mass=.375` を再選択、全月非悪化。
- v362 current LIVE165 combined:
  - wall3 only 83/165 / return58,650 / ROI118.485%
  - wall3 + 5>6 core 87/165 / return63,700 / ROI128.687%
  - gain4 / loss0
  - DEV +2、SUPPORT +2
- 正式採用後も `pre_five6_tickets` としてwall3後・5>6前の3点を保持し監査可能にする。
- historical production 276R sentinel / HEAD gate / BASIC/WATCH gateは変更しない。
- 2026-09結果/払戻は読まない。保存済みcausal LIVE入力とhistorical prepared causal rowsで回帰する。
- ROI定義確認: 各3点100円、1R300円。的中時に実3連単払戻100円分を加算し、総払戻/総投資。数学的な合成オッズを事前計算した値ではなく、3点買いポートフォリオの実回収率。


## AFTER — 5>6 ST買い目 正式LIVE採用完了
- ユーザー明示許可により5>6 ST rerankを正式LIVE採用。
- profile commit `f8fb309fc9df6c27bf3347ae6c46d4ffefa95023`
  - `FIVE6_LIVE_TICKET_PROFILE_NAME = 1HEAD_5TO6_ST_TICKET_V363_SCORE6_060_STGAP040_G2_000_G3_075`
  - `FIVE6_LIVE_TICKET_PROMOTED = True`
  - backward alias `FIVE6_SHADOW_PROFILE_NAME` は同profileへ。
- finalizer commit `2d95939fdcdb8051b5eb542d35e9de943984c349`
  - 現正式wall3の後段で5>6条件が発火した時、5>6補正後3点を正式 `tickets` に採用。
  - wall3後・5>6前の買い目を `pre_five6_tickets` に保持。
  - `five6_ticket_promoted`, `five6_ticket_applied` を追加。
  - ticket_profileは5>6発火時 `1HEAD_5TO6_ST_TICKET_V363_SCORE6_060_STGAP040_G2_000_G3_075`。
- 非発火回帰:
  - v356 Run `35333715902` completed success on finalizer commit。
  - びわこ7Rのformal wall3 ticketsは5>6非発火のため従来のまま。
- 発火回帰:
  - v364 script commit `60f1fe919b0defae449cfcad2243a51936805f2d`
  - workflow commit `8d438994cc429aad51c8d2a6d9bd6fb34ebb1b58`
  - Run `35333921236` / Job `105564287024` success / Artifact `10541834290`
  - causal historical row `202605141610` で、
    - pre-five6: `1-2-3 / 1-2-4 / 1-3-2`
    - formal tickets: **`1-2-3 / 1-2-6 / 1-3-2`**
    - score6=.68 / ST6-ST5=.80
    - five6_ticket_applied=true
    - result_or_payout_used=false / September outcomes unread / AUDIT_OK=true。
- 採用根拠:
  - v362 current LIVE165: wall3 only 83/165 ROI118.485% -> wall3+5>6 87/165 ROI128.687%、gain4/loss0。
  - v363: 1200-cell robustness / plateau126 cells / LOMO全5月非悪化 / current core再選択 / 近傍delta_hits>=0 100%。
- historical production 276R sentinel / HEAD/BASIC/WATCH gateは変更なし。
- ROI定義:
  - 3点各100円、1R=300円 stake。
  - 選択3点のどれかが的中した場合、その3連単の公式100円払戻をreturnへ加算。
  - `ROI = total return / total stake`。
  - したがって数学的な「合成オッズ」そのものではなく、3点均等買いポートフォリオの実現回収率。呼び方として「3点合成ROI」は可だが、合成オッズとは区別する。
- 今後のLIVE「判別して」ではwall3→5>6 STの順に正式rerankし、最終 `tickets` を正式買い目として返す。


## BEFORE — v365 exact3 hit-rate push after formal wall3 + 5>6
- ユーザー要望: 「もう少し3連単的中率は上げたい」。
- 現正式LIVE165基準:
  - 165R
  - exact3 87/165 = **52.73%**
  - 3点買いROI **128.687%**
  - wall3 + 5>6 ST正式採用済み。
- 目標: まず3点固定のまま **91〜92/165（55%前後）** を狙う。ROIは大きく崩さない。
- v365方針:
  1) current formal wall3→5>6を完全再現してbaseline化。
  2) その後段にまだ正式化していない展示後rerankを追加:
     - 2>3
     - 4>5
     - 必要に応じて両方のcombo
  3) basisは corrected SCORE / ST / COMBO を比較。
  4) score outer threshold / pair gap / THIRD gamma / optional SECOND gamma をgrid。
  5) 165R exact3最大化を主目的にするが、DEV選定・SUPPORT確認・313R拡大母集団のgeneralizationも必須。
- selection discipline:
  - Feb-Jun DEVのみで候補選定。
  - Jul-Aug SUPPORTは選定に使わない。
  - loss増加よりnet exact3を優先しつつ、3点買いROI floorは **120%** を目安に確認。
- もし3点固定で55%へ届かなければ、次段で「条件付き4点目」を別研究として比較する。既存正式3点ロジックはその時点まで変更しない。
- 2026-09結果/払戻は読まない。historical production sentinel / HEAD / BASIC / WATCH gateは変更しない。


## BEFORE — v366 条件付き4点目でexact3 hit-rate向上
- v365 3点固定rerankはRun `35336816467` 実行中。
- ローカルcausal再現では3点固定の追加2>3/4>5 rerankは現時点で約89/165（53.9%）付近が上限に見える。
- 一方、current formal wall3+5>6後の確率から「dominant SECONDに対するconditional THIRD rank3」を4点目候補にすると、extra-hit候補が8R存在。
- 単純gap閾値ローカル確認:
  - gap<=.015: 23Rだけ4点化、90/165=54.55%
  - gap<=.075: 80Rだけ4点化、92/165=55.76%
  - gap<=.10: 97Rだけ4点化、93/165=56.36%
  - 全件近く4点化なら最大95/165=57.58%。
- v366では結果を見ずに使えるpre-race条件だけで4点目追加を選ぶ:
  - conditional THIRD rank2-rank3 gap max
  - extra pair probability min
  - conditional pc(extra) min
  - optional dominant SECOND p2 min
- stakeは正式3点=300円/R + expansion時100円。returnは実3連単100円払戻。
- DEV Feb-Junのみで選定。SUPPORT Jul-Augは選定に使わない。
- 主目的: exact3 hit率55%以上。ROI floorはまず **115%**、120%以上残る候補を優先。
- current formal 3点は変更しない。v366完了までは4点目は研究のみ。
- 2026-09結果/払戻は読まない。


## AFTER — 2026-09-18 丸亀11R LIVE直前判定
- ユーザー指示: 「丸亀11の直前判定出して」。
- race_code=`202609181511`。LIVE request更新commit `dcea29efdf5f48b4dfb0784e83d59fad66d62ae4`。
- chat-live Run `35337502009` / Job `105575648238` completed success / Artifact `10543318656` name `live-v351-final-202609181511`。
- 締切 20:10 JST / evaluated 20:02:47 JST / 約8.75分前。
- 事前値: HEAD=.7823204105 / opponent mass=.4454775433。
- 現行LIVE BASIC cutoffは HEAD>=.790 / mass>=.375、WATCHはBASIC通過かつ mass>=.425。massはWATCH水準だがHEADが.790未満。
- 展示gate自体は PASS: head_exhibition_pass=true / attack_core=.8766667 / threshold=.5010534。
- 展示: EX 1=6.71,2=6.76,3=6.75,4=6.75,5=6.77,6=6.85。ST展示 1=-.03,2=.15,3=.34,4=-.01,5=.02,6=.08。
- original: 1号艇 一周36.93 / まわり足5.40 / 直線6.13。
- 最終判定: **DROP / 見送り**。理由はHEAD=.78232 < LIVE cutoff=.790。tickets=[]。
- 展示が良くてもHEAD gateを上書きしない。WATCH/wall3/five6 ticket補正もBASIC不通過のため非適用。
- result_or_payout_used=false / chronology_guard=true。2026-09-18結果払戻未使用、2026-09-17結果払戻UNREAD維持。


## AFTER — v366 conditional fourth-ticket audit
- Run `35337461131` / Job `105575518121` completed success / Artifact `10542829009` / head `e5f1a630f53ab6cd8be78877efe707dca2f52093`。
- current formal wall3+5>6 baseline:
  - 87/165 = **52.73%**
  - stake 49,500 / return 63,700 / profit +14,200 / ROI **128.687%**。
- DEV-only selected 4th-ticket gate:
  - conditional THIRD rank2-rank3 gap <= .10
  - extra pair prob >= .075
  - p2 dominant SECOND >= .35
  - pc_extra制限なし
  - DEV 75/137 =54.74%、69R expansion、ROI118.77%
  - SUPPORT 18/28 =64.29%、11R expansion、ROI136.53%
  - ALL 93/165 = **56.36%**、80R expansion、stake57,500 / return69,980 / profit+12,480 / ROI **121.704%**
  - formal比 +6 hits、target55%達成。
- always 4th:
  - 95/165=57.58%だがROI **109.32%**。常時4点化は非効率。
- gap-only benchmarks:
  - <=.005: 88/165 ROI129.34%
  - <=.010: 89/165 ROI129.37%
  - <=.015: **90/165=54.55% / ROI129.61%**
  - <=.075: 92/165=55.76% / ROI119.67%
  - <=.10: 93/165=56.36% / ROI118.21%
- LOMO再選定では5 holdout月すべてdelta_hits=0で、ROIは全月低下。したがって広い条件付き4点目はhit-rate向上効果は大きいがcross-month robustnessは弱く、現時点で単独正式採用はしない。
- September outcomes unread / production unchanged / AUDIT_OK=true。

## BEFORE — v367 2>3 rerank + sparse 4th ticket joint search
- 目的: 3点固定rerankと条件付き4点目を合成し、**55%以上のexact3 hit率を保ちながらROI125〜130%台を狙う**。
- current formal 87/165 / ROI128.687%を基準。
- まずFeb-Jun DEVだけで2>3 exhibition rerank候補を探索:
  - basis SCORE/ST/COMBO
  - score3 min .40/.50/.60/.70
  - pair risk min 0/.10/.20/.30
  - mass min .375/.400/.425
  - SECOND g2 0/.25/.50
  - THIRD g3 .25/.50/.75
- DEV上位候補だけをshortlistし、その後にconditional 4thをjoint探索:
  - gap max .005/.01/.015/.02/.03/.05/.075/.10
  - extra pair prob min 0/.075/.09
  - dominant SECOND p2 min 0/.35/.40
- joint選定はDEVのみ。SUPPORT Jul-Augは完全holdout。
- 優先順位:
  1) DEV exact3最大
  2) DEV ROI >=120%
  3) expansion少
  4) loss少
- ALL165で55%以上か、ROIがcurrent formal以上/近傍か、SUPPORT非悪化かを確認。
- production/LIVEは研究完了まで変更しない。


## AFTER — v367 joint 2>3 rerank + conditional 4th
- Run `35337939828` / Job `105577022436` completed success / Artifact `10542749548` / head `2e5d8ae9504c333ce817055d76d482b2b29e385f`。
- current formal baseline:
  - 87/165 =52.73%
  - stake49,500 / return63,700 / profit+14,200 / ROI128.687%。
- DEV-only selected 2>3:
  - basis SCORE
  - score3>=.40
  - score3-score2>=.20
  - mass>=.40
  - SECOND g2=.25 / THIRD g3=.25
- DEV-only selected conditional 4th:
  - THIRD rank2-rank3 gap<=.10
  - extra pair prob>=.075
  - dominant SECOND p2>=.35
- frozen selected:
  - DEV 76/137 = **55.47%**, 68R expansion, ROI **120.52%**
  - SUPPORT 18/28 =64.29%, 11R expansion, ROI136.53%
  - ALL 94/165 = **56.97%**, 79R expansion
  - stake57,400 / return70,700 / profit+13,300 / ROI **123.171%**
- formal比で最終hitは **+7 / loss0**。
  - gains: 202605061107, 202605211711, 202606141601, 202606252104, 202606300106, 202608030402, 202608061001。
- 月別: Feb/Mar/Apr +0、May +2、Jun +3、Jul +0、Aug +2。
- sparse diagnostic after selected 2>3:
  - gap<=.015のみ4点化: 24R expansion / **91/165=55.15%**
  - stake51,900 / return67,860 / profit+15,960 / ROI **130.751%**
  - ただしDEVでは73/137で、.005と同hitのためDEVだけなら.015は選ばれない。supportにより良く見えるので正式候補選定には使わない。
- v366単独4thよりjointで +1 hit（94 vs93）かつROI +1.47pp（123.17 vs121.70）。
- September outcomes unread / production unchanged / AUDIT_OK=true。

## BEFORE — v368 joint hit-push robustness
- 目的: v367 DEV-selected joint案を正式採用候補として近傍・LOMO監査する。
- current formal87/165とv367 94/165をsentinel。
- 2>3近傍:
  - score3 min .35/.40/.45/.50
  - score gap min .15/.20/.25
  - mass .375/.40/.425
  - g2 .125/.25/.375
  - g3 .125/.25/.375
- 4th近傍:
  - gap max .075/.09/.10/.11/.125
  - pair min .07/.075/.08
  - p2 min .30/.35/.40
- DEV-onlyで各近傍を評価、最大hit帯のplateau幅・loss/ROIを見る。
- fixed v367 coreのDEV LOMO（各月holdout）を実施し、hit非悪化を確認。
- SUPPORTは選定に使わず確認のみ。
- 正式採用候補条件:
  - current formal比 hit増
  - formal hit loss=0または極小
  - DEV LOMOで非悪化月多数
  - SUPPORT非悪化
  - ROI>=120%
- current LIVE ticketsはv368完了まで変更しない。


## AFTER — v365 3点固定 hit-rate push
- Run `35336816467` / Job `105573443464` completed success / Artifact `10543264376` / head `fade334bb5108ffa5a3eb423a3ef416759c82fd0`。
- current formal baseline 87/165 / ROI128.687%。
- DEV-only best3点rerank:
  - 4>5 / COMBO
  - outer score>=.50 / risk>=.40 / mass>=.40
  - SECOND g2=0 / THIRD g3=.50
  - DEV 71->72 / ROI129.44->131.80 / gain1 loss0
  - SUPPORT 16->15 / gain0 loss1
  - ALL 87->87 / ROI128.69->129.49 / gain1 loss1
- 313Rもhit数不変、PROD276では-1 hit。
- LOMOはMar holdoutで-1 hit。3点固定だけではexact3 hit-rate向上は再現せず、正式採用根拠なし。
- target55%未達。production unchanged。

## AFTER — v367 joint 2>3 rerank + conditional 4th
- Run `35337939828` / Job `105577022436` success / Artifact `10542749548`。
- DEV-selected:
  - 2>3 SCORE: score3>=.40 / score3-score2>=.20 / mass>=.40 / g2=.25 / g3=.25
  - conditional 4th: THIRD gap<=.10 / extra pair prob>=.075 / dominant SECOND p2>=.35
- result:
  - DEV 76/137=55.47%, ROI120.52%
  - SUPPORT 18/28=64.29%, ROI136.53%
  - ALL **94/165=56.97%**
  - stake57,400 / return70,700 / profit+13,300 / ROI **123.17%**
  - current formal87比 **+7 hits / loss0**
- sparse .015 diagnostic: 91/165=55.15% / ROI130.75% / profit+15,960だが、DEV単独では.005にdominateされるため正式候補選定には使わない。
- production unchanged。

## AFTER — v368 joint hit-push robustness
- Run `35338296659` / Job `105578163902` completed success / Artifact `10544315420` / head `c78f38136b630fa678fac717d170e46aabef169a`。
- v367 core sentinel完全再現:
  - **94/165=56.97%**
  - gain7 / loss0
  - expanded79R
  - stake57,400 / return70,700 / profit+13,300 / ROI123.17%。
- DEV:
  - 76/137=55.47%
  - gain5 / loss0
  - ROI120.52%。
- SUPPORT:
  - 18/28=64.29%
  - gain2 / loss0
  - ROI136.53%。
- 近傍14,580 cells、DEV plateau **1,728 cells** と広い。
  - c23 score min .35-.50
  - c23 risk min .15-.25
  - mass .40-.425
  - c23 g2 .125-.375 / g3 .125-.375
  - 4th gap .075-.125
  - pair min .070-.075
  - p2 min .30-.40
- fixed-core month holdout:
  - Feb +0 / Mar +0 / Apr +0 / May +2 / Jun +3
  - **全DEV月でhit非悪化、loss0**
  - LOMO total +5 hits。
- SUPPORT month:
  - Jul +0 / Aug +2
  - **全support月でhit非悪化、loss0**。
- ROIは追加券コストでFeb/Mar/Aprでは低下するが、全165Rでは123.17%を維持。
- 結論:
  - hit-rate優先なら現時点の最有力はv367/v368 joint core。
  - current formal 52.73% -> **56.97%**（+4.24pt）。
  - ROI 128.69% -> **123.17%**（-5.52pt）だが依然120%超。
  - formal hitを1件も落とさず+7R拾えており、パラメータplateauも広い。
  - ただしユーザーの明示許可前なのでproduction/LIVEへはまだ未昇格。
- September outcomes unread / production unchanged / AUDIT_OK=true。
- 次の再開地点: ユーザーが正式採用を指示したら、wall3 -> 5>6 -> 2>3 hit-push -> conditional 4th の順でLIVE finalizerへ昇格し、pre-hit-push ticketsを監査用に保持して回帰。


## USER DECISION — hit-rate pushは正式採用せず現行維持
- ユーザー判断: 「ROI下がるならこのままでいいかな」。
- 正式LIVEは **現行 wall3 + 5>6 ST** を維持:
  - 87/165 = 52.73%
  - 3点買いROI **128.687%**
- v367/v368 joint hit-push（94/165=56.97%, ROI123.17%）は研究結果として保存するが、正式LIVEへは昇格しない。
- 条件付き4点目も正式採用しない。
- 今後は「的中率だけ上げるためにROIを落とす」変更は優先しない。ROIを維持/改善しつつ的中率も上がる案のみ再検討対象。


## BEFORE — v369 formal ticket rank / staking audit
- ユーザー要望: 「あとは買い方を研究したい。3連単買い目の当たったときの的中買い目が1から3でどれが多いかみたい」。
- 現正式LIVE165（wall3 + 5>6 ST）を固定し、買い目内容は変更しない。
- まず87的中をticket rank別に分解:
  - 第1買い目 / 第2買い目 / 第3買い目の的中数・構成比
  - 各rankの総払戻・平均/中央値払戻・全returnへの寄与
  - 月別 / DEV Feb-Jun / SUPPORT Jul-Aug
- 買い方研究:
  1) rank1のみ / rank2のみ / rank3のみ
  2) 1+2 / 1+3 / 2+3 / 1+2+3均等
  3) 3点を残した固定資金配分（合計600円/R = 6 units、各rank>=100円）の全組合せ
- 固定配分はDEVでROI最大の配分を選び、SUPPORTで確認する。supportを選定には使わない。
- baselineは各100円の300円/R、87/165、return63,700、ROI128.687%。
- 2026-09結果/払戻は読まない。production/LIVE ticketsは変更しない。


## AFTER — v369 formal ticket rank / staking audit
- Run `35344087154` / Job `105596491873` completed success / Artifact `10546631786` / head `89e151b0e18b81ac97c0543e40841ccf2d19e440`。
- current formal baseline完全再現:
  - 165R / 87 hit / return63,700 / stake49,500 / ROI128.687%。
- 87的中のticket rank内訳:
  - **第1買い目: 34 hit (39.08%)**
  - **第2買い目: 28 hit (32.18%)**
  - **第3買い目: 25 hit (28.74%)**
- ただし払戻寄与:
  - rank1 return19,770 (31.04%) / avg581円 / median500円
  - rank2 return22,710 (**35.65%**) / avg811円 / median680円
  - rank3 return21,220 (33.31%) / avg849円 / median770円
- rank単独100円/Rの全165R ROI:
  - rank1 119.82%
  - rank2 **137.64%**
  - rank3 128.61%
- period差が非常に大きい:
  - DEV Feb-Jun: rank1 24hit ROI99.27%, rank2 25hit ROI152.77%, rank3 22hit ROI136.28%
  - SUPPORT Jul-Aug: rank1 10hit ROI220.36%, rank2 3hit ROI63.57%, rank3 3hit ROI91.07%
  - つまり固定でrank2を厚くするルールはDEVに強いがsupportで逆転する。
- rank組合せ100円ずつ:
  - 1+2: 62/165 / ROI128.73%
  - 1+3: 59/165 / ROI124.21%
  - 2+3: 53/165 / ROI133.12%だがsupport ROI77.32%で不安定
  - 1+2+3: 87/165 / ROI128.69%。
- DEVだけで選んだ固定all-three配分:
  - 400円/R best = 1:2:1 (100/200/100)
    - DEV ROI135.27%
    - SUPPORT ROI109.64%
    - ALL ROI130.92%
  - 500円/R best = 1:3:1
    - DEV138.77%, SUPPORT100.43%, ALL132.27%
  - 600円/R best = 1:4:1
    - DEV141.11%, SUPPORT94.29%, ALL133.16%
- 結論:
  - 的中頻度はrank1最多だが、収益性はrank2/rank3の高配当寄与が大きい。
  - rank傾向がDEVとSUPPORTで大きく反転しており、**固定順位ウェイトは頑健ではない**。
  - 現時点では100/100/100均等買いをformal維持。
  - 次の買い方研究はrank番号固定ではなく、各レースのpair probability gap / conditional THIRD gap / wall3・5>6発火 / 市場オッズ等を使ったdynamic stakeが本命。
- September outcomes unread / production unchanged / AUDIT_OK=true。


## BEFORE — v370 closing-odds dynamic stake allocation
- ユーザー指示: 「研究続けて」。
- v369固定rank配分はDEV/SUPPORTで反転したため、固定1:2:1等は正式採用しない。
- repoには `data/official_closing_odds3t/YYYY/MM/DD.csv` と旧v340 adaptive odds Dutch研究が存在。BOAT RACE公式締切時3連単オッズを165Rのbuying featureとして再利用する。
- 旧v340のrace skip/点数追加ルールは現formalへそのまま移植しない。今回は**165R全件・現正式3点を固定**し、レース数も買い目も減らさず資金配分だけ研究する。
- 公平比較:
  - 1R総額600円固定（6 units ×100円）
  - 3点すべて最低100円
  - equal baseline = 200/200/200。ROIは100/100/100と同一理論値128.687%。
- dynamic allocation candidate:
  - 各ticketのformal pair probability `p_i`
  - 公式締切odds `o_i`
  - score = `p_i^alpha * o_i^beta`
  - alpha=0/.5/1/1.5/2、beta=-1/-.5/0/.5/1
  - 残り3unitsをscore比例で100円単位配分。
  - alpha=0,beta=-1 はDutch寄り、alpha=1,beta=0 はmodel確率寄り、alpha=1,beta=1 はmodel×odds（EV寄り）。
  - positive-edge `max(p*odds-threshold,0)` 系も比較する。
- 選定:
  - Feb-Jun DEVのみでROI最大/安定候補を選ぶ。
  - Jul-Aug SUPPORTは完全holdout。
  - 月別・DEV LOMO・近傍plateauを確認。
- returnは結果の公式100円払戻×購入unitsで計算し、closing oddsそのものを払戻として使わない。
- 2026-09 outcomes/payoutは読まない。production/LIVE ticket compositionは変更しない。


## v370 initial failure — closing odds coverage gap
- Run `35345276839` / Job `105600270321` failure。
- 原因: current repo `data/official_closing_odds3t` だけではLIVE165のうち144R coverage、Jul-Aug 21Rが欠損。
- missing例: `202607231508`, `202608030402`, `202608061001`, `202608112101` 等、計21R。
- 研究/モデル/正式ticketのfailureではなく、repo archive coverageの問題。
- 旧v340 sharded auditは276/276公式締切オッズcoverageを達成済みで、各shard artifactの `odds_N.csv` にrace_codeごとの `odds_json`（1頭固定20通り）を保存していることをコード監査で確認。
- 修正方針:
  - repo公式締切odds CSVを第一ソース
  - 欠損のみv340 shard artifacts（IDs 10329564703 / 10330810260 / 10330651756 / 10329684566 / 10330273057 / 10330357729）からfallback
  - 165/165にならなければfail
- decision/staking gridは一切変更しない。fresh Runで再監査。


## v370 second failure — one-race closing odds gap
- Run `35345499496` / Job `105600982926` failure。
- repo CSV + v340 shard fallbackで **164/165** まで復元。
- 残るmissingは `202608210402` 1Rのみ。旧v340 production276対象外のためshardにも存在しない。
- 修正: repo CSV -> v340 shard -> BOAT RACE公式 historical odds3t fetch（旧v340と同じfetch関数）の3段fallback。
- 公式fetchもclosing trifecta oddsのみで、結果/払戻はdecision featureに使わない。
- 165/165にならなければ引き続きfail。staking gridは変更なし。


## AFTER — v370 closing-odds within-race 600yen allocation
- final Run `35345751484` / Job `105601806665` completed success / Artifact `10545859624` / head `b80dcbb02e14047cf8f5775cedb466fa5b3f1a36`。
- official closing odds coverage **165/165**:
  - repo CSV 144R
  - v340 shard fallback 20R
  - BOAT RACE公式historical odds3t page fallback 1R
  - missing 0。
- equal 600円（200/200/200）baseline:
  - stake99,000 / return127,400 / profit+28,400 / ROI **128.687%**（100/100/100と同率）。
- DEV-only raw bestは EDGE threshold=.8:
  - DEV ROI143.75% vs equal129.44%
  - ALL ROI137.89% vs128.69%。
- しかし SUPPORT:
  - equal125.00% -> selected109.23%（-15.77pt）
  - Jul -39.26pt / Aug -4.65pt
- LOMOは5月中3月のみ非悪化。Mar/Mayで悪化。
- 結論: 固定600円を3点内でEV配分する方式はDEV過適合が強く、正式採用しない。
- production unchanged / September outcomes unread / AUDIT_OK=true。

## BEFORE — v371 base300 + positive-edge boost staking
- 目的: 165R全件・formal3点を必ず各100円買いつつ、期待値の高い券だけ追加100円する。
- race skipなし / ticket削除なし。最低stakeは常に300円/R。
- decision featureは公式締切oddsとformal model exact-pair probabilityのみ。
- edge mode:
  1) conditional edge = `pair_prob * odds`
  2) unconditional edge = `p_head * pair_prob * odds`
- threshold grid .5/.6/.7/.8/.9/1.0/1.1/1.2/1.3/1.4/1.5/1.75/2.0。
- 1レースで追加するのは、threshold以上のticketをedge順に最大1/2/3点、各+100円。
- DEV選定は単純最大ROIではなく月別robustnessを入れる:
  - DEV全体でequal baseline比 +5pt以上
  - Feb-Jun 5月中4月以上で非悪化
  - worst monthly delta >= -3pt
  - 上記を満たす中でworst month最大 -> DEV ROI最大 -> 追加units少を優先。
- Jul-Aug SUPPORTは完全holdout。
- DEV LOMOでも同じrobust selectionを4月trainで再選定しholdout確認。
- 現formal100/100/100は変更しない。v371はresearch only。


## BEFORE — v372 purchase-time pre-close validation of v371 edge boost
- v371 closing-odds research coreを固定:
  - mode=COND
  - edge = formal pair_prob × odds
  - threshold=.70
  - max_extra=2
  - base100/100/100は必ず購入。
- pre-close source監査:
  - BoatraceCSV `data/previews/od3`
  - `取得日時 < 締切時刻` のsnapshotのみ
  - raceごとにT-10分に最も近いものを使用
  - 過去v112/v134で平均約9.1分前、履歴は2026-07-19以降。
- 重要: v371 threshold=.70はFeb-Jun DEVのclosing oddsで選定済み。このv372ではJul19-Augのpre-close結果を見てthreshold/最大点数を変更しない。
- current formal LIVE165のうち、pre-close coverageがあるJul19-Aug subsetだけをoperational validation対象にする。
- 比較:
  1) base100/100/100
  2) fixed v371 coreをclosing oddsで適用（同一subset）
  3) fixed v371 coreをT-10 pre-close oddsで適用（本命）
- 指標:
  - coverage R / lead time
  - preclose vs closingでboost対象ticket一致率・race-level allocation一致率
  - ROI / profit / extra units
  - closing-edgeとの差
  - Jul19-31 / Aug別
- pre-close oddsはdecision featureのみ、actual payout100はsettlement-only。
- threshold再選定なし。production/LIVE stakingは変更しない。
- 2026-09 outcomesは読まない。


## AFTER — v371 base300 + positive-edge boost staking
- Run `35346333370` / Job `105603666579` completed success / Artifact `10546911950` / head `3897f9baf8bf6c47707bc8f8432a632f42c01bd3`。
- all165 / formal3点は全て100円購入し、edgeの高い券だけ+100円。
- DEV robust選択:
  - edge=`formal pair_prob * official closing odds`
  - threshold=.70
  - 1R最大2券boost
- ALL:
  - equal baseline stake49,500 / return63,700 / profit+14,200 / ROI128.687%
  - boost stake70,600 / return97,350 / profit**+26,750** / ROI**137.890%**
  - ROI +9.20pp / profit +12,550。
- DEV ROI138.29%（equal129.44%）、SUPPORT ROI135.98%（equal125.00%）。
- fixed core月別: Feb +35.27pp, Mar +6.88, Apr +6.42, May -1.58, Jun +14.66, Jul +21.51, Aug +6.12。7月中6月改善。
- ただしLOMO再選定は5月中3月のみ非悪化でparameter selectionは完全安定ではない。
- closing oddsは購入時点で同値を保証できないためformal採用せず、v372でpre-close operational validationへ。

## AFTER — v372 T-10 pre-close validation
- script commit `2ac2521f0046b2f329b12d2a45bf8aadf723a2d6`
- workflow commit `3faf7a3f3305b084bc63bba83ea284266c0c30b0`
- Run `35346829065` / Job `105605266732` completed success / Artifact `10547476108` / digest `sha256:2a481aee6b948829db2c386c44bc07ddbd2b15544bdb7c30e1bbd77340163465`。
- fixed v371 core (.70 / max2)を一切再調整せず、BoatraceCSV `data/previews/od3` の取得時刻<締切、T-10に最も近いsnapshotへ適用。
- current formal rows in historical preclose period=21R / coverage21R / missing0。
- snapshot lead: mean9.42分前 / median9.58 / min8.39 / max9.67。
- closing allocationとのrace-level完全一致 14/21=66.7%、ticket-level 56/63=88.9%。
- 同一21R:
  - equal100/100/100: stake6,300 / return7,370 / profit+1,070 / ROI**116.98%**
  - closing-edge boost: stake9,100 / return10,870 / profit+1,770 / ROI119.45%
  - **T-10 preclose-edge boost: stake9,600 / return9,710 / profit+110 / ROI101.15%**
  - equal比 -15.84pp / profit -960。
- Aug19Rだけでも equal115.09% -> closing121.20% -> preclose102.30%。
- 結論: v371のclosing-odds edge boostは実運用T-10へ転送できずREJECT。formal stakingは100/100/100維持。
- thresholdはv372で再選定していない。September outcomes unread / production unchanged / AUDIT_OK=true。

## BEFORE — v373 model-only dynamic boost research
- オッズ依存を完全に外し、直前判定時点で確定しているmodel/exhibition情報だけで追加100円を配る。
- formal3点・165R・各100円baseは固定。race skip/ticket削除なし。
- ticket-level features:
  - formal ticket rank 1/2/3
  - formal pair probability p_i
  - p1-p2 / p2-p3 / p_i / p1 ratio
- race-level causal features:
  - HEAD probability
  - opponent mass
  - wall3 applied/risk
  - five6 applied / ST6-ST5 / score6
- candidate boost ruleは最大1券+100円を基本にし、必要なら最大2券も比較。
- p閾値・rank subset・gap・HEAD/mass・overlay発火でsimple rule gridを作る。
- DEV Feb-Junで選定する際は:
  - DEV全体ROI改善
  - 月別4/5以上非悪化
  - worst-month悪化を制限
  - boost件数最低sample guard
- Jul-Aug SUPPORT完全holdout。
- LOMO再選定、近傍plateauも監査。
- closing/preclose oddsはfeatureとして使用しない。actual payoutはsettlementのみ。
- formal LIVE tickets / 100/100/100 stakingはv373完了まで変更しない。


## BEFORE — v370 current formal 3-ticket dynamic staking with official odds
- ユーザー指示: 「研究続けて」。v369後の買い方研究を継続。
- repo確認で公式締切3連単オッズ履歴 `data/official_closing_odds3t/2026/MM/DD.csv` と旧v340 adaptive odds Dutchを発見。
- 旧v340は低合成オッズの大量skipがROI改善の主因だったが、今回はユーザー意向に合わせ**165R全部・正式3点全部を最低100円買う**。レース/買い目は削らない。
- current formal baseline:
  - wall3 + 5>6 ST
  - 165R / 87hit / 52.73%
  - 100/100/100 = stake49,500 / return63,700 / ROI128.687%。
- v370目的:
  1) current formal3点にBOAT RACE公式締切3連単オッズを結合。
  2) formal post-wall3+5>6 probabilitiesから各ticketの conditional pair probability と `p_head * pair_prob * odds` のmarket-EV proxyを作る。
  3) 全レース最低1/1/1 unit(各100円)を維持し、DEV Feb-Junだけで「追加unit」を選定。
  4) 比較:
     - fixed 600円/R equal 2:2:2
     - fixed 600円/R Dutch（inverse odds）
     - fixed 600円/R model-prob配分
     - base300円 + EV/combined-odds gate時のみ100〜300円bonusを最有力ticketへ
  5) DEV選定→SUPPORT Jul-Aug確認。月別・近傍・bonus回数も監査。
- settlement returnは結果から公式100円払戻を使うが、stake決定には結果/払戻を一切使わない。
- **重要な時系列制約**: archived `official_closing_odds3t` は締切時表示オッズであり、historical explorationには使えるがLIVE購入時点より後になる可能性がある。v370結果だけで正式採用しない。採用前に現在のLIVE odds parserで取得可能な時点へ移植/forward確認が必要。
- 2026-09 outcomes/payoutsはUNREAD。production/LIVE stakeは変更しない。


## AFTER — v373 model-only ticket boost
- Run `35347241967` / Job `105606588151` completed success / Artifact `10547917067` / head `954eaba129168dcd2b1755c6356a6cea36006a23`。
- odds feature完全不使用。current formal100/100/100 baseline 165R / stake49,500 / return63,700 / ROI128.687%。
- DEV robust-selected:
  - rank2のみ
  - pair probability <= .085
  - p1-p2 gap <= .020
  - mass>=.375
  - overlay ANY
  - +100円最大1ticket
- DEV: +20units / extra return5,620 / incremental ROI281% / total ROI136.47%。
- ALL: +25units / extra return5,620 / stake52,000 / return69,320 / ROI133.31%。
- しかし SUPPORT Jul-Aug:
  - +5unitsに対して extra return **0円**
  - equal ROI125.00% -> total117.98%
  - Jul/Augとも悪化。
- LOMO再選定は5/5 holdout月でROI悪化、nonnegative=0。モデルonly ticket-level boostもREJECT。
- production/LIVE stakingは100/100/100維持。

## BEFORE — v374 formal-overlay race-level stake concentration audit
- v369〜v373でrank固定・closing odds・T-10 odds・model-only ticket boostはいずれもperiod反転あり。
- 新仮説: **すでに正式採用済みのwall3 / 5>6 ST overlayが発火するレースだけ、3点を均等に厚くする**。
- これは新しい結果最適化gateではなく、現formal ticket rerankのcausal状態フラグをそのままstake signalに使う。
- current LIVE165 preliminary descriptive:
  - overlay EITHER =36R / 3点均等 subgroup ROI **163.33%**
  - NONE=129R / ROI **119.02%**
  - DEV overlay29R ROI156.78%
  - SUPPORT overlay7R ROI190.48%
  - category: FIVE6-only24R ROI155.0%, WALL3-only11R ROI166.36%, BOTH1R ROI330%。
- v374では閾値を再調整せず、formal overlay定義を固定したまま母集団拡大:
  - LIVE165
  - H078_M375 236R
  - H0775_M375 269R
  - H0775_M350 313R
  - PROD276
- 各母集団で:
  - equal100/100/100 baseline
  - overlay EITHER subgroup ROI
  - NONE subgroup ROI
  - overlay発火時だけ 200/200/200 (2x), 300/300/300 (3x), 400/400/400 (4x)
  - DEV/SUPPORT/月別/disjoint added bands
- ticket compositionは各rowにcurrent wall3→5>6を適用して再構成。race selection自体は各母集団固定。
- 目標: 165R固有の偶然ではなく、拡大母集団でもoverlay群のROI優位が残るか確認。
- 2026-09 outcomes/payoutsは読まない。production/LIVE stakeはv374完了まで変更しない。


## AFTER — v374 formal-overlay race-level stake concentration
- Run `35351286759` / Job `105619772837` completed success / Artifact `10548879270` / head `6c617dfb9b50bc75293141da53b6dfe96ac093f4`。
- parameter tuningなし / odds featureなし / current formal overlay flagのみをstake signalに使用。
- LIVE165 baseline: 165R / 87hit / stake49,500 / return63,700 / ROI128.687%。
- overlay EITHER (wall3 OR five6):
  - 36R / 21hit / subgroup ROI **163.33%**
  - NONE 129R / 66hit / ROI119.02%
  - DEV overlay29R ROI156.78%
  - SUPPORT overlay7R ROI190.48%
- overlay時だけ3点均等を2倍（200/200/200）:
  - stake60,300 / return81,340 / profit+21,040 / ROI **134.892%**
  - baseline比 +6.21pp / profit +6,840。
  - DEV ROI129.44 ->134.22%
  - SUPPORT ROI125.00 ->138.10%
- multiplier 3x: ROI139.21%、4x:142.39%（当然overlay subgroup ROI163.33%へ近づく）。倍率自体は未選定。
- expanded universesでもoverall overlay subgroupはbaselineより高い:
  - 236R overlay49R ROI150.48%
  - 269R overlay58R ROI132.93%
  - 313R overlay65R ROI129.79%
  - PROD276 overlay60R ROI141.78%
- 2x portfolioも全expanded universeでoverall ROI改善。
- ただしdisjoint追加帯は不均一:
  - +71R overlay13R ROI114.87%
  - +33R overlay9R ROI37.41%（明確に弱い）
  - +45R overlay7R ROI103.81%
  よって「overlayなら普遍的に高ROI」ではなく、current core165内で特に強い可能性あり。
- LIVE165 category:
  - FIVE6を含む25R ROI162.0%（DEV148.42 / SUPPORT205.0）
  - WALL3を含む12R ROI180.0%（DEV186.97 / SUPPORT1Rのみ103.33）
  - NONE129R ROI119.02%。
- 月別EITHER overlay ROIは Feb0 / Mar41.11 / Apr217.22 / May77.88 / Jun323.33 / Jul296.67 / Aug172.78。月単位では振れが大きい。
- production/LIVE stake unchanged / September outcomes unread / AUDIT_OK=true。

## BEFORE — v375 fixed overlay-stake robustness
- v374で見えたstake signalを**新規チューニングなし**で頑健性監査する。
- fixed candidateは自然な最小倍率2xのみ:
  1) EITHER: wall3 OR five6 発火レースを200/200/200
  2) FIVE6: five6発火レースのみ200/200/200
  3) WALL3: wall3発火レースのみ200/200/200
- current LIVE165を主対象。
- 監査:
  - 各月単体delta ROI/profit
  - leave-one-month-out（固定signal、再選定なし）
  - 7か月の全month subsets（4か月以上）でbaseline比ROI非悪化率
  - DEV Feb-Jun / SUPPORT Jul-Aug
  - expanded universe全体とdisjoint band
- signal選定に新しい閾値や払戻最適化は使わない。FIVE6/WALL3/EITHERは既にformal overlay componentとして事前定義済み。
- 目的: stake shadowとしてforward運用に回せるほど安定かを見る。正式stake採用はユーザー許可まで行わない。


## AFTER — v375 fixed overlay-stake robustness
- Run `35351867665` / Job `105621672737` completed success / Artifact `10550240515` / digest `sha256:31038e65a699413c61f5eac60d50ee6f83526a47cefc67e9b30414d276df14a1` / head `01ad9245e69dc35f53a3bd94d35dc966b0c42787`。
- parameter searchなし。固定2x（signal raceだけ200/200/200、他は100/100/100）を監査。
- EITHER:
  - ALL ROI128.687 -> **134.892%**, profit +14,200 -> **+21,040**
  - DEV 129.44 ->134.22
  - SUPPORT 125.00 ->138.10
  - leave-one-month-out 7/7すべてROI改善
  - 4か月以上の全month subsetで非悪化 **85.94%**
  - subset median delta +6.80pp / worst -5.99pp
- FIVE6:
  - ALL ROI -> **133.070%**, profit +18,850
  - DEV +2.31pp / SUPPORT +14.12pp
  - LOO 7/7改善
  - month subset非悪化 **93.75%**（3 signal中最高）
  - subset median +4.63pp / worst -3.52pp
- WALL3:
  - ALL ROI ->132.166%
  - SUPPORTは -0.75pp（1 signal raceのみ）
  - LOO 7/7改善
  - month subset非悪化90.63%
- 単月ではEITHER/FIVE6ともFeb/Mar/May悪化、Apr/Jun/Jul/Aug改善。したがって短期の月単位振れは大きい。
- expanded universe overallではEITHER/FIVE6/WALL3の2xはいずれも概ね改善するが、disjoint追加33R帯は全signalで悪化。current LIVE165で特に強い。
- 結論: overlay signalをrace-level stake signalとして使う価値は高い。特にFIVE6はsubset robustness、EITHERは総ROI/利益で優勢。ただし単月varianceがあるため正式採用前に資金曲線/最大DD監査が必要。
- production/LIVE stake unchanged / September outcomes unread / AUDIT_OK=true。

## BEFORE — v376 overlay staking bankroll / drawdown audit
- 目的: v374/v375で有望なformal overlay stake concentrationについて、ROIだけでなく**時系列リスク**を評価する。
- 新しいpredictive gate/thresholdは一切導入しない。
- current LIVE165をrace_code時系列順に固定。
- signal: EITHER / FIVE6 / WALL3。
- multiplier: 1x / 2x / 3x / 4x（signal raceの3点を均等に倍率化、他は100/100/100）。
- 評価:
  - total ROI / profit
  - max drawdown（円）
  - max drawdown / cumulative stake
  - peak-to-trough race count
  - longest losing streak
  - worst 10R / 20R rolling profit
  - profit per 10,000円 stake
  - monthly profit volatility
- DEV / SUPPORTも別集計。
- 目的はROI最大の倍率を選ぶことではなく、**追加リスク1円あたりの利益**とDDの増え方を比較し、forward stake shadowの自然な倍率を決めること。
- 2026-09 outcomes/payoutsは読まない。formal stakingは変更しない。


## AFTER — v376 overlay staking bankroll / drawdown audit
- Run `35352111242` / Job `105622465377` completed success / Artifact `10550135945` / digest `sha256:36f1660db43aac2698db949485db19079f319bdab449a85fa48f63596577afa2` / head `97daff8edf55df0d009dddfd365e78e80f6a755d`。
- formal baseline 100/100/100:
  - stake49,500 / return63,700 / profit+14,200 / ROI128.687%
  - max DD 2,240円 / worst10R -1,930 / worst20R -1,580 / longest losing streak7。
- EITHER 2x:
  - stake60,300 / return81,340 / profit**+21,040** / ROI**134.892%**
  - extra stake10,800 / extra return17,640 / extra profit+6,840 / incremental ROI163.33%
  - max DD **3,320円**（baseline比+1,080）
  - worst10R -2,760 / worst20R -2,670 / longest losing streak7。
- FIVE6 2x:
  - profit+18,850 / ROI133.07%
  - max DD3,020（+780）
  - extra profit+4,650 / incremental ROI162.0%。
- WALL3 2x:
  - profit+17,080 / ROI132.17%
  - max DD2,610（+370）
  - extra profit+2,880 / incremental ROI180.0%。
- 3x/4xはhistorical subgroup ROIが高いためROI/利益も機械的に増えるが、maxDDも大きく増加:
  - EITHER 3x maxDD4,820 / 4x6,320
  - FIVE6 3x4,220 / 4x5,420
  - WALL3 3x3,210 / 4x3,810。
- 結論: forward shadowの自然な最小非自明倍率は **2x**。3x/4xはhistorical結果を見て倍率を上げる形になるので現時点では採用根拠にしない。
- production/LIVE official stake unchanged / September outcomes unread / AUDIT_OK=true。

## BEFORE — v377 LIVE overlay stake shadow
- formal tickets・formal stakeは変更しない。
- current official stake = 各ticket100円（100/100/100）。
- research-only stake shadow:
  - formal wall3_ticket_applied OR five6_ticket_applied のとき **200/200/200**
  - それ以外は100/100/100
  - profile名を固定し、`research_only=true`。
- LIVE final JSONに official_stakes / stake_shadow_profile / stake_shadow_signal / stake_shadow_applied / stake_shadow_stakes / stake_shadow_total を追加。
- 保存済みcausal inputで
  1) wall3発火
  2) five6発火
  3) overlay非発火
  の3ケース回帰を作る。
- formal ticket identity / HEAD / BASIC/WATCH / historical production sentinelは不変。
- 2026-09 outcomes/payoutsは読まない。


## AFTER — v377 LIVE overlay stake shadow
- profile commit `e8c256499d2a6108a0d38ddd88379af2f9dcb3f8`
  - official stake = 100円/ticket
  - shadow profile = `1HEAD_OVERLAY_STAKE_SHADOW_V375_EITHER_2X`
  - multiplier=2
  - research_only=true。
- finalizer commit `830c0a452e7ea100b4eb321fb00da6ab740f5488`
  - formal tickets/stakingは不変。
  - PASS時 `official_stakes_yen=[100,100,100]` / total300。
  - formal wall3 OR five6 が発火した時のみ shadow `[200,200,200]` / total600。
  - 非発火はshadowも100/100/100。
  - 新規出力: official_stakes_yen / official_total_stake_yen / stake_shadow_profile / stake_shadow_signal / stake_shadow_applied / stake_shadow_stakes_yen / stake_shadow_total_stake_yen / stake_shadow_research_only。
- v377 regression:
  - script commit `5d295af9886e7aa626b2a8fbd03490c6ecac4ec2`
  - workflow commit `f0de6cf7944b6faa8dc6b7b1f040c5659df76dab`
  - Run `35352429954` / Job `105623519742` success / Artifact `10550325833`
  - digest `sha256:5e0e03fd05144c6b2e44d049e642932cec1dd2869b177a5094ff3844815643bb`
  - wall-only causal case `202603290511`: official100/100/100, shadow200/200/200。
  - five6-only causal case `202602222401`: official100/100/100, shadow200/200/200。
  - no-overlay causal case `202602012104`: official100/100/100, shadow100/100/100。
  - result_or_payout_used=false / September outcomes unread / AUDIT_OK=true。
- existing formal ticket regressions after finalizer change:
  - v356 Run `35352354794` success
  - v364 Run `35352354777` success
  - formal wall3 / five6 ticket identities unchanged。
- 現時点の運用:
  - **正式買い方は引き続き100/100/100**
  - stake shadowのみ overlay発火時200/200/200
  - 今後のmanual LIVE「判別して」では正式買い目と併せてshadow stake発火有無を確認できる。
- forward結果を読む許可が得られるまで、shadowの実戦成績でformal昇格は行わない。


## BEFORE — v370 current formal 3-ticket dynamic staking with official closing odds
- ユーザー指示: 買い方研究を継続。
- v369で固定rank配分はDEV/SUPPORTで傾向反転したため、rank番号固定ではなくraceごとのmodel probability + 公式3連単オッズで動的配分を研究する。
- 現正式買い目は固定:
  - opponentCore -> wall3 -> 5>6 ST
  - 87/165 / equal 100-100-100実払戻ROI128.687%
- odds source:
  - repo `data/official_closing_odds3t/YYYY/MM/DD.csv`
  - BOAT RACE公式締切3連単オッズ。
  - これはhistorical backtestでは「締切時の最終表示」であり、実LIVEで発注直前に完全同値が必ず見えるわけではない。したがってallocation研究用proxyとして扱い、productionへそのまま直結しない。
- 全165Rを買う。skip/dropはしない。
- 3点すべて最低100円を維持。
- budget:
  - 600円/R = 6 units
  - 1000円/R = 10 units
- candidate allocation:
  1) EQUAL
  2) DUTCH: inverse oddsでgross return均等化
  3) MODEL: formal pair probability比例
  4) VALUE_PROP: score = p^alpha * odds^beta の比例配分
  5) VALUE_TOP: base1unitずつ + 残unitを最大 p^alpha*odds^beta の1点へ
- grid alpha=.5/1/1.5/2, beta=-1/-.5/0/.5/1。
- 評価returnはallocationに使用したclosing oddsから逆算せず、実公式払戻100円をstake units倍して算出。
- selectionはFeb-Jun DEVのみ。Jul-Aug SUPPORTは完全holdout。
- baselineは同budgetの均等配分と、現行300円 equalの両方を表示。
- 月別、rank別stake、profit、ROI、support劣化を監査。
- 2026-09 outcomes/payoutsは読まない。LIVE tickets/productionは変更しない。

- v370実装時のbudget補正:
  - 1000円/Rは3点均等を100円単位で表現できず4:3:3のrank biasが入るため不採用。
  - 比較budgetは **600 / 900 / 1200円/R**（2:2:2 / 3:3:3 / 4:4:4が完全均等）。


## v370 初回failure — Jul/Aug closing odds archive 21R不足
- Run `35358284121` / Job `105642936999` failure。
- 原因: repo `data/official_closing_odds3t` のcurrent LIVE165対象でclosing oddsが21R不足。
- missing例: `202607231508`, `202607282409`, `202608012209`, `202608030402`, `202608041001`, `202608061001` 等。
- formal ticket/payout baselineやallocationロジックのfailureではない。
- v340 sharded official odds auditは276/276 coverage成功済みで、公式closing oddsを6 shard Artifactに凍結保存:
  - 10329564703 / 10330810260 / 10330651756 / 10329684566 / 10330273057 / 10330357729
- 修正方針: repo archiveを第一source、欠損のみv340 frozen shard `odds_json` をfallbackとして使う。ネット再取得はしない。
- 165/165 coverageを必須sentinelにしてfresh Run。


## v370 second coverage failure — current LIVE固有1R
- Run `35358619903` / Job `105644044180` failure。
- repo archive + v340 frozen shardsで missing 21R -> **1R** まで回復。
- 残り `202608210402` はcurrent LIVE165には含まれるが旧v340 production276には含まれず、frozen shardにも存在しない。
- 修正: この1Rのみ v340と同じ BOAT RACE公式historical `odds3t` endpointをfallback使用。取得sourceをrace_inputs/resultへ明記し、今回Artifactに固定。
- 165/165 coverage必須は維持。allocation条件は変更しない。


## AFTER — v370 dynamic odds staking
- Final success Run `35358877372` / Job `105644898048` / Artifact `10553791049` / digest `sha256:e43c00bc770b52ea7175905662a2e0106a738c4db8d01f6a371ad6c48a9783b9` / head `1a5eccc4e09fa58b632db0682f71104c2f14e9c1`。
- odds coverage 165/165:
  - repo archive 144R
  - v340 frozen official odds 20R
  - official historical endpoint fallback 1R (`202608210402`)
- formal equal300 sentinel: 87/165 / stake49,500 / return63,700 / ROI128.687%。
- DEV-only bestは全budgetで同じ:
  - `VALUE_TOP`
  - score = `p^0.5 * closing_odds^1.0`
  - 3点最低100円、残unitをscore最大の1点へ全投入。
- B600:
  - DEV ROI148.11%
  - SUPPORT ROI126.79% vs equal125.00%
  - ALL ROI **144.49%** / stake99,000 / return143,050 / profit+44,050
  - equal600 ROI128.69%比 +15.81pt。
- B900:
  - DEV154.34%
  - SUPPORT127.38%
  - ALL **149.76%** / profit+73,900 / +21.08pt vs equal。
- B1200:
  - DEV157.45%
  - SUPPORT127.68%
  - ALL **152.40%** / profit+103,750 / +23.71pt vs equal。
- allocation pattern:
  - score最大rankは rank1=15R / rank2=75R / rank3=75R。
  - したがって「rank2固定厚め」ではなく、オッズ×モデル確率でrank2/3を選び分ける動的配分。
  - score最大ticketが実際に的中したのは24/165R（rank1 3 / rank2 11 / rank3 10）。
- named baseline:
  - DUTCHはALL ROI117.05〜119.25%でequalを下回る。
  - MODEL probability比例もALL ROI125.29〜128.29%でequalを超えない。
  - 改善源はVALUE_TOP。
- 月別VALUE_TOP:
  - Feb/Mar/Jun/Augでequal超え
  - Apr/May/Julでequal割れ。
  - SUPPORT合計はプラスだがJul悪化/Aug改善で相殺傾向。
- 重要注意:
  - closing oddsはhistorical最終表示で、LIVE発注直前に同値を保証しないため、現時点ではallocation研究proxy。
  - budgetを増やすほどALL ROIは上がるが、資金集中・分散のリスクも増すためそのまま採用しない。
- September outcomes unread / production unchanged / AUDIT_OK=true。

## BEFORE — v371 dynamic staking robustness / concentration audit
- 目的: v370 VALUE_TOPの過学習・closing-odds依存・資金集中を監査。
- v370 Artifact `10553791049` の `race_inputs.csv` を固定入力として使用し、オッズ再取得なし。
- candidate score:
  - `p^alpha * odds^beta`
  - alpha 0/.25/.5/.75/1.0/1.25
  - beta .5/.75/1.0/1.25/1.5
- allocation:
  1) TOP: base1unitずつ + 残り全部をscore最大
  2) TOP2: 残unitをscore上位2点へ2:1で配分
  3) PROP: score比例
  4) CAP67: score最大の総stake比を約2/3以下にし、残りをscore2位へ
- budget 600/900/1200。
- 選定はFeb-Jun DEVのみ。
- robustness:
  - actual DEV LOMO: 1月holdoutごとに残4月で再選定→holdout評価
  - Jul-Aug SUPPORT完全holdout
  - 近傍plateau
  - 月別ROI
  - max drawdown / losing streak / profit volatility
  - score最大ticketのrank構成/的中寄与
- 採用候補は「ALL ROI最大」ではなく、SUPPORTでequal非劣化・LOMO多数月非悪化・過度な集中を避けるものを優先。
- production/LIVE stakingはv371完了まで変更しない。


## v371 初回failure — pandas mode列名衝突
- Run `35359370762` / Job `105646533493` failure / partial Artifact `10554156750`。
- 原因: plateau抽出で `g.mode.eq('TOP')` と書き、DataFrame.modeメソッドと列名が衝突してAttributeError。
- DEV grid / raw+robust選定 / support/all評価 / true LOMO計算までは実行済み。データ・研究条件のfailureではない。
- 修正: `g['mode'].eq('TOP')` のみ。fresh Runで最終Artifactを作る。


## BEFORE — v378 overlay内 3点資金配分 audit
- 買い方研究を継続。
- current formal ticketsは固定（87/165）。
- current stake shadowも総額レベルでは固定:
  - formal wall3 OR five6発火レース: total600円
  - その他: total300円
- 今回は**総stakeを変えず、overlay36Rの600円を3点へどう配るかだけ**を研究。
- 候補は100円単位・各ticket最低100円・合計6 units:
  - 全positive integer composition of 6 = 10通り
  - 例 2/2/2, 1/2/3, 1/1/4 等
- 主比較:
  1) EITHER overlay36Rすべて同一weights
  2) FIVE6発火のみweights変更、その他overlayは2/2/2
  3) WALL3発火のみweights変更、その他overlayは2/2/2
- DEV Feb-Junのみでweights選定。
- SUPPORT Jul-Augは完全holdout。
- 評価:
  - overall ROI/profit（stakeはEITHER2x baselineと同額60,300円）
  - overlay subset ROI
  - rank別hit/return寄与
  - 月別
  - fixed-weight leave-one-month-out
  - 近傍（weight 10通り）でsupport非悪化有無
- 比較baseline: EITHER 2x equal = 200/200/200 on overlay, 100/100/100 otherwise。
- 2026-09 outcomes/payoutsは読まない。formal tickets / official stake / shadow stakeは変更しない。


## AFTER — v371 dynamic staking robustness
- Run `35359641195` / Job `105647445277` success / Artifact `10553427745` / digest `sha256:d2a6fe568f57d95a8eef5dc96b23b662d89ab5af785e1b51dec5fbee7a055463` / head `36005c8b82d9f15ec41b81c3b6f2b032e2ee3bb2`。
- frozen v370 165R inputsのみ使用。再取得なし。AUDIT_OK=true / September unread。
- 360-cell gridのDEV raw/robust bestは全budgetで同じ:
  - mode=TOP
  - alpha=0
  - beta=.5
  - score = `odds^0.5`
  - つまり実質 **3点の中で最高オッズの1点へ残資金を全投入**。モデル確率は使わない。
- DEV:
  - B600 ROI152.97% / drawdown6,390 / 4/5月でequal以上
  - B900 ROI160.81% / drawdown11,150
  - B1200 ROI164.73% / drawdown15,950
- SUPPORT:
  - B600 ROI126.79% vs equal125.00% (+1.79pt)
  - B900 127.38% (+2.38pt)
  - B1200 127.68% (+2.68pt)
- ALL:
  - B600 **148.53%** / profit48,040 / maxDD6,390
  - B900 **155.14%** / profit81,880 / maxDD11,150
  - B1200 **158.44%** / profit115,720 / maxDD15,950
- target rank構成 ALL: rank1=9R / rank2=71R / rank3=85R。ほぼrank2/3を動的に選ぶ。
- TOP plateauは各budget 7 cellsで同一DEV ROI:
  - alpha 0〜.25 / beta .5〜1.5。
  - 最高オッズ順位が変わらない範囲で同じ配分になるため。
- true LOMO再選定は不安定:
  - holdout Feb/Junはequal超え
  - Mar/Apr/Mayはequal割れ、特にMarで大幅悪化。
  - よって「alpha/beta最適化」をproduction化する根拠は弱い。
- 一方、固定した単純 highest-odds rule はDEV5月中4月でequal非劣化、SUPPORT合計もequal超え。
- risk-adjusted private check（同じfrozen165R）:
  - B400 ALL ROI138.61%, maxDD3,430
  - B500 144.56%, maxDD4,910
  - B600 148.53%, maxDD6,390
  - B900 155.14%, maxDD11,150
  - B1200 158.44%, maxDD15,950
  - profit/maxDDはB500〜600近辺が良く、budget増ほどROIは上がるがdrawdownも急増。
- production/LIVE stakingは未変更。

## BEFORE — v372 simple highest-odds staking / gate audit
- 目的: v371の複雑チューニングを捨て、「formal3点の最高オッズへ追加stake」の単純買い方を固定監査する。
- frozen input: v370 Artifact `10553791049/race_inputs.csv`。
- 基本:
  - 全165R購入
  - formal3点は変更しない
  - 各3点100円を必ず購入
  - 追加stakeのみ最高closing-odds ticketへ。
- extra stake grid: +100 / +200 / +300 / +400 / +500 / +600 / +900円。
- no-gate（全Rで追加）を主baseline。
- さらにDEVだけで条件付き追加を研究:
  - target highest odds max 8/10/12/15/20/∞
  - odds ratio(top/2nd) max 1.4/1.6/2.0/∞
  - formal3点 combined odds max 1.8/2.0/2.2/2.5/∞
  - min active 20R
  - DEV月3/5以上でequal非劣化をrobust条件。
- SUPPORT Jul-Augは選定に使わない。
- true LOMOでgate再選定の安定性も確認。
- 評価: ROI/profit/maxDD/profit÷maxDD/月別、active R、target hit。
- closing oddsはhistorical最終表示proxyであり、LIVEでは直前current odds順位へ置換する前提。production変更なし。


## AFTER — v378 overlay内 3点資金配分 audit
- Run `35360135917` / Job `105649077585` success / Artifact `10554227933` / digest `sha256:7aac075cd5db1c40a8f3ab94e6449ad27c3dfe9438b7ffd16e82b87a766d2a30`。
- baseline = current EITHER 2x shadow:
  - overlay36Rを200/200/200、それ以外100/100/100
  - stake60,300 / return81,340 / profit+21,040 / ROI134.892%。
- overlay36R hit rank:
  - rank1 9/21 hit / return6,210
  - rank2 5/21 / return5,360
  - rank3 7/21 / return6,070
- EITHER一括weightsは不安定:
  - DEV raw 1:4:1 -> support ROI100%、ALL ROI132.31%でbaseline未満
  - robust 1:3:2 -> ALL133.48%でbaseline未満。
- FIVE6だけreweight:
  - raw1:4:1 ALL138.82%だがsupport102.95%で大幅悪化
  - robust1:3:2 ALL136.45%だがsupport122.48%、不安定。
- **WALL3だけreweight 1:1:4**:
  - DEV ROI143.82%（baseline134.22%）
  - SUPPORT ROI135.14%（baseline138.10%、ただしsupport WALL3は1Rのみ）
  - ALL ROI **142.305%**
  - stake60,300固定 / profit **+25,510**
  - baseline EITHER2x比 +7.41pp / +4,470円。
- WALL3 fixed/reselected LOMO:
  - Feb 0 / Mar0 / Apr+21.28pp / May+6.79pp / Jun+9.92pp
  - 5/5 holdoutで非悪化、毎回1:1:4が選ばれた。
- WALL3 category rank:
  - ALL 11R / 7hit: rank1=3, rank2=1, rank3=3
  - DEV 10R / 6hit: rank1=2, rank2=1, rank3=3
  - rank3払戻2,660 vs rank1 2,310 vs rank2 520。
- conclusion: overlay全体/rank2厚めは不安定。WALL3時のみrank3厚めは有望だがsupport1Rのため独立拡大監査が必要。
- production/official stake/shadow stake unchanged / September outcomes unread / AUDIT_OK=true。

## BEFORE — v379 fixed WALL3 rank3 overweight expanded robustness
- v378でDEV選定された自然な固定ruleを**再チューニングなし**で監査:
  - non-overlay: 100/100/100
  - five6-only: 200/200/200
  - wall3（BOTH含む）: **100/100/400**
- current EITHER2x equal shadow（overlay全て200/200/200）と総stakeは各universeで同額。
- 使用入力: v374 Artifact `10548879270` rows_LIVE165 / H078_M375 / H0775_M375 / H0775_M350 / PROD276。
- 評価:
  - 5 universes all/dev/support
  - LIVE165 fixed month LOO
  - LIVE165 all month subsets size>=4
  - env=.05 chain disjoint added bands
  - WALL3 hit-rank distribution by universe
- parameter searchなし。support結果でrule変更しない。
- 目的: rank3厚めがcurrent165固有でなく、拡大母集団でもbaseline EITHER2x equalに非劣化か確認。
- 2026-09 outcomes/payouts unread。LIVE shadowはv377 EITHER2x equalのまま維持。


## AFTER — v379 fixed WALL3 rank3 overweight expanded robustness
- Run `35360355015` / Job `105649804384` success / Artifact `10554033465` / digest `sha256:297304a0960345f388609ad989f817f2c573c55b3bcdb3da6d9e2100c8f70ce2`。
- fixed rule（再チューニングなし）:
  - non-overlay 100/100/100
  - five6-only 200/200/200
  - wall3（BOTH含む） **100/100/400**
- baseline = current EITHER2x equal shadow（overlay全部200/200/200）。
- LIVE165:
  - stakeは両方60,300円で完全同一
  - baseline return81,340 / profit+21,040 / ROI134.892%
  - candidate return85,810 / profit**+25,510** / ROI**142.305%**
  - +4,470円 / +7.41pp。
- 5 expanded universes ALLで全てbaseline以上:
  - LIVE165 +7.41pp
  - H078_M375 +3.15pp
  - H0775_M375 +3.80pp
  - H0775_M350 +4.12pp
  - PROD276 +4.40pp。
- SUPPORT:
  - LIVE/H078/PRODはwall3 supportサンプルが1〜2Rで少なく小幅悪化
  - H0775_M375/H0775_M350は改善。
- fixed LIVE leave-one-month-out（rule再選定なし）7/7非悪化。
- 4か月以上の全month subset:
  - nonnegative 98.44%
  - positive 98.44%
  - median +8.02pp
  - worst -1.52pp。
- disjoint bands:
  - LIVE165 +7.41pp
  - +71R帯 -7.06pp（唯一明確な弱帯）
  - +33R帯 +8.25pp
  - +45R帯 +6.03pp
  - 3/4帯非悪化。
- wall3 rank distributionもexpandedでrank3優位が持続:
  - LIVE165: rank3 4hit / return3,650（rank1 3hit/2,310、rank2 1hit/520）
  - H0775_M350: rank3 6hit/4,640（rank1 4hit/3,490、rank2 2hit/1,120）
  - PROD276: rank3 7hit/4,980（rank1 5hit/4,010、rank2 3hit/1,510）。
- parameter searchなし / total stake identical / September unread / production unchanged / AUDIT_OK=true。
- 結論: WALL3時rank3厚めはかなり有望。ただしLIVE165 wall3対象12Rと小標本、+71R disjoint帯で悪化があるため正式stake変更前に時系列risk監査を行う。

## BEFORE — v380 WALL3 rank3 overweight bankroll/risk audit
- v379 fixed candidateを再最適化せず監査。
- 比較:
  - baseline current EITHER2x equal shadow
  - candidate wall3=100/100/400, five6-only=200/200/200, none=100/100/100
- 両者total stakeは各raceで同一。
- LIVE165 race_code時系列順で:
  - total ROI/profit
  - max drawdown円
  - drawdown race span
  - longest losing streak
  - worst10R / 20R rolling profit
  - monthly profit std / worst month
  - peak-to-trough
- wall3対象12Rだけのincremental cashflowも別監査。
- expanded universesでは総DDとprofit/DD比も比較。
- parameter searchなし。official/shadow stakeは変更しない。


## AFTER — v371 dynamic closing-odds staking robustness
- 修正版 Run `35359641195` / Job `105647445277` success / Artifact `10553427745` / digest `sha256:d2a6fe568f57d95a8eef5dc96b23b662d89ab5af785e1b51dec5fbee7a055463`。
- DEV raw/robustは全budgetで同一: TOP / alpha=0 / beta=.5（実質odds順位中心）。
- ALL ROI:
  - B600 148.53%
  - B900 155.14%
  - B1200 158.44%
  - supportもequal比わずかにプラス。
- ただしtrue LOMO再選定は各budgetとも5 holdout月中 **2月のみ明確プラス**、Mar/Apr/Mayが大幅悪化。
  - B600 delta pp: +35.56 / -49.62 / -15.51 / -2.36 / +33.89
  - B900: +47.41 / -66.15 / -20.67 / -3.15 / +45.19
  - B1200: +53.33 / -74.42 / -23.26 / -3.55 / +50.83
- 結論: closing odds最終値での3点内集中はhistorical ROIは強いがmonth generalizationが弱い。production/LIVE採用しない。closing odds自体も発注前に完全同値を保証しないproxy。
- September unread / production unchanged / AUDIT_OK=true。

## AFTER — v380 WALL3 rank3 overweight bankroll/risk
- Run `35360578646` / Job `105650549805` success / Artifact `10554293618` / digest `sha256:c26398fe195d79aaf5ba3bccff22a75a1e847980172c92e29160074ddef906aa`。
- fixed candidate:
  - wall3: 100/100/400
  - five6-only: 200/200/200
  - non-overlay: 100/100/100
- current EITHER2x equal baselineと**各race total stake同一**。
- LIVE165:
  - baseline stake60,300 / return81,340 / profit+21,040 / ROI134.892%
  - candidate stake60,300 / return85,810 / profit**+25,510** / ROI**142.305%**
  - +4,470円 / +7.41pp。
- risk:
  - maxDD 3,320 -> **3,320（不変）**
  - DD span19 ->19
  - longest losing streak7 ->7
  - worst10R -2,760 -> -2,760
  - worst20R -2,670 -> -2,670
  - profit/maxDD 6.34 -> **7.68**
  - monthly profit stdは4,021 ->4,634へ増えるが、worst monthは -1,740 -> **-640**。
- WALL3 12R incremental:
  - rank1 hit3 / rank2 hit1 / rank3 hit4 / miss4
  - positive delta4R / negative4R / zero4R
  - total +4,470
  - worst single -1,430 / best +3,140。
- expanded risk:
  - H078 / H0775_M375: maxDD不変
  - H0775_M350: +10円のみ
  - PROD276: maxDD 5,000 -> **4,490**。
- parameter searchなし / total stake identical / September unread / production unchanged / AUDIT_OK=true。
- conclusion: forward shadowへ進める価値あり。正式stake変更はまだしない。

## BEFORE — v381 LIVE wall3 rank3 allocation shadow
- official stakesは引き続き100/100/100。
- existing stake shadow v377も維持:
  - wall3 OR five6時 200/200/200
  - otherwise100/100/100。
- 新しい第二研究shadowを追加:
  - wall3_ticket_applied=true: **100/100/400**
  - wall3=false & five6=true: 200/200/200
  - overlayなし:100/100/100
  - BOTH時はwall3 ruleを優先。
- 新規fieldは allocation shadow専用にし、既存stake_shadowの意味を変えない。
- 保存済みcausal inputで wall3-only / five6-only / no-overlay を回帰。
- formal tickets / official stake / existing shadow / HEAD gatesは変更しない。
- 2026-09 outcomes/payouts unread。


## BEFORE — v370 current formal3 odds-aware dynamic staking
- ユーザー要望: 買い方研究の続行。
- v369結論: ticket rank固定ウェイトはDEV/SUPPORTで反転し頑健でない。
- repo内に `data/official_closing_odds3t/YYYY/MM/DD.csv` のBOAT RACE公式締切3連単オッズ履歴が存在することを確認。
- v340で公式closing odds / combined odds / Dutch実装済みだが旧production276R・旧買い目用。今回は**現正式165R / wall3+5>6後の3点**へ再監査する。
- レース選定・買い目3点は固定。研究対象は資金配分のみ。
- realized returnは公式結果の100円払戻を使い、stake配分の意思決定には締切オッズ＋モデル確率のみを使う。
- 研究1: fixed-total allocation（全レース同額）
  - 600円/R（6 units）・1000円/R（10 units）、各ticket最低100円。
  - equal
  - odds Dutch（stake ∝ 1/odds）
  - model probability power
  - odds/model power grid: score = pair_prob^a * odds^b
- 研究2: selective boost
  - 毎R baseline 100/100/100を必ず買う。
  - formal3の中で model_prob*closing_odds（value score）が最も高い1点だけ、閾値を超えた時に+100〜+500円。
  - value threshold / top-vs-second marginをgrid。
- 選定: Feb-Jun DEVのみ。Jul-Aug SUPPORTは選定に使わない。
- 評価:
  - ROI / profit / total stake
  - SUPPORT ROI
  - 月別
  - odds coverage
  - stake distribution
  - baseline 100/100/100 = 165R / 87hit / stake49,500 / return63,700 / ROI128.687%
- race数・hit率は資金配分だけなので原則不変。
- production/LIVE買い目は変更しない。2026-09結果/払戻は読まない。


## v370 initial failure — closing odds repo coverage不足
- Run `35361383408` / Job `105653205939` failure。
- 原因: current165Rのうちrepo内 `data/official_closing_odds3t` coverageが144/165。missing21RはすべてJul/Aug SUPPORT:
  `202607231508, 202607282409, 202608012209, 202608030402, 202608041001, 202608061001, 202608061704, 202608081508, 202608100901, 202608112101, 202608112301, 202608112311, 202608150110, 202608171508, 202608180509, 202608181110, 202608202301, 202608210402, 202608212407, 202608242010, 202608301612`。
- DEV Feb-Junのofficial closing oddsはrepo内でcoverage済み。
- 修正: repo CSVをfirst sourceとし、missingのみv340と同じBOAT RACE公式 `odds3t` closing pageから取得するfallbackを追加。
- 結果/払戻からのodds逆算は禁止。fallbackもpre-race market informationのみ。
- 研究grid・DEV選定条件は変更しない。


## AFTER — v370 odds-aware dynamic staking
- Run `35361600631` / Job `105653943807` completed success / Artifact `10554711567` / head `e88e8257fad713ddc17d25ab1d62d1d097d2ea79`。
- official closing odds coverage 165/165:
  - repo CSV 144R
  - BOAT RACE official web fallback 21R（全Jul/Aug）
  - outcome/payoutからのodds逆算なし。
- formal equal100 baseline完全再現:
  - 87/165 / stake49,500 / return63,700 / profit+14,200 / ROI128.687%。
- named fixed-total:
  - Dutch 600円/R: ALL ROI122.84%（悪化）
  - MODEL_P 600円/R: 128.14%（ほぼ同等）
  - VALUE p*odds 600円/R: **130.44%**、DEV131.93%、SUPPORT123.15%
  - VALUE p*odds 1000円/R: ALL134.30%、DEV136.68%、SUPPORT122.64%（support悪化）
- raw DEV best fixed powerは高odds寄せ（a=0,b=1）:
  - 600円/R ALL131.23%だが SUPPORT121.13%
  - 1000円/R ALL137.19%だが SUPPORT119.14%
  - DEV最適をそのまま採用するのはoverfit傾向。
- selective p*odds boost DEV-selected:
  - value>=1.4 / margin>=.1 / +500円
  - DEV ROI164.15%、ALL156.07%だが SUPPORT111.70%、support boost2Rとも外れ。
  - 明確に不安定なので不採用。
- grid診断では confidence-weighted value `score = p^2 * odds` が有望:
  - 900円/R: DEV131.74 / SUPPORT126.83 / ALL130.90%
  - 1200円/R: DEV132.55 / SUPPORT132.53 / ALL132.55%
  - 1500円/R: DEV132.88 / SUPPORT131.02 / ALL132.56%
  - 2400円/R: DEV133.19 / SUPPORT128.60 / ALL132.41%
  - 3000円/R: DEV134.17 / SUPPORT128.36 / ALL133.18%
- `p^2*odds` はEV=`p*odds`にconfidence pをもう1回掛けた理論的なrisk-adjusted value。SUPPORTを見て後付け選定するのではなく、v371でpre-specified strategyとしてbudget感度を正式監査する。
- September outcomes unread / production unchanged / AUDIT_OK=true。

## BEFORE — v371 confidence-weighted value staking robustness
- current formal3買い目は固定、レース165R固定。
- pre-specified staking formulasを比較:
  1) EQUAL
  2) DUTCH = odds^-1
  3) MODEL = p
  4) EV = p*odds
  5) CONF_EV = p^2*odds
  6) SOFT_EV = p*sqrt(odds)
- 100円unit / 各ticket最低100円。
- total budgetは3で割り切れる `600/900/1200/1500/1800/2100/2400/3000円/R` を比較し、equal配分が完全に均等になるようにする。
- 主要仮説: CONF_EVは高オッズ追随を抑えつつvalueを厚くでき、DEV/SUPPORT双方でequal ROIを上回る。
- 評価:
  - DEV / SUPPORT / ALL ROI, profit
  - 月別equal差
  - budget感度
  - 各rank平均stake
  - max/min stake distribution
- strategy式はSUPPORT結果を見る前に固定。budgetは採用判断時に安定plateauを見る。
- production/LIVE ticket内容は変更しない。September outcomes unread。


## AFTER — v371 confidence-weighted value staking
- Run `35362589423` / Job `105657218973` completed success / Artifact `10555121550` / head `88bd494b88d2c4da9dca580ac6adfc861cc49170`。
- pre-specified `CONF_EV = pair_prob^2 * closing_odds` をbudget 600〜3000円/Rで感度監査。
- equalは各budgetが3で割り切れるため完全均等、ROIはformal baselineと同じ。
- CONF_EV robust budgets（DEV/SUPPORT双方でequalよりROI改善）:
  - **900, 1200, 1500, 1800, 2100, 2400, 3000円/R**
  - 600円のみSUPPORTで-1.85pt。
- 900円/R:
  - DEV131.74%, SUPPORT126.83%, ALL130.90%
  - equal比 +2.30 / +1.83 / +2.22pt。
- 1200円/R:
  - DEV **132.55%**
  - SUPPORT **132.53%**
  - ALL **132.55%**
  - equal比 +3.11 / +7.53 / +3.86pt
  - average units rank1/2/3 = 3.94 / 4.45 / 3.61（100円unit）。
- 1500円/R: ALL132.56%, SUPPORT131.02%
- 1800円/R: ALL132.68%, SUPPORT125.63%
- 2400円/R: ALL132.41%, SUPPORT128.60%
- 3000円/R: ALL133.18%, SUPPORT128.36%
- 1200円月別equal差: Feb +23.28pt, Mar -1.99, Apr -1.97, May -3.59, Jun +9.77, Jul +7.50, Aug +7.54。
- 結論: `p^2*odds` は予算900円以上で広いbudget plateauがあり、単純Dutchより明確に頑健。ただし元の300円/Rから資金量を3〜10倍にするため、ROI改善と同時に資金リスクも増える。
- production/stake policyは未変更。September outcomes unread / AUDIT_OK=true。

## BEFORE — v372 same-300-yen soft Dutch / odds-spread reallocation
- 目的: **総投資300円/Rを増やさず**ROI改善できるか。
- current formal3は100/100/100。
- pre-race closing oddsだけで次の単純ルールを監査:
  - selected3の `max_odds / min_odds >= threshold` の時、
  - 最長オッズticketを100円→0円、
  - 最短オッズticketを100円→200円、
  - 中間は100円維持。
  - 合計300円/R固定。
- threshold grid 2.5〜6.0（0.1刻み）。
- DEV Feb-Junのみでthreshold選定:
  1) formal hitを1件も落とさないことを最優先
  2) DEV ROI最大
  3) 変更Rが少ない方
- SUPPORT Jul-Augは完全holdout。
- 評価:
  - hit / lost hit / ROI / profit
  - 月別
  - threshold plateau
  - どのrankを削ってどのrankへ増額したか
  - omitted ticketが実際に当たったケース
- ローカル診断:
  - threshold3.5: DEV 71hit維持 / ROI135.52%, SUPPORT16hit維持 / ROI128.69%, ALL87hit維持 / ROI134.36%
  - threshold3.5〜4.8でDEV/SUPPORTともhit loss0の帯を確認。
- 結果を見てthresholdを選ばないよう、正式v372ではDEV-only selectionを固定してからSUPPORT評価。
- production/LIVE stakeは変更しない。September outcomes unread。


## AFTER — v372 same-300-yen soft Dutch
- Run `35363056059` / Job `105658776084` completed success / Artifact `10554908463` / head `840de0c9623e3680c8ca70cedf0aa2d905c83f90`。
- DEV-only selected threshold = **max_odds / min_odds >= 3.5**。
- rule:
  - 最長オッズticket 100円→0円
  - 最短オッズticket 100円→200円
  - 中間100円
  - 合計300円/R固定。
- DEV:
  - 137R / 71hit維持 / lost hit0
  - changed22R / doubled winning ticket6R
  - return53,200→55,700
  - ROI129.44→**135.52%** (+6.08pt)
- SUPPORT:
  - 28R / 16hit維持 / lost hit0
  - changed3R / doubled win1R
  - return10,500→10,810
  - ROI125.00→**128.69%** (+3.69pt)
- ALL:
  - **87/165 hit完全維持**
  - changed25R / lost hit0 / doubled win7R
  - stake49,500据え置き
  - return63,700→**66,510**
  - profit14,200→**17,010**
  - ROI128.687→**134.364%** (+5.68pt)
- 削減元rank: rank1=0R / rank2=13R / rank3=12R。第1買い目は1度も削らない。
- 増額先rank: rank1=14R / rank2=4R / rank3=7R。
- threshold 3.5〜6.0の**26 cellsすべてDEV/SUPPORT lost hit=0**。
  - 3.5がDEV ROI最大。
  - 3.6-3.7でもALL ROI133.52%、lost0。
  - 4.0-4.8でもALL130.08%、lost0。
- 月別selected3.5:
  - Feb ±0
  - Mar +9.49pt
  - Apr +3.84
  - May +10.31
  - Jun +4.24
  - Jul ±0
  - Aug +5.44
  - 全月hit loss0、ROI非悪化。
- production/stake policy未変更。September outcomes unread / AUDIT_OK=true。

## BEFORE — v373 soft-Dutch LOMO robustness
- v372 threshold selectionの月依存性を監査。
- Feb-Jun DEVで各holdout月を1つ外し、残り4月だけで:
  1) lost hit=0のthresholdを抽出
  2) ROI最大
  3) 同率なら変更R少ない
  でthresholdを再選定。
- 選んだthresholdをholdout月へ適用し、hit loss / ROI差を見る。
- fixed threshold3.5についてもFeb-Aug各月を再確認。
- promotion候補条件:
  - LOMO 5/5月 lost hit=0
  - LOMO total ROI非悪化
  - SUPPORT lost0
  - threshold近傍plateau
- production/LIVE stakeは変更しない。September outcomes unread。


## AFTER — v373 soft-Dutch LOMO
- Run `35363316170` / Job `105659633519` completed success / Artifact `10555323741` / head `ac1d49c09d8c69727779528565ab88e08e9f0733`。
- 各DEV月holdout再選定:
  - Feb: threshold3.5 / hit loss0 / ROI差0
  - Mar: 3.5 / loss0 / +9.49pt
  - Apr: 3.5 / loss0 / +3.84pt
  - May: 3.5 / loss0 / +10.31pt
  - Jun: 3.7 / loss0 / +0
- LOMO 5/5月 lost hit=0、5/5月 ROI非悪化。
- LOMO aggregate DEV:
  - baseline ROI129.44%
  - policy ROI **134.50%**
  - +5.06pt、stake同額。
- fixed3.5もFeb-Aug全7月 lost hit=0、全月ROI非悪化。
- SUPPORT fixed3.5: ROI125.00→128.69%、loss0。
- threshold選定の月依存性は小さく、3.5 coreが4/5 LOMOで再選択、残りも3.7。
- production/stake policy未変更。September outcomes unread / AUDIT_OK=true。

## BEFORE — v374 soft-Dutch expanded-universe generalization
- fixed threshold **3.5** を再最適化せず、v360 preparedの拡大母集団へ適用。
- universes:
  - LIVE165
  - H078_M375 236R
  - H0775_M375 269R
  - H0775_M350 313R
  - PROD276
- 各raceではcurrent formal ticket machinery相当（opponentCore後 + wall3 + 5>6）から3点を作り、official closing odds比だけで300円配分を変更。
- ルール固定: max/min odds >=3.5なら最長0 / 最短200 / 中間100。
- 評価:
  - exact3 baseline vs policy
  - lost hit
  - equal ROI vs policy ROI
  - disjoint nested bands（165外71R / 次33R / 次44R）の独立成績
- odds source: repo official closing CSV first、missingのみBOAT RACE公式web fallback。outcomeからodds逆算なし。
- v372/v373で選んだthresholdは固定し、拡大母集団結果を選定には使わない。
- production/LIVE stake未変更。September outcomes unread。


## BEFORE — v370 current formal3 dynamic odds staking
- ユーザー指示: 買い方研究を継続。
- v369で固定ticket-rankウェイトはDEV/SUPPORTで順位傾向が逆転し、formalは100/100/100維持。
- 過去v340を再確認:
  - BOAT RACE公式締切3連単オッズを履歴保存済み。
  - 旧276Rでは低合成オッズskip中心のadaptive DutchがROI93.03%→115.53%。
  - 今回はユーザー意図に合わせ**レース選別は行わず165R全購入固定**。v340のofficial odds / Dutch実装だけ再利用する。
- 現formal買い目はwall3→5>6後の3点を固定。買い目自体は変更しない。
- 資金配分を比較するため、各レース総額600円（6 units、100円単位、各3点最低100円）に統一:
  1) EQUAL: 2/2/2 units
  2) DUTCH: 締切オッズ逆数で払戻均等化
  3) MODEL: formal pair probability比例
  4) EDGE: model pair probability × closing odds のedgeに応じて追加3 units配分
  5) HYBRID_SCORE: p^a × odds^b のscoreで追加3 units配分。a/bはDEV Feb-Junでgrid選択。
- ROI比較は全方式同一stake 600円/Rなので純粋な配分差。
- DEVでパラメータ選択、SUPPORT Jul-Augは選定に使わない。
- official closing odds coverage 165/165を要求。欠損があれば採用判定しない。
- September outcomes/payoutsは読まない。production/LIVEは変更しない。


## BEFORE — v382 fixed soft-Dutch + WALL3 allocation combined audit
- 買い方研究の継続。
- 新規パラメータ探索は行わない。
- 固定済み2ルールを合成:
  1) v372-v374 soft Dutch threshold=3.5
     - odds ratio max/min>=3.5時、最長odds 0 / 最短odds 200 / 中間100
     - total300円、LIVE165 87hit維持 / ROI134.364%
     - expanded 5 universes + 全disjoint bandsでlost hit0、ROI改善。
  2) v379-v380 WALL3 allocation
     - WALL3時100/100/400
     - five6-only時200/200/200
     - none時100/100/100
     - total stakeはEITHER2x baselineとrace-by-race同一
     - LIVE165 ROI142.305%、maxDD非悪化。
- v382 fixed combined rules:
  - WALL3（BOTH含む）: **100/100/400を最優先**
  - five6-only:
    - soft Dutch非発火: 200/200/200
    - soft Dutch発火: shortest/middle/longest oddsへ **400/200/0**（v372比率を2x）
  - NONE:
    - soft Dutch非発火:100/100/100
    - soft Dutch発火:200/100/0
- 比較:
  - official 100/100/100
  - soft Dutch only
  - v379 allocation only
  - v382 combined
- v379 allocationとv382 combinedは**各race total stake完全同一**にして、純粋な配分差を比較。
- 既存Artifactのみ使用:
  - overlay rows: v374 Artifact 10548879270
  - soft Dutch expanded rows: v374-soft Artifact 10555204782
- 評価:
  - 5 universes ALL
  - DEV/SUPPORT
  - disjoint bands
  - LIVE165月別
  - time-series maxDD / worst10R / worst20R / losing streak
  - lost formal hit
- support/expanded結果でルール変更しない。
- production/official stake/shadows変更なし。September outcomes unread。


## AFTER — v382 fixed soft-Dutch + WALL3 allocation combined
- Run `35364692971` / Job `105664169322` success / Artifact `10555891309` / digest `sha256:b6a71f9ded39c67799f29e6e6a4abb5d2c721ca29a94763beccf214ccfa9e67a`。
- 新規parameter searchなし。v372 threshold3.5 + v379 WALL3 1:1:4を固定合成。
- LIVE165:
  - official 100/100/100: stake49,500 / return63,700 / profit+14,200 / ROI128.687%
  - soft only: stake49,500 / return66,510 / profit+17,010 / ROI134.364%
  - v379 alloc only: stake60,300 / return85,810 / profit+25,510 / ROI142.305%
  - **combined: stake60,300 / return88,530 / profit+28,230 / ROI146.816%**
  - alloc比 **+4.51pp / +2,720円**、stake完全同一。
  - hit 87維持 / lost hit0。
- DEV: alloc143.82 -> combined149.28% (+5.46pp)。
- SUPPORT: alloc=combined135.14%、非悪化。
- expanded 5 universes ALLすべてalloc以上:
  - LIVE +4.51pp
  - H078 +4.95
  - H0775_M375 +5.01
  - H0775_M350 +5.11
  - PROD276 +4.51。
- disjoint 4/4 bands alloc以上:
  - LIVE +4.51pp
  - +71R +5.99
  - +33R +5.40
  - +45R +5.64。
- risk LIVE165:
  - maxDD 3,320円（v379 allocと不変）
  - worst10R / worst20R / losing streakも不変
  - worst month -640 -> **+180**
  - profit/maxDD 7.68 -> **8.50**。
- interaction: soft changed25R、うちwall3 4R（wall3 rule優先）、five6-only 3R、none18R。
- production/official stake/shadows未変更 / September unread / AUDIT_OK=true。
- 重要制約: soft Dutch decisionはofficial closing oddsを使用。実LIVE購入時にclosing値は未確定なので、正式採用前にpre-close odds drift robustnessが必要。

## BEFORE — v383 soft-Dutch odds-drift stress
- v382 combined ruleを固定し、threshold3.5 / WALL3 1:1:4 / five6-only 2x soft / none softを変更しない。
- historical pre-close snapshotはrepoに保存されていないため、closing oddsに対するrelative drift stressを実施。
- stress幅: 各formal ticket oddsに独立 ±5% / ±10% / ±15% / ±20%。
- deterministic tests:
  1) 各raceで8 corner perturbations（各ticket x(1±d)）を全列挙し、soft allocationが全cornerで不変なrace割合を計測。
  2) fixed seed Monte Carloで各delta 1000 simulations、各race/ticket独立uniform[1-d,1+d]。
- WALL3 raceはodds非依存1:1:4なので完全固定。odds stressはfive6-only/noneのsoft decisionだけ。
- 各simulationでtotal stakeはv382と同じ60,300円固定。
- 評価:
  - ROI mean/median/p05/p95/min/max
  - v379 alloc ROI142.305%を上回るsimulation比率
  - official ROI128.687%を上回る比率
  - closing-based v382 ROI146.816%との差
  - decision stability率
- これはreal pre-close distributionの予測ではなく、closing odds依存性のstress test。結果を見てthreshold変更しない。
- production/LIVE stake変更なし。September outcomes unread。


## AFTER — v383 soft-Dutch odds-drift stress
- Run `35364966275` / Job `105665061552` success / Artifact `10555697457` / digest `sha256:c2f143b67a001d12a45729df11510c66d965b49fede66e62031c108a0c5e0533`。
- fixed combined closing-odds sentinel:
  - stake60,300 / return88,530 / ROI146.816%。
- closing odds各ticket独立relative drift stress、threshold3.5固定、1000 simulations/delta:
  - ±5%:
    - allocation fully stable 149/165=90.3%
    - mean ROI145.21%
    - p05 141.94%
    - v379 alloc ROI142.31%以上 88.8%
    - official ROI128.69%以上 100%
  - ±10%:
    - stable 137/165=83.0%
    - mean ROI143.37%
    - p05 137.13%
    - alloc以上67.4%
    - official以上100%
  - ±15%:
    - stable 123/165=74.5%
    - mean ROI141.93%
    - p05 134.23%
    - alloc以上52.5%
    - official以上100%
  - ±20%:
    - stable108/165=65.5%
    - mean ROI140.95%
    - p05133.17%
    - alloc以上42.8%
    - official以上99.9%
- 解釈:
  - closing-based146.82%は当然best寄りだが、±10〜20%程度のrelative odds driftを入れても平均ROIは141〜143%台。
  - downside p05でも133〜137%台でofficial均等128.69%より上。
  - ただしこれはreal pre-close odds distributionの実測ではなくstress test。closing odds完全同値が買付時に利用できるとは扱わない。
- production/official stake/shadows変更なし / September outcomes unread / AUDIT_OK=true。

## BEFORE — current-odds allocation shadow plumbing
- 目的: historical closing-odds研究を、実LIVE購入時に取得可能なcurrent official oddsでprospective shadow観測できる形へ繋ぐ。
- formal ticketsは変更しない。
- official stakesも100/100/100のまま。
- current finalizerの既存stake shadows:
  - EITHER2x equal
  - WALL3 rank3 allocation
  を維持。
- 追加候補shadow:
  - current odds比 max/min>=3.5
  - WALL3時は1:1:4優先
  - five6-onlyはsoft units x2
  - noneはsoft units
- まず既存1head LIVE workflow内のodds fetch位置とJSON入出力を監査し、結果/払戻endpointへ触れず追加可能か確認する。
- September outcomes unread。


## AFTER — current-odds allocation shadow plumbing 完了
- profile commit `5b896f73c1b119cab80880fc59318a6d4b3227f3`
  - `CURRENT_ODDS_ALLOC_SHADOW_PROFILE_NAME = 1HEAD_CURRENT_ODDS_ALLOC_SHADOW_V382_SOFT35_WALL3_114`
  - soft odds ratio threshold=3.5 / research_only=true。
- current-odds shadow script commit `5086d9ff36138dd123c78e76ef8f614b4b24813e`
  - `run_1head_v351_live_current_odds_shadow.py`
  - formal LIVE JSON確定後に BOAT RACE official current odds3t だけ取得。
  - result/payout endpointは使用しない。
  - WALL3:100/100/400優先。
  - FIVE6-only: soft発火時2x soft、非発火200/200/200。
  - NONE: soft発火時200/100/0系、非発火100/100/100。
  - formal tickets / official stakesは変更しない。
- v384 regression:
  - script commit `8f8802084b2a7b5949b3a08732952b9963518670`
  - workflow commit `e25e108fb59258fa89aa930df5c3a9266162622f`
  - Run `35365441930` / Job `105666647818` success / Artifact `10556525324`
  - digest `sha256:47c86692208263673081bca95ca8df162e6ddedae51cf9c0632362090b227406`
  - synthetic 4 cases all pass:
    - WALL3 -> 100/100/400
    - FIVE6-only soft -> 400/200/0
    - NONE soft -> 200/100/0
    - NONE no-soft -> 100/100/100
  - result_or_payout_used=false / AUDIT_OK=true。
- LIVE workflow plumbing:
  - manual workflow commit `b3ed27542281c461469ebce2b90d1578f280cc39`
  - chat workflow commit `5677a4f71109479779bca8dfaf1425a5dafea5e6`
  - formal finalize成功後にcurrent odds shadowを取得。
  - `continue-on-error: true` なのでオッズshadow取得失敗で正式判定を失敗扱いにしない。
  - artifactへcurrent odds shadow JSONを追加。
- formal regression after profile extension:
  - v356 Run `35365352106` success
  - v364 Run `35365352148` success
  - v377 Run `35365352095` success
  - formal wall3 / five6 tickets / existing stake shadowにdriftなし。
- 現運用:
  - **正式stakeは100/100/100のまま**。
  - existing EITHER2x shadow + WALL3 allocation shadowも維持。
  - current-odds combined shadowを追加しただけで、formal化していない。
- 今後ユーザーが「判別して」と依頼したLIVEでは、formal判定artifactに加え、その時点のofficial oddsでcurrent-odds allocation shadowを確認可能。
- September outcomes unread / production unchanged。


## BEFORE — v385 current-odds safety-margin audit
- 買い方研究をv384のcurrent-odds shadowから継続。
- 現候補v382:
  - WALL3は100/100/400固定
  - five6-onlyはsoft発火時400/200/0、非発火200/200/200
  - NONEはsoft発火時200/100/0、非発火100/100/100
  - soft発火閾値 = selected3 odds max/min >= 3.5
  - historical closing oddsでLIVE165 ROI146.816% / stake60,300 / profit+28,230。
- v383でclosing odds relative drift ±5/10/15/20% stressは通したが、実LIVEで3.5ぎりぎり発火はcurrent→closeで反転しやすい。
- v385では**パラメータ再最適化せず**、3.5 coreに対して数学的なsafety bufferだけを導出:
  - relative odds drift ±d の時、ratio worst shrink factor=(1-d)/(1+d)
  - closingで3.5を保証するcurrent ratio閾値 = 3.5*(1+d)/(1-d)
  - d=5/10/15/20%を評価。
- v382 Artifact 10555891309のrace-level
  - live_alloc_detail.csv（softなしv379配分）
  - live_combined_detail.csv（threshold3.5 combined）
  を再利用。
- WALL3はodds非依存なので常にalloc側とcombined側同一扱い。
- non-WALL3で closing odds ratio がcandidate threshold以上ならcombined配分、未満ならalloc配分へ戻す。
- 評価:
  - ALL / DEV / SUPPORT / 月別
  - changed R
  - ROI / profit
  - v379 alloc142.305%比
  - v382 closing146.816%比
  - worst month
- supportを見て閾値変更しない。これは「想定drift幅を選んだ時の機械的安全マージン」評価。
- production/official stakeは変更しない。current-odds shadowもresearch_onlyのまま。September outcomes unread。


## AFTER — v385 current-odds safety-margin audit
- Run `35367849832` / Job `105674519902` success / Artifact `10557427105` / digest `sha256:da066892fb55df97463c6d4ca28e28260cdc28626c4bf0bf1a31d721879a0fa1`。
- v382 closing-based core:
  - threshold3.5 / stake60,300 / return88,530 / profit+28,230 / ROI146.816%。
- v379 odds-independent allocation baseline:
  - stake60,300 / return85,810 / profit+25,510 / ROI142.305%。
- current->close relative drift ±d を想定した機械的安全閾値:
  - `T_safe = 3.5*(1+d)/(1-d)`, 実装値は0.1刻み切上げ。
- practical results LIVE165:
  - d=0% / T=3.5: soft21R / ROI146.816% / profit+28,230
  - d=5% / T=3.9: soft12R / ROI144.163% / profit+26,630
  - d=10% / T=4.3: soft7R / ROI142.935% / profit+25,890
  - d=15% / T=4.8: soft4R / ROI142.935% / profit+25,890
  - d=20% / T=5.3: soft2R / ROI142.305% / profit+25,510
- maxDDは全候補 **3,320円で不変**。worst10R=-2,760 / worst20R=-2,670も不変。
- SUPPORT ROIは全候補 **135.143%で不変**。
- 3.9はv379比+1.86pp、4.3/4.8は+0.63pp。5.3でv379と同値。
- 解釈:
  - 3.5のclosing optimumから安全側へ寄せてもROI改善の大半は残る。
  - **3.9〜4.3がcurrent oddsで使う安全マージン候補**。ただしsupport結果で閾値を選ばず、想定drift幅に応じて機械的に決める。
- production/official stake/current-odds shadow未変更 / September unread / AUDIT_OK=true。

## BEFORE — v386 expanded current-odds safety-margin audit
- v385の安全閾値を再最適化せず、拡大5母集団へ固定適用。
- data source:
  - v374 overlay Artifact `10548879270`
  - v374 soft-Dutch Artifact `10555204782`
- universes: LIVE165 / H078_M375 / H0775_M375 / H0775_M350 / PROD276。
- thresholds: 3.5 / 3.9 / 4.3 / 4.8 / 5.3（drift0/5/10/15/20%由来）。
- disjoint bandsも監査。
- Run `35368163224` 発火済み、現在queued。production変更なし。


## BEFORE — v370 current formal 3-ticket dynamic staking with official closing odds
- ユーザー要望: 買い方研究を継続。
- v369で固定rank配分はperiod反転が大きく、100/100/100均等をformal維持。
- 過去v340にBOAT RACE公式締切3連単オッズ276/276の履歴とDutch実装があるため再利用する。
- 重要: 今回はv340の「低合成オッズ見送り/買い目追加」は使わない。**現正式LIVE165Rを全件購入し、正式3点も固定**。
- 市場オッズはv340 sharded artifact:
  - shard0 `10329564703`
  - shard1 `10330810260`
  - shard2 `10330651756`
  - shard3 `10329684566`
  - shard4 `10330273057`
  - shard5 `10330357729`
  を結合。current LIVE165全件coverageを最初に監査する。不足分があればhistorical公式ページから補完し、coverage不足のまま比較しない。
- 現formal ticketsは v360 prepared Artifact `10539401122` + current wall3+5>6正式ロジックから再構成。baseline sentinel 87/165 / return63,700 / ROI128.687%を要求。
- 研究対象（全レース最低100円×3は維持）:
  1) equal 100/100/100 baseline
  2) fixed 600円/R odds-Dutch（逆オッズ）
  3) fixed 600円/R model-proportional
  4) fixed 600円/R value-proportional（model pair probability × closing odds）
  5) dynamic extra units: baseline300円に対し、pre-race market/model edgeが強い時だけ+100〜+300円を1〜3点へ追加
- dynamic gate候補:
  - combined odds
  - max ticket edge = p_head × pair_prob × odds
  - top3 normalized model-vs-market disagreement
  - rank probability concentration
- DEV Feb-Junのみでルール選定。SUPPORT Jul-Augはholdout。
- ROIは実払戻100円単位×購入unitで計算。closing oddsそのものをreturn計算には使わない。
- exact closing oddsは実運用で完全には先取りできないため、v370はまず**execution upper-bound / market-informed research**。正式LIVE採用は別途live snapshot再現が必要。
- 2026-09結果/払戻は読まない。production/LIVE ticketsは変更しない。


## AFTER — v370 current formal dynamic staking with closing odds
- Run `35377022445` / Job `105703985847` completed success / Artifact `10560443188` / digest `sha256:5bd74f3f2a0cb9386e2c3a7d3c209cfbc141f9afca8003b94bbea926632c5d2d`。
- closing odds coverage 165/165:
  - repo official CSV 144R
  - v340 shard fallback 20R
  - official page fetch 1R
- equal 600円/R（2:2:2）はformal baselineを完全再現:
  - 165R / return127,400 / stake99,000 / ROI128.687%
  - DEV129.44% / SUPPORT125.00%。
- DEV raw best = EDGE threshold .8:
  - DEV ROI143.75%
  - ALL ROI137.89%
  - しかし SUPPORT ROI109.23%（equal125.00%から-15.77pt）
  - LOMOも5月中3月・5月で悪化。raw bestは過学習傾向、正式候補にしない。
- 固定rank 600円配分もperiod反転:
  - DEVではrank2厚めが良いがSUPPORTで悪化。v369結論を再確認。
- closing oddsはexecution upper-bound featureであり、正式採用にはlive snapshot再現が別途必要。
- September outcomes unread / production unchanged / AUDIT_OK=true。

## BEFORE — v371 value-gated top-up robustness
- v370 artifact `10560443188` の `formal_with_closing_odds.csv` を直接再利用し、オッズ再取得しない。
- 全165Rを買う。formal 3点も固定。各レース最低100/100/100を維持。
- 構造を事前固定:
  - gate A: top3合成オッズ >= C
  - gate B: max conditional value score = max(pair_prob × closing_odds) >= E
  - A&Bを満たす時だけextra 1〜3 unitsを追加
  - 追加後の全unitsはvalue score比例で3点へ配分、各点最低1unit
- DEV grid:
  - C=2.00〜4.00（.25刻み）
  - E=.70〜1.50（.10刻み）
  - extra=1/2/3
- raw DEV bestをそのまま選ばず、DEV bestからROI 2.5pt以内のplateauを作り、そのplateauのparameter medoidをDEV-only coreとして選ぶ。
- さらにFeb-Jun各月のdelta ROI / worst month / nonnegative month数を記録。
- Jul-Augはcore固定後にholdout評価。
- ROI計算は実払戻×unit。closing oddsはgate/配分特徴だけ。
- 正式採用条件候補:
  - ALL ROI > equal baseline
  - SUPPORT ROI >= equal baseline
  - DEV month robustnessが極端に偏らない
  - parameter plateauが広い
- production/LIVE betting remains unchanged。


## NEXT CHAT HANDOFF — dynamic staking / official closing odds research
- ユーザー希望により、重くなったため次チャットへ移行。
- 現正式LIVE買い目は変更なし:
  - wall3正式 + 5>6 ST正式
  - 87/165 = 52.73%
  - 3点各100円の均等買いROI 128.687%
- v369 ticket-rank監査完了:
  - rank1: 34hit (39.08%), return19,770, solo ROI119.82%
  - rank2: 28hit (32.18%), return22,710, solo ROI137.64%
  - rank3: 25hit (28.74%), return21,220, solo ROI128.61%
  - ただしDEVとSUPPORTでrank傾向が大きく反転するため、固定rankウェイトは不採用。
  - v369 Run 35344087154 / Job 105596491873 / Artifact 10546631786 / AUDIT_OK=true。
- 買い方研究の次テーマ:
  - 固定順位ウェイトではなく、**レースごとの動的資金配分**。
  - 3点の買い目自体は固定したまま、公式締切3連単オッズとモデル確率を使って配分を変える。
- 既存研究として v340 adaptive odds Dutch が発見済み:
  - handoff: CHAT_HANDOFF_20260914_1HEAD_V340_ODDS_DUTCH.md
  - 旧正式276RでBOAT RACE公式締切3連単オッズ coverage 276/276。
  - Run 34796402852 / Artifact 10329904344。
  - ユーザー指定adaptive policyでは bought33R / ROI115.53% vs baseline276R ROI93.03%。
  - 主効果は低合成オッズraceのskipで、今回はrace数を減らすのが主目的ではないため、**v340のDutch配分・公式closing odds取得部分だけ再利用する**。
- 次チャットで最初に読むもの:
  1) CHAT_HANDOFF_20260917_1HEAD_CURRENT_NEXT.md
  2) CHAT_HANDOFF_20260914_1HEAD_V340_ODDS_DUTCH.md
  3) run_v340_prepare_rankings.py
  4) run_v340_odds_shard.py
  5) run_v340_aggregate_shards.py
  6) run_v322_1head_composite_odds.py
  7) data/official_closing_odds3t/*
- 次にやる研究:
  1) 現正式165Rの各3点に公式締切オッズをjoin。
  2) 100/100/100均等をbaseline。
  3) 同総額300円または600円で、
     - Dutch均等払戻型
     - model probability比例
     - model probability × odds期待値型
     - conservative capped Kelly風
     を比較。
  4) DEV Feb-Junだけで配分ルール選定、SUPPORT Jul-Augは完全holdout。
  5) 買うrace数は原則165R固定。skip型は比較参考のみ。
  6) ROI / profit / 最大1R投入 / rank別寄与 / 月別安定性を監査。
- 重要:
  - September outcomes/payoutsはUNREAD維持。
  - current formal LIVE ticketsは変更しない。
  - ROIを落としてhit率だけ上げる案は不採用方針。


## AFTER — v371 value-gated top-up robustness
- Run `35377804773` / Job `105706558975` completed success / Artifact `10560801328` / digest `sha256:96b71a89bca7b500c979022e3e80a349a409b8b59cf77e43d00fde9268589305`。
- formal baseline:
  - 165R / stake49,500 / return63,700 / profit+14,200 / ROI128.687%
  - DEV129.44% / SUPPORT125.00%。
- DEV raw best:
  - combined>=2.50 / conditional value>=1.30 / extra3 units
  - DEV ROI145.68%だが月別非悪化3/5、worst -17.05pt。
- DEV plateau:
  - bestから2.5 ROI pt以内 = 8 cells
  - combined 2.00〜2.50 / value .90〜1.30 / extra=3固定。
- DEV-only medoid core:
  - combined>=**2.25**
  - max(pair_prob×closing_odds)>=**1.10**
  - gate発火時extra **3 units**
  - total unitsはvalue score比例、各formal ticket最低1unit。
- medoid core:
  - DEV: 35R trigger / stake51,600 / return74,330 / profit+22,730 / ROI **144.05%**
  - SUPPORT: 5R trigger / stake9,900 / return13,060 / profit+3,160 / ROI **131.92%**
  - ALL: 40R trigger / stake61,500 / return87,390 / profit **+25,890** / ROI **142.10%**
  - baseline比 ALL +13.41 ROI pt / profit +11,690円
  - SUPPORT +6.92 ROI pt。
- 月別:
  - Feb +1.96pt
  - Mar +20.14pt
  - Apr +16.44pt
  - May -7.33pt
  - Jun +40.10pt
  - Jul +27.41pt
  - Aug -3.88pt
- 近傍18 cellsはDEV delta ROI>=0が100%。
- closing oddsは正式締切後に確定するexecution upper-boundであり、**このままLIVE正式採用はしない**。
- September outcomes unread / production unchanged / AUDIT_OK=true。

## BEFORE — v372 value-gated staking LOMO + live-odds feasibility
- v371 family/medoid方式をDEV内LOMOで再選定:
  - 各holdout月を除く4DEV月でplateau medoidを再選定
  - holdout月のROI差を監査
- DEV plateau 8 cells全件についてSUPPORT成績も「選定には使わず」robustness診断。
- repoにhistorical pre-close odds snapshotが存在するか調査。
- snapshotがなければ、v371はupper-bound研究として保存し、今後forward LIVEで判定時オッズを保存するlogger設計へ進む。
- formal tickets/race setは変更しない。

## BEFORE — 2026-09-19 v372 LOMO + pre-close odds feasibility continuation
- ユーザー指示: dynamic staking / BOAT RACE公式締切3連単オッズを使った買い方研究の続き。
- 最新main/handoff確認済み。v371は165R全購入・formal 3点固定のvalue-gated top-upで ALL ROI 142.10%、SUPPORT 131.92%だが、closing odds使用のためexecution upper-bound扱い。
- これからやること:
  1. v371 familyをDEV Feb-JunでLOMO再選定し、各holdout月の外部月差を監査。
  2. v371 DEV plateau 8 cellsをSUPPORT Jul-Augへ固定適用してrobustnessのみ診断（SUPPORTで選定しない）。
  3. repo内のhistorical pre-close/current odds snapshot保存実装の有無を監査。
  4. snapshotが無ければforward LIVE用に判定時オッズを保存するlogger設計/実装へ進む。
- formal race set/ticketsは変更しない。September outcomes/payoutsはUNREAD維持。production/LIVE betting ruleはこの研究だけでは変更しない。


## AFTER — v386 expanded current-odds safety-margin audit
- Run `35368163224` / Job `105675520424` success / Artifact `10556873896` / digest `sha256:89bd1a40236ee615c865eaf73d0b5dcf24790e7c84799d669442c1445433a7e3`。
- v379 odds-independent allocation baselineとの厳密比較:
  - LIVE165 baseline142.305%
    - threshold3.9: **144.163%** (+1.857pp)
    - threshold4.3: **142.935%** (+0.630pp)
  - H078_M375 baseline128.503%
    - 3.9: **131.099%** (+2.596pp)
    - 4.3: **129.263%** (+0.760pp)
  - H0775_M375 baseline123.211%
    - 3.9: **125.474%** (+2.263pp)
    - 4.3: **123.874%** (+0.663pp)
  - H0775_M350 baseline119.709%
    - 3.9: **122.443%** (+2.734pp)
    - 4.3: **120.608%** (+0.899pp)
  - PROD276 baseline124.861%
    - 3.9: **127.381%** (+2.520pp)
    - 4.3: **125.823%** (+0.962pp)
- disjoint nested bands against reconstructed v379 baseline:
  - LIVE165: 3.9 +1.857pp / 4.3 +0.630pp
  - added71R baseline95.476%: 3.9 **99.841%** (+4.365pp), 4.3 **96.548%** (+1.071pp)
  - added33R baseline87.302%: 3.9/4.3ともsoft発火0で完全同値
  - added45R baseline97.255%: 3.9 **101.026%** (+3.771pp), 4.3 **97.756%** (+0.502pp)
- 結論: 3.9/4.3はLIVE165だけの改善ではなく、拡大母集団でもodds-independent allocation以上。特に3.9は独立追加71R/45Rでも改善。
- ただし3.9/4.3は「想定current→close drift 5%/10%」から機械的に導いた安全閾値で、historical outcomeで最適化した値ではない。
- production/official stake/current-odds shadow未変更 / September unread / AUDIT_OK=true。

## BEFORE — prospective current-odds telemetry 3.5/3.9/4.3
- historical pre-close odds snapshotが存在しないため、これ以上closing oddsだけで正式採用判断しない。
- 現在のLIVE current-odds shadowはresearch_onlyのまま維持。
- forward観測を強化:
  - current odds取得時刻
  - formal deadline_jst
  - minutes_to_deadline
  - current selected3 odds ratio
  - threshold3.5 / 3.9 / 4.3それぞれのsoft発火有無
  - 各thresholdでの仮想stakes
  を同一shadow JSONに保存。
- WALL3時はodds非依存100/100/400なので全threshold同一。
- five6-only / NONEだけthreshold別soft allocationを比較。
- 既存 `stakes_yen` / threshold3.5 shadow semanticsは変更しない。3.9/4.3は追加telemetryのみ。
- result/payout endpointは使用しない。formal tickets / official stakes / HEAD gatesは変更しない。
- 保存済みsynthetic regressionで既存3.5出力不変 + 3.9/4.3追加fieldを監査する。


## AFTER — prospective current-odds telemetry 3.5/3.9/4.3
- current odds shadow script commit `2d1163625f70d0308fe25f96c0a5b295cfc6bc73`
  - existing threshold3.5 `stakes_yen` / signal semanticsは変更なし。
  - `formal_deadline_jst`, `formal_evaluated_at_jst`, `formal_minutes_to_deadline` を追加。
  - `safety_scenarios` に3.5 / 3.9 / 4.3を同時出力:
    - ratio_min
    - odds_ratio_max_min
    - soft_applied
    - soft_units
    - signal
    - stakes_yen
    - total_stake_yen
  - WALL3は全thresholdで100/100/400固定。five6-only/NONEはthresholdごとにsoft発火を比較。
- regression update commit `caa6db21573ad8c96c856a0ce02c99cf6553b72e`。
- v384 regression Run `35378645210` / Job `105709293039` success / Artifact `10561770747`
  - digest `sha256:1b94145aae6b200d52318f7bc09cd6a210eac54eb8bd3fb8b291849c67aca585`
  - existing3.5 output不変
  - deadline/minutes telemetry確認
  - safety_scenarios 3.5/3.9/4.3確認
  - result_or_payout_used=false / AUDIT_OK=true。
- 現運用:
  - formal ticket / official stakeは変更なし。
  - current-odds allocationはresearch shadowのまま。
  - 今後「判別して」のLIVE artifactで実購入可能時点のodds ratioと3.5/3.9/4.3配分をprospectiveに保存可能。
- 次の研究価値:
  - forward sampleで current ratio → 締切ratio drift を蓄積し、5%安全margin(3.9) / 10%margin(4.3) のどちらが実測に合うかを結果ではなくodds drift自体で判定する。
  - これが十分貯まるまではclosing-odds historical ROIだけでformal stakeへ昇格しない。
- September outcomes unread / production unchanged。


## AFTER — 2026-09-19 v372 LOMO + pre-close execution audit
- 実装:
  - `run_v372_1head_value_gated_lomo_preclose.py`
  - workflow `.github/workflows/v372-1head-value-gated-lomo-preclose.yml`
- commits:
  - handoff BEFORE `434fcddbfb0b64a1bd168139abfd32761a41da88`
  - script `c3b9b507de6b2ce7421f12448bfa835b8addcb7e`
  - workflow `34b85911f3d8b048b0e92fe19e4e6277def962a2`
  - self-publish metadata `bf2c8a417c26c9153ce264e89a17fb9d7a852677`
  - audit result publish `705e758c7a4b1ede2b12e284dfad96f28bbd5e61`
- Actions:
  - Run `35378456509`
  - Job `105708674939`
  - Artifact `10561425801`
  - digest `sha256:cdb44e32c9f13f328b4cc57f02287d6542f77531a63ebe0458fa83b6d2bffda9`
  - completed SUCCESS / AUDIT_OK=true.
- closing v371 identity reproduced exactly:
  - core = combined>=2.25 / max(pair_prob×odds)>=1.10 / extra3 units.
  - ALL 165R: trigger40 / stake61,500 / return87,390 / profit+25,890 / ROI142.10%.
  - DEV 137R: ROI144.05%.
  - SUPPORT 28R: ROI131.92%.
- DEV内LOMO:
  - Feb -17.05pt / Mar +20.14pt / Apr 0.00pt / May -3.12pt / Jun +17.69pt.
  - 非悪化 3/5月。
  - LOMO合計profit差は baseline比 +3,240円。
  - よってclosing coreは完全な一月依存ではないが、月ごとの選定parameterは動く。
- DEV plateau 8セルをSUPPORTへ固定診断:
  - baseline以上は4/8セル = 50%。
  - medoid core自体はSUPPORT +6.92ptだが、plateau全域が強いわけではない。
- BoatraceCSV `data/previews/od3` のpre-close snapshotを current formal165Rへjoin:
  - coverage 21/165のみ。
  - Feb-Jun 0R、Jul 2/9、Aug 19/19。
  - 21Rの取得lead time median 574.5秒（約9分35秒前）、range 503.3〜580.1秒。
- covered同一21R比較:
  - equal 100/100/100 baseline: stake6,300 / return7,370 / profit+1,070 / ROI116.98%。
  - closing odds v371 core: trigger3 / stake7,200 / return8,150 / profit+950 / ROI113.19%。
  - pre-close oddsへ同coreをそのまま適用: trigger8 / stake8,700 / return8,620 / profit-80 / ROI99.08%。
- closing vs pre-close market drift 21R:
  - trigger agreement 76.19% / Jaccard .375。
  - allocation exact match 76.19%。
  - combined odds |relative drift| median15.59% / p90 27.49% / p95 28.18%。
  - signed combined drift median -14.12%、21R中17R(80.95%)でclosing combined oddsの方がpre-closeより低い。
  - つまり約9分前はclosingより高い合成オッズを示しやすく、raw v371 gateが過剰発火しやすい。
- LIVE current odds infrastructureは既に存在:
  - `boatrace_live_odds3t.py`
  - `run_1head_v351_live_current_odds_shadow.py`
  - formal3点のcurrent official odds + fetched_atをartifactへ保存可能。
- 結論:
  - closing v371はexecution upper-boundとして維持。
  - raw closing thresholdをcurrent/pre-close oddsへそのまま適用しない。
  - production/formal stakeは変更なし。September outcomes/payouts UNREAD維持。

## BEFORE — v373 current-odds safety translation
- v372 covered21Rの結果/払戻ではなく、closing↔pre-closeの市場変動だけで安全マージンを決める。
- v371 closing gate C=2.25 / E=1.10 に対し、current oddsからclosing oddsが最大d下落すると仮定し:
  - C_safe = 2.25/(1-d)
  - E_safe = 1.10/(1-d)
  を機械的に適用する。
- 1%刻みで「pre-close safe triggerがclosing core triggerのsubsetになり、allocationも一致する最小d」をmarket-onlyで求める。
- さらにcombined odds absolute drift p95を5%刻み切上げしたconservative dも作る。
- payoutは各固定candidateの診断にのみ使い、d選定には使わない。
- full165 closing odds上でも安全閾値によるtrigger縮小とROI残存を診断。
- formal tickets/stakes/productionは変更しない。September outcomes UNREAD。


## AFTER — v373 current-odds safety translation
- 実装:
  - `run_v373_1head_value_gated_current_odds_safety.py`
  - workflow `.github/workflows/v373-1head-current-odds-safety.yml`
- commits:
  - v372 AFTER / v373 BEFORE handoff `a400d5c244b611754215307e33b76ab8de7ad6cd`
  - script `239a0993700f16d4b4ef4f40a257df4664154792`
  - workflow `b4e1d9d6497062f73a92f8784ac87160e8b64fdf`
  - audit publish `e45d2148f413b439282bc4733260a38803a51e92`
- Actions:
  - Run `35378979553`
  - Job `105710361495`
  - Artifact `10560887429`
  - digest `sha256:3c0b283ce5589a61773a034f1d98e59ad54f52747919c20963f28a0428ae68c0`
  - SUCCESS / AUDIT_OK=true。
- safety dの選定にpayout/resultは不使用。
- closing gate = combined>=2.25 / max(pair_prob×odds)>=1.10 / extra3。
- covered21Rのmarket transitionだけで:
  - zero false-positive + triggered allocation完全一致となる最小d = 18%。
  - 5%刻み安全側切上げ = **d=20%**。
  - combined |drift| p95=28.18% -> 5%刻み conservative = d=30%。
- d=20% research shadow:
  - current/pre-close threshold = **combined>=2.8125 / max(pair_prob×odds)>=1.375**。
  - covered21R pre-closeでは trigger3R。raw closing coreの3Rと発火集合・配分が完全一致。
  - covered21R payout診断（選定には未使用）: stake7,200 / return8,150 / profit+950 / ROI113.19%。
- d=30% conservative shadow:
  - threshold combined>=3.2143 / value>=1.5714。
  - covered21R trigger1 / payout診断 ROI123.48%。ただしこのROIでdは選んでいない。
- full165 closing oddsへ安全側thresholdだけを固定適用するdiagnostic:
  - d=20%: trigger13 / ROI138.73% / profit+20,680、DEV142.24%、SUPPORT120.69%。
  - d=30%: trigger4 / ROI135.13% / profit+17,810、DEV137.14%、SUPPORT125.00%。
- 結論:
  - raw v371をcurrent oddsへ直接適用せず、まずd=20%をresearch-only prospective shadowとしてforward収集する価値がある。
  - sample21Rのためformal stake昇格はしない。
  - September outcomes unread / formal unchanged。

## BEFORE — prospective v373 value-gate current-odds telemetry
- 既存current odds shadowにはsoft-Dutch ratio 3.5/3.9/4.3 telemetryが並行実装済み。
- v373は別ロジック（combined odds + pair_prob×odds）なので、既存soft-Dutch outputを変更せずadditive fieldとして保存する。
- final LIVE JSONにformal最終3点のpair probabilityをresult-freeで追加する。
- current odds shadowで:
  - d20: combined>=2.8125 / max(pair_prob×current odds)>=1.375 / extra3
  - d30: combined>=3.2142857 / value>=1.5714286 / extra3
  をresearch-only telemetryとして出力。
- formal `official_stakes_yen` / tickets / existing current-odds `stakes_yen` は変更しない。
- regressionを追加し、既存shadow semantics不変・value gate telemetryのみ追加を確認する。


## AFTER — prospective v373 value-gate current-odds telemetry
- implementation commits:
  - thresholds/profile `4e95fb58fa08b5a27186e0bf858f6348495f3d9a`
  - LIVE finalize formal ticket pair probabilities `ed5c7b7c7fce36f739e9ce1518d12526692b51e4`
  - current odds shadow additive value-gate telemetry `5cbe0d65f714298af66f311c7238b4b3760dc937`
  - regression script `b6e136632362c90275ce26003bf00617a619ac89`
  - regression workflow `cbf1c4c624581c8c48f23e3e9275ea6459146f2a`
  - audit publish `9f1a7fd395e191d779015c3e56b50f6c4a9ffbf2`
- v374 telemetry regression:
  - Run `35379286090`
  - Job `105711349027`
  - Artifact `10561117781`
  - digest `sha256:b1e6babf5c7c1075e829d5c57759186d5183acf09469f16f909a2b9c3cbd1efb`
  - SUCCESS / AUDIT_OK=true。
- LIVE finalize:
  - formal最終3点について `ticket_pair_probs` をadditive出力。
  - wall3 / five6反映後のfinal pair distributionを再構成し、ticket ranking一致をassert。
  - result/payoutは不使用。
- current odds shadow additive output:
  - existing soft-Dutch `stakes_yen` / safety_scenarios 3.5/3.9/4.3 は不変。
  - `value_gate_scenarios.D20`:
    - combined_min 2.8125
    - value_min 1.375
    - extra_units 3
    - active時はvalue=p×current_odds比例でbase1unit+extra3。
  - `value_gate_scenarios.D30`:
    - combined_min 3.2142857143
    - value_min 1.5714285714
    - extra_units 3。
  - いずれもresearch_only=true。
  - pair probabilityが無い古いfinal JSONでは `UNAVAILABLE_NO_PAIR_PROBS` とし、existing shadowを壊さない。
- synthetic regression:
  - D20だけ発火case: legacy 100/100/100維持、D20=200/200/200、D30非発火。
  - D20/D30両発火case: legacy 100/100/100維持、value gate=300/200/100。
  - backward compatibility case: pair probs無しでもlegacy stakes unchanged。
- existing regressions after modifications:
  - v384 current odds shadow Run `35379228026` / Job `105711157653` / Artifact `10560812888` SUCCESS。
  - v356 wall3 Run `35379203378` / Job `105711076049` / Artifact `10561801678` SUCCESS。
  - v364 five6 Run `35379203415` / Job `105711076284` / Artifact `10561971352` SUCCESS。
  - live-finalizer contract Run `35379203554` / Job `105711076584` / Artifact `10561961448` SUCCESS。
  - v377 overlay stake Run `35379203585` / Job `105711079265` / Artifact `10561656831` SUCCESS。
- broad historical workflows triggered by additive production-profile constants were still in_progress at the last check; targeted LIVE/finalizer regressions above are all green.
- production/formal:
  - formal tickets unchanged。
  - `official_stakes_yen` remains 100/100/100。
  - existing stake/allocation/current-odds shadows unchanged; v373 fields are additive research telemetry only。
  - September outcomes/payouts remain UNREAD。

## NEXT — dynamic staking / current-odds forward validation
1. 今後の1head LIVE PASS判定artifactで `ticket_pair_probs` + official current odds + D20/D30 active/stakes をprospective保存する。
2. まず結果を読まず、判定時current odds → official closing oddsのmarket driftだけを蓄積。
3. D20が「currentで発火した後もclosing core条件を保つ」率を十分な件数で確認する。
4. 件数が貯まるまでD20/D30はresearch shadowのまま。closing v371 ROIを理由にformal stakeへ昇格しない。
5. September outcomesはUNREAD維持。production変更なし。


## 2026-09-19 USER DIRECTIVE — dynamic stakeはShadow表示で継続
### BEFORE
- ユーザー指示: 母数がまだ少ないためformal増額には昇格せず、「一応Shadowで出して」運用を継続する。
- 既存LIVE実装を確認し、formal買い目/official stakeを変えずにShadowがartifactへ出ることを再確認する。

### AFTER
- 既存LIVE workflowを確認:
  - `.github/workflows/manual-1head-v351-live.yml`
  - `.github/workflows/chat-live-1head-v351-request.yml`
  - どちらもformal finalize後に `run_1head_v351_live_current_odds_shadow.py` を実行し、current odds Shadow JSONをartifactへ保存済み。
- Shadowで既に観測できる内容:
  - WALL3: 100/100/400
  - FIVE6-only: 基本200/200/200、current odds soft発火時はsoft配分
  - current odds safety 3.5 / 3.9 / 4.3
  - value gate D20 / D30
- 今後ChatGPTが1head直前判定を返す際は、formal買い目（official 100/100/100）と明確に分離して「Shadow」として仮想stakes/発火理由も併記する。
- production/formal stake変更なし。research_only維持。
- September outcomes/payoutsはUNREAD維持。


## BEFORE — 2026-09-19 v387 4HEAD-style added71 exhibition rescue
- ユーザー指示: 1HEAD実運用も4HEADのように「本線＋拡張候補→展示後救済」にすると買うレースを増やせるか研究を続行。
- current formal LIVE165は一切変更しない。
- 拡張候補は frozen v360 Artifact `10539401122` の `H078_M375 236R - LIVE165 165R = added71R` に限定。
- added71は HEAD>=.780 / opponent mass>=.375 / env_w=.05 / q=.70 の外側帯。現LIVE165はHEAD>=.790。
- 研究構造:
  1. LIVE165を本線固定。
  2. added71だけに二次 rescue score を作る。
  3. scoreはPREの `p_head` と同一時点で利用可能な展示後 `v332_score/attack_core` 等の小数特徴だけを使い、結果/払戻はscore入力にしない。
  4. Feb-Jun DEVのみでweight/thresholdを比較。
  5. Jul-Aug SUPPORTはcandidate凍結後に評価。
  6. current formal wall3 + 5>6 ticket machineryを追加帯にも適用した3点100円均等でROI/頭率/exact3を評価。
- 目標は全71Rを買うことではなく、+20〜40R程度を追加してcombined volumeを185〜205R付近へ伸ばせるかを見る。
- September outcomes/payoutsはUNREAD維持。production/LIVE official gateは変更しない。


## AFTER — v387 4HEAD-style added71 exhibition rescue
- Script commit `f75e3b47ef8393d5579f6933e2adc0eb6bb524f4`; set-difference fix `22c247c183c156d81d0778f4550fbc1ba157481e`.
- Workflow commit `cf0fc1afa4ca5eaab1721df0d87a89c1cba5d1f2`.
- First Run `35382004598` failed only because code incorrectly assumed added71 was pure p_head<.79; actual set difference includes 1 race >=.79 because exhibition gate is refit per PRE universe.
- Corrected success:
  - Run `35382176160`
  - Job `105720673428`
  - Artifact `10562742211`
  - digest `sha256:0239ecd455880a33ead43d6c7e67371b341a1bfaeceebe02e34a4705e38b8571`
  - AUDIT_OK=true / September unread / production unchanged.
- added71 identity = `H078_M375 236R - LIVE165 165R`:
  - p_head range .78006〜.81530
  - 70R are <.790, 1R is >=.790.
- Current formal wall3+5>6 tickets, equal 100x3:
  - LIVE165: head 140/165=84.85%, exact3 87/165=52.73%, ROI128.69%.
  - added71: **head 63/71=88.73%**, exact3 33/71=46.48%, ROI100.28%.
  - DEV added53: head88.68%, exact3 27/53, ROI112.77%.
  - SUPPORT added18: head88.89%, exact3 6/18, ROI63.52%.
- Main finding: expansion head quality is NOT the bottleneck; added71 head rate is even higher than LIVE165. SUPPORT deterioration is from opponent-3-ticket capture/payout, not 1-head selection.
- DEV-only volume-first rescue score picked HEAD_EX_MASS q=.35:
  - all selected48R, head93.75%, ROI114.03%
  - DEV34R head94.12%, ROI135.69%
  - SUPPORT14R head92.86%, ROI61.43%
  - LIVE+rescue combined 213R ROI125.38%; SUPPORT combined42R ROI103.81%.
- DEV LOMO for chosen rescue was positive in all five holdout months (ROI 114.6/152.0/121.7/124.3/137.1), but Jul-Aug SUPPORT ticket ROI still collapsed.
- Therefore a head/exhibition rescue gate alone is insufficient. The next bottleneck is opponent/ticket confidence in the added band.

## BEFORE — v388 added71 opponent-confidence rescue
- Keep LIVE165 fixed and keep 3-ticket count fixed.
- Use the same frozen added71 and current formal wall3+5>6 distributions.
- Build result-free opponent confidence features after formal reranks:
  - top3 pair probability mass
  - pair rank3-vs-rank4 probability margin
  - pair distribution concentration/entropy
  - optional combination with exhibition score.
- DEV Feb-Jun only for threshold/family comparison; SUPPORT Jul-Aug evaluated after freezing.
- Objective: determine whether +15〜35 rescue races can preserve added-band exact3/ROI better than head/exhibition score alone.
- No current/closing odds required in this pass. September outcomes unread. Production unchanged.


## AFTER — v388 added71 opponent-confidence rescue
- Initial implementation:
  - script commit `84faa62cf4e7aed7906b3bd47bc762af421e8368`
  - workflow commit `e73e5007c83f3d9b459cb7cb87fe6d90de446705`
- Initial Run `35382453687` / Job `105721568220` / Artifact `10562747789` is **INVALID FOR ANALYTIC CONCLUSIONS**:
  - bug: confidence feature calculation accidentally used raw pair-probability order as the actual 3 tickets.
  - baseline drifted to LIVE165 73 hits instead of formal87; therefore all selection metrics from that run are rejected.
- Bug fix commit `032312577aa541bbb283343342e69570699e5f43`:
  - formal tickets frozen to current HYBRID strategy after formal wall3+5>6.
  - pair-confidence features are additive only.
- Corrected Run:
  - Run `35382584562`
  - Job `105721997631`
  - Artifact `10562702937`
  - digest `sha256:34474ed65dc2548223b9b2df5c529946bbee376cee69a4abb9a24497576dc43a`
  - SUCCESS / AUDIT_OK=true.
- Corrected baseline identity:
  - LIVE165 = 165R / 87 exact3 / return63,700 / ROI128.69%.
  - added71 = 71R / 33 exact3 / return21,360 / ROI100.28%.
  - DEV added53 ROI112.77%; SUPPORT added18 ROI63.52%.
- DEV-only volume-first selection:
  - family `PAIR_MARGIN` / q=.35
  - selected 43R total = DEV34 + SUPPORT9
  - DEV: exact3 18/34=52.94%, ROI117.55%, profit+1,790
  - SUPPORT: **0/9 exact3, ROI0%, profit-2,700**
  - combined LIVE+rescue 208R: ROI121.30%
  - combined SUPPORT 37R: ROI94.59%.
- Some stricter cells happen to improve SUPPORT (e.g. PAIR_CONC q=.55 support 3/5, ROI126.67%), but those are not DEV-selected and their DEV ROI is below100%; SUPPORT must not be used to cherry-pick them.
- Conclusion:
  - a single opponent-confidence scalar is not temporally stable enough.
  - expansion head quality remains strong, but added-band ticket ranking/coverage is regime-sensitive.
  - production unchanged / September outcomes unread.

## BEFORE — v389 added71 ticket-policy consensus
- Keep LIVE165 formal path fixed and added71 as the only expansion pool.
- Hypothesis: added-band opponent ranking is safer when multiple pre-race ticket-ordering views agree, instead of relying on one probability-margin scalar.
- Build result-free consensus features from the SAME post-wall3+5>6 p2/pc distribution:
  - HYBRID top3 (formal)
  - JOINT top3
  - TOP2XTOP2 top3
  - SECOND1X3 top3
  - SECOND3X1 top3
  - overlap counts with formal HYBRID
  - number of formal tickets supported by multiple strategies
  - formal 3-ticket pair-prob mass
  - best-outside probability / weakest-formal probability risk ratio
- Candidate rules are selected on Feb-Jun DEV only.
- Include DEV leave-one-month-out stability when choosing among comparable volume candidates.
- Jul-Aug SUPPORT is evaluated only after freezing the candidate.
- Goal remains +15〜35R rescue with formal 3-ticket count unchanged.
- September outcomes/payouts unread. Production unchanged.
