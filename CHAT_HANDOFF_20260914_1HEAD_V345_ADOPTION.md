# 1号艇 v345 attack_core weight adoption

## 作業前
- User approved adoption of v345 attack_core weights.
- Adopted weights: one_ex=.40 / one_st=.25 / one_straight=.15 / one_orig_avg=.20.
- v345 diagnostic Run 34810960669 / Job 103872046240 SUCCESS.
- Artifact 10334534376 `v345-1head-attackcore-weight-diagnostic`, digest sha256:4712a4f6c6769562ddd56e16cdd9d6e9022018be5d686092034ffe718a06c0fb.
- Historical diagnostic: current .30/.30/.23/.17 hit Spearman ~.362, return ~.366, worst LOMO ~.294; adopted .40/.25/.15/.20 hit ~.399, return ~.397, worst LOMO ~.352.
- Formal production before this change: profile `1HEAD_PRODUCTION_20260914_HEAD078`, HEAD cutoff .78, v332 ATTACK_ENV_SOFT env_w=.10 q=.65, SECOND v317, THIRD v318, ticket v320 alpha=.70.
- September outcomes remain UNREAD. Jul/Aug NON-PRISTINE.

## 今回やること
- Production profileにv345 attack_core weightsを正式記録する。
- Historical research modulesは再現性のため凍結し、production側で新weightsを明示する。
- 9月結果は読まない。
- 採用後の引き継ぎをこのファイルへ追記する。
