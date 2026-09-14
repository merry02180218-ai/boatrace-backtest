# 1号艇 v349 相手attackCore 本番候補 固定監査

## 前提
- 正式本番はまだ `1HEAD_PRODUCTION_20260914_HEAD078_V345_ATTACKCORE` のまま。
- HEAD cutoff .78 / opponent mass .375 / env_w .10 / q .65 / SECOND v317 / THIRD v318 / ticket v320 alpha=.70 は変更なし。
- 相手attackCore候補は v348 で固定した `SECOND g2=.50 / THIRD g3=1.00`。追加の係数探索は行わない。
- September 2026 outcomes は引き続き UNREAD。
- Jul/Aug は `NON_PRISTINE_SUPPORT_ONLY`。

## v348までの根拠
- baseline: 121/276 = 43.8406%。Feb-Jun 98/220。
- 固定候補 g2=.50/g3=1.00: 130/276 = 47.1014%。Feb-Jun 106/220 = 48.1818%。
- Feb-Jun baseline比 +8的中。Jul-Aug support-onlyは24/56でbaseline比+1。
- 局所9点 `g2={.25,.50,.75}` × `g3={.75,1.00,1.25}` は9/9点すべてFeb-Jun baselineを改善し、9/9点すべて全期間baselineも改善。
- 中央だけの孤立ピークではない。

## v349 固定再現監査 完了
- 新規コード追加はGitHub安全チェックで止まったため、確定済みv348 Artifact `10351490539` の `v348_center_race_delta.csv` 276行から固定候補を直接監査した。
- Artifact digest: `sha256:24072378f5dbbb39ac9fda781f4a5fd47d146f322f75f5331b73d8a77199b216`。
- 276Rをrace_code昇順で改行連結し、v346 `identity_hash` と同じ方式でSHA256を算出。
- race identity SHA256 = `08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd`。
- これはv345正式productionの `CURRENT_EXPECTED_PASS_ID_SHA256` と完全一致。したがって対象276Rは完全同一。
- baseline exact3 = 121、候補 exact3 = 130をArtifactから再確認。
- gain/loss = +hit 12R / -hit 3R、net +9でv347/v348監査と一致。
- 買い目識別値は race_code昇順で `race_code:tickets` を改行連結してSHA256化。
- baseline ticket identity SHA256 = `bb5b7fd44245e616a1bc6455f15f2df1a59083f55196b78ac83d59abbf39daae`。
- candidate ticket identity SHA256 = `50378499c439f3c13572f2ee5d4c012a812043fea34cf840e3aa47db4ebbec0c`。

## 固定候補 sentinel
- 候補名: `v349_OPPONENT_ATTACKCORE_G2_050_G3_100`
- PASS: 276R
- HEAD: 241
- EXACT3: 130
- exact3 rate: 47.1014492754%
- race identity SHA256: `08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd`
- ticket identity SHA256: `50378499c439f3c13572f2ee5d4c012a812043fea34cf840e3aa47db4ebbec0c`
- baseline ticket identity SHA256: `bb5b7fd44245e616a1bc6455f15f2df1a59083f55196b78ac83d59abbf39daae`
- `SEPTEMBER_OUTCOMES_READ=false`
- `JUL_AUG_STATUS=NON_PRISTINE_SUPPORT_ONLY`
- `PRODUCTION_CHANGED=false`

## 結論
- `g2=.50/g3=1.00` は、同一276R上で 121→130 的中を再現し、race identityもv345正式本番と完全一致した。
- 買い目identityも固定できたため、候補の再現監視が可能になった。
- ただしFeb-Jun同一開発期間由来のため独立holdoutではない。現時点では候補sentinel確定までとし、正式production変更はまだ行わない。

## 次の再開地点
- 正式production昇格を行う場合は、`onehead_production_profile.py` に opponent attackCore `g2=.50/g3=1.00` と候補sentinel（276/241/130、race SHA、ticket SHA）を明示してから、独立verifierで再確認する。
- その昇格判断まではv345 productionを維持する。

## 2026-09-14 production昇格作業 開始
- ユーザー指示により `v349_OPPONENT_ATTACKCORE_G2_050_G3_100` を正式productionへ昇格する作業を開始。
- 最新GitHubの `onehead_production_profile.py` は確認時点で `1HEAD_PRODUCTION_20260914_HEAD078_V345_ATTACKCORE` のまま。
- 既存v345 HEAD側 attackCore、HEAD_MODEL=v308、HEAD_CUTOFF=.78、OPPONENT_MASS_MIN=.375、SECOND=v317、THIRD=v318、ticket=v320 alpha=.70、env_w=.10、q=.65 は維持する。
- 追加する相手attackCoreは SECOND g2=.50 / THIRD g3=1.00 のみ。
- 新production名は `1HEAD_PRODUCTION_20260914_HEAD078_V349_OPPONENT_ATTACKCORE` とする。
- 新sentinelは PASS=276 / HEAD=241 / EXACT3=130 / race SHA=`08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd` / ticket SHA=`50378499c439f3c13572f2ee5d4c012a812043fea34cf840e3aa47db4ebbec0c`。
- 旧v345およびpre-v345 sentinelは再現用に残す。
- production反映後、独立verifierをGitHub Actionsで実行し、上記sentinel完全一致を確認するまで昇格完了とはしない。
- September 2026 outcomesは絶対に読まず `SEPTEMBER_OUTCOMES_READ=false` を維持する。
- Jul/Augは `NON_PRISTINE_SUPPORT_ONLY` のみ。
