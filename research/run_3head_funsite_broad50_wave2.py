from __future__ import annotations
import json
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, HistGradientBoostingClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier

from run_3head_funsite_broad50 import fetch, features, SRC, EX

TARGETS=[.50,.45,.40]
MODEL_NAMES=['logit','extra','rf','hist','tree','gb']
TOPNS=[10,20,30,50,75,100,150,200]

def wave2_model(name):
    if name=='logit':
        return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
            LogisticRegression(C=.08,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=17))
    if name=='extra':
        return make_pipeline(SimpleImputer(strategy='median'),
            ExtraTreesClassifier(n_estimators=600,min_samples_leaf=10,max_features=.8,class_weight='balanced',random_state=17,n_jobs=-1))
    if name=='rf':
        return make_pipeline(SimpleImputer(strategy='median'),
            RandomForestClassifier(n_estimators=500,min_samples_leaf=12,max_features=.65,class_weight='balanced',random_state=17,n_jobs=-1))
    if name=='hist':
        return make_pipeline(SimpleImputer(strategy='median'),
            HistGradientBoostingClassifier(max_iter=260,max_leaf_nodes=11,l2_regularization=3,learning_rate=.04,random_state=17))
    if name=='tree':
        return make_pipeline(SimpleImputer(strategy='median'),
            DecisionTreeClassifier(max_depth=3,min_samples_leaf=25,class_weight='balanced',random_state=17))
    return make_pipeline(SimpleImputer(strategy='median'),
        GradientBoostingClassifier(n_estimators=180,learning_rate=.035,max_depth=2,min_samples_leaf=20,random_state=17))

def add_signals(x: pd.DataFrame) -> pd.DataFrame:
    x=x.copy()
    high_good=['全国勝率','全国2連対率','全国3連対率','当地勝率','当地2連対率','当地3連対率',
               'モーター2連対率','モーター3連対率','ボート2連対率','ボート3連対率',
               'rn_win','rn_top2','rn_top3','rl_win','rl_top2','rl_top3','rn_starts','rl_starts']
    low_good=['全国平均ST','F本数','L本数','rn_mean','rl_mean']
    for c in high_good+low_good:
        cols=[f'b{i}_{c}' for i in range(1,7)]
        if not all(z in x.columns for z in cols):
            continue
        vals=x[cols].apply(pd.to_numeric,errors='coerce')
        ranks=vals.rank(axis=1,ascending=(c in low_good),method='average')
        x[f'sig_rank_{c}']=7-ranks[f'b3_{c}']
        opp=[f'b{i}_{c}' for i in [1,2,4,5,6]]
        inner=[f'b{i}_{c}' for i in [1,2]]
        sign=-1.0 if c in low_good else 1.0
        x[f'sig_all_{c}']=sign*(vals[f'b3_{c}']-vals[opp].mean(axis=1))
        x[f'sig_inner_{c}']=sign*(vals[f'b3_{c}']-vals[inner].mean(axis=1))
        for i in [1,2,4]:
            x[f'sig_vs{i}_{c}']=sign*(vals[f'b3_{c}']-vals[f'b{i}_{c}'])
    # Explicit attack-archetype composites; all components are oriented so higher is better for boat 3.
    def z(name):
        return pd.to_numeric(x[name],errors='coerce') if name in x.columns else pd.Series(np.nan,index=x.index)
    x['sig_attack_player_inner']=(
        z('sig_inner_全国2連対率')+z('sig_inner_当地2連対率')+
        0.5*z('sig_inner_全国勝率')+0.5*z('sig_inner_当地勝率')
    )
    x['sig_attack_start_inner']=z('sig_inner_全国平均ST')
    x['sig_attack_motor_inner']=z('sig_inner_モーター2連対率')+0.5*z('sig_inner_モーター3連対率')
    x['sig_attack_recent_inner']=(
        z('sig_inner_rn_win')+z('sig_inner_rl_win')+
        0.5*z('sig_inner_rn_top2')+0.5*z('sig_inner_rl_top2')
    )
    x['sig_b2_wall_break']=(
        z('sig_vs2_全国2連対率')+z('sig_vs2_当地2連対率')+
        z('sig_vs2_全国平均ST')+0.5*z('sig_vs2_モーター2連対率')
    )
    x['sig_b1_pressure']=(
        z('sig_vs1_全国2連対率')+z('sig_vs1_当地2連対率')+
        z('sig_vs1_全国平均ST')+0.5*z('sig_vs1_モーター2連対率')
    )
    x['sig_b4_counter_margin']=(
        z('sig_vs4_全国2連対率')+z('sig_vs4_当地2連対率')+
        z('sig_vs4_全国平均ST')+0.5*z('sig_vs4_モーター2連対率')
    )
    x['sig_attack_balanced']=(
        x['sig_attack_player_inner']+
        1.5*x['sig_attack_start_inner']+
        x['sig_attack_motor_inner']+
        x['sig_attack_recent_inner']+
        0.75*x['sig_b4_counter_margin']
    )
    return x

def load_data():
    b=pd.read_csv(SRC,low_memory=False)
    b['date']=pd.to_datetime(b.date)
    b['rc']=pd.to_numeric(b.race_code_norm,errors='coerce').astype('Int64')
    b=b[(b.settle__usable==1)&(b.closing_odds__ok==1)&(~b.rc.isin(EX))&
        (b.date>='2026-02-01')&(b.date<'2026-04-01')].copy()
    rows=[]
    for d in pd.date_range('2026-02-01','2026-03-31'):
        parts={k:fetch(k,d.date()) for k in ['programs/race_cards','programs/recent_national','programs/recent_local']}
        if not all(parts.values()):
            continue
        maps={k:{str(r.get('レースコード','')):r for r in v} for k,v in parts.items()}
        for c in set.intersection(*[set(m) for m in maps.values()]):
            if c.isdigit():
                rows.append(features(maps['programs/race_cards'][c],maps['programs/recent_national'][c],maps['programs/recent_local'][c]))
    x=pd.DataFrame(rows).drop_duplicates('rc')
    x=add_signals(x)
    d=b[['rc','date','settle__winner']].merge(x,on='rc')
    d['y']=(d.settle__winner==3).astype(int)
    return d,x

def split_feb(d):
    feb=d[d.date<'2026-03-01'].sort_values(['date','rc']).copy()
    mar=d[d.date>='2026-03-01'].sort_values(['date','rc']).copy()
    days=sorted(feb.date.dt.date.unique())
    cut1=days[int(len(days)*.55)]
    cut2=days[int(len(days)*.78)]
    tr=feb[feb.date.dt.date<=cut1].copy()
    v1=feb[(feb.date.dt.date>cut1)&(feb.date.dt.date<=cut2)].copy()
    v2=feb[feb.date.dt.date>cut2].copy()
    return feb,mar,tr,v1,v2

def rank_pct(a):
    return pd.Series(np.asarray(a,float)).rank(pct=True,method='average').to_numpy()

def metrics(mask,y):
    mask=np.asarray(mask,bool)
    yy=np.asarray(y,int)
    n=int(mask.sum())
    return {'n':n,'hits':int(yy[mask].sum()) if n else 0,'rate':float(yy[mask].mean()) if n else None}

def model_scores(tr,v1,v2,mar,feats,fit_mar=False):
    ms={}
    out={}
    for n in MODEL_NAMES:
        m=wave2_model(n);m.fit(tr[feats],tr.y)
        ms[n]=m
        s1=m.predict_proba(v1[feats])[:,1]
        s2=m.predict_proba(v2[feats])[:,1]
        out[n]={'v1':s1,'v2':s2}
    return ms,out

def diagnostic_topn(scores,v1,v2):
    diag={}
    for n,ss in scores.items():
        diag[n]={}
        for k in TOPNS:
            if k<=len(v1) and k<=len(v2):
                i1=np.argsort(-ss['v1'])[:k]
                i2=np.argsort(-ss['v2'])[:k]
                diag[n][str(k)]={'v1_rate':float(v1.y.iloc[i1].mean()),'v2_rate':float(v2.y.iloc[i2].mean())}
    return diag

def consensus_candidates(scores,v1,v2):
    names=list(scores)
    r1=np.column_stack([rank_pct(scores[n]['v1']) for n in names])
    r2=np.column_stack([rank_pct(scores[n]['v2']) for n in names])
    rows=[]
    for q in [.80,.85,.90,.925,.95,.975]:
        for k in [2,3,4,5,6]:
            m1=(r1>=q).sum(axis=1)>=k
            m2=(r2>=q).sum(axis=1)>=k
            a,b=metrics(m1,v1.y),metrics(m2,v2.y)
            rows.append({'kind':'consensus','q':q,'k':k,'v1':a,'v2':b})
    return rows

def curated_signal_cols(d):
    preferred=[
        'sig_attack_balanced','sig_attack_player_inner','sig_attack_start_inner','sig_attack_motor_inner',
        'sig_attack_recent_inner','sig_b2_wall_break','sig_b1_pressure','sig_b4_counter_margin',
        'sig_rank_全国2連対率','sig_rank_当地2連対率','sig_rank_全国平均ST','sig_rank_モーター2連対率',
        'sig_rank_rn_win','sig_rank_rl_win','sig_inner_全国2連対率','sig_inner_当地2連対率',
        'sig_inner_全国平均ST','sig_inner_モーター2連対率','sig_inner_rn_win','sig_inner_rl_win',
        'sig_vs1_全国2連対率','sig_vs2_全国2連対率','sig_vs4_全国2連対率',
        'sig_vs1_全国平均ST','sig_vs2_全国平均ST','sig_vs4_全国平均ST'
    ]
    return [c for c in preferred if c in d.columns and d[c].notna().sum()>=50]

def rule_candidates(tr,v1,v2,signal_cols):
    atoms=[]
    for c in signal_cols:
        base=pd.to_numeric(tr[c],errors='coerce')
        for q in [.55,.65,.75,.85,.90,.95]:
            th=float(base.quantile(q))
            if not np.isfinite(th):
                continue
            m1=pd.to_numeric(v1[c],errors='coerce')>=th
            m2=pd.to_numeric(v2[c],errors='coerce')>=th
            a,b=metrics(m1,v1.y),metrics(m2,v2.y)
            if a['n']>=8 and b['n']>=8:
                atoms.append({'kind':'single','c1':c,'th1':th,'q1':q,'v1':a,'v2':b})
    atoms=sorted(atoms,key=lambda z:(min(z['v1']['rate'] or 0,z['v2']['rate'] or 0),min(z['v1']['n'],z['v2']['n'])),reverse=True)
    seed=atoms[:36]
    pairs=[]
    for i,a in enumerate(seed):
        for b in seed[i+1:]:
            if a['c1']==b['c1']:
                continue
            m1=(pd.to_numeric(v1[a['c1']],errors='coerce')>=a['th1'])&(pd.to_numeric(v1[b['c1']],errors='coerce')>=b['th1'])
            m2=(pd.to_numeric(v2[a['c1']],errors='coerce')>=a['th1'])&(pd.to_numeric(v2[b['c1']],errors='coerce')>=b['th1'])
            x1,x2=metrics(m1,v1.y),metrics(m2,v2.y)
            if x1['n']>=8 and x2['n']>=8:
                pairs.append({'kind':'pair','c1':a['c1'],'th1':a['th1'],'q1':a['q1'],
                              'c2':b['c1'],'th2':b['th1'],'q2':b['q1'],'v1':x1,'v2':x2})
    return atoms+pairs

def freeze(rows,target):
    strict=[r for r in rows if r['v1']['n']>=12 and r['v2']['n']>=12 and
            r['v1']['rate'] is not None and r['v2']['rate'] is not None and
            r['v1']['rate']>=target and r['v2']['rate']>=target]
    relaxed=[r for r in rows if r['v1']['n']>=12 and r['v2']['n']>=12 and
             r['v1']['rate'] is not None and r['v2']['rate'] is not None and
             r['v1']['rate']>=target-.05 and r['v2']['rate']>=target-.05]
    pool=strict if strict else relaxed
    if not pool:
        return None
    best=max(pool,key=lambda r:(min(r['v1']['n'],r['v2']['n']),min(r['v1']['rate'],r['v2']['rate']),
                                r['v1']['n']+r['v2']['n']))
    z=dict(best);z['strict']=bool(strict)
    return z

def apply_rule(rowset,z):
    if z['kind']=='single':
        return pd.to_numeric(rowset[z['c1']],errors='coerce')>=z['th1']
    if z['kind']=='pair':
        return ((pd.to_numeric(rowset[z['c1']],errors='coerce')>=z['th1'])&
                (pd.to_numeric(rowset[z['c2']],errors='coerce')>=z['th2']))
    raise ValueError(z['kind'])

def march_eval_rule(mar,z):
    mask=apply_rule(mar,z)
    sel=mar[mask].sort_values(['date','rc']).copy()
    n=len(sel);half=n//2
    venues=sel.groupby('venue').y.agg(['count','sum','mean']).sort_values('count',ascending=False).head(12).reset_index().to_dict('records')
    return {'n':n,'hits':int(sel.y.sum()),'rate':float(sel.y.mean()) if n else None,
            'early_n':half,'early_hits':int(sel.iloc[:half].y.sum()),
            'late_n':n-half,'late_hits':int(sel.iloc[half:].y.sum()),
            'venues_top12':venues}

def march_eval_consensus(feb,mar,feats,z):
    ranks=[]
    for n in MODEL_NAMES:
        m=wave2_model(n);m.fit(feb[feats],feb.y)
        ranks.append(rank_pct(m.predict_proba(mar[feats])[:,1]))
    rr=np.column_stack(ranks)
    mask=(rr>=z['q']).sum(axis=1)>=z['k']
    sel=mar[mask].sort_values(['date','rc']).copy()
    n=len(sel);half=n//2
    venues=sel.groupby('venue').y.agg(['count','sum','mean']).sort_values('count',ascending=False).head(12).reset_index().to_dict('records')
    return {'n':n,'hits':int(sel.y.sum()),'rate':float(sel.y.mean()) if n else None,
            'early_n':half,'early_hits':int(sel.iloc[:half].y.sum()),
            'late_n':n-half,'late_hits':int(sel.iloc[half:].y.sum()),
            'venues_top12':venues}

def compact_frontier(rows,limit=30):
    def key(r):
        return (min(r['v1']['rate'] or 0,r['v2']['rate'] or 0),min(r['v1']['n'],r['v2']['n']))
    return sorted(rows,key=key,reverse=True)[:limit]

def main():
    d,x=load_data()
    feb,mar,tr,v1,v2=split_feb(d)
    exclude={'rc','venue','date','settle__winner','y'}
    feats=[c for c in d.columns if c not in exclude and pd.api.types.is_numeric_dtype(d[c]) and d[c].notna().sum()>=30]
    _,scores=model_scores(tr,v1,v2,mar,feats)
    diag=diagnostic_topn(scores,v1,v2)
    cons=consensus_candidates(scores,v1,v2)
    sigs=curated_signal_cols(d)
    rules=rule_candidates(tr,v1,v2,sigs)
    combined=cons+rules

    frozen={}
    march={}
    for t in TARGETS:
        z=freeze(combined,t)
        frozen[str(t)]=z
        if z is None:
            march[str(t)]=None
        elif z['kind']=='consensus':
            march[str(t)]=march_eval_consensus(feb,mar,feats,z)
        else:
            march[str(t)]=march_eval_rule(mar,z)

    out={
        'policy':{
            'feb_only_selection':True,'march_one_shot':True,'september_outcomes_read':False,
            'current_meet_used':False,'production_v288_changed':False,
            'tiny_n_50pct_is_diagnostic_only':True
        },
        'joined_feb':len(feb),'joined_mar':len(mar),'features':len(feats),
        'signal_columns':sigs,
        'diagnostic_topn':diag,
        'consensus_frontier':compact_frontier(cons,30),
        'rule_frontier':compact_frontier(rules,40),
        'frozen':frozen,
        'march_results':march
    }
    with open('research_3head_funsite_broad50_wave2_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
