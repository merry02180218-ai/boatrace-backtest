# 1号艇 v351 LIVE 引き継ぎ — 2026-09-15

## 最重要ルール
- 最新GitHubを最優先する。古いチャット・古い記憶と競合したら最新GitHubを採用する。
- 2026年9月15日のレース結果・払戻は絶対に読まない。LIVE判断では `UNREAD` を維持する。
- `result_or_payout_used=False` / `chronology_guard=True` を維持する。
- repo変更前に「これからやること」、変更後に結果・commit SHA・Actions Run/Job/Artifact ID・結論・次の再開地点をこの引き継ぎへ記録する。
- workflow名・ファイル名・artifact名だけで1号艇/4号艇を判定しない。実際のscript、target、依存関係、production上の親モデルまで確認する。
- 実際にGitHub作業をしていない状態で「進めている」「終わった」と言わない。必ず実Run/Job/Artifact/commitを確認して報告する。

## 現在の1号艇production / LIVE
- 1号艇LIVEは v351。
- workflow: `.github/workflows/auto-live-1head-v351-exhibition-20260915.yml`
- venue-aware修正: `376748f25079cd3a717fbb42da71fc8fcb5b4b9f`。
- WAIT継続job化（後に不採用）: `480c57a4da7d1b3f6f78b787beefc87790a08195`。
- nonblocking polling修正: `b953b27d45831a5a139466bb57ea0ca0a2ffcab6`。
- nonblocking修正後の引き継ぎcommit: `468aba82c868ac6f741932e15a4ffb1cca5c7d42`。
- 福岡10R自己copy hotfix後のHEAD: `ba7b53f9ab48170aaed179ef53ccd82c624ca621`。

## 1. Runner占有問題と解消
### 問題
- Run `34938438610` は1号艇 `auto-live-1head-v351-exhibition-20260915`。
- 各候補jobがWAIT中に15秒sleepを継続してRunnerを占有する設計だった。
- 常滑11R `202609150811` PRE=A / `0.8048050886183357` のjob `104281420706` もqueuedになった。
- ユーザー指示で旧RunをCancel。キャンセル後、WAIT継続jobによるRunner占有は停止した。

### nonblocking化
実装commit: `b953b27d45831a5a139466bb57ea0ca0a2ffcab6`

変更内容:
- WAIT中の `while true` / `sleep 15` を撤去。
- 各cron Runで候補を1回だけ評価する。
- `MODE=WAIT` は `POLL_DONE=WAIT` で即終了しRunner解放。
- TRY/FINAL5のみ展示probe。
- READYなら prediction cache → exact v351 exhibition gate → finalizer → immutable artifact。
- FINAL5で展示未READYの場合だけfail-close。
- watch timeout 45分→10分。
- max-parallel 20は維持。
- matrixはrace_code順であり、締切優先順ではない。締切優先を実装済みと誤認しないこと。

### 残る構造問題
- WAITでもcheckout/setup-python/pip installまでは走るためRunner overheadは残っている。
- cron起動自体がGitHub Actions scheduleの遅延/欠落に依存する。
- より堅牢にするなら、prepare/orchestratorでWAIT候補をmatrixから除外する、または1本のcontroller jobで候補全体を監視する構成を検討する。

## 2. schedule発火問題
workflowのcron設定は現在も:

```yaml
schedule:
  - cron: '*/5 * 15 9 *'
```

つまり9/15は5分ごとの設定。

しかし実運用確認時:
- v351 Run `34939662186` は16:01:50 JST作成、16:10台に終了。
- 16:15/16:20付近に期待した次のv351 scheduled Runが確認できなかった。
- 一方16:22台には別workflow `auto-live-3head-v288-production` のscheduled Run `34941377307` が実際に起動した。
- したがって「GitHub Actions全体が止まった」わけではない。
- v351はschedule eventの遅延/欠落に依存するため、LIVE用途としてcronだけに頼るのは危険。
- このschedule発火問題は未解決。次チャットで優先監査対象。

## 3. 常滑11R確認
- race_code `202609150811`
- PRE=A
- PRE probability `0.8048050886183357`
- 締切15:46 JST。
- 旧RunではWAIT/Runner問題に巻き込まれ、finalizerまで到達しなかった。
- nonblocking Run `34939662186` のjob `104286849859` はsuccessだが、exact finalizer/uploadはskip。
- 常滑11Rのfinal artifactはこの時点で未確認。

## 4. 福岡10R LIVE復旧の全経緯
### 対象
- 福岡 JCD22 R10
- race_code `202609152210`
- PRE class = A
- PRE probability / legacy_pre_p = `0.8034152525704932`
- 締切 = 16:30 JST

### 最初のcron Run
Run `34939662186` の福岡10R job:
- Job `104286850028`
- 16:10:06 JST時点
- remaining = 約19.889分
- `MODE=WAIT`
- `should_fetch_exhibition=false`
- workflow仕様によりWAITなら即終了したため、このjobでは展示probeもfinalizerも実行されなかった。

ユーザーから「もう福岡10出てるぞ」と指摘あり。つまり展示自体は公開済みでも、時間windowがWAITだったため取りに行かない設計だった。

### 緊急rerun
福岡10R jobを再実行し、新Job:
- `104291330238`

このjobでは16:25:46 JST時点で:
- `MODE=FINAL5`
- `EXHIBITION_READY=1`
- `POLL_DONE=READY`

まで正常到達。

つまり福岡10Rについて展示取得/READY判定そのものは成功した。

### 自己copyエラー
その後finalizer直前に以下で失敗:

```text
cp: '/tmp/cache/v351_exhibition_train.csv' and '/tmp/cache/v351_exhibition_train.csv' are the same file
Process completed with exit code 1.
```

原因:
- TRAINファイルがすでにBASEと同じ場所なのに、自分自身へ `cp` しようとして `set -e` でexit 1。
- モデルや展示データのエラーではなくworkflowのファイルコピー処理バグ。

### hotfix
自己copy時は `cp` しないようworkflowを修正。
- hotfix後HEAD/commit: `ba7b53f9ab48170aaed179ef53ccd82c624ca621`

### hotfix後Run
- Run ID: `34941864661`
- prepare Job: `104292164481` → success
- 福岡10R Job: `104292235997`
- head SHA: `ba7b53f9ab48170aaed179ef53ccd82c624ca621`

福岡10R Job `104292235997` の最終step状態:
- checkout: success
- setup-python: success
- pip install: success
- Skip immutable final: success
- Resolve window and probe once: success
- T-5 fail close: skipped
- Download shared prediction cache: success
- Exact v351 exhibition gate and finalizer: **success**
- upload-artifact: **success**
- Complete job: success

### 福岡10R final Artifact
- Artifact name: `live-v351-final-202609152210`
- Artifact ID: `10385348792`
- created_at: `2026-09-15T07:30:19Z` = 16:30:19 JST付近
- size: 3047 bytes
- digest: `sha256:1fb5550c3ec63a79204f9b89d6cad119768053d77b53f5d88eb015d3daf1fa07`

### 福岡10R 最終判定
Artifactを回収して確認した結果:
- PRE=A / `0.8034152525704932`
- 展示反映後の1号艇頭確率: **`0.74939`**
- production HEAD cutoff: **0.78**
- `0.74939 < 0.78`
- `head_exhibition_pass=false`
- 最終判定: **DROP / 見送り**
- `tickets=[]`
- 買い目なし。
- `result_or_payout_used=false`
- `chronology_guard=true`
- 2026年9月15日の結果・払戻はUNREADのまま。

### タイミング上の結論
- 最終Artifact作成が16:30:19 JST付近で、締切16:30に間に合っていない。
- よって福岡10Rは**実運用成績には混ぜない**。動作確認/復旧監査として扱う。
- finalizerの判定計算自体は非常に短時間（確認時約0.078ms）。遅延原因はモデル計算ではなく、Actions起動・Runner準備・checkout/setup/pip・データ取得などのworkflow側。

## 5. 現時点で確認できたv351の良い点
- venue-aware展示READY判定は機能している。
- 福岡10Rで展示READYまで実際に到達できた。
- prediction cache取得も成功。
- 自己copy hotfix後、exact v351 exhibition gate/finalizerがsuccess。
- final artifact生成もsuccess。
- chronology guard / result-payout未使用を維持。
- PRE 0.8034から展示後0.74939へ落ちたレースを正しくDROPできたため、展示ゲート自体が実際に判定へ効いていることを確認できた。

## 6. 現時点の問題点 / 次に直すべきこと
最優先は**LIVEで締切前に確実に最終判定を出すこと**。

問題:
1. GitHub Actions `schedule` の5分cronが期待時刻に必ず発火しない。16:15/16:20のv351 Runが確認できなかった。
2. WAIT候補でもcheckout/setup-python/pip installまで実行するため無駄なRunner時間がある。
3. matrix全候補を毎回起動するので、必要な直近レースだけを軽量に処理できていない。
4. 現行matrixはrace_code順で、締切優先ではない。
5. cron遅延が起きるとFINAL5ぎりぎりになり、今回の福岡10Rのように締切後artifactになる。
6. venueでoriginal展示必須項目が空でもoriginal fetch自体を行う箇所が残っている可能性がある。不要fetch削減余地あり。

### 次チャットでの推奨作業順
1. **最新GitHubとこの引き継ぎを最初に読む。**
2. 9月結果/払戻UNREADを確認。
3. v351 workflowのschedule発火履歴を時系列で監査し、16:15/16:20欠落の実態を確定。
4. cronだけに依存しないLIVE構成を設計する。
5. 第一候補は「1本の軽量controller/orchestratorが候補をdeadline順に管理し、展示が出たレースだけfinalizerへ送る」方式。18本のpersistent matrix jobを保持する旧方式には戻さない。
6. WAIT候補ではcheckout/setup-python/pip installをしないようprepare段階でfilterする案も比較。
7. race_code順ではなくdeadline優先を検討。
8. 実装前にこの引き継ぎへ作業予定を追記。
9. 実装後はcommit SHA / Run / Job / Artifact / 所要時間を記録。
10. 次の実レースで、展示公開→READY→exact gate→finalizer→artifactが**締切より十分前**に完了することを確認する。

## 7. head4 / 4head / legacy4についての注意
今回の会話中、ユーザーから「head4もlegacy4も1号艇だぞ」「中身まで見ろ」と強い指摘あり。

確認済み:
- `.github/workflows/trigger-4head-exhibition-original-v2.yml`
- `analyze_4head_exhibition_original_trainonly.py`

script単体では:
- `actual_head4` / `head4` をtargetにしている。
- player4/motor4/ex4/st4/turn4/straight4等を使う。
- `analyze_4head_headrate_3ren_player_st` をbase import。
- 1号艇v326を展示completeness logic共有のためimport。

ただし、これだけで「独立4号艇production」と断定しないこと。1号艇productionの相手選び/内部componentとしての親子関係があり得るため、**component targetとproduction ownershipを分けて監査する**。

workflow display名だけ `legacy-4head-research-trigger-only` に変更したcommit:
- `2074128e124a0993f3999e695a28856f179713ee`

この命名がproduction ownership上適切かは未確定。必要ならconsumer/dependency graphを追って再整理する。

`head4-jul18-19-primitives` もdefault branchの文字列検索だけでは特定できていない。歴史的workflow/artifact/commitを追って、中身のtarget/親モデルを確認してから分類する。

## 8. 重要ID一覧
- venue-aware fix: `376748f25079cd3a717fbb42da71fc8fcb5b4b9f`
- persistent WAIT（不採用）: `480c57a4da7d1b3f6f78b787beefc87790a08195`
- nonblocking polling: `b953b27d45831a5a139466bb57ea0ca0a2ffcab6`
- handoff after nonblocking: `468aba82c868ac6f741932e15a4ffb1cca5c7d42`
- 福岡自己copy hotfix HEAD: `ba7b53f9ab48170aaed179ef53ccd82c624ca621`
- Runner占有旧Run: `34938438610`
- 常滑11R旧queued Job: `104281420706`
- nonblocking v351 Run: `34939662186`
- 常滑11R nonblocking Job: `104286849859`
- 福岡10R最初のWAIT Job: `104286850028`
- 福岡10R緊急rerun/self-copy error Job: `104291330238`
- hotfix後Run: `34941864661`
- hotfix後prepare Job: `104292164481`
- hotfix後福岡10R Job: `104292235997`
- 福岡10R final Artifact: `10385348792`
- 福岡10R artifact name: `live-v351-final-202609152210`
- 徳山9R旧Run: `34934002769`
- 徳山9R旧Job: `104267980339`
- 徳山9R旧Artifact: `10382617649`
- 16:22に発火確認した別workflow Run: `34941377307` (`auto-live-3head-v288-production`)

## 9. 次の再開地点
**1号艇v351の判定ロジック自体は福岡10Rでfinal artifactまで通った。次は「締切前に確実に出すLIVE運用基盤」の修正が最優先。**

再開時はまずこのファイルと最新GitHubを読み、schedule発火欠落/遅延の監査 → controller/orchestrator方式またはprepare filter方式の比較 → 最小安全修正 → 次の実レースで締切前完了確認、の順で進める。

福岡10Rは最終DROPだったが締切後出力なので実運用成績には含めない。9月15日の結果・払戻は引き続きUNREAD。
