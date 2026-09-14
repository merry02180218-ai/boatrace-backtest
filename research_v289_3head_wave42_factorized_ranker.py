from pathlib import Path
import json, numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36_lda_stable_gate as w36
import research_v289_3head_wave40_blend_ranker as w40

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); BC=Path('v288_operational_pre_replay_94_baseline_codes.csv'); OUT=Path('research_v289_3head_wave42_factorized_ranker.json')
CUT=.365448; CS=[.02,.05,.10,.15,.30]

def pipe(C): return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=1500,C=C,solver='lbfgs'))
def fit_factor(trainX,train_combo,testX,C):
    sec=train_combo.str.split('-').str[1]; third=train_combo.str.split('-').str[2]
    m2=pipe(C).fit(trainX,sec); p2=m2.predict_proba(testX); d2={c:i for i,c in enumerate(m2.classes_)}
    mods={}
    for a in ['1','2','4','5','6']:
        mask=sec.eq(a); mods[a]=pipe(C).fit(trainX.loc[mask],third.loc[mask])
    s=np.zeros((len(testX),len(base.COMBOS)))
    for j,c in enumerate(base.COMBOS):
        _,a,b=c.split('-'); m3=mods[a]; d3={cc:i for i,cc in enumerate(m3.classes_)}; p3=m3.predict_proba(testX)[:,d3[b]] if b in d3 else 0.; s[:,j]=p2[:,d2[a]]*p3
    return s

def top20(scores): return [';'.join(base.COMBOS[j] for j in np.argsort(-row)) for row in scores]
def money(q,col):
    z=q.copy(); z['variant_return']=[base.dutch_return(r,str(r[col]).split(';')[:5]) for _,r in z.iterrows()]; m=base.block(z); m['max_drawdown_yen']=base.maxdd(z.sort_values(['date','race_code'])); return m

def score_month(d,X,y,mo,trm,C=None):
    tem=d.month==mo; ti=np.flatnonzero(trm.to_numpy()); ei=np.flatnonzero(tem.to_numpy()); hp,old=w36.fit_predict(X.iloc[ti],y.iloc[ti],X.iloc[ei]); out=d.iloc[ei].copy(); out['p3']=hp; out['old_rank']=top20(old)
    if C is not None:
        hc=y.iloc[ti].str.startswith('3-'); out['new_rank']=top20(fit_factor(X.iloc[ti][hc.to_numpy()],y.iloc[ti][hc.to_numpy()],X.iloc[ei],C))
    return out

def main():
    d=pd.read_csv(SRC,dtype=str).fillna('');
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str)); d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
    X=base.build_static(d); y=d.settle__actual_combo.astype(str); d['actual']=y; d['actual3']=y.str.startswith('3-').astype(int)
    march=score_month(d,X,y,'2026-03',d.month=='2026-02').sort_values(['date','race_code']).reset_index(drop=True); qm=march[march.p3>=CUT].reset_index(drop=True); oldm=w40.rank_metrics(qm,'old_rank'); cand=[]
    ti=np.flatnonzero((d.month=='2026-02').to_numpy()); ei=np.flatnonzero((d.month=='2026-03').to_numpy()); hc=y.iloc[ti].str.startswith('3-')
    for C in CS:
        raw=d.iloc[ei].copy(); raw['p3']=march.set_index('race_code').reindex(raw.race_code).p3.to_numpy(); raw['actual']=raw.settle__actual_combo.astype(str); raw['actual3']=raw.actual.str.startswith('3-').astype(int); raw['new_rank']=top20(fit_factor(X.iloc[ti][hc.to_numpy()],y.iloc[ti][hc.to_numpy()],X.iloc[ei],C)); q=raw[raw.p3>=CUT].sort_values(['date','race_code']).reset_index(drop=True); mid=len(q)//2
        full=w40.rank_metrics(q,'new_rank'); early=w40.rank_metrics(q.iloc[:mid],'new_rank'); late=w40.rank_metrics(q.iloc[mid:],'new_rank'); oldhit={(r.race_code,r.actual) for _,r in qm.iterrows() if r.actual3==1 and r.actual in r.old_rank.split(';')[:5]}; newhit={(r.race_code,r.actual) for _,r in q.iterrows() if r.actual3==1 and r.actual in r.new_rank.split(';')[:5]}
        cand.append({'C':C,'full':full,'early':early,'late':late,'worst_half_top5_rate':min(early['top5_rate'],late['top5_rate']),'old_hits_lost':len(oldhit-newhit),'old_misses_rescued':len(newhit-oldhit)})
    chosen=max(cand,key=lambda z:(z['worst_half_top5_rate'],z['full']['top5_rate'],z['full']['mrr'],-z['full']['mean_rank'],-z['old_hits_lost'])); C=chosen['C']
    parts=[]
    for mo,trm in [('2026-04',d.month<'2026-04'),('2026-05',d.month<'2026-05'),('2026-06',d.month<'2026-06'),('2026-07',d.month<='2026-06'),('2026-08',d.month<='2026-06')]: parts.append(score_month(d,X,y,mo,trm,C))
    z=pd.concat(parts,ignore_index=True); out={'wave':'42-factorized-second-third-ranker','protocol':'Feb train/design; March OOS selection only; Apr-Jun frozen evaluation','head_cut':CUT,'march_old':oldm,'march_candidates':cand,'chosen':chosen,'months':{}}
    ev=z[z.month.isin(['2026-04','2026-05','2026-06'])&(z.p3>=CUT)].copy()
    for mo in ['2026-04','2026-05','2026-06']:
        q=ev[ev.month==mo]; out['months'][mo]={'rank':w40.rank_metrics(q,'new_rank'),'money':money(q,'new_rank')}
    out['apr_jun_rank']=w40.rank_metrics(ev,'new_rank'); out['apr_jun_money']=money(ev,'new_rank'); oldhit={(r.race_code,r.actual) for _,r in ev.iterrows() if r.actual3==1 and r.actual in r.old_rank.split(';')[:5]}; newhit={(r.race_code,r.actual) for _,r in ev.iterrows() if r.actual3==1 and r.actual in r.new_rank.split(';')[:5]}; out['old_vs_new']={'old_top5_hits':len(oldhit),'new_top5_hits':len(newhit),'old_hits_retained':len(oldhit&newhit),'old_hits_lost':len(oldhit-newhit),'old_misses_rescued':len(newhit-oldhit)}
    out['v288_overlap']=int(ev.race_code.astype(str).isin(ex).sum()); out['september_forbidden']=True; sh=z[z.month.isin(['2026-07','2026-08'])&(z.p3>=CUT)].copy(); out['jul_aug_nonpristine']={'rank':w40.rank_metrics(sh,'new_rank'),'money':money(sh,'new_rank')}; out['decision']='RESEARCH_CANDIDATE' if out['apr_jun_rank']['top5']>87 and out['apr_jun_money']['roi_pct']>=110 else 'NO_ADOPTION'
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
