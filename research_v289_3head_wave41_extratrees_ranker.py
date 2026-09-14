from pathlib import Path
import json, numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.pipeline import make_pipeline
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36_lda_stable_gate as w36
import research_v289_3head_wave40_blend_ranker as w40

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); BC=Path('v288_operational_pre_replay_94_baseline_codes.csv'); OUT=Path('research_v289_3head_wave41_extratrees_ranker.json')
CUT=.365448; LEAVES=[5,10,15,20,30]; MAX_FEATURES=.7; TREES=240

def pair_features_fast(df):
    n=len(df); mats=[]
    for met in base.METRICS:
        vals={b:base.num(df[f'card__艇{b}_{met}']).to_numpy() for b in range(1,7)}
        v3=np.repeat(vals[3],len(base.COMBOS))
        second=np.concatenate([[vals[int(c.split('-')[1])][i] for c in base.COMBOS] for i in range(n)])
        third=np.concatenate([[vals[int(c.split('-')[2])][i] for c in base.COMBOS] for i in range(n)])
        mats += [second,third,second-third,v3-second,v3-third]
    return pd.DataFrame(np.vstack(mats).T).replace([np.inf,-np.inf],np.nan)

def fit_tree(train_df,test_df,leaf):
    tr=train_df[train_df.settle__actual_combo.astype(str).str.startswith('3-')].copy(); Xtr=pair_features_fast(tr); yy=[]
    for c in tr.settle__actual_combo.astype(str): yy.extend([int(x==c) for x in base.COMBOS])
    m=make_pipeline(SimpleImputer(strategy='median'),ExtraTreesClassifier(n_estimators=TREES,min_samples_leaf=leaf,max_features=MAX_FEATURES,class_weight='balanced',random_state=41,n_jobs=-1))
    m.fit(Xtr,np.array(yy)); return m.predict_proba(pair_features_fast(test_df))[:,1].reshape(len(test_df),len(base.COMBOS))

def top20(scores): return [';'.join(base.COMBOS[j] for j in np.argsort(-row)) for row in scores]
def money(q,col):
    z=q.copy(); z['variant_return']=[base.dutch_return(r,str(r[col]).split(';')[:5]) for _,r in z.iterrows()]; m=base.block(z); m['max_drawdown_yen']=base.maxdd(z.sort_values(['date','race_code'])); return m

def score_month(d,X,y,mo,trm,leaf=None):
    tem=d.month==mo; ti=np.flatnonzero(trm.to_numpy()); ei=np.flatnonzero(tem.to_numpy()); hp,old=w36.fit_predict(X.iloc[ti],y.iloc[ti],X.iloc[ei]); out=d.iloc[ei].copy(); out['p3']=hp; out['old_rank']=top20(old)
    if leaf is not None: out['new_rank']=top20(fit_tree(d.iloc[ti],d.iloc[ei],leaf))
    return out

def main():
    d=pd.read_csv(SRC,dtype=str).fillna('');
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str)); d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
    X=base.build_static(d); y=d.settle__actual_combo.astype(str); d['actual']=y; d['actual3']=y.str.startswith('3-').astype(int)
    march=score_month(d,X,y,'2026-03',d.month=='2026-02').sort_values(['date','race_code']).reset_index(drop=True); raw_march=d[d.month=='2026-03']; mid=len(march[march.p3>=CUT])//2
    oldm=w40.rank_metrics(march[march.p3>=CUT],'old_rank'); cand=[]
    for leaf in LEAVES:
        s=fit_tree(d[d.month=='2026-02'],raw_march,leaf); tmp=raw_march.copy(); tmp['p3']=march.set_index('race_code').reindex(tmp.race_code).p3.to_numpy(); tmp['actual']=tmp.settle__actual_combo.astype(str); tmp['actual3']=tmp.actual.str.startswith('3-').astype(int); tmp['new_rank']=top20(s); q=tmp[tmp.p3>=CUT].sort_values(['date','race_code']).reset_index(drop=True); m=len(q)//2
        full=w40.rank_metrics(q,'new_rank'); early=w40.rank_metrics(q.iloc[:m],'new_rank'); late=w40.rank_metrics(q.iloc[m:],'new_rank'); oldq=march[march.p3>=CUT].sort_values(['date','race_code']).reset_index(drop=True)
        oldhit={(r.race_code,r.actual) for _,r in oldq.iterrows() if r.actual3==1 and r.actual in r.old_rank.split(';')[:5]}; newhit={(r.race_code,r.actual) for _,r in q.iterrows() if r.actual3==1 and r.actual in r.new_rank.split(';')[:5]}
        cand.append({'leaf':leaf,'full':full,'early':early,'late':late,'worst_half_top5_rate':min(early['top5_rate'],late['top5_rate']),'old_hits_lost':len(oldhit-newhit),'old_misses_rescued':len(newhit-oldhit)})
    chosen=max(cand,key=lambda z:(z['worst_half_top5_rate'],z['full']['top5_rate'],z['full']['mrr'],-z['full']['mean_rank'],-z['old_hits_lost'])); leaf=chosen['leaf']
    parts=[]
    for mo,trm in [('2026-04',d.month<'2026-04'),('2026-05',d.month<'2026-05'),('2026-06',d.month<'2026-06'),('2026-07',d.month<='2026-06'),('2026-08',d.month<='2026-06')]: parts.append(score_month(d,X,y,mo,trm,leaf))
    z=pd.concat(parts,ignore_index=True); out={'wave':'41-extratrees-opponent-ranker','protocol':'Feb train/design; March OOS selection only; Apr-Jun frozen evaluation','head_cut':CUT,'pair_feature_count':45,'n_trees':TREES,'max_features':MAX_FEATURES,'march_old':oldm,'march_candidates':cand,'chosen':chosen,'months':{}}
    evaldf=z[z.month.isin(['2026-04','2026-05','2026-06'])&(z.p3>=CUT)].copy()
    for mo in ['2026-04','2026-05','2026-06']:
        q=evaldf[evaldf.month==mo]; out['months'][mo]={'rank':w40.rank_metrics(q,'new_rank'),'money':money(q,'new_rank')}
    out['apr_jun_rank']=w40.rank_metrics(evaldf,'new_rank'); out['apr_jun_money']=money(evaldf,'new_rank')
    oldhit={(r.race_code,r.actual) for _,r in evaldf.iterrows() if r.actual3==1 and r.actual in r.old_rank.split(';')[:5]}; newhit={(r.race_code,r.actual) for _,r in evaldf.iterrows() if r.actual3==1 and r.actual in r.new_rank.split(';')[:5]}
    out['old_vs_new']={'old_top5_hits':len(oldhit),'new_top5_hits':len(newhit),'old_hits_retained':len(oldhit&newhit),'old_hits_lost':len(oldhit-newhit),'old_misses_rescued':len(newhit-oldhit)}; out['v288_overlap']=int(evaldf.race_code.astype(str).isin(ex).sum()); out['september_forbidden']=True
    sh=z[z.month.isin(['2026-07','2026-08'])&(z.p3>=CUT)].copy(); out['jul_aug_nonpristine']={'rank':w40.rank_metrics(sh,'new_rank'),'money':money(sh,'new_rank')}; out['decision']='RESEARCH_CANDIDATE' if out['apr_jun_rank']['top5']>87 and out['apr_jun_money']['roi_pct']>=110 else 'NO_ADOPTION'
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
