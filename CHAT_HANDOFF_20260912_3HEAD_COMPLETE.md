# CHAT HANDOFF — 3号艇モデル COMPLETE — 2026-09-12

Repository: `merry02180218-ai/boatrace-backtest`

このファイルは **3号艇モデルだけ** の引き継ぎ用。1号艇/4号艇/5号艇の研究はここでは扱わない。

**最重要:** 次チャットでは必ず最初に最新 `main` と最新 Actions を確認すること。このファイルと新しいGitHubコード/commit/resultが競合した場合は、必ず最新GitHubを優先する。

作成時に確認した `main` HEAD は `283a85661c7ac701e45b1ff2abcd9ff3e2e53620`。このHEADの変更は1号艇v310関連であり、確認した3号艇productionコードは引き続き v288 系だった。ただし次チャット開始時に再確認必須。

---

# 1. 絶対ルール / leakage・運用原則

- 予想、判定、モデル改良、バックテスト結論の前に実際の最新GitHubコード/データを確認する。
- 古いチャット、メモリ、古いhandoffとGitHubが競合したら **GitHub最新版が正**。
- PRE/LIVE判定に対象レースの結果、払戻、着順、締切後情報を使わない。
- 結果・払戻は意思決定と買い目をfreezeした後にのみsettlementとして結合する。
- 必須入力が欠けたら fail closed。展示/ST/オリジナル展示/オッズ/Waku等を推測・デフォルト補完しない。
- 2026年7月・8月は NON-PRISTINE。繰り返し研究・確認されているのでクリーンholdout扱い禁止。
- 2025年12月〜2026年6月もfeature/rule discoveryで広く使用済み。historical/model-selection evidenceとして扱う。
- 2026年9月は outcome-blind pristine production evidence として維持する方針。9月の結果を見てルールを調整し、それを同じproductionモデルと呼ばない。
- 同じrepoを複数chatが触る可能性があるので、編集前に対象ファイルの最新SHAを再取得する。
- 古い失敗runをrerunしても古いcommitを使う。コード修正後はlatest commitから新runを起動する。

---

# 2. 現行3号艇productionモデル

現行の重要なproduction lineageは **v288**。

短く表現すると:

**結果blind PRE（v249系 S+A） -> 展示/オリ展/現在オッズ -> v243判定 + v288 S/A/B route -> v242可変点数 -> 1レース合計10,000円Dutch**

重要な用語区別:

- **PRE grade S/A/B** は v249系PREのgrade。
- productionへ持ち越すPRE候補は **S+Aのみ**。
- **v288 route S/A/B** は展示後の最終route名であり、PRE gradeとは別物。
- 特に **v288 route B != PRE grade B**。PRE grade Bはproduction候補にしない。
- v288 route A/Bは、PRE S+A候補の中でv243本線を補う独立rescue route。

---

# 3. 3号艇モデルの主要lineage / 役割

現行実装につながる主要段階:

- `v165`: 3号艇頭モデルのwalk-forward基礎。head model/feature foundation。
- `v166`: 3号艇頭時の相手・ordered pair ranking系の基礎。
- `v221`: scenario/pair系 feature expansion。
- `v222`: broad current-feature expansion。
- `v223`: unused-feature audit / head feature expansion。
- `v224`: national/form decomposition。
- `v234`: Waku10 restored replay / Waku10 reconstruction基盤。
- `v242`: 3連単ordered-pair ranking + composite odds target + 可変TopN + 10,000円Dutch。
- `v243`: 展示後final selectionのcanonical gate。
- `v249`: leakage-free PRE rolling S/A/B grading。production PREではS+Aのみ使用。
- `v288`: v243本線に加えてS/A/B route semanticsを確定し、September productionへ凍結。

古い `v249 PRE S+A -> v243 -> v242` はv288の祖先/基盤であり、v288ではこれにroute rescue semanticsが追加されている。

---

# 4. September v288 frozen production scope

September productionは **2026-09-01..2026-09-30限定**で凍結。

- history cutoff: `2026-08-31`
- PRE bias start: `2026-08-01`
- current month内部でthresholdを再学習しない。
- October以降はそのまま延長せず、prior-month freezeを作り直して監査する必要がある。

現行production builder:

- `build_3head_v288_daily_live.py`

production guard:

- September外の日付は停止。
- cache `history_cutoff` は必ず `2026-08-31`。
- target-day result/payout leakage flagは false必須。
- legacy current-universe percentile bridgeは禁止。

---

# 5. PRE入力取得ルール

現行current PRE fetcher:

- `fetch_3head_v288_pre_inputs_live.py`

入力ポリシー:

1. race card / Waku10-equivalentのprimaryは **Kyoteibiyori**。
2. Kyoteibiyoriで必要なWaku10-equivalent rowが作れない場合のみ、過去にoverlap検証済みの **direct BOATCAST Waku10 parser** をfallbackとして使用。
3. 両方で取得できないレースは除外/fail closed。
4. PREではcurrent exhibition/ST/original exhibitionを使わない。
5. result/payout endpointは使わない。
6. current complete PRE universeが120R未満ならfetcher自体をfailさせる。

manifestに保存する重要項目:

- result_blind = true
- result_or_payout_used = false
- current_exhibition_used = false
- complete_race_rows
- excluded_rows
- waku_source_counts
- fallback recovered list
- failures

Historical verifier 2026-09-11:

- run `34583558321`
- 144/144 PRE rows
- Kyoteibiyori 132
- BOATCAST fallback 12
- excluded 0

Waku関連の重要commit:

- `302ed4978c423cc741aa26f6fd583df2b1ff0e45` — historical direct BOATCAST fallback
- `14ff3b9e79f012abb7d808425feaa8ab30277125` — production Waku fallback
- `642bd2778854c62e8de50f69fc0fa6ebc360dc54` — verifier

---

# 6. PRE候補生成の実装詳細

canonical PRE scanner:

- `scan_20260911_3head_v288_pre.py`
- generic wrapper: `build_3head_v288_daily_live.py`

対象日には結果blind current rowsを作り、historical augmented frameへ追加する。

current rowには明示的に:

- `winner=0`
- `valid_result=0`
- `actual_combo=''`
- `valid_payout=0`
- `payout100=0`

を入れ、対象日結果をfeature構築に使わない。

current dayのv221/v222 fetchではtarget dayのcards/Wakuだけを与え、target-day tkz/ST/original/resultは空にする。

### v243 current head universeの作り方

単純にcurrent raceで `p3>=0.30` を使うだけではない。

実装では:

1. base feature head modelで `p>=0.30` の件数 `k` を求める。
2. full expanded feature head modelを走らせる。
3. current dayからfull-model p3上位 `k` 件をv243 head universeとして取る。

このhead universeに対してv249系PRE scoreを計算する。

### PRE score cutpoint

PRE score thresholdは **frozen prior-history training universeのみ** から学習。

September固定:

- S quantile = 70%
- A quantile = 20%
- S threshold = `3.290592837278`
- A threshold = `-4.79847489663985`

current day/monthのpercentileでthresholdを再定義しない。

PRE grade:

- score >= S threshold -> S
- score >= A threshold -> A
- else B

production候補として保持するのは **S + Aだけ**。

PRE grade Bは見送り。

---

# 7. LIVE入力・deadline safety

production workflow:

- `.github/workflows/daily-3head-v288-production.yml`
- `.github/workflows/auto-live-3head-v288-production.yml`

日次PRE bundle作成:

- 06:00 JST primary
- 06:30 JST retry/refresh

AUTO LIVE watcher:

- September中 5分間隔
- official deadlineを取得
- deadlineまで30分超なら WAIT
- 30分以内なら TRY
- deadline通過済みなら `ERROR_NO_BET`
- すでにfinal immutable artifactがあるraceは重複実行しない

LIVE scorer:

- `run_3head_v288_production_live.py`
- audited core: `run_20260911_3head_v288_live.py`

LIVEで取得するcurrent inputs:

- BOATCAST 展示タイム (`tkz`)
- BOATCAST スタート展示 (`stt`)
- BOATCAST オリジナル展示 (`orig`)
- BOAT RACE official 3連単 odds3t 120/120

取得前・取得後・decision emit直前の各段階でdeadline未通過を確認する。

120 combinations全て揃わないoddsは無効。

result/payout endpointはLIVE decisionではrequestしない。

---

# 8. 展示後feature更新

LIVE scorerではcached PRE rowへcurrent exhibitionを反映し直す。

`v51.corrected_direct(...)` を使ってcurrent:

- exhibition
- start exhibition
- original exhibition lap/turn/straight/avg

を補正値へ変換する。

主な再計算feature family:

- ex
- st
- lap
- turn
- straight
- origavg
- motor
- wr
- waku_wr
- nst
- waku_st
- waku_sr
- pastwin
- meetst

各familyでboat3対各艇margin、inside/outside margin、spread/sdを再計算。

主要composite:

- `c_wall12_weak`
- `c_attack3_stretch`
- `c_attack3_turn`
- `c_outer_follow`

---

# 9. v242 odds / variable TopN / Dutch

canonical ticket logic:

- `analyze_v242_3head_target_comp3_min5_max10.py`
- Dutch rounding foundation: `analyze_v205_3head_operational_replay.py::round_dutch`

ordered pair/trifecta ranking後、raw TopN `N=2..20` を評価し、**composite oddsが3.00に最も近いN** を選ぶ。

purchase rule:

- raw N < 5 -> NO BET / not buyable
- raw N = 5..10 -> raw N点購入
- raw N > 10 -> Top10へcap

最終購入は **1レース総額10,000円**。

Dutch:

- inverse odds allocation
- 100円単位
- Hamilton / largest-remainder rounding
- 合計を必ず10,000円にする
- zero stake ticketは購入しない

`composite odds` はvalue指標でありROIではない。

実現ROI:

`total payout / total settled stake`

外れレースは payout=0, profit=-10,000円。

---

# 10. v243 canonical final gate

LIVEで現在のhead probability `p3`、pair rank、current oddsを計算した後にv243を判定。

定数:

- KEEP = `-0.1999999999999999`
- RESCUE = `0.5672342857142857`

### v243 base

`buyable` かつ:

- `p3 >= 0.45`
- `raw_top_n` が 7..18
- `comp_odds` が 3.05..4.00

### keep

- `c_b3_minus_b5_st >= -0.1999999999999999`

**literal `-0.2` に丸めない。** 過去検証で4R余分に選択される差が出た。

### rescue

base外のときのみ:

- `c_attack3_stretch <= 0.5672342857142857`

canonical実装:

`v243 = buyable and ((base and keep) or ((not base) and rescue))`

つまり:

- base内でkeep失敗したraceをrescueで復活させない。
- rescueは **not base** にのみ適用。

---

# 11. v288 route semantics — 最重要

route precedence:

**S -> A -> B -> NO_BET**

### Route S

Sは **v243 pass必須**。

S condition:

- `c_b3_minus_b4_waku_st <= 0.4999999999999999`
- `c_b3_minus_b4_st >= -0.6`
- `c_b3_meetst <= 0.861111111111111`

したがって:

`S = v243_pass AND S_condition`

### Route A

Aは **v243 pass不要の独立rescue**。

ただし:

- raceはPRE S+A候補であること
- v242がbuyableであること
- Sが成立していないこと

A condition:

- `c_b3_minus_b4_st >= 0.6`
- `c_wall12_weak <= 0.24875`

実装:

`A = buyable AND not S AND A_condition`

### Route B

Bも **v243 pass不要の独立rescue**。

ただし:

- raceはPRE S+A候補
- v242 buyable
- S/Aが成立していない

B condition:

- `c_b3_minus_b2_motor >= 0.22388571428571424`
- `c_b3_inside_nst <= -0.0714285714285712`

実装:

`B = buyable AND not S AND not A AND B_condition`

再度重要:

**v288 route BはPRE grade Bではない。**

---

# 12. v288 historical verification

corrected route semanticsでのhistorical adopted result:

- 100 races
- 56 hits
- hit rate 56.00%
- stake ¥1,000,000
- payout ¥1,743,810
- profit +¥743,810
- ROI 174.381%

production-compatible leakage-free PRE replay before September:

- 94 races
- 52 hits
- hit rate 55.319%
- stake ¥940,000
- payout ¥1,622,070
- profit +¥682,070
- ROI 172.561%

route breakdown:

- S: 55R / 33 hits / ROI 184.062%
- A: 21R / 10 hits / ROI 149.162%
- B: 18R / 9 hits / ROI 164.717%

proof:

- run `34560827602`
- marker `V288_OPERATIONAL_PRE_REPLAY_OK`

LIVE route parity proof:

- run `34560454539`
- marker `V288_LIVE_ROUTE_PARITY_OK cases=32`

これらはhistorical/model-selection evidence。pristine future performanceとして過信しない。

---

# 13. September 1-11 production-rule retrospective

artifact:

- `v288-sep1-11-production-replay-final`

run / marker:

- run `34669018555`
- `V288_SEP1_11_REPLAY_OK`

result:

- PRE candidates: 9
- final BET: 2
- hits: 0
- stake ¥20,000
- payout ¥0
- profit -¥20,000
- ROI 0%

BET races:

- 2026-09-06 蒲郡3R — route A — actual 1-3-6
- 2026-09-09 びわこ2R — route S — actual 2-1-6

**この9月結果を見てv288を調整しない。** pristine holdoutを守る。

current-day candidate数や当日の途中runはこのhandoffへ固定しない。次チャットで最新daily artifact / auto-live artifactを必ず確認する。

---

# 14. June 2026 strict operational-process replay

目的:

2026-06-01..2026-06-30を、月初時点で利用可能な情報だけにfreezeしてv288運用processを再現。

freeze:

- history cutoff `2026-05-31`
- PRE score training strictly before `2026-06-01`
- bias start `2026-05-01`
- June S threshold `2.941228852972743`
- June A threshold `-4.868019039818082`

v288 rule自体は後から確定したため、これは **operational-process replay** でありpristine model-selection validationではない。

### June replay main files

- `build_3head_v288_operational_month_day.py`
- `replay_v288_operational_day.py`
- `prepare_v288_historical_pre_input.py`
- `aggregate_v288_june_operational_repair.py`
- `aggregate_v288_june_liveinput_fixed.py`

重要commit:

- `9cda9b2b5f921175f3e8aee8c9493144402c8a2f` — initial day build
- `470f7a22333931010ecfc9c8db3d1a4f9e59ccfe` — zero-PRE fast path
- `6fd5e8b3b0116da0b2ec50fecdf8cd7b7640f964` — historical pair-training nonfinite guard
- `e5108b938e347e4d532fa40abc6705dbd7682545` — non-Sep replay helper
- `f379315f084ec76d7a4df78a3484d0014b9342de` — BOAT RACE official racelist fallback
- `5af47ca6588dc7f6d31906590edf74961a5801ea` — parallel Waku recovery
- `7f211595fc2e9b2d8b7df64657e620f2ddb368cb` — June repair aggregator
- `e5dba6b534b9acdb2652347ce1168bb5f39e6a51` — repaired LIVE input replay
- `eef2b381f7acdf96904818e1afb01d1b93341a0d` — corrected LIVE replay aggregation automation

---

# 15. June PRE/card recovery

Historical PRE card source fallback chain:

1. BoatraceCSV archived race cards
2. Kyoteibiyori historical PRE
3. BOAT RACE official `/race/racelist` cards-only fallback

official racelist fallbackではresult/payout endpointをrequestしない。

meeting ST historyを使う場合も、埋め込みhrefの日付がtarget dayよりstrictly前だけを利用し、target-day meeting historyを除外する。

June17は旧archive card sourceに欠落がありofficial racelist fallbackで復旧。

June17:

- source `boatrace_official_racelist_fallback`
- 156 cards
- 156 complete
- Waku recovery 156
- excluded 0

probe:

- workflow `.github/workflows/probe-official-racelist-0617.yml`
- run `34683848653`
- job `103527229989`
- SUCCESS

repair run:

- run `34684264842`
- artifact ID `10295551330`
- artifact `v288-june-operational-17-repair`

---

# 16. Juneの「0 BET集計」は最終性能値ではない — 重要

30日PRE/card coverageを揃えた後のaggregate:

- run `34692240958`
- artifact `v288-june-operational-replay-final-repaired`
- artifact ID `10298185378`
- marker `V288_JUNE_30DAY_REPAIR_OK`

このrunは:

- PRE candidates 18
- BET 0

と出たが、**LIVE input reconstruction修正前のdecision replayを集計したため、v288のJune最終BET/ROI性能として使わない。**

このrunは主に:

- 30日PRE/card coverage
- source recovery
- leak guard

の監査に使う。

June BET/ROIのsource of truthは次節の `LIVEINPUT_FIXED`。

---

# 17. June corrected LIVE-input replay — 最終性能source of truth

18 PRE-candidate daysをfrozen May31 model cache + repaired historical LIVE inputsで再評価。

replay:

- workflow `.github/workflows/replay-june-v288-liveinput-fixed.yml`
- run `34689337291`
- 18 matrix jobs success

final aggregate:

- workflow `.github/workflows/aggregate-june-v288-liveinput-fixed.yml`
- run `34691540904`
- job `103547539466`
- SUCCESS
- artifact `v288-june-liveinput-fixed-final`
- artifact ID `10296859515`
- marker `V288_JUNE_LIVEINPUT_FIXED_OK`

### Corrected June final metrics

- PRE candidates: **18**
- LIVE evaluable: **15**
- input/decision errors: **3**
- genuine NO_BET: **13**
- BET: **2**
- hits: **1**
- hit rate among bets: **50.0%**
- stake: **¥20,000**
- payout: **¥30,720**
- profit: **+¥10,720**
- ROI: **153.60%**
- max drawdown: **¥10,000**

route:

- A: 1 bet / 1 hit / stake ¥10,000 / payout ¥30,720 / ROI 307.2%
- S: 1 bet / 0 hit / stake ¥10,000 / payout 0 / ROI 0%
- B: 0 bet

BET dates:

- 2026-06-06 — route S — miss — -¥10,000
- 2026-06-12 — route A — hit — payout ¥30,720 — +¥20,720

### Gate pass counts among 15 evaluable

- v242_buyable: 12/15
- v243_pass: 5/15
- S_condition: 4/15
- A_condition: 3/15
- B_condition: 0/15

### genuine NO_BET breakdown

- `v242_not_buyable`: 3
- `v243_pass_but_S_fail_no_rescue`: 4
- `v243_fail_no_A_or_B_rescue`: 6

Total = 13。

### 3 input errors

1. 2026-06-05 candidate: original exhibition unavailable / BOATCAST 403
2. 2026-06-14 candidate: original exhibition unavailable / BOATCAST 403
3. 2026-06-17 candidate: archived odds incomplete 0/120

したがってclean LIVE-evaluable populationは15。

### June odds caveat

legacy od3が取れないケースではofficial BOAT RACE closing 3連単odds archiveをrepairに使用。

これはhistorical exact purchase-time snapshotではなくclosing snapshotなので、真の当時購入時オッズなら払戻相当値が多少ずれる可能性がある。

ただしdecision logicは結果blindで、結果/払戻はdecision freeze後にのみjoin。

---

# 18. June結果の解釈

正しいJune v288 operational resultは:

**18 PRE -> 15 evaluable -> 13 genuine NO_BET -> 2 BET -> 1 HIT -> ROI 153.6%**

ただしbetは2レースだけなので統計的には極小sample。

言えること:

- 初期の「18 PRE -> 0 BET」はmodel behaviorではなくLIVE input reconstruction artifactだった。
- repair後は実際にv288 ruleでBETが発生した。
- Juneはプラスだが、2betだけでmodel provenとは言えない。
- June evaluable setではroute Bは0回。

---

# 19. Historical / production verificationで絶対に混同しないもの

1. historical adopted 100R / ROI 174.381%
   - model selection/history evidence
2. production-compatible pre-Sep replay 94R / ROI 172.561%
   - leakage-free operational compatibility evidenceだが完全なpristine future testではない
3. June corrected operational-process replay 2 bets / ROI 153.6%
   - month-frozen process audit、ただしv288 rule finalized later + tiny sample
4. Sep1-11 production-rule retrospective 2 bets / 0 hit
   - pristine production evidenceとして扱い、結果を見てretuneしない

これらを一つのROIとして混ぜない。

---

# 20. Production artifact / fail-closed behavior

AUTO LIVEがvalid final decisionをfreezeするとrace単位でimmutable artifact:

- `live-v288-final-<race_code>`

を作る。

deadline前にvalid inputが揃わなければBETを作らない。

deadline通過時:

- `ERROR_NO_BET`

有効LIVE scoringが一時的にできなければ transient attempt artifactを残し、deadline前なら次のscheduled runが再試行可能。

同race final artifactが既にあればduplicateをskip。

---

# 21. 3号艇モデルで禁止する簡略化・誤運用

- PRE Sだけを強いtierとしてstake増額しない。
- PRE grade Bをproduction candidateにしない。
- v288 route BをPRE grade Bと混同しない。
- v243 KEEP thresholdを `-0.2` に丸めない。
- v243 rescueをbase内keep失敗raceへ適用しない。
- route A/Bにv243 passを誤って必須化しない。
- route Sからv243 passを外さない。
- current-day percentileでS/A thresholdを作らない。
- missing Waku / current exhibition / original exhibition / oddsを0や平均値で埋めない。
- incomplete odds (<120)で買い目を出さない。
- deadlineを越えたsnapshotで正式買い目を出さない。
- closing historical oddsをexact purchase-time oddsと表現しない。
- composite oddsをROIと呼ばない。
- 1レースstakeを10,000円以外へ勝手に変更しない。
- Dutch方式/100円丸めを勝手に変更しない。
- September結果を見てthresholdをretuneし、同じv288と呼ばない。

---

# 22. 次チャットで最初に確認するファイル

最低限、最新mainから以下を読む:

- `CHAT_HANDOFF_20260912_3HEAD_COMPLETE.md`
- `fetch_3head_v288_pre_inputs_live.py`
- `build_3head_v288_daily_live.py`
- `scan_20260911_3head_v288_pre.py`
- `build_20260911_3head_v288_live_cache.py`
- `run_3head_v288_production_live.py`
- `run_20260911_3head_v288_live.py`
- `analyze_v242_3head_target_comp3_min5_max10.py`
- `analyze_v249_3head_pre_rolling_sab_optimize.py`
- `.github/workflows/daily-3head-v288-production.yml`
- `.github/workflows/auto-live-3head-v288-production.yml`

必要に応じてJune audit/replay filesと最新Actions artifactsも確認。

---

# 23. 次チャットでの再開手順

1. latest `main` SHAを確認。
2. 3号艇関連でこのhandoffより新しいcommitがないか確認。
3. latest daily v288 production run / artifactを確認。
4. latest auto-live v288 final/attempt artifactsを確認。
5. 今日の候補を聞かれた場合は、記憶ではなく最新daily bundleのPRE候補を使用。
6. 展示後なら最新current exhibition/original/official 120 oddsを実取得してLIVE scorerを走らせる。
7. deadline前にfreezeできない場合はNO BET。
8. performance確認ではJune source-of-truthを `v288-june-liveinput-fixed-final` にする。
9. 9月はpristine evidenceを保護し、結果からretuneしない。

---

# 24. 次チャットへ貼る開始文

`boatrace-backtest の CHAT_HANDOFF_20260912_3HEAD_COMPLETE.md と最新GitHubを読んで、3号艇モデルだけ続きを進めて。最新GitHubを最優先。現行productionはv288で、PRE S+A -> LIVE v243/v288 S>A>B -> v242可変5〜10点 -> 1万円Dutch。JuneはLIVEINPUT_FIXEDの結果を正として、Septemberはpristineのまま扱って。まず最新mainと最新3号艇Actionsを確認して。`

---

# 25. 超短縮current state

- production: **3号艇 v288**
- PRE: **v249系 S+Aのみ**
- Sep history cutoff: **2026-08-31**
- LIVE: current exhibition + original exhibition + official odds120/120
- v243: exact keep/rescue semantics
- v288 precedence: **S -> A -> B -> NO_BET**
- A/Bはv243非必須rescue、ただしv242 buyable必須
- tickets: v242 variable TopN / purchased 5〜10点 / exactly ¥10,000 Dutch
- historical 100R: 56 hit / ROI 174.381%
- pre-Sep production-compatible 94R: 52 hit / ROI 172.561%
- corrected June: 18 PRE -> 15 evaluable -> 2 BET -> 1 hit -> ROI 153.6%
- Sep1-11: 9 PRE -> 2 BET -> 0 hit。retune禁止。
- missing input / deadline violation = fail closed
- 次チャットは必ず最新GitHub/Actionsを先に確認
