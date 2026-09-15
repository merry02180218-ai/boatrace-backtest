# 1号艇 v351 2026-09-15 retrospective audit addendum

## 2026-09-15 作業前記録
- ユーザーが2026-09-15結果の開封を明示許可。retrospective auditではUNREADを解除する。過去LIVE artifactの時刻・pristine性は別管理する。
- Phase Aは結果・払戻を一切使わず、当時のPRE + 展示データ + frozen v351 / HEAD cutoff 0.78で判定とproduction買い目を先に凍結する。
- Run 34944414581 / Job 104300312733 は徳山3Rの復元に成功後、蒲郡10RのBOATCAST展示STが403で停止した。
- 2026-09-15 蒲郡10Rの締切は19:32 JSTで、当該Run時点では未来レース。403を「取得方式故障」と断定せず、未公開展示を含む可能性として扱う。
- Phase A artifactが生成されるまで結果・払戻とのmergeは行わない。

## venue completeness監査結果
- Run 34946437040 / Job 104306844965: success。
- Artifact 10387378147 `audit-v351-venue-completeness`。
- 全345R中 source_complete/model_ready は237R。108Rが展示特徴量の欠損でstrict除外。
- 徳山35R、尼崎25R、住之江5Rはmodel_ready=0。特に徳山はorig_straight=0/35のため全件除外。

## original exhibition schema監査結果
- Run 34948892215 / Job 104314826115: success。
- Artifact 10387899217 `audit-v351-original-metric-schema`。
- 345R中original exhibitionあり304R。
- 桐生01は21/21Rが `半周ラップ + まわり足 + 直線`。現行norm_metricが「ラップ」を一周へ潰すため半周と一周を混同していた。
- 住之江12は3/5R、尼崎13は24/25R、徳山18は30/35Rが `一周 + まわり足` で、直線非公開を欠損扱いしてはいけない。

## schema-correct再構築
- 半周ラップ/一周/まわり足/直線を独立チャネルとして保持する。
- 場のschemaに存在しないチャネルを欠損ペナルティにせず、存在するチャネルだけで展示比較特徴量を構築する。
- schema定義は結果列を見ずに固定する。
- 実装 `audit_v351_schema_correct_rebuild.py` は commit 991c15b767dd6cfd8e7cac49ac328669b353f999。

## schema-correct実行結果
- Run 34955007753 / Job 104334834599: success。
- Artifact 10390973051 `audit-v351-schema-correct-rebuild`。
- TOTAL 345 / SCHEMA_READY 288 / OLD_MODEL_READY 237。
- OOF_SCORED 195、HEAD 162、HEAD_RATE 83.08%。cutoff 0.78 は148R中123頭=83.11%、exact3 58=39.19%。

## 次作業：母集団差分比較
- ユーザー指示により、schema-correctで精度が下がって見える原因を分解する。
- 同一schema-correctスコアを用い、旧model_ready群、新たに復活した群、全schema_ready群を分けてcutoff 0.78のHEAD/exact3を比較する。
- 徳山18・尼崎13・住之江12を個別集計する。
- 旧237Rと新51Rというready母集団の差だけでなく、OOF scoreが存在する行数も明示し、分母の混同を避ける。
- 結果確認後、Run/Job/Artifact ID、結論、次の再開地点を追記する。
