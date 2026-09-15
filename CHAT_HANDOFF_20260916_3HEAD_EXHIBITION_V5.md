# boatrace-backtest 3号艇モデル 引き継ぎ — Exhibition v5 corrected freeze

Repo: `merry02180218-ai/boatrace-backtest`
Branch: `research/3head-player-attack-mode`
Date: 2026-09-16

## 最重要ルール

1. 作業開始前に最新GitHubとこの引き継ぎを読む。古いチャットより最新GitHub優先。
2. 作業前に「これからやること」を引き継ぎへ記録し、作業後も結果・commit SHA・Actions Run/Job/Artifact ID・結論・次の再開地点を記録する。
3. September 2026 race outcomes は絶対に読まない。`UNREAD`維持。
4. production は v288 のまま変更しない。94R / 52 hits / ROI 172.560638%。
5. July/August 2026 は NON-PRISTINE。
6. 研究入力は締切前情報のみ。実際の決まり手を入力に使わない。
7. exact v288 94-race exclusion を維持する。

## 今回のテーマ

3号艇相手選びへ、1号艇モデルで使っている場・枠補正済みの展示タイム / ST展示 / オリジナル展示を入れた場合に改善するかを検証した。

1号艇側の補正参照は `backtest_v51_lane_corrected_tickets.py` 系。単純な場平均差し引きではなく、枠補正 + causal ST frame bias + race-relative rank を使用。オリジナル展示は場ごとの利用可能性を考慮する。

## 固定ソース

- Source Run: `34754875342`
- Artifact: `10317157868` (`3head-wave21-allrace-source-build`)
- CSV: `analysis_v289_3head_wave21_allrace_feature_settled.csv`
- source max date <= 2026-08-31
- September outcomes: UNREAD

Canonical eligibility:
- exact v288 exclusion
- `settle__usable == 1`
- `closing_odds__ok == 1`

再現基準:
- February eligible = 3,970R
- February boat3 heads = 478R
- March eligible = 4,482R
- Wave54 March = 210R / 71 boat3 heads = 33.80952381%

## 既存相手選び基準

Reproducible opponent v1/v2/v3 の基準は direct ordered-pair logistic。
v2/v3 freeze C=.25。
March Wave54 3 tickets/R の再現値:
- 25 hits / 71
- capture 35.2113%
- stake ¥63,000
- return ¥62,830
- ROI 99.73015873%

Wave55 historical 27/71, ROI106.8889% は完全な実装再現性がなく、Wave57/Wave58も UNVERIFIED。再現可能な基準を優先する。

## Exhibition v5 初回Runは無効

初回 Run `34992010310` は canonical February heads が489Rとなり、本来478Rと一致せず、A/B/Cの比較母集団も同一ではなかったため INVALID とした。

この無効化を引き継ぎへ記録した commit:
- `57267f485ebcda177d19f1aa5923988da8c68a1e`

前回の「Bが勝者」という判断は撤回済み。

## corrected v5 実装

主な修正:
- canonical eligibility を v1 と一致
- February 3970 eligible / 478 heads を assert
- A/B/Cを同一 common-ready 母集団で比較
- GroupKFold OOF top3 capture を全OOFで算出
- venue-aware original exhibition availabilityを補正
- `--phase feb` 対応

関連commit:
- eligibility等修正: `8fe5bc4c...`
- 実行修正: `40950aef8759add2b9ddb27df992a32fcc0857af`
- fresh trigger main commit: `6d3cc14c8ce9b11294e3ce0f852a234bf36aeb3b`

実行script:
- `research/run_3head_exhibition_v5.py`

## corrected February-only freeze — 正式結果

Actions:
- Run: `34994783250`
- Job: `104468173813` (`feb-freeze`)
- conclusion: SUCCESS
- Artifact: `10407605495` (`research-3head-exhibition-v5-feb`)
- Artifact ZIP SHA256: `b4af49b233746cba3e59045c4c5e94d9247951b1c749d2d340f6e4872110689d`
- checkout research SHA: `40950aef8759add2b9ddb27df992a32fcc0857af`

Canonical verification:
- February eligible: **3970R**
- February boat3 heads: **478R**
- common exhibition/start-exhibition ready head races: **390R**
- exact v288 exclusion preserved: true
- September outcomes read: false
- production changed: false

同一390RでA/B/C比較:

### A — frozen baseline
- 67 features
- pair rows 7,800
- OOF hits **145/390**
- capture **37.17948718%**
- AUC **0.6846610609**
- fold capture SD 0.0486504

### B — baseline + corrected exhibition / ST exhibition
- 79 features
- pair rows 7,800
- OOF hits **143/390**
- capture **36.66666667%**
- AUC **0.6840994498**
- fold capture SD 0.0476951

### C — B + venue-aware original exhibition
- 103 features
- pair rows 7,800
- OOF hits **135/390**
- capture **34.61538462%**
- AUC **0.6863849960**
- fold capture SD 0.0601335

### 正式freeze

**A wins.**

展示/ST展示を直接相手選びの学習特徴へ追加しても A より2R悪化。オリジナル展示まで追加すると10R悪化。したがって、この形で展示情報を相手選びモデルへ直接追加する案は REJECT。

March結果はこの corrected February freeze の段階では開かない。Aが勝者なので展示追加案をMarchで追試して選択し直す必要はない。

## post-ranking / ticket-rescue 研究 BEFORE — 2026-09-16

これから行うこと:
- frozen baseline A の OOF ordered-pair score / top3 tickets を固定する。
- 展示を学習特徴へ再投入しない。
- February common-ready 390Rだけで、baseline top3から漏れた実着2・3着艇（ordered pair）を展示/ST展示で救えるケースを監査する。
- 同時に baseline hit を壊す damage を必ず数え、`net_rescue = rescued_miss - broken_hit` を主指標にする。
- 補正は post-ranking のみ。まず corrected exhibition と corrected ST exhibition の race-relative signal を使い、閾値/重みの小さなgridを February のみで探索する。
- original exhibition は v5 C が悪化したため初手では使わず、必要なら venue-aware の限定補正として別枝で検証する。
- tie-break は baseline score を優先し、展示差が明確なときだけ順位を動かす。
- September 2026 outcomes は読まない。production v288も変更しない。
- Februaryで正の net rescue が再現できた場合だけ、freezeした1案を March の一発診断へ進める。

## 次に試す価値がある方向

展示そのものを捨てるのではなく、**学習特徴量として混ぜずに直前の相手順位補正として使う**方向。

候補:
- frozen baseline/v288系の相手順位を壊さず、展示が明確に良い艇だけ1段上げる
- ST展示が極端に悪い艇だけ下げる
- 伸び系（展示・直線）と出足/回り足系を攻め方に応じて別補正
- baseline 3点から漏れた的中レースで、展示補正なら救えるケース数を先に監査
- 同時に baseline 的中を展示補正で壊すケース数を数え、net rescue が正か確認
- 閾値は Februaryだけで決め、Marchはfreeze後の一発診断にする

## 現在の結論

- 展示を直接相手選び特徴量へ追加: REJECT
- frozen winner: A（従来67特徴）
- production v288: unchanged
- September 2026 outcomes: **UNREAD**
- 次の再開地点: **post-ranking / ticket-rescue exhibition correction のFebruary-only実装・実行**
