#!/usr/bin/env python3
"""v299: improve v298's 3-ticket exact-order ranking on the identical selected races.

Development-only. Jul/Aug remain excluded upstream and September outcomes are unread.
The v298 head gate and baseline confidence gate are frozen: HGB q0.95 and baseline
(alpha=.60 TOP2XTOP2) top5 mass >= .45. Policy search only changes the ordering of the
three exact-order tickets on that same race set, so gains cannot come from shrinking
the denominator.
"""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
import pandas as pd

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v297_1head_guard_trifecta5_research as settlement
import run_v298_1head_v288v283_audited as fastbase
import run_v298_1head_v288v283_audited_v2 as v2

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'analysis_v299_1head_trifecta3_policy_search'
SUMMARY=ROOT/'summary_v299_1head_trifecta3_policy_search.md'
BOATS=v298.BOATS
TEST_MONTHS=list(v298.TEST_MONTHS)
ALPHAS=(.20,.30,.40,.50,.60,.70,.80)
BASE_ALPHA=.60
BASE_CONF=.45


def pair_prob(p2,pc,alpha):
    raw={}
    for s in BOATS:
        for t in BOATS:
            if s==t:continue
            sc=alpha*math.log(max(p2[s],1e-12))+(1-alpha)*math.log(max(pc[(s,t)],1e-12))
            raw[(s,t)]=math.exp(sc)
    den=sum(raw.values())
    return {k:v/den for k,v in raw.items()}


def joint_order(prob):
    return sorted(prob,key=lambda x:(-prob[x],x[0],x[1]))


def top2x2_order(p2,pc,prob):
    ordinary=joint_order(prob)
    sr=sorted(BOATS,key=lambda s:(-p2[s],s));s1,s2=sr[:2]
    cr={s:sorted([t for t in BOATS if t!=s],key=lambda t:(-pc[(s,t)],t)) for s in BOATS}
    pool=[(s,cr[s][k]) for k in (0,1) for s in (s1,s2)]
    rank={x:ordinary.index(x) for x in pool};pre=sorted(pool,key=lambda x:rank[x])
    out=[]
    for x in pre+ordinary:
        if x not in out:out.append(x)
    return out


def second1x3_order(p2,pc,prob):
    s=max(BOATS,key=lambda b:(p2[b],-b))
    thirds=sorted([t for t in BOATS if t!=s],key=lambda t:(-pc[(s,t)],t))
    pre=[(s,t) for t in thirds[:3]];out=[]
    for x in pre+joint_order(prob):
        if x not in out:out.append(x)
    return out


def second3x1_order(p2,pc,prob):
    seconds=sorted(BOATS,key=lambda s:(-p2[s],s))[:3]
    pre=[]
    for s in seconds:
        t=max([x for x in BOATS if x!=s],key=lambda x:(pc[(s,x)],-x))
        pre.append((s,t))
    pre=sorted(pre,key=lambda x:(-prob[x],x[0],x[1]));out=[]
    for x in pre+joint_order(prob):
        if x not in out:out.append(x)
    return out


def hybrid_order(p2,pc,prob):
    ordinary=joint_order(prob);first=ordinary[0];s=first[0]
    same=[x for x in ordinary if x[0]==s and x!=first]
    other=[x for x in ordinary if x[0]!=s]
    pre=[first]
    if same:pre.append(same[0])
    if other:pre.append(other[0])
    out=[]
    for x in pre+ordinary:
        if x not in out:out.append(x)
    return out


STRATEGIES={
    'TOP2XTOP2':top2x2_order,
    'JOINT':lambda p2,pc,prob:joint_order(prob),
    'SECOND1X3':second1x3_order,
    'SECOND3X1':second3x1_order,
    'HYBRID':hybrid_order,
}


def setup_v298():
    v298.add_threat_original=v298.add_threat
    fastbase.cand_record_original=fastbase.cand_record
    fastbase._cand_record_original=fastbase.cand_record
    fastbase.curated_suffixes=v2.curated_suffixes
    fastbase.cand_record=v2.cand_record
    v298.add_threat=fastbase.add_threat
    v298.suffixes=v2.curated_suffixes
    v298.cand_record=v2.cand_record
    v298.second_long=v2.second_long_all
    v298.conditional_long=v2.conditional_long_all
    v298.v279.ListwiseSoftmax=fastbase.FastSecond
    v298.v282.ListwiseN=fastbase.FastConditional
    settlement.AUDIT.clear()
    v298.v297.settle_full_after_freeze=settlement.settle_union_after_freeze


def run(d,fams,threat):
    sufs=v298.suffixes(d);sl=v298.second_long(d,sufs);cl=v298.conditional_long(d,sufs)
    core0=list(dict.fromkeys(fams['CLEAN_STATIC6_PLAYER']+threat))
    guard0=[c for c in core0 if c.startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]
    pred=[];folds=[]
    for tm in TEST_MONTHS:
        tr=d[d.month<tm].copy();te=d[d.month==tm].copy()
        core=v298.v293.available(tr,core0,.55);guard=v298.v293.available(tr,guard0,.55)
        ph,pg,hc,gc,noh,nog=v298.head_fold(tr,te,core,guard)
        p2,nf2,nr2=v298.p2_fit_predict(sl,tm);pc,nf3,nr3=v298.pc_fit_predict(cl,tm)
        z=te[['date','month','race_code','venue','race','head_hit','actual_combo','combo_valid']].copy()
        z['test_month']=tm;z['p_head_hgb']=ph;z['p_safe_lr']=pg
        for q,c in hc.items():z[f'hgb_q{q}_cut']=c;z[f'hgb_q{q}_sel']=(ph>=c).astype(int)
        base_top5=[];base_mass=[]
        policy_tickets={f'{name}_a{int(round(a*100)):02d}':[] for name in STRATEGIES for a in ALPHAS}
        for _,r in z.iterrows():
            code=str(r.race_code).zfill(12)
            probs0=pair_prob(p2[code],pc[code],BASE_ALPHA)
            o0=top2x2_order(p2[code],pc[code],probs0)
            base_top5.append(';'.join(f'1-{s}-{t}' for s,t in o0[:5]))
            base_mass.append(sum(probs0[x] for x in o0[:5]))
            for a in ALPHAS:
                pr=pair_prob(p2[code],pc[code],a)
                for name,fn in STRATEGIES.items():
                    order=fn(p2[code],pc[code],pr)
                    policy_tickets[f'{name}_a{int(round(a*100)):02d}'].append(';'.join(f'1-{s}-{t}' for s,t in order[:3]))
        z['base_top5']=base_top5;z['base_top5_mass']=base_mass
        z['base_selected']=((z['hgb_q0.95_sel']==1)&(z.base_top5_mass>=BASE_CONF)).astype(int)
        for key,vals in policy_tickets.items():
            z[f'top3_{key}']=vals
            z[f'hit3_{key}']=[int(bool(a) and a in t.split(';')) for a,t in zip(z.actual_combo,vals)]
        pred.append(z)
        folds.append({'month':tm,'train':len(tr),'test':len(te),'head_features':len(core),'guard_features':len(guard),
                      'second_features':nf2,'third_features':nf3,'second_train_races':nr2,'third_train_races':nr3,
                      'head_oof':noh,'guard_oof':nog})
        print('fold',tm,'done',len(te),flush=True)
    return pd.concat(pred,ignore_index=True),pd.DataFrame(folds)


def summarize(p):
    s=p[p.base_selected==1].copy();rows=[];monthly=[]
    for a in ALPHAS:
        for name in STRATEGIES:
            key=f'{name}_a{int(round(a*100)):02d}';col=f'hit3_{key}'
            gm=s.groupby('test_month')[col].agg(['size','sum','mean'])
            rows.append({'strategy':name,'alpha':a,'R':len(s),'hits':int(s[col].sum()),'hit_rate':float(s[col].mean()),
                         'worst_month':float(gm['mean'].min()),'min_month_R':int(gm['size'].min()),'months':len(gm)})
            for mo,r in gm.iterrows():monthly.append({'strategy':name,'alpha':a,'month':mo,'R':int(r['size']),'hits':int(r['sum']),'hit_rate':float(r['mean'])})
    return s,pd.DataFrame(rows),pd.DataFrame(monthly)


def make_summary(sel,score,monthly,folds):
    base=score[(score.strategy=='TOP2XTOP2')&(score.alpha==BASE_ALPHA)].iloc[0]
    stable=score[(score.months==5)&(score.min_month_R>=10)].copy()
    stable['delta_vs_base']=stable.hit_rate-float(base.hit_rate)
    best=stable.sort_values(['hit_rate','worst_month','hits'],ascending=False).head(15)
    L=['# v299 1HEAD exact-trifecta 3-ticket policy search','',
       '- Development research only; production unchanged.','- Jul/Aug excluded upstream; September outcomes unread.',
       '- Race selection is frozen to v298 HGB q0.95 + baseline alpha=.60 TOP2XTOP2 top5 mass >= .45.',
       '- Every candidate policy is scored on the identical selected denominator; boat-1 losses remain misses.',
       f'- Fixed selected races: **{len(sel)}**; head rate: **{100*sel.head_hit.mean():.2f}%**.','',
       '## Baseline','|strategy|alpha|R|3pt hits|3pt hit rate|worst month|','|---|---:|---:|---:|---:|---:|',
       f"|{base.strategy}|{base.alpha:.2f}|{int(base.R)}|{int(base.hits)}|{100*base.hit_rate:.2f}%|{100*base.worst_month:.2f}%|",'',
       '## Best 3-ticket policies on the same races','|strategy|alpha|R|hits|hit rate|delta|worst month|','|---|---:|---:|---:|---:|---:|---:|']
    for _,r in best.iterrows():
        L.append(f"|{r.strategy}|{r.alpha:.2f}|{int(r.R)}|{int(r.hits)}|{100*r.hit_rate:.2f}%|{100*r.delta_vs_base:+.2f}pt|{100*r.worst_month:.2f}%|")
    top=best.iloc[0]
    L+=['','## Monthly best-policy audit','|month|R|hits|hit rate|','|---|---:|---:|---:|']
    mm=monthly[(monthly.strategy==top.strategy)&(monthly.alpha==top.alpha)]
    for _,r in mm.iterrows():L.append(f"|{r.month}|{int(r.R)}|{int(r.hits)}|{100*r.hit_rate:.2f}%|")
    L+=['','## Decision']
    if top.hit_rate>base.hit_rate:
        L.append(f"- Best development policy improves 3-point exact hit rate from **{100*base.hit_rate:.2f}%** to **{100*top.hit_rate:.2f}%** on the same {int(base.R)} races.")
        L.append('- This is reused Feb-Jun development evidence, so freeze the winning policy before prospective validation.')
    else:L.append('- No policy beats the frozen v298 3-point baseline; retain baseline and change model features rather than ticket ordering.')
    return '\n'.join(L)+'\n'


def main():
    setup_v298()
    d,_=v298.v294.freeze_true_pre();d=v298.v294.add_prior_history(d);d=v298.v294.add_rel(d);d,threat=v298.add_threat(d)
    fams=v298.v296.clean_manifest(d)
    for fs in fams.values():
        if any('meet_' in c for c in fs):raise RuntimeError('forbidden meeting feature')
    print('v299 features frozen; audited settlement now',flush=True)
    d,cov=v298.v297.settle_full_after_freeze(d);d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    p,folds=run(d,fams,threat);sel,score,monthly=summarize(p)
    folds.to_csv(str(PREFIX)+'_folds.csv',index=False,encoding='utf-8-sig')
    score.to_csv(str(PREFIX)+'_policies.csv',index=False,encoding='utf-8-sig')
    monthly.to_csv(str(PREFIX)+'_monthly.csv',index=False,encoding='utf-8-sig')
    p.to_csv(str(PREFIX)+'_predictions.csv',index=False,encoding='utf-8-sig')
    SUMMARY.write_text(make_summary(sel,score,monthly,folds),encoding='utf-8')
    print(SUMMARY.read_text(),flush=True)

if __name__=='__main__':main()
