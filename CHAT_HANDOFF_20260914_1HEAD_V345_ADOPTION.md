# 1号艇 v345 attack_core weight adoption

## 作業前
- User approved adoption of v345 attack_core weights.
- Adopted weights: one_ex=.40 / one_st=.25 / one_straight=.15 / one_orig_avg=.20.
- v345 diagnostic Run 34810960669 / Job 103872046240 SUCCESS.
- Artifact 10334534376 `v345-1head-attackcore-weight-diagnostic`, digest sha256:4712a4f6c6769562ddd56e16cdd9d6e9022018be5d686092034ffe718a06c0fb.
- Historical diagnostic: current .30/.30/.23/.17 hit Spearman ~.362, return ~.366, worst LOMO ~.294; adopted .40/.25/.15/.20 hit ~.399, return ~.397, worst LOMO ~.352.
- Formal production before this change: profile `1HEAD_PRODUCTION_20260914_HEAD078`, HEAD cutoff .78, v332 ATTACK_ENV_SOFT env_w=.10 q=.65, SECOND v317, THIRD v318, ticket v320 alpha=.70.
- September outcomes remain UNREAD. Jul/Aug NON-PRISTINE.

## 採用完了
- `onehead_production_profile.py` を更新。
- 新PROFILE_NAME: `1HEAD_PRODUCTION_20260914_HEAD078_V345_ATTACKCORE`。
- EXHIBITION_MODEL: `v332_ATTACK_ENV_SOFT_V345_ATTACKCORE`。
- 正式attack_core weights:
  - `ATTACK_CORE_W_ONE_EX = 0.40`
  - `ATTACK_CORE_W_ONE_ST = 0.25`
  - `ATTACK_CORE_W_ONE_STRAIGHT = 0.15`
  - `ATTACK_CORE_W_ONE_ORIG_AVG = 0.20`
- production profile更新commit: `012d1f9f8295d985e7f70c603264c1930f0ba99c`。
- historical v332/v337 modulesは旧weightsの再現性維持のため変更していない。
- 旧v337 identity 276R / head241 / exact3 119 / SHA `89e0b32c...` はpre-v345 regression sentinelとして保持。新weights適用後の正式identityは専用regressionで再確定する必要がある。
- HEAD cutoff .78 / opponent mass .375 / env_w .10 / q .65 / SECOND v317 / THIRD v318 / ticket v320 alpha .70 は変更なし。
- `SEPTEMBER_OUTCOMES_READ=false`。9月結果は読んでいない。

## 次工程
- v345 weightsをproduction計算経路へ適用した専用regressionを走らせ、新しいpass R/head/exact3/race_code SHAを確定する。
- そのregressionまでは旧identity値を新weightsの結果だと誤認しないこと。
