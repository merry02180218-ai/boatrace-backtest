#!/usr/bin/env python3
from pathlib import Path
import numpy as np, pandas as pd

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT=Path('analysis_v287_3head_add_route_expand.csv')
SUM=Path('summary_v287_3head_add_route_expand.md')
KEEP=-0.1999999999999999
RESCUE=0.5672342857142857
WAKU34=0.4999999999999999
ST34=-0.6
MEETST=0.861111111111111

def target(q):
    b=(q.bet==1)&(q.p3>=.45)&q.raw_top_n.between(7,18)&q.comp_odds.between(3.05,4.0)
    return (b&(pd.to_numeric(q.f__c_b3_minus_b5_st,errors='coerce')>=KEEP))|((q.bet==1)&(~b)&(pd.to_numeric(q.f__c_attack3_stretch,errors='coerce')<=RESCUE))

def precols(q):
    bad=('pair_','p3','odds','comp','top_n','raw_top','ticket','hit','ret','profit','bet','invalid','result','settle')
    cur=('attack3','wall12','_st','_ex','lap','turn','straight','orig','tilt','exh','tenji','display')
    return [c for c in q if c.startswith('f__') and not any(x in c.lower() for x in bad) and not any(x in c.lower() for x in cur)]

def fit_score(tr,te,cs):
    y=tr._target.astype(int); fs=[]
    for c in cs:
        x=pd.to_numeric(tr[c],errors='coerce'); a=x[y==1].dropna(); b=x[y==0].dropna(); sd=x.std()
        if len(a)>=5 and len(b)>=20 and np.isfinite(sd) and sd>1e-12:
            e=(a.mean()-b.mean())/sd
            if np.isfinite(e): fs.append((abs(e),e,c))
    fs=sorted(fs,reverse=True)[:12]; s=pd.Series(0.,index=te.index)
    for _,e,c in fs:
        a=pd.to_numeric(tr[c],errors='coerce'); x=pd.to_numeric(te[c],errors='coerce'); med=a.median(); sd=a.std()
        if np.isfinite(sd) and sd>1e-12: s+=np.sign(e)*((x.fillna(med)-med)/sd).clip(-4,4)
    return s

def metrics(z):
    n=len(z); hit=int(pd.to_numeric(z.trifecta_hit,errors='coerce').fillna(0).sum()); ret=float(pd.to_numeric(z.ret,errors='coerce').fillna(0).sum()); stake=n*10000
    return dict(n=n,hits=hit,hit_rate=(100*hit/n if n else np.nan),stake=stake,ret=ret,profit=ret-stake,roi=(100*ret/stake if stake else np.nan))

def core_mask(z):
    return ((pd.to_numeric(z.f__c_b3_minus_b4_waku_st,errors='coerce')<=WAKU34)&
            (pd.to_numeric(z.f__c_b3_minus_b4_st,errors='coerce')>=ST34)&
            (pd.to_numeric(z.f__c_b3_meetst,errors='coerce')<=MEETST))

def main():
    q=pd.read_csv(SRC,dtype={'race_code':str}); q.date=q.date.astype(str); q['month']=q.date.str[:7]; q['_target']=target(q).astype(int)
    ms=sorted(q.month.unique()); pred=[]; cs=precols(q)
    for i,m in enumerate(ms):
        if i<2: continue
        tr=q[q.month.isin(ms[:i])]; te=q[q.month==m].copy(); te['_score']=fit_score(tr,te,cs); pred.append(te[['month','race_code','_score']])
    p=pd.concat(pred,ignore_index=True); p['_pct']=p.groupby('month')['_score'].rank(pct=True,method='first'); p['grade']=np.where(p._pct>=.70,'S',np.where(p._pct>=.20,'A','B'))
    z=q.merge(p[['race_code','grade']],on='race_code'); z=z[(z._target==1)&z.grade.isin(['S','A'])].copy()
    base=metrics(z)
    if (base['n'],base['hits'],round(base['ret']))!=(104,39,1200350): raise RuntimeError(f'canonical mismatch {base}')
    core=z[core_mask(z)].copy(); cm=metrics(core)
    if (cm['n'],cm['hits'],round(cm['ret']))!=(58,34,1048340): raise RuntimeError(f'58R core mismatch {cm}')

    train=z[z.month<='2026-06'].copy(); hold=z[z.month>='2026-07'].copy()
    tr_core=train[core_mask(train)].copy(); ho_core=hold[core_mask(hold)].copy()
    tr_pool=train[~core_mask(train)].copy(); ho_pool=hold[~core_mask(hold)].copy()

    # Independent A-route features: motor, ST/start, stretch/straight, wall, Waku10 and meeting-start context.
    allow=('motor','waku','stretch','straight','wall','meetst','_st','nst')
    deny=('hit','ret','profit','result','settle','odds','comp','ticket','pair_')
    feats=[]
    for c in z.columns:
        lc=c.lower()
        if c.startswith('f__') and any(k in lc for k in allow) and not any(k in lc for k in deny):
            x=pd.to_numeric(tr_pool[c],errors='coerce')
            if x.notna().sum()>=20 and x.nunique(dropna=True)>=3: feats.append(c)

    rows=[]
    for c in feats:
        vals=pd.to_numeric(tr_pool[c],errors='coerce').dropna()
        for qq in np.linspace(.05,.95,37):
            t=float(vals.quantile(qq))
            for op in ('<=','>='):
                def m(df):
                    x=pd.to_numeric(df[c],errors='coerce'); return x<=t if op=='<=' else x>=t
                ta=tr_pool[m(tr_pool)]; ha=ho_pool[m(ho_pool)]
                tc=pd.concat([tr_core,ta],ignore_index=True); hc=pd.concat([ho_core,ha],ignore_index=True); ac=pd.concat([tc,hc],ignore_index=True)
                mt,mh,ma=metrics(tc),metrics(hc),metrics(ac)
                # Target roughly 100-116 races overall without using Jul/Aug outcomes in selection.
                if not (90<=ma['n']<=125): continue
                rows.append(dict(feature=c,op=op,threshold=t,train_n=mt['n'],train_hits=mt['hits'],train_hit_rate=mt['hit_rate'],train_roi=mt['roi'],train_profit=mt['profit'],nonpristine_n=mh['n'],nonpristine_hits=mh['hits'],nonpristine_hit_rate=mh['hit_rate'],nonpristine_roi=mh['roi'],nonpristine_profit=mh['profit'],all_n=ma['n'],all_hits=ma['hits'],all_hit_rate=ma['hit_rate'],all_roi=ma['roi'],all_profit=ma['profit']))
    r=pd.DataFrame(rows)
    if r.empty: raise RuntimeError('no candidates')
    # Rank ONLY on Feb-Jun outcomes. Jul/Aug are report-only NON-PRISTINE evidence.
    r['train_ok']=(r.train_hit_rate>=55)&(r.train_roi>=150)
    r['distance100_116']=np.where(r.all_n<100,100-r.all_n,np.where(r.all_n>116,r.all_n-116,0))
    r=r.sort_values(['train_ok','distance100_116','train_hit_rate','train_roi','train_profit'],ascending=[False,True,False,False,False])
    r.to_csv(OUT,index=False)

    L=['# v287 3-head independent A-route expansion','',
       '- Frozen official core is unchanged: v249 S+A -> v243 -> Waku34 ST <= 0.4999999999999999 -> current 3-4 ST >= -0.6 -> b3 meetST <= 0.861111111111111 -> v242 Dutch.',
       '- Core assertion: 58 races / 34 hits / payout 1,048,340 / profit +468,340 / ROI 180.75%.',
       '- A-route is searched ONLY among races rejected by the 58R core.',
       '- Rule thresholds and ranking use Feb-Jun outcomes only.',
       '- Jul/Aug are NON-PRISTINE robustness evidence and do not affect ranking.',
       '- Candidate count target is 100-116 total races; count itself is not an outcome label.', '',
       '## Top train-selected candidates','',
       '|feature|op|threshold|All N|All hits|All hit%|All ROI|All profit|Feb-Jun N|Feb-Jun hit%|Feb-Jun ROI|Feb-Jun profit|Jul-Aug N|Jul-Aug hit%|Jul-Aug ROI|Jul-Aug profit|',
       '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,x in r.head(30).iterrows():
        L.append(f"|{x.feature}|{x.op}|{x.threshold:.15g}|{int(x.all_n)}|{int(x.all_hits)}|{x.all_hit_rate:.2f}%|{x.all_roi:.2f}%|{x.all_profit:+.0f}|{int(x.train_n)}|{x.train_hit_rate:.2f}%|{x.train_roi:.2f}%|{x.train_profit:+.0f}|{int(x.nonpristine_n)}|{x.nonpristine_hit_rate:.2f}%|{x.nonpristine_roi:.2f}%|{x.nonpristine_profit:+.0f}|")
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))

if __name__=='__main__': main()
