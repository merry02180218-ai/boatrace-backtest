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

## BEFORE-WORK PLAN — Wave44d sparse contextual player attack mode — 2026-09-14
User approved the next direction after Wave44c failure.
1. Use leakage-safe individual racer tendency (1-year prior AUC0.5765) as the anchor; do not throw all 63 matchup features into one model.
2. Audit Wave21 exact safe columns and construct a deliberately small context set centered on race mechanics: boat3 vs boat1/2 average-ST gaps, boat1/2 wall strength proxies, boat3 vs boat1/2 national/local win-rate gaps, and boat3 vs boat1/2 motor performance gaps. Avoid outer-boat/global noise unless separately justified.
3. Test sparse additions conservatively on Feb train -> March OOS only. Report individual-prior baseline plus each small feature-family/addition, March AUC/logloss/accuracy and early/late stability. Do not tune on Apr-Jun.
4. Promotion target remains March AUC >=0.60, preferably >=0.62, with both halves stable. If no sparse variant beats the 0.5765 individual-prior baseline materially, stop this attack-mode route rather than opening Apr-Jun.
5. Only if the mode gate passes, softly blend mode probability into frozen Wave36 opponent ranking and apply the existing March ranking promotion gate before any Apr-Jun economics.
6. v288 untouched; Jul/Aug NON-PRISTINE; September outcomes remain unread.

## Exact restart point
- Implement Wave44d sparse contextual audit on research/3head-player-attack-mode using the existing Wave21 artifact and Wave44b prior-history construction, then run CI and compare March OOS variants.
