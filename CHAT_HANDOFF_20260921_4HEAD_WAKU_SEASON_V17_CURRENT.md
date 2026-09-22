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


## v18 ready to fire
Started fixed-rule falsification after v17. v18 tests whether the observed water>=30C x 4-vs-3 SR/ST advantage is merely venue/month concentration. Fixed water cut=30C and signal cut=zero sign; no threshold search. Outputs: month/venue cells, leave-one-venue-out stability, and LT30 vs GE30 contrasts within ALL/SR_GT0/ST_GT0/BOTH_GT0. Script commit 6d13af54b4310336634e5dbb37d81c29bb3fbaf2; workflow commit ba108124b3357c2f0dd580956e5e873019f2d723. Refetched main and preflight guards verified: workflow_dispatch, timeout 60, py_compile, no literal escaped-newline, threshold_tuning=false, fixed 30C, September UNREAD, production unchanged. Need fresh workflow_dispatch of audit-4head-water30-falsify-v18 on main.


## v18 SUCCESS
Run 35621333244 / Job 106404840064 / Artifact 10648933304 completed SUCCESS on head 7a4cdf263e5a2b3dcfa58c7e9444965347d764d2. Artifact digest sha256:afad45ae7b49cac64fdeb059d46026059be0d34536b93a99d6b00148aac037ba. Fixed contrasts: ALL LT30 264/115=43.56%, GE30 37/21=56.76%; SR_GT0 LT30 176/80=45.45%, GE30 25/17=68.0%; ST_GT0 LT30 194/88=45.36%, GE30 25/17=68.0%; BOTH_GT0 LT30 154/71=46.10%, GE30 25/17=68.0%. Month: Jul high-water SR/ST positive 8/4=50%; Aug 17/13=76.47%, so effect is materially stronger in August and not cleanly replicated at same magnitude in July. Leave-one-venue-out SR/ST positive remains 64.71%-71.43% across every venue removal; removing venue23 gives 17/11=64.71%, so aggregate 68% is not solely venue23-driven. However high-water sample remains only 37R/25 signal-positive; production unchanged. September UNREAD; threshold_tuning=false.

Next: quantify uncertainty/significance and distinguish August regime from temperature using fixed comparisons only (no threshold search), preferably Wilson/Fisher and month x water interaction. Do not adopt yet.


## v19 ready to fire
Built fixed statistical falsification to quantify v18 uncertainty and separate July/August from water>=30C without changing cuts. Uses two-sided Fisher exact tests and 95% Wilson intervals; fixed water=30C, SR/ST zero-sign, fixed months July/August, no model refit, no threshold tuning. Script commit 9b93feacd19c438738029dd35ca4a5d38df0dc70; workflow commit e8f865b7ac0560f8939a20e1975b634d73b97f32. Full refetch/preflight passed: workflow_dispatch, timeout60, scipy dependency, py_compile, no literal escaped-newline, fixed30, threshold_tuning=false, model_refit=false, September UNREAD, production unchanged. Need fresh workflow_dispatch audit-4head-water30-stats-v19.


## v19 SUCCESS
Run 35622878439 / Job 106409995001 / Artifact 10649909849 SUCCESS; artifact digest sha256:391adac7dd99b855c53934e1c9ee80582f0c398647d7865edf8b25c1bda630a3. Fixed GE30 vs LT30: ALL 56.76% vs 43.56%, Fisher p=.1586; SR 68.0% vs45.45%, p=.05266; ST 68.0% vs45.36%, p=.03576; BOTH 68.0% vs46.10%, p=.05254. GE30 17/25 Wilson95%=48.41%-82.79%. Critical month split: July GE30 signal 4/8=50% and does NOT beat LT30 (SR59.38%, ST54.05%, BOTH65.38%; p .70/1.0/.68). August GE30 signal 13/17=76.47% versus LT30 SR7/22=31.82% p=.00953; ST9/23=39.13% p=.02668; BOTH7/20=35.0% p=.02020. Therefore the aggregate water>=30 effect is substantially August-driven; current evidence does not support a generic temperature-only rule. Production unchanged; September UNREAD. Next should investigate August regime causes with predeclared covariates / PLAYER_HISTORY, venue mix, racer composition, environment, while avoiding post-hoc threshold tuning.


## v20 ready to fire
August-regime decomposition prepared after v19 showed July non-replication and strong August-only GE30 effect. Fixed comparisons only: July/Aug x LT30/GE30 within rel4_b3 SR>0 & ST>0; composition medians for PLAYER_HISTORY, Waku, base p/orig advantage, environment; venue concentration; b4_pl_all_p2 bins fixed from Mar-May quartiles; August venue-vs-water membership diagnostics. No new gate selection, no threshold tuning/refit. Script commit cbb7e4c85a467a47792d51804627e1fb05cb04d7; workflow commit 7fc5ae4902c8895889e37243d8951539fcfa545a. Refetched main/preflight passed; September UNREAD; production unchanged. Need fresh workflow_dispatch audit-4head-aug-regime-v20.


## v20 SUCCESS
Run 35624485765 / Job 106415349134 / Artifact 10651527019 SUCCESS; digest sha256:f928d44a1b395c5756aedc2e78fb6e7f2eaf39ab4d6b9949d39c61bb3825c144. Fixed BOTH(SR>0 & ST>0) cells: Jul LT30 17/26=65.38%, Jul GE30 4/8=50%; Aug LT30 7/20=35%, Aug GE30 13/17=76.47%. Aug GE30 vs Aug LT30 medians: b4_pl_all_p2 .5363 vs .5243 (small), w10_b4_sr 2.50 vs2.65, rel4_b1_sr .90 vs1.10, rel4_b3_sr 1.10 vs.85, rel4_b3_st .060 vs.045, p .4514 vs.4145, orig4_adv_inside .3556 vs.4000, wind 3 vs3, wave2 vs3. Venue concentration similar (9 venues/max share29.4% vs11 venues/max30%), so simple concentration not explanation. Venue-water membership differs for venue4 (0/6 GE30, p=.022) and venue23 (5/5 GE30, p=.014), but v18 LOVO already showed aggregate survives removing venue23. PLAYER_HISTORY fixed Mar-May bins: Aug GE30 middle bins strong (.461-.511:4/5=80%; .511-.57:7/8=87.5%), but samples small; Aug LT30 corresponding 1/4=25%, 0/5=0%. Main new contrast appears higher model p and stronger rel4_b3 SR/ST in Aug GE30, not b4_pl_all_p2 alone. No new gate selected. September UNREAD; production unchanged. Next: fixed matched/stratified test controlling p and PLAYER_HISTORY to test whether water/Aug effect remains after baseline candidate strength.


## v21 ready to fire
Prepared fixed August stratified/matched falsification to test whether Aug GE30 76.47% is just stronger baseline candidates. Controls only p and b4_pl_all_p2. Strata edges are tertiles learned from Mar-May only; overlap-strata standardized GE30/LT30 rates reported. Sensitivity matching pairs each Aug GE30 BOTH-positive candidate to nearest Aug LT30 candidate by Mar-May-standardized p+PLAYER_HISTORY, with replacement and outcome-blind matching. No threshold tuning/refit. Script commit 035306c0912385c730d10160e185905271dc93a8; workflow commit d5361a1f284e34eadc1b55bd7a4e0ec5d936c456. Refetch/preflight passed including no literal escaped newline, py_compile, fixed30, September UNREAD, production unchanged. Need fresh workflow_dispatch audit-4head-aug-stratified-v21.


## v21 SUCCESS
Run 35626120357 / Job 106420793890 / Artifact 10652302655 SUCCESS; digest sha256:7d06bdfa94e52f7ec7b3ed531d88442ac9faf8c20c1b641c60f5e079aeeaa151. Fixed August BOTH-positive p+PLAYER_HISTORY control: 5 overlap strata, GE30 13R vs LT30 14R. Standardized rates GE30 73.09% vs LT30 28.27%, diff +44.81pp. Outcome-blind nearest-neighbor sensitivity (Mar-May standardized p + b4_pl_all_p2, replacement): 17 pairs, GE30 76.47% vs matched LT30 35.29%, diff +41.18pp, median standardized distance .343. Thus v20 August GE30 effect is not explained by baseline p and b4_pl_all_p2 alone. Individual strata remain tiny and matching reuses controls, so this is falsification evidence, not production rule proof. Next: control for the stronger rel4_b3 SR/ST magnitude themselves and venue composition using fixed predeclared bins/LOVO; if effect persists, investigate an August-specific latent/environment regime. September UNREAD; production unchanged.


## v22 ready to fire
Prepared fixed full matching falsification after v21. August BOTH-positive GE30 vs LT30 matching now controls p, b4_pl_all_p2, rel4_b3_sr magnitude, rel4_b3_st magnitude, scaled only by Mar-May means/sds. Includes same-venue-only sensitivity and leave-one-venue-out matching. Matching is outcome-blind, with replacement; no cut search/refit. Script commit b3d3dc7acf8104e6a0a5d781ab3ac5f10125fb64; workflow commit 02f8909f49ddf49b1a606509c9b849e8662130f6. Full refetch/preflight passed; September UNREAD; production unchanged. Need fresh workflow_dispatch audit-4head-aug-match-full-v22.


## v22 SUCCESS
Run 35627380056 / Job 106424961588 / Artifact 10652124831 SUCCESS; digest sha256:5582b3c8e847a425ae834dee00f4ca783e05f23af5ae1bbd93d7709d7e5ebf71. FULL4 outcome-blind matching controlling p, b4_pl_all_p2, rel4_b3_sr magnitude, rel4_b3_st magnitude: 17 treated / 10 unique controls, GE30 76.47% vs matched LT30 35.29%, diff +41.18pp, median distance .859, max2.545. Same-venue sensitivity has only 3 pairs: GE30 33.33% vs LT30 0%, too sparse to interpret. Leave-one-venue-out FULL4 effect remains positive for every venue removed: smallest diff +25.0pp when venue23 removed (12 pairs, 66.67% vs41.67%); other diffs +33.3pp to +58.8pp. Thus effect is not explained by baseline p, PLAYER_HISTORY, SR/ST magnitude, or any single venue, but matching quality is only moderate and control reuse/small N remain. Do not productionize. Next should seek independent temporal replication / fixed placebo-style tests rather than add more post-hoc covariates. September UNREAD; production unchanged.


## High-water shadow signal frozen for future live integration
User decision: preserve the research as a SHADOW/attention signal, not a purchase gate, because 2026 high-water season is effectively ending. Canonical signal definition is frozen in head4_high_water_shadow.py: water_c >= 30.0 AND w10_rel4_b3_sr > 0 AND w10_rel4_b3_st > 0 => label HIGH_WATER_30C_WAKU43_SR_ST. research_only=true, production_applied=false, changes_bet_decision=false. Commit 302937040bcad255fb0dfce0cb1916920dc30bc7. Forward validation target: 2027 summer high-water season. Important integration note: current live fast path run_4head_120r_lastminute_fast.py does not currently have causal pre-race water temperature input; do NOT fake water_c from result rows or use post-race BoatraceCSV. Before surfacing the flag in live JSON/UI, add/verify a causal pre-deadline water-temperature source and Waku43 SR/ST live values. Until then helper remains dormant and production behavior is unchanged. September outcomes remain UNREAD for research.


## LIVE high-water shadow integrated
Correction after user noted water temperature should be available at BET time: confirmed existing result-blind BOATCAST bc_sui pre-race feed. BoatraceCSV sui schema independently confirms pre-race rows include wind, wave, air temperature, water temperature. Extended build_4head_env_context_live.parse_sui_weather to parse wave_cm/air_c/water_c from bc_sui; commit e606f5b5853d8a6f17a2449ac21a26f8e2e6aa24. Integrated bc_sui fetch into run_4head_120r_lastminute_fast.py concurrent current-data fetch and added prerace_weather + high_water_shadow output; commit d9f102f0909e02542f374b05894f96b730f9e06e. Signal remains water>=30 AND causal Waku10 rel4_b3_sr>0 AND rel4_b3_st>0. It does not alter selected/decision/tickets/staking. Refetch audit passed: pre-race source only, result endpoint unused, existing BET/PASS contract unchanged. Need a fresh live/benchmark run to verify actual Waku10 column-name mapping and bc_sui live column layout before calling integration operational. September outcome labels remain UNREAD.


## Water LIVE verification failure fixed
Push-triggered validate-4head-env-context-live Run 35667738176 / Job 106557131447 failed in verify_4head_env_context_live.py because the old bc_sui fixture had only 7 columns and expected the old 3-value parser. This was a stale test fixture caused by the water parser extension, not a live-source/model failure. Updated fixture to explicit pinned layout HHMM,status/weather,wind-dir,wind-speed,wave,air,water and updated parser/build assertions including water_c=30.5 and pre-race source kind. Fix commit 7d8ce60f9d2eabf8543fd10e22dfc13f8be1717a. Refetch checks passed. The push should trigger a fresh validate workflow; inspect it before declaring operational. September outcomes UNREAD; production decision unchanged.


## Water parser validation green
Fresh push validation completed SUCCESS: Run 35667902979 / Job 106557630567, head 7d8ce60f9d2eabf8543fd10e22dfc13f8be1717a. Logs: PASS verify_4head_env_context_live; PASS verify_4head_env_entry_auto_live; PASS verify_4head_full_auto_live. This closes the stale-fixture failure from Run 35667738176. Current static/contract validation confirms pre-race bc_sui water parsing is wired without result/payout use. Remaining operational check is one real current-race HEAD4 fast/BET-path execution that reaches bc_sui and Waku10 rel4_b3 SR/ST fields; do not call the signal operational until that passes. September outcome labels remain UNREAD; production selection unchanged.


## NEXT ACTIVE RESEARCH: PLAYER_HISTORY + Waku10 soft reranking
User approved moving from high-water SHADOW to 4HEAD improvement research using PLAYER_HISTORY + Waku10 as score/probability correction rather than hard gates. Motivation: v13 hard gate b4_pl_all_p2>=.50 + REL43_WR>.10 degraded performance, while v9-v15 show PLAYER_HISTORY predictive value and later-period 4-vs-3 SR/ST strength. Research only; production unchanged; September outcomes UNREAD.
Plan: preserve frozen candidate reference p>=.36 + ready + orig4_adv_inside>=-.06 and compare soft reranking/calibration families using causal pre-race PLAYER_HISTORY (especially b4_pl_all_p2 and relative boat4-vs-3 player strength) plus Waku10 rel4_b3 SR/ST/WR. DEV Mar-May for fitting, June for fixed family/strength selection, Jul-Aug holdout reporting only. Primary constraint: do not materially collapse race count; report monthly R/head-rate plus overlap/add/drop versus frozen reference. No Jul-Aug-driven threshold selection. Before workflow dispatch follow full mandatory preflight.


## v23 soft rerank + original feature reduction ready
User additionally requested testing reduction of original HEAD-probability features. Added research_4head_player_waku_soft_ablation_v23.py commit b47b8ccf0d72160fe26f833fa880a244e43bad87 and workflow commit a8f15cf114367cf5654600e2bdacbd658a496d90. Families cross baseline ablations (FULL, DROP_BOAT, DROP_LOCAL, DROP_TOP3, CORE=drop boat/local/top3) with causal PLAYER_HISTORY boat4, 4-vs-3 PLAYER_HISTORY differences, and Waku10 rel4_b3 WR/ST/SR. Logistic soft reranking only; no hard player/Waku gate. Fit Mar-May; June selects cut with >=45 selections volume floor; Jul-Aug holdout report only. Preflight refetch: workflow_dispatch/py_compile/September guard/holdout-selection guard/BASE_CORE/volume floor present; literal escaped-newline absent. Need fresh workflow_dispatch research-4head-player-waku-soft-ablation-v23. Production unchanged; September UNREAD.


## v23 first run failure / fixed
Run 35670052141 / Job 106564280385 FAILURE in research step after parent build succeeded. Root cause: v93 parent already contains PLAYER_HISTORY columns; merging independently rebuilt causal PH created pandas _x/_y suffixes, so expected b4_pl_all_win was absent (KeyError). Not a data/model/leakage failure. Fix commit 2f89900edfa61f855fa61cb734c8e13b54171ebb drops any parent _pl_ columns before merging the independently rebuilt causal PH table as canonical source. Refetched script/workflow: collision fix present, workflow_dispatch/September UNREAD/holdout selection guards intact, no literal escaped-newline. Need fresh dispatch; do not rerun old pinned failed run.


## v23 SUCCESS — soft rerank + baseline ablation
Run 35670737379 / Job 106566375952 / Artifact 10671170262 SUCCESS; digest sha256:28d677c59e5a8cf70c1e4e892257177299dd7b950fea6fc99458ba8f34299d28. September UNREAD, holdout not used for selection, production unchanged.
Key June-selected results (June / Jul-Aug): BASE_FULL 66R 34.85% /145R 35.17%. BASE_FULL_PH4 48R 52.08% /117R 52.14%. FULL_PH4_REL43 47R51.06% /118R50.85%. FULL_PH4_W43 49R51.02% /125R48.80%. FULL_PH4_REL43_W43 52R50.0% /128R47.66%. Removing LOCAL: DROP_LOCAL_PH4 50R50.0% /113R52.21%; DROP_LOCAL_PH4_W43 45R51.11% /102R52.94%; DROP_LOCAL_PH4_REL43_W43 62R51.61% /142R45.07%. CORE mirrors DROP_LOCAL in this parent (boat/top3 drops had no effect on numeric baseline): CORE_PH4 50R50.0% /113R52.21%; CORE_PH4_W43 45R51.11% /102R52.94%.
Interpretation: PLAYER_HISTORY itself provides the large improvement over original baseline. Waku43 does not improve FULL PH4 holdout, but after removing LOCAL features PH4+W43 reaches 52.94% on 102 Jul-Aug races versus 52.21%/113 for reduced PH4 and 52.14%/117 for FULL PH4; difference is small and retrospective. Adding relative PLAYER_HISTORY/Waku together increases June volume but weakens holdout. Feature reduction evidence: local block is removable without hurting PH4 holdout; boat/top3 blocks appear absent/ineffective in this numeric parent. Next research should freeze PH4 as anchor and perform finer baseline feature ablation / regularization with monthly stability and volume target ~50-60/month, rather than add more Waku features blindly.


## v24 PH4 fine ablation ready
Following v23 success, PH4 is frozen as the anchor and original HEAD features are ablated more finely: local, motor, boat, top3, top2, avg_st, national_win, plus cumulative NO_LOCAL_BOAT_TOP3 and compact CORE_WIN_ST_MOTOR. Also tests logistic C=.1/.25/.5/1.0. Fit Mar-May; June alone selects cut under 45-70 race volume band; Jul and Aug reported separately plus combined, never used for selection. Script commit f7e9b276cce61ae066296f3875206e9f4eb9a93c; workflow commit 23b18a223f8c934805fb3900a5894bfbb6c57e80. Refetch preflight passed: py_compile step, September UNREAD, holdout-selection guard, volume band, separate Jul/Aug reporting, no literal escaped-newline. Production unchanged. Next: dispatch research-4head-ph4-fine-ablation-v24 and inspect result before any adoption.


## v24 SUCCESS — PH4 fine ablation
Run 35671585748 / Job 106569029978 / Artifact 10671536585 SUCCESS; digest sha256:a51f8f14179a594a5df35ca568a41a03484450ec0d89234bc5355e0365c2e09f. September UNREAD; holdout not selected on; production unchanged.
June ranking leader DROP_MOTOR_C0.25: 24/45=53.33%. FULL_C0.5 anchor: June25/48=52.08%, July30/59=50.85%, Aug31/58=53.45%, Jul-Aug61/117=52.14%. Important compact result NO_LOCAL_BOAT_TOP3_C0.1: June25/49=51.02%, July27/53=50.94%, Aug32/54=59.26%, Jul-Aug59/107=55.14%, DEV58/154=37.66%. This removes 5 baseline features vs FULL (30 total features incl PH4 vs35) and uses stronger regularization C=.1. More aggressive CORE_WIN_ST_MOTOR collapses to ~30% holdout and is rejected. Individual DROP_TOP3/TOP2/AVG_ST/NATIONAL_WIN mostly duplicate FULL in this parent; their named columns are effectively absent or identical under feature detection. Next: independently falsify NO_LOCAL_BOAT_TOP3_C0.1 versus FULL_C0.5 and DROP_MOTOR_C0.25 using fixed thresholds, month/venue/class stability, bootstrap/binomial uncertainty, overlap/add-drop analysis, and no further Jul-Aug tuning. Do not promote yet.


## v25 fixed falsification ready
Frozen before audit: FULL_C05 cut.36, COMPACT_C01 cut.36 (drop local_/boat_/top3), DROP_MOTOR_C025 cut.36. No further tuning. Added month stability, venue stability, bootstrap 95% intervals, overlap/full-only/candidate-only decomposition, and explicit feature inventory to detect ineffective drop patterns. Script commit e89301fa028734b37c49f7dae17304375cffd1db; workflow ea38531079157036d528430f7a03337a6a46df25. Refetch preflight passed: compile, September UNREAD, fixed candidate definitions, bootstrap, overlap, venue audit, no literal escaped-newline. Production unchanged. Next dispatch audit-4head-ph4-compact-v25.


## v25 SUCCESS — fixed compact falsification
Run 35672469477 / Job 106571765112 / Artifact 10671258267 SUCCESS; digest sha256:b843b6af2a54c61961d7d514f1ce0557b154d21062ae165d2d00677bd92f167e. September UNREAD; no selection on evaluation; production unchanged.
Monthly: FULL_C05 Jun25/48=52.08%, Jul30/59=50.85%, Aug31/58=53.45%. COMPACT_C01 Jun25/49=51.02%, Jul27/53=50.94%, Aug32/54=59.26%. DROP_MOTOR_C025 Jun24/45=53.33%, Jul28/52=53.85%, Aug27/52=51.92%. Feature inventory clarified COMPACT actually removes only five opponent-local features (opp_local_b1/b2/b3/b5/b6); boat_/top3 patterns remove nothing in this parent. Thus the v24 compact gain is specifically local-opponent feature removal + stronger C=.1, not a broad five-feature-family reduction.
Paired FULL vs COMPACT Jun-Aug: overlap151R 80 heads=52.98%; FULL-only14R 6=42.86%; COMPACT-only5R 4=80.0%. August drives most differential: overlap52R30=57.69%, FULL-only6R1=16.67%, compact-only2R2=100%; small add/drop counts mean uncertainty remains high. DROP_MOTOR is steadier monthly but paired changes do not clearly dominate FULL (FULL-only27R 55.56%, candidate-only11R72.73%). Bootstrap intervals are wide. Conclusion: COMPACT_C01 remains promising but not independently proven enough for production. Next useful falsification: separate effects of (A) removing opponent-local only at same C=.5 and (B) changing regularization to C=.1 with full features, fixed cut .36, so we can attribute the gain rather than confound feature removal and regularization. Then use leave-one-venue-out / class if available. No Jul-Aug tuning.


## v26 attribution audit ready
Fixed 2x2 experiment to separate the v25 confound: FULL_C05, FULL_C01 (regularization-only), NOLOCAL_C05 (opponent-local removal-only), NOLOCAL_C01 (both), all at cut .36. Fit Mar-May only; Jun-Aug fixed evaluation only; no selection/tuning. Exact paired overlap/a-only/b-only contrasts are emitted for ALL and each month. Script efac807e1fd9220963cca4a6f1f104ef28cd15bd; workflow 7e6061663309f129f4166c56ddb73bf2c80710e9. Refetch preflight passed: compile, fixed cut, four cells, paired attribution, September UNREAD, no literal escaped-newline. Production unchanged. Next dispatch audit-4head-ph4-local-reg-v26.


## v26 SUCCESS — attribution local vs regularization
Run 35681227532 / Job 106598402882 / Artifact 10674628979 SUCCESS; digest sha256:c1ed938bb05639c144fa0a511d47ba3840f40d9a5a0a58f958b2af060c827e8f. September UNREAD; production unchanged.
Monthly fixed cut .36: FULL_C05 Jun25/48=52.08 Jul30/59=50.85 Aug31/58=53.45. FULL_C01 Jun23/46=50.00 Jul30/58=51.72 Aug31/54=57.41. NOLOCAL_C05 Jun25/50=50.00 Jul27/56=48.21 Aug32/57=56.14. NOLOCAL_C01 Jun25/49=51.02 Jul27/53=50.94 Aug32/54=59.26.
Attribution: regularization-only vs FULL changes very few races overall (FULL-only9R 4 heads; C01-only2R 2 heads), with most apparent gain August where FULL-only 5R has 1 head and C01-only1R has 1. Local-removal-only is not independently beneficial: FULL-only9R 6 heads vs NOLOCAL-only7R 4 heads. At C=.1, local removal swaps 11 FULL_C01-only at 6/11=54.55% for 9 NOLOCAL-only at 6/9=66.67%, a modest small-N improvement. Strongest clear mechanistic signal is regularization after local removal: NOLOCAL_C05-only 8R are 0/8 and NOLOCAL_C01-only 1R is 0/1; C=.1 mostly prunes eight misses, explaining combined gain. Thus combined NOLOCAL_C01 improvement is driven mainly by stronger regularization pruning misses, with local removal secondary/uncertain. Next: fixed robustness audit of FULL_C01 vs NOLOCAL_C01 across venue leave-one-out and player/class strata if source columns permit; also examine score-margin distribution of pruned 0/8 to ensure threshold-edge instability rather than accidental fit. Do not retune cut on Jul-Aug.


## v27 fixed robustness ready
Following v26 attribution, freeze FULL_C01 vs NOLOCAL_C01 at C=.1/cut=.36. Audit Jun-Aug only without retuning: leave-one-venue-out stability for all venue codes, fixed score bands around .36 to inspect threshold-edge fragility, and race-level score/selection flips between full and no-local. Script 2673f04b3582f53b480727560974290b81b4ceb9; workflow b93aaa34fb79cba24b70f0d082920225e2e60bb7. Refetch preflight passed: compile, September UNREAD, retuning false, LOO, score-band diagnostics, no literal escaped-newline. Class/grade strata were not added because the current frozen v93 parent does not expose an obvious verified class column; do not invent one. Production unchanged. Next dispatch audit-4head-ph4-robustness-v27.


## v27 SUCCESS — C=.1 robustness
Run 35681891478 / Job 106600401001 / Artifact 10675199513 SUCCESS; digest sha256:c0dc24eaae7d8975e0bafd68c95545536594a450b9dfbd72c07f8f57a96f9bdf. September UNREAD; no retuning; production unchanged.
Jun-Aug aggregate fixed cut .36: FULL_C01 158R/84=53.16%; NOLOCAL_C01 156R/84=53.85%. Venue LOO output currently shows only venue keys 06/07/08 because venue extraction used race_code[4:6], which is month, not venue. Therefore the LOO venue diagnostic is INVALID and must not be interpreted; root cause identified in audit script. Score bands are valid because they do not depend on venue extraction. FULL_C01: .35-.36 11/26=42.31%, .36-.37 14/26=53.85%, .37-.38 7/15=46.67%, .38-.40 14/34=41.18%, .40-.45 26/41=63.41%, >=.45 23/42=54.76%. NOLOCAL_C01: .35-.36 7/30=23.33%, .36-.37 13/21=61.90%, .37-.38 10/21=47.62%, .38-.40 14/32=43.75%, .40-.45 25/42=59.52%, >=.45 22/40=55.0%. Threshold .36 is directionally meaningful locally but score ordering is not monotonic across every narrow band, so do not tighten based on these retrospective bins.
FULL vs NOLOCAL selection flips =20R, 12 heads=60%; differences are mostly within ~0.03 probability of threshold, confirming local-feature removal mainly perturbs borderline races. Need v27b correction for true venue code extraction before any venue robustness conclusion. Handoff must treat current venue LOO as invalid, not evidence.


## v27b corrected venue audit ready
Corrected race_code schema to YYYYMMDDJJRR and venue slice [8:10]. Added hard preflight assertions: >=20 unique venues and every venue code 01-24, preventing recurrence of month-as-venue bug. Fixed FULL_C01 vs NOLOCAL_C01, C=.1/cut=.36, Mar-May fit, Jun-Aug evaluation, no retuning. Outputs true leave-one-venue-out plus per-venue selected counts/rates to detect concentration. Script bf701b9dc2a4a430a8e27e654dff4f55ac47a841; workflow ea02ff23b63bfbb813b761c3e3ecbc1332d2360d. Refetch preflight passed: venue slice/assertions, compile, September UNREAD, retuning false, no literal escaped-newline. Production unchanged. Next dispatch audit-4head-ph4-robustness-v27b.


## v27b SUCCESS — corrected true venue robustness
Run 35683257760 / Job 106604590618 / Artifact 10675412601 SUCCESS; digest sha256:6ad661c816d6ce0733d5b03b5806b7c432743109de3f294801fe3068ddb158b9. Correct venue schema YYYYMMDDJJRR, venue [8:10], 23 venues present in Jun-Aug evaluation (03 absent). September UNREAD; no retuning; production unchanged.
Aggregate: FULL_C01 158/84=53.16%; NOLOCAL_C01 156/84=53.85%. Correct LOO ranges: FULL lowest after leaving venue23 =73/143=51.05%, highest leaving venue22=83/150=55.33%; NOLOCAL lowest leaving venue08=52/102? NOTE that prior line belongs invalid v27; corrected v27b lowest among printed corrected rows is venue23:74/141=52.48%, highest venue10:81/145=55.86%. Thus neither model's aggregate success is dependent on a single venue; NOLOCAL stays >=52.48% under every observed venue omission. Per-venue samples are small and heterogeneous: examples FULL venue08 1/5=20%, venue10 3/11=27.27%, venue22 1/8=12.5%, venue23 11/15=73.33%; NOLOCAL venue08 1/5=20%, venue10 3/11=27.27%, venue22 1/5=20%, venue23 10/15=66.67%. Do not create venue gates from these retrospective tiny cells.
Conclusion: corrected venue audit supports broad robustness of C=.1 aggregate; NOLOCAL only modestly exceeds FULL (+0.69pp) and should not yet be claimed superior. The larger reliable research result remains PH4 + stronger regularization. Next best falsification: rolling-origin/monthly refit comparison of FULL_C05 vs FULL_C01 (and optionally NOLOCAL_C01 shadow) using only prior months, fixed cut .36, to test whether C=.1 advantage persists without a single Mar-May fit regime. No Jul-Aug tuning.


## v28 rolling-origin regularization audit ready
Fixed FULL PH4 feature set; compare C=.5 vs C=.1 at cut=.36 under rolling origin: June train Mar-May; July train Mar-Jun; August train Mar-Jul. No future month enters each fit, no retuning, September UNREAD. Emits monthly and paired overlap/C05-only/C01-only diagnostics. Script 5f7a79f08340cda4654e095873a5cc0691e0820b; workflow 14e06fd172f3a87b3fc312ebe4e26eb2aa045cf9. Refetch preflight passed: compile, fixed cut, rolling schedule, no future training declaration, September UNREAD, no literal escaped-newline. Production unchanged. Next dispatch audit-4head-ph4-rolling-c-v28.


## v28 SUCCESS — rolling-origin falsifies C=.1 advantage
Run 35684094228 / Job 106607130022 / Artifact 10676072788 SUCCESS; digest sha256:3e77c3ce7a681f730bb4a2b6d2c971a579f11400947ff320ab5c7e7b2425100b. September UNREAD; no retuning; production unchanged.
Rolling fixed cut .36: June C05 25/48=52.08%, C01 23/46=50.00%; July both 28/59=47.46%; August C05 32/62=51.61%, C01 31/60=51.67%. Paired aggregate overlap 165/82=49.70%; C05-only 4/3=75%; C01-only 0R. Therefore C=.1 does NOT show a robust rolling-origin advantage; it merely prunes four C05 selections, three of which were winners. Earlier fixed-fit August improvement from C=.1 was regime/fit dependent and should not be promoted as a general improvement.
Research conclusion update: strongest robust result remains PLAYER_HISTORY PH4 itself. Do not claim stronger regularization as established improvement. FULL_C05 remains at least as defensible as C01 under rolling refits; production remains unchanged. Next research should isolate PH4 components (all_p2 was dominant in v9) under fixed rolling-origin ablation, comparing full PH4 vs compact PH subsets without tuning cut on Jun-Aug, to see whether PLAYER_HISTORY can be simplified/strengthened robustly.


## v29 rolling PLAYER_HISTORY component ablation ready
After v28 falsified a general C=.1 advantage, return to C=.5/cut=.36 fixed and isolate PH4 components under the same rolling origin. Specs frozen before evaluation: BASE, all_p2 only, all_p2+recent_p2, all_p2+frame_p2, P2 trio, win pair, FULL5. June train Mar-May; July Mar-Jun; August Mar-Jul. No future month, no retuning, September UNREAD. Outputs monthly/aggregate plus paired selection changes versus BASE and FULL5. Script cd7d27f92e110f94c85f637d15acc1c3772e9867; workflow 76e9167a8310405034fe417a621204acc390fbe9. Refetch preflight passed: compile, C/cut fixed, PH specs present, September UNREAD, no literal escaped-newline. Production unchanged. Next dispatch audit-4head-ph4-component-rolling-v29.


## v29 SUCCESS — rolling PH component ablation
Run 35685339099 / Job 106610841909 / Artifact 10676218048 SUCCESS; digest sha256:0ad235e7d8374c3cabecf172ce380bb4d6bce89a961d7823e510f6b0522ebdaf. Fixed C=.5/cut=.36, rolling origin, no retuning, September UNREAD, production unchanged.
Aggregate Jun-Aug: BASE 3/9=33.33% (almost no selections at same cut); PH_ALL_P2 77/156=49.36%; ALL_P2+RECENT 76/156=48.72%; ALL_P2+FRAMEP2 76/156=48.72%; P2_TRIO 76/152=50.00%; WIN_PAIR 80/163=49.08%; FULL5 85/169=50.30%. Monthly FULL5: Jun25/48=52.08, Jul28/59=47.46, Aug32/62=51.61. P2_TRIO: Jun22/42=52.38, Jul26/55=47.27, Aug28/55=50.91. ALL_P2 only: 50.00,49.12,49.09. WIN_PAIR:52.83,48.00,46.67.
Interpretation: all_p2 is indeed a strong single PH signal and creates nearly all of the candidate-volume jump from BASE, but FULL5 remains slightly best aggregate (+0.94pp over all_p2, +0.30pp over P2 trio) and especially August. No compact subset clearly dominates FULL5 under rolling origin. PH_FULL5 remains the strongest current research form; do not simplify yet. Note BASE at cut .36 has only 9 selections, so PH is not merely a tiny refinement: it materially recalibrates scores/candidate volume. Next audit should compare FULL5 against leave-one-PH-feature-out variants under rolling origin to identify whether any individual PH feature is harmful/redundant, while keeping C=.5/cut=.36 fixed and no tuning.


## v30 rolling PH5 leave-one-feature-out ready
Fixed C=.5/cut=.36 and same rolling origin as v28/v29. Compare PH_FULL5 against exactly five 4-feature variants dropping one of all_win, all_p2, frame_win, frame_p2, recent_p2. No future month, no retuning, September UNREAD. Paired diagnostics use FULL5 as reference so we can see which omission adds/removes winners rather than relying only on aggregate rate. Script eeede100ebdd91c410af16b7b76c45a08d138e5c; workflow e74bb24300e52a962ea1660c1c68020a64dda5ce. Refetch preflight passed: compile, fixed C/cut, generated five DROP specs, September UNREAD, no literal escaped-newline. Production unchanged. Next dispatch audit-4head-ph4-leaveone-rolling-v30.


## v30 first dispatch failed in preflight; root cause fixed
Run 35688127757 / Job 106619216468 failed before data build/research. Root cause was an incorrect grep assertion in workflow: it searched regex DROP_.*UPPER, but source constructs names with k.upper(), so valid source could never match. Python compile itself passed. This was not a model/data failure and no September outcomes were read. Fixed workflow preflight to verify SPECS presence while source refetch separately confirms generated DROP expression. Fix commit 9c5f17eeff59a2e5767e0598c36d870daddd3f49. Full refetch preflight repeated: compile command present, fixed C=.5/cut=.36, five DROP generation expression present, September UNREAD declaration, no literal escaped-newline. Do not reuse failed run; fresh dispatch required.


## v30 SUCCESS — PH5 leave-one-feature-out
Fresh Run 35689710826 / Job 106623891496 / Artifact 10678138186 SUCCESS; digest sha256:fa16760fe24989b7339a87fb3189dd1842cb157875445a7d6a0f2b985ffd7dbb. Fixed C=.5/cut=.36 rolling origin, no retuning, September UNREAD, production unchanged.
Aggregate Jun-Aug: FULL5 169/85=50.30%; DROP_ALL_WIN 157/77=49.04%; DROP_ALL_P2 166/85=51.20%; DROP_FRAME_WIN 175/84=48.00%; DROP_FRAME_P2 171/86=50.29%; DROP_RECENT_P2 173/84=48.55%. Monthly DROP_ALL_P2: Jun29/54=53.70%, Jul25/54=46.30%, Aug31/58=53.45%. DROP_FRAME_P2: Jun24/46=52.17, Jul29/63=46.03, Aug33/62=53.23.
Interpretation: all_win, frame_win and recent_p2 are useful enough that dropping them worsens aggregate. frame_p2 is approximately neutral. Surprisingly, dropping all_p2 gives the best aggregate rate (+0.91pp vs FULL5) with nearly same winner count (85) and 3 fewer selections, despite all_p2 being strong alone in v29. This indicates redundancy/interaction: all_p2 carries signal alone but may be partially redundant or distort calibration when the other four PH features are present. Difference is small and July worsens, so do not promote yet. Next research should specifically validate FULL5 vs DROP_ALL_P2 vs DROP_FRAME_P2 with fixed design across additional historical rolling windows if available, or paired flip analysis from v30 artifact; first inspect paired flips to determine whether DROP_ALL_P2's 3 pruned races are misses/winners and month concentration before any new model choice.


## v30 paired-flip inspection — DROP_ALL_P2 is not a clean pruning improvement
Downloaded Artifact 10678138186 and inspected paired.csv directly. FULL5 vs DROP_ALL_P2 aggregate: overlap 147R/77 heads=52.38%; FULL5-only 22R/8=36.36%; DROP_ALL_P2-only 19R/8=42.11%. Thus DROP_ALL_P2 does NOT simply prune 3 bad FULL5 races; it swaps 41 races while preserving the same 85 winners overall. Monthly flips: Jun FULL-only4/1=25%, DROP-only10/5=50% (helps); Jul FULL-only9/3=33.33%, DROP-only4/0=0% (hurts); Aug FULL-only9/4=44.44%, DROP-only5/3=60% (helps). The +0.91pp aggregate rate is from 3 fewer selections with equal winners, but the mechanism is month-dependent and July replacement set failed 0/4. Therefore no promotion; FULL5 remains safer current research anchor. Next useful falsification is extend fixed FULL5 vs DROP_ALL_P2 (and optionally DROP_FRAME_P2) to earlier historical rolling windows if causal source coverage permits, without changing cut/C or using Sep outcomes.


## FORMAL ADOPTION decision — HEAD4 PLAYER_HISTORY PH5
User explicitly approved formal adoption on 2026-09-22. Adopt the five boat-4 PLAYER_HISTORY features (all_win, all_p2, frame_win, frame_p2, recent_p2) into the HEAD4 head-probability model. Research evidence at fixed C=.5/cut=.36 rolling Jun-Aug: 169R/85 heads=50.30%, ~56R/month; PH-free score at same cut selected only 9R/3 heads, noting same-cut comparison is not calibration-fair. v30 did not establish a robust feature removal, so keep all five.
Production freeze script commit 7caa3533eba58afe9e6db8a8d0b5aec934480f99 and workflow commit 1e059394ddeb1a492dac9922db5f7dac25581df4 prepared. Freeze fits causal Mar-Aug data through 2026-08-31 only, C=.5, cut=.36, September labels unread, and emits HEAD4_PH5_PRODUCTION_V31_20260831 artifact. IMPORTANT: formal adoption is decided, but production integration is not complete until freeze workflow succeeds and emitted artifact is committed/wired into LIVE scanner/runner with verification. Next: dispatch freeze-4head-ph5-production-v31, verify artifact, then integrate into LIVE head_prob replacing old 78-feature racecard-only artifact while preserving causal player history through target_date-1.


## v31 pre-dispatch exhaustive inspection strengthened
User explicitly requested error-risk inspection before firing. Refetched full freeze script, workflow, and six-month parent builder. The v31 code path reuses the same prepare_4head_6m_v93_neutral_waku + v23 build_ph chain that succeeded in v29/v30. Static checks: no literal escaped-newline, py_compile present, fixed C=.5/cut=.36, exactly PH_FULL5 spec, Sep labels false, same-day false. Added a post-BoatraceCSV-checkout import smoke test so dependency/import/env errors are caught before the expensive parent build; it asserts C, cut, and exactly five PH features. Workflow hardening commit 54bc29863663fbf8625d1dcb062e30fa3470f64a. No dispatch was triggered by assistant. Remaining runtime risk is external/source availability or an unexpected upstream data change; no known deterministic code/workflow error remains from inspection.


## v31 production freeze SUCCESS
Run 35692378750 / Job 106631911557 / Artifact 10678742960 SUCCESS; digest sha256:794fa223975c40a24f7a33bba383e884c3693e3b25336eee31a9119a3e362026. Preflight/import smoke passed. Reproduced rolling PH_FULL5: Jun48/25=52.0833%, Jul59/28=47.4576%, Aug62/32=51.6129%, aggregate169/85=50.2959%. Artifact contains HEAD4_PH5_PRODUCTION_V31_20260831 fitted Mar-Aug through 2026-08-31, C=.5, cut=.36, five b4 PLAYER_HISTORY features, September UNREAD. Formal model freeze is now complete. LIVE integration is still the next step: commit the emitted artifact into repo and wire scan_4head_120r_pre_live.py head_prob to the new PH5 artifact plus causal target_date-1 player state, then verify against artifact scoring before declaring LIVE production switch complete.
