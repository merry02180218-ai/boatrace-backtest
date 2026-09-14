# 1号艇 v349 正式production昇格 完了

## production
- PROFILE=`1HEAD_PRODUCTION_20260914_HEAD078_V349_OPPONENT_ATTACKCORE`
- production反映 commit=`e11e75b9bcfd5f14cd586939b8a2bc91544d96b9`
- opponent attackCore version=`v349_OPPONENT_ATTACKCORE_G2_050_G3_100`
- SECOND g2=.50
- THIRD g3=1.00
- HEAD側v345設定は変更なし。

## 独立再現監査
- verifier=`run_v349_1head_production_regression.py`
- workflow=`.github/workflows/v349-1head-production-regression.yml`
- Actions Run ID=`34857980865`
- Run conclusion=`success`
- Jobs:
  - prepare=`104022395756` success
  - second=`104024025171` success
  - base-third=`104024025705` success
  - third=`104024025242` success
  - production-regression=`104025699457` success
- Artifact=`v349-1head-production-regression`
- Artifact ID=`10355950395`
- Artifact digest=`sha256:9aa31d2486d786dc6c12b403b73eb5c1c15d87d296437c9b320ae41d171eb1e4`

## 独立監査実測
- PASS=276
- HEAD=241
- EXACT3=130
- exact3 rate=47.101449275362317%
- race SHA=`08eb41e04c36d25074d6a1e471ff9334fafd34c8306cd5d336923772b613b8bd`
- ticket SHA=`50378499c439f3c13572f2ee5d4c012a812043fea34cf840e3aa47db4ebbec0c`
- core_ready_R=276
- Feb-Jun pristine=106/220
- Jul-Aug support-only=24/56
- AUDIT_SOURCE=`raw/frozen pipeline regeneration; no v348 artifact read`
- AUDIT_OK=true

## データ取り扱い
- SEPTEMBER_OUTCOMES_READ=false
- September 2026 outcomesは最後までUNREAD。
- JUL_AUG_STATUS=NON_PRISTINE_SUPPORT_ONLY
- 結果を見て後からレース除外はしていない。

## 結論
- GitHub本番反映と独立再現監査の両方が成功したため、v349の正式production昇格は完了。
- 276 / 241 / 130、race SHA、ticket SHAは固定sentinelと完全一致。

## 次の再開地点
- 今後の1号艇研究は `1HEAD_PRODUCTION_20260914_HEAD078_V349_OPPONENT_ATTACKCORE` を正式基準とする。
- September outcomesは明示的に解禁されるまでUNREADを維持する。
