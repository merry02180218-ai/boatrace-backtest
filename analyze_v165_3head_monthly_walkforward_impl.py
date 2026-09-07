#!/usr/bin/env python3
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler
ROOT=Path(__file__).resolve().parent
CANDS=[ROOT/'analysis_v108_1head_feasibility.csv',ROOT/'analysis_v109_1head_monthly_walkforward.csv',ROOT/'analysis_v90_model_candidates.csv',ROOT/'analysis_v90_candidates.csv',ROOT/'analysis_v83_candidates.csv']

def pc(df,names):
    return next((c for c in names if c in df.columns),None)
def load():
    for p in CANDS:
        if p.exists():
            d=pd.read_csv(p)
            if len(d): return p,d
    raise SystemExit('no source csv')
def target(df):
    for c in ['three_head','boat3_win','lane3_win','is_3head','y3']:
        if c in df.columns:return pd.to_numeric(df[c],errors='coerce'),c
    for c in ['first','winner','first_lane','result_1','head']:
        if c in df.columns:return (pd.to_numeric(df[c],errors='coerce')==3).astype(float),c+'==3'
    for c in ['result','trifecta','kumi','combination']:
        if c in df.columns:
            s=df[c].astype(str).str.extract(r'^\s*([1-6])')[0]
            if s.notna().any(): return (pd.to_numeric(s,errors='coerce')==3).astype(float),c+'[0]==3'
    raise SystemExit('no 3-head target')
def feats(df):
    out=[]
    for c in df.columns:
        if c.startswith(('three_','boat3_','lane3_','b3_','3_')):out.append(c)
    stems=['grade','wr','local','motor','motor2','motor3','waku_wr','waku_sr_strength','nst_strength','past_win','meet_st_strength','ex','st','lap','turn','straight','orig_avg','direct','score']
    for s in stems:
        for c in [f'{s}3',f'{s}_3',f'3_{s}']:
            if c in df.columns:out.append(c)
    for c in ['threat1','threat2','threat4','threat5','threat6','margin1','margin2','margin4','margin_all','st_margin12','st_margin23','st_margin34','st_margin_all','ex_margin12','ex_margin23','ex_margin34','ex_margin_all','turn_margin12','turn_margin23','turn_margin34','turn_margin_all','straight_margin12','straight_margin23','straight_margin34','straight_margin_all','structure_3makuri','structure_3makurizashi','score_3makuri','score_3makurizashi','pre_3makuri','pre_3makurizashi','comp_3makuri','comp_3makurizashi']:
        if c in df.columns:out.append(c)
    return sorted(set(out))
def model(nums,cats):
    ts=[]
    if nums:ts.append(('n',Pipeline([('i',SimpleImputer(strategy='median')),('s',StandardScaler())]),nums))
    if cats:ts.append(('c',Pipeline([('i',SimpleImputer(strategy='most_frequent')),('o',OneHotEncoder(handle_unknown='ignore'))]),cats))
    return Pipeline([('p',ColumnTransformer(ts)),('m',LogisticRegression(C=.35,max_iter=1800))])
def auc(y,p):
    try:return roc_auc_score(y,p) if len(set(y))>1 else np.nan
    except:return np.nan

def main():
    src,df=load(); dc=pc(df,['date','race_date','ymd']); vc=pc(df,['venue','jcd','stadium','place'])
    if not dc:raise SystemExit('no date col')
    y,td=target(df); fs=feats(df)
    schema={'source':src.name,'rows':len(df),'date_col':dc,'target':td,'features':fs,'columns':list(df.columns)}
    (ROOT/'analysis_v165_3head_schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2),encoding='utf-8')
    if len(fs)<4:raise SystemExit('insufficient explicit lane3 features')
    d=df.copy();d['_date']=pd.to_datetime(d[dc].astype(str),errors='coerce');d['_y']=y;d=d[d._date.notna()&d._y.notna()].copy()
    rows=[]
    for m in [pd.Timestamp('2026-06-01'),pd.Timestamp('2026-07-01'),pd.Timestamp('2026-08-01')]:
        e=m+pd.offsets.MonthBegin(1);tr=d[d._date<m].copy();te=d[(d._date>=m)&(d._date<e)].copy()
        if len(tr)<200 or len(te)<20 or tr._y.nunique()<2:continue
        nums=[]
        for c in fs:
            q=pd.to_numeric(d[c],errors='coerce')
            if q.notna().mean()>=.8:
                d[c]=q;tr[c]=pd.to_numeric(tr[c],errors='coerce');te[c]=pd.to_numeric(te[c],errors='coerce');nums.append(c)
        cats=[vc] if vc and vc not in nums else []
        mo=model(nums,cats);mo.fit(tr[nums+cats],tr._y.astype(int));p=mo.predict_proba(te[nums+cats])[:,1]
        for ix,pr in zip(te.index,p):rows.append({'date':d.loc[ix,'_date'].strftime('%Y-%m-%d'),'month':m.strftime('%Y-%m'),'p3head':float(pr),'y3head':int(d.loc[ix,'_y']),'source_index':int(ix)})
    o=pd.DataFrame(rows)
    if o.empty:raise SystemExit('no holdout rows')
    o.to_csv(ROOT/'analysis_v165_3head_monthly_walkforward.csv',index=False)
    L=['# v165 3-head monthly walk-forward','',f'- source: `{src.name}`',f'- target: `{td}`',f'- explicit features: {len(fs)}','- strict monthly walk-forward: target month trains only on earlier dates','','|month|R|actual 3-head|AUC|Brier|p>=20 R|head%|p>=25 R|head%|p>=30 R|head%|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for mon,g in o.groupby('month'):
        cells=[mon,str(len(g)),f'{100*g.y3head.mean():.2f}%',f'{auc(g.y3head,g.p3head):.4f}',f'{brier_score_loss(g.y3head,g.p3head):.5f}']
        for th in [.20,.25,.30]:
            z=g[g.p3head>=th];cells += [str(len(z)),f'{100*z.y3head.mean():.2f}%' if len(z) else '-']
        L.append('| '+' | '.join(cells)+' |')
    L += ['','## Aggregate','',f'- R: {len(o)}',f'- actual 3-head: {100*o.y3head.mean():.2f}%',f'- AUC: {auc(o.y3head,o.p3head):.4f}',f'- Brier: {brier_score_loss(o.y3head,o.p3head):.5f}']
    for th in [.15,.20,.25,.30,.35,.40]:
        z=o[o.p3head>=th]
        if len(z):L.append(f'- p>={th:.2f}: {len(z)}R, head {100*z.y3head.mean():.2f}%')
    (ROOT/'summary_v165_3head_monthly_walkforward.md').write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
