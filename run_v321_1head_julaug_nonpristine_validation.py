#!/usr/bin/env python3
"""v321: July/August 2026 NON-PRISTINE reference validation for the frozen 1-head stack.

This is intentionally NOT pristine validation and must not be used for model promotion.
Head selection is frozen from v308: absolute p_head cutoff derived only from the original
Feb-Jun development predictions at q=.98, plus opponent_mass >= .375.
Opponent ranking is frozen to v317 SECOND + v318 DROP_START THIRD and the v320 winning
3-ticket policy HYBRID alpha=.70. No tuning is performed on Jul/Aug.
September outcomes remain unread. meet_* is forbidden. Month M trains only on < M.
"""
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v303_1head_headmodel_transfer_ablation as v303
import run_v305_1head_leakage_audit as v305
import run_v307_1head_causal_turn_form as v307
import run_v310_1head_opponent_headrisk_second as v310
import run_v311_1head_opponent_second_family_autoresearch as v311
import run_v312_1head_opponent_outer_gate as v312
import run_v317_1head_opponent_error_features as v317
import run_v318_1head_opponent_third_rebuild as v318
import run_v299_1head_trifecta3_policy_search as v299

ROOT=Path(__file__).resolve().parent
DEV_PRED=ROOT/'analysis_v308_1head_volume_opponent_joint_pred.csv'
P=ROOT/'analysis_v321_1head_julaug_nonpristine_validation'
S=ROOT/'summary_v321_1head_julaug_nonpristine_validation.md'
TARGET_MONTHS=['2026-07','2026-08']
Q=.98
OPP_MASS_CUT=.375
POLICY='HYBRID'
ALPHA=.70


def build_head_selection():
    # Absolute cutoff comes only from the original Feb-Jun development prediction file.
    dev=pd.read_csv(DEV_PRED,dtype={'race_code':str})
    if any(str(m).startswith(('2026-07','2026-08','2026-09')) for m in dev['test_month'].astype(str).unique()):
        raise RuntimeError('v321 DEV_PRED unexpectedly contains Jul/Aug/Sep')
    hcut=float(pd.to_numeric(dev.p_head,errors='coerce').quantile(Q))

    # v294 is deliberately capped at Jun for pristine development. v321 is an explicit
    # NON-PRISTINE stress check, so extend only the source horizon to Aug while retaining
    # the same causal construction. Never extend into September.
    v300.setup_v298()
    old_end=v298.v294.END
    try:
        v298.v294.END=date(2026,8,31)
        d,_=v298.v294.freeze_true_pre()
    finally:
        v298.v294.END=old_end
    d=v298.v294.add_prior_history(d); d=v298.v294.add_rel(d)
    d,th=v298.add_threat(d); fam=v298.v296.clean_manifest(d); d,tf=v303.add_transfer_features(d); d,ca=v307.add_causal(d)
    safe=list(dict.fromkeys(v305.safe_transfer(tf['TURN_FORM'])+v305.safe_transfer(tf['STMOTOR'])+ca))
    if any('meet_' in str(c).lower() for c in safe): raise RuntimeError('v321 unsafe head feature')
    d,_=v298.v297.settle_full_after_freeze(d); d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    if any(str(m).startswith('2026-09') for m in d.month.astype(str).unique()):
        raise RuntimeError('v321 extended universe unexpectedly contains September')
    masses=v303.opponent_mass(d)
    core=list(dict.fromkeys(fam['CLEAN_STATIC6_PLAYER']+th))
    guard=[c for c in core if c.startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]
    out=[]
    for tm in TARGET_MONTHS:
        tr=d[d.month<tm].copy(); te=d[d.month==tm].copy()
        if te.empty: raise RuntimeError(f'v321 no source rows for {tm}')
        bc=v298.v293.available(tr,core,.55); bg=v298.v293.available(tr,guard,.55); ex=v303.available(tr,safe)
        ph,_,_,_,_,_=v298.head_fold(tr,te,list(dict.fromkeys(bc+ex)),bg)
        z=te[['date','month','race_code','venue','race','head_hit','actual_combo']].copy()
        z['race_code']=z.race_code.astype(str).str.zfill(12); z['p_head']=ph
        z['opp_mass']=[masses.get(str(x).zfill(12),np.nan) for x in z.race_code]
        z['selected']=((z.p_head>=hcut)&(z.opp_mass>=OPP_MASS_CUT)).astype(int)
        out.append(z)
    return pd.concat(out,ignore_index=True),hcut,d


def build_opponent_probs(d):
    # Reuse the audited v313 p3/p4 maps. They intentionally end with the development
    # horizon, so Jul/Aug receive explicit unavailable=0 flags via add_headrisk; there is
    # no future backfill. The PRE/prior table itself is extended causally above because
    # the committed v313 table is intentionally capped at Jun.
    _,p3,p4=v312.load_cache()
    d=d.copy(); d.race_code=d.race_code.astype(str).str.zfill(12)
    drop=[c for c in d.columns if 'meet_' in str(c)]
    if drop: d=d.drop(columns=drop)
    if any('meet_' in str(c) for c in d.columns): raise RuntimeError('v321 meet_* present after drop')
    have=set(d.month.astype(str).unique())
    missing=[m for m in TARGET_MONTHS if m not in have]
    if missing: raise RuntimeError(f'v321 extended PRE missing target months {missing}')
    v300.setup_v298(); sufs=v298.suffixes(d)
    if any('meet_' in str(x) for x in sufs): raise RuntimeError('v321 forbidden meet suffix')
    sl=v310.add_headrisk(v300.augment_second(v298.second_long(d,sufs)),p3,p4)
    sx,_=v317.add_engineered(sl,'OUTER')
    cl=v300.augment_third(v298.conditional_long(d,sufs))
    p2={}; pc={}
    for tm in TARGET_MONTHS:
        p2[tm]=v311.p2_predict_explicit(sx,tm,1.0,None,{'START'})[0]
        pc[tm]=v318.pc_predict(cl,tm,.1,'DROP_START')[0]
    return d,p2,pc


def main():
    head,hcut,d=build_head_selection()
    d,p2,pc=build_opponent_probs(d)
    selected=head[head.selected==1].copy()
    if selected.empty: raise RuntimeError('v321 no Jul/Aug selected races')
    missing=sorted(set(selected.race_code)-set(d.race_code))
    if missing: raise RuntimeError(f'v321 selected races absent from extended PRE n={len(missing)} sample={missing[:5]}')
    rows=[]; fn=v299.STRATEGIES[POLICY]
    for _,r in selected.iterrows():
        tm=str(r.month); code=str(r.race_code).zfill(12)
        probs=v299.pair_prob(p2[tm][code],pc[tm][code],ALPHA)
        order=fn(p2[tm][code],pc[tm][code],probs); top3=order[:3]
        if len(top3)!=3 or len(set(top3))!=3: raise RuntimeError(f'v321 invalid ticket set {code}')
        tickets=[f'1-{s}-{t}' for s,t in top3]
        actual=str(r.actual_combo)
        rows.append({'month':tm,'race_code':code,'head_hit':int(r.head_hit),'actual_combo':actual,
                     'p_head':float(r.p_head),'opp_mass':float(r.opp_mass),'tickets':';'.join(tickets),
                     'hit':int(actual in tickets)})
    z=pd.DataFrame(rows)
    gm=z.groupby('month').agg(R=('race_code','size'),head_hits=('head_hit','sum'),hits=('hit','sum')).reset_index()
    gm['head_rate']=gm.head_hits/gm.R; gm['hit_rate']=gm.hits/gm.R
    overall={'R':len(z),'head_hits':int(z.head_hit.sum()),'hits':int(z.hit.sum())}
    z.to_csv(str(P)+'_race.csv',index=False); gm.to_csv(str(P)+'_monthly.csv',index=False)
    L=['# v321 Jul/Aug 2026 NON-PRISTINE validation','',
       '- **Reference only; NOT pristine and NOT eligible for promotion.**',
       f'- v308 head selection frozen using development-only absolute q=.98 cutoff **p_head>={hcut:.8f}** and opponent mass >= {OPP_MASS_CUT:.3f}.',
       '- Opponent ranking frozen to v317 SECOND + v318 DROP_START THIRD.',
       f'- Ticket policy frozen to v320 winner **{POLICY} alpha={ALPHA:.2f}**, exactly 3 tickets per selected race.',
       '- Month M trains only on months < M; `meet_*` forbidden; missing p3/p4 are explicit unavailable/neutral and never future-backfilled; September outcomes untouched.','',
       '## Result',f"- Jul+Aug: R **{overall['R']}**, head **{overall['head_hits']}/{overall['R']}={100*overall['head_hits']/overall['R']:.2f}%**, exact3 **{overall['hits']}/{overall['R']}={100*overall['hits']/overall['R']:.2f}%**.",'',
       '## Monthly','|month|R|head|head rate|exact3|exact3 rate|','|---|---:|---:|---:|---:|---:|']
    for _,r in gm.iterrows(): L.append(f"|{r.month}|{int(r.R)}|{int(r.head_hits)}|{100*r.head_rate:.2f}%|{int(r.hits)}|{100*r.hit_rate:.2f}%|")
    L += ['','## Interpretation','- Compare only as a contamination-aware stress check against Feb-Jun development behavior.','- Do not call this holdout/pristine validation and do not tune thresholds, features, alpha, or strategy from these results.']
    S.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(S.read_text(),flush=True)

if __name__=='__main__': main()
