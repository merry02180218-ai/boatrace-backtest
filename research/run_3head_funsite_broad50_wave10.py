from __future__ import annotations
import json, warnings
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier

from run_3head_funsite_broad50_wave6 import build_pre, load_canonical

warnings.filterwarnings("ignore")

WINDOWS=[14,21,28,42]
BANDS=[(1,4),(1,6),(1,8),(1,10),(1,12)]
QS=[.70,.75,.80,.85,.875,.90,.925,.95,.975]
SUPPORTS=[20,30,50,75,100,150,200]

# All inputs are PRE and oriented by add_signals so higher = better for boat 3.
GROUPS={
  'wall':[
    'sig_vs2_全国2連対率','sig_vs2_全国平均ST','sig_b2_wall_break'
  ],
  'inner':[
    'sig_vs1_全国2連対率','sig_vs1_全国平均ST',
    'sig_vs2_全国2連対率','sig_vs2_全国平均ST',
    'sig_b1_pressure','sig_b2_wall_break'
  ],
  'attack':[
    'sig_attack_player_inner','sig_attack_start_inner',
    'sig_attack_motor_inner','sig_attack_recent_inner'
  ],
  'counter':[
    'sig_vs4_全国2連対率','sig_vs4_全国平均ST','sig_b4_counter_margin'
  ]
}

def pct_ref(ref,x):
    a=np.asarray(ref,float);a=a[np.isfinite(a)];a=np.sort(a)
    xx=np.asarray(x,float)
    out=np.full(len(xx),np.nan)
    if len(a)==0:return out
    ok=np.isfinite(xx)
    out[ok]=np.searchsorted(a,xx[ok],side='right')/len(a)
    return out

def gm(a):
    a=np.asarray(a,float)
    with np.errstate(invalid='ignore'):
        return np.exp(np.nanmean(np.log(np.clip(a,1e-6,1.0)),axis=1))

def harmonic(a):
    a=np.asarray(a,float)
    valid=np.isfinite(a)
    den=np.nansum(np.where(valid,1.0/np.clip(a,1e-6,1.0),np.nan),axis=1)
    cnt=valid.sum(axis=1)
    return np.divide(cnt,den,out=np.full(len(a),np.nan),where=(cnt>0)&(den>0))

def rowmin(a):
    a=np.asarray(a,float)
    return np.nanmin(a,axis=1)

def normalized_signal(train,target,c,positive_gate=False):
    tr=pd.to_numeric(train[c],errors='coerce').to_numpy(float)
    tx=pd.to_numeric(target[c],errors='coerce').to_numpy(float)
    p=pct_ref(tr,tx)
    if positive_gate:
        p=np.where(np.isfinite(tx)&(tx>0),p,0.0)
    return p

def derive_scenarios(train,target,positive_gate=False):
    comps={}
    group_members={}
    for g,cols in GROUPS.items():
        avail=[c for c in cols if c in train.columns and c in target.columns and
               pd.to_numeric(train[c],errors='coerce').notna().sum()>=50]
        if not avail:continue
        mat=np.column_stack([normalized_signal(train,target,c,positive_gate) for c in avail])
        group_members[g]=avail
        comps[g+'_gm']=gm(mat)
        comps[g+'_min']=rowmin(mat)
        comps[g+'_harm']=harmonic(mat)

    # Select one core form for cross-component nonlinear interactions.
    core_names=[g+'_gm' for g in ['wall','inner','attack','counter'] if g+'_gm' in comps]
    if len(core_names)>=2:
        core=np.column_stack([comps[n] for n in core_names])
        comps['scenario_geom']=gm(core)
        comps['scenario_min']=rowmin(core)
        comps['scenario_harm']=harmonic(core)

    def mul(name,*names):
        if all(n in comps for n in names):
            v=np.ones(len(target),float)
            for n in names:v*=comps[n]
            comps[name]=v

    mul('wall_x_attack','wall_gm','attack_gm')
    mul('inner_x_attack','inner_gm','attack_gm')
    mul('attack_x_counter','attack_gm','counter_gm')
    mul('wall_x_counter','wall_gm','counter_gm')
    mul('wall_x_inner','wall_gm','inner_gm')
    mul('wall_inner_attack','wall_gm','inner_gm','attack_gm')
    mul('wall_attack_counter','wall_gm','attack_gm','counter_gm')
    mul('fourway_product','wall_gm','inner_gm','attack_gm','counter_gm')

    return pd.DataFrame(comps,index=target.index),group_members

def model_pair():
    logit=make_pipeline(
      SimpleImputer(strategy='median'),StandardScaler(),
      LogisticRegression(C=.10,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=101)
    )
    hist=make_pipeline(
      SimpleImputer(strategy='median'),
      HistGradientBoostingClassifier(max_iter=170,max_leaf_nodes=9,l2_regularization=4,
                                     learning_rate=.04,random_state=101)
    )
    return logit,hist

def metric(mask,frame):
    m=np.asarray(mask,bool);y=frame.y.to_numpy(dtype=int);n=int(m.sum())
    return {'n':n,'hits':int(y[m].sum()) if n else 0,
            'rate':float(y[m].mean()) if n else None,
            'venues':int(frame.loc[m,'venue'].nunique()) if n else 0}

def weekly(mask,frame):
    d=frame.date.dt.day.to_numpy();out=[]
    for lo,hi in [(1,7),(8,14),(15,21),(22,28)]:
        m=np.asarray(mask,bool)&(d>=lo)&(d<=hi)
        z=metric(m,frame);z['week']=f'{lo:02d}-{hi:02d}';out.append(z)
    return out

def walk_predictions(history,target):
    rows=[]
    target=target.sort_values(['date','rc']).copy()
    for dayv in sorted(target.date.dt.normalize().unique()):
        day=pd.Timestamp(dayv)
        today=target[target.date.dt.normalize()==day].copy()
        for window in WINDOWS:
            tr=history[(history.date<day)&(history.date>=day-pd.Timedelta(days=window))].copy()
            if len(tr)<500 or tr.y.nunique()<2:continue
            for gate_name,positive_gate in [('pct',False),('positive',True)]:
                xtr,_=derive_scenarios(tr,tr,positive_gate)
                xt,_=derive_scenarios(tr,today,positive_gate)
                common=[c for c in xtr.columns if c in xt.columns and xtr[c].notna().sum()>=100]
                if len(common)<8:continue
                xtr=xtr[common];xt=xt[common]

                logit,hist=model_pair()
                logit.fit(xtr,tr.y);hist.fit(xtr,tr.y)
                lp=pct_ref(logit.predict_proba(xtr)[:,1],logit.predict_proba(xt)[:,1])
                hp=pct_ref(hist.predict_proba(xtr)[:,1],hist.predict_proba(xt)[:,1])

                base=today[['rc','date','venue','race_no','y']].copy()
                base['window']=window;base['gate_mode']=gate_name
                base['p_logit']=lp;base['p_hist']=hp;base['p_mean']=(lp+hp)/2
                for c in common:
                    # Convert every scenario feature itself to a trailing-training percentile,
                    # so gates have a stable 0-1 meaning.
                    base['s_'+c]=pct_ref(xtr[c].to_numpy(float),xt[c].to_numpy(float))
                rows.append(base)
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()

def mask_candidate(sub,c):
    rn=pd.to_numeric(sub.race_no,errors='coerce').to_numpy()
    lo,hi=c['band'];m=(rn>=lo)&(rn<=hi)
    if c['kind']=='scenario':
        m &= pd.to_numeric(sub['s_'+c['scenario']],errors='coerce').to_numpy()>=c['q']
    elif c['kind']=='model':
        m &= pd.to_numeric(sub[c['model']],errors='coerce').to_numpy()>=c['q']
    elif c['kind']=='scenario_model':
        m &= pd.to_numeric(sub['s_'+c['scenario']],errors='coerce').to_numpy()>=c['sq']
        m &= pd.to_numeric(sub[c['model']],errors='coerce').to_numpy()>=c['mq']
    elif c['kind']=='scenario_pair':
        m &= pd.to_numeric(sub['s_'+c['s1']],errors='coerce').to_numpy()>=c['q1']
        m &= pd.to_numeric(sub['s_'+c['s2']],errors='coerce').to_numpy()>=c['q2']
    return m

def candidate_universe(pred):
    out=[]
    for window in WINDOWS:
      for gate_mode in ['pct','positive']:
        sub=pred[(pred.window==window)&(pred.gate_mode==gate_mode)]
        if len(sub)==0:continue
        scenarios=[c[2:] for c in sub.columns if c.startswith('s_')]
        preferred_pairs=[
          ('wall_gm','attack_gm'),('inner_gm','attack_gm'),
          ('attack_gm','counter_gm'),('wall_gm','counter_gm'),
          ('scenario_geom','scenario_min'),('wall_x_attack','attack_x_counter')
        ]
        preferred_pairs=[p for p in preferred_pairs if p[0] in scenarios and p[1] in scenarios]
        for band in BANDS:
          for s in scenarios:
            for q in QS:
              out.append({'kind':'scenario','window':window,'gate_mode':gate_mode,'band':list(band),'scenario':s,'q':q})
          for model_name in ['p_logit','p_hist','p_mean']:
            for q in [.75,.80,.85,.875,.90,.925,.95,.975]:
              out.append({'kind':'model','window':window,'gate_mode':gate_mode,'band':list(band),'model':model_name,'q':q})
          for s in scenarios:
            for sq in [.80,.85,.90,.925,.95]:
              for model_name in ['p_logit','p_hist','p_mean']:
                for mq in [.80,.85,.90,.925,.95]:
                  out.append({'kind':'scenario_model','window':window,'gate_mode':gate_mode,'band':list(band),
                              'scenario':s,'sq':sq,'model':model_name,'mq':mq})
          for s1,s2 in preferred_pairs:
            for q1 in [.75,.80,.85,.90,.925]:
              for q2 in [.75,.80,.85,.90,.925]:
                out.append({'kind':'scenario_pair','window':window,'gate_mode':gate_mode,'band':list(band),
                            's1':s1,'q1':q1,'s2':s2,'q2':q2})
    return out

def build_eval_cache(pred):
    cache={}
    for window in WINDOWS:
      for gate_mode in ['pct','positive']:
        sub=pred[(pred.window==window)&(pred.gate_mode==gate_mode)].copy()
        if len(sub)==0:continue
        venues=pd.factorize(sub.venue.astype(str))[0]
        arrays={
          'sub':sub,
          'rn':pd.to_numeric(sub.race_no,errors='coerce').to_numpy(float),
          'day':sub.date.dt.day.to_numpy(),
          'y':sub.y.to_numpy(dtype=int),
          'venue_codes':venues,
        }
        for col in sub.columns:
            if col.startswith('s_') or col in ['p_logit','p_hist','p_mean']:
                arrays[col]=pd.to_numeric(sub[col],errors='coerce').to_numpy(float)
        cache[(window,gate_mode)]=arrays
    return cache

def fast_metric(mask,arr):
    m=np.asarray(mask,bool);n=int(m.sum());y=arr['y']
    return {'n':n,'hits':int(y[m].sum()) if n else 0,
            'rate':float(y[m].mean()) if n else None,
            'venues':int(np.unique(arr['venue_codes'][m]).size) if n else 0}

def evaluate_fast(cache,c):
    arr=cache[(c['window'],c['gate_mode'])]
    rn=arr['rn'];lo,hi=c['band'];m=(rn>=lo)&(rn<=hi)
    if c['kind']=='scenario':
        m &= arr['s_'+c['scenario']]>=c['q']
    elif c['kind']=='model':
        m &= arr[c['model']]>=c['q']
    elif c['kind']=='scenario_model':
        m &= arr['s_'+c['scenario']]>=c['sq']
        m &= arr[c['model']]>=c['mq']
    else:
        m &= arr['s_'+c['s1']]>=c['q1']
        m &= arr['s_'+c['s2']]>=c['q2']
    day=arr['day']
    z=dict(c)
    z['h1']=fast_metric(m&(day<=14),arr);z['h2']=fast_metric(m&(day>=15),arr)
    weeks=[]
    for lo2,hi2 in [(1,7),(8,14),(15,21),(22,28)]:
        w=fast_metric(m&(day>=lo2)&(day<=hi2),arr);w['week']=f'{lo2:02d}-{hi2:02d}';weeks.append(w)
    z['weeks']=weeks
    return z

def summarize(z):
    if z is None:return None
    a,b=z['h1'],z['h2'];n=a['n']+b['n'];hits=a['hits']+b['hits']
    eligible=[w for w in z['weeks'] if w['n']>=5 and w['rate'] is not None]
    return {**z,
      'worst_half_rate':min(a['rate'],b['rate']),
      'combined_n':n,'combined_hits':hits,'combined_rate':hits/n if n else None,
      'eligible_week_min_rate':min((w['rate'] for w in eligible),default=None),
      'eligible_week_mean_rate':sum(w['rate'] for w in eligible)/len(eligible) if eligible else None
    }

def main():
    canon=load_canonical()
    jan,jres,ja=build_pre('2026-01-01','2026-01-31',True)
    feb,fres,fa=build_pre('2026-02-01','2026-02-28',True)

    fc=canon[canon.date<'2026-03-01'].merge(fres[['rc','result_winner']],on='rc',how='inner')
    agree=float((pd.to_numeric(fc.settle__winner,errors='coerce')==fc.result_winner).mean()) if len(fc) else 0.0
    if len(fc)<3000 or agree<.995:raise RuntimeError(f'winner cross-check failed n={len(fc)} agreement={agree}')

    jan=jan.merge(jres[['rc','result_winner']],on='rc',how='inner')
    jan['y']=(jan.result_winner==3).astype(int)
    feb=canon[canon.date<'2026-03-01'][['rc','date','settle__winner']].merge(feb.drop(columns=['date']),on='rc',how='inner')
    feb['y']=(pd.to_numeric(feb.settle__winner,errors='coerce')==3).astype(int)

    history=pd.concat([jan,feb],ignore_index=True,sort=False)
    pred=walk_predictions(history,feb)
    universe=candidate_universe(pred)
    eval_cache=build_eval_cache(pred)
    evals=[evaluate_fast(eval_cache,c) for c in universe]

    frontier={}
    for mn in SUPPORTS:
        pool=[z for z in evals if z['h1']['n']>=mn and z['h2']['n']>=mn and
              z['h1']['venues']>=8 and z['h2']['venues']>=8 and
              z['h1']['rate'] is not None and z['h2']['rate'] is not None]
        if not pool:
            frontier[str(mn)]={'candidate_count':0,'best_worst_half':None,'best_combined':None}
            continue
        bw=max(pool,key=lambda z:(min(z['h1']['rate'],z['h2']['rate']),
                                  (z['h1']['hits']+z['h2']['hits'])/(z['h1']['n']+z['h2']['n']),
                                  z['h1']['n']+z['h2']['n']))
        bc=max(pool,key=lambda z:((z['h1']['hits']+z['h2']['hits'])/(z['h1']['n']+z['h2']['n']),
                                  min(z['h1']['rate'],z['h2']['rate']),
                                  z['h1']['n']+z['h2']['n']))
        frontier[str(mn)]={'candidate_count':len(pool),'best_worst_half':summarize(bw),'best_combined':summarize(bc)}

    out={
      'policy':{
        'existing_pre_only':True,'nonlinear_interactions_predeclared':True,
        'daily_walk_forward':True,'february_only_diagnostic':True,
        'march_outcomes_opened':False,'september_outcomes_read':False,
        'production_v288_changed':False
      },
      'cross_source_feb_winner_check':{'n':len(fc),'agreement':agree},
      'source_audit':{'jan':ja,'feb':fa},
      'rows':{'jan':len(jan),'feb':len(feb),'prediction_rows':len(pred)},
      'candidate_count':len(evals),
      'support_frontier':frontier,
      'wave9_baseline_worst_half':{
        '20':0.391304347826087,'30':0.375,'50':0.34408602150537637,
        '75':0.34408602150537637,'100':0.3235294117647059,
        '150':0.2974137931034483,'200':0.27611940298507465
      }
    }
    for k,v in frontier.items():
        b=v['best_worst_half']
        if b is not None:
            out.setdefault('improvement_vs_wave9',{})[k]=b['worst_half_rate']-out['wave9_baseline_worst_half'][k]
    with open('research_3head_funsite_broad50_wave10_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
