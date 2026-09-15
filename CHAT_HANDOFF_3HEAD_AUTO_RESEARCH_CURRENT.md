# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy / non-negotiables
- Active branch: `research/3head-player-attack-mode`. Latest GitHub wins over old chats/memory.
- Production remains **v288: 94R/52 hits/ROI172.560638%**. Research does not change production.
- Inputs pre-deadline only; realized 決まり手 never input. Exact v288 94-race exclusion preserved.
- Jul/Aug NON-PRISTINE. September 2026 outcomes **UNREAD** and must remain UNREAD.

## Reproducible head layer
- Wave54 March population remains **210R /71 heads =33.8095%**.

## Wave57/Wave58 REPRODUCIBILITY AUDIT — FAILED
### BEFORE commit
- `2f19697c95e36d4e0bc64726a06710ff308e4660`.

### Audit finding
- Wave57 commit `e2803294d68cb7fe5cf849651febb35595f370bf` added only `research_v289_3head_wave57_pair_interaction_result.json`; **no executable Wave57 implementation or ticket-level output was committed**.
- Wave58 commit `2eded90296f0f04f3a20fb4362adaae2de999456` likewise added only a result JSON; **no executable robustness-audit implementation was committed**.
- No new Actions run/job/artifact exists for Wave57/58; both claimed reuse of Run34754875342 / Artifact10317157868.
- The result JSON describes feature families but does not specify exact feature formulas/columns, preprocessing order, pair-label construction, GroupKFold details, logistic solver/random state/encoding, tie-breaking, ticket list, or settlement implementation.
- Independent reconstruction from the documented prose produced March **25 hits / ROI99.73%**, not the claimed **29 hits / ROI117.6349%**.
- It would be invalid to search implementation choices against March labels merely to force the historical 29-hit number.

### Canonical conclusion
- **Wave57 29/71 / ROI117.6349% is UNVERIFIED and is no longer a frozen research leader.**
- **Wave58 robustness metrics are also UNVERIFIED**, because they depend on the unreproducible Wave57 implementation and themselves have no executable audit code.
- Revoke prior status `FREEZE_WAVE57_OPPONENT_SPEC_PENDING_PRISTINE_FUTURE_VALIDATION`.
- Audit result file `research_v289_3head_wave57_reproducibility_audit.json`.
- Audit result commit `b5f892dc003af1ff6f7af9579a7eff34e4f18f87`.
- Production v288 unchanged. September outcomes remain UNREAD.

## What remains usable
- Wave54 head-population result 210R/71 remains the current reproduced head-layer research base.
- Do not use the prior monthly ROI table as canonical Wave57 performance; it came from an independent reconstruction and was explicitly not the recorded Wave57 implementation.
- Opponent layer must be rebuilt as a **fully executable deterministic implementation** with code, exact feature list/formulas, model parameters, ticket-level output and result hash committed together.

## Exact restart point
- Build a new reproducible opponent experiment from the Wave54 210R/71 base. Freeze its implementation before March settlement, preferably select using February-only grouped CV. Commit executable code + deterministic ticket output + summary in the same research step. Do not attempt to recover 29 hits by March tuning. September UNREAD; production v288 unchanged.
