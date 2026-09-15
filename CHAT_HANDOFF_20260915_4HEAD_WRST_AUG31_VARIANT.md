# CHAT HANDOFF — 2026-09-15 — 4HEAD WR_ST AUG31 HISTORY VARIANT

## CURRENT RULES
- 2026年7月・8月結果は学習・検証に使用可。
- 2026年9月結果は `UNREAD` 維持。
- production `HEAD4_V291_COMP7` は変更しない。

## PREVIOUS RESULT — 4号艇−3号艇 モーター差
- Run `34901233777` / Job `104167416359` / Artifact `10371331473` / success
- fixed rule: `motor_win_diff_4v3 >= 0.010782 AND motor_2ren_diff_4v3 >= 0.4000pt`
- Apr-Jun v250 PRE>=0.18 universe: 65R / 4頭30.77% / 3連単16.92% / ROI140.56%
- Jul-Aug holdout: 23R / 4頭47.83% / 3連単13.04% / ROI131.46%
- implementation SHA `08e13b0cdc64e4006ba22a4c2dabfffd49f291cd`

## PREVIOUS RESULT — 全レース母集団 固定モーター条件
- Run `34906818624` / Job `104185318430` / Artifact `10371974671` / success
- Apr-Jun: 107R / 4頭27.10% / 3連単14.02% / ROI124.79%
- Jul-Aug: 89R / 4頭32.58% / 3連単7.87% / ROI72.70%

## RESULT — player4_all_win Pareto
- cut .210863: Apr-Jun 77R/29.87%; Jul-Aug 61R/42.62%
- cut .215605: Apr-Jun 75R/30.67%; Jul-Aug 61R/42.62%
- cut .230699: Apr-Jun 64R/32.81%; Jul-Aug 50R/50.00%

## RESULT — 項目別展示 頭率改善
- Run `34962290514` / Job `104358460571` / Artifact `10394097349` / success
- `straight4_adv_inside >= 0.0`: Apr-Jun 37R/37.84%; Jul-Aug 21R/52.38%。
- availability自体は加点しない。

## AFTER — モーター条件緩和 × 展示判定 Pareto
- Run `34966369280` / Job `104371677153` / Artifact `10394589438` / success
- exact: motor win `-0.0299361318939513`, motor 2ren `-7.080000000000001`, player `.215605`, ST `-0.6000000000000001`。
- Apr-Jun 111R / 36.94%; Jul-Aug 96R / 39.58%。

## AFTER — exact 111R replay × original exhibition combo
- Workflow `head4-111r-orig-combo`: Run `34970281220` / Job `104384603205` / Artifact `10397252191` / success。
- exact replay `EXACT_111R_REPLAY_OK`。
- fixed base Apr-Jun 111R/41頭/36.9369%; Jul-Aug 96R/38頭/39.5833%。
- selected `orig4_adv_inside >= -0.057777777777777706`:
  - Apr-Jun 86R / 40.6977%（same-availability 108R/37.0370%, +3.6606pt）。
  - Jul-Aug 78R / 44.8718%（same-availability 93R/40.8602%, +4.0116pt）。
- 100R前後40%は未達。86R候補を正式研究候補とする。
- Sep `UNREAD`、production unchanged。
Status: `HEAD4_111R_ORIG_COMBO_COMPLETE`

## AFTER — 86R独立再現監査 完了
- fresh audit head SHA: `c732387d1bbf01afb4ffdb266d08eb1f74a2399b`
- Workflow: `audit-4head-86r-independent`
- Run `34984842829` / Job `104434176443` / Artifact `10402973600`: success
- Apr-Jun: 86R / 35頭 / 40.6977%
- Apr 25R/11頭/44.00%, May 35R/15頭/42.86%, Jun 26R/9頭/34.62%
- Jul 47R/24頭/51.06%, Aug 31R/11頭/35.48%, Jul-Aug 78R/35頭/44.8718%
- frozen v283: `TOP2XTOP2`, alpha2=.60, Top4 exactly 4 tickets; v96禁止。
- formal prospective ROIは `NOT_COMPUTABLE`。Sep `UNREAD`、production unchanged。
Status: `HEAD4_86R_INDEPENDENT_AUDIT_COMPLETE`

## BEFORE — v283 締切時オッズ retrospective diagnostic
ユーザー明示許可: 「締切時オッズでいいよ、検証なんだから」。formal prospective ROIとは分離する。
- 固定164R（Apr-Jun 86R + Jul-Aug 78R）を変更しない。
- frozen v283を使用し、v96代用禁止。
- official closing oddsを結合し月別・期間別ROIを算出。
- Sep outcomes `UNREAD`、production unchanged。
Status: `HEAD4_V283_CLOSING_ODDS_DIAGNOSTIC_STARTED`

## INTERIM — v283 closing odds diagnostic
- implementation `7c18054ec4a23981867c8afd83c0f4964bbf02ee`
- workflow fix `7ac801ce35899d5566239d2cc1bf55034875be33`
- Workflow `audit-4head-v283-closing-odds`
- Run `34991765053` / Job `104457918590` / Artifact `10406490587`: success
- Apr-Aug 164R中115R coverage=70.12%, hits=17, stake=46,000円, payout=63,070円, profit=+17,070円, ROI=137.11%。
- Augは31R中0R coverageで未評価。
- retrospective diagnosticのみ。formal prospective ROI=`NOT_COMPUTABLE`。Sep `UNREAD`、production unchanged。

## BEFORE — 締切時オッズ coverage 100% 回収監査
ユーザー指示: 「締切時オッズは全部何処かにあるはず」「続けて」。

これからやること:
1. 現在115/164Rしか結合できていない原因を、候補race keyと `data/official_closing_odds3t` の保存範囲・日付・場コード・R番号の対応から特定する。
2. 特にAug 31Rが0 coverageの原因を最優先で調べる。現時点のmain `data/official_closing_odds3t/2026` directory listingでは01〜07までは確認でき、`2026/08` contents APIは404だったため、別path・別artifact・取得workflow・生成元を探索する。
3. repo内のclosing odds取得/生成コード、過去Actions artifacts、別保存形式を調査し、Apr-Aug 164Rの締切時3連単オッズを可能な限り回収する。
4. 取得可能なら不足日をofficial sourceから再取得するworkflowを実装し、保存/診断へ接続する。September outcomeは絶対に読まない。
5. coverage 100%を目標にv283 retrospective diagnosticを再実行し、Apr/Augを含む月別・Apr-Jun・Jul-Aug・Apr-Augのhits/stake/payout/profit/ROIを更新する。
6. fresh Actions Run/Job/Artifactを確認後、AFTERへ原因、回収方法、coverage、全指標、commit SHA、Run/Job/Artifact、結論、次の再開地点を追記する。
7. formal prospective ROIは引き続き `NOT_COMPUTABLE`。production `HEAD4_V291_COMP7` は変更しない。v96禁止。

Status: `HEAD4_V283_CLOSING_ODDS_COVERAGE_RECOVERY_STARTED`
