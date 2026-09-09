#!/usr/bin/env python3
from pathlib import Path
import numpy as np, pandas as pd

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT=Path('analysis_v247_3head_strict_pre_lomo_rolling.csv')
SUM=Path('summary_v247_3head_strict_pre_lomo_rolling.md')
BANK=10000
CANON_KEEP_THR=-0.1999999999999999
CANON_RESCUE_THR=0.5672342857142857

def final_mask(q):
    base=(q.bet==1)&(q.p3>=.45)&q.raw_top_n.between(7,18)&q.comp_odds.between(3.05,4.0)
    keep=base & (pd.to_numeric(q['f__c_b3_minus_b5_st'],errors='coerce')>=CANON_KEEP_THR)
    pool=(q.bet==1)&(~base)
    rescue=pool & (pd.to_numeric(q['f__c_attack3_stretch'],errors='coerce')<=CANON_RESCUE_THR)
    return keep|rescue

def strict_pre_cols(q):
    bad=('pair_','p3','odds','comp','top_n','raw_top','ticket','hit','ret','profit','bet','invalid','result','settle')
    current=('attack3','wall12','_st','_ex','lap','turn','straight','orig','tilt','exh','tenji','display')
    cols=[]
    for c in q.columns:
        if not c.startswith('f__'): continue
        s=c.lower()
        if any(x in s for x in bad): continue
        if any(x in s for x in current): continue
        cols.append(c)
    return cols

def fit_rank(train, test, cols, ycol='_target', maxfeat=12):
    feats=[]; y=train[ycol].astype(int)
    for c in cols:
        x=pd.to_numeric(train[c],errors='coerce')
        a=x[y==1].dropna(); b=x[y==0].dropna()
        if len(a)<5 or len(b)<20: continue
        sd=x.std()
        if not np.isfinite(sd) or sd<=1e-12: continue
        eff=(a.mean()-b.mean())/sd
        if np.isfinite(eff): feats.append((abs(eff),eff,c))
    feats=sorted(feats,reverse=True)[:maxfeat]
    score=pd.Series(0.0,index=test.index); used=[]
    for _,eff,c in feats:
        tr=pd.to_numeric(train[c],errors='coerce'); te=pd.to_numeric(test[c],errors='coerce')
        med=tr.median(); sd=tr.std()
        if not np.isfinite(med): med=0.0
        if not np.isfinite(sd) or sd<=1e-12: continue
        score += np.sign(eff)*((te.fillna(med)-med)/sd).clip(-4,4); used.append(c)
    return score,used

def metrics(g):
    n=len(g); t=int(g._target.sum()) if n else 0
    return n,t,(t/n if n else np.nan)

def main():
    q=pd.read_csv(SRC,dtype={'race_code':str})
    q['date']=q.date.astype(str); q['month']=q.date.str[:7]
    q['_target']=final_mask(q).astype(int)
    if int(q._target.sum())!=182: raise RuntimeError(f'canonical target mismatch: {int(q._target.sum())} != 182')
    cols=strict_pre_cols(q)
    if not cols: raise RuntimeError('no strict PRE features')
    months=sorted(q.month.unique()); rec=[]
    for m in months:
        tr=q[q.month!=m]; te=q[q.month==m].copy(); score,used=fit_rank(tr,te,cols); te['_score']=score
        for frac in (.67,.80,.94):
            k=max(1,int(np.ceil(len(te)*frac))); g=te.nlargest(k,'_score'); n,t,r=metrics(g); total=int(te._target.sum())
            rec.append(dict(mode='LOMO',test_month=m,train_months='all_except_'+m,candidate_frac=frac,candidates=n,target_total=total,captured=t,recall=t/total if total else np.nan,precision=r,features=';'.join(used)))
    for i,m in enumerate(months):
        if i<2: continue
        tr=q[q.month.isin(months[:i])]; te=q[q.month==m].copy(); score,used=fit_rank(tr,te,cols); te['_score']=score
        for frac in (.67,.80,.94):
            k=max(1,int(np.ceil(len(te)*frac))); g=te.nlargest(k,'_score'); n,t,r=metrics(g); total=int(te._target.sum())
            rec.append(dict(mode='ROLLING',test_month=m,train_months=';'.join(months[:i]),candidate_frac=frac,candidates=n,target_total=total,captured=t,recall=t/total if total else np.nan,precision=r,features=';'.join(used)))
    out=pd.DataFrame(rec); out.to_csv(OUT,index=False)
    L=['# v247 strict PRE LOMO / rolling validation','',
       '- Target is canonical v243 182R policy.',
       '- PRE ranking uses only strict pre-exhibition features; current-race exhibition/ST/lap/turn/straight/original/tilt and attack/wall composites are rejected.',
       '- LOMO learns feature direction/magnitude on all months except the held-out month.',
       '- ROLLING learns only from chronologically prior months; first two months are warm-up and not tested.',
       '- Candidate fractions 0.67/0.80/0.94 approximate practical broad-screening levels.','',
       '|mode|fraction|test months|targets|captured|recall|','|---|---:|---:|---:|---:|---:|']
    for mode in ['LOMO','ROLLING']:
      for frac in (.67,.80,.94):
        z=out[(out['mode']==mode)&(out.candidate_frac==frac)]; total=int(z.target_total.sum()); cap=int(z.captured.sum())
        L.append(f'|{mode}|{frac:.2f}|{len(z)}|{total}|{cap}|{100*cap/total:.2f}%|')
    L+=['','## Monthly detail at 0.80','|mode|month|candidates|target|captured|recall|','|---|---|---:|---:|---:|---:|']
    for _,r in out[np.isclose(out.candidate_frac,.80)].iterrows():
        L.append(f"|{r['mode']}|{r.test_month}|{int(r.candidates)}|{int(r.target_total)}|{int(r.captured)}|{100*r.recall:.2f}%|")
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__': main()
