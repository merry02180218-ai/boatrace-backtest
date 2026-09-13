from __future__ import annotations
import json,re
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
OLD=Path('analysis_v289_3head_wave19_full_universe_payout_enriched.csv')
OUT=Path('analysis_v289_3head_wave27_leakfree_exactorder.csv')
OUTJ=Path('research_v289_3head_wave27_leakfree_exactorder.json')
OUTM=Path('research_v289_3head_wave27_leakfree_exactorder.md')
METRICS=['全国平均ST','全国勝率','全国2連対率','全国3連対率','当地勝率','当地2連対率','モーター2連対率','モーター3連対率','ボート2連対率']
COMBOS=[f'3-{a}-{b}' for a in [1,2,4,5,6] for b in [1,2,4,5,6] if b!=a]
CLASSES=['OTHER']+COMBOS
THRESHOLDS=[.18,.20,.22,.24,.26,.28,.30,.32,.35,.38,.40]
KS=[3,5,7,10,15,20]
BASELINE={'races':94,'hits':52,'stake_yen':940000,'payout_yen':1622070,'profit_yen':682070,'roi_pct':172.560638}

def num(s): return pd.to_numeric(s.astype(str).str.replace('%','',regex=False),errors='coerce')
def digits(s): return pd.to_numeric(s.astype(str).str.extract(r'(\d+)')[0],errors='coerce')

def build_static_features(df):
    X=pd.DataFrame(index=df.index)
    for met in METRICS:
        vals={}
        for b in range(1,7):
            c=f'card__艇{b}_{met}'
            if c in df: vals[b]=num(df[c])
        if 3 not in vals: continue
        X[f'b3_{met}']=vals[3]
        oth=pd.concat([vals[b] for b in vals if b!=3],axis=1)
        X[f'b3_minus_mean_{met}']=vals[3]-oth.mean(axis=1)
        for b in [1,2,4,5,6]:
            if b in vals: X[f'b3_minus_b{b}_{met}']=vals[3]-vals[b]
    forbidden=('節D','着順','closing','settle','払戻','結果','actual','odds')
    bad=[c for c in X.columns if any(x.lower() in c.lower() for x in forbidden)]
    if bad: raise RuntimeError(f'forbidden feature(s): {bad[:10]}')
    if X.shape[1]!=63: raise RuntimeError(f'expected 63 static features got {X.shape[1]}')
    return X.replace([np.inf,-np.inf],np.nan)

def target(s):
    s=str(s); return s if s in COMBOS else 'OTHER'

def fit(X,y):
    m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=350,C=.35,solver='lbfgs'))
    m.fit(X,y); return m

def probs(m,X):
    p=m.predict_proba(X); out=np.zeros((len(X),len(CLASSES)))
    for j,c in enumerate(m.classes_):
        if c in CLASSES: out[:,CLASSES.index(c)]=p[:,j]
    return out

def dutch_return(r,tickets):
    try: od=json.loads(r['closing_odds__json'])
    except: return 0
    try: odds=np.array([float(od[c]) for c in tickets],dtype=float)
    except: return 0
    if len(odds)==0 or np.any(odds<=1): return 0
    raw=100*(1/odds)/(1/odds).sum(); units=np.floor(raw).astype(int); rem=100-int(units.sum())
    if rem>0:
        frac=raw-units
        for i in np.argsort(-frac)[:rem]: units[i]+=1
    ac=str(r['settle__actual_combo'])
    if ac not in tickets: return 0
    pay=int(float(r['settle__trifecta_payout_100_yen'] or 0))
    return int(units[tickets.index(ac)]*pay)

def block(g):
    n=len(g); payout=int(g['variant_return'].sum()) if n else 0; stake=n*10000; hits=int((g['variant_return']>0).sum()) if n else 0
    return {'races':n,'hits':hits,'hit_rate_pct':100*hits/n if n else None,'stake_yen':stake,'payout_yen':payout,'profit_yen':payout-stake,'roi_pct':100*payout/stake if stake else None}

def maxdd(g):
    if g.empty:return 0
    pnl=(g['variant_return'].astype(float)-10000).cumsum(); return float((pnl.cummax()-pnl).max())

def score(base,t,k):
    q=base[base['p3']>=t].copy()
    rets=[]; tsall=[]
    for _,r in q.iterrows():
        ts=str(r[f'top{k}']).split(';') if r[f'top{k}'] else []
        tsall.append(';'.join(ts)); rets.append(dutch_return(r,ts))
    q['tickets']=tsall; q['variant_return']=rets
    m=block(q); monthly={mo:block(g) for mo,g in q.groupby('month')}
    m.update({'threshold':t,'k':k,'monthly':monthly,'min_month_roi_pct':min((x['roi_pct'] for x in monthly.values()),default=None),'red_months':sum(1 for x in monthly.values() if x['roi_pct']<100),'max_drawdown_yen':maxdd(q.sort_values(['date','race_code']))})
    return q,m

def leak_signature(df):
    # Historical race_cards appear to contain current-race outcomes in 節D slots for many rows.
    # This is a diagnostic only; Wave27 does not use any 節D field at all.
    cur=digits(df['race']); fin=np.full(len(df),'',dtype=object)
    for d in range(1,8):
        for s in range(1,3):
            rc=f'card__艇3_節D{d}走{s}_R番号'; fc=f'card__艇3_節D{d}走{s}_枠'; ff=f'card__艇3_節D{d}走{s}_着順'
            if rc not in df: continue
            m=(fin=='') & (digits(df[rc])==cur).to_numpy() & (digits(df[fc])==3).to_numpy() & df[ff].astype(str).str.strip().ne('').to_numpy()
            fin[m]=df.loc[m,ff].astype(str)
    have=fin!=''; f1=np.zeros(len(df),dtype=bool); f1[have]=digits(pd.Series(fin[have])).eq(1).to_numpy()
    actual=df['settle__actual_combo'].astype(str).str.startswith('3-').to_numpy()
    return {'matched_rows':int(have.sum()),'matched_share':float(have.mean()),'finish1_vs_actual_head3_agreement':float((f1[have]==actual[have]).mean()) if have.any() else None}

def main():
    df=pd.read_csv(SRC,dtype=str).fillna('')
    if df['date'].max()>'2026-08-31': raise RuntimeError('September forbidden')
    audit=leak_signature(df)
    old=pd.read_csv(OLD,dtype=str).fillna(''); exclusion=set(old['race_code'].astype(str))
    if len(exclusion)!=678: raise RuntimeError(f'expected exclusion 678 got {len(exclusion)}')
    df=df[~df['race_code'].astype(str).isin(exclusion)].copy()
    df=df[(df['settle__usable']=='1')&(df['closing_odds__ok']=='1')].copy(); df['month']=df['date'].str[:7]
    X=build_static_features(df); y=df['settle__actual_combo'].map(target)
    P=np.full((len(df),len(CLASSES)),np.nan); pos={idx:i for i,idx in enumerate(df.index)}
    for mo in ['2026-04','2026-05','2026-06']:
        tr=df['month']<mo; te=df['month']==mo; pp=probs(fit(X.loc[tr],y.loc[tr]),X.loc[te])
        for j,idx in enumerate(df.index[te]): P[pos[idx],:]=pp[j]
    frozen=fit(X.loc[df['month']<='2026-06'],y.loc[df['month']<='2026-06'])
    for mo in ['2026-07','2026-08']:
        te=df['month']==mo; pp=probs(frozen,X.loc[te])
        for j,idx in enumerate(df.index[te]): P[pos[idx],:]=pp[j]
    df['p3']=np.nansum(P[:,1:],axis=1)
    for k in KS:
        arr=[]
        for i in range(len(df)):
            order=np.argsort(-P[i,1:])[:k]; arr.append(';'.join(COMBOS[j] for j in order))
        df[f'top{k}']=arr
    # Strict selection: tune only on April; May-Jun are untouched holdout.
    tune=df[df['month']=='2026-04'].copy(); variants=[]
    for k in KS:
        for t in THRESHOLDS:
            _,m=score(tune,t,k)
            if m['races']>=100: variants.append(m)
    if not variants: raise RuntimeError('no April tuning variant >=100R')
    chosen=max(variants,key=lambda z:z['roi_pct']); t=chosen['threshold']; k=chosen['k']
    hold=df[df['month'].isin(['2026-05','2026-06'])].copy(); sel_h,hm=score(hold,t,k)
    shadow=df[df['month'].isin(['2026-07','2026-08'])].copy(); sel_s,sm=score(shadow,t,k)
    selected=pd.concat([sel_h,sel_s],ignore_index=True); selected.to_csv(OUT,index=False,encoding='utf-8-sig')
    cmb={'races':BASELINE['races']+hm['races'],'hits':BASELINE['hits']+hm['hits'],'stake_yen':BASELINE['stake_yen']+hm['stake_yen'],'payout_yen':BASELINE['payout_yen']+hm['payout_yen']}; cmb['profit_yen']=cmb['payout_yen']-cmb['stake_yen']; cmb['roi_pct']=100*cmb['payout_yen']/cmb['stake_yen']
    decision='SHADOW_CANDIDATE' if hm['races']>=100 and hm['roi_pct']>=BASELINE['roi_pct'] and hm['red_months']==0 else 'NO_ADOPTION'
    out={'wave':'27-leakfree-exactorder','source_rows':len(df),'feature_count':X.shape[1],'feature_policy':'STATIC_CARD_ONLY_NO_SECTION_HISTORY','wave26_leak_signature':audit,'tuning_april':chosen,'strict_holdout_may_june':hm,'shadow_non_pristine_jul_aug':sm,'legacy_overlap':0,'baseline':BASELINE,'combined_baseline_plus_holdout':cmb,'decision':decision,'notes':['Wave26 recent ST/finish section-history features are removed entirely because historical race_cards show a strong current-result signature.','Threshold/K tuned only on April. May-Jun are untouched holdout for decision.','Jul-Aug remain NON-PRISTINE shadow. Closing odds are staking only. September forbidden.']}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave27 leak-free exact-order audit','',f"- Wave26 leak signature: **{audit['matched_rows']} matched rows / agreement {100*audit['finish1_vs_actual_head3_agreement']:.3f}%**",f'- features: **{X.shape[1]} static card-only; all 節D ST/着順 removed**',f"- April tune chose: **p3>={t:.2f}, top{k}**",f"- strict May-Jun holdout: **{hm['races']}R / {hm['hits']} hits / ROI {hm['roi_pct']:.3f}% / profit {hm['profit_yen']:+,} yen**",f"- min-month ROI: **{hm['min_month_roi_pct']:.3f}%** / red months **{hm['red_months']}** / max DD **{hm['max_drawdown_yen']:,.0f} yen**",f"- Jul-Aug NON-PRISTINE shadow: **{sm['races']}R / {sm['hits']} hits / ROI {sm['roi_pct']:.3f}% / profit {sm['profit_yen']:+,} yen**",f"- baseline + strict holdout: **{cmb['races']}R / ROI {cmb['roi_pct']:.3f}% / profit {cmb['profit_yen']:+,} yen**",'- legacy overlap: **0**',f'- decision: **{decision}**','','## Holdout monthly']
    for mo,x in hm['monthly'].items(): lines.append(f"- {mo}: {x['races']}R / {x['hits']} hits / ROI {x['roi_pct']:.3f}% / profit {x['profit_yen']:+,} yen")
    lines += ['','## NON-PRISTINE shadow monthly']
    for mo,x in sm['monthly'].items(): lines.append(f"- {mo}: {x['races']}R / {x['hits']} hits / ROI {x['roi_pct']:.3f}% / profit {x['profit_yen']:+,} yen")
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines),flush=True)

if __name__=='__main__': main()
