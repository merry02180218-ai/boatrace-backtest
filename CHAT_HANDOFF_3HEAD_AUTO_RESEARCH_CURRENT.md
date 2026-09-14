# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline 94R /52 hits / ROI172.560638%.
- Full research universe is Wave20 every available six-boat race Feb 1-Aug 31 2026, no v243/PRE/bet/route candidate prefilter.
- Wave20 Run34749917116 success: 32,111R; Feb4100 Mar4607 Apr4244 May4832 Jun4488 Jul4920 Aug4920; missing program date 2026-06-17.
- Wave19b Run34749707037 failed for missing payout column and remains superseded; do not revert to 584R scope.
- Pre-deadline features only; required feature missing => fail closed. Settlement and closing odds evaluation/staking only. JPY10,000 per selected race. Jul/Aug NON-PRISTINE. September forbidden.

## Wave36 benchmark
- Run34780059085: Apr-Jun391R/87 hits/ROI114.913%/+583,090; min month70.290%; red months1; maxDD717,360; exact v288 overlap0.

## Wave36S-C
- Run34786354062: Apr-Jun305R/74 hits/ROI128.218%/+860,660. RESEARCH_CANDIDATE, not production adoption.

## Rank replacement research
- Wave39 direct linear pair, Wave40 blend, Wave36G ordinal blend, Wave41 ExtraTrees, Wave42 factorized, Wave43 conservative rerank: all NO_ADOPTION.
- Wave44 attack-mode Run34794666290: March attack predictor AUC0.5078, March Top5 24->20, gate failed; NO_ADOPTION.

## Wave45 adaptive TopK — COMPLETE / NO_ADOPTION
- Run34796877432 success; artifact10330610070.
- March OOS gate passed at Top5-mass threshold0.747010 (q50): old24 hits -> adaptive26; early14->15, late10->11; avg tickets6.5.
- Apr-Jun pristine adaptive:391R/103 hits/ROI101.576%/+61,610; monthly Apr148.470 May97.624 Jun60.766; min month60.766; red months2; maxDD831,730; avg tickets7.01; v288 overlap0.
- Frozen Top5 comparator:391R/87 hits/ROI114.913%/+583,090; red months1; maxDD717,360.
- Jul-Aug NON-PRISTINE adaptive:328R/95 hits/ROI82.690%/-567,780; Jul73.077 Aug91.198; red months2; maxDD640,040.
- Combined v288+adaptive Apr-Jun:485R/155 hits/ROI115.334%/+743,680.
- Decision NO_ADOPTION: wider tickets materially raise hit count but dilute economics, worsen min month/red months/maxDD.

## Wave46 selective ticket compression — STARTING
- Preserve exact Wave36 head selection and opponent score ordering. Do not rerank and do not change p3 cutoff.
- Distinct hypothesis from Wave45: instead of widening uncertain races, compress tickets only when frozen opponent distribution is highly concentrated; use Top3 or Top4 on confident races and Top5 otherwise. JPY10,000 total per race remains constant, so fewer tickets concentrate stake without using odds for prediction.
- Confidence statistic is cumulative frozen opponent-model probability mass in Top3/Top4. Feb trains March. March OOS only chooses one predeclared quantile/width using ticket-hit retention and average ticket count, never payout/ROI.
- March gate: retain at least 23 of frozen Top5's 24 ticket hits, lose no more than one hit in either chronological half, and average ticket count <=4.6. Candidate selection prefers fewer tickets, then more retained hits.
- If gate passes, freeze absolute confidence threshold and width, evaluate Apr-Jun pristine once with standard expanding prior-month Wave36 training. Jul/Aug NON-PRISTINE use Wave36 frozen-through-Jun convention. September forbidden.
- Report R/hits/ROI/profit/monthly/min month/red months/maxDD/overlap/combined and average ticket count. No Apr-Aug tuning.

## Exact restart point
1. Implement/run Wave46 selective ticket compression.
2. Record exact March gate and Apr-Jun/Jul-Aug results.
3. If NO_ADOPTION, immediately launch a distinct full-population walk-forward idea; if candidate, retain only as research/shadow unless robustness is clearly superior.

## 2026-09-15 JST — RESUME BEFORE
- Re-read the latest prior chat context and this handoff; newest GitHub state remains authoritative.
- Confirmed Wave46 implementation/trigger commits are already present and Actions Run `34798878358` completed successfully after the prior handoff text was written.
- This work unit will recover the exact Wave46 job/artifact/results, compare them against the frozen Wave36 benchmark and v288 production baseline, and decide the next research step without changing production.
- Guardrails remain unchanged: Jul/Aug NON-PRISTINE; September outcomes forbidden/unread; no Apr-Aug tuning; no production change during this audit.
- Status: `WAVE46_RESULT_AUDIT_STARTED`.

## 2026-09-15 JST — WAVE46 RESULT AUDIT AFTER
- GitHub Actions Run `34798878358` completed `success`.
- Job `research`: `103837304227` (`success`).
- Head SHA: `9c61979a43b54560952bb1589c3f85dcb63ec68a`.
- Artifact: `3head-wave46-selective-ticket-compression`, Artifact ID `10330378720`, digest `sha256:9d540f66672a7e999ffa07b1a3519580bf49d1747242cd0591d8031a9a905441`.
- Frozen March comparator: 90 races / 38 head hits / 24 Top5 ticket hits; chronological halves 14 early + 10 late.
- Wave46 gate candidates:
  - Top3 q50: 19/24 retained, avg 4.0 tickets.
  - Top3 q60: 21/24, avg 4.2.
  - Top3 q70: 21/24, avg 4.4.
  - Top3 q80: 22/24, avg 4.6.
  - Top3 q90: 23/24, avg 4.8.
  - Top4 q50: 20/24, avg 4.5.
  - Top4 q60: 22/24, avg 4.6.
  - Top4 q70: 22/24, avg 4.7.
  - Top4 q80: 22/24, avg 4.8.
  - Top4 q90: 23/24, avg 4.9.
- Predeclared gate required >=23/24 retained, <=1 hit loss in each chronological half, and avg tickets <=4.6. No candidate satisfies all conditions.
- Therefore `march_gate_pass=false` / `decision=NO_ADOPTION_MARCH_GATE`.
- By design Apr-Jun payout/ROI evaluation was not opened after the failed March gate; Jul/Aug were not used for tuning; September outcomes remain forbidden/unread.
- Interpretation: simple confidence-based Top3/Top4 compression cannot reduce average ticket width enough without losing too many correct combinations. Preserve frozen Wave36 ordering and Top5 benchmark; do not adopt Wave46.
- Next research direction should return to the user's opponent-selection hypothesis while respecting the Wave44 failure: do not use or predict `決まり手` as an input. Test a distinct pre-deadline-only opponent-topology approach that allows different opponent ordering behavior for makuri-like vs makuri-sashi-like observable race states, using only features available before deadline and an OOS March gate before any Apr-Jun money evaluation.
- Production v288 remains unchanged.
- BEFORE commit for this resumed audit: `ee2313a165a048452dfc2c8881438b9b75b662b3`.
- Status: `WAVE46_COMPLETE_NO_ADOPTION_NEXT_OPPONENT_TOPOLOGY_RESEARCH_PENDING`.

## Updated exact restart point
1. Design the next opponent-topology experiment as a genuinely distinct walk-forward test, not another small rerank/threshold tweak.
2. Preserve Wave36 head selection, p3 cutoff, JPY10,000/race, and exact v288 exclusion; use pre-deadline features only.
3. Use March OOS as the first gate; only if it passes open Apr-Jun pristine evaluation. Jul/Aug remain NON-PRISTINE and September outcomes remain forbidden/unread.
4. Record BEFORE/AFTER, Run/Job/Artifact IDs, commit SHAs, exact gate/result, and adoption decision in this handoff.
