# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy / non-negotiables
- Active branch: `research/3head-player-attack-mode`. Latest GitHub wins over old chats/memory.
- Production remains **v288: 94R/52 hits/ROI172.560638%**. Research does not change production.
- Inputs pre-deadline only; realized 決まり手 never input. Exact v288 94-race exclusion preserved.
- Jul/Aug NON-PRISTINE. September 2026 outcomes **UNREAD** and must remain UNREAD.

## Reproducible head layer
- Wave54 March population independently reproduced again: **210R/71 heads=33.8095%**.
- Exact March eligible universe reproduced: **4,482R**; February eligible: **3,970R /478 boat3 heads**.

## Wave57/Wave58 audit
- Historical Wave57 29/71/ROI117.6349% and Wave58 robustness metrics remain **UNVERIFIED**.
- Audit commit `b5f892dc003af1ff6f7af9579a7eff34e4f18f87`.

## Reproducible opponent rebuild v1 — completed
### BEFORE commit
- `93009885fced10aee154a1b87921d26011527d32`.

### Deterministic implementation
- February training: 478 boat3-head races, **9,560 ordered-pair rows**.
- 67 explicit ordered-pair features: second/third lane one-hot; each candidate's national ST/win/2/3, local win/2, motor2/3, boat2; candidate-vs-boat3 gaps; second-minus-third gaps; pair means; inner/outer structure indicators.
- Pipeline: median imputation -> StandardScaler -> LogisticRegression(C=1.0, class_weight=balanced, solver=liblinear, max_iter=2000, random_state=0).
- Exactly 3 tickets/R. Deterministic tie-break: score descending, second lane ascending, third lane ascending.
- Executable code: `research/rebuild_3head_opponent_v1.py`, commit `a20b5da985299d0b445110e6783dcaebf0f76a02`.

### March diagnostic
- Frozen Wave54: **210R /71 boat3 heads**.
- 3-ticket hits: **25/71 =35.2113% head capture**.
- Stake ¥63,000 -> return **¥62,830** -> **ROI99.7302%**.
- Summary commit `278c60feb707b29417b4ab4a306fa126f888fca4`.
- Hit-level audit commit `3d42f2c3fe8177305908cf799548d0852da3adf8`.

### Reproducibility audit
- Full 210-race ticket output generated twice independently with the same executable implementation.
- Both runs produced identical SHA256: **6d35377b76be2b403fd7ccaa466374666452d3404cd0fae2752f640396b35897**.
- Local audited script SHA256: `e8113a0b176f4988e33d633aa2a290d73fd877a5d4a00fd79ce50945ea55c079`.
- Therefore v1 is the first new opponent baseline after the Wave57 audit that is deterministic and independently rerunnable.

### Conclusion
- Do NOT restore the old Wave57 29-hit claim. The honest reproducible baseline is currently **25 hits / ROI99.73%**.
- This v1 is deliberately a reproducibility baseline, not March-optimized.
- Next research should improve opponent ranking using **February-only grouped CV**, with all candidate specifications frozen before March settlement. Every successor must retain executable code + deterministic output hashes.
- No new Actions Run/Job/Artifact; fixed source Run34754875342 / Artifact10317157868 reused.
- September outcomes remain UNREAD; production v288 unchanged.

## Exact restart point
- Start reproducible opponent v2 research using February-only grouped CV. Compare candidate feature/model families without March labels; freeze the best February-CV specification first, then run one March diagnostic. Preserve v1 as immutable benchmark: 25 hits, ¥62,830 return, ROI99.7302%, ticket hash `6d35377b...`.
