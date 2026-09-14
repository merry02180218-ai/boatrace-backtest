# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Active continuation branch: research/3head-player-attack-mode, forked from historical verified attack-mode pivot commit dcc012e4e81ef19636a070f221282c1b87ed262c. Do not rewrite current main.
- Fixed v288 baseline 94R /52 hits / ROI172.560638%.
- Pre-deadline features only; JPY10,000 per selected race. Jul/Aug NON-PRISTINE. September forbidden/unread.
- 3号艇 hourly research monitor was explicitly disabled by user on 2026-09-14. Do not recreate it unless user asks.

## Wave36 benchmark
- Run34780059085: Apr-Jun391R/87 hits/ROI114.913%/+583,090.
- Conditional ranking on160 actual boat3-head cases: Top5=87/160.

## Wave36S-C
- Run34786354062: Apr-Jun305R/74 hits/ROI128.218%/+860,660. RESEARCH_CANDIDATE.

## Rank replacement research
- Wave39 direct linear pair:68/160, ROI70.911%, NO_ADOPTION.
- Wave40 blend:68/160, ROI70.911%, NO_ADOPTION.
- Wave36G ordinal blend:88/160 but ROI94.187%, NO_ADOPTION.
- Wave41 ExtraTrees:71/160, ROI74.814%, NO_ADOPTION.
- Wave42 factorized second/third:79/160, ROI90.795%, NO_ADOPTION.
- Wave43 conservative boundary correction: March no-op; Apr-Jun old/new Top5 both87/160. NO_ADOPTION.

## Wave44 attack-mode route — CLOSED
- Wave44b individual prior AUC0.5765; ML AUC0.5672.
- Wave44c broad context AUC0.5420.
- Wave44d best sparse context prior_st_win12 AUC0.5895 (early0.6117 / late0.5691), below promotion AUC0.60.
- Wave44d CI Run34830607670 / Job103932793240 success at commit44955e231d3f6bab1cf3a7fd72e5536f20bd0c1e.
- Decision NO_ADOPTION_STOP_ATTACK_MODE. Apr-Jun not opened; September unread.

## BEFORE-WORK PLAN — Wave45 Wave36 ranking confidence/margin topology — 2026-09-14
User approved continuing from a genuinely different structural hypothesis after closing attack-mode.
1. Keep the frozen Wave36 conditional opponent ranker itself unchanged. Do not train another replacement ranker.
2. Audit March OOS ranking topology using only Wave36's pre-race pair probabilities: probability mass in Top5, p5-p6 boundary margin, entropy/concentration, top1/top3/top5 cumulative mass, and rank-gap shape.
3. Test a small predeclared family of confidence/margin rules whose purpose is to identify when Top5 is trustworthy versus ambiguous. Do not use actual winning pair to construct the rule; outcomes are evaluation only.
4. Primary March gate: preserve/improve Wave36 Top5 hit behavior while isolating a stable high-confidence subset or a narrowly justified ambiguous subset. Require early/late stability; reject rules that merely shrink sample opportunistically.
5. Do not open Apr-Jun until a March rule passes the predeclared structural gate. If it passes, evaluate Apr-Jun economics once using the existing exact JPY10,000 Dutch settlement and compare against Wave36 and Wave36S-C.
6. No blind Top6+ expansion: prior diagnostics showed Top6 ROI101.224%, Top7 97.775%, Top8 97.932%; expansion must be conditional on pre-race ambiguity and justified by March first.
7. v288 untouched; Jul/Aug NON-PRISTINE; September outcomes remain unread.

## Exact restart point
- Inspect the historical Wave36 script/artifact fields needed to reproduce pair-probability vectors on Feb/March without reading Apr-Jun outcomes, then implement Wave45 confidence/margin topology audit and run CI.
