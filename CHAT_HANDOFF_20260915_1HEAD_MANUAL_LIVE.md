# 1号艇 v351 手動LIVE 引き継ぎ — 2026-09-15

## 最重要ルール
- 最新GitHubを最優先。古いチャット・古い記憶と競合した場合は最新GitHubを採用。
- GitHub作業は必ず、作業前にこの引き継ぎへ「これからやること」を記録し、作業後にも結果・commit SHA・Actions Run/Job/Artifact ID・結論・次の再開地点を追記する。
- mainをforce updateしない。通常contents APIで更新し、連続更新時は必ず最新blob SHAを取り直す。
- 実際にtool操作・Run確認していないことを「進めた／発火した／終わった」と言わない。
- Actionsは対象workflow名とRun IDを確認する。別モデルworkflowを誤認しない。
- September 2026のレース結果・払戻は研究で読まない。`UNREAD`維持。
- LIVEでは結果・払戻を絶対に使用しない。`result_or_payout_used=False` / `chronology_guard=True`。
- 1号艇LIVEは速度最優先。締切後の判定は運用失敗扱い。

## 現行production / LIVE
- production profile: `1HEAD_PRODUCTION_20260915_HEAD078_V351_OPPONENTCORE_G2_045_G3_100`
- 現行HEAD cutoff `.78`、opponent core `SECOND G2=.45 / THIRD G3=1.00`。
- core scripts: `run_1head_v351_live_window.py`, `probe_1head_v351_boatcast_exhibition.py`, `run_1head_v351_live_exhibition_gate.py`, `run_1head_v351_live_finalize.py`。
- 1号艇のレース時刻自動controllerは停止。ユーザーが「判別して」等と依頼したときだけ直前判定。
- 03:00 JST daily preparationは承認済み。

## 03:00 daily / LIVE高速化
- LIVE bridge fail-close commit `2592874f23254a1bdc8220ebdec8ec06021c1784`。
- 03:00 JST workflow commit `f4eff2a8a534c819521cde7113b770386454d254`。
- 全R cache対応 commit `55de6538561ac8b7df36e5bdae738636c7ddae37`。
- 03:00設計: 当日全場全R causal base + PRE候補生成 → LIVE時はshared cacheから対象Rだけ読み、展示probe→gate→finalizer。
- 注意: 03:00 workflowはrolling PRE artifact依存が残っている。PRE sourceが03:00に無ければ `PRE_SOURCE_NOT_READY`。未監査。

## 2026-09-15 LIVE実績
- ユーザー評価: 当日は「全部間に合ってない」。0 usable successful races / operational failureとして扱う。
- 蒲郡12R `202609150712`: Run `34962990778` / Job `104360757399`、shared base欠損から重いv321 prepareへ入りcancel、Artifactなし。
- これを受けLIVE bridgeをcache-only fail-closeへ変更済み。

## schema復活研究 — schema-correct audit
- Run `34955947116` / Job `104337913699` / Artifact `10390159767` / success。
- TOTAL345 / SCHEMA_READY288 / OLD_MODEL_READY237 / OOF_SCORED195。
- cutoff .78 overall: 148R / HEAD123=83.11% / exact3 58=39.19%。
- OLD_MODEL_READY cutoff .78: 139R / HEAD119=85.61% / exact3 58=41.73%。
- RECOVERED_ONLY READY51 / OOF18 / cutoff .78: 9R / HEAD4=44.44% / exact3 0。
- recovered OOF18は全て `lap+turn`。JCD18=徳山13 OOF、JCD13=尼崎5 OOF、JCD12=住之江0 OOF。
- recovered OOF18では低schema_p側の方が良く、`<=.66` 5RはHEAD5/5・exact3 3/5。ただし小標本のためこの逆閾値はproduction不採用。

## schema map
- 主なschema: `lap+turn+straight`, `lap+turn`, `half+turn+straight`, `turn+straight`, `base`。
- `base` は「展示タイムのみ」と断定しない。コード上BASE=`one_ex, one_st, sec_ex_mean_margin, sec_st_mean_margin`。意味は元dataset定義を必要なら再確認。
- JCD13/JCD18は `lap+turn`。JCD19は `turn+straight`。

## 専用schema HEAD OOF — 完了
- script `audit_v351_dedicated_schema_head.py`。
- 初回実装 commit `5daed9e991bfcc1de1a56ae3557ffe9f8fab085a`。
- pandas `b.head` collision修正 commit `f0c8aeaa6196748b334d3a12e23233c662e96a0c`。
- retrigger commit `5330e0ae6f4659a1a4984d11b2d126f9da0de736`。
- Run `34979361041` / Job `104415303329` / Artifact `10401475091` / success。
- `lap+turn`: READY48 / OOF43。選択条件 C=1.5 / cutoff .82 → 25R / HEAD20=80.00% / exact3 10=40.00%。JCD13 11R HEAD81.82%、JCD18 14R HEAD78.57%。
- `half+turn+straight`: READY18 / OOF13 → 13R / HEAD11=84.62% / exact3 3=23.08%。
- `base`: READY10 / OOF3 → 3R / HEAD3=100% / exact3 2=66.67%。極小標本。
- `turn+straight`: READY5 / OOF0。評価不能。
- `lap+turn+straight`: READY207 / OOF202 → 202R / HEAD172=85.15% / exact3 79=39.11%。
- 注意: gridで同じOOF結果を見てbest cutoff/hyperparameterを選択している探索結果。独立temporal holdout前なので過度にproduction-readyと解釈しない。

## ユーザー承認済みの正式schema方針
2026-09-15 ユーザー指示:
> `turn+straight以外は正式に入れよう。ただ3連単が当てれてないからそこを研究しよう`

正式production対象として採用する方針:
- `lap+turn+straight`
- `lap+turn`
- `half+turn+straight`
- `base`（OOF3Rのみなので低標本フラグを残す）

保留:
- `turn+straight`（OOF0なので正式対象外）

重要: ユーザー承認は済んでいるが、schema別HEAD scorer/cutoffをLIVE production経路へ統合する実装・独立監査はまだ完了していない。次チャットで忘れず実装する。ただし既存v351のHEAD以外のgate/finalizer条件を勝手に変えない。

## 3連単研究 — 現在の目的
- HEAD的中率は80%台まで戻せたがexact3が低い。ここを次の主要研究テーマにする。
- 現行相手選び: v351 opponent core `G2=.45 / G3=1.00`。
- まずHEAD的中レースの3連単不的中を以下に分解する:
  1. `EXACT3_HIT`
  2. `ORDER_MISS`: 2着・3着の相手2艇自体は合っているが順序逆
  3. `OPPONENT_PAIR_MISS`: 相手艇そのものが候補から抜け
- その後、schema別に2着ranking / 3着rankingを分ける。候補特徴: 展示、ST、選手力、攻撃力、人気、相手2艇の順序、現行G2/G3。
- 「3頭内には入っているが順序違い」と「相手候補外」を必ず分離して研究する。
- 改善案は時系列OOFで比較し、同じデータで選んだbestをそのままproductionへ入れない。独立temporal holdoutを行う。

## 3連単原因分解コード — 追加済みだがworkflow未発火
- research script: `analyze_v351_schema_exact3_errors.py`
- script commit `13caab319e109080b4fcb89578f9ad90aa817f8c`。
- workflow: `.github/workflows/analyze-v351-schema-exact3-errors.yml`
- workflow initial commit `ef9821fda7fc5cb01a80cbd53f52997240f60f50`。
- scriptはhistorical audit rowsのみ使用し、`race_code < 20260901` hard guard。
- intended output: `analysis_v351_schema_exact3_errors.csv`, `analysis_v351_schema_exact3_error_summary.csv`。

### workflow発火トラブル
- 初回追加pushでは目的workflowが発火しなかった。
- retrigger前handoff commit `ce19656b446e522a002f2d02edd02f6f8ba0dce5`。
- retrigger workflow commit `ce024c355741a4a552cb4f4e77008f0964d63ccf`。
- このcommitでは4本の別workflowが起動したが、目的 `analyze-v351-schema-exact3-errors` は含まれなかった。例: monthly-backtest Run `34983883872`。目的Runではない。
- workflow YAMLの `on` を明示quote + `workflow_dispatch: {}` へ変更した commit `b0132ad0c56c537256f2ff20ec3d079da61f5d8a`。
- `b0132ad0...` 直後の確認では head_sha一致Actions Run `0件`。つまり目的workflowはまだ発火確認できていない。
- GitHub connectorのgeneric fetchでは `/actions/workflows` endpointが許可されず、workflow登録一覧を直接取れなかった。
- workflowファイル自体はmainに存在する。最新blobは次チャット開始時に必ずfetchし直すこと。

### 次チャットの最優先再開地点
1. 最新GitHubとこのhandoffを読む。
2. **作業前にこのhandoffへ次の作業予定を追記する。**
3. `.github/workflows/analyze-v351-schema-exact3-errors.yml` がなぜActionsに認識/発火されないかを特定する。
   - 他の正常に動く新規workflow YAMLと構文・triggerを比較。
   - GitHub Actionsがworkflow fileをinvalid扱いしていないかcommit/check status等で確認。
   - 必要なら正常稼働workflowの構造をコピーして最小構成へ作り直す。
   - `workflow_dispatch`を実行できるconnector actionが利用可能ならdiscoverして明示dispatchを優先。
4. 対象workflow名 `analyze-v351-schema-exact3-errors` の**実Run ID**を確認するまで「発火した」と言わない。
5. 完走までpollし、Job ID / logs / Artifact IDを取得。
6. `EXACT3_HIT / ORDER_MISS / OPPONENT_PAIR_MISS` のschema別件数・率を確認。
7. 原因に応じて2着/3着ranking研究を実装→時系列OOF→独立temporal holdout。
8. 並行して、ユーザー承認済み4 schemaのHEAD production統合を安全に実装・監査する。`turn+straight`は保留。
9. 作業後にこのhandoffへcommit/Run/Job/Artifact/結果/結論/次再開地点を追記。

## 次チャット開始用プロンプト
`boatrace-backtest の CHAT_HANDOFF_20260915_1HEAD_MANUAL_LIVE.md と最新GitHubを読んで、1号艇v351の続きから。最新GitHubを最優先。turn+straight以外のschema正式production統合と3連単相手選び研究を続けて。まず未発火の analyze-v351-schema-exact3-errors workflow を直してRun/Job/Artifactまで確認。September 2026結果はUNREAD。作業前後に必ずhandoffを更新して。`
