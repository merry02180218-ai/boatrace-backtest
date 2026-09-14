# 1号艇 v344 pre-race feature diagnostic handoff

## 作業前/現在地
- v343で、単純な3連単上位3点の合成オッズ閾値だけでは、Feb-Jun pristineでBET 80R以上とROI 110%以上を同時達成できないことを確認。
- 正式productionは変更しない。`1HEAD_PRODUCTION_20260914_HEAD078` を維持。
- HEAD cutoff=.78 / exhibition v332 ATTACK_ENV_SOFT env_w=.10 q=.65 / SECOND v317 OUTER_L2_1 / THIRD v318 DROPSTART_T0.1 / ticket v320 HYBRID alpha=.70。
- production identity: 276R / head 241 / exact3(top3) 119 / race_code SHA256 `89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73`。
- Jul/AugはNON-PRISTINEで補助確認のみ。September outcomesはUNREADのまま。

## v344目的
過去データの診断として、広めの合成オッズ帯における事前特徴量とhit/returnの関係を調べる。主対象はFeb-Jun pristine。Jul/Augは補助のみ。productionは変更しない。

主な特徴量: p_head, opp_mass, attack_core, env_pair, 1号艇展示/ST/直線/オリジナル展示、SECOND/THIRDの展示関連margin。
LOMOで方向安定性も確認し、特定月・特定binへの過学習を避ける。

## CI完了
- workflow: `.github/workflows/v344-1head-prerace-feature-diagnostic.yml`（top-level `name:` なし）
- script: `run_v344_1head_prerace_feature_diagnostic.py`
- Run: `34808981813` SUCCESS
- Job: `103866342121` SUCCESS
- Artifact: `10334491773` / `v344-1head-prerace-feature-diagnostic`
- Artifact digest: `sha256:7ef7f969191481179b59826b4a89b8d0e48e0fb48a29f28957da5a81101ec132`
- workflow head SHA: `9369bd98f4ff493c48be9ab31cd72575fd989306`
- 全step成功。診断artifactの詳細解析へ進む。

## 厳守
- `SEPTEMBER_OUTCOMES_READ=false`
- 9月結果を読まない。
- Jul/Augをmodel selectionの根拠にしない。
- v344はretrospective diagnosticであり、現時点でproduction変更なし。
