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

def band_mask(frame,band):
    rn=pd.to_numeric(frame.race_no,errors='coerce').to_numpy()
    return (rn>=band[0])&(rn<=band[1])

def pct_ref_sorted(sorted_ref,x):
    xx=np.asarray(x,float)
    out=np.searchsorted(sorted_ref,xx,side='right')/max(1,len(sorted_ref))
    out[~np.isfinite(xx)]=np.nan
    return out

def make_signal_context(tr,frames,band):
    bt=band_mask(tr,band)
    refs={}
    used=[]
    for c in SIGNALS:
        if c not in tr.columns:continue
        a=pd.to_numeric(tr.loc[bt,c],errors='coerce').to_numpy(dtype=float)
        a=a[np.isfinite(a)]
        if len(a)<50:continue
        refs[c]=np.sort(a);used.append(c)
    mats={}
    for key,frame in frames.items():
        cols=[]
        for c in used:
            x=pd.to_numeric(frame[c],errors='coerce').to_numpy(dtype=float)
            cols.append(pct_ref_sorted(refs[c],x))
        mats[key]=np.column_stack(cols)
    return used,mats

def score_matrix(mat,w):
    valid=np.isfinite(mat)
    num=np.nansum(mat*w,axis=1)
    den=np.sum(valid*w,axis=1)
    return np.divide(num,den,out=np.full(len(mat),np.nan),where=den>0)

def weight_grid(used):
    support_patterns=[
      {},
      {'sig_b1_pressure':.5},
      {'sig_b4_counter_margin':.5},
      {'sig_attack_motor_inner':.5},
      {'sig_attack_recent_inner':.5},
      {'sig_b1_pressure':.5,'sig_b4_counter_margin':.5},
      {'sig_attack_motor_inner':.5,'sig_attack_recent_inner':.5},
    ]
    rows=[]
    for wa in [1.5,2.0,2.5]:
      for wb in [1.5,2.0,2.5]:
       for wc in [.5,1.0,1.5]:
        for sp in support_patterns:
         d={
           'sig_vs2_全国2連対率':wa,
           'sig_vs2_全国平均ST':wb,
           'sig_attack_player_inner':wc,
           'sig_rank_全国2連対率':.5,
           'sig_rank_全国平均ST':.5,
         }
         d.update(sp)
         rows.append({c:float(d.get(c,0.0)) for c in used})
    return rows

def make_model_context(tr,frames,band,feats):
    bt=band_mask(tr,band)
    btr=tr.loc[bt].copy()
    percs={key:[] for key in frames}
    for n in MODEL_NAMES:
        m=wave2_model(n);m.fit(btr[feats],btr.y)
        sr=m.predict_proba(btr[feats])[:,1]
        sr=np.sort(sr[np.isfinite(sr)])
        for key,frame in frames.items():
            s=m.predict_proba(frame[feats])[:,1]
            percs[key].append(pct_ref_sorted(sr,s))
    stacks={k:np.column_stack(v) for k,v in percs.items()}
    gates={}
    for q in MODEL_Q:
        for k in MODEL_K:
            gates[(q,k)]={key:((arr>=q).sum(axis=1)>=k) for key,arr in stacks.items()}
    return gates

def usable(z,min_n=8):
    return z['v1']['n']>=min_n and z['v2']['n']>=min_n and z['v1']['venues']>=5 and z['v2']['venues']>=5

def candidate_key(z):
    return (min(z['v1']['rate'] or 0,z['v2']['rate'] or 0),
            z['v1']['n']+z['v2']['n'],
            min(z['v1']['n'],z['v2']['n']),
            z['v1']['venues']+z['v2']['venues'])

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

def public_candidate(z):
    return {k:v for k,v in z.items() if not k.startswith('_')}

def main():
    d,_=load_data()
    feb,mar,tr,v1,v2=split_feb(d)
    feats=numeric_features(d)
    frames={'tr':tr,'v1':v1,'v2':v2,'mar':mar}
    contexts={}
    rows=[]

    for band in BANDS:
        bt=band_mask(tr,band)
        if int(bt.sum())<200:continue
        used,mats=make_signal_context(tr,frames,band)
        gates=make_model_context(tr,frames,band,feats)
        bm={key:band_mask(frame,band) for key,frame in frames.items()}
        contexts[band]={'used':used,'mats':mats,'gates':gates,'bm':bm}

        attack_rows=[]
        for weights in weight_grid(used):
            w=np.array([weights[c] for c in used],float)
            scores={key:score_matrix(mat,w) for key,mat in mats.items()}
            ref=scores['tr'][bm['tr']]
            ref=ref[np.isfinite(ref)]
            if len(ref)<100:continue
            for q in QS:
                th=float(np.quantile(ref,q))
                masks={key:(bm[key]&np.isfinite(scores[key])&(scores[key]>=th)) for key in ['v1','v2','mar']}
                z={'kind':'attack_score','band':list(band),'q':q,'threshold':th,'weights':weights,
                   'v1':metric(masks['v1'],v1),'v2':metric(masks['v2'],v2),
                   '_mar_mask':masks['mar']}
                if usable(z,8):
                    attack_rows.append(z);rows.append(z)

        for (q,k),gm in gates.items():
            z={'kind':'model_consensus','band':list(band),'q':q,'k':k,
               'v1':metric(bm['v1']&gm['v1'],v1),'v2':metric(bm['v2']&gm['v2'],v2),
               '_mar_mask':bm['mar']&gm['mar']}
            if usable(z,8):rows.append(z)

        top_attack=sorted(attack_rows,key=candidate_key,reverse=True)[:40]
        for a in top_attack:
            w=np.array([a['weights'][c] for c in used],float)
            sv1=score_matrix(mats['v1'],w);sv2=score_matrix(mats['v2'],w);sm=score_matrix(mats['mar'],w)
            am1=bm['v1']&np.isfinite(sv1)&(sv1>=a['threshold'])
            am2=bm['v2']&np.isfinite(sv2)&(sv2>=a['threshold'])
            amm=bm['mar']&np.isfinite(sm)&(sm>=a['threshold'])
            for q in [.75,.80,.85,.90]:
                for k in [2,3,4]:
                    gm=gates[(q,k)]
                    z={'kind':'attack_model','band':list(band),'score_q':a['q'],'threshold':a['threshold'],
                       'weights':a['weights'],'q':q,'k':k,
                       'v1':metric(am1&gm['v1'],v1),'v2':metric(am2&gm['v2'],v2),
                       '_mar_mask':amm&gm['mar']}
                    if usable(z,8):rows.append(z)

    rows=sorted(rows,key=candidate_key,reverse=True)
    strict50=[z for z in rows if usable(z,12) and z['v1']['rate'] is not None and z['v2']['rate'] is not None
              and z['v1']['rate']>=.50 and z['v2']['rate']>=.50]
    near50=[z for z in rows if usable(z,12) and z['v1']['rate'] is not None and z['v2']['rate'] is not None
            and z['v1']['rate']>=.47 and z['v2']['rate']>=.47]

    frozen_raw={str(t):freeze(rows,t) for t in [.50,.45,.40]}
    march={}
    frozen={}
    for key,z in frozen_raw.items():
        if z is None:
            frozen[key]=None;march[key]=None;continue
        m=z['_mar_mask'];sel=mar.loc[m].sort_values(['date','rc']).copy();n=len(sel);h=n//2
        frozen[key]=public_candidate(z)
        march[key]={'n':n,'hits':int(sel.y.sum()),'rate':float(sel.y.mean()) if n else None,
                    'early_n':h,'early_hits':int(sel.iloc[:h].y.sum()),
                    'late_n':n-h,'late_hits':int(sel.iloc[h:].y.sum()),
                    'venue_count':int(sel.venue.nunique()) if n else 0}

    out={
      'policy':{'feb_only_selection':True,'march_one_shot':True,'september_outcomes_read':False,
                'production_v288_changed':False,'wave4_motivated_by_wave3_feb_only':True,
                'cached_computation_only_no_research_gate_change':True},
      'split':{'train_n':len(tr),'v1_n':len(v1),'v2_n':len(v2),'feb_n':len(feb),'march_n':len(mar)},
      'features':len(feats),'candidate_count':len(rows),
      'strict50_count':len(strict50),'near50_count':len(near50),
      'strict50_frontier':[public_candidate(z) for z in strict50[:30]],
      'near50_frontier':[public_candidate(z) for z in near50[:30]],
      'overall_frontier':[public_candidate(z) for z in rows[:50]],
      'frozen':frozen,'march_results':march
    }
    with open('research_3head_funsite_broad50_wave4_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
