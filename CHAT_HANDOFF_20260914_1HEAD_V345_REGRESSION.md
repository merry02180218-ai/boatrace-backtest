# 1号艇 v345 production regression

## 作業開始
- v345 attack_core weights は正式採用。
- production profile: `1HEAD_PRODUCTION_20260914_HEAD078_V345_ATTACKCORE`。
- 採用weights: one_ex=.40 / one_st=.25 / one_straight=.15 / one_orig_avg=.20。
- HEAD cutoff .78 / opponent mass .375 / env_w .10 / q .65 / SECOND v317 / THIRD v318 / ticket v320 alpha=.70 は維持。
- 旧identity 276R / head241 / exact3 119 / SHA `89e0b32c...` はpre-v345 sentinel。
- 今回の目的はv345 weightsをproduction計算経路に適用した専用regressionを実行し、新しい pass R / head / exact3 / race_code SHA256 を確定すること。
- September outcomes remain UNREAD. Jul/Aug are NON-PRISTINE.

## v346 regression 実装
- `run_v346_1head_v345_production_regression.py` を追加。commit `23b7c109ec9d7c321ae0b7f221ebdcc99df90ede`。
- historical `run_v337_1head_head_cutoff_volume.py` は変更せず、旧feature routeを構築した後にproduction profileのv345 attack_core weightsだけをoverlayする。
- まずpre-v345 sentinel 276R / 241 head / 119 exact3 / SHA `89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73` を再現できることをassertし、その後v345重みで再評価する二段監査。
- `.github/workflows/v346-1head-v345-production-regression.yml` を追加。commit `fb480c6a97c5ca76468c66e4b8bbfab346a96873`。
- full reconstruction GitHub Actions Run `34828125951`。

## v345 production identity 確定
- repaired canonical v337 artifactを使う独立fast verifierを追加。
  - script commit `babf37b43abaecde130e2a4806d27974602c49e7`
  - workflow commit `12231493851422c50a3f71d97c0149aab3a17e1d`
- fast Run `34828751133` SUCCESS / Job `103926831308` / Artifact `10340843551`。
- profileへCURRENT identityを記録。commit `374381c9f65e31476d7b728e9ec831ddb11907dc`。
- verifierをCURRENT identityへlock。commit `75933a6960ab38208c269007dd6e20de2d3f7557`。
- lock後 Run `34828990049` SUCCESS / Job `103927596157` / Artifact `10340983608` / digest `sha256:e5973b04ebf9dffbd0184f9ad59ba13bdde41877ca25a508bbe649e6afdd701e`。
- `current_profile_identity_verified=true` / `pre_v345_sentinel_verified=true`。
- 現正式identity:
  - PRE_R 1114
  - PASS 276R
  - head 241 / 87.3188405797%
  - exact3 121 / 43.8405797101%
  - race_code SHA256 `08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd`
- pre-v345 sentinelは 276 / 241 / 119 / `89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73` として別保持。
- v345化でPASS総数/head数は同じだが、race identityは31追加/31除外に入れ替わり、exact3は119→121（+2）。
- `SEPTEMBER_OUTCOMES_READ=false`。9月結果は未読。
- Jul/Augは`NON_PRISTINE_SUPPORT_ONLY`のまま。

## full reconstruction 二重確認完了
- Run `34828125951` は全ジョブSUCCESS。
  - prepare `103924872439`
  - second `103926393845`
  - base-third `103926393915`
  - third `103926394046`
  - regression `103927840153`
- final Artifact `10341577466` / `v346-1head-v345-production-regression`。
- artifact digest `sha256:f83dceefe1ebd5828fa658d9cef76e581875aab739b86e78b6d6f0cdd02071d6`。
- full reconstruction result:
  - PRE_R 1114
  - PASS 276R
  - head 241 / 87.3188405797%
  - exact3 121 / 43.8405797101%
  - race_code SHA256 `08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd`
  - pre-v345 sentinel verified = true
  - race identity delta = 31 added / 31 removed
  - top venue share = 10.8695652174%
  - venue HHI = 0.0648498215
  - `SEPTEMBER_OUTCOMES_READ=false`
  - `JUL_AUG_STATUS=NON_PRISTINE_SUPPORT_ONLY`
- fast verifierとfull reconstructionが metrics / race identity SHA の両方で完全一致。v345 production identityを正式確定する。
- stale commit `1d84f552d01d223fe6ccfd89c0dc24dc6e8ddda3` のv339 continuationはこのhandoffで明示的にsuperseded。

## 次の再開地点
- v345正式identity上では exact3 miss = 155件。
- 次は head-hit / exact3-miss を中心に、SECOND / THIRD / ticket側の相手選び診断へ進む。
- v345 production本体のHEAD cutoff .78 / opponent mass .375 / env_w .10 / q .65 / v317 / v318 / v320 alpha=.70 は固定して比較する。
- September outcomesは引き続きUNREAD。Jul/AugはNON-PRISTINE support only。

## 2026-09-14 19:40 JST 今回の作業開始記録
- 現正式productionは `1HEAD_PRODUCTION_20260914_HEAD078_V345_ATTACKCORE`。PASS 276R / head 241 / exact3 121を基準とする。
- September 2026 outcomesは `UNREAD` を厳守。Jul/Augは `NON_PRISTINE_SUPPORT_ONLY`。
- v345 identity固定でSECOND / THIRD / ticketの相手選びを診断する。

## 2026-09-14 20:xx JST v347再開前記録
- 相手艇2〜6号艇ごとに v345 と同じ attackCore（EX .40 / ST .25 / straight .15 / original平均 .20）を作り、SECOND係数 `g2` とTHIRD係数 `g3` を比較。
- 初回Run `34835017760` 最終Job `103949065798` は pandas `base.head` 衝突のみで失敗。モデル結論未確定。
- 修正commit `0d74def18c58fac4f6fddc1fc68ecd2229dfcd9f`。production変更なし、September UNREAD。

## 2026-09-14 22:xx JST v347分解監査 作業開始
- 修正版 Run `34843974949` 全job SUCCESS。attackcore Job `103978592224`、Artifact `10348980075`、digest `sha256:fca910c0bbf8b1f291a4e97c0457399ec7b4806c5151833b75700ef3c3245db9`。
- baseline 121/276、best `g2=.5/g3=1.0`=130/276。Feb-Jun 106/220、Jul-Aug 24/56。

## 2026-09-14 22:xx JST v347分解監査 完了
- baseline `(0,0)`：all 121/276、Feb-Jun 98/220、Jul-Aug 23/56。
- SECOND-only `(0.5,0)`：126/276、Feb-Jun 102/220（+4）、support 24/56（+1）。
- THIRD-only `(0,1.0)`：128/276、Feb-Jun 104/220（+6）、support 24/56（+1）。
- 併用 `(0.5,1.0)`：130/276、Feb-Jun 106/220（+8）、support 24/56（+1）、worst-month 40.9091%。
- 改善主成分はTHIRD側。強いg2/g3は劣化し、単調な後付け改善ではない。
- production unchanged / September unread。

## 2026-09-14 22:xx JST v347 gain/loss ticket境界監査 完了
- Artifact `10348980075` の `v347_best_race_delta.csv` を使い、best `(g2=.5,g3=1.0)` とbaselineの的中状態が変わった15Rを全件監査した。
- 全期間15R内訳は +hit 12R / -hit 3R。Feb-Jun pristineは +hit 11R / -hit 3R = net +8。Jul-Aug support-onlyは7月の +hit 1Rのみ、8月は的中状態変化0R。
- ticketの2着艇系列（3点のsecond position）が変わったものを `SECOND boundary/rank`、2着艇系列が同じで3着艇だけが入れ替わったものを `THIRD/top3 boundary` と分類した。
- Feb-Jun pristineのSECOND系は4R：+hit 3R（202602102303, 202603212404, 202605171708）/ -hit 1R（202604061012）= net +2。
- Feb-Jun pristineのTHIRD/top3系は10R：+hit 8R（202602101612, 202602241701, 202602251412, 202604301712, 202605041909, 202605070801, 202605211601, 202606231001）/ -hit 2R（202603300608, 202606300106）= net +6。
- Jul-Aug support-onlyの唯一の変化は 202607130905 のSECOND boundaryで +hit 1。8月はgain/lossなし。
- よってFeb-Junのnet +8は `THIRD境界 +6` と `SECOND境界 +2` に分解でき、25-grid監査の「THIRDが主効果、SECONDは弱い補助」とrace-levelでも一致した。
- gainが特定1か月だけに集中する形ではなく、Feb +4、Mar net0、Apr net0、May +4、Jun net0。損失3RもMar/Apr/Junに分散しており、少数月の全勝だけで作られた改善ではない。
- 一方、最適係数は同一Feb-Jun gridから選択しているため、この監査だけで独立holdoutとはみなさない。production昇格はまだ行わない。
- 次の再開地点：`g2=.5/g3=1.0` を固定して、係数近傍（特に g2=.25/.5/.75、g3=.75/1.0/1.25）でplateau/感度監査を行い、ピンポイント最適化でないことを確認する。その後、production昇格候補v348として固定sentinelを作るか判断する。
- `PRODUCTION_CHANGED=false` / `SEPTEMBER_OUTCOMES_READ=false` / Jul-Aug=`NON_PRISTINE_SUPPORT_ONLY`。

## 2026-09-14 22:21 JST v348 local plateau監査 作業開始
- `g2=.5/g3=1.0` のピンポイント最適化懸念を監査するため、局所9点 `g2={.25,.50,.75}` × `g3={.75,1.00,1.25}` を固定比較する。
- 評価の主証拠はFeb-Jun pristineのみ。Jul/Augは`NON_PRISTINE_SUPPORT_ONLY`として参考表示だけに使い、設定選択の主証拠にはしない。September outcomesは引き続きUNREAD。
- baselineは276R / head241 / exact3 121、Feb-Jun 98/220。中央候補 `.5/1.0` は粗gridで130/276、Feb-Jun 106/220（+8）。
- plateau判定は9点のうち何点がbaselineを改善するか、中央候補±1 dev hit以内の点数、dev worst-month、月別安定性を確認する。中央だけ突出する場合はproduction昇格を見送る。
- 実装: `run_v348_1head_opponent_attackcore_plateau.py` commit `53121257be60e367d93c58328ea8413c6256e70b`、workflow `.github/workflows/v348-1head-opponent-attackcore-plateau.yml` commit `0f354ee6d1b27abbf46c85cb9084603dabceec07`。
- productionはこの監査中変更しない。完了後にRun/Job/Artifact、9点結果、plateau判定、次のproduction regression可否を追記する。
