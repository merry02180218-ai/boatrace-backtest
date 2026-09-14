from pathlib import Path
import json, numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36_lda_stable_gate as w36
import research_v289_3head_wave40_blend_ranker as w40

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); BC=Path('v288_operational_pre_replay_94_baseline_codes.csv'); OUT=Path('research_v289_3head_wave43_conservative_rerank.json')
CUT=.365448
CS=[.03,.08,.15,.30]
THRESH=[.55,.60,.65,.70,.75,.80,.85]

# Correction model asks only: among Wave36 ranks 4..10, which candidate is the actual pair?
def boundary_rows(df,X,score):
    rows=[]; yy=[]; meta=[]
    for i in range(len(df)):
        order=np.argsort(-score[i]); actual=str(df.iloc[i].settle__actual_combo)
        for pos in range(3,10):
            j=order[pos]; c=base.COMBOS[j]
            # static race features + frozen Wave36 probability + rank + local score margins
            prev=score[i,order[pos-1]] if pos else score[i,j]
            nxt=score[i,order[pos+1]] if pos+1<len(order) else 0.
            feat=np.r_[X.iloc[i].to_numpy(dtype=float),score[i,j],pos+1,score[i,j]-nxt,prev-score[i,j]]
            rows.append(feat); yy.append(int(c==actual)); meta.append((i,pos,j,c))
    return np.asarray(rows,float),np.asarray(yy,int),meta

def fit_scores(train_df,trainX,train_score,test_df,testX,test_score,C):
    A,y,_=boundary_rows(train_df,trainX,train_score); B,_,meta=boundary_rows(test_df,testX,test_score)
    m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=C,class_weight='balanced',solver='lbfgs'))
    m.fit(A,y); p=m.predict_proba(B)[:,1]
    out=np.full((len(test_df),7),np.nan)
    for pr,(i,pos,j,c) in zip(p,meta): out[i,pos-3]=pr
    return out

def rerank(base_score,corr,thr):
    ans=[]
    for i,row in enumerate(base_score):
        order=list(np.argsort(-row)); best=None
        # only ranks6..10 may enter; rank4/5 are the only displacement zone
        for pos in range(5,10):
            pr=corr[i,pos-3]
            if np.isfinite(pr) and pr>=thr and (best is None or pr>best[0]): best=(pr,pos)
        if best is not None:
            j=order.pop(best[1]); order.insert(4,j)
        ans.append(';'.join(base.COMBOS[j] for j in order))
    return ans

def money(q,col):
    z=q.copy(); z['variant_return']=[base.dutch_return(r,str(r[col]).split(';')[:5]) for _,r in z.iterrows()]; m=base.block(z); m['max_drawdown_yen']=base.maxdd(z.sort_values(['date','race_code'])); return m

def hits(q,col): return {(str(r.race_code),str(r.actual)) for _,r in q.iterrows() if r.actual3==1 and str(r.actual) in str(r[col]).split(';')[:5]}

def main():
    d=pd.read_csv(SRC,dtype=str).fillna('');
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str)); d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
    X=base.build_static(d); y=d.settle__actual_combo.astype(str); d['actual']=y; d['actual3']=y.str.startswith('3-').astype(int); n=len(d)
    p3=np.full(n,np.nan); sc=np.full((n,len(base.COMBOS)),np.nan)
    specs=[('2026-03',d.month=='2026-02'),('2026-04',d.month<'2026-04'),('2026-05',d.month<'2026-05'),('2026-06',d.month<'2026-06'),('2026-07',d.month<='2026-06'),('2026-08',d.month<='2026-06')]
    for mo,trm in specs:
        te=d.month==mo; ti=np.flatnonzero(trm.to_numpy()); ei=np.flatnonzero(te.to_numpy()); a,b=w36.fit_predict(X.iloc[ti],y.iloc[ti],X.iloc[ei]); p3[ei]=a; sc[ei]=b
    d['p3']=p3; d['old_rank']=[';'.join(base.COMBOS[j] for j in np.argsort(-r)) if np.isfinite(r).any() else '' for r in sc]
    # March correction candidates are trained strictly on February.
    trm=d.month=='2026-02'; mm=d.month=='2026-03'; tri=np.flatnonzero(trm.to_numpy()); mi=np.flatnonzero(mm.to_numpy())
    # Need frozen Wave36 Feb in-sample score only as training representation; fit conditional model on Feb then score Feb/March.
    _,febsc=w36.fit_predict(X.iloc[tri],y.iloc[tri],X.iloc[tri]); march=d.iloc[mi].copy(); marchsc=sc[mi]; marchX=X.iloc[mi].reset_index(drop=True); feb=d.iloc[tri].reset_index(drop=True); febX=X.iloc[tri].reset_index(drop=True)
    march=march[march.p3>=CUT].copy(); sel=np.flatnonzero((d.iloc[mi].p3>=CUT).to_numpy()); marchsc=marchsc[sel]; marchX=marchX.iloc[sel].reset_index(drop=True); march=march.reset_index(drop=True); mid=len(march)//2
    cand=[]; cached={}
    for C in CS:
        corr=fit_scores(feb,febX,febsc,march,marchX,marchsc,C); cached[C]=corr
        for th in THRESH:
            col=rerank(marchsc,corr,th); q=march.copy(); q['new_rank']=col
            oh=hits(q,'old_rank'); nh=hits(q,'new_rank'); e=q.iloc[:mid]; l=q.iloc[mid:]
            em=w40.rank_metrics(e,'new_rank'); lm=w40.rank_metrics(l,'new_rank'); fm=w40.rank_metrics(q,'new_rank')
            cand.append({'C':C,'thr':th,'rank':fm,'early':em,'late':lm,'retained':len(oh&nh),'lost':len(oh-nh),'rescued':len(nh-oh),'net':len(nh)-len(oh),'worst_half_top5_rate':min(em['top5_rate'],lm['top5_rate'])})
    # Explicit preservation penalty: first minimize lost, then maximize net/rescued and stability.
    chosen=max(cand,key=lambda z:(-z['lost'],z['net'],z['rescued'],z['worst_half_top5_rate'],z['rank']['mrr'],-z['rank']['mean_rank'],z['thr']))
    C=chosen['C']; th=chosen['thr']
    # Frozen C/th; rolling historical training is permitted, no Apr-Jun selection/tuning.
    for mo,trm in specs[1:]:
        te=d.month==mo; ti=np.flatnonzero(trm.to_numpy()); ei=np.flatnonzero(te.to_numpy()); tr=d.iloc[ti].reset_index(drop=True); tx=X.iloc[ti].reset_index(drop=True); tst=d.iloc[ei].reset_index(drop=True); exx=X.iloc[ei].reset_index(drop=True)
        _,trsc=w36.fit_predict(tx,tr.settle__actual_combo.astype(str),tx)
        corr=fit_scores(tr,tx,trsc,tst,exx,sc[ei],C); d.loc[te,'new_rank']=rerank(sc[ei],corr,th)
    d.loc[mm,'new_rank']=rerank(marchsc,cached[C],th)
    ev=d[(d.month.isin(['2026-04','2026-05','2026-06']))&(d.p3>=CUT)].copy(); oh=hits(ev,'old_rank'); nh=hits(ev,'new_rank')
    out={'wave':'43-conservative-boundary-rerank','protocol':'Feb train; March OOS select; Apr-Jun one-shot','cut':CUT,'chosen':chosen,'march_candidates':cand,'apr_jun_old_rank':w40.rank_metrics(ev,'old_rank'),'apr_jun_new_rank':w40.rank_metrics(ev,'new_rank'),'old_vs_new':{'old_hits':len(oh),'new_hits':len(nh),'retained':len(oh&nh),'lost':len(oh-nh),'rescued':len(nh-oh),'net':len(nh)-len(oh)},'apr_jun_old_money':money(ev,'old_rank'),'apr_jun_new_money':money(ev,'new_rank'),'months':{},'v288_overlap':int(ev.race_code.astype(str).isin(ex).sum()),'september_forbidden':True}
    for mo in ['2026-04','2026-05','2026-06']:
        q=ev[ev.month==mo]; out['months'][mo]={'old':money(q,'old_rank'),'new':money(q,'new_rank')}
    sh=d[(d.month.isin(['2026-07','2026-08']))&(d.p3>=CUT)].copy(); out['jul_aug_nonpristine']={'rank':w40.rank_metrics(sh,'new_rank'),'money':money(sh,'new_rank')}
    out['decision']='RESEARCH_CANDIDATE' if out['old_vs_new']['net']>=0 and out['old_vs_new']['lost']<=2 and out['apr_jun_new_money']['roi_pct']>=out['apr_jun_old_money']['roi_pct'] else 'NO_ADOPTION'
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
