# CHAT HANDOFF — HEAD4 LIVE TRIAL 2026-09-14

Status: IN PROGRESS

## Start record
User requested a trial on today's races (2026-09-14 JST).

Planned work:
1. Generate today's result-blind PRE inputs and frozen v291 PRE scan before reading any target-race result.
2. Identify a 4-head candidate from the PRE scan.
3. If current exhibition and a future real deadline are available, run `run_4head_full_auto_live.py` first with `--prepare-only`, then the real market/Dutch path before deadline.
4. If it is too early for exhibition/odds, stop at the exact valid PRE boundary and do not substitute post-deadline data.
5. Record exact GitHub Actions Run IDs, candidate(s), blockers, and the next restart point here before ending.

Frozen rules remain unchanged: Jul/Aug NON-PRISTINE, Sep outcome-blind for tuning, official pre-deadline 120-way odds only, exact JPY10,000 Dutch, audit before result retrieval.
