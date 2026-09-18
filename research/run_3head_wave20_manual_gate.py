from __future__ import annotations
import json
import numpy as np
import pandas as pd

from run_3head_funsite_broad50_wave16 import build_pre_enhanced, load_canonical
from run_3head_wave19_motor_exhibition_gate import (
    prefetch_sources, build_motor_exhibition, prep_month, make_pre_scores
)

BROAD_QS=[.90,.925,.95,.97,.98,.985,.99]
BANDS=[(1,8),(1,12)]

def cond_mask(df,cond):
    col,op,val=cond
    x=pd.to_numeric(df[col],errors='coerce')
    if op=='>=': return x>=val
    if op=='<=': return x<=val
    if op=='==': return x==val
    raise ValueError(op)

def add_gate(out,name,family,*conds):
    out.append({'name':name,'family':family,'conds':[list(x) for x in conds]})

def primitive_gates():
    g=[]
    # Exhibition time: lower time is better; all "edge" columns are opponent - boat3, so positive favors boat3.
    for k in [1,2,3]:
        add_gate(g,f'ex_rank_le_{k}','EXHIBIT',('post_ex_rank3','<=',k))
    for v in [0.0,.01,.02,.03,.04,.05]:
        add_gate(g,f'ex_field_ge_{v:.2f}','EXHIBIT',('post_ex_field_edge','>=',v))
    for v in [-.02,0.0,.01,.02,.03,.04]:
        add_gate(g,f'ex_vs2_ge_{v:.2f}','EXHIBIT',('post_ex_edge2','>=',v))
        add_gate(g,f'ex_inner_ge_{v:.2f}','EXHIBIT',('post_ex_inner_edge','>=',v))

    # Start exhibition: lower ST is better; positive edge favors boat3.
    for k in [1,2,3]:
        add_gate(g,f'st_rank_le_{k}','START',('post_st_rank3','<=',k))
    for v in [-.02,0.0,.02,.04,.06,.08]:
        add_gate(g,f'st_field_ge_{v:.2f}','START',('post_st_field_edge','>=',v))
    for v in [-.05,-.02,0.0,.02,.04,.06]:
        add_gate(g,f'st_vs2_ge_{v:.2f}','START',('post_st_edge2','>=',v))
        add_gate(g,f'st_inner_ge_{v:.2f}','START',('post_st_inner_edge','>=',v))
    add_gate(g,'course3_fixed','COURSE',('post_course3_abs_shift','==',0))

    # Original exhibition metrics. Only all-six complete rows pass these gates.
    for lab in ['turn','straight','lap']:
        for v in [0.0,.03,.06,.10]:
            add_gate(g,f'{lab}_field_ge_{v:.2f}','ORIGINAL',
                     (f'post_{lab}_available','==',1),(f'post_{lab}_field_edge','>=',v))
        for v in [0.0,.03,.06]:
            add_gate(g,f'{lab}_vs2_ge_{v:.2f}','ORIGINAL',
                     (f'post_{lab}_available','==',1),(f'post_{lab}_edge2','>=',v))

    # Prior-day causal motor current form.
    for v in [-.05,0.0,.03,.05,.08]:
        add_gate(g,f'motor_top2_vs2_ge_{v:.2f}','MOTOR',('post_motor_gap2_top2','>=',v))
        add_gate(g,f'motor_top2_vs4_ge_{v:.2f}','MOTOR',('post_motor_gap4_top2','>=',v))
        add_gate(g,f'motor_inner_top2_ge_{v:.2f}','MOTOR',('post_motor_inner_top2_gap','>=',v))
    for v in [-.30,0.0,.20,.40,.60]:
        add_gate(g,f'motor_rank_vs2_ge_{v:.2f}','MOTOR',('post_motor_rank_edge2','>=',v))
        add_gate(g,f'motor_rank_vs4_ge_{v:.2f}','MOTOR',('post_motor_rank_edge4','>=',v))
        add_gate(g,f'motor_inner_rank_ge_{v:.2f}','MOTOR',('post_motor_inner_rank_edge','>=',v))
    for v in [-.03,0.0,.01,.02,.03]:
        add_gate(g,f'motor_st_vs2_ge_{v:.2f}','MOTOR',('post_motor_st_edge2','>=',v))
        add_gate(g,f'motor_st_vs4_ge_{v:.2f}','MOTOR',('post_motor_st_edge4','>=',v))
    return g

def conjunction_gates():
    g=[]
    # Attack scenario: boat3 must look at least neutral/strong in both stretch and start.
    exs=[
      ('ex_vs2_0',('post_ex_edge2','>=',0.0)),
      ('ex_vs2_2',('post_ex_edge2','>=',.02)),
      ('ex_inner_0',('post_ex_inner_edge','>=',0.0)),
      ('ex_field_1',('post_ex_field_edge','>=',.01)),
      ('ex_rank2',('post_ex_rank3','<=',2)),
    ]
    sts=[
      ('st_vs2_m2',('post_st_edge2','>=',-.02)),
      ('st_vs2_0',('post_st_edge2','>=',0.0)),
      ('st_vs2_2',('post_st_edge2','>=',.02)),
      ('st_inner_0',('post_st_inner_edge','>=',0.0)),
      ('st_rank2',('post_st_rank3','<=',2)),
    ]
    motors=[
      ('m_top2_vs2_0',('post_motor_gap2_top2','>=',0.0)),
      ('m_top2_vs2_3',('post_motor_gap2_top2','>=',.03)),
      ('m_rank_vs2_0',('post_motor_rank_edge2','>=',0.0)),
      ('m_inner_top2_0',('post_motor_inner_top2_gap','>=',0.0)),
      ('m_st_vs2_0',('post_motor_st_edge2','>=',0.0)),
    ]
    for en,ec in exs:
        for sn,sc in sts:
            add_gate(g,f'{en}__{sn}','EX_ST',ec,sc)
    for mn,mc in motors:
        for en,ec in exs:
            add_gate(g,f'{mn}__{en}','MOTOR_EX',mc,ec)
        for sn,sc in sts:
            add_gate(g,f'{mn}__{sn}','MOTOR_ST',mc,sc)

    # Focused three-way attack families, predeclared rather than arbitrary Cartesian products.
    triples=[
      ('m_top2_vs2_0__ex_vs2_0__st_vs2_0',
       ('post_motor_gap2_top2','>=',0.0),('post_ex_edge2','>=',0.0),('post_st_edge2','>=',0.0)),
      ('m_rank_vs2_0__ex_vs2_0__st_vs2_0',
       ('post_motor_rank_edge2','>=',0.0),('post_ex_edge2','>=',0.0),('post_st_edge2','>=',0.0)),
      ('m_top2_vs2_3__ex_vs2_0__st_vs2_0',
       ('post_motor_gap2_top2','>=',.03),('post_ex_edge2','>=',0.0),('post_st_edge2','>=',0.0)),
      ('m_top2_vs2_0__ex_rank2__st_rank2',
       ('post_motor_gap2_top2','>=',0.0),('post_ex_rank3','<=',2),('post_st_rank3','<=',2)),
      ('m_inner_top2_0__ex_inner_0__st_inner_0',
       ('post_motor_inner_top2_gap','>=',0.0),('post_ex_inner_edge','>=',0.0),('post_st_inner_edge','>=',0.0)),
    ]
    for name,*conds in triples:add_gate(g,name,'TRIPLE',*conds)
    return g

def build_gates():
    g=[{'name':'NONE','family':'PRE','conds':[]}]
    g.extend(primitive_gates());g.extend(conjunction_gates())
    # Deduplicate exact condition sets.
    out=[];seen=set()
    for z in g:
        k=tuple(tuple(x) for x in z['conds'])
        if k in seen:continue
        seen.add(k);out.append(z)
    return out

def metrics(mask,df):
    m=np.asarray(mask,bool);n=int(m.sum())
    if n==0:return {'n':0,'hits':0,'rate':None,'venues':0}
    y=df.y.to_numpy(dtype=int)
    return {'n':n,'hits':int(y[m].sum()),'rate':float(y[m].mean()),
            'venues':int(df.loc[m,'venue'].nunique())}

def eval_candidate(df,c,month):
    rn=pd.to_numeric(df.race_no,errors='coerce')
    pre=pd.to_numeric(df.pre_score,errors='coerce')
    lo,hi=c['band']
    mask=(rn>=lo)&(rn<=hi)&pre.notna()&(pre>=c['bq'])
    for cond in c['gate']['conds']:
        mask &= cond_mask(df,cond).fillna(False)
    d=df.date.dt.day
    split=14 if month=='feb' else 15
    return {'h1':metrics(mask&(d<=split),df),'h2':metrics(mask&(d>split),df)}

def combined(z):
    n=z['h1']['n']+z['h2']['n'];h=z['h1']['hits']+z['h2']['hits']
    return {'n':n,'hits':h,'rate':h/n if n else None}

def eligible(ms,lo=40,hi=70):
    for m in ['nov','dec','jan']:
        z=ms[m];n=z['h1']['n']+z['h2']['n']
        if n<lo or n>hi:return False
        for h in ['h1','h2']:
            if z[h]['n']<8 or z[h]['venues']<6 or z[h]['rate'] is None:return False
    return True

def summary(ms):
    rates=[ms[m][h]['rate'] for m in ['nov','dec','jan'] for h in ['h1','h2']]
    monthly={m:combined(ms[m]) for m in ['nov','dec','jan']}
    n=sum(x['n'] for x in monthly.values());h=sum(x['hits'] for x in monthly.values())
    valid=[r for r in rates if r is not None]
    persistent_worst=min(valid) if len(valid)==len(rates) else -1.0
    return {
      'persistent_worst':persistent_worst,
      'combined_n':n,'combined_hits':h,'combined_rate':h/n if n else None,
      'avg_month_n':sum(x['n'] for x in monthly.values())/3,
      'monthly':monthly
    }

def rank_key(z):
    s=z['summary']
    return (s['persistent_worst'],s['combined_rate'],-abs(s['avg_month_n']-50.0))

def main():
    canon=load_canonical()
    raw={}
    for m,(a,b) in {
      'oct':('2025-10-01','2025-10-31'),
      'nov':('2025-11-01','2025-11-30'),'dec':('2025-12-01','2025-12-31'),
      'jan':('2026-01-01','2026-01-31'),'feb':('2026-02-01','2026-02-28')}.items():
        x,r,audit=build_pre_enhanced(a,b,True);raw[m]=(x,r,audit)

    frames={m:prep_month(x,r) for m,(x,r,_) in raw.items()}

    # Canonicalize February reference universe exactly to the frozen settled artifact.
    cf=canon[(canon.date>='2026-02-01')&(canon.date<'2026-03-01')][['rc','date','settle__winner']].copy()
    fpre=raw['feb'][0].copy()
    frames['feb']=cf.merge(fpre.drop(columns=['date']),on='rc',how='inner')
    frames['feb']['y']=(pd.to_numeric(frames['feb'].settle__winner,errors='coerce')==3).astype(int)

    fc=cf.merge(raw['feb'][1][['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)!=3970 or agree<.999:
        raise RuntimeError(f'feb canonical/realtime mismatch n={len(fc)} agreement={agree}')

    prescores,enh_count=make_pre_scores(frames)
    days,cache=prefetch_sources()
    post,post_audit=build_motor_exhibition(days,cache)

    months={}
    for m in ['nov','dec','jan','feb']:
        q=prescores[m].merge(post,on=['rc','date'],how='left',validate='one_to_one')
        months[m]=q

    gates=build_gates()
    candidates=[]
    for band in BANDS:
        for bq in BROAD_QS:
            for gate in gates:
                candidates.append({'band':list(band),'bq':bq,'gate':gate})

    rows=[]
    for c in candidates:
        ms={m:eval_candidate(months[m],c,m) for m in ['nov','dec','jan']}
        s=summary(ms)
        rows.append({'candidate':c,'months':ms,'summary':s})

    strict=sorted([z for z in rows if eligible(z['months'],40,70)],key=rank_key,reverse=True)
    wide=sorted([z for z in rows if eligible(z['months'],30,80)],key=rank_key,reverse=True)

    by_family={}
    for fam in sorted({g['family'] for g in gates}):
        sp=[z for z in strict if z['candidate']['gate']['family']==fam]
        wp=[z for z in wide if z['candidate']['gate']['family']==fam]
        best=sp[0] if sp else (wp[0] if wp else None)
        ref=None
        if best:
            e=eval_candidate(months['feb'],best['candidate'],'feb')
            cc=combined(e)
            ref={'h1':e['h1'],'h2':e['h2'],**{f'combined_{k}':v for k,v in cc.items()}}
        by_family[fam]={
          'strict_count':len(sp),'wide_count':len(wp),
          'best_source':'strict_40_70' if sp else ('wide_30_80' if wp else None),
          'best_pre_feb':best,'feb_reference_non_pristine':ref
        }

    best=strict[0] if strict else (wide[0] if wide else None)
    bref=None
    if best:
        e=eval_candidate(months['feb'],best['candidate'],'feb');cc=combined(e)
        bref={'h1':e['h1'],'h2':e['h2'],**{f'combined_{k}':v for k,v in cc.items()}}

    out={
      'policy':{
        'manual_interpretable_gates_only':True,'second_stage_classifier_used':False,
        'motor_strict_prior_day':True,'same_day_results_used':False,
        'selection_nov_dec_jan_only':True,'february_reference_non_pristine':True,
        'march_outcomes_opened':False,'september_2026_outcomes_read':False,
        'production_v288_changed':False
      },
      'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
      'source_audit':{m:raw[m][2] for m in raw},
      'post_source_audit':post_audit,
      'feature_context':{'enhanced_pre_count':enh_count,'gate_count':len(gates)},
      'rows':{m:len(months[m]) for m in months},
      'common_ready':{m:int(pd.to_numeric(months[m].post_common_ready,errors='coerce').fillna(0).eq(1).sum()) for m in months},
      'candidate_count':len(candidates),
      'strict_40_70_count':len(strict),'wide_30_80_count':len(wide),
      'best_overall_pre_feb':best,
      'best_overall_feb_reference_non_pristine':bref,
      'by_family':by_family,
      'top25_strict':strict[:25],
      'top25_wide':wide[:25]
    }
    with open('research_3head_wave20_manual_gate_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
