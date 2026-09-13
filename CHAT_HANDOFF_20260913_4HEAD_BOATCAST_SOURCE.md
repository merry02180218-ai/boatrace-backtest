# CHAT HANDOFF — 2026-09-13 — 4号艇 BOATCAST original-exhibition source candidate

Updated: 2026-09-13 JST
Repository: `merry02180218-ai/boatrace-backtest`
Priority: latest GitHub > older handoffs/chat memory.
Previous handoff: `CHAT_HANDOFF_20260913_4HEAD_POST_LINEAGE.md`.

## Immutable rules

- Keep v291 race-entry logic unchanged.
- Adopted overlay remains `HEAD4_V291_COMP7_VARN_F4_N16`: original v291 Top4 composite >= 7.0, then largest N=4..16 with composite >= 4.0, exactly ¥10,000/race inverse-odds Dutch with ¥100 Hamilton rounding.
- Jul/Aug 2026 are NON-PRISTINE. Do not use outcomes for fitting/tuning/promotion.
- September 2026 remains strictly outcome-blind. Do not read results/payouts for fitting/tuning/evaluation.
- Missing/late/incomplete LIVE inputs fail closed. Never replace pre-deadline odds with closing/post-deadline odds.

## State inherited

- Current HEAD at start of this research run was `263fa3dfdc8327a7898495173493dc70f3248d93` (`Record corrected HEAD4 POST source audit CI`).
- Dedicated POST source-audit CI `34726340979` was green after the prior feature-order-only correction.
- Current-day POST builder remained incomplete because central official `beforeinfo` had proven direct coverage for only 4/7 exhibition-side inputs. `orig_straight4`, `orig_lap4`, `orig_turn4` were source-unproven and fail-closed.
- ST numeric parity, including F-start representation, also remains unproven.

## 2026-09-13 new source research — official BOATCAST

### Important result

The three previously source-unproven original-exhibition metric families are not merely historical/private concepts. BOAT RACE's own official BOATCAST documentation explicitly states that BOATCAST exposes venue-specific **original exhibition data**, described as `一周・直線・まわり足` etc.

Official BOAT RACE source checked:
- `https://www.boatrace.jp/owsp/sp/site/news/2025/07/44414/`
- Published 2025-07-21, BOATCAST communication vol.4.
- It distinguishes the common official exhibition time from venue-specific original exhibition measurements and explicitly names one-lap, straight, and turning-foot metrics.

The BOATCAST service itself is official and currently reachable through web indexing at `https://boatcast.jp/`; BOAT RACE's 2025 renewal notice also states that BOATCAST integrates race video with competition data and odds.

### Decision

**ACCEPT BOATCAST as an official pre-result SOURCE CANDIDATE for the missing original-exhibition family. DO NOT yet accept it as a production LIVE data adapter.**

Why this is important:
- It materially changes the prior source-availability conclusion: the missing 3/7 POST fields have an official publication surface candidate rather than having no known official source.
- The candidate maps semantically to the required historical `orig_straight4`, `orig_lap4`, `orig_turn4` families.
- This research did not read September results or payouts and did not use Jul/Aug outcomes.
- v291, v283, A-LIVE, variable-N selection and bankroll logic were not changed.

Why production adoption is still rejected for now:
- A stable machine-readable BOATCAST URL/API and exact race-key mapping have not yet been proven from the repository/runtime.
- The container network used during this run could not resolve `boatcast.jp`, so direct JS/network inspection there was not reliable enough to define an adapter.
- Search-index visibility is not sufficient evidence for exact numeric parity or availability timing.
- We still need to prove that the values can be acquired before cutoff, with timestamp/raw payload/hash, and match the frozen historical `original_exhibition.csv` semantics/ranking transformation exactly.
- Missing or unparsable metrics must continue to fail closed; no historical 0.5 fallback may be used to fabricate a LIVE value.

## ST F-notation status

Repository lineage review confirms historical ST ultimately enters numeric feature construction as floats, but this alone does **not** prove how an official `F` display token was normalized at acquisition time. No new conversion rule was invented. F-start handling remains fail-closed until acquisition lineage or Apr–Jun result-free fixture parity proves the exact mapping.

## Next research checkpoint

1. Resolve BOATCAST race-page/data endpoint structure from a network-capable path without touching result/payout endpoints.
2. Freeze a pre-result raw fixture with URL, retrieval timestamp and SHA256 for a race exposing original exhibition values.
3. Map raw BOATCAST labels/values to the historical `original_exhibition.csv` fields and reproduce the existing `original_scores` semantics exactly.
4. Prove Apr–Jun parity on result-free fixtures for straight/lap/turn and ST including F notation.
5. Only then extend the current-day POST builder; after complete POST parity continue ENV_ENTRY 25, A-LIVE 17, v283 SECOND 5 and conditional THIRD 20.

Current status: **important source candidate identified and recorded; production POST builder remains incomplete/fail-closed. No model or betting-policy change.**
