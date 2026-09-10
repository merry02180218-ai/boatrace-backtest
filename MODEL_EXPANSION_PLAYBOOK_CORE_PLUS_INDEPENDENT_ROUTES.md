# Model Expansion Playbook — Fixed Core + Independent Add-On Routes

Purpose: increase race count while preserving hit rate and ROI, without weakening an already-profitable core rule.

This playbook was derived from the adopted 3-head v288 process and is intended to be reused for other head models (e.g. 4-head, 5-head) as an audit/search pattern. It is a method, not proof that the same features or thresholds will work across models.

## Core principle
Do NOT loosen the adopted high-precision core first.

Instead:
1. Freeze the existing core rule and its historical metrics.
2. Define the eligible universe from the model's existing PRE/final/purchasable chain.
3. Remove core-selected races from that universe.
4. Search an independent Route A only on the remaining races.
5. Freeze Route A before searching Route B.
6. Search Route B only on races remaining after Core + A.
7. Continue only if each incremental route adds acceptable hit rate/ROI and the combined portfolio still meets targets.

This prevents a broad loosened rule from destroying the precision of the strongest cohort.

## Required reporting
Every candidate and every combined portfolio must report:
- race count
- hit count
- hit rate
- stake
- payout
- profit
- ROI
- monthly breakdown
- train/development period separately from NON-PRISTINE periods

Never report ROI without counting losing races as full negative stake.

## Data/selection discipline
- Use the current canonical frozen artifact or reproducible upstream rebuild.
- Prediction/selection features must be available before result/payout information.
- July/August 2026 remain NON-PRISTINE for the current project.
- If July/August performance is inspected while choosing between candidates, it cannot be described as validation.
- Keep a clear distinction between development evidence and true forward evidence.
- Never overwrite an adopted model; create a new version for every threshold/feature/route/staking change.

## Route-search procedure
### Step 1 — Freeze Core
Record exact floating thresholds, not rounded display values.
Assert that the core reproduces its historical N / hits / payout / ROI before doing any expansion work.

### Step 2 — Build remainder pool
`remainder_A = eligible_universe - core`

Search only in this remainder. The core is never weakened to create more volume.

### Step 3 — Find Route A
Prefer simple, interpretable one- or two-feature rules first.
Useful feature families may include, depending on the model:
- target boat vs adjacent boat ST differential
- target boat vs inner/outer motor differential
- wall strength/weakness
- Waku10 historical frame-context features
- stretch/straight/turn/exhibition features when available at the appropriate decision stage
- opponent weakness or attack-path compatibility

Do not copy feature directions or thresholds from another head model mechanically. Refit/search them within the target model.

Route A should be evaluated both standalone and as `Core + A`.

### Step 4 — Freeze A, then find B
`remainder_B = eligible_universe - core - A`

Search Route B only on this new remainder. This is important: Route B should find a genuinely different winning cohort rather than rediscovering A.

Evaluate:
- B standalone
- Core + A + B
- month-by-month stability
- incremental profit and incremental ROI

### Step 5 — Stop when marginal quality breaks
Do not force a target race count by loosening thresholds.
Stop expansion when additional routes materially reduce combined hit rate/ROI or become too fragile/complex.

A larger model is not automatically better. Prefer the maximum race count that still satisfies the predeclared quality floor.

## Suggested objective hierarchy
For expansion work, optimize lexicographically rather than by ROI alone:
1. Meet minimum combined hit-rate floor.
2. Meet minimum combined ROI floor.
3. Maximize race count.
4. Maximize total profit.
5. Prefer simpler/more stable rules if results are close.

Example project target used in the 3-head expansion:
- combined hit rate >= 55%
- combined ROI >= 160%
- maximize race count around 100-116R

These are project-specific targets, not universal constants.

## Overfitting controls
- Prefer thresholds derived from training/development months only.
- Show later NON-PRISTINE months separately, but do not call them validation if they were visible during selection.
- Penalize very small incremental route sample sizes.
- Be suspicious of candidates that owe most profit to one payout or one month.
- Check neighboring thresholds; avoid rules that depend on accidental floating-point boundaries unless the feature grid itself is discrete and the boundary is intentionally frozen.
- If a feature has discrete values, freeze the actual semantic boundary (e.g. <= exact grid value) rather than an arbitrary interpolated quantile.

## Application to 4-head / 5-head
When applying this method to another model:
1. Identify that model's current adopted PRE/final/ticket chain from latest GitHub.
2. Reproduce its canonical historical baseline exactly.
3. Freeze its strongest current core.
4. Build the non-core eligible remainder.
5. Search independent A/B routes with features relevant to that head model's attack pattern.
6. Keep ticket construction and staking fixed during selection expansion unless staking is the explicit experiment.
7. Compare the expanded model against the original on race count, hit rate, profit and ROI.
8. Version and save both the search script and adopted specification.

## 3-head v288 reference outcome
The method produced an adopted historical 3-head portfolio of:
- Core 58R / 34 hits / 58.62% / ROI 180.75%
- Core + A 82R / 47 hits / 57.32% / ROI 176.50%
- Core + A + B 100R / 56 hits / 56.00% / ROI 174.381%

See `OFFICIAL_3HEAD_V288_100R_ADOPTED_20260911.md` for the exact 3-head rules. These numerical thresholds are NOT defaults for other models.
