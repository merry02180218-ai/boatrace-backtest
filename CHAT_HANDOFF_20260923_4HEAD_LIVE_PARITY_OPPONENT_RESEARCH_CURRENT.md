# CHAT_HANDOFF_20260923_4HEAD_LIVE_PARITY_OPPONENT_RESEARCH_CURRENT.md

## 0. 目的 / 次チャット開始点
Repo: `merry02180218-ai/boatrace-backtest`

2026-09-23時点の4号艇モデルについて、このチャットでは主に以下を実施した。
1. 4号艇LIVE運用と標準PH5の最終BET判定が一致しているか監査。
2. 不一致を発見し、LIVE最終ゲートを標準PH5へ合わせた。
3. 9/22 replayで標準/LIVEが同じ1R（常滑7R）になることを確認。
4. LIVE出力へ standard-vs-LIVE parity audit を追加。
5. 現行PH5＋相手選び SECOND/THIRD の6〜8月成績を再確認。
6. 相手選び研究を開始。PLAYERHistory＋Waku10の因果的事前特徴を使う研究v1を追加し、Run SUCCESSまで確認。
7. 現時点の次タスクは「2着候補（SECOND）改善」が最優先。頭モデルPH5は固定し、本番変更はまだしない。

次チャットでは、まずこのファイルと最新mainを読み、Run 35844974687 の相手研究v1結果を基点に、SECOND再ランキング/救済モデル研究を続ける。

---

## 1. 標準PH5とLIVEの不一致発見
標準PH5 walk-forwardの最終選択は:
- `head_prob >= .36`
- `orig4_adv_inside >= -.06`

標準側: `audit_4head_ph5_live_walkforward.py`
選択:
`selected=bool(hp>=.36 and orig>=-.06)`

一方、修正前LIVE `run_4head_120r_lastminute_fast.py` は PH5 head probability自体は使っていたが、最終BETは旧 `newfeature_decide()` の `d['selected']` をそのまま使っていた。
このため9/22 replayで:
- 標準PH5: 1 BET
- 旧LIVE: 20 BET
となり、LIVE/標準が不一致だった。

### 修正
Commit:
`eaa598beba2b8cf62c6a30d08d358d8ac244f742`
message: `fix: align 4head LIVE production gate with frozen PH5 standard`

LIVEで旧newfeature判定は診断値として残し、production selectedをPH5標準へ置換:
```python
d=newfeature_decide(hp,mass,comp,exh,cards[code],state,a.jcd)
sadv=structural_advantages(exh)
ph5_standard_selected=bool(
    hp>=.36 and
    sadv['orig4_adv_inside'] is not None and
    sadv['orig4_adv_inside']>=-.06
)
d['legacy_newfeature_selected']=bool(d['selected'])
d['selected']=ph5_standard_selected
d['ph5_standard_selected']=ph5_standard_selected
d['selection_policy']='PH5_V31_P036_ORIG_M006'
```

Replay trigger commit:
`1f4efdf01465ace64728c78fed640f1421452572`

Run 35821669664 / Job 107054634171 SUCCESS.
結果:
- watchlist 36
- frozen 33
- valid 33
- BET 1
- head4 1
- hit 0
- stake 10,000
- payout 0
- ROI 0
- BETは常滑7R
- hp 0.387234...
- ticket_count 6
- actual 4-3-2

これで9/22は標準PH5と修正後LIVEが同じ1R（常滑7R）、同じhp、同じ6買い目になった。

---

## 2. LIVE parity audit追加
Commit:
`30daeb271ba2b5817b994e9102bc1f74c6796bcc`
message: `audit: persist standard-vs-LIVE PH5 parity on every decision`

LIVE出力へ:
```python
'selection_policy_artifact':'artifacts/head4_ph5_production_v31_20260831.json',
'standard_parity':{
  'standard_selected': bool(...),
  'live_selected': bool(d['selected']),
  'match': bool(...),
  'head_cut': .36,
  'orig_cut': -.06
}
```
を追加。
今後は各レースで `match=true` が前提。

旧 `.github/workflows/replay-4head-live-20260922-v3.yml` はinvalid/古いworkflowでpushのたびfailureが出ることがある。現在の本体評価とは分離して扱う。v3 failureを本番失敗と誤認しない。

---

## 3. 現在のPH5頭モデル
Frozen artifact:
- ID: HEAD4_PH5_PRODUCTION_V31_20260831
- artifact: `artifacts/head4_ph5_production_v31_20260831.json`
- LogisticRegression C=.5
- cut=.36
- 35 features
- same-day result禁止
- September labels未使用

PH5 PLAYERHistory 5特徴:
- b4_pl_all_win
- b4_pl_all_p2
- b4_pl_frame_win
- b4_pl_frame_p2
- b4_pl_recent_p2

PLAYERHistoryはtarget dateより前だけで更新する因果的特徴。

標準最終ゲート:
- hp >= .36
- orig4_adv_inside >= -.06

頭モデルは今回の相手研究では変更しない。

---

## 4. 現行相手選び
Production module:
`run_4head_v291_third010_live.py`

Policy:
`HEAD4_V291_COMP7_OPP_S011_T018`

現在:
- SECOND_GAP = .11
- THIRD_GAP = .18
- MIN_TICKETS = 4
- MAX_TICKETS = 9
- 1レース総額 historical audit = JPY10,000
- 資金配分 = 均等買いではなくinverse-odds Dutch
- 100円単位
- 買い目数は固定6点ではない。4〜9点可変。
- 6〜8月163Rの平均点数 = 7.711656点

基本はv283 Top4を維持し、
- SECOND rank2/rank3差が閾値以下ならrank3 SECONDを救済し、そのSECONDの上位THIRDを追加
- 選択SECONDごとにTHIRD rank2/rank3差が閾値以下ならrank3 THIRD追加

ユーザーへ「6点固定ではなく4〜9点可変」と説明済み。

---

## 5. 現行6〜8月成績
対象: PH5標準最終ゲート + 現行相手選び。
Run系で再現済み。

月別:
- 2026-06: 47R / 4頭24 / 頭率51.06% / 3連単13 / 的中率27.66% / ROI 89.21%
- 2026-07: 57R / 4頭27 / 頭率47.37% / 3連単22 / 的中率38.60% / ROI 122.18%
- 2026-08: 59R / 4頭30 / 頭率50.85% / 3連単21 / 的中率35.59% / ROI 117.30%

合計:
- BET 163R
- 4号艇頭 81R
- 頭率 49.69%
- 3連単的中 56R
- 3連単的中率 34.36%
- 4頭81Rに対する相手捕捉 56/81 = 69.14%
- stake 1,630,000
- payout 1,807,760
- profit +177,760
- ROI 110.9055%
- max drawdown 135,690
- max losing streak 11
- avg points 7.711656

重要: これは「1万円均等買い」ではない。
1R合計1万円のDutch配分。買い目ごとのオッズ逆数に応じて概ね払戻を均す。実運用の5,000円化を研究する場合は100円丸めの影響があるため、単純1/2ではなく実コードで再計算する。

---

## 6. 相手選び研究を開始した理由
ユーザー:
「相手選び研究しようか PLAYERHistoryとかwaku10入ってるんだっけ」

確認:
- PLAYERHistoryはPH5頭確率には入っている。
- Waku10も既存v93/研究系には存在。
- しかし現行相手選びは主にp2/pcランキング＋SECOND/THIRD gap救済で、PLAYERHistory/Waku10を「相手専用」に十分最適化していない。

方針:
- PH5頭モデルは固定。
- BET母集団163Rを固定。
- 特に実際に4頭だった81Rで、現行買い目が取れなかった25Rを研究。
- 平均7.71点を大きく増やさず、相手捕捉69.14%とROI改善を狙う。
- 目安は平均8点前後。
- 本番変更は検証完了までしない。

候補特徴:
PLAYERHistoryを2/3/5/6号艇へ展開:
- all_win
- all_p2
- frame_win
- frame_p2
- recent_p2

加えて:
- Waku10
- 現行v283 opponent primitives
- 展示/ST/オリジナル展示
- モーター
など。

---

## 7. 相手研究v1追加
新規:
`research_4head_opponent_player_waku_v1.py`

最初のcommit:
`c0b7081b7f3c44ef799ce404fdfaea35a1040c42`
message:
`research: add causal PLAYERHistory Waku10 opponent diagnostics`

目的:
- frozen PH5 production BETだけを対象。
- PLAYERHistoryは `research_4head_player_waku_soft_ablation_v23.build_ph()` を利用しprior-day causal。
- Waku10は `research_4head_waku10_rel43_v4.build_waku()` のpre-race data。
- September outcomesを読まない。
- productionを変更しない。
- 4頭レースのcovered/missedで事前特徴を診断。

Workflow:
`.github/workflows/audit-4head-ph5-live-walkforward.yml`
へ相手研究stepとartifact pathを追加。

### 途中エラー1: YAML literal \n
Workflow編集時、stepとartifact pathにliteral `\n` が入りYAML不正。
Commit:
`baa90290b4be83b4178d726339c612cd0a98968e`
message:
`fix: restore real YAML newlines in opponent research workflow`
で実改行へ修正。

注意: 過去にもliteral \n事故が多発している。今後GitHub編集では必ずfetchして実ファイル確認。危険なglobal replaceは禁止。

### 途中エラー2: 出力ファイル名
Run 35843266424 はPH5本体は成功したが相手研究だけfailure。
Job 107123192121。
原因:
`FileNotFoundError: /tmp/head4_ph5_live_walkforward/decisions.csv`

PH5 audit実際の出力は:
`/tmp/head4_ph5_live_walkforward/race_detail.csv`

修正commit:
`f0439efdc43ffd2e3ffe500e5c7822adeb02046a`
message:
`fix: read frozen PH5 race_detail output in opponent research`

さらに相手研究スクリプト変更でもworkflowが発火するようpathsへ追加。
Commit:
`f455db1d560a9a0f0e292200e921ca49f7d41643`
message:
`ci: trigger PH5 audit on opponent research changes`

---

## 8. 相手研究v1 SUCCESS
最終Run:
- Run 35844974687
- Job 107128815614
- conclusion SUCCESS

Run URL:
https://github.com/merry02180218-ai/boatrace-backtest/actions/runs/35844974687

ログ:
```
OPPONENT_MISS_COUNTS {"COVERED": 48, "SECOND_OUTSIDE_TOP2": 26, "THIRD_OUTSIDE_SELECTED": 7}
HEAD4_PH5_LIVE_WALKFORWARD_OK
{"production_bets": 163, "head4_R": 81, "covered": 56, "missed": 25,
 "PLAYER_HISTORY": "causal prior-day",
 "Waku10": "pre-race only",
 "SEPTEMBER_OUTCOMES_READ": false,
 "PRODUCTION_CHANGED": false}
HEAD4_OPPONENT_PLAYER_WAKU_V1_OK
SEPTEMBER_UNREAD
```

研究artifact directory:
`/tmp/head4_opponent_player_waku_v1/`
主な出力:
- head4_opponent_causal_features.csv
- feature_miss_deltas.csv
- meta.json

PH5 parent artifactも同Runで作成。

注意:
OPPONENT_MISS_COUNTSのCOVERED 48 / SECOND_OUTSIDE_TOP2 26 / THIRD_OUTSIDE_SELECTED 7 はparent auditの分類ロジック上の集計で、production hit=56との数え方が完全同一ではない。次研究で分類定義を精査し、81Rの「現行的中56/外れ25」と整合させること。数字をそのまま足して25と比較しない。

最重要の示唆:
- THIRDだけ広げるより、SECOND候補ランキング/救済改善が優先。
- SECOND_OUTSIDE_TOP2が大きい。
- 次はPLAYERHistory＋Waku10でSECOND再ランキング/救済を研究する。

---

## 9. 次にやること
### 最優先
相手研究v2:
1. Run 35844974687 artifact / logsを回収。
2. `feature_miss_deltas.csv` を確認。
3. 現行SECOND p2に、各艇PLAYERHistory/Waku10を足した再ランキング候補を作る。
4. leakage-free walk-forwardで評価。
5. 6月で探索/選択し、7〜8月はholdout、または月次rolling-origin。未来月を選択に使わない。
6. 9月結果は引き続き研究選択には使わない（LIVE historyとして過去日を使う場合はユーザー許可済みだが、今回の6〜8月benchmarkと混ぜない）。
7. 頭PH5選択163Rは固定。
8. 比較指標:
   - 3連単 hits
   - 4頭時 opponent capture
   - avg ticket count
   - ROI
   - monthly ROI
   - max drawdown
   - losing streak
   - SECOND actual rank distribution
   - THIRD actual rank distribution
9. 平均点数は現行7.71を基準に、できれば8前後まで。
10. 本番採用は7〜8月holdout改善とリーク監査を通ってから。

### 研究案
A. SECOND rank3救済の判定を単純p2 gapだけでなく、
- candidate PLAYERHistory relative score
- Waku10 frame strength
- ST/exhibition
- motor
で補正。

B. 既存p2を完全置換せず「soft rerank」から始める。
現行強いベースを壊さないため:
`p2_adjusted = logit(p2) + alpha * PH_score + beta * Waku_score`
などを研究し、alpha/betaは開発期間だけで選ぶ。

C. 2着候補を3艇へ増やす場合も全レース無条件ではなく、PH/Waku救済条件付き。
点数増加とDutch dilutionによるROI低下を必ず同時評価。

D. THIRDは現行.18を一旦固定し、SECOND改善だけの寄与を分離。その後THIRDも再研究。

---

## 10. 9/22 replay関連
旧 broad LIVE replay:
Run 35817582564 / Job 107042322764
- BET 20
- head4 4
- hits 3
- ROI 133.06%
これは旧newfeature final selectionなので現在のproduction比較には使わない。

PH5 replay gate修正:
`a37cbb392bbc1108a0b92cd9c025959678563110`
Run 35818854216 / Job 107046170757 SUCCESS
BET 1 常滑7。

常滑7 opponent diagnostic:
Run 35819580087 / Job 107048357940 SUCCESS。
p2:
- 2: .52910
- 5: .23580
- 1: .10949
- 3: .07736
- 6: .04824
SECOND rank [2,5,1,3,6]
actual = 4-3-2
3号艇SECONDを4位にして落とした例。
もしSECOND=3を拾えていれば、その条件付きTHIRDで2はトップだった。
現行tickets:
- 4-2-5
- 4-5-2
- 4-2-3
- 4-5-1
- 4-2-1
- 4-5-3
この実例もSECOND改善研究の参考にする。

---

## 11. LIVE/データ運用注意
- September LIVEはユーザー許可により、9/23判定なら9/22までを因果的履歴として利用可。
- same-day resultは絶対禁止。
- historical 9/22 replayなら9/21まで。
- frozen Aug31 artifactは再現性基準として維持。
- leakage audit strict。
- result/payoutはdecision freeze後だけjoin。
- oddsはpredeadline official OD3優先。
- closing odds fallbackはhistorical audit上存在するため、タイミング差を明示。

---

## 12. 9/23 watchdog依存バグ（このチャット以前から継続事項）
徳山1R actual watchdog Run 35796574270:
`ModuleNotFoundError: No module named 'pandas'`
そのため徳山1はPRE yesでもfinal LIVE unjudged。
依存修正:
commit `aa4a7c57c3eee859c0ffd6e61417bfad6007f39c`
watchdog pip installへ pandas/scipy/scikit-learn等追加。
strict workflowにも同様の不足がないか必要時確認。

---

## 13. エラー防止ルール
ユーザーはエラー多発を強く気にしている。必ず:
1. 編集前に最新main fetch。
2. source/workflow編集後に内容をfetchして確認。
3. Pythonはpy_compile。
4. YAMLはliteral `\n` が入っていないか確認。
5. path/file名を実出力と照合。
6. dependencies/env/path確認。
7. leakage確認。
8. 検査後に発火。
9. failure時はログのroot causeを取ってから修正。blind rerun禁止。
10. SUCCESSログ確認前に「完了」と言わない。

特にliteral `\n`事故は再発させない。

---

## 14. 主要commit一覧
- eaa598beba2b8cf62c6a30d08d358d8ac244f742 — LIVE final gateをPH5標準へ統一
- 1f4efdf01465ace64728c78fed640f1421452572 — 9/22 replay trigger
- 30daeb271ba2b5817b994e9102bc1f74c6796bcc — standard-vs-LIVE parity audit
- c0b7081b7f3c44ef799ce404fdfaea35a1040c42 — opponent PLAYERHistory/Waku10 research v1
- baa90290b4be83b4178d726339c612cd0a98968e — workflow real newline fix
- f0439efdc43ffd2e3ffe500e5c7822adeb02046a — decisions.csv -> race_detail.csv fix
- f455db1d560a9a0f0e292200e921ca49f7d41643 — opponent script changes trigger workflow

---

## 15. 主要Run一覧
- 35821669664 / 107054634171 — patched LIVE parity replay SUCCESS
- 35843266424 / 107123192121 — PH5本体成功、opponent研究のみFileNotFoundでfailure
- 35844974687 / 107128815614 — opponent PLAYERHistory/Waku10 v1 SUCCESS

---

## 16. 次チャット用一文
「CHAT_HANDOFF_20260923_4HEAD_LIVE_PARITY_OPPONENT_RESEARCH_CURRENT.md と最新GitHubを読んで、Run 35844974687 の PLAYERHistory＋Waku10相手研究v1結果から、SECOND再ランキング/救済モデル研究を続けて。PH5頭モデルと163R母集団は固定、本番変更はholdout・リーク監査後。」

