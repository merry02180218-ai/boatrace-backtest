# CHAT_HANDOFF_20260914_1HEAD_CUTOFF078_ADOPT_AND_VALIDATE

Latest GitHub wins. This handoff continues `CHAT_HANDOFF_20260914_1HEAD_V337_V336_COMPARE.md`.

## PRE-WORK — written before adoption/validation
User explicitly instructed: provisionally FORMALLY ADOPT the v337 PRE head cutoff 0.78 and continue validation.

Adopted settings to freeze now:
- HEAD pipeline remains v308 logic, but production head cutoff changes from 0.8073405637 to 0.78.
- SECOND remains v317 OUTER_L2_1.
- THIRD remains v318 DROPSTART_T0.1.
- ticket policy remains v320 HYBRID alpha=.70.
- exhibition stage remains v332 ATTACK_ENV_SOFT env_w=.1 q=.65.
- Waku10 remains non-causal to this PRE path per completed audit.

Development evidence supporting provisional formal adoption (Feb-Aug only):
- cutoff .78: 276 PASS / 39.4 per month / head 241/276=87.32% / exact3 119/276=43.12%.
- newly admitted versus old anchor: +180 PASS / head 87.78% / exact3 41.11%.
- monthly head rates: Feb 86.96, Mar 90.63, Apr 85.42, May 84.38, Jun 88.68, Jul 90.48, Aug 88.57.
- September outcomes remain UNREAD.

Exact work now:
1. Locate every production/config/documentation path that still encodes the old 0.8073405637 cutoff and identify which files actually control live/production 1-head behavior versus historical regression research only.
2. Change only the production-facing cutoff/config to 0.78; do NOT rewrite historical v308/v332 research artifacts or old scripts whose purpose is reproducibility.
3. Add an explicit regression/adoption check that reports the frozen provisional production identity for Feb-Aug under cutoff .78 as 276/241/119 and keeps exhibition q=.65.
4. Run validation focused on .78 robustness: month/venue/date concentration and uncertainty using Feb-Aug only. Do not optimize a new cutoff in this work unit.
5. Keep September outcomes strictly UNREAD. If a workflow or script would read September results, stop that path and fix it before execution.
6. Append actual changed files, commit SHAs, Actions Run/Job/Artifact IDs, validation results, and exact next resume point to this handoff before reporting completion.

Production status at this exact moment: adoption requested, code/config change not yet applied.