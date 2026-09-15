# 1号艇 v351 2026-09-15 retrospective audit addendum

## 2026-09-15 作業前記録
- ユーザーが2026-09-15結果の開封を明示許可。retrospective auditではUNREADを解除する。過去LIVE artifactの時刻・pristine性は別管理する。
- Phase Aは結果・払戻を一切使わず、当時のPRE + 展示データ + frozen v351 / HEAD cutoff 0.78で判定とproduction買い目を先に凍結する。
- Run 34944414581 / Job 104300312733 は徳山3Rの復元に成功後、蒲郡10RのBOATCAST展示STが403で停止した。
- 2026-09-15 蒲郡10Rの締切は19:32 JSTで、当該Run時点では未来レース。403を「取得方式故障」と断定せず、未公開展示を含む可能性として扱う。
- これからaudit workflowをfail-fastからvenue/race単位のskip方式へ変更し、現時点で展示READYの候補だけを復元してartifact化する。未READY/取得失敗はerrors/skippedとして保存し、他レースの監査を止めない。
- Phase A artifactが生成されるまで結果・払戻とのmergeは行わない。

## venue completeness監査結果
- Run 34946437040 / Job 104306844965: success。
- Artifact 10387378147 `audit-v351-venue-completeness`。
- 全345R中 source_complete/model_ready は237R。108Rが展示特徴量の欠損でstrict除外。
- 徳山35R、尼崎25R、住之江5Rはmodel_ready=0。特に徳山はorig_straight=0/35のため全件除外。

## 2026-09-15 次作業（venue-aware再構築）
- ユーザー承認により、345Rを場ごとの公開項目に合わせて再構築する。
- 結果を見て閾値を調整するのではなく、まず各場の利用可能な展示特徴量パターンを固定し、欠損項目を理由に場全体を落とさないvenue-aware feature/gateを作る。
- 徳山・尼崎・住之江を含む345Rで同一条件のバックテストを実行し、全体/場別の母数、1頭率、PASS/DROP、ticket ROIを旧v351と比較する。
- 実装・CI後にcommit SHA、Run/Job/Artifact ID、結論、次の再開地点をここへ追記する。

## 2026-09-15 作業前追記（original exhibition 生項目監査）
- 現行 `norm_metric` は「直線」「まわり/回り/ターン」「一周/ラップ」を正規化しているが、v326/v351特徴量は主に turn/straight/avg で、lap を独立特徴量として保持していない。
- そのため暫定venue-awareモデルを正式採用せず、まず `data/previews/original_exhibition` の生CSVにある `計測項目1..4` を全345R・24場で抽出し、実際の公開項目名・組合せ・欠損率を固定する。
- 次に一周/回り足/直線/半周ラップ等を別特徴量として再定義し、結果を使った閾値調整なしで345Rを再構築する。
- この作業では結果列は項目定義・schema選択に使用しない。
