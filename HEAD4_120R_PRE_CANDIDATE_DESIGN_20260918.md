# HEAD4 120R — PRE candidate design — 2026-09-18

## Conclusion

A pre-exhibition candidate list **can be emitted** for the frozen 120R research rule.

The safe architecture is two-layered:

1. **Internal monitoring parent** — broad, designed not to miss final candidates.
2. **User-facing PRE shortlist** — smaller display list only; never blocks the post-exhibition scan.

The post-exhibition 120R engine must scan the full internal monitoring parent, not only the displayed shortlist.

September 2026 outcomes remain **UNREAD**. Production remains unchanged.

---

## 1. Internal monitoring parent

Pre-only inputs:

- causal motor win-rate difference, boat4 minus boat3
- race-card motor 2-ren difference, boat4 minus boat3
- causal prior player4 all-race win rate

Rule:

- `motor_win_diff_4v3 >= -0.0299361318939513`
- `motor_2ren_diff_4v3 >= -7.08`
- `player4_all_win >= 0.215605`

Explicitly excluded:

- current exhibition
- current exhibition ST
- original exhibition
- opponent_mass
- current odds
- result / payout / finishing order

Apr-Aug historical diagnostics:

- 3,743 candidates
- 153 calendar days
- average 24.46 candidates/day
- median active day 25
- p90 32
- max 42
- frozen final120 recall: **120/120 = 100%**

Official audit:

- Run `35310772723`
- Job `105492167010`
- Artifact `10533587079`
- digest `sha256:572a7b66b6d033432c33191e978d51fffd41aaae1b05dbd7b0a6e54d0bf0f27e`

This parent is too broad for the user-facing list but appropriate as the internal watch universe.

---

## 2. head_prob-only shortlist

Official detailed audit:

- Run `35310003505`
- Job `105489898968`
- Artifact `10533178842`
- digest `sha256:95ff090ac800265fb7db0145e60099d34c1cf2c96befaf83bb9b9a242ec2ff9a`

Within the monitoring parent:

### head_prob >= .10

- 2,438 candidates
- avg 15.93/day
- final120 recall 116/120 = 96.67%

### head_prob >= .14

- 1,770 candidates
- avg 11.57/day
- final120 recall 112/120 = 93.33%

A hard head_prob-only PRE gate is rejected because profitable final120 races can be omitted.

---

## 3. Existing v250 PRE score alone

Official audit:

- Run `35310957111`
- Job `105492712848`
- Artifact `10533133682`

Fixed production-style `PRE >= .28`:

- 702 candidates
- avg 4.59/day
- frozen final120 recall only 57/120 = **47.5%**

Thus v250 PRE alone is not suitable as the 120R pre-candidate parent.

A second successful run persisted all v250 PRE scores:

- Run `35311685276`
- Job `105494865314`
- Artifact `10534055421`
- digest `sha256:88451dbd23e0fbec29e074a307ddc8f042353d9c61b7199e74b09a4b7f277cd8`

---

## 4. Preferred user-facing PRE shortlist

Using the successful audited monitoring-parent data, leakage-audited race-card `head_prob`, and persisted v250 PRE score:

First require the internal monitoring parent.

Then display the race when:

- `head_prob >= 0.18`
- **OR** `v250_PRE >= 0.12`

If the race-card head probability is unavailable, keep/flag the race rather than silently dropping it.

Apr-Aug research diagnostics:

- **2,408 displayed candidates**
- avg **15.74/day**
- p90 active day: 22
- max: 38
- frozen final120 recall: **119/120 = 99.17%**
- monthly final120 recall:
  - Apr 100%
  - May 96.43%
  - Jun 100%
  - Jul 100%
  - Aug 100%

Historical final120 outcome audit:

- final120 trifecta ticket hits retained: **30/30**
- historical final120 payout retained: **100%**
- only omitted final120 race: `202605132210`
- that omitted race was a historical miss

The retained 119R has retrospective ROI 128.79%, but this is **not validation evidence** because the shortlist was selected after reviewing Apr-Aug.

---

## 5. Why the shortlist must remain display-only

An earlier 95%-recall shortlist at ~12.6/day dropped five final120 races.

Two of those five were historical winning tickets:

- `202606192105` — payout 135,600 JPY
- `202608071409` — payout 52,160 JPY

Therefore raw final120 recall is not enough. A user-facing shortlist must never be used as a hard gate for the final scanner.

Safe architecture:

```
ALL CURRENT RACES
        |
        v
PRE causal parent (~24.5/day historical)
        |
        +----> User display shortlist (~15.7/day historical)
        |
        v
post-exhibition scoring
opponent_mass + exhibition/original exhibition
        |
        v
pre-deadline live odds
        |
        v
120R final BET/PASS rule
```

A race omitted from the user-facing PRE display may still be promoted after exhibition because the internal monitoring parent continues to track it.

---

## 6. Leakage / timing discipline

PRE layer does not use:

- same-race results
- payouts
- current exhibition
- final/closing odds

Unified 120R leakage audit already passed:

- Run `35306188702`
- Job `105478741668`
- Artifact `10531229990`
- outcome leakage: PASS
- temporal leakage: PASS
- closing-odds timing: WARN / retrospective proxy
- Apr-Aug selection: NON-PRISTINE
- September: UNREAD

Race-card head-probability leakage audit:

- Run `35234326600`
- Job `105246227265`
- Jul-Aug AUC 0.727090
- shuffled-target AUC mean 0.503484
- source code unchanged from the audit run

---

## 7. Live implementation requirement

Before formal deployment:

1. freeze the race-card `head_prob` model state;
2. use the existing frozen/live v250 PRE semantics;
3. compute the causal motor/player monitoring parent before exhibition;
4. display the dual-score shortlist;
5. continue monitoring the full parent after exhibition;
6. use immutable timestamped pre-deadline odds at the final stage;
7. never tune from September outcomes before the future checkpoint.

Research policy artifact:

`artifacts/head4_120r_pre_display_policy_20260918.json`

## Status

`HEAD4_120R_PRE_CANDIDATE_DESIGN_READY__DISPLAY_NOT_HARD_GATE`

- September results: **UNREAD**
- Production: **unchanged**
