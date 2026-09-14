# 1号艇 v345 production regression

## 作業開始
- v345 attack_core weights は正式採用。
- production profile: `1HEAD_PRODUCTION_20260914_HEAD078_V345_ATTACKCORE`。
- 採用weights: one_ex=.40 / one_st=.25 / one_straight=.15 / one_orig_avg=.20。
- HEAD cutoff .78 / opponent mass .375 / env_w .10 / q .65 / SECOND v317 / THIRD v318 / ticket v320 alpha=.70 は維持。
- 旧identity 276R / head241 / exact3 119 / SHA `89e0b32c...` はpre-v345 sentinel。
- 今回の目的はv345 weightsをproduction計算経路に適用した専用regressionを実行し、新しい pass R / head / exact3 / race_code SHA256 を確定すること。
- September outcomes remain UNREAD. Jul/Aug are NON-PRISTINE.
