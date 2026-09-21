# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research version: `v289-addon-wave1`
- decision: **NO_ADOPTION_WAVE1**
- v288 production is unchanged; baseline replay assertion is 94R / 52 hits / payout 1,622,070 yen.
- July/August are NON-PRISTINE. September outcomes were not loaded or used.
- Candidate universe is only v288 final NO_BET among operational PRE S/A and v242-buyable races.

## Wave-1 result
- candidate pool: 178 races
- best tested variant: `return_rank@0.45`
- best add-on: 84R / 15 hits / ROI 54.92% / profit -378,700 yen
- combined: 178R / ROI 117.04%

## Methods tested / dead ends retained
- `residual_hit`: prior-reject outcome effect ranking over pre-race safe features.
- `exhibition_upgrade`: current exhibition/ST/original-exhibition family only.
- `return_rank`: prior-reject realized-return ranking trained only on prior months.
- `attack_style_split`: separate stretch-vs-turn regimes, then outcome ranking.
- `orthogonal_consensus`: residual + exhibition + return independent-score consensus.
- `ev_calibrated`: residual hit score plus current composite odds, alpha chosen on prior months only.

## Real-operation audit
- all scoring inputs are columns already present before settlement in the canonical v243/v288 audit artifact;
- decisions use only prior-month outcomes for fitting; current test-month result/payout enters settlement only;
- missing features are median-imputed from prior training; production promotion must replace any required-current missingness with fail-closed gates;
- overlap with v288 baseline is zero by construction;
- no production workflow/model was changed.

## Next restart point
- If no wave-1 variant passes, next research must change the information/ticket family rather than loosen v288 thresholds.
- Priority next: opponent/ticket re-ranking on NO_BETs, PRE-B/new-population research with full leak audit, and venue/field archetype residual models.
- Before any promotion, build live shadow scorer with fail-closed source checks and exact 10,000-yen Dutch.

## Generated artifacts
- `research_v289_3head_addon.json`
- `research_v289_3head_addon.md`



## 2026-09-21 — Waku10 restored-source v288 audit (WORK START)
- User reports historical Waku10 restoration is complete. Fresh main confirms shared Boatcast Waku10 Mar-Jun commit 6410b14d, July shared store edcb7be3, and nested-loader fix 44231256.
- Existing v288 operational parity remains frozen reference: 94R total, Feb8/Mar12/Apr12/May16/Jun14/Jul13/Aug19. Do not alter thresholds/routes while measuring Waku10 source effect.
- February fair overlap audit Run 35563969125 was SUCCESS: v288 8R/6 heads=75%, A+.60 32R/12 heads=37.5%, BOTH=0; Sep-2026 unused; no threshold tuning.
- Next: build a source-only Waku10 audit for v288. Compare frozen v288 reference vs restored historical Waku10 with all v288 thresholds unchanged. Measure changed Waku34 values, candidate additions/removals, route changes, race count/head rate; only after membership freeze inspect outcomes. September 2026 outcomes remain UNREAD.

- Waku10 audit Run 35579065473 / Job 106267460878 FAILED before main audit. Preflight passed. Root cause: workflow downloaded wrong artifact Run 35467021760 / research-3head-a-opponent-reference-audit, which contains only reference JSON and not analysis_v243_3head_expand_feature_audit.csv. Main audit was skipped; no outcomes read.
- Verified canonical source path from successful v288 parity workflow: Run 34383567078 artifact v243-3head-expand-feature-audit / analysis_v243_3head_expand_feature_audit.csv. Workflow fixed to use this exact source and added required-column contract check. Fix commit 5af7a5b4440923c15ad50b4c9f36da8510963da7. Do not rerun old failed attempt unchanged.

- Restored Waku10 membership audit SUCCESS: Run 35580738921 / Job 106272777317 / Artifact 10630525833. Outcome-free; thresholds unchanged; September outcomes unread. Old v288 operational membership 94R -> restored 96R, with NO removals. Added only 2 races: 202607222309 and 202608080206. Monthly old->restored: Feb 8->8, Mar 12->12, Apr 12->12, May 16->16, Jun 14->14, Jul 13->14, Aug 19->20. Restored routes: Feb S7/A1/B0; Mar S8/A2/B2; Apr S8/A3/B1; May S9/A3/B4; Jun S4/A6/B4; Jul S7/A3/B4; Aug S16/A2/B2. Coverage restored all source rows except 1 June row (72/73); old Waku values differ widely from reconstructed exact values, so next step must audit formula/semantics before settlement, not immediately treat all reconstructed values as canonical. Membership is frozen before any outcome read.

- STARTED Waku10 semantics audit after Run 35580738921. Critical finding from source: v288 feature f__c_b3_minus_b4_waku_st is NOT raw ST3-ST4. In analyze_v222_3head_broad_feature_audit.py, c_b*_waku_st = clamp((0.24 - raw_waku_st)/0.14), then c_b3_minus_b4_waku_st = normalized_strength3 - normalized_strength4. The first restored audit used raw ST3-ST4, so its 94->96 membership comparison is not semantically valid for adoption. backtest.py confirms raw race_features waku_st itself is raw frame-average ST with national-ST fallback. Next audit must reconstruct the exact v222 transform and fallback semantics, then rerun outcome-free membership before any settlement.

- Run 35581413076 / Job 106274916102 FAILED at preflight compile only; main audit skipped and no outcome data read. Root cause was literal backslash-n tokens introduced in both Python source and workflow while patching exact normalized Waku10 semantics. Fully re-audited source text, removed all literal backslash-n tokens, verified restored() now computes clamp((.24-ST3)/.14)-clamp((.24-ST4)/.14), and repaired workflow semantic preflight. Final cleanup commits: 60299025 (script), 37794501 + d2bf32c (workflow). Next action: fresh manual dispatch only after these commits.


## 2026-09-21 chat handoff — v288 Waku10 restoration / two-tier preparation

### User intent / operating rules
- Continue 3HEAD research/production from latest GitHub, not stale chat memory.
- v288 remains the high-precision CORE candidate; current A+.60 model is intended as EXPANDED layer. Do not silently change native v288 identity (v242 opponent selection / variable 5–10 tickets / 10,000-yen Dutch) into the newer V221 protected-six system.
- Same-race overlap, if any, should be classified CORE and not double-bought.
- September 2026 outcomes must remain UNREAD for this project.
- Before every trigger: compile/import/path/signature/required-column/type/month/data-scope/leakage/fixed-ticket/artifact/YAML/dependency checks. After every run: verify actual Job/log/artifact before claiming success.
- User manually dispatches workflows. Never claim dispatch/completion without evidence.
- Repeated literal `/n` / `\\n` mistakes have been a major user pain point; inspect the exact committed file after any text patch, especially YAML heredocs/Python.
- Record meaningful work before/after in this handoff. Concurrent agents edit main, so always fetch fresh file SHA before update.

### Frozen state carried into this chat
- 3HEAD A head gate formally adopted; purchase gate `post_motor_inner_rank_edge >= +0.60`.
- Nov–Jan development cohort 118R / 54 boat3 wins = 45.76%.
- Feb and Mar are already READ/non-pristine after one-shot forward checks. September remains UNREAD.
- Opponent protected fixed-six SECOND4 rescue rule is frozen at p4 turn >= .50:
  - if condition fires, promote highest-ranked 3-4-X outside Top6;
  - never drop existing Top6 3-4-X;
  - drop weakest non-4-second Top6;
  - exactly six tickets.
- Dec–Jan dev protected: 29/41=70.73%; Feb forward 6/12=50%; Mar forward 11/15=73.33%; Feb+Mar forward 17/27=62.96%.
- Formal two-tier production implementation is still pending.

### v288 exact operational replay baseline
- `verify_v288_operational_pre_replay.py` is the frozen operational PRE replay.
- Source: `analysis_v243_3head_expand_feature_audit.csv`.
- Walk-forward prior-month training; Dec/Jan are training-only because `if i<2: continue`; operational evaluation starts Feb.
- Frozen routes:
  - S core: target + `f__c_b3_minus_b4_waku_st <= 0.5` + `f__c_b3_minus_b4_st >= -0.6` + `f__c_b3_meetst <= .861111...`
  - A: bet=1, not S, ST34 >= .6, wall12_weak <= .24875
  - B: bet=1, not S/A, motor32 >= .223885714..., inside_nst <= -.07142857...
- Exact historical 94R parity previously confirmed:
  - Feb 8 (S7/A1/B0)
  - Mar 12 (S7/A3/B2)
  - Apr 12 (S8/A3/B1)
  - May 16 (S9/A3/B4)
  - Jun 14 (S4/A6/B4)
  - Jul 13 (S6/A3/B4)
  - Aug 19 (S14/A2/B3)
  - total 94.
- Exact source-date audit confirmed source 2025-12-01..2026-08-31, no Sep rows.

### Fair overlap finding before Waku10 correction
- Feb-only fair overlap audit: v288 8R/6 heads=75%; A+.60 32R/12 heads=37.5%; BOTH=0.
- This supports CORE+EXPANDED direction but is only one month and does not replace a full overlap audit.

### Waku10 source restoration context
- Shared historical Boatcast Waku10 has been restored/wired by concurrent work for Mar–Jul, with July validated against BoatraceCSV.
- `backtest.py::race_features` raw `waku_st` semantics:
  `f(w.get('艇b_枠番別平均ST'), f(r.get('艇b_全国平均ST'),0.20))`.
- Important: the v288 feature `f__c_b3_minus_b4_waku_st` is NOT raw ST3-ST4.
- Exact construction is in `analyze_v222_3head_broad_feature_audit.py::build_current`:
  `c_b{b}_waku_st = clamp((.24 - raw_waku_st)/.14)`
  then
  `c_b3_minus_b4_waku_st = c_b3_waku_st - c_b4_waku_st`.
- Therefore exact restored edge must be:
  `clamp((.24-ST3)/.14) - clamp((.24-ST4)/.14)`.
- This is a normalized “start strength” difference, where smaller raw ST produces larger normalized strength.

### First restored membership audit — technically successful but semantically invalid for adoption
Run 35580738921 / Job 106272777317 / Artifact 10630525833, SUCCESS.
- Preflight/source contract/main audit/artifact all succeeded.
- No outcomes, payouts, odds, or Sep2026 outcomes were read.
- It reported old94 -> restored96, no removals, additions:
  - `202607222309`
  - `202608080206`
- Monthly old->reported restored:
  Feb 8->8, Mar 12->12, Apr 12->12, May16->16, Jun14->14, Jul13->14, Aug19->20.
- BUT that version incorrectly reconstructed `_restored_waku34` as raw `ST3-ST4`. Because v288 uses normalized strength difference, **do not use the 94->96 result as model evidence or production membership**.
- The very low exact-match counts against the frozen old feature were the clue that exposed this semantic error.

### Exact-semantics correction work
- Source audit established exact v222 formula above and recorded it in handoff.
- `research/audit_v288_waku10_restored_membership.py` was changed to reconstruct normalized edge only, with no threshold tuning and no outcome access.
- Workflow: `.github/workflows/research-v288-waku10-restored-membership.yml`.
- Canonical frozen source download was corrected earlier to use successful Run `34383567078`, artifact name `v243-3head-expand-feature-audit`, file `analysis_v243_3head_expand_feature_audit.csv`.
- Workflow now performs canonical source contract check for race_code/date/Waku10/ST/meetST columns before audit.

### Failure history in this chat — important not to repeat
1. Run 35579065473 / Job 106267460878 failed before main audit because workflow downloaded wrong artifact from Run 35467021760. That artifact contained reference JSON, not canonical CSV. No outcomes read.
2. Corrected canonical source to Run 34383567078 artifact `v243-3head-expand-feature-audit`.
3. Run 35580738921 succeeded but used the wrong raw Waku10 difference formula; result is diagnostic only, not adoptable.
4. Exact normalized formula was then patched, but text patching introduced literal backslash-n tokens.
5. Run 35581413076 / Job 106274916102 failed at **Preflight compile**:
   `SyntaxError: unexpected character after line continuation character`
   at `def clamp(... )\\ndef restored(code):`.
   Main audit skipped; no outcomes read.
6. Further inspection found literal `\\n` contamination in BOTH Python source and YAML heredoc. These were removed and exact files re-fetched.
7. Workflow was temporarily malformed as:
   `code="\\`
   newline
   `".join(...)`
   which made GitHub unable to expose/dispatch the workflow. User reported “発火できない”.
8. Fixed the YAML source join to a simple safe line:
   `code=" ".join(line for line in s.splitlines() if not line.lstrip().startswith("#"))`
   Commit `5ad85dbcfbd248ac79e964856ba5e387488c26e5`.
- After that fix, the user explicitly reported: **“発火した”**.
- This new fresh run is currently the next checkpoint. Its Run ID was not yet supplied in this chat at handoff time.

### Current committed audit expectations
Before trusting the fresh run, verify from GitHub, not assumptions:
1. Job status/conclusion.
2. Preflight compile succeeded.
3. Static safety assertions succeeded:
   - no `data/results/`
   - no payout path
   - no odds path
   - `thresholds_changed=False`
   - `sep2026_read=False`
   - normalized formula string present.
4. Canonical frozen v243 artifact downloaded from Run 34383567078 and required-column contract passed.
5. Main audit ran.
6. Artifact `research-v288-waku10-restored-membership` exists.
7. Inspect JSON/log for:
   - exact match counts by month,
   - old_selected vs restored_selected,
   - added and removed race codes,
   - old/restored monthly counts,
   - restored S/A/B route counts.
8. Do NOT read results/payout/odds just to evaluate membership. First freeze the exact corrected membership outcome-free.
9. If corrected Waku10 feature still differs widely from frozen old feature, investigate parser/source/fallback semantics before settlement. Do not tune thresholds.
10. One June source row was missing in the earlier raw-difference audit (72/73 restored). Check whether it remains missing and whether exact `race_features` national-ST fallback must be reconstructed for that row before claiming canonical parity.

### Likely next research sequence after fresh run succeeds
A. Freeze corrected v288 membership using exact normalized Waku10 semantics.
B. Explain any membership changes from old94 race-by-race using only pre-race values/routes.
C. Only after membership is frozen, perform a one-shot historical outcome comparison for the corrected v288 set (respecting already-read/non-pristine periods and keeping Sep UNREAD).
D. Re-run fair CORE(v288 corrected) vs EXPANDED(A+.60) overlap by common operational months, not Dec/Jan cold-start.
E. Then formalize two-tier production:
   - CORE = native v288 semantics unchanged.
   - EXPANDED = A+.60 + V221 Top6 + protected SECOND4 .50 exact-six.
   - overlap => CORE only, no double buy.
F. Preserve v288 native opponent/ticket/staking identity; do not retroactively label V221 protected-six as “v288”.

### Latest relevant commits from this chat
- `5af7a5b4440923c15ad50b4c9f36da8510963da7`: correct canonical frozen v243 source artifact path.
- `5c2a06e6f95c4d50a92d95f165af66d05a311d05`: recorded successful but raw-difference audit result.
- `aee69577a71038acd174309b950b9eac1707fcd1`: recorded exact normalized v288 Waku10 semantics finding.
- Multiple intermediate patch commits attempted normalized formula/newline repair; do not rely on them alone.
- `60299025daf50d11189ca7de9d12d883dd8eea9b`, `37794501fffad4c8c35fc9936844e2cd3f1c3276`: literal backslash-n cleanup attempts.
- `5cc0e443cfbeb91c796afc99fee3fa307f6dae1a`: recorded Run 35581413076 preflight failure.
- **`5ad85dbcfbd248ac79e964856ba5e387488c26e5`**: latest key workflow fix restoring valid dispatchable YAML/Python preflight source join.
- Always inspect current main before editing because concurrent 1HEAD/4HEAD agents may have added newer commits.

### Exact next-chat restart instruction
“Read `CHAT_HANDOFF_3HEAD_AUTO_RESEARCH_CURRENT.md` and latest GitHub. The corrected normalized-v288-Waku10 audit was manually fired after commit `5ad85dbc`. First identify/check that fresh Actions Run, verify Job/log/artifact and outcome-free guardrails, then freeze the corrected membership. Do not use Run 35580738921’s 94->96 result as canonical because it used raw ST3-ST4. September 2026 outcomes stay UNREAD.”


## 2026-09-21 — corrected Waku10 audit Run 35582576531 failure + repair
- Fresh manual dispatch after 5ad85dbc identified as Run 35582576531 / Job 106278568971, head 5ad85dbcfbd248ac79e964856ba5e387488c26e5.
- Run FAILED at Preflight compile only. Canonical artifact download and main outcome-free audit were skipped; no outcomes/payout/odds/Sep-2026 outcomes were read. Upload step found no JSON artifact.
- Exact error: research/audit_v288_waku10_restored_membership.py line 79 had an unterminated string literal in OUT.write_text(...+" newline "), left by earlier newline patching.
- Repaired output newline without escape-sensitive text by using +chr(10). Fix commit: 4306cf8779ed3dab3108dc1bf69dafa59c09cfad.
- Re-fetched committed source after repair; normalized Waku10 formula remains unchanged. Next action is manual fresh dispatch of research-v288-waku10-restored-membership from current main, then verify preflight/static safety/canonical v243 source/main audit/artifact before freezing membership. Run 35580738921 94->96 remains non-canonical. September 2026 outcomes remain UNREAD.


## 2026-09-21 — exact normalized Waku10 membership audit SUCCESS
- Fresh Run 35583037910 / Job 106279998203 / Artifact 10631555647 completed SUCCESS on head 329387671979b293f1fc255e20724f614ccfb689.
- All steps passed: compile/static safety, canonical frozen v243 artifact download/contract, outcome-free membership audit, artifact upload.
- Guardrails confirmed: thresholds_changed=false, outcomes_read=false, sep2026_read=false. Exact normalized formula used: clamp((0.24-ST3)/0.14)-clamp((0.24-ST4)/0.14).
- Corrected membership: old 94R -> restored 93R. Added none. Removed exactly 202605040103. Monthly: Feb 8, Mar 12, Apr 12, May 15 (old16), Jun14, Jul13, Aug19.
- Exact restored-vs-old Waku feature matches every comparable row in Dec-May, Jul, Aug; June 72/73 comparable rows all exact, with one restored-source missing row. Therefore prior 94->96 result from Run 35580738921 is definitively invalid and must not be used.
- Restored routes: Feb S7/A1/B0; Mar S7/A3/B2; Apr S7/A4/B1; May S8/A3/B4; Jun S4/A6/B4; Jul S5/A4/B4; Aug S14/A2/B3. Some S/A route relabels occur while total membership stays same because corrected Waku edge affects S core but A can rescue.
- Membership is now frozen outcome-free at 93R subject to investigating the single June missing source/fallback and explaining removed race 202605040103 pre-race values. Do not read outcomes yet for those investigations. September 2026 outcomes remain UNREAD.


## 2026-09-21 — next pre-outcome audit started
- After successful exact normalized Waku10 membership Run 35583037910, next task is outcome-free diagnosis only: identify why race 202605040103 is removed and identify the single June row whose restored Waku10 is missing.
- Must print old/restored Waku34, relevant frozen S/A/B gate inputs, old/new route, source/fallback provenance. No results/payout/odds and no Sep outcomes. Thresholds remain frozen.
