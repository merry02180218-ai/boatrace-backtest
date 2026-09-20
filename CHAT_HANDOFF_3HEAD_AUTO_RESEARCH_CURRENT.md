# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research version: `v289-addon-wave1`
- decision: **NO_ADOPTION_WAVE1**
- v288 production is unchanged; baseline replay assertion is 94R / 52 hits / payout 1,622,070 yen.
- July/August are NON-PRISTINE. September outcomes were not loaded or used.
- Candidate universe is only v288 final NO_BET among operational PRE S/A and v242-buyable races.

## Wave-1 result
- candidate pool: 178 races
- best tested variant: `return_rank@0.45`
- best add-on: 84R / 15 hits / ROI 54.92% / profit -378,700 yen
- combined: 178R / ROI 117.04%

## Methods tested / dead ends retained
- `residual_hit`: prior-reject outcome effect ranking over pre-race safe features.
- `exhibition_upgrade`: current exhibition/ST/original-exhibition family only.
- `return_rank`: prior-reject realized-return ranking trained only on prior months.
- `attack_style_split`: separate stretch-vs-turn regimes, then outcome ranking.
- `orthogonal_consensus`: residual + exhibition + return independent-score consensus.
- `ev_calibrated`: residual hit score plus current composite odds, alpha chosen on prior months only.

## Real-operation audit
- all scoring inputs are columns already present before settlement in the canonical v243/v288 audit artifact;
- decisions use only prior-month outcomes for fitting; current test-month result/payout enters settlement only;
- missing features are median-imputed from prior training; production promotion must replace any required-current missingness with fail-closed gates;
- overlap with v288 baseline is zero by construction;
- no production workflow/model was changed.

## Next restart point
- If no wave-1 variant passes, next research must change the information/ticket family rather than loosen v288 thresholds.
- Priority next: opponent/ticket re-ranking on NO_BETs, PRE-B/new-population research with full leak audit, and venue/field archetype residual models.
- Before any promotion, build live shadow scorer with fail-closed source checks and exact 10,000-yen Dutch.

## Generated artifacts
- `research_v289_3head_addon.json`
- `research_v289_3head_addon.md`



## 2026-09-20 — Adopted A+.60 opponent-model stage
- Adopted head gate remains frozen: PRE q>=.925, boat3 motor EWMA-rank edge vs boat2 >= +0.20, boat3 current exhibition rank=1.
- Adopted purchase gate remains frozen: post_motor_inner_rank_edge >= +0.60.
- Nov-Jan development cohort reproduced: 118R / 54 boat3 wins = 45.76%.
- March venue-aware forward audit remains 33 purchases / 16 boat3 wins / 12 ticket hits / ROI 106.61%; March is validation only, not tuning.
- Loss-pattern research complete. motor-edge1 extra filter was rejected; do not alter A or +0.60.
- Opponent reference audit SUCCESS: Run 35467021760 / Job 105961123488 / Artifact 10591343589.
- Among 54 boat3 wins: SECOND counts 1=20,4=18,2=10,5=5,6=1; THIRD counts 6=15,4=12,5=11,2=8,1=8.
- Reference architecture frozen for next research: 1HEAD factorized SECOND+THIRD preferred over direct ordered pair; 4HEAD separate SECOND and scenario/conditional THIRD, then TOP2xTOP2 composition.
- Existing 3HEAD baseline remains V221 direct ordered-pair ranking + v242 variable TopN/Dutch.
- Next: develop role-split SECOND + conditional THIRD on Nov-Jan/earlier causal data, compare against V221 by SECOND Top1/Top2, THIRD Top1/Top2, exact-pair Top1/2/4/6/10 and monthly stability. Do not use March for selection; after freeze, one-shot March compare against current 12/16 opponent/ticket capture. September 2026 outcomes remain UNREAD.


## 2026-09-20 — 次チャット引き継ぎ：3号艇 相手モデル role-split 開発中

### 固定済み・変更禁止
- 3HEAD頭ゲートは正式採用済み A gate のまま。
- 購入ゲートは `post_motor_inner_rank_edge >= +0.60` のまま。
- Nov-Jan 開発母集団は 118R / 54頭 = 45.76%。
- March は forward validation 専用。閾値・特徴量選定に使わない。
- September 2026 結果は UNREAD 維持。
- loss filter `post_motor_rank_edge1 >= 1.0247765679169158` は March で不採用。復活させない。
- 相手モデル研究で頭/購入レース数を減らさない。下流の相手順位・買い目だけを研究する。

### March 現行基準
A + .60 の March venue-aware audit:
- 33R購入
- 16R 3号艇頭
- 12 ticket hits
- 3頭時 opponent/ticket capture 12/16 = 75%
- ROI 106.61%
この16頭/12的中を、最終的な相手モデル forward 比較基準にする。

### 相手モデル方針
ユーザー指定で 1号艇モデルと4号艇モデルを参考にする。
- 1HEAD: v317 SECOND + v318 THIRD の factorized role split。v319 direct pair より役割分離を優先。
- 4HEAD: v280/v281 SECOND/THIRD 分離 + scenario THIRD、v283 TOP2XTOP2。
- 3HEAD現行は V221 direct scenario pair + v242 TopN/合成オッズ/Dutch。
- 新案は SECOND 専用モデル + conditional THIRD `P(third|second, context)`、factorized pair score。
- まず odds を入れず opponent coverage を凍結してから March 一発検証する。

### opponent reference audit 完了
Run 35467021760 / Job 105961123488 / Artifact 10591343589 SUCCESS。
A+.60 を 118R / 54頭で再現。
54頭の相手分布:
- SECOND: 1=20, 4=18, 2=10, 5=5, 6=1
- THIRD: 6=15, 4=12, 5=11, 2=8, 1=8
SECOND の1+4 = 70.4%、THIRD の4+5+6 = 70.4%。

### role-split 開発ファイル
- `research/run_3head_a_opponent_rolesplit_dev.py`
- `.github/workflows/research-3head-a-opponent-rolesplit-dev.yml`
- trigger: `.github/triggers/research-3head-a-opponent-rolesplit-dev.txt`
Workflow name: `research-3head-a-opponent-rolesplit-dev`

目的:
- Nov-Jan のみで SECOND / conditional THIRD を学習・評価
- SECOND Top1/Top2
- conditional THIRD Top1/Top2
- factorized exact pair Top1/2/4/6/10
- V221 direct pair Top1/2/4/6/10
- overall + monthly
- expected adopted cohort 118R、head-win eval 54R
- March/Sepは選定に使わない

### 直近エラー履歴と修正
1. Run 35504986948 / Job 106063163789
   - Preflight failure: `ModuleNotFoundError analyze_v221_3head_scenario_pair`
   - repo root sys.path と preflight import を修正。
   - commits 42662c8... / 02d3e8a... / trigger f9cab3b...

2. Run 35505140396 / Job 106063562980
   - Preflight SUCCESS。
   - main failure: `SECOND training 3-head races too small: 0`
   - V221 feature frameに確定2着/3着教師ラベルがないため、results/realtimeから race_code で1〜3着を結合する修正。
   - commits 579a5ea... / trigger c359157...

3. Run 35506084018 / Job 106066029455
   - 同じ0件。
   - actual_combo形式と既存parser不一致を疑い、`3-1-4`, `3>1>4`, `3_1_4`, `314` 等のrobust parser + settlement audit追加。
   - commits 159b373... / trigger 2ef3c9c...

4. Run 35506484184 / Job 106067069592
   - failureだが監査で重要事実を確認:
     - settlement attached = 34,985R
     - parsed 3-head = 4,344R
     - sample = 1-4-6 / 3-2-5 / 6-3-4 / 3-1-2 / 1-5-4
   - よって settlement取得/parseは正常。0件化はその後の training date/filter 系。
   - `_date` を race_code YYYYMMDD から再構築し、各月 training母数と3-head件数を `train_audit` ログへ出す修正を投入。
   - fix commit `88014b8e33c54dd6fd05bbffdd387a5aa5ff60a3`
   - retrigger commit `307e1129d30352a73231659af49d081f8e90af33`

### 現在の再開地点
次チャットでは最初に **最新GitHubとこの引き継ぎを読み、role-split最新Run（trigger SHA 307e112...）の実Run ID / Job ID / statusを確認すること。**
成功ならArtifactを回収し、role-split vs V221の overall/monthly coverageを解析。
失敗ならログの `settlement_audit` と新設 `train_audit` を最優先で確認し、4,344件がどのfilterで0になるか特定して修正・再発火する。

ユーザーから「次エラー出たら隅々まで大丈夫か探査して」と明示指示あり。単発エラー修正だけでなく、workflow/preflight/import/schema/date/race_code/settlement/cohort/month counts/output/artifactまで一括監査する。

### 成功後の次段階
Nov-Janで role-split が V221 より coverage/stability 改善なら、そこで architecture/parameters をfreezeして March one-shot validation。
Marchでは33購入レースを維持し、16頭に対して現行12/16=75%と比較する。
4つの現行missは
- opponent ranking miss
- v242 TopN selection/drop
- odds/Dutch issue
に分類する。
Marchを見てから閾値を変更しない。
