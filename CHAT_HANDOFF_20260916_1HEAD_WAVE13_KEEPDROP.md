# 1号艇 v351 Wave13 KEEP/DROP 引き継ぎ — 2026-09-16

## BEFORE
- 最新基準は `CHAT_HANDOFF_20260915_1HEAD_MANUAL_LIVE.md` と最新main。
- September 2026 の結果・払戻は `UNREAD` 維持。研究データは `race_code < 20260901` hard guard。
- production profile / HEAD cutoff .78 / opponent mass .375 / G2=.45 / G3=1.00 / HYBRID 3点は変更しない。
- 展示をHEAD学習特徴へ直接入れる案はREJECT済み。研究対象は post-ranking / ticket-rescue のみ。
- Wave11では低mass [.350,.375) のHEAD-hit exact3-miss 81Rのfirst pairをoracle分解し、KEEP_ONE_REPLACE_ONE=57 / REPLACE_BOTH=19 / ORDER_ONLY=5。one-replace余地は大きい。
- Wave12は結果非依存frozen guardを作り、5月で閾値0.25を選択、6月25Rではoverride=0 / rescue=0 / damage=0 / delta=0。安全に発動できるguardは未確立。production変更なし。

## これからやること
1. Wave11の57Rを、現行first pairの「残すべき1艇」と「捨てるべき1艇」に分解する。
2. boat番号、SECOND/THIRD位置、展示補正値・順位、ST、turn/straight/orig_avg、選択時の相対差、schema、場を比較し、KEEP/DROPの分離要因を監査する。
3. 単なる57R内の説明で終わらせず、結果非依存guard候補を作るため、同じ特徴定義を低mass母集団へ適用可能な形にする。
4. 小標本の場別ルールはproductionへ直接入れない。主力 `lap+turn+straight` / `lap+turn` を優先する。
5. fresh Actions Runで再現し、Run/Job/Artifact ID・commit SHA・結果・結論・次の再開地点をAFTERへ追記する。
