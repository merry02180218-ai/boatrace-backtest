from __future__ import annotations
import json
import numpy as np

from run_3head_funsite_broad50_wave2 import load_data
from run_3head_funsite_broad50_wave4 import (
    BANDS, QS, MODEL_Q, MODEL_K, split_feb, numeric_features, band_mask,
    make_signal_context, make_model_context, weight_grid, score_matrix, metric,
    usable, candidate_key
)

def strict50(z):
    return usable(z,12) and z['v1']['rate'] is not None and z['v2']['rate'] is not None and z['v1']['rate']>=.50 and z['v2']['rate']>=.50

def public(z):
    return {k:v for k,v in z.items() if not k.startswith('_')}

def generate_wave4_strict(d):
    feb,mar,tr,v1,v2=split_feb(d)
    feats=numeric_features(d)
    frames={'tr':tr,'v1':v1,'v2':v2,'mar':mar}
    rows=[]
    for band in BANDS:
        bt=band_mask(tr,band)
        if int(bt.sum())<200:continue
        used,mats=make_signal_context(tr,frames,band)
        gates=make_model_context(tr,frames,band,feats)
        bm={key:band_mask(frame,band) for key,frame in frames.items()}

        attack_rows=[]
        for weights in weight_grid(used):
            w=np.array([weights[c] for c in used],float)
            scores={key:score_matrix(mat,w) for key,mat in mats.items()}
            ref=scores['tr'][bm['tr']]
            ref=ref[np.isfinite(ref)]
            if len(ref)<100:continue
            for q in QS:
                th=float(np.quantile(ref,q))
                m1=bm['v1']&np.isfinite(scores['v1'])&(scores['v1']>=th)
                m2=bm['v2']&np.isfinite(scores['v2'])&(scores['v2']>=th)
                mm=bm['mar']&np.isfinite(scores['mar'])&(scores['mar']>=th)
                z={'kind':'attack_score','band':list(band),'q':q,'threshold':th,'weights':weights,
                   'v1':metric(m1,v1),'v2':metric(m2,v2),'_m1':m1,'_m2':m2,'_mm':mm}
                if usable(z,8):
                    attack_rows.append(z);rows.append(z)

        for (q,k),gm in gates.items():
            m1=bm['v1']&gm['v1'];m2=bm['v2']&gm['v2'];mm=bm['mar']&gm['mar']
            z={'kind':'model_consensus','band':list(band),'q':q,'k':k,
               'v1':metric(m1,v1),'v2':metric(m2,v2),'_m1':m1,'_m2':m2,'_mm':mm}
            if usable(z,8):rows.append(z)

        top_attack=sorted(attack_rows,key=candidate_key,reverse=True)[:40]
        for a in top_attack:
            for q in [.75,.80,.85,.90]:
                for k in [2,3,4]:
                    gm=gates[(q,k)]
                    m1=a['_m1']&gm['v1'];m2=a['_m2']&gm['v2'];mm=a['_mm']&gm['mar']
                    z={'kind':'attack_model','band':a['band'],'score_q':a['q'],'threshold':a['threshold'],
                       'weights':a['weights'],'q':q,'k':k,
                       'v1':metric(m1,v1),'v2':metric(m2,v2),'_m1':m1,'_m2':m2,'_mm':mm}
                    if usable(z,8):rows.append(z)
    strict=[z for z in rows if strict50(z)]
    strict=sorted(strict,key=lambda z:(z['v1']['n']+z['v2']['n'],min(z['v1']['rate'],z['v2']['rate'])),reverse=True)
    return feb,mar,v1,v2,strict

def dedup(strict):
    out=[];seen=set()
    for z in strict:
        key=np.packbits(z['_m1']).tobytes()+b'|'+np.packbits(z['_m2']).tobytes()
        if key in seen:continue
        seen.add(key);out.append(z)
    return out

def make_agg(kind,label,m1,m2,mm,v1,v2,meta=None):
    z={'kind':kind,'label':label,'v1':metric(m1,v1),'v2':metric(m2,v2),
       '_m1':m1,'_m2':m2,'_mm':mm}
    if meta:z.update(meta)
    return z

def aggregate_candidates(strict,v1,v2):
    u=dedup(strict)
    out=[]
    if not u:return u,out
    a1=np.column_stack([z['_m1'] for z in u])
    a2=np.column_stack([z['_m2'] for z in u])
    am=np.column_stack([z['_mm'] for z in u])
    n=len(u)

    # Vote/consensus thresholds across Feb-defined strict50 members.
    thresholds=sorted(set([1,2,3,4,5,n,max(1,int(np.ceil(n*.25))),max(1,int(np.ceil(n*.5))),max(1,int(np.ceil(n*.75))),max(1,int(np.ceil(n*.9)))]))
    v1votes=a1.sum(axis=1);v2votes=a2.sum(axis=1);mvotes=am.sum(axis=1)
    for k in thresholds:
        z=make_agg('vote',f'vote>={k}/{n}',v1votes>=k,v2votes>=k,mvotes>=k,v1,v2,{'k':k,'members':n})
        if strict50(z):out.append(z)

    # Pairwise unions and intersections.
    top=u[:min(40,n)]
    for i in range(len(top)):
        for j in range(i+1,len(top)):
            x,y=top[i],top[j]
            z=make_agg('pair_union',f'union_{i}_{j}',x['_m1']|y['_m1'],x['_m2']|y['_m2'],x['_mm']|y['_mm'],v1,v2,{'members':[i,j]})
            if strict50(z):out.append(z)
            z=make_agg('pair_intersection',f'intersect_{i}_{j}',x['_m1']&y['_m1'],x['_m2']&y['_m2'],x['_mm']&y['_mm'],v1,v2,{'members':[i,j]})
            if strict50(z):out.append(z)

    # Greedy unions from diverse starts, adding volume only while preserving strict50.
    starts=range(min(15,n))
    for s in starts:
        chosen=[s];m1=u[s]['_m1'].copy();m2=u[s]['_m2'].copy();mm=u[s]['_mm'].copy()
        remaining=set(range(n))-{s}
        while True:
            best=None
            base=int(m1.sum()+m2.sum())
            for j in remaining:
                c1=m1|u[j]['_m1'];c2=m2|u[j]['_m2'];cm=mm|u[j]['_mm']
                z=make_agg('greedy_union','tmp',c1,c2,cm,v1,v2)
                gain=int(c1.sum()+c2.sum())-base
                if gain<=0 or not strict50(z):continue
                key=(gain,int(c1.sum()+c2.sum()),min(z['v1']['rate'],z['v2']['rate']))
                if best is None or key>best[0]:best=(key,j,c1,c2,cm,z)
            if best is None:break
            _,j,m1,m2,mm,z=best
            chosen.append(j);remaining.remove(j)
            out.append(make_agg('greedy_union',f'greedy_{s}_m{len(chosen)}',m1.copy(),m2.copy(),mm.copy(),v1,v2,{'members':chosen.copy()}))
    out=[z for z in out if strict50(z)]
    out=sorted(out,key=lambda z:(z['v1']['n']+z['v2']['n'],min(z['v1']['rate'],z['v2']['rate'])),reverse=True)
    return u,out

def march_metric(z,mar):
    m=z['_mm'];sel=mar.loc[m].sort_values(['date','rc']).copy();n=len(sel);h=n//2
    return {'n':n,'hits':int(sel.y.sum()),'rate':float(sel.y.mean()) if n else None,
            'early_n':h,'early_hits':int(sel.iloc[:h].y.sum()),
            'late_n':n-h,'late_hits':int(sel.iloc[h:].y.sum()),
            'venue_count':int(sel.venue.nunique()) if n else 0}

def main():
    d,_=load_data()
    feb,mar,v1,v2,strict=generate_wave4_strict(d)
    unique,agg=aggregate_candidates(strict,v1,v2)
    volume=max(agg,key=lambda z:(z['v1']['n']+z['v2']['n'],min(z['v1']['rate'],z['v2']['rate']))) if agg else None
    precision=max(agg,key=lambda z:(min(z['v1']['rate'],z['v2']['rate']),z['v1']['n']+z['v2']['n'])) if agg else None
    if volume is None and strict:volume=strict[0]
    if precision is None and strict:
        precision=max(strict,key=lambda z:(min(z['v1']['rate'],z['v2']['rate']),z['v1']['n']+z['v2']['n']))
    out={
      'policy':{'feb_only_membership':True,'feb_only_aggregation_selection':True,'march_one_shot':True,
                'september_outcomes_read':False,'production_v288_changed':False},
      'wave4_strict50_count':len(strict),'unique_strict50_masks':len(unique),'aggregate_strict50_count':len(agg),
      'aggregate_frontier':[public(z) for z in agg[:50]],
      'volume_frozen':public(volume) if volume else None,
      'precision_frozen':public(precision) if precision else None,
      'march_volume':march_metric(volume,mar) if volume else None,
      'march_precision':march_metric(precision,mar) if precision else None
    }
    with open('research_3head_funsite_broad50_wave5_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
