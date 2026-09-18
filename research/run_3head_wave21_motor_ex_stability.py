from __future__ import annotations
import json
import numpy as np
import pandas as pd

from run_3head_funsite_broad50_wave16 import build_pre_enhanced, load_canonical
from run_3head_wave19_motor_exhibition_gate import (
    prefetch_sources, build_motor_exhibition, prep_month, make_pre_scores
)

BANDS=[(1,8),(1,12)]
BQS=[.925,.95,.97,.98,.985]

def cond_mask(df,cond):
    col,op,val=cond
    x=pd.to_numeric(df[col],errors='coerce')
    if op=='>=':return x>=val
    if op=='<=':return x<=val
    raise ValueError(op)

def gates():
    out=[]
    def add(name,*conds):out.append({'name':name,'conds':[list(c) for c in conds]})

    motor_rank=[-.20,0.0,.20,.40]
    motor_top2=[-.03,0.0,.03,.05,.08]
    ex_ranks=[1,2,3]
    ex_edges=[-.02,0.0,.01,.02,.03]

    for mv in motor_rank:
        for er in ex_ranks:
            add(f'mrank{mv:+.2f}__exrank{er}',
                ('post_motor_rank_edge2','>=',mv),('post_ex_rank3','<=',er))
        for ev in ex_edges:
            add(f'mrank{mv:+.2f}__exedge{ev:+.2f}',
                ('post_motor_rank_edge2','>=',mv),('post_ex_edge2','>=',ev))

    for mv in motor_top2:
        for er in ex_ranks:
            add(f'mtop2{mv:+.2f}__exrank{er}',
                ('post_motor_gap2_top2','>=',mv),('post_ex_rank3','<=',er))
        for ev in ex_edges:
            add(f'mtop2{mv:+.2f}__exedge{ev:+.2f}',
                ('post_motor_gap2_top2','>=',mv),('post_ex_edge2','>=',ev))

    # Limited inner sensitivity family.
    for mv in [0.0,.03,.05]:
        for er in [1,2]:
            add(f'minner{mv:+.2f}__exrank{er}',
                ('post_motor_inner_top2_gap','>=',mv),('post_ex_rank3','<=',er))
    return out

def select_mask(df,c):
    rn=pd.to_numeric(df.race_no,errors='coerce')
    pre=pd.to_numeric(df.pre_score,errors='coerce')
    lo,hi=c['band']
    m=(rn>=lo)&(rn<=hi)&pre.notna()&(pre>=c['bq'])
    for cond in c['gate']['conds']:
        m &= cond_mask(df,cond).fillna(False)
    return m

def metrics(mask,df):
    m=np.asarray(mask,bool);n=int(m.sum())
    if n==0:return {'n':0,'hits':0,'rate':None,'venues':0}
    y=df.y.to_numpy(dtype=int)
    return {'n':n,'hits':int(y[m].sum()),'rate':float(y[m].mean()),
            'venues':int(df.loc[m,'venue'].nunique())}

def eval_month(df,c,month):
    m=select_mask(df,c)
    d=df.date.dt.day
    split=14 if month=='feb' else 15
    return {'h1':metrics(m&(d<=split),df),'h2':metrics(m&(d>split),df)}

def comb(z):
    n=z['h1']['n']+z['h2']['n'];h=z['h1']['hits']+z['h2']['hits']
    return {'n':n,'hits':h,'rate':h/n if n else None}

def eligible(ms):
    for mon in ['nov','dec','jan']:
        z=ms[mon]; c=comb(z)
        if c['n']<40 or c['n']>70:return False
        for h in ['h1','h2']:
            if z[h]['n']<8 or z[h]['venues']<6 or z[h]['rate'] is None:return False
    return True

def summarize(ms):
    monthly={m:comb(ms[m]) for m in ['nov','dec','jan']}
    halves=[ms[m][h]['rate'] for m in ['nov','dec','jan'] for h in ['h1','h2']]
    n=sum(x['n'] for x in monthly.values());hits=sum(x['hits'] for x in monthly.values())
    return {
      'min_month_rate':min(x['rate'] for x in monthly.values()),
      'persistent_worst_half':min(halves),
      'combined_n':n,'combined_hits':hits,'combined_rate':hits/n,
      'avg_month_n':sum(x['n'] for x in monthly.values())/3,
      'monthly':monthly
    }

def rank_key(z):
    s=z['summary']
    return (s['min_month_rate'],s['combined_rate'],s['persistent_worst_half'],
            -abs(s['avg_month_n']-50.0))

def venue_audit(months,c):
    parts=[]
    for mon in ['nov','dec','jan']:
        df=months[mon]
        m=select_mask(df,c)
        q=df.loc[m,['venue','y']].copy()
        q['month']=mon
        parts.append(q)
    sel=pd.concat(parts,ignore_index=True)
    total_n=len(sel); total_h=int(sel.y.sum())
    by=[]
    for v,g in sel.groupby('venue'):
        by.append({'venue':str(v),'n':len(g),'hits':int(g.y.sum()),'rate':float(g.y.mean()),
                   'share':len(g)/total_n if total_n else 0})
    by=sorted(by,key=lambda x:x['n'],reverse=True)
    loo=[]
    for v in sorted(sel.venue.astype(str).unique()):
        g=sel[sel.venue.astype(str)!=v]
        if len(g):
            loo.append({'left_out':v,'n':len(g),'hits':int(g.y.sum()),'rate':float(g.y.mean())})
    return {
      'total_n':total_n,'total_hits':total_h,'total_rate':total_h/total_n if total_n else None,
      'max_venue_share':max((x['share'] for x in by),default=0),
      'top_venues':by[:10],
      'loo_min_rate':min((x['rate'] for x in loo),default=None),
      'loo_max_rate':max((x['rate'] for x in loo),default=None),
      'loo':loo
    }

def main():
    canon=load_canonical()
    raw={}
    for m,(a,b) in {
      'oct':('2025-10-01','2025-10-31'),
      'nov':('2025-11-01','2025-11-30'),'dec':('2025-12-01','2025-12-31'),
      'jan':('2026-01-01','2026-01-31'),'feb':('2026-02-01','2026-02-28')}.items():
        x,r,audit=build_pre_enhanced(a,b,True); raw[m]=(x,r,audit)

    frames={m:prep_month(x,r) for m,(x,r,_) in raw.items()}

    cf=canon[(canon.date>='2026-02-01')&(canon.date<'2026-03-01')][['rc','date','settle__winner']].copy()
    frames['feb']=cf.merge(raw['feb'][0].drop(columns=['date']),on='rc',how='inner')
    frames['feb']['y']=(pd.to_numeric(frames['feb'].settle__winner,errors='coerce')==3).astype(int)

    fc=cf.merge(raw['feb'][1][['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)!=3970 or agree<.999:
        raise RuntimeError(f'feb cross-check failed n={len(fc)} agreement={agree}')

    prescores,enh_count=make_pre_scores(frames)
    days,cache=prefetch_sources()
    post,post_audit=build_motor_exhibition(days,cache)

    months={}
    for m in ['nov','dec','jan','feb']:
        months[m]=prescores[m].merge(post,on=['rc','date'],how='left',validate='one_to_one')

    gs=gates()
    candidates=[{'band':list(b),'bq':q,'gate':g} for b in BANDS for q in BQS for g in gs]
    rows=[]
    for c in candidates:
        ms={m:eval_month(months[m],c,m) for m in ['nov','dec','jan']}
        if not eligible(ms):continue
        rows.append({'candidate':c,'months':ms,'summary':summarize(ms)})
    rows=sorted(rows,key=rank_key,reverse=True)
    best=rows[0] if rows else None

    feb=None;va=None
    if best:
        e=eval_month(months['feb'],best['candidate'],'feb')
        feb={'h1':e['h1'],'h2':e['h2'],**comb(e)}
        va=venue_audit(months,best['candidate'])

    # Neighborhood around exact Wave20 signal for robustness display.
    neighbors=[]
    for z in rows:
        name=z['candidate']['gate']['name']
        if ('mrank' in name or 'mtop2' in name) and ('exrank' in name or 'exedge' in name):
            neighbors.append(z)
    neighbors_combined=sorted(neighbors,key=lambda z:(z['summary']['combined_rate'],
                                                     z['summary']['min_month_rate'],
                                                     z['summary']['persistent_worst_half']),reverse=True)[:20]

    out={
      'policy':{
        'local_motor_ex_neighborhood_only':True,'selection_nov_dec_jan_only':True,
        'rank_min_month_then_combined_then_half':True,'motor_strict_prior_day':True,
        'same_day_results_used':False,'february_reference_non_pristine':True,
        'march_outcomes_opened':False,'september_2026_outcomes_read':False,
        'production_v288_changed':False
      },
      'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
      'source_audit':{m:raw[m][2] for m in raw},
      'post_source_audit':post_audit,
      'feature_context':{'enhanced_pre_count':enh_count,'gate_count':len(gs)},
      'candidate_count':len(candidates),'eligible_count':len(rows),
      'best_pre_feb':best,
      'best_feb_reference_non_pristine':feb,
      'best_venue_audit':va,
      'top20_stability':rows[:20],
      'top20_combined_neighbors':neighbors_combined
    }
    with open('research_3head_wave21_motor_ex_stability_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
