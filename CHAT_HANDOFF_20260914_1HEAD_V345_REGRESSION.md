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
- full reconstruction GitHub Actions Run `34828125951`。prepare / second / base-third / third はSUCCESSし、最終regression job `103927840153` 実行中。

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

## 次の確認
- full reconstruction Run `34828125951` の最終regression結果をfast verifierと照合して二重確定する。
- 二重確定後は新v345 identity上のexact3 miss 155件、とくにhead-hit / exact3-missの相手選び診断へ進む。
