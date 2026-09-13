# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## READ THIS FIRST — authoritative current 1-head state
Latest GitHub wins over old chat memory/stale handoff text.
Mandatory pattern: **handoff update -> work -> result append -> next work handoff update**.
Before every work unit/code change/restart record current position, exact work, success criteria, failure fallback. After every work unit record actual work, commit SHA(s), Actions Run ID/status, metrics/results, exact next resume point.

---

# 1. Frozen production stack — DO NOT ALTER
- HEAD v308
- SECOND v317 `OUTER_L2_1`
- THIRD v318 `DROPSTART_T0.1`
- 3-ticket policy v320 `HYBRID alpha=.70`
- exactly 3 trifecta tickets per selected race
- composite odds = `1 / (1/o1 + 1/o2 + 1/o3)`
- frozen regression **345 selected / 290 boat1 wins / 139 exact3**
- v308 q=.980, opponent mass>=.375, head cutoff=0.8073405637
- v308 is true PRE; same-race exhibition is post-PRE only.

Guardrails:
- Jul/Aug 2026 = NON-PRISTINE/reference-only; never tune/promote on them.
- September outcomes = UNREAD.
- no same/later-race result, payout, future/backfill contamination.
- month M trains strictly on `<M`.
- missing current exhibition inputs fail closed for any feature/route that requires them.
- no `meet_*` unless separately audited.
- neutral 0.5 defaults are not proof a raw metric existed.
- do not modify v308/v317/v318/v320/v323.

Mandatory causal cache family:
- `cache_v313_1head_opponent_pre.csv.gz`
- `cache_v313_1head_opponent_p3.csv.gz`
- `cache_v313_1head_opponent_p4.csv.gz`
- `CACHE_V313_1HEAD_OPPONENT_CAUSAL.md`

---

# 2. Frozen research summary through v320
- v309 exact3 132/345; SECOND TOP2 71.72%.
- v310 causal p3/p4 exact3 133/345; SECOND TOP2 72.07%.
- v311 DROP_START exact3 136/345; SECOND TOP2 72.41%.
- v312 outer gate exact3 136/345; SECOND TOP2 73.10%.
- v314 role split unstable, not promoted.
- v315 pairwise SECOND exact3 133/345.
- v316 multiclass SECOND exact3 136/345.
- v317 `OUTER_L2_1` exact3 137/345.
- v318 `DROPSTART_T0.1` exact3 137/345.
- v319 direct ordered-pair weaker, exact3 134/345.
- v320 `HYBRID alpha=.70` exact3 **139/345=40.29%**.

Useful frozen code:
- `run_v308_1head_volume_opponent_joint.py`
- `run_v317_1head_opponent_error_features.py`, `add_engineered(...,'OUTER')`
- `run_v318_1head_opponent_third_rebuild.py`, `pc_predict(...,.1,'DROP_START')`
- `run_v299_1head_trifecta3_policy_search.py`
- frozen ticket identity `analysis_v320_1head_exact3_ticket_policy_best_race.csv`

---

# 3. Completed production/reference work v321-v324
- v321 Jul/Aug NON-PRISTINE reference: Run 34750719803; 55R / head45 / exact3 21 (38.18%).
- v322 composite odds: Run 34753932483; 345R / 139 exact3 / 339 complete odds; ROI 91.27%; no BUY cutoff promoted.
- v323 production adapter: Run 34757079269; frozen 345/290/139 preserved; September outcomes unread.
- v324 corrected Jul/Aug odds audit: Run 34762939723; 55R/21 exact3, ROI85.66%; composite>=3 unsupported.

---

# 4. Exhibition source audit
Historical result-blind sources:
- `data/previews/tkz/YYYY/MM/DD.csv`
- `data/previews/stt/YYYY/MM/DD.csv`
- `data/previews/original_exhibition/YYYY/MM/DD.csv`
- audited transform `backtest_v51_lane_corrected_tickets.py::corrected_direct`
- `corrected_direct` applies lane/frame correction then within-race rank scores; ST bias is learned only from prior dates.
- coverage on historical frozen source family: tkz/stt ~92.8%, original exhibition ~88.5%.

`corrected_direct` semantics confirmed:
- exhibition time: lower raw adjusted time => higher 0..1 rank score.
- start exhibition: lower lane-bias-adjusted ST => higher 0..1 rank score.
- original lap/turn/straight: lower corrected raw metric => higher 0..1 rank score.
- missing original metrics leave neutral 0.5 internally, therefore route readiness must rely on raw source-completeness flags and must fail closed rather than treat 0.5 as observed.

Live/result-blind current exhibition source builder lineage includes `build_4head_v283_current_exhibition_live.py` with `cur_ex`, `cur_st`, `cur_orig_lap`, `cur_orig_turn`, `cur_orig_straight`, `cur_orig_avg`.

---

# 5. v325-v327 postfilter attempts — COMPLETE / NOT PROMOTED
## v325
Run 34764329333 success. Candidate `one_turn>=0.8`. June PASS 8/25=32.00%, baseline 32/92=34.78%. `FORWARD_SUPPORTED=False`.

## v326
Final Run 34766426083 success. Candidate `sec_st_mean_margin<=-0.6`. June PASS 8/25=32.00%, baseline 34.78%. `FORWARD_SUPPORTED=False`.
Feature-specific raw readiness implemented in `run_v326_1head_ticketaware_exhibition.py`.

## v327
Run 34766775614 success. Candidate `opp_mass>=0.416322574702382 AND third_orig_mean_margin>=-0.37777777777777793`.
Feb-Apr 18/42=42.86%; May 28/56=50.00%; June PASS 13/39=33.33% vs baseline 34.78%; `FORWARD_SUPPORTED=False`.
Conclusion: another narrow 1D/2D postfilter is not enough.

---

# 6. v328 ticket-selection error audit — COMPLETE / REPORTED
Implementation commits:
- `bab1896a23393f0b564f741cf0332fb20f74922b` script
- `9418247f6bc40534881b03586b9019443da45a52` workflow
Actions Run **34767480326** SUCCESS, Job **103750928927**, Artifact **10321143424**, SHA256 `ad41a0084632207b45debcb10b52da6bd8e8a2c25386e9cdfa7c83be9b43f89e`.

ALL: R345, head290=84.06%, exact3 139=40.29%; misses HEAD_LOSS55 / SECOND_NOT_COVERED77 / SECOND_COVERED_THIRD_MISS74.
June: R92, head75=81.52%, exact3 32=34.78%; SECOND top2 51/75=68.00%; conditional THIRD top2 53/75=70.67%; HYBRID pair top3 32/75=42.67%, top6 47/75=62.67%.
Conclusion: June deterioration is broad; richer direct-before-start judgement is the next target.

---

# 7. Work Unit 6B — v329 3-head/4-head direct-before-start source audit — COMPLETE
User requested that v329 imitate the 3-head and 4-head immediate-before-start judgement mechanism after v328.

Actual audit:
1. Current 3-head handoff `CHAT_HANDOFF_20260911_3HEAD_V288_PRODUCTION.md` confirms direct-before-start is **not a single exhibition cutoff**. The v242/v243 exhibition base is organized into later **S/A/B routes with independent rescue behavior**.
2. Audited historical implementation `backtest_v51_lane_corrected_tickets.py` shows the concrete 3-head multi-axis exhibition architecture:
   - 3-makuri preview composite = `.28*ex + .28*st + .22*straight + .17*orig_avg + .05*venue`
   - 3-makuri-sashi preview composite = `.17*ex + .22*st + .17*lap + .27*turn + .12*orig_avg + .05*venue`
   - direct judgement historically separated A/S grades rather than one keep/drop scalar.
   These old exact thresholds are NOT copied as current 1-head thresholds; the architecture/axis weighting is what is transferred.
3. Current 4-head handoff `CHAT_HANDOFF_20260911_4HEAD_V291_AUTOLIVE.md` confirms sequential **PRE -> POST -> ENV_ENTRY** gating with strict fail-closed missing-input behavior.
4. Current 4-head S policy thresholds are PRE>=0.28, POST>=0.25, ENV_ENTRY>=0.224790, but these head4-specific thresholds are NOT transferable to head1.
5. 4-head POST requires result-blind current fields including current ST rank, boat4 ST, boat4-vs-boat3 ST gap, original straight/lap/turn and tilt. Required missing inputs => ERROR_NO_BET/fail closed.

Transferable common architecture:
- keep PRE selection frozen before current exhibition;
- evaluate multiple current exhibition dimensions, not one metric;
- use a primary POST/core strength stage plus a separate context/opponent/entry-quality stage;
- support multiple grades/routes (strong S, balanced A, exceptional-dimension B rescue) instead of tuning one cutoff;
- route-specific raw readiness and fail-closed behavior;
- do not change frozen tickets in this experiment.

Not transferred in v329:
- 3-head/4-head head-specific thresholds;
- 3-head tilt bonus and venue bonus (not yet independently audited for the 1-head frozen cohort);
- 4-head-specific boat4-vs-boat3 tactical fields;
- odds/market features;
- Jul/Aug/September outcomes;
- any live refit.

---

# 8. Work Unit 6C — v329 multistage exhibition judgement — ABOUT TO IMPLEMENT
Current position:
- source audit above is complete and recorded before model code.
- frozen production remains v308/v317/v318/v320/v323.

Exact implementation design:
1. Reuse frozen 345-row v320 identity and `run_v326_1head_ticketaware_exhibition.py::build_dataset()` so historical exhibition inputs retain audited lane correction and raw-source readiness.
2. Define two head1 POST composites from semantically favorable 0..1 rank scores:
   - `attack_core = .30*one_ex + .30*one_st + .23*one_straight + .17*one_orig_avg` (3-makuri-like straight/ST route, renormalized after excluding venue).
   - `turn_core = .21*one_ex + .27*one_st + .34*one_turn + .18*one_orig_avg` (3-makuri-sashi-like turn route, renormalized without lap/venue because `one_lap` is not yet exposed by the frozen v326 dataset).
3. Define separate ticket/opponent environment quality using only current audited ticket-aware margins:
   - `env_pair = .30*sec_ex_mean_margin + .30*sec_st_mean_margin + .20*third_turn_mean_margin + .20*third_straight_mean_margin`.
   Higher is semantically stronger because all underlying corrected rank scores are higher=better.
4. Route-specific readiness:
   - attack requires tkz_all6 + stt_all6 + orig_straight_all6 + orig_avg_all6.
   - turn requires tkz_all6 + stt_all6 + orig_turn_all6 + orig_avg_all6.
   - env requires tkz_all6 + stt_all6 + orig_turn_all6 + orig_straight_all6.
   Missing any required family => that route is unavailable; no neutral-value rescue.
5. Mimic S/A/B architecture using a **small predeclared grid** of discovery quantiles only (not arbitrary continuous optimization):
   - S: attack strong + env strong.
   - A: turn strong + env strong.
   - B rescue: either core exceptional + env at least non-weak.
   Candidate quantiles are restricted to core {0.55,0.65,0.75}, exceptional {0.80,0.90}, env {0.40,0.50,0.60} from Feb-Apr only.
6. Freeze one route configuration only if May confirms same-direction exact3 lift with meaningful coverage; selection preference is validation coverage first, then validation exact3 rate, then discovery rate. Minimum combined PASS coverage: Feb-Apr>=25 and May>=15; May exact3 must be at least its unfiltered baseline and discovery exact3 must be at least its unfiltered baseline.
7. Only after a config is frozen from Feb-Apr + May, perform one-shot June forward evaluation. If no config passes validation, record v329 unsupported without searching June.
8. Production promotion criterion for this research version: June PASS R>=15, June exact3 rate > June baseline 34.78%, June head rate not more than 5 percentage points below June baseline head rate, and direction remains positive. Otherwise NOT PROMOTED.
9. Never alter the 3 frozen ticket strings; assert 345/290/139 identity before any route search.

Success criteria:
- deterministic script/workflow completes and preserves 345/290/139.
- route-specific readiness is audited and fail-closed.
- chosen config, Feb-Apr, May and one-shot June metrics are emitted.
- no Jul/Aug tuning/outcomes and no September outcomes are opened.

Failure fallback:
- if code/schema/readiness fails, record the exact failure here before any correction, then patch and rerun.
- if no May-supported configuration exists, v329 ends NOT PROMOTED; do not weaken constraints by looking at June.

Exact next resume point:
- create `run_v329_1head_multistage_exhibition.py` and `.github/workflows/v329-1head-multistage-exhibition.yml`, run Actions, then append actual result before any v330 work.
