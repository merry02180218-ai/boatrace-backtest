from __future__ import annotations
import json
import numpy as np
import pandas as pd

from run_3head_funsite_broad50_wave2 import load_data, wave2_model, MODEL_NAMES

BANDS=[(1,4),(1,6),(1,8)]
QS=[.70,.75,.80,.85,.90,.925,.95,.975]
MODEL_Q=[.75,.80,.85,.90,.925,.95]
MODEL_K=[2,3,4,5]
SIGNALS=[
    'sig_vs2_全国2連対率',
    'sig_vs2_全国平均ST',
    'sig_attack_player_inner',
    'sig_b1_pressure',
    'sig_b4_counter_margin',
    'sig_attack_motor_inner',
    'sig_attack_recent_inner',
    'sig_rank_全国2連対率',
    'sig_rank_全国平均ST',
]

def metric(mask,frame):
    m=np.asarray(mask,bool); y=frame.y.to_numpy(dtype=int); n=int(m.sum())
    return {'n':n,'hits':int(y[m].sum()) if n else 0,
            'rate':float(y[m].mean()) if n else None,
            'venues':int(frame.loc[m,'venue'].nunique()) if n else 0}

def split_feb(d):
    feb=d[d.date<'2026-03-01'].sort_values(['date','rc']).copy()
    mar=d[d.date>='2026-03-01'].sort_values(['date','rc']).copy()
    tr=feb[feb.date<'2026-02-15'].copy()
    v1=feb[(feb.date>='2026-02-15')&(feb.date<'2026-02-22')].copy()
    v2=feb[feb.date>='2026-02-22'].copy()
    return feb,mar,tr,v1,v2

def numeric_features(d):
    ex={'rc','venue','date','settle__winner','y'}
    return [c for c in d.columns if c not in ex and pd.api.types.is_numeric_dtype(d[c]) and d[c].notna().sum()>=30]

def in_band(frame,band):
    rn=pd.to_numeric(frame.race_no,errors='coerce').to_numpy()
    return (rn>=band[0])&(rn<=band[1])

def pct_ref(ref,x):
    a=np.asarray(ref,float); a=a[np.isfinite(a)]
    if len(a)==0:return np.full(len(x),np.nan)
    a=np.sort(a)
    xx=np.asarray(x,float)
    out=np.searchsorted(a,xx,side='right')/len(a)
    out[~np.isfinite(xx)]=np.nan
    return out

def band_signal_context(tr,band):
    sub=tr.loc[in_band(tr,band)].copy()
    refs={}
    for c in SIGNALS:
        if c in sub.columns:
            refs[c]=pd.to_numeric(sub[c],errors='coerce').to_numpy()
    return sub,refs

def signal_matrix(frame,refs):
    cols=[]
    used=[]
    for c in SIGNALS:
        if c in refs and c in frame.columns:
            cols.append(pct_ref(refs[c],pd.to_numeric(frame[c],errors='coerce').to_numpy()))
            used.append(c)
    return np.column_stack(cols),used

def score_from_weights(frame,refs,weights):
    mat,used=signal_matrix(frame,refs)
    w=np.array([weights.get(c,0.0) for c in used],float)
    valid=np.isfinite(mat)
    num=np.nansum(mat*w,axis=1)
    den=np.nansum(valid*w,axis=1)
    return np.divide(num,den,out=np.full(len(frame),np.nan),where=den>0)

def weight_grid():
    rows=[]
    for wa in [1.5,2.0,2.5]:
      for wb in [1.5,2.0,2.5]:
       for wc in [.5,1.0,1.5]:
        for wd in [0,.5]:
         for we in [0,.5]:
          for wf in [0,.5]:
           for wg in [0,.5]:
            w={
              'sig_vs2_全国2連対率':wa,
              'sig_vs2_全国平均ST':wb,
              'sig_attack_player_inner':wc,
              'sig_b1_pressure':wd,
              'sig_b4_counter_margin':we,
              'sig_attack_motor_inner':wf,
              'sig_attack_recent_inner':wg,
              'sig_rank_全国2連対率':.5,
              'sig_rank_全国平均ST':.5,
            }
            rows.append(w)
    return rows

def fit_band_models(tr,band,feats):
    btr=tr.loc[in_band(tr,band)].copy()
    models={}
    train_scores={}
    for n in MODEL_NAMES:
        m=wave2_model(n);m.fit(btr[feats],btr.y)
        models[n]=m
        train_scores[n]=m.predict_proba(btr[feats])[:,1]
    return btr,models,train_scores

def model_consensus(frame,band,models,train_scores,q,k):
    bm=in_band(frame,band)
    idx=np.where(bm)[0]
    out=np.zeros(len(frame),dtype=bool)
    if len(idx)==0:return out
    sub=frame.iloc[idx]
    votes=np.zeros(len(sub),dtype=int)
    for n,m in models.items():
        s=m.predict_proba(sub[FEATS])[:,1]
        p=pct_ref(train_scores[n],s)
        votes += (p>=q)
    out[idx]=votes>=k
    return out

def attack_mask(frame,band,refs,weights,threshold):
    bm=in_band(frame,band)
    score=score_from_weights(frame,refs,weights)
    return bm & np.isfinite(score) & (score>=threshold)

def candidate_key(z):
    return (min(z['v1']['rate'] or 0,z['v2']['rate'] or 0),
            z['v1']['n']+z['v2']['n'],
            min(z['v1']['n'],z['v2']['n']),
            z['v1']['venues']+z['v2']['venues'])

def usable(z,min_n=8):
    return z['v1']['n']>=min_n and z['v2']['n']>=min_n and z['v1']['venues']>=5 and z['v2']['venues']>=5

def freeze(rows,target):
    strict=[z for z in rows if usable(z,12) and z['v1']['rate'] is not None and z['v2']['rate'] is not None
            and z['v1']['rate']>=target and z['v2']['rate']>=target]
    relaxed=[z for z in rows if usable(z,15) and z['v1']['rate'] is not None and z['v2']['rate'] is not None
             and z['v1']['rate']>=target-.03 and z['v2']['rate']>=target-.03
             and (z['v1']['hits']+z['v2']['hits'])/(z['v1']['n']+z['v2']['n'])>=target-.02]
    pool=strict if strict else relaxed
    if not pool:return None
    best=max(pool,key=lambda z:(z['v1']['n']+z['v2']['n'],min(z['v1']['rate'],z['v2']['rate']),z['v1']['venues']+z['v2']['venues']))
    out=dict(best);out['strict']=bool(strict)
    return out

def march_eval(cand,mar,contexts):
    ctx=contexts[tuple(cand['band'])]
    if cand['kind']=='attack_score':
        m=attack_mask(mar,tuple(cand['band']),ctx['refs'],cand['weights'],cand['threshold'])
    elif cand['kind']=='model_consensus':
        m=model_consensus(mar,tuple(cand['band']),ctx['models'],ctx['train_scores'],cand['q'],cand['k'])
    else:
        a=attack_mask(mar,tuple(cand['band']),ctx['refs'],cand['weights'],cand['threshold'])
        b=model_consensus(mar,tuple(cand['band']),ctx['models'],ctx['train_scores'],cand['q'],cand['k'])
        m=a&b
    sel=mar.loc[m].sort_values(['date','rc']).copy()
    n=len(sel);h=n//2
    return {'n':n,'hits':int(sel.y.sum()),'rate':float(sel.y.mean()) if n else None,
            'early_n':h,'early_hits':int(sel.iloc[:h].y.sum()),
            'late_n':n-h,'late_hits':int(sel.iloc[h:].y.sum()),
            'venue_count':int(sel.venue.nunique()) if n else 0}

def main():
    global FEATS
    d,_=load_data()
    feb,mar,tr,v1,v2=split_feb(d)
    FEATS=numeric_features(d)
    contexts={}
    rows=[]
    wg=weight_grid()

    for band in BANDS:
        btr,refs=band_signal_context(tr,band)
        if len(btr)<200:continue
        _,models,train_scores=fit_band_models(tr,band,FEATS)
        contexts[band]={'refs':refs,'models':models,'train_scores':train_scores}

        # Continuous attack-score family.
        attack_rows=[]
        for weights in wg:
            st=score_from_weights(btr,refs,weights)
            finite=st[np.isfinite(st)]
            if len(finite)<100:continue
            for q in QS:
                th=float(np.nanquantile(finite,q))
                m1=attack_mask(v1,band,refs,weights,th)
                m2=attack_mask(v2,band,refs,weights,th)
                z={'kind':'attack_score','band':list(band),'q':q,'threshold':th,'weights':weights,
                   'v1':metric(m1,v1),'v2':metric(m2,v2)}
                if usable(z,8):
                    attack_rows.append(z);rows.append(z)

        # Dedicated early-race model consensus.
        model_rows=[]
        for q in MODEL_Q:
            for k in MODEL_K:
                m1=model_consensus(v1,band,models,train_scores,q,k)
                m2=model_consensus(v2,band,models,train_scores,q,k)
                z={'kind':'model_consensus','band':list(band),'q':q,'k':k,
                   'v1':metric(m1,v1),'v2':metric(m2,v2)}
                if usable(z,8):
                    model_rows.append(z);rows.append(z)

        # Attack score + specialist model consensus.
        top_attack=sorted(attack_rows,key=candidate_key,reverse=True)[:60]
        for a in top_attack:
            for q in [.75,.80,.85,.90]:
                for k in [2,3,4]:
                    m1=attack_mask(v1,band,refs,a['weights'],a['threshold']) & model_consensus(v1,band,models,train_scores,q,k)
                    m2=attack_mask(v2,band,refs,a['weights'],a['threshold']) & model_consensus(v2,band,models,train_scores,q,k)
                    z={'kind':'attack_model','band':list(band),'score_q':a['q'],'threshold':a['threshold'],
                       'weights':a['weights'],'q':q,'k':k,'v1':metric(m1,v1),'v2':metric(m2,v2)}
                    if usable(z,8):rows.append(z)

    rows=sorted(rows,key=candidate_key,reverse=True)
    strict50=[z for z in rows if usable(z,12) and z['v1']['rate'] is not None and z['v2']['rate'] is not None
              and z['v1']['rate']>=.50 and z['v2']['rate']>=.50]
    near50=[z for z in rows if usable(z,12) and z['v1']['rate'] is not None and z['v2']['rate'] is not None
            and z['v1']['rate']>=.47 and z['v2']['rate']>=.47]

    frozen={str(t):freeze(rows,t) for t in [.50,.45,.40]}
    march={k:(None if z is None else march_eval(z,mar,contexts)) for k,z in frozen.items()}

    out={
      'policy':{'feb_only_selection':True,'march_one_shot':True,'september_outcomes_read':False,
                'production_v288_changed':False,'wave4_motivated_by_wave3_feb_only':True},
      'split':{'train_n':len(tr),'v1_n':len(v1),'v2_n':len(v2),'feb_n':len(feb),'march_n':len(mar)},
      'features':len(FEATS),'candidate_count':len(rows),
      'strict50_count':len(strict50),'near50_count':len(near50),
      'strict50_frontier':strict50[:30],'near50_frontier':near50[:30],
      'overall_frontier':rows[:50],'frozen':frozen,'march_results':march
    }
    with open('research_3head_funsite_broad50_wave4_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
