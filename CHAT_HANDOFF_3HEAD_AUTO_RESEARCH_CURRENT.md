# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Active branch: research/3head-player-attack-mode. Do not rewrite main.
- v288 baseline fixed: 94R / 52 hits / ROI172.560638%.
- Pre-deadline only. Jul/Aug NON-PRISTINE. September unread.
- Hourly 3-head monitor remains disabled unless user asks.

## Benchmarks
- Wave36: Apr-Jun 391R / 87 hits / ROI114.913% / +583,090 yen.
- Wave36S-C: Apr-Jun 305R / 74 hits / ROI128.218% / +860,660 yen. RESEARCH_CANDIDATE.

## Closed research
- Wave39/40/41/42/43 rank replacements: NO_ADOPTION.
- Wave44 attack-mode route: best March AUC0.5895, below 0.60 gate. CLOSED.
- Wave45 confidence/margin: zero lift. NO_ADOPTION.
- Wave46 second/third role factorization: March 16/90 role, 21/90 blend vs Wave36 24/90. NO_ADOPTION.

## Wave47 head-condition zoning — COMPLETE / NO_ADOPTION
- March plan commit 3fc1f8b8bb3e1e42a50db2a8308c1f11e73b4a8d; implementation 55588d48e5ce5bd2e4fc1536e98d63a19ef6cec3.
- March CI Run34843925397 / Job103975145924 success; artifact10347171131; SHA256 7595ce0c4bc51a4788fac272a27c8335b7503244a5854f69c4e23683f404459b.
- March baseline:90R /38 head hits /42.222%; Top5 24 /26.667%.
- March winner: motor family top60% =>54R / head48.148% (+5.926pt), early46.875%, late50.000%. Gate passed.
- Apr-Jun single pristine opening used the frozen March-selected structure with no retuning.
- Holdout runner commit6617b10240a64815f2bcc5c77aa2064eadbe1922; trigger commit a00a1ec323906d9bf535996eec50550019801ed6.
- Holdout CI Run34844221809 / Job103976135822 success.
- Wave36 recomputed exactly:391R /87 hits / ROI114.913% / +583,090 yen.
- Wave47 holdout:174R /36 hits / ROI95.511% / -78,100 yen; min month53.623%; red months1; maxDD336,140 yen.
- Monthly Wave47: Apr49R/12 hits/ROI111.384%/+55,780; May63R/15/124.390%/+153,660; Jun62R/9/53.623%/-287,540.
- Decision NO_ADOPTION. Do not retune Wave47 on Apr-Jun after this failure.
- Wave47 March audit entrypoint restored at commit496688106d20b65fce5531f4a27700767ea3e97d.
- v288 untouched. Jul/Aug remain NON-PRISTINE. September outcomes unread.

## Exact restart point
- Wave47 is closed. Preserve Wave36 and Wave36S-C benchmarks. Next research must use a new structural hypothesis and must avoid reusing Apr-Jun outcomes for retuning Wave47.
