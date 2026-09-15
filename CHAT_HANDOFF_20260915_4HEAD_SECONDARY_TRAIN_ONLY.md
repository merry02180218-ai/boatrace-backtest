# CHAT HANDOFF — 2026-09-15 — 4HEAD SECONDARY TRAIN-ONLY

## SOURCE OF TRUTH
- Previous handoff: `CHAT_HANDOFF_20260915_4HEAD_WRST_AUG31_VARIANT.md`
- Latest completed result: player4_all_win Pareto Run `34926782402` / Job `104246398587` / Artifact `10379723183`.
- Fixed motor base remains `motor_win_diff_4v3 >= 0.010782 AND motor_2ren_diff_4v3 >= 0.4000pt`.
- Quantity-preserving player-strength band: `player4_all_win >= 0.210863` to `>= 0.215605`.
- September 2026 outcomes remain `UNREAD`.
- production `HEAD4_V291_COMP7` remains frozen.

## BEFORE — secondary causal gate research
ユーザー指定: 「続けてください」。

これからやること:
1. `player4_all_win >= 0.210863` と `>= 0.215605` を固定ベース候補として扱い、Apr-Junだけでsecondary gateを探索する。
2. secondary候補は causal prior-only の `motor_3ren_diff_4v3`, `player4_recent_p2`, `player4_frame4_win` に限定する。STはlineage完全監査まで使用しない。
3. 各secondary閾値はApr-Junの分布だけから生成し、Jul-Augを条件選択・閾値選択に一切使わない。
4. 第一目的はApr-Jun頭率を35%近辺以上へ上げること。R数を極端に落とさないよう、train R・月別頭率・最低月頭率を併記してPareto評価する。
5. train-onlyで代表条件を固定してからJul-Augを一括評価する。holdoutを見た後の選び直しは禁止する。
6. September outcome accessを明示的にguardし、productionは変更しない。
7. CI完了後、commit SHA / Run / Job / Artifact / train・holdout・Apr-Aug結果 / 結論 / 次の再開地点をこの引き継ぎへ追記する。

Status: `HEAD4_SECONDARY_CAUSAL_TRAIN_ONLY_STARTED`
