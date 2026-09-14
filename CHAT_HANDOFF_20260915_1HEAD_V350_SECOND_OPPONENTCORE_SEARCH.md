# 1号艇 v350 2着 opponentCore 係数探索

## 作業開始
- 正式基準は v349 production。
- 3着側は現行係数 `g3=1.00` を固定する。
- 今回は2着側の opponentCore 係数 `g2` だけを細かく探索する。
- 目的は単一点の最大値ではなく、Feb-Jun pristine の的中数・月別安定性・近傍台地性を見て適切な g2 を決めること。
- Jul-Aug は `NON_PRISTINE_SUPPORT_ONLY` として参考値のみ。
- September 2026 outcomes は UNREAD のまま維持する。
- 結果を見て対象レースを後から除外しない。

## 命名ルール
- v350以降の新規コード、Workflow、Artifact、引き継ぎでは `opponentCore` を使用する。
- 既存v349 productionの名称は再現性のため変更しない。

## 検証予定
- g3=1.00固定。
- g2を現行 .50 の周辺から細粒度で走査する。
- 比較基準は現行 v349 の g2=.50 / g3=1.00。
- Feb-Jun pristine を最優先し、月別最悪値、全期間、Jul-Aug support-only、race-level gain/loss も確認する。
- 最良点の前後も比較して過学習的な尖りか台地かを確認する。

## 実装・Run
- 探索スクリプト=`run_v350_1head_second_opponentcore_search.py`
- workflow=`.github/workflows/v350-1head-second-opponentcore-search.yml`
- g2=0.00〜2.00を0.05刻み、41点。
- rankingは修正版で `Feb-Jun dev_hits desc → Feb-Jun worst-month desc → 現行.50からの距離 asc`。
- Jul-Augはranking/tie-breakに不使用。
- ranking修正 commit=`377b1f207b0fc790d232950b626f6428cd61a8f0`

## 修正版正式探索Run
- Actions Run ID=`34865283208`
- Run conclusion=`success`
- Jobs:
  - prepare=`104047448231` success
  - third=`104049615422` success
  - second=`104049615463` success
  - base-third=`104049615756` success
  - search=`104051424923` success
- Artifact=`v350-1head-second-opponentcore-search`
- Artifact ID=`10358221883`
- digest=`sha256:c12513db2f405ed84a26f59b327a394e213787443e9a27b81826a4711c6c77a4`

## 結果
### 現行 g2=.50 / g3=1.00
- all=130/276 = 47.1014492754%
- Feb-Jun pristine=106/220 = 48.1818181818%
- pristine worst-month=40.91%
- Jul-Aug support-only=24/56

### Best pristine g2=.45 / g3=1.00
- all=131/276 = 47.4637681159%
- Feb-Jun pristine=107/220 = 48.6363636364%
- pristine worst-month=40.91%
- Jul-Aug support-only=24/56
- vs current race swaps: +hit 1 / -hit 0

### 近傍
- g2=.30: all 130 / dev 106 / support 24
- g2=.35: all 130 / dev 106 / support 24
- g2=.40: all 130 / dev 106 / support 24
- g2=.45: all 131 / dev 107 / support 24
- g2=.50: all 130 / dev 106 / support 24
- g2=.55: all 131 / dev 107 / support 24
- g2=.60: all 128 / dev 104 / support 24
- bestから1 pristine hit以内は6点、g2=.30〜.55。
- .60で明確に悪化。

## 結論
- 41点探索では `g2=.45` がpristine ranking上の最良。
- `g2=.55` も同じ 131/276・107/220 で同率性能。
- 現行 `.50` より改善は+1 hitのみなので、まだproduction変更はしない。
- 適切な2着係数の最終決定には、次に `.45〜.55` を0.01刻み程度で細分化し、どの境界で+1 hitが成立するか、race-level swapと月別安定性を確認する。

## データ取り扱い
- `SEPTEMBER_OUTCOMES_READ=false`
- `JUL_AUG_STATUS=NON_PRISTINE_SUPPORT_ONLY`
- `PRODUCTION_CHANGED=false`

## 次の再開地点
- v349 productionを基準のまま維持。
- g3=1.00固定。
- g2=.45〜.55をさらに細粒度探索し、.45/.55の同率点の間に安定した台地があるか確認する。
