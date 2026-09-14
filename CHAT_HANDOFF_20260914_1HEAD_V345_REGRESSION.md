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
- GitHub Actions Run `34828125951` 起動。現在prepareから実行中。
- September outcomesは読み込まないguardを維持。Jul/AugはNON-PRISTINE support onlyとして結果に明記する。
