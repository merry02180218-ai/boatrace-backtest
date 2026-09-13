# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch: `research/3head-v289-addon-expansion`; newest GitHub state wins.
- Legacy v288 stays unchanged: 94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%.
- Current research source is no longer limited to v243 678R or 584R. Use all available six-boat races from 2026-02-01 through 2026-08-31 from BoatraceCSV race_cards.
- Jul/Aug NON-PRISTINE. September outcomes forbidden.
- Features must be pre-deadline. Results/payouts are evaluation-only. Historical closing trifecta odds are staking/post-hoc ROI only and must not be prediction features.
- Missing required current inputs fail closed. Add-on overlap with v288 must be zero. Stake JPY10,000/race.

## Prior state
- Wave18b Run `34749443471`: 678/678 official settlements and exact-order results recovered.
- Wave19a Run `34749575986`: 678/678 payouts recovered; 3-head all-20 equal stake benchmark ROI 70.929941%.
- Wave19b Run `34749707037` failed with `RuntimeError: missing payout`; superseded by Wave20.

## Wave20 — FINAL
- Run `34749917116`: success.
- Artifact `3head-wave20-allrace-universe`, ID `10314839371`.
- Full available six-boat universe: **32,111R**.
- Monthly: Feb 4100 / Mar 4607 / Apr 4244 / May 4832 / Jun 4488 / Jul 4920 / Aug 4920.
- Missing race_cards date: 2026-06-17 only.
- Decision: `ALLRACE_UNIVERSE_READY`.

## Wave21 — FINAL source audit
- Successful recovery Run `34751314113`, head `10fabebaa444fdb6730b16287fe95051a6f3942b`.
- Artifact `3head-wave21-allrace-source-build`, ID `10316605199`.
- rows 32,111; feature columns 786; retry days 13.
- result coverage 31,472/32,111 = 98.010%.
- payout coverage 31,553/32,111 = 98.262%.
- usable exact settlement 31,518/32,111 = 98.153%.
- agreement when both exact sources exist 31,300/31,314 = 99.9553%; true mismatches 14.
- actual 3-head wins in usable rows 4,040.
- Decision: `ALLRACE_SETTLED_SOURCE_READY`.

## Wave22 — historical closing trifecta odds — RUNNING
- Historical source implementation reused from v102: Kyotei24 Odds Bank pages explicitly labelled `締切時オッズ`, parsing all 120 trifecta odds per race.
- New script: `research_v289_3head_wave22_closing_trifecta_odds.py`, commit `2f8f8f377204ff4feb424303c7dfc8d4827bfe21`.
- Wave22 is chained after Wave21 in `research_v289_3head_wave21_allrace_source_build.py`, commit `195e14da883d291b633dbe4deaf0bd5a57298cd5`.
- Current Run: **`34752573368`**, workflow `research-3head-wave21-allrace-source-build`, head `195e14da883d291b633dbe4deaf0bd5a57298cd5`.
- Latest state: **in_progress**; Python source-build step is running. It will rebuild Wave21, then execute Wave22 and merge closing odds into the all-race source.
- Target: audit odds available rows, full-120 rows, coverage share, then use closing odds only for JPY10,000 Dutch staking and realized ROI evaluation.

## Exact restart point
1. Inspect Run `34752573368` first.
2. If success, inspect Wave22 figures from job log/artifact: odds available, full 120 odds coverage, failures by date/venue/source reason.
3. If Wave22 coverage is acceptable, immediately launch full-population temporal/walk-forward 3-head research using only pre-deadline features; use closing odds only after selection for Dutch allocation/evaluation.
4. If Wave22 fails, inspect logs, fix parser/source/retry issues without weakening no-leakage/date guards, rerun automatically.
5. For candidate research report R, hits, stake, payout, ROI, profit, monthly, min-month ROI, red months, max DD, overlap, combined baseline+addon.
6. Jul/Aug remain NON-PRISTINE; September outcomes forbidden; legacy v288 94R is baseline/floor; add-on overlap zero.
