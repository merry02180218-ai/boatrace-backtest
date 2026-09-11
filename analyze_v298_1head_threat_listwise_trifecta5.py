#!/usr/bin/env python3
"""v298: clean 1-head threat guard + v283-style listwise/conditional trifecta research.

Development-only.  Jul/Aug 2026 are excluded and September outcomes are never read.
All PRE features/history are frozen before settlement.  Boat-1 losses remain misses in
all exact-trifecta denominators.

v283 ideas intentionally reused structurally:
- SECOND: five-candidate race-listwise softmax, L2=10.
- THIRD: four-candidate conditional ranker P(third=t | second=s), L2=0.3.
- Pair ordering: alpha2=0.60 log-probability blend with TOP2XTOP2 prefix.

The 1-head gate keeps v297 HGB+LR consensus, but adds explicit clean PRE threat
structure (relative start strength, wall/inner resistance and 2/3/4 attack roles).
"""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
import pandas as pd
from scipy.special import logsumexp

import analyze_v294_1head_verified_prepost_research as v294
import analyze_v296_1head_clean_operational_rebuild as v296
import analyze_v297_1head_guard_trifecta5_research as v297
import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v282_4head_conditional_third as v282
import analyze_v293_1head_direct_history_research as v293

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'analysis_v298_1head_threat_listwise_trifecta5'
SUMMARY=ROOT/'summary_v298_1head_threat_listwise_trifecta5.md'
TEST_MONTHS=list(v294.TEST_MONTHS)
HEAD_Q=list(v297.HEAD_Q)
GUARD_Q=list(v297.GUARD_Q)
CONF_CUTS=list(v297.CONF_CUTS)
K_LIST=(1,2,3,4,5)
BOATS=(2,3,4,5,6)
SECOND_L2=10.0
THIRD_L2=0.3
ALPHA2=0.60


def num(s):
    return pd.to_numeric(s,errors='coerce')


def add_threat(d):
    """Clean PRE relative threat decomposition; never uses meeting/self-slot fields."""
    q=d.copy(); made=[]
    keys=('nst_strength','motor','grade','wr','local','f_safety')
    for k in keys:
        b1=num(q[f'b1_{k}'])
        opp=[]
        for b in BOATS:
            c=f'b{b}_{k}'
            if c not in q: continue
            x=num(q[c]); name=f'v298_threat_{k}_b{b}_minus1';q[name]=x-b1;made.append(name);opp.append(x)
        if opp:
            mat=pd.concat(opp,axis=1)
            name=f'v298_threat_{k}_oppmax_minus1';q[name]=mat.max(axis=1)-b1;made.append(name)
        if all(f'b{b}_{k}' in q for b in (2,3,4)):
            attack=pd.concat([num(q[f'b3_{k}']),num(q[f'b4_{k}'])],axis=1).max(axis=1)
            n=f'v298_attack34_{k}_minus1';q[n]=attack-b1;made.append(n)
            n=f'v298_wall2_{k}_vs_attack34';q[n]=num(q[f'b2_{k}'])-attack;made.append(n)
            n=f'v298_inner23_{k}_vs4';q[n]=pd.concat([num(q[f'b2_{k}']),num(q[f'b3_{k}'])],axis=1).max(axis=1)-num(q[f'b4_{k}']);made.append(n)
    # Interactions mirror the role decomposition used by 3/4-head models while
    # remaining morning-PRE only.
    if all(x in q for x in ('b1_nst_strength','b2_nst_strength','b3_nst_strength','b4_nst_strength')):
        n='v298_wall2_start_x_attack34_start'
        wall=num(q.b2_nst_strength)-pd.concat([num(q.b3_nst_strength),num(q.b4_nst_strength)],axis=1).max(axis=1)
        attack=pd.concat([num(q.b3_nst_strength),num(q.b4_nst_strength)],axis=1).max(axis=1)-num(q.b1_nst_strength)
        q[n]=wall*attack;made.append(n)
    return q,list(dict.fromkeys(made))


def suffixes(d):
    """Symmetric per-boat candidate attributes available for every boat."""
    s=[]
    for c in d.columns:
        if not c.startswith('b1_') or 'meet_' in c: continue
        x=c[3:]
        if all(f'b{b}_{x}' in d for b in range(1,7)):
            s.append(x)
    return sorted(set(s))


def actual23(x):
    try:
        a=[int(z) for z in str(x).split('-')]
        return (a[1],a[2]) if len(a)==3 and a[0]==1 else (0,0)
    except Exception:return (0,0)


def cand_record(r,b,sufs,prefix=''):
    z={'boat':int(b),'pos_boat':float(b),'pos_inner':float(b<=3),'pos_outer':float(b>=4),'pos_distance1':float(b-1)}
    for k in sufs:
        cv=pd.to_numeric(pd.Series([r.get(f'b{b}_{k}',np.nan)]),errors='coerce').iloc[0]
        ov=pd.to_numeric(pd.Series([r.get(f'b1_{k}',np.nan)]),errors='coerce').iloc[0]
        z[f'{prefix}cand_{k}']=cv
        z[f'{prefix}diff1_{k}']=cv-ov if pd.notna(cv) and pd.notna(ov) else np.nan
    # Inner-wall context relative to this candidate.
    for k in ('nst_strength','motor','grade','wr'):
        cc=pd.to_numeric(pd.Series([r.get(f'b{b}_{k}',np.nan)]),errors='coerce').iloc[0]
        inn=[]
        for j in range(2,b):
            v=pd.to_numeric(pd.Series([r.get(f'b{j}_{k}',np.nan)]),errors='coerce').iloc[0]
            if pd.notna(v):inn.append(float(v))
        z[f'{prefix}innermax_{k}_minus_cand']=(max(inn)-cc) if inn and pd.notna(cc) else 0.0 if b==2 and pd.notna(cc) else np.nan
    return z


def second_long(d,sufs):
    rec=[]
    for _,r in d.iterrows():
        a2,a3=actual23(r.actual_combo)
        if int(r.head_hit)!=1 or a2 not in BOATS or a3 not in BOATS:continue
        for b in BOATS:
            z={'date':r.date,'month':r.month,'race_code':str(r.race_code).zfill(12),'y2':int(b==a2),'actual2':a2,'actual3':a3}
            z.update(cand_record(r,b,sufs));rec.append(z)
    return pd.DataFrame(rec)


def conditional_long(d,sufs):
    rec=[]
    for _,r in d.iterrows():
        a2,a3=actual23(r.actual_combo)
        if int(r.head_hit)!=1 or a2 not in BOATS or a3 not in BOATS:continue
        for s in BOATS:
            sr=cand_record(r,s,sufs,'s_')
            for t in BOATS:
                if t==s:continue
                tr=cand_record(r,t,sufs,'t_')
                z={'date':r.date,'month':r.month,'race_code':str(r.race_code).zfill(12),'group_id':f'{str(r.race_code).zfill(12)}|{s}',
                   'second_boat':s,'third_boat':t,'train_group':int(s==a2),'ycond':int(s==a2 and t==a3),'actual2':a2,'actual3':a3,
                   'pair_same_side':float((s<=3 and t<=3) or (s>=4 and t>=4)),'pair_adjacent':float(abs(s-t)==1),'pair_distance':float(abs(s-t))}
                z.update(sr);z.update(tr)
                for k in sufs:
                    a=z.get(f't_cand_{k}',np.nan);b=z.get(f's_cand_{k}',np.nan)
                    z[f't_minus_s_{k}']=a-b if pd.notna(a) and pd.notna(b) else np.nan
                rec.append(z)
    return pd.DataFrame(rec)


def good(df,fs,mincov=.55):
    out=[]
    for c in fs:
        if c not in df:continue
        x=num(df[c])
        if x.notna().mean()>=mincov and x.nunique(dropna=True)>=2:out.append(c)
    return out


def p2_fit_predict(sl,tm):
    tr=sl[sl.month<tm].copy();te=sl[sl.month==tm].copy()
    meta={'date','month','race_code','y2','actual2','actual3','boat'}
    fs=good(tr,[c for c in tr.columns if c not in meta])
    m=v279.ListwiseSoftmax(SECOND_L2).fit(tr,fs,'y2');te=te.copy();te['score']=m.score(te)
    out={}
    for code,g in te.groupby('race_code'):
        out[str(code).zfill(12)]=v279.probs_within_race(g,'score')
    return out,len(fs),tr.race_code.nunique()


def pc_fit_predict(cl,tm):
    tr=cl[(cl.month<tm)&(cl.train_group==1)].copy();te=cl[cl.month==tm].copy()
    meta={'date','month','race_code','group_id','second_boat','third_boat','train_group','ycond','actual2','actual3'}
    fs=good(tr,[c for c in tr.columns if c not in meta])
    m=v282.ListwiseN(THIRD_L2).fit(tr,fs);te=te.copy();te['score']=m.score(te)
    out={}
    for code,g in te.groupby('race_code'):
        pc={}
        for s,gs in g.groupby('second_boat'):
            a=gs.score.to_numpy(float);pp=np.exp(a-logsumexp(a))
            for t,p in zip(gs.third_boat.astype(int),pp):pc[(int(s),int(t))]=float(p)
        out[str(code).zfill(12)]=pc
    return out,len(fs),tr.race_code.nunique()


def pair_order(p2,pc):
    base=[]
    for s in BOATS:
        for t in BOATS:
            if s==t:continue
            sc=ALPHA2*math.log(max(p2[s],1e-12))+(1-ALPHA2)*math.log(max(pc[(s,t)],1e-12))
            base.append((sc,s,t))
    base.sort(key=lambda x:(-x[0],x[1],x[2]))
    ordinary=[(s,t) for _,s,t in base]
    sr=sorted(BOATS,key=lambda s:(-p2[s],s));s1,s2=sr[:2]
    cr={s:sorted([t for t in BOATS if t!=s],key=lambda t:(-pc[(s,t)],t)) for s in BOATS}
    pool=[(s,cr[s][k]) for k in (0,1) for s in (s1,s2)]
    rank={x:ordinary.index(x) for x in pool};pre=sorted(pool,key=lambda x:rank[x])
    order=[]
    for x in pre+ordinary:
        if x not in order:order.append(x)
    raw={(s,t):math.exp(sc) for sc,s,t in base};den=sum(raw.values())
    prob={k:v/den for k,v in raw.items()}
    return order,prob


def head_fold(tr,te,core,guard):
    return v297.head_fold(tr,te,core,guard)


def run(d,fams,threat):
    sufs=suffixes(d);sl=second_long(d,sufs);cl=conditional_long(d,sufs)
    core0=list(dict.fromkeys(fams['CLEAN_STATIC6_PLAYER']+threat))
    guard0=[c for c in core0 if c.startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]
    pred=[];folds=[]
    for tm in TEST_MONTHS:
        tr=d[d.month<tm].copy();te=d[d.month==tm].copy()
        core=v293.available(tr,core0,.55);guard=v293.available(tr,guard0,.55)
        ph,pg,hc,gc,noh,nog=head_fold(tr,te,core,guard)
        p2,nf2,nr2=p2_fit_predict(sl,tm);pc,nf3,nr3=pc_fit_predict(cl,tm)
        z=te[['date','month','race_code','venue','race','head_hit','actual_combo','combo_valid']].copy();z['test_month']=tm;z['p_head_hgb']=ph;z['p_safe_lr']=pg
        for q,c in hc.items():z[f'hgb_q{q}_cut']=c;z[f'hgb_q{q}_sel']=(ph>=c).astype(int)
        for q,c in gc.items():z[f'lr_q{q}_cut']=c;z[f'lr_q{q}_sel']=(pg>=c).astype(int)
        tops=[];masses=[]
        for _,r in z.iterrows():
            code=str(r.race_code).zfill(12)
            if code not in p2 or code not in pc:raise RuntimeError(f'missing opponent prediction {tm} {code}')
            order,pr=pair_order(p2[code],pc[code]);tickets=[f'1-{a}-{b}' for a,b in order[:5]]
            tops.append(';'.join(tickets));masses.append(sum(pr[(a,b)] for a,b in order[:5]))
        z['top5']=tops;z['top5_mass']=masses
        for k in K_LIST:z[f'hit{k}']=[int(bool(a) and a in t.split(';')[:k]) for a,t in zip(z.actual_combo,z.top5)]
        pred.append(z);folds.append({'month':tm,'core_features':len(core),'guard_features':len(guard),'second_features':nf2,'third_features':nf3,
                                     'train':len(tr),'test':len(te),'head_oof':noh,'guard_oof':nog,'second_train_races':nr2,'third_train_races':nr3})
        print('fold',tm,'test',len(te),'headf',len(core),'secondf',nf2,'thirdf',nf3,flush=True)
    return pd.concat(pred,ignore_index=True),pd.DataFrame(folds),sufs


def pct(x):return '-' if pd.isna(x) else f'{100*float(x):.2f}%'


def make_summary(cov,folds,pool,km,sufs,threat):
    stable=pool[(pool.months==5)&(pool.R>=100)&(pool.min_month_R>=10)].copy()
    stable['joint_gap']=np.maximum(0,.90-stable.head_rate)+np.maximum(0,.80-stable.trifecta5_rate)
    best=stable.sort_values(['joint_gap','trifecta5_rate','head_rate','R'],ascending=[True,False,False,False]).head(20)
    target=stable[(stable.head_rate>=.90)&(stable.trifecta5_rate>=.80)]
    L=['# v298 clean 1HEAD threat + v283-style listwise trifecta <=5','',
       '- Development research only; production unchanged.','- Jul/Aug 2026 excluded; September outcomes unread.',
       '- PRE/history features are frozen before exact settlement; meeting self-slot leakage features stay forbidden.',
       '- Every final-selected settled race is in the exact denominator. Boat-1 losses are misses.',
       f'- SECOND = listwise PLAYER-style candidate ranker L2={SECOND_L2:g}; THIRD = conditional four-way L2={THIRD_L2:g}.',
       f'- Pair policy = TOP2XTOP2 prefix + alpha2={ALPHA2:.2f} joint blend (frozen from v283 semantics).',
       f'- candidate symmetric suffixes={len(sufs)}; explicit head-threat features={len(threat)}; exact settlement coverage={100*cov:.2f}%.','',
       '## Fold audit','|month|train|test|head f|guard f|second f|third f|second train races|third train races|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in folds.iterrows():L.append(f'|{r.month}|{int(r.train)}|{int(r.test)}|{int(r.core_features)}|{int(r.guard_features)}|{int(r.second_features)}|{int(r.third_features)}|{int(r.second_train_races)}|{int(r.third_train_races)}|')
    L+=['','## Best stable development zones','|rule|conf|R|head|5pt exact|worst head|worst 5pt|min month R|','|---|---:|---:|---:|---:|---:|---:|---:|']
    if best.empty:L.append('|None|-|-|-|-|-|-|-|')
    else:
        for _,r in best.iterrows():L.append(f'|{r.rule}|{r.conf_cut:.2f}|{int(r.R)}|{pct(r.head_rate)}|{pct(r.trifecta5_rate)}|{pct(r.worst_head_month)}|{pct(r.worst_tri5_month)}|{int(r.min_month_R)}|')
    L+=['','## <=5-point ceiling for best joint rule','|points|R|hits|hit rate|Wilson low|','|---:|---:|---:|---:|---:|']
    if km.empty:L.append('|-|-|-|-|-|')
    else:
        for _,r in km.iterrows():L.append(f'|{int(r.points)}|{int(r.R)}|{int(r.hits)}|{pct(r.hit_rate)}|{pct(r.wilson_lo)}|')
    L+=['','## Target decision']
    if target.empty:L.append('- **No stable development rule simultaneously reaches head >=90% and exact <=5 points >=80%. Do not promote v298.**')
    else:
        L.append('- Development zones meeting both numeric targets exist, but Feb-Jun is reused development evidence; freeze before any prospective validation.')
        for _,r in target.sort_values(['trifecta5_rate','head_rate','R'],ascending=False).head(10).iterrows():L.append(f'  - {r.rule}, conf>={r.conf_cut:.2f}: R={int(r.R)}, head={pct(r.head_rate)}, 5pt={pct(r.trifecta5_rate)}')
    return '\n'.join(L)+'\n'


def main():
    d,_=v294.freeze_true_pre();d=v294.add_prior_history(d);d=v294.add_rel(d);d,threat=add_threat(d)
    fams=v296.clean_manifest(d)
    for fs in fams.values():
        if any('meet_' in c for c in fs):raise RuntimeError('forbidden meeting feature')
    print('features frozen; exact settlement now',flush=True)
    d,cov=v297.settle_full_after_freeze(d);d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    p,folds,sufs=run(d,fams,threat)
    monthly,pool=v297.evaluate(p);km=v297.k_metrics(p,pool)
    folds.to_csv(str(PREFIX)+'_folds.csv',index=False,encoding='utf-8-sig');monthly.to_csv(str(PREFIX)+'_monthly.csv',index=False,encoding='utf-8-sig')
    pool.to_csv(str(PREFIX)+'_pooled.csv',index=False,encoding='utf-8-sig');km.to_csv(str(PREFIX)+'_kpoints.csv',index=False,encoding='utf-8-sig')
    p.to_csv(str(PREFIX)+'_predictions.csv',index=False,encoding='utf-8-sig')
    SUMMARY.write_text(make_summary(cov,folds,pool,km,sufs,threat),encoding='utf-8');print(SUMMARY.read_text(),flush=True)

if __name__=='__main__':main()
