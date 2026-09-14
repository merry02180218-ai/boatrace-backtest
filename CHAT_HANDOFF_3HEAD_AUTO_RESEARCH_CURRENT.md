# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline 94R /52 hits / ROI172.560638%.
- Pre-deadline features only; JPY10,000 per selected race. Jul/Aug NON-PRISTINE. September forbidden.

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

## Wave43 conservative boundary correction — COMPLETE / NO_ADOPTION
- Plan commit6657d886e6ec0b8bce57c4113fd9275530b8fa8a.
- Implementation commit475ba5fc73d04df975ade02c2f2612f370626eb0; workflow commit e89d18b8231359d6f1365034ac5b5fce43274141.
- CI Run34793612036 success; Job103822377750; artifact10328797771; SHA256 50501785b9d1b306141bb57e6e7a538a6020fbfaa476b2db9bd33515fbad50ed.
- Architecture preserved Wave36 ordering and allowed only conservative Top5-boundary promotion from ranks6-10 using score ratio; no outcome/odds feature.
- March OOS selected rank7 / ratio0.95. Crucially this made ZERO effective correction on March winners: old Top5=24/38, new=24/38, lost0, rescued0. More aggressive candidates only lost existing hits and rescued none. Therefore March supplied no evidence for a useful boundary promotion.
- Frozen Apr-Jun likewise produced no rank change: old/new Top5 both87/160; retained87, lost0, rescued0; Top1=29, Top3=61, Top8=115, Top10=125, MRR.348439, mean rank6.43125.
- Evaluation implementation reports same hit set but payout4,484,870 / ROI114.7026% / +574,870, slightly below canonical Wave36 benchmark payout4,493,090 / ROI114.913% / +583,090. Treat canonical Wave36 artifact as economic authority; the small payout mismatch is an evaluation-path parity issue, not a rank improvement. Do not use Wave43 money figure to redefine baseline.
- Monthly Wave43 rank-identical evaluation: Apr33 hits ROI174.601%; May33 hits ROI103.005%; Jun21 hits ROI70.290%. Jul-Aug NON-PRISTINE rank79 hits ROI89.888%. v288 overlap0. September forbidden/unread.
- Decision NO_ADOPTION: conservative score-ratio boundary correction found no March rescues and therefore correctly collapsed to effectively no-op.

## Current ranking conclusion
- Frozen Wave36 conditional multiclass logistic remains the strongest verified opponent ranking.
- Replacement architectures failed OOS; conservative score-ratio correction found no validated promotion rule.
- Do NOT blindly widen TopN and do NOT globally alter stake allocation.
- Important next question is not another generic classifier. We need diagnose WHY current Wave36 misses rank6-15 winners and identify a stable pre-April subgroup where a specific structural correction is supported.

## Exact restart point
1. Audit February+March only for structural patterns in Wave36 Top5 misses versus hits: especially second-place boat identity (outer4/5/6), score/rank margins, racer/motor/ST/course-relative features and pair topology.
2. Build candidate subgroup hypotheses strictly from Feb training + March OOS; require positive rescue-minus-loss on March and reasonable early/late support before any Apr-Jun opening.
3. Only then implement one targeted correction and one-shot Apr-Jun evaluation.
4. Keep v288 untouched; Jul/Aug NON-PRISTINE; September unread.
