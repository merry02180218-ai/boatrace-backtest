# 1号艇 v351 2026-09-15 retrospective audit addendum

## 2026-09-15 作業前記録
- ユーザーが2026-09-15結果の開封を明示許可。retrospective auditではUNREADを解除する。過去LIVE artifactの時刻・pristine性は別管理する。
- Phase Aは結果・払戻を一切使わず、当時のPRE + 展示データ + frozen v351 / HEAD cutoff 0.78で判定とproduction買い目を先に凍結する。
- Run 34944414581 / Job 104300312733 は徳山3Rの復元に成功後、蒲郡10RのBOATCAST展示STが403で停止した。
- 2026-09-15 蒲郡10Rの締切は19:32 JSTで、当該Run時点では未来レース。403を「取得方式故障」と断定せず、未公開展示を含む可能性として扱う。
- これからaudit workflowをfail-fastからvenue/race単位のskip方式へ変更し、現時点で展示READYの候補だけを復元してartifact化する。未READY/取得失敗はerrors/skippedとして保存し、他レースの監査を止めない。
- Phase A artifactが生成されるまで結果・払戻とのmergeは行わない。
