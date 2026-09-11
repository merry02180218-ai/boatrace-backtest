#!/usr/bin/env python3
"""v300: improve v298/v299 3-ticket exact-order accuracy via opponent-model features.

Development-only. Jul/Aug remain excluded upstream and September outcomes are unread.
The evaluation denominator is frozen to the same v298 race selection used by v299:
HGB q0.95 plus baseline alpha=.60 TOP2XTOP2 top5 mass >= .45.

Unlike v299, v300 changes SECOND/THIRD model features and regularization, not ticket
policy.  The baseline ticket policy stays TOP2XTOP2 alpha=.60 and every candidate is
scored on the identical selected races, with boat-1 losses retained as misses.
"""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
import pandas as pd
from scipy.special import logsumexp

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v297_1head_guard_trifecta5_research as settlement
import run_v298_1head_v288v283_audited as fastbase
import run_v298_1head_v288v283_audited_v2 as v2
import run_v299_1head_trifecta3_policy_search as v299

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'analysis_v300_1head_trifecta3_feature_upgrade'
SUMMARY=ROOT/'summary_v300_1head_trifecta3_feature_upgrade.md'
BOATS=v298.BOATS
TEST_MONTHS=list(v298.TEST_MONTHS)
BASE_ALPHA=.60
BASE_CONF=.45
SECOND_L2S=(3.0,10.0,30.0)
THIRD_L2S=(0.1,0.3,1.0)
KEYS=('nst_strength','motor','grade','wr','local','f_safety')


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
    settlement.AUDIT.clear()
    v298.v297.settle_full_after_freeze=settlement.settle_union_after_freeze


def augment_second(sl):
    q=sl.copy()
    # A linear ranker needs explicit role x quality interactions to learn that the
    # same relative strength means something different for boat 2 vs 4/5/6.
    pos={b:(q.boat.astype(int)==b).astype(float) for b in BOATS}
    for k in KEYS:
        for stem in (f'cand_{k}__pct',f'cand_{k}__center',f'diff1_{k}',f'innermax_{k}_minus_cand'):
            if stem not in q: continue
            x=pd.to_numeric(q[stem],errors='coerce')
            for b in BOATS:
                q[f'v300_{stem}_x_b{b}']=x*pos[b]
    # Compact strength/motor consensus features.
    if 'cand_nst_strength__pct' in q and 'cand_motor__pct' in q:
        a=pd.to_numeric(q['cand_nst_strength__pct'],errors='coerce');m=pd.to_numeric(q['cand_motor__pct'],errors='coerce')
        q['v300_start_motor_pct_mean']=(a+m)/2
        q['v300_start_motor_pct_min']=pd.concat([a,m],axis=1).min(axis=1)
        q['v300_start_x_motor_pct']=a*m
    return q


def augment_third(cl):
    q=cl.copy()
    # Conditional THIRD needs explicit relative/rank geometry between second and third.
    for k in KEYS:
        sp=f's_cand_{k}__pct';tp=f't_cand_{k}__pct';sc=f's_cand_{k}__center';tc=f't_cand_{k}__center'
        if sp in q and tp in q:
            s=pd.to_numeric(q[sp],errors='coerce');t=pd.to_numeric(q[tp],errors='coerce')
            q[f'v300_pct_t_minus_s_{k}']=t-s
            q[f'v300_pct_t_plus_s_{k}']=t+s
            q[f'v300_pct_pair_min_{k}']=pd.concat([s,t],axis=1).min(axis=1)
            q[f'v300_pct_pair_max_{k}']=pd.concat([s,t],axis=1).max(axis=1)
            q[f'v300_pct_pair_prod_{k}']=s*t
        if sc in q and tc in q:
            s=pd.to_numeric(q[sc],errors='coerce');t=pd.to_numeric(q[tc],errors='coerce')
            q[f'v300_center_t_minus_s_{k}']=t-s
            q[f'v300_center_pair_prod_{k}']=s*t
    # Role-specific pair interactions, important for 1-2-x / 1-3-x vs outer second.
    for role in ('pair_second_is2','pair_second_is3','pair_second_is4','pair_second_is5','pair_second_is6'):
        if role not in q: continue
        r=pd.to_numeric(q[role],errors='coerce')
        for k in ('nst_strength','motor'):
            c=f't_cand_{k}__pct'
            if c in q:q[f'v300_{role}_x_t_{k}_pct']=r*pd.to_numeric(q[c],errors='coerce')
    if all(c in q for c in ('s_cand_nst_strength__pct','t_cand_nst_strength__pct','s_cand_motor__pct','t_cand_motor__pct')):
        ss=pd.to_numeric(q['s_cand_nst_strength__pct'],errors='coerce');ts=pd.to_numeric(q['t_cand_nst_strength__pct'],errors='coerce')
        sm=pd.to_numeric(q['s_cand_motor__pct'],errors='coerce');tm=pd.to_numeric(q['t_cand_motor__pct'],errors='coerce')
        q['v300_pair_start_motor_balance']=(ss+ts+sm+tm)/4
        q['v300_third_start_motor_mean']=(ts+tm)/2
    return q


def good(df,fs,mincov=.55):
    out=[]
    for c in fs:
        if c not in df:continue
        x=pd.to_numeric(df[c],errors='coerce')
        if x.notna().mean()>=mincov and x.nunique(dropna=True)>=2:out.append(c)
    return out


def p2_predict(sl,tm,l2,aug):
    tr=sl[sl.month<tm].copy();te=sl[sl.month==tm].copy()
    meta={'date','month','race_code','y2','actual2','actual3','boat'}
    fs=good(tr,[c for c in tr.columns if c not in meta and (aug or not c.startswith('v300_'))])
    m=fastbase.FastSecond(l2).fit(tr,fs,'y2');te=te.copy();te['score']=m.score(te)
    out={}
    for code,g in te.groupby('race_code'):
        out[str(code).zfill(12)]=v298.v279.probs_within_race(g,'score')
    return out,len(fs)


def pc_predict(cl,tm,l2,aug):
    tr=cl[(cl.month<tm)&(cl.train_group==1)].copy();te=cl[cl.month==tm].copy()
    meta={'date','month','race_code','group_id','second_boat','third_boat','train_group','ycond','actual2','actual3'}
    fs=good(tr,[c for c in tr.columns if c not in meta and (aug or not c.startswith('v300_'))])
    m=fastbase.FastConditional(l2).fit(tr,fs);te=te.copy();te['score']=m.score(te)
    out={}
    for code,g in te.groupby('race_code'):
        pc={}
        for s,gs in g.groupby('second_boat'):
            a=gs.score.to_numpy(float);pp=np.exp(a-logsumexp(a))
            for t,p in zip(gs.third_boat.astype(int),pp):pc[(int(s),int(t))]=float(p)
        out[str(code).zfill(12)]=pc
    return out,len(fs)


def ticket3(p2,pc):
    pr=v299.pair_prob(p2,pc,BASE_ALPHA)
    order=v299.top2x2_order(p2,pc,pr)
    return ';'.join(f'1-{s}-{t}' for s,t in order[:3])


def base5(p2,pc):
    pr=v299.pair_prob(p2,pc,BASE_ALPHA);order=v299.top2x2_order(p2,pc,pr)
    return ';'.join(f'1-{s}-{t}' for s,t in order[:5]),sum(pr[x] for x in order[:5])


def run(d,fams,threat):
    sufs=v298.suffixes(d)
    sl=augment_second(v298.second_long(d,sufs));cl=augment_third(v298.conditional_long(d,sufs))
    core0=list(dict.fromkeys(fams['CLEAN_STATIC6_PLAYER']+threat))
    guard0=[c for c in core0 if c.startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]
    configs=[('BASE',10.0,.3,False)]+[(f'AUG_s{sl2:g}_t{tl2:g}',sl2,tl2,True) for sl2 in SECOND_L2S for tl2 in THIRD_L2S]
    pred=[];folds=[]
    for tm in TEST_MONTHS:
        tr=d[d.month<tm].copy();te=d[d.month==tm].copy()
        core=v298.v293.available(tr,core0,.55);guard=v298.v293.available(tr,guard0,.55)
        ph,pg,hc,gc,noh,nog=v298.head_fold(tr,te,core,guard)
        z=te[['date','month','race_code','venue','race','head_hit','actual_combo','combo_valid']].copy()
        z['test_month']=tm;z['p_head_hgb']=ph
        for q,c in hc.items():z[f'hgb_q{q}_sel']=(ph>=c).astype(int)
        feature_counts={}
        for name,sl2,tl2,aug in configs:
            p2,nf2=p2_predict(sl,tm,sl2,aug);pc,nf3=pc_predict(cl,tm,tl2,aug);feature_counts[name]=(nf2,nf3)
            vals=[];masses=[]
            for _,r in z.iterrows():
                code=str(r.race_code).zfill(12)
                vals.append(ticket3(p2[code],pc[code]))
                if name=='BASE':masses.append(base5(p2[code],pc[code])[1])
            z[f'top3_{name}']=vals
            z[f'hit3_{name}']=[int(bool(a) and a in t.split(';')) for a,t in zip(z.actual_combo,vals)]
            if name=='BASE':z['base_top5_mass']=masses
        z['base_selected']=((z['hgb_q0.95_sel']==1)&(z.base_top5_mass>=BASE_CONF)).astype(int)
        pred.append(z)
        folds.append({'month':tm,'train':len(tr),'test':len(te),'head_features':len(core),'head_oof':noh,'guard_oof':nog,
                      'base_second_features':feature_counts['BASE'][0],'base_third_features':feature_counts['BASE'][1],
                      'aug_second_features':max(x[0] for n,x in feature_counts.items() if n!='BASE'),
                      'aug_third_features':max(x[1] for n,x in feature_counts.items() if n!='BASE')})
        print('v300 fold',tm,'done',len(te),flush=True)
    return pd.concat(pred,ignore_index=True),pd.DataFrame(folds),configs


def summarize(p,configs):
    s=p[p.base_selected==1].copy();rows=[];monthly=[]
    for name,sl2,tl2,aug in configs:
        col=f'hit3_{name}';gm=s.groupby('test_month')[col].agg(['size','sum','mean'])
        rows.append({'config':name,'augmented':int(aug),'second_l2':sl2,'third_l2':tl2,'R':len(s),'hits':int(s[col].sum()),
                     'hit_rate':float(s[col].mean()),'worst_month':float(gm['mean'].min()),'months':len(gm),'min_month_R':int(gm['size'].min())})
        for mo,r in gm.iterrows():monthly.append({'config':name,'month':mo,'R':int(r['size']),'hits':int(r['sum']),'hit_rate':float(r['mean'])})
    return s,pd.DataFrame(rows),pd.DataFrame(monthly)


def make_summary(sel,score,monthly):
    base=score[score.config=='BASE'].iloc[0];q=score.copy();q['delta']=q.hit_rate-base.hit_rate
    best=q.sort_values(['hit_rate','worst_month','hits'],ascending=False).head(12);top=best.iloc[0]
    L=['# v300 1HEAD exact-trifecta 3-ticket opponent feature upgrade','',
       '- Development research only; production unchanged.','- Jul/Aug excluded upstream; September outcomes unread.',
       '- Evaluation race set is frozen to the v299/v298 baseline selector; every config uses the same denominator.',
       '- Boat-1 losses remain exact-trifecta misses. Ticket policy is fixed TOP2XTOP2 alpha=.60.',
       f'- Fixed selected races: **{len(sel)}**; head rate: **{100*sel.head_hit.mean():.2f}%**.','',
       '## Baseline','|config|R|hits|3pt hit|worst month|','|---|---:|---:|---:|---:|',
       f"|BASE|{int(base.R)}|{int(base.hits)}|{100*base.hit_rate:.2f}%|{100*base.worst_month:.2f}%|",'',
       '## Feature/regularization candidates','|config|S L2|T L2|R|hits|hit rate|delta|worst month|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in best.iterrows():L.append(f"|{r.config}|{r.second_l2:g}|{r.third_l2:g}|{int(r.R)}|{int(r.hits)}|{100*r.hit_rate:.2f}%|{100*r.delta:+.2f}pt|{100*r.worst_month:.2f}%|")
    L+=['','## Monthly best-config audit','|month|R|hits|hit rate|','|---|---:|---:|---:|']
    for _,r in monthly[monthly.config==top.config].iterrows():L.append(f"|{r.month}|{int(r.R)}|{int(r.hits)}|{100*r.hit_rate:.2f}%|")
    L+=['','## Decision']
    if top.hit_rate>base.hit_rate:
        L.append(f"- v300 improves the frozen 3-point baseline from **{100*base.hit_rate:.2f}% ({int(base.hits)}/{int(base.R)})** to **{100*top.hit_rate:.2f}% ({int(top.hits)}/{int(top.R)})** on the identical races.")
        L.append(f"- Winning development config: **{top.config}**, worst-month hit rate **{100*top.worst_month:.2f}%**.")
        L.append('- Feb-Jun is reused development evidence; freeze this config before any prospective validation.')
    else:
        L.append('- v300 opponent feature interactions do not beat the frozen 50% baseline. Do not promote.')
    return '\n'.join(L)+'\n'


def main():
    setup_v298()
    d,_=v298.v294.freeze_true_pre();d=v298.v294.add_prior_history(d);d=v298.v294.add_rel(d);d,threat=v298.add_threat(d)
    fams=v298.v296.clean_manifest(d)
    for fs in fams.values():
        if any('meet_' in c for c in fs):raise RuntimeError('forbidden meeting feature')
    print('v300 PRE features frozen; audited settlement now',flush=True)
    d,cov=v298.v297.settle_full_after_freeze(d);d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    p,folds,configs=run(d,fams,threat);sel,score,monthly=summarize(p,configs)
    folds.to_csv(str(PREFIX)+'_folds.csv',index=False,encoding='utf-8-sig')
    score.to_csv(str(PREFIX)+'_configs.csv',index=False,encoding='utf-8-sig')
    monthly.to_csv(str(PREFIX)+'_monthly.csv',index=False,encoding='utf-8-sig')
    SUMMARY.write_text(make_summary(sel,score,monthly),encoding='utf-8')
    print(SUMMARY.read_text(),flush=True)

if __name__=='__main__':main()
