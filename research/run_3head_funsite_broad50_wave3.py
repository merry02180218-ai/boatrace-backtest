from __future__ import annotations
import json
import numpy as np
import pandas as pd

from run_3head_funsite_broad50_wave2 import load_data, wave2_model, MODEL_NAMES

QGRID=[.65,.75,.80,.85,.90,.925,.95,.975]
CORE_Q=[.75,.85,.90,.95]
MODEL_Q=[.75,.80,.85,.90,.925,.95]
MODEL_K=[2,3,4,5,6]

def metric(mask, frame):
    m=np.asarray(mask,bool)
    y=frame.y.to_numpy(dtype=int)
    n=int(m.sum())
    return {
        'n':n,
        'hits':int(y[m].sum()) if n else 0,
        'rate':float(y[m].mean()) if n else None,
        'venues':int(frame.loc[m,'venue'].nunique()) if n else 0
    }

def pct_against_train(train_score, score):
    a=np.sort(np.asarray(train_score,float))
    s=np.asarray(score,float)
    return np.searchsorted(a,s,side='right')/max(1,len(a))

def split_feb_stable(d):
    feb=d[d.date<'2026-03-01'].sort_values(['date','rc']).copy()
    mar=d[d.date>='2026-03-01'].sort_values(['date','rc']).copy()
    tr=feb[feb.date<'2026-02-15'].copy()
    v1=feb[(feb.date>='2026-02-15')&(feb.date<'2026-02-22')].copy()
    v2=feb[feb.date>='2026-02-22'].copy()
    return feb,mar,tr,v1,v2

def numeric_features(d):
    exclude={'rc','venue','date','settle__winner','y'}
    return [c for c in d.columns if c not in exclude and
            pd.api.types.is_numeric_dtype(d[c]) and d[c].notna().sum()>=30]

def fit_model_percentiles(tr, frames, feats):
    out={name:{} for name in MODEL_NAMES}
    for name in MODEL_NAMES:
        m=wave2_model(name)
        m.fit(tr[feats],tr.y)
        st=m.predict_proba(tr[feats])[:,1]
        out[name]['train_score']=st
        for key,frame in frames.items():
            s=m.predict_proba(frame[feats])[:,1]
            out[name][key]=pct_against_train(st,s)
    return out

def model_gate_mask(percs, key, q, k):
    arr=np.column_stack([percs[n][key] for n in MODEL_NAMES])
    return (arr>=q).sum(axis=1)>=k

def cond_mask(frame, conds):
    m=np.ones(len(frame),dtype=bool)
    for c,th in conds:
        m &= pd.to_numeric(frame[c],errors='coerce').to_numpy()>=th
    return m

def apply_candidate(frame, cand, percs=None, pkey=None):
    m=cond_mask(frame,cand.get('conds',[]))
    band=cand.get('race_band')
    if band is not None:
        lo,hi=band
        rn=pd.to_numeric(frame.race_no,errors='coerce').to_numpy()
        m &= (rn>=lo)&(rn<=hi)
    venues=cand.get('venues')
    if venues:
        m &= frame.venue.astype(str).isin(venues).to_numpy()
    gate=cand.get('model_gate')
    if gate is not None:
        m &= model_gate_mask(percs,pkey,gate['q'],gate['k'])
    return m

def qth(tr,col,q):
    s=pd.to_numeric(tr[col],errors='coerce')
    v=float(s.quantile(q))
    return v if np.isfinite(v) else None

def base_rule_specs(tr):
    core=[
        'sig_vs2_全国2連対率',
        'sig_vs2_全国平均ST',
        'sig_b2_wall_break',
    ]
    support=[
        'sig_attack_player_inner',
        'sig_attack_motor_inner',
        'sig_attack_recent_inner',
        'sig_b4_counter_margin',
        'sig_b1_pressure',
        'sig_rank_全国2連対率',
        'sig_rank_全国平均ST',
        'sig_rank_モーター2連対率',
        'sig_vs1_全国2連対率',
        'sig_vs4_全国2連対率',
        'sig_vs2_モーター2連対率',
        'sig_vs2_rn_win',
        'sig_vs2_rl_win',
    ]
    core=[c for c in core if c in tr.columns and tr[c].notna().sum()>=50]
    support=[c for c in support if c in tr.columns and tr[c].notna().sum()>=50]
    specs=[]
    seen=set()
    def add(conds,label):
        key=tuple((c,round(float(t),12)) for c,t in conds)
        if key in seen:return
        seen.add(key)
        specs.append({'kind':'rule','label':label,'conds':[(c,float(t)) for c,t in conds]})
    for c in core+support:
        for q in QGRID:
            th=qth(tr,c,q)
            if th is not None:add([(c,th)],f'{c}@q{q}')
    for a in core:
        for b in support+core:
            if a==b:continue
            for qa in CORE_Q:
                ta=qth(tr,a,qa)
                if ta is None:continue
                for qb in CORE_Q:
                    tb=qth(tr,b,qb)
                    if tb is not None:add([(a,ta),(b,tb)],f'{a}@{qa}+{b}@{qb}')
    if 'sig_vs2_全国2連対率' in core and 'sig_vs2_全国平均ST' in core:
        extras=[c for c in support if c not in {'sig_vs2_全国2連対率','sig_vs2_全国平均ST'}]
        for qa in CORE_Q:
            ta=qth(tr,'sig_vs2_全国2連対率',qa)
            for qb in CORE_Q:
                tb=qth(tr,'sig_vs2_全国平均ST',qb)
                if ta is None or tb is None:continue
                for c in extras:
                    for qc in [.75,.85,.90,.95]:
                        tc=qth(tr,c,qc)
                        if tc is not None:
                            add([('sig_vs2_全国2連対率',ta),('sig_vs2_全国平均ST',tb),(c,tc)],
                                f'vs2_player@{qa}+vs2_st@{qb}+{c}@{qc}')
    return specs

def eval_candidate(cand,tr,v1,v2,percs):
    a=metric(apply_candidate(v1,cand,percs,'v1'),v1)
    b=metric(apply_candidate(v2,cand,percs,'v2'),v2)
    z=dict(cand)
    z['v1']=a;z['v2']=b
    return z

def robustness_key(z):
    rates=[z['v1']['rate'] or 0,z['v2']['rate'] or 0]
    return (min(rates),min(z['v1']['n'],z['v2']['n']),sum(rates)/2,z['v1']['n']+z['v2']['n'])

def eligible_for_frontier(z,min_n=8):
    return z['v1']['n']>=min_n and z['v2']['n']>=min_n and z['v1']['venues']>=3 and z['v2']['venues']>=3

def train_learned_venue_variant(cand,tr):
    m=cond_mask(tr,cand.get('conds',[]))
    sub=tr.loc[m,['venue','y']].copy()
    if len(sub)<30:return None
    g=sub.groupby('venue').y.agg(['count','sum','mean'])
    # Training-only venue learning with real support; threshold is intentionally coarse.
    keep=g[(g['count']>=8)&(g['mean']>=.35)].index.astype(str).tolist()
    if len(keep)<3:return None
    z=dict(cand)
    z['kind']='rule_venue'
    z['venues']=sorted(keep)
    z['label']=cand['label']+'+trainVenue'
    return z

def weekly_report(feb,cand,percs_full=None):
    rows=[]
    for lo,hi in [(1,7),(8,14),(15,21),(22,28)]:
        sub=feb[(feb.date.dt.day>=lo)&(feb.date.dt.day<=hi)].copy()
        if not len(sub):continue
        if percs_full is None:
            m=apply_candidate(sub,cand)
        else:
            key=f'w{lo}_{hi}'
            m=apply_candidate(sub,cand,percs_full,key)
        r=metric(m,sub);r.update({'days':f'{lo:02d}-{hi:02d}'})
        rows.append(r)
    return rows

def freeze(rows,target):
    strict=[z for z in rows if eligible_for_frontier(z,12) and
            z['v1']['rate'] is not None and z['v2']['rate'] is not None and
            z['v1']['rate']>=target and z['v2']['rate']>=target]
    relaxed=[z for z in rows if eligible_for_frontier(z,15) and
             z['v1']['rate'] is not None and z['v2']['rate'] is not None and
             z['v1']['rate']>=target-.05 and z['v2']['rate']>=target-.05 and
             ((z['v1']['hits']+z['v2']['hits'])/(z['v1']['n']+z['v2']['n']))>=target-.03]
    pool=strict if strict else relaxed
    if not pool:return None
    # Volume first within a precision-stable pool, matching user priority.
    best=max(pool,key=lambda z:(z['v1']['n']+z['v2']['n'],min(z['v1']['rate'],z['v2']['rate']),z['v1']['venues']+z['v2']['venues']))
    out=dict(best);out['strict']=bool(strict)
    return out

def refit_full_feb_percentiles(feb,mar,feats):
    frames={'feb':feb,'mar':mar}
    out={name:{} for name in MODEL_NAMES}
    for name in MODEL_NAMES:
        m=wave2_model(name);m.fit(feb[feats],feb.y)
        sf=m.predict_proba(feb[feats])[:,1]
        out[name]['feb']=pct_against_train(sf,sf)
        out[name]['mar']=pct_against_train(sf,m.predict_proba(mar[feats])[:,1])
    return out

def march_eval(cand,mar,percs_mar=None):
    m=apply_candidate(mar,cand,percs_mar,'mar' if percs_mar is not None else None)
    sel=mar.loc[m].sort_values(['date','rc']).copy()
    n=len(sel);half=n//2
    venues=sel.groupby('venue').y.agg(['count','sum','mean']).sort_values('count',ascending=False).head(12).reset_index().to_dict('records')
    return {
        'n':n,'hits':int(sel.y.sum()),'rate':float(sel.y.mean()) if n else None,
        'early_n':half,'early_hits':int(sel.iloc[:half].y.sum()),
        'late_n':n-half,'late_hits':int(sel.iloc[half:].y.sum()),
        'venue_count':int(sel.venue.nunique()) if n else 0,
        'venues_top12':venues
    }

def main():
    d,_=load_data()
    feb,mar,tr,v1,v2=split_feb_stable(d)
    feats=numeric_features(d)
    percs=fit_model_percentiles(tr,{'v1':v1,'v2':v2},feats)

    rows=[]
    base=[]
    for cand in base_rule_specs(tr):
        z=eval_candidate(cand,tr,v1,v2,percs)
        if eligible_for_frontier(z,8):
            base.append(z);rows.append(z)

    base_sorted=sorted(base,key=robustness_key,reverse=True)[:100]

    # Coarse race-number regime variants.
    for z0 in base_sorted:
        cand={k:v for k,v in z0.items() if k not in {'v1','v2'}}
        for band in [(1,4),(5,8),(9,12)]:
            z=dict(cand);z['kind']='rule_raceband';z['race_band']=band;z['label']=cand['label']+f'+R{band[0]}-{band[1]}'
            e=eval_candidate(z,tr,v1,v2,percs)
            if eligible_for_frontier(e,8):rows.append(e)

    # Venue sets learned from training block only.
    for z0 in base_sorted:
        cand={k:v for k,v in z0.items() if k not in {'v1','v2'}}
        vv=train_learned_venue_variant(cand,tr)
        if vv is not None:
            e=eval_candidate(vv,tr,v1,v2,percs)
            if eligible_for_frontier(e,8):rows.append(e)

    # Model-only consensus gates.
    for q in MODEL_Q:
        for k in MODEL_K:
            cand={'kind':'model_consensus','label':f'model_q{q}_k{k}','conds':[],'model_gate':{'q':q,'k':k}}
            e=eval_candidate(cand,tr,v1,v2,percs)
            if eligible_for_frontier(e,8):rows.append(e)

    # Rule + model consensus. The rule shortlist is frozen from Feb validation evidence only.
    for z0 in base_sorted[:60]:
        cand0={k:v for k,v in z0.items() if k not in {'v1','v2'}}
        for q in [.75,.80,.85,.90]:
            for k in [2,3,4]:
                cand=dict(cand0)
                cand['kind']='rule_model'
                cand['model_gate']={'q':q,'k':k}
                cand['label']=cand0['label']+f'+M{q}/{k}'
                e=eval_candidate(cand,tr,v1,v2,percs)
                if eligible_for_frontier(e,8):rows.append(e)

    rows=sorted(rows,key=robustness_key,reverse=True)

    frozen={}
    for t in [.50,.45,.40]:
        frozen[str(t)]=freeze(rows,t)

    # For weekly reporting and March, model-based candidates use models refit on all February,
    # with the percentile gate itself unchanged.
    percs_full=None
    if any(z and z.get('model_gate') for z in frozen.values()):
        frames={}
        for lo,hi in [(1,7),(8,14),(15,21),(22,28)]:
            frames[f'w{lo}_{hi}']=feb[(feb.date.dt.day>=lo)&(feb.date.dt.day<=hi)].copy()
        percs_full={name:{} for name in MODEL_NAMES}
        for name in MODEL_NAMES:
            m=wave2_model(name);m.fit(feb[feats],feb.y)
            sf=m.predict_proba(feb[feats])[:,1]
            for key,frame in frames.items():
                percs_full[name][key]=pct_against_train(sf,m.predict_proba(frame[feats])[:,1])

    weekly={}
    for key,z in frozen.items():
        if z is None:
            weekly[key]=None
        else:
            weekly[key]=weekly_report(feb,z,percs_full if z.get('model_gate') else None)

    need_model=any(z and z.get('model_gate') for z in frozen.values())
    pm=refit_full_feb_percentiles(feb,mar,feats) if need_model else None
    march={}
    for key,z in frozen.items():
        march[key]=None if z is None else march_eval(z,mar,pm if z.get('model_gate') else None)

    strict50=[z for z in rows if eligible_for_frontier(z,12) and
              z['v1']['rate'] is not None and z['v2']['rate'] is not None and
              z['v1']['rate']>=.50 and z['v2']['rate']>=.50]
    near50=[z for z in rows if eligible_for_frontier(z,15) and
            z['v1']['rate'] is not None and z['v2']['rate'] is not None and
            z['v1']['rate']>=.45 and z['v2']['rate']>=.45]

    out={
        'policy':{
            'wave3_family_defined_before_march':True,
            'feb_only_selection':True,
            'march_one_shot':True,
            'september_outcomes_read':False,
            'production_v288_changed':False,
            'venue_sets_train_only':True
        },
        'split':{
            'train_n':len(tr),'v1_n':len(v1),'v2_n':len(v2),
            'joined_feb':len(feb),'joined_mar':len(mar)
        },
        'features':len(feats),
        'candidate_count':len(rows),
        'strict50_count':len(strict50),
        'near50_count':len(near50),
        'strict50_frontier':strict50[:30],
        'near50_frontier':near50[:30],
        'overall_frontier':rows[:50],
        'frozen':frozen,
        'weekly_frozen':weekly,
        'march_results':march
    }
    with open('research_3head_funsite_broad50_wave3_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
