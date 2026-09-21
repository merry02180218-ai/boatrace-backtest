# 4HEAD Waku10 / PLAYER_HISTORY / seasonal research handoff — 2026-09-21

Repo: merry02180218-ai/boatrace-backtest
Latest GitHub/main overrides old chat/memory. September 2026 outcomes/payouts MUST remain UNREAD. Production unchanged unless user explicitly adopts.

## Mandatory workflow rule
Before EVERY dispatch/rerun: refetch actual committed workflow + all used/edited scripts from main; inspect complete files; compare YAML to a known-successful workflow; ensure literal escaped newline is absent; check YAML indentation/quoting/with/env/path/dependencies/timeout/artifact; py_compile Python; verify input paths/leakage guards/September UNREAD/no result-derived Waku. On failure inspect full logs+source+inputs, fix root cause, refetch, full preflight, only then rerun. Never blind rerun or claim success without verification.

## Frozen reference
Frozen candidate remains p>=.36 + ready + orig4_adv_inside>=-.06. Reproduced: Mar-May 49/124=39.516%, Jun 24/50=48.0%, Jul-Aug 63/127=49.6063%. Jul-Aug has been observed repeatedly and is NON-PRISTINE retrospective evidence.

## Shared PLAYER_HISTORY decision
User instructed PLAYER_HISTORY to be organized as common features now and introduced model-by-model later in SHADOW/RESEARCH, not production. 30 features = 6 boats x {pl_all_win, pl_all_p2, pl_frame_win, pl_frame_p2, pl_recent_p2}. Common registry: CHAT_HANDOFF_SHARED_FEATURES_CURRENT.md, commit 15960d3d980f8e6289ae235c5462957c2cb9bb6c.

## Waku v3-v6
v3 Run 35581005957 / Job 106273624255 / Artifact 10630775410 SUCCESS. BASE HOLD 140/70=50.00%; OWN4_WR_ST 118/60=50.85%; OWN4_WR_SR 109/57=52.29%; OWN4_WR_PASTWIN 131/66=50.38%.
Frozen WR+SR stability Run 35582200276 / Job 106277403860 / Artifact 10630029434 SUCCESS. WR+SR cut .37 monthly: Mar40.68 Apr36.59 May30.19 Jun52.94 Jul54.39 Aug50.00. WR_SR_ONLY 27/10=37.04%; BASE_ONLY 108/46=42.59%.
v4 REL43 Run 35583173038 / Job 106280409429 / Artifact 10631126842 SUCCESS. BASE HOLD50.00%; REL43_WR_ST53.33%; combo OWN4_WR_SR+REL43_WR_SR 59/110=53.64%, June54.0%.
v5 Run 35585646348 / Job 106288237386 / Artifact 10632565666 SUCCESS. Fixed cuts BASE.35 / REL43_WR_ST.36 / combo.37. Combo monthly Mar40.00 Apr36.11 May29.09 Jun54.00 Jul52.83 Aug54.39. Candidate-only sets did not beat BASE-only aggregate.
v6 Run 35586237864 / Job 106290131335 / Artifact 10632183071 SUCCESS. Raw REL43 distributions did not show a clear June jump; BASE score calibration/actual head-rate relation did change around June. Triggered leakage forensics.

## Leakage / causality audits
v7 Run 35589976860 / Job 106301927190 / Artifact 10634007859 SUCCESS: clean/v93 builders causal; target-day features frozen before result updates; HEAD4_LEAK_FORENSIC_V7_OK.
v8 Run 35591622050 / Job 106307071457 / Artifact 10634439444 SUCCESS: result/payout reads blocked, 28011 rows identical, mismatch_columns=[], exhibition leakage strongly ruled out.
v9 Run 35593228759 / Job 106312094381 / Artifact 10635251844 SUCCESS: PLAYER_HISTORY dominant; top standardized coefficient b4_pl_all_p2 +0.484267. DROP_DIRECT retained later jump; DROP_PLAYER_HISTORY collapsed high-p selection.
v10 Run 35597225826 / Job 106324736532 / Artifact 10637383105 SUCCESS: 23,855 races / 715,650 PLAYER_HISTORY cells / 0 mismatches; strict prior-date; same-day results not used. PLAYER_HISTORY_INDEPENDENT_AUDIT_V10_OK.
v11 Run 35597873022 / Job 106326785722 / Artifact 10637950770 SUCCESS: b4_pl_all_p2 has real monotonic-ish predictive relation across months; supports shared family.
v12 Run 35599346690 / Job 106331483273 / Artifact 10637319884 SUCCESS: broad-population b4 prior top2 + positive 4-vs-3 Waku WR directional signal stable early/late.
v13 Run 35600320936 / Job 106334619569 / Artifact 10638576990 SUCCESS: inside frozen set, hard gate b4_pl_all_p2>=.50 + REL43 WR>.10 worsened to Mar-May37.5%, Jun33.3%, Jul-Aug36.36%. Do not hard-gate.
v14 Run 35601591501 / Job 106338720561 / Artifact 10638849164 SUCCESS: frozen win/loss diagnostic. Jul-Aug strongest Waku differences were SR-relative: b4_sr -0.410, rel4_b3_sr +0.364, rel4_b1_sr +0.342, inside_min_sr +0.331; rel4_b3_st +0.289. June also strong relative SR. p direction flips early vs late.

## v15 fixed Waku SR/ST validation
Workflow creation had repeated YAML failures: Runs 35603671925, 35603998387, 35604363840 failed before useful execution. Root cause included malformed YAML/literal escaped newline during fixes. Final fix commit c6315c3abeaf34b341a1daebbebeed260c89a3de. This is why literal escaped newline + known-good-YAML comparison is mandatory.
Successful Run 35605250496 / Job 106350639571 / Artifact 10641499301 / digest sha256:16a55461ffb237a25caa5d59b760a97654ea1a90c6e3eca132b74eabb53e702d.
Conditions/cuts selected from Mar-May only; Jun-Aug not used for selection.
BASE: DEV39.52 / Jun48.00 / Jul-Aug49.61.
b4_sr: 44.93 / 51.52 / 53.73.
rel4_b1_sr: 37.68 / 56.25 / 57.69.
rel4_b3_sr: 45.16 / 48.15 / 59.32.
rel4_b1_st: 44.59 / 34.48 / 47.83.
rel4_b3_st: 43.24 / 41.67 / 62.30.
CONSENSUS_4OF6: 40.68 / 48.15 / 63.79.
CONSENSUS_5OF6: 47.22 / 42.86 / 65.12.
Interpretation: striking later-period strengthening, especially 4-vs-3 SR/ST, but not production-ready.

## BoatraceCSV environment data verification
User correctly noted water temperature exists. Verified data/results/realtime/YYYY/MM/DD.csv columns: 天候, 風向, 風速(m), 波の高さ(cm), 気温(℃), 水温(℃). Example 2026-07-17 water 31.3C; 2026-03-01 water 13.0C. Since these live in result rows, ONLY environmental columns may be whitelisted; never let finish/kimarite/actual ST/payout leak into predictors.

## v16 environment x Waku
Script commit edb14d7cfe64af50ab943cc896cc186db4f5554d; workflow commit 9a678225c3b9f07728c041af317c1be8ff3380ca.
Run 35606656425 / Job 106355269863 / Artifact 10642031507 / digest sha256:e272913dadd72da2138339f984c05721774ed8aa47ff696dbd151ac3dcf98c2e SUCCESS.
Meta: environment whitelist only; result_fields_used_as_features=false; descriptive_only=true; threshold_tuning=false; September UNREAD; production unchanged.
Monthly frozen: Mar40.63% water12.94; Apr51.52% water15.93; May32.20% water20.38; Jun48.0% water23.20; Jul49.23% water26.71; Aug50.0% water28.97.
Water bins: <20C 43/97=44.33%; 20-25C 32/79=40.51%; 25-30C 40/88=45.45%; 30+C 21/37=56.76%.
At water 30+C: rel4_b3_sr LOW 8/18=44.44%, HIGH 13/19=68.42%; rel4_b3_st LOW 5/15=33.33%, HIGH 16/22=72.73%.
At air 30+C: rel4_b3_sr LOW33.33%, HIGH62.16%; rel4_b3_st LOW35.29%, HIGH58.97%. Sample high-water only 37R: interesting, not adoption-grade.

## CURRENT ACTIVE: v17 seasonal falsification
Purpose: distinguish Jul-Aug calendar effect from actual high-water effect. Within Jul-Aug compare fixed water bands <25 / 25-30 / 30+, and within each compare 4-vs-3 SR/ST by fixed zero-sign split (not tuned median). Venue descriptive cells >=5. Also check 2025 Jul-Aug environment coverage only; do NOT analyze 2025 outcomes yet.
Script audit_4head_season_falsify_v17.py commit 30fc28a640f673e5b6e15003f4a3c2a9280c5b73; workflow commit e10752e46b114b3390606ad799e217be346a65e6.
Pre-fire blobs: script ddd586621df9ee3f4aba06b59f1f508c0be40ba2; workflow 1252a600b9fdb69d7d029c86203d2375942154f1. literal escaped newline false; workflow_dispatch true; py_compile true; threshold_tuning false; September guard true.
User fired v17 then said エラー, but last verified state was NOT failed: Run 35611769092 / Job 106372395453 / head SHA e10752e46b114b3390606ad799e217be346a65e6 was IN_PROGRESS. checkout/setup succeeded and it was at pip install. No conclusion yet.

## NEXT CHAT START EXACTLY HERE
1. Fetch Run 35611769092 current status first.
2. If running, inspect current job step; do not claim error/completion.
3. If failure, inspect FULL logs + actual committed script/workflow + inputs before any fix/rerun.
4. If success, report exact Run/Job/Artifact IDs and parse within-Jul-Aug water-band x SR/ST results plus 2025 environment coverage.
5. Scientific question: within SAME Jul-Aug, does high water preserve/amplify 4-vs-3 SR/ST advantage? If yes, environment hypothesis strengthens; otherwise calendar/composition/regime effect is more likely.
6. If 2025 Jul-Aug coverage is sufficient, next safe step is independent 2025 comparison only if the same causal Waku/frozen inputs exist. Never fabricate historical inputs.
7. Jul-Aug 2026 remains NON-PRISTINE retrospective. September 2026 remains UNREAD. Production unchanged.


## 2026-09-21 v17 failure recovery start
Run 35611769092 / Job 106372395453 completed FAILURE at the final 2025 coverage summary, after the 2026 within-season tables had already printed. Root cause: prior-year coverage list was empty, so pd.DataFrame(cov) had no month column and groupby("month") raised KeyError. This is a reporting/coverage-empty handling bug, not a model calculation failure. Before rerun: patch v17 to handle empty 2025 coverage explicitly, then refetch script/workflow, inspect full files, py_compile, literal escaped-newline/YAML/dependency/path/leakage/September guards, and only then rerun. Production unchanged; September 2026 remains UNREAD.

## v17 repair ready to fire
Patched empty prior-year coverage handling in commit 56cff90e1abca32a4ff87699dc90ca9caf21da38. Current script blob 3c63ab09883371fe5b42bb2f68accf090c7b1365; workflow blob unchanged 1252a600b9fdb69d7d029c86203d2375942154f1. Refetched both from main: threshold_tuning=false, SEPTEMBER_OUTCOMES_READ=false, PRODUCTION_CHANGED=false, workflow_dispatch present, timeout 60, py_compile preflight present, literal escaped newline absent, empty coverage now emits 2025_JUL_AUG_ENV_COVERAGE_EMPTY instead of crashing. Need fresh workflow_dispatch on current main; do NOT rerun old Run 35611769092 because that is pinned to old head e10752e. After fresh run, parse 2026 Jul-Aug water-band x SR/ST and confirm 2025 coverage status. Production unchanged; September UNREAD.


## v17 SUCCESS / next falsification start
Fresh Run 35615915964 / Job 106386465229 / Artifact 10645954075 completed SUCCESS on head cb47cb97a92db38548a45102ba854de620b2d851. HEAD4_SEASON_FALSIFY_V17_OK. Jul-Aug BASE 127/63=49.6063%. Water <25 20/9=45.0%; 25-30 70/33=47.1429%; 30+ 37/21=56.7568%. At 30+: fixed zero-sign rel4_b3_sr GT0 25/17=68.0% vs LE0 12/4=33.3333%; rel4_b3_st same 25/17=68.0% vs 12/4=33.3333%. 2025_JUL_AUG_ENV_COVERAGE_EMPTY confirmed. September outcomes UNREAD; threshold_tuning=false; production unchanged.

Next research starts by locating the actual historical BoatraceCSV environment-data layout for 2025 rather than assuming data absence. If historical environment truly cannot be recovered, perform a fixed-rule 2026 falsification comparing high-water vs lower-water periods/venues without tuning thresholds. Do not adopt the 30C gate from 37R alone. Before any new workflow dispatch, follow mandatory full preflight.
