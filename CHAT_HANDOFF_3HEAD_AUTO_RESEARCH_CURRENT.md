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

## Wave44b player-specific attack mode — COMPLETE / WEAK
- CI Run34809931603 success; Job103869078993; artifact10334735981; artifact SHA256 510da759ef69fbf34cdcbe233778a726873ebdb3a3902e98754a6631f4a20641.
- Historical joined rows22074. Feb train381; March OOS445 (MAKURI241 / MAKURI-SASHI204).
- March ML AUC0.5672 / logloss0.6841 / accuracy53.933%.
- Individual 1-year prior AUC0.5765 / logloss0.6920.
- Decision MODE_SIGNAL_WEAK. Apr-Jun not opened.

## Wave44c broad contextual player attack mode — COMPLETE / NO_ADOPTION
- CI Run34815647859 success at commit 573c44bf632e75f3594d7cdba659d5e9ec4371fb.
- 69 features = player priors6 + broad static matchup63.
- Feb train381; March OOS445.
- March AUC0.5420 / logloss0.7530 / accuracy52.360%.
- Early AUC0.5467 / late AUC0.5398.
- Worse than Wave44b ML0.5672 and individual-prior0.5765. Decision MODE_SIGNAL_WEAK / NO_ADOPTION.
- Context gate failed, therefore Apr-Jun was not opened and Wave36 ranking was not modified. September outcomes unread.

## Wave44d sparse contextual player attack mode — COMPLETE / NO_ADOPTION
- Implementation commit: 05d1cc6b66eae9d96cdd0c50b0226b14f2e6e2dd.
- Circular-import fix / successful run commit: 44955e231d3f6bab1cf3a7fd72e5536f20bd0c1e.
- CI Run34830607670 success; Job103932793240.
- Feb train381; March OOS445. September outcomes unread.
- Individual 1-year prior baseline AUC0.5765.
- Sparse variants:
  - prior_st12: AUC0.5684 / logloss0.6833 / accuracy53.483% / early0.5502 / late0.5814.
  - prior_win12: AUC0.5888 / logloss0.6805 / accuracy57.528% / early0.6132 / late0.5660.
  - prior_motor12: AUC0.5575 / logloss0.6867 / accuracy51.461% / early0.5503 / late0.5632.
  - prior_st_win12: AUC0.5895 / logloss0.6800 / accuracy57.079% / early0.6117 / late0.5691.
  - prior_st_motor12: AUC0.5570 / logloss0.6863 / accuracy53.258% / early0.5346 / late0.5776.
  - prior_st_win_motor12: AUC0.5782 / logloss0.6840 / accuracy57.753% / early0.5907 / late0.5677.
- Best sparse variant: prior_st_win12, March AUC0.5895.
- Promotion target AUC>=0.60 not met. Decision NO_ADOPTION_STOP_ATTACK_MODE.
- Therefore do not open Apr-Jun for Wave44d, do not blend mode probability into Wave36 opponent ranking, and stop this attack-mode route unless a genuinely new hypothesis is introduced.
- Workflow artifact upload still points at old Wave44b filenames, so no Wave44d artifact was uploaded despite job success; authoritative metrics are in the CI log above.
- v288 production untouched; Jul/Aug remain NON-PRISTINE; September outcomes remain unread.

## Exact restart point
- Attack-mode route is closed for now. Resume 3-head research from a different structural hypothesis, while preserving Wave36/Wave36S-C benchmarks and all outcome-blind rules above.
