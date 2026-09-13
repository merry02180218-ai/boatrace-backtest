# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch: `research/3head-v289-addon-expansion`; newest GitHub state wins.
- Legacy v288 stays unchanged: 94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%.
- Current research source is no longer limited to v243 678R or 584R. Use all available six-boat races from 2026-02-01 through 2026-08-31 from BoatraceCSV race_cards.
- Jul/Aug NON-PRISTINE. September outcomes forbidden.
- Features must be pre-deadline. Results/payouts are evaluation-only. Missing required current inputs fail closed.
- Add-on overlap with v288 must be zero. Stake JPY10,000/race.

## Prior state
- Wave18b Run `34749443471`: 678/678 official settlements and exact-order results recovered.
- Wave19a Run `34749575986`: 678/678 payouts recovered; 3-head all-20 equal stake benchmark ROI 70.929941%.
- Wave19b Run `34749707037` failed with `RuntimeError: missing payout`. This 584R branch is superseded by Wave20; keep only as audit history.

## Wave20 — FINAL
- Script: `research_v289_3head_wave20_allrace_universe.py`; commit `7b45397f47eeb08c3558268b5288db6768c104cb`.
- Workflow commit: `33c296c008a7a588e9f694feb577a3612b4731d7`.
- Run `34749917116`: success.
- Artifact `3head-wave20-allrace-universe`, ID `10314839371`.
- Full available six-boat universe: **32,111R**.
- Monthly: Feb 4100 / Mar 4607 / Apr 4244 / May 4832 / Jun 4488 / Jul 4920 / Aug 4920.
- Missing race_cards date: 2026-06-17 only.
- Decision: `ALLRACE_UNIVERSE_READY`.

## Exact restart point
1. Use Wave20 artifact CSV as the 32,111R base.
2. Join complete pre-deadline race_cards plus waku10 fields.
3. After feature freeze, attach realtime exact order plus official trifecta combo and payout for settlement only.
4. Audit coverage, date range, and result/payout combo agreement; fail closed on insufficient coverage.
5. Then run full-population 3-head walk-forward research. Exclude the legacy 94R only when checking add-on overlap, not as an initial candidate-universe restriction.
6. Report R, hits, stake, payout, ROI, profit, monthly, min-month ROI, red months, max DD, overlap, and combined baseline+addon.
7. If a run fails or a wave ends without the next wave, fix/restart automatically and update this file.
