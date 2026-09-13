from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import mean

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

V320 = Path('analysis_v320_1head_exact3_ticket_policy_best_race.csv')
V108 = Path('analysis_v108_1head_feasibility.csv')
OUT = Path('/tmp/v325')
OUT.mkdir(parents=True, exist_ok=True)

FEATURES = [
    'one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg',
    'ex_margin23','turn_margin23','straight_margin23',
]
ONE_D = ['one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg',
         'ex_margin23','turn_margin23','straight_margin23']


def pct(n,d): return 100.0*n/d if d else float('nan')

def metrics(x: pd.DataFrame) -> dict:
    n=len(x); h=int(x['hit'].sum()) if n else 0; hh=int(x['head_hit'].sum()) if n else 0
    return {'R':n,'H':h,'exact3_rate':pct(h,n),'head_H':hh,'head_rate':pct(hh,n)}

def load_v108_subset(codes:set[str]) -> pd.DataFrame:
    # Stream the large feasibility CSV and retain only frozen v320 race identities.
    rows=[]
    cols=['race_code','date','month','has_tkz','has_stt','has_orig']+FEATURES
    with V108.open('r',encoding='utf-8-sig',newline='') as f:
        rd=csv.DictReader(f)
        missing=[c for c in cols if c not in (rd.fieldnames or [])]
        if missing: raise AssertionError(f'v108 missing columns: {missing}')
        for r in rd:
            code=str(r.get('race_code','')).zfill(12)
            if code not in codes: continue
            z={'race_code':code}
            for c in cols[1:]: z[c]=r.get(c,'')
            rows.append(z)
    return pd.DataFrame(rows)

def prepare() -> pd.DataFrame:
    x=pd.read_csv(V320,dtype={'race_code':str})
    x['race_code']=x['race_code'].astype(str).str.zfill(12)
    x['hit']=pd.to_numeric(x['hit'],errors='coerce').fillna(0).astype(int)
    x['head_hit']=pd.to_numeric(x['head_hit'],errors='coerce').fillna(0).astype(int)
    if len(x)!=345 or int(x.hit.sum())!=139:
        raise AssertionError(f'v320 reconcile failed R={len(x)} H={int(x.hit.sum())}')
    v=load_v108_subset(set(x.race_code))
    if v.empty: raise AssertionError('v108 join subset empty')
    if v.race_code.duplicated().any():
        v=v.drop_duplicates('race_code',keep='last')
    y=x.merge(v,on='race_code',how='left',suffixes=('','_v108'))
    for c in ['has_tkz','has_stt','has_orig']+FEATURES:
        y[c]=pd.to_numeric(y[c],errors='coerce')
    y['joined']=y['date'].notna().astype(int)
    y['ex_complete']=(y[['has_tkz','has_stt']].fillna(0).min(axis=1)>=1).astype(int)
    y['orig_complete']=(y['has_orig'].fillna(0)>=1).astype(int)
    y['all_complete']=(y[['has_tkz','has_stt','has_orig']].fillna(0).min(axis=1)>=1).astype(int)
    # Research features must be actual frozen exhibition observations; no median/future backfill.
    y['feature_complete']=y[FEATURES].notna().all(axis=1).astype(int)
    y.to_csv(OUT/'v325_joined_dev.csv',index=False)
    return y

def eval_rule(df, feat, op, thr):
    if op=='>=': p=df[df[feat]>=thr]
    else: p=df[df[feat]<=thr]
    m=metrics(p);m.update({'kind':'1d','feature':feat,'op':op,'threshold':thr})
    return m

def discover_1d(disc:pd.DataFrame, val:pd.DataFrame):
    cand=[]
    for feat in ONE_D:
        vals=disc[feat].dropna().to_numpy(float)
        if len(vals)<20: continue
        qs=np.unique(np.quantile(vals,np.arange(.10,.91,.05)))
        for op in ('>=','<='):
            for t in qs:
                dm=eval_rule(disc,feat,op,float(t))
                vm=eval_rule(val,feat,op,float(t))
                row={f'disc_{k}':v for k,v in dm.items() if k not in ('kind','feature','op','threshold')}
                row.update({f'val_{k}':v for k,v in vm.items() if k not in ('kind','feature','op','threshold')})
                row.update({'kind':'1d','feature':feat,'op':op,'threshold':float(t)})
                cand.append(row)
    c=pd.DataFrame(cand)
    # Validation is the freeze set. Require useful size and >=50% on validation, then maximize retained validation R,
    # tie-break by validation exact3, discovery exact3, and simpler threshold extremeness is not mined further.
    ok=c[(c.val_R>=15)&(c.val_exact3_rate>=50)&(c.disc_R>=30)]
    if ok.empty:
        ok=c[(c.val_R>=10)&(c.val_exact3_rate>=48)&(c.disc_R>=25)]
    if ok.empty:return c,None
    best=ok.sort_values(['val_R','val_exact3_rate','disc_exact3_rate'],ascending=[False,False,False]).iloc[0].to_dict()
    return c,best

def logistic_candidate(disc:pd.DataFrame,val:pd.DataFrame):
    tr=disc.dropna(subset=FEATURES).copy(); va=val.dropna(subset=FEATURES).copy()
    if len(tr)<30 or len(va)<10:return pd.DataFrame(),None,None
    model=Pipeline([('sc',StandardScaler()),('lr',LogisticRegression(C=.25,max_iter=2000,class_weight=None))])
    model.fit(tr[FEATURES],[*tr.hit])
    pdsc=model.predict_proba(tr[FEATURES])[:,1]; pv=model.predict_proba(va[FEATURES])[:,1]
    rows=[]
    # threshold candidates defined on discovery probability quantiles, selected on May validation.
    for t in np.unique(np.quantile(pdsc,np.arange(.10,.91,.05))):
        a=tr[pdsc>=t]; b=va[pv>=t]
        dm=metrics(a);vm=metrics(b)
        rows.append({'kind':'logit','threshold':float(t),**{f'disc_{k}':v for k,v in dm.items()},**{f'val_{k}':v for k,v in vm.items()}})
    c=pd.DataFrame(rows)
    ok=c[(c.val_R>=15)&(c.val_exact3_rate>=50)&(c.disc_R>=30)]
    if ok.empty: ok=c[(c.val_R>=10)&(c.val_exact3_rate>=48)&(c.disc_R>=25)]
    if ok.empty:return c,None,model
    best=ok.sort_values(['val_R','val_exact3_rate','disc_exact3_rate'],ascending=[False,False,False]).iloc[0].to_dict()
    return c,best,model

def apply_candidate(df,best,model=None):
    if best is None:return df.iloc[0:0].copy()
    if best['kind']=='1d':
        if best['op']=='>=': return df[df[best['feature']]>=float(best['threshold'])]
        return df[df[best['feature']]<=float(best['threshold'])]
    z=df.dropna(subset=FEATURES).copy()
    z['pass_prob']=model.predict_proba(z[FEATURES])[:,1]
    return z[z.pass_prob>=float(best['threshold'])]

def candidate_key(best):
    if best is None:return 'NONE'
    if best['kind']=='1d':return f"1d:{best['feature']} {best['op']} {best['threshold']:.6f}"
    return f"logit:p>={best['threshold']:.6f}"

def main():
    y=prepare()
    print('V320_RECONCILE',len(y),int(y.hit.sum()),int(y.head_hit.sum()))
    print('JOIN',int(y.joined.sum()),'tkz',int((y.has_tkz==1).sum()),'stt',int((y.has_stt==1).sum()),'orig',int((y.has_orig==1).sum()),'all_complete',int(y.all_complete.sum()),'feature_complete',int(y.feature_complete.sum()))
    print('BASE',metrics(y))
    monthly=[]
    for m,g in y.groupby('month'):
        mm=metrics(g);monthly.append({'month':m,'scope':'base',**mm})
        print('BASE_MONTH',m,mm)

    disc=y[y.month.isin(['2026-02','2026-03','2026-04'])].copy()
    val=y[y.month.eq('2026-05')].copy()
    fwd=y[y.month.eq('2026-06')].copy()
    print('SPLITS',metrics(disc),metrics(val),metrics(fwd))

    c1,b1=discover_1d(disc,val)
    cl,bl,model=logistic_candidate(disc,val)
    c1.to_csv(OUT/'v325_candidates_1d.csv',index=False)
    cl.to_csv(OUT/'v325_candidates_logit.csv',index=False)

    candidates=[]
    if b1 is not None:candidates.append(('1d',b1,None))
    if bl is not None:candidates.append(('logit',bl,model))
    chosen=None
    # Freeze candidate on May validation: prioritize retained R then exact3; model type only tie-breaks to 1d.
    if candidates:
        candidates.sort(key=lambda z:(float(z[1].get('val_R',0)),float(z[1].get('val_exact3_rate',0)),1 if z[0]=='1d' else 0),reverse=True)
        chosen=candidates[0]
    if chosen is None:
        print('FROZEN_CANDIDATE NONE')
        summary={'candidate':'NONE','reason':'No predeclared candidate met validation freeze criteria'}
    else:
        typ,best,mdl=chosen
        print('FROZEN_CANDIDATE',candidate_key(best),best)
        fp=apply_candidate(fwd,best,mdl); fm=metrics(fp)
        skip=fwd[~fwd.index.isin(fp.index)]; sm=metrics(skip)
        print('JUN_FORWARD_PASS',fm)
        print('JUN_FORWARD_SKIP',sm)
        for m,g in y.groupby('month'):
            p=apply_candidate(g,best,mdl);monthly.append({'month':m,'scope':'candidate',**metrics(p)})
        # Forward support rule: target >=50%, or credible lift >=+5pp with >=10 retained races.
        base_f=metrics(fwd)
        supported=(fm['R']>=10 and (fm['exact3_rate']>=50 or fm['exact3_rate']>=base_f['exact3_rate']+5))
        summary={'candidate':candidate_key(best),'kind':typ,'jun_supported':bool(supported),
                 'jun_pass_R':fm['R'],'jun_pass_H':fm['H'],'jun_pass_exact3_rate':fm['exact3_rate'],
                 'jun_base_exact3_rate':base_f['exact3_rate'],'jun_skip_R':sm['R'],'jun_skip_H':sm['H'],
                 'val_R':best.get('val_R'),'val_exact3_rate':best.get('val_exact3_rate')}
        print('FORWARD_SUPPORTED',supported)

    pd.DataFrame(monthly).to_csv(OUT/'v325_monthly.csv',index=False)
    pd.DataFrame([summary]).to_csv(OUT/'v325_summary.csv',index=False)
    with (OUT/'summary_v325_1head_exhibition_postfilter.md').open('w',encoding='utf-8') as f:
        f.write('# v325 1HEAD exhibition postfilter\n\n')
        f.write(f"- v320 reconcile: {len(y)}R / {int(y.hit.sum())} exact3 / {int(y.head_hit.sum())} head hits\n")
        f.write(f"- join: {int(y.joined.sum())}/{len(y)}; tkz={int((y.has_tkz==1).sum())}; stt={int((y.has_stt==1).sum())}; orig={int((y.has_orig==1).sum())}; all_complete={int(y.all_complete.sum())}\n")
        for k,v in summary.items(): f.write(f'- {k}: {v}\n')
        f.write('\nJul/Aug are intentionally not read/evaluated by this script. Run reference only after a development candidate is frozen and forward-supported.\n')

if __name__=='__main__': main()
