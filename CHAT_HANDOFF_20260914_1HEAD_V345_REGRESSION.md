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
- 前チャットと最新GitHubを再確認。最新main HEADは作業開始確認時 `1caf0e8530b411fb48450ae257e0828b8d43a02f`（v345 regression full reconstruction成功記録）。
- 現正式productionは `1HEAD_PRODUCTION_20260914_HEAD078_V345_ATTACKCORE`。PASS 276R / head 241 (87.3188%) / exact3 121 (43.8406%) / race SHA `08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd` を基準とする。
- September 2026 outcomesは今回も `UNREAD` を厳守。Jul/Augは `NON_PRISTINE_SUPPORT_ONLY`。
- 今回やること:
  1. v345正式identityを固定したまま、head-hit / exact3-miss を中心にSECOND / THIRD / ticketの相手選び失敗をrace-levelで診断する。
  2. まず現行 v317 SECOND / v318 THIRD / v320 HYBRID alpha=.70 のどこで正解艇を落としているかを分類し、改善余地を定量化する。
  3. 結果リーク型の後付け除外はせず、候補改善は事前・展示時点で利用可能な特徴だけを使う。
  4. production本体（HEAD .78 / opponent mass .375 / env_w .10 / q .65 / v345 attack_core）は固定し、相手側の比較だけを行う。
  5. 作業完了後、実測結果・commit・Actions Run/Job/Artifact ID・結論・次の再開地点をこのファイルへ追記する。

## 2026-09-14 20:xx JST v347再開前記録
- ユーザー指示「相手選びにもattackCore使ってみよう」を受け、相手艇2〜6号艇ごとに v345 と同じ attackCore 構成（EX .40 / ST .25 / straight .15 / original平均 .20）を作り、SECOND側係数 `g2` と THIRD側係数 `g3` を別々に比較する `run_v347_1head_opponent_attackcore.py` と workflow を追加済み。
- v347初回 Run `34835017760` は prepare / second / base-third / third がSUCCESSしたが、最終 attackcore Job `103949065798` は baseline assert 部分で `base.head` が pandas Series の `.head` method と衝突し、`TypeError: int() argument must be ... not 'method'` で失敗。モデル比較そのものの結論は未確定。
- 今回の再開作業は、この命名衝突だけを修正し、同じ276R・同じv345 production identityを固定してv347を再実行する。baseline `g2=0,g3=0` が 276 / 241 / 121 を再現しない場合は比較を無効とする。
- production本体は変更しない。September outcomesは引き続きUNREAD、Jul/AugはNON_PRISTINE_SUPPORT_ONLY。
- 再Run完了後、最良g2/g3・exact3・Feb-Jun pristine評価・Jul/Aug support-only評価・Run/Job/Artifact IDと採否を追記する。

## 2026-09-14 22:xx JST v347分解監査 作業開始
- v347修正版 Run `34843974949` は全job SUCCESS。attackcore Job `103978592224`、Artifact `10348980075`、digest `sha256:fca910c0bbf8b1f291a4e97c0457399ec7b4806c5151833b75700ef3c3245db9`。
- baseline `g2=0,g3=0` は 121/276=43.8406% を完全再現。attackCore ready=276/276R。
- 現時点の最良研究候補は `g2=.5 / g3=1.0`：130/276=47.1014%（+9）。Feb-Jun pristine 106/220=48.1818%（baseline比+8）、Jul-Aug support-only 24/56=42.8571%（+1）、race swap +hit 12 / -hit 3。
- 今回は25 gridを分解し、SECOND-only (`g2>0,g3=0`)、THIRD-only (`g2=0,g3>0`)、併用のどこが改善源か、Feb-Jun月別worst-monthを含めて監査する。Jul/Augは採用判断の主証拠にしない。
- September outcomesは引き続きUNREAD。productionは変更せず、分解監査後に昇格可否を判断する。

## 2026-09-14 22:xx JST v347分解監査 完了
- 25 gridをArtifact `10348980075` の `v347_grid.csv` / `v347_monthly.csv` で分解監査した。
- baseline `(g2,g3)=(0,0)`：all 121/276=43.8406%、Feb-Jun 98/220=44.5455%、Jul-Aug 23/56=41.0714%、Feb-Jun worst-month=34.8485%。
- SECOND-only最良は `(0.5,0)`：126/276=45.6522%（+5）、Feb-Jun 102/220=46.3636%（+4）、support 24/56=42.8571%（+1）、worst-month=36.3636%。SECOND tiltは弱い0.5が最良で、g2=1.0ではFeb-Junが97/220へ悪化。強く掛けるのは不安定。
- THIRD-only最良は `(0,1.0)`：128/276=46.3768%（+7）、Feb-Jun 104/220=47.2727%（+6）、support 24/56=42.8571%（+1）、worst-month=39.3939%。改善の主成分はTHIRD側。
- 併用 `(0.5,1.0)`：130/276=47.1014%（+9）、Feb-Jun 106/220=48.1818%（+8）、support 24/56=42.8571%（+1）、worst-month=40.9091%。単純なSECOND(+4 dev)＋THIRD(+6 dev)の完全加算ではないが、併用がdev hits最大。
- `(0.5,1.5)` もall 130/276だが、Feb-Junは103/220（+5）に落ち、Jul-Aug supportの+4で見かけ上並ぶため採用候補にはしない。Jul/Aug非pristineに引かれない観点でも `(0.5,1.0)` が優位。
- 月別 `(0.5,1.0)` は Feb 13/25=52.0%、Mar 15/32=46.875%、Apr 24/48=50.0%、May 27/66=40.909%、Jun 27/49=55.102%。baselineは Feb 9/25、Mar 15/32、Apr 24/48、May 23/66、Jun 27/49。改善は主にFeb +4 / May +4、Mar-Apr-Junは維持。
- したがってattackCoreを相手選びへ入れる方向は有望。特にTHIRD g3=1.0が主効果、SECONDはg2=.5の弱い補正が適切。強いg2/g3は劣化が確認でき、単調な後付け改善ではない。
- ただし同一Feb-Junで25 gridから選んだ研究候補なので、直ちにproduction昇格せず、次は `(0.5,1.0)` を固定候補としてrace-level gain/loss 15Rとticket構造を監査し、可能なら独立holdout/追加sentinelを作ってから昇格判断する。
- productionは引き続きv345 unchanged。`PRODUCTION_CHANGED=false` / `SEPTEMBER_OUTCOMES_READ=false` / Jul-Aug=`NON_PRISTINE_SUPPORT_ONLY`。
- 次の再開地点：`g2=.5/g3=1.0` を固定し、+hit12R/-hit3Rの原因分類（SECOND順位変更、THIRD順位変更、HYBRID top3境界）と、過学習耐性を確認する。
