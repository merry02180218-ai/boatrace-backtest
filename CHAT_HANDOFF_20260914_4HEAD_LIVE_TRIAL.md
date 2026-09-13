# CHAT HANDOFF — HEAD4 LIVE TRIAL 2026-09-14

Status: PRE TRIAL COMPLETE; WAITING FOR EXHIBITION WINDOW

## Start record
User requested a trial on today's races (2026-09-14 JST).

Planned work:
1. Generate today's result-blind PRE inputs and frozen v291 PRE scan before reading any target-race result.
2. Identify a 4-head candidate from the PRE scan.
3. If current exhibition and a future real deadline are available, run `run_4head_full_auto_live.py` first with `--prepare-only`, then the real market/Dutch path before deadline.
4. If it is too early for exhibition/odds, stop at the exact valid PRE boundary and do not substitute post-deadline data.
5. Record exact GitHub Actions Run IDs, candidate(s), blockers, and the next restart point here before ending.

Frozen rules remain unchanged: Jul/Aug NON-PRISTINE, Sep outcome-blind for tuning, official pre-deadline 120-way odds only, exact JPY10,000 Dutch, audit before result retrieval.

## Completion / progress record

### PRE workflow
- Trigger commit: `9e4e6fe523c28e79aca4d147413a5f8ee68d3c12`
- GitHub Actions Run: `34768882968`
- Result: **SUCCESS**
- Result-blind current PRE inputs: **SUCCESS**
- Frozen v291 PRE scan: **SUCCESS**
- Artifact: `live-4head-v291-pre-6` (artifact id `10321775792`)
- Current race rows: 168
- Active venues: 02,04,06,07,08,09,10,11,12,18,19,20,21,22
- S PRE cutoff = 0.28
- S PRE eligible rows = **0**

### Highest PRE rows
1. `202609142204` = JCD22 福岡 4R, PRE **0.238086**
2. `202609141204` = JCD12 4R, PRE **0.158916**
3. `202609140904` = JCD09 4R, PRE **0.116247**
4. `202609140611` = JCD06 11R, PRE **0.089786**
5. `202609142202` = JCD22 福岡 2R, PRE **0.088329**

### Trial target
`202609142204` / 福岡4R is the only current row above the frozen outside-S A PRE floor 0.18.
- PRE = **0.238086**
- S candidate: **NO** (below 0.28)
- Potential outside-S A continuation: **YES**, subject to POST >= 0.18 and frozen `A_SCORE_LIVE >= 0.2710428764008591` after exhibition.
- 4号艇: 4614 石倉洋行 A1; national avg ST 0.13; national win rate 7.18; motor 2-ren 26.62%.
- Other boats: 1=5395 日高龍之介 B1, 2=5125 高井雄基 A2, 3=4553 坪口竜也 A2, 5=5418 堀内亜海 B2, 6=3863 海老澤泰行 B1.

### Why the full market trial was not run yet
At the execution time (~01:30 JST), current exhibition/start-display/current weather/official pre-deadline odds for 福岡4R were not yet published. Therefore the production contract requires stopping at PRE. No post-deadline or synthetic odds were substituted.

### Exact restart point
When 福岡4R exhibition is published and the real deadline is still in the future:
1. run `run_4head_full_auto_live.py` for `20260914 / JCD22 / R4` with `--prepare-only`;
2. check POST, ENV_ENTRY and A/S classification;
3. if classification permits a bet, rerun without `--prepare-only` using the real `--deadline-jst`;
4. verify official 120-way odds completeness, VARN N, exact JPY10,000 Dutch allocation, and audit persistence before reading the result;
5. append final live market outcome here.
