from pathlib import Path
import json, numpy as np, pandas as pd
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36_lda_stable_gate as w36
import research_v289_3head_wave39_pair_ranker as w39
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); BC=Path('v288_operational_pre_replay_94_baseline_codes.csv'); OUT=Path('research_v289_3head_wave40_blend_ranker.json')
CUT=.365448; K=5; PAIR_C=.08; ALPHAS=[0.0,0.25,0.5,0.75,1.0]

def rank_metrics(q,col):
 z=q[q.actual3==1].copy(); ranks=[]
 for a,t in zip(z.actual,z[col]):
  xs=t.split(';'); ranks.append(xs.index(a)+1 if a in xs else 21)
 n=len(ranks); r=np.array(ranks,float)
 return {'head_cases':n,'mrr':float(np.mean(1/r)) if n else 0.,'mean_rank':float(np.mean(r)) if n else 0.,'median_rank':float(np.median(r)) if n else 0.,'top1':int(np.sum(r<=1)),'top3':int(np.sum(r<=3)),'top5':int(np.sum(r<=5)),'top8':int(np.sum(r<=8)),'top10':int(np.sum(r<=10)),'top5_rate':float(np.mean(r<=5)) if n else 0.}

def top20(scores): return [';'.join(base.COMBOS[j] for j in np.argsort(-row)) for row in scores]
def money(q,col):
 z=q.copy(); z['variant_return']=[base.dutch_return(r,str(r[col]).split(';')[:5]) for _,r in z.iterrows()]; m=base.block(z); m['max_drawdown_yen']=base.maxdd(z.sort_values(['date','race_code'])); return m

def main():
 d=pd.read_csv(SRC,dtype=str).fillna('');
 if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
 ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str)); d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
 X=base.build_static(d); y=d.settle__actual_combo.astype(str); d['actual']=y; d['actual3']=y.str.startswith('3-').astype(int)
 if X.shape[1]!=63: raise RuntimeError('feature guard')
 n=len(d); p3=np.full(n,np.nan); bs=np.full((n,len(base.COMBOS)),np.nan); ps=np.full_like(bs,np.nan)
 specs=[('2026-03',d.month=='2026-02'),('2026-04',d.month<'2026-04'),('2026-05',d.month<'2026-05'),('2026-06',d.month<'2026-06'),('2026-07',d.month<='2026-06'),('2026-08',d.month<='2026-06')]
 for mo,trm in specs:
  tem=d.month==mo; ti=np.flatnonzero(trm.to_numpy()); ei=np.flatnonzero(tem.to_numpy()); hp,cs=w36.fit_predict(X.iloc[ti],y.iloc[ti],X.iloc[ei]); p3[ei]=hp; bs[ei]=cs; ps[ei]=w39.fit_pair(d.iloc[ti],d.iloc[ei],PAIR_C)
 d['p3']=p3; d['old_rank']=top20(bs)
 for a in ALPHAS:
  sc=a*bs+(1-a)*ps; d[f'rank_a{a}']=top20(sc)
 march=d[(d.month=='2026-03')&(d.p3>=CUT)].sort_values(['date','race_code']).reset_index(drop=True); mid=len(march)//2; cand=[]
 oldm=rank_metrics(march,'old_rank')
 for a in ALPHAS:
  col=f'rank_a{a}'; full=rank_metrics(march,col); early=rank_metrics(march.iloc[:mid],col); late=rank_metrics(march.iloc[mid:],col)
  oldhit={(r.race_code,r.actual) for _,r in march.iterrows() if r.actual3==1 and r.actual in r.old_rank.split(';')[:5]}; newhit={(r.race_code,r.actual) for _,r in march.iterrows() if r.actual3==1 and r.actual in r[col].split(';')[:5]}
  cand.append({'alpha_baseline':a,'full':full,'early':early,'late':late,'worst_half_top5_rate':min(early['top5_rate'],late['top5_rate']),'old_hits_lost':len(oldhit-newhit),'old_misses_rescued':len(newhit-oldhit)})
 chosen=max(cand,key=lambda z:(z['worst_half_top5_rate'],-z['old_hits_lost'],z['full']['top5_rate'],z['full']['mrr'])); col=f"rank_a{chosen['alpha_baseline']}"
 out={'wave':'40-blended-opponent-ranker','protocol':'Feb train/design; March OOS selection only; Apr-Jun frozen pristine','head_cut':CUT,'pair_C_preselected_from_March':PAIR_C,'feature_count_static':63,'pair_feature_count':45,'march_old':oldm,'march_candidates':cand,'chosen':chosen,'months':{},'apr_jun_rank':None,'apr_jun_money':None,'old_vs_new':{}}
 evaldf=d[(d.month.isin(['2026-04','2026-05','2026-06']))&(d.p3>=CUT)].copy()
 for mo in ['2026-04','2026-05','2026-06']:
  q=evaldf[evaldf.month==mo]; out['months'][mo]={'rank':rank_metrics(q,col),'money':money(q,col)}
 out['apr_jun_rank']=rank_metrics(evaldf,col); out['apr_jun_money']=money(evaldf,col)
 oldhit={(r.race_code,r.actual) for _,r in evaldf.iterrows() if r.actual3==1 and r.actual in r.old_rank.split(';')[:5]}; newhit={(r.race_code,r.actual) for _,r in evaldf.iterrows() if r.actual3==1 and r.actual in r[col].split(';')[:5]}
 out['old_vs_new']={'old_top5_hits':len(oldhit),'new_top5_hits':len(newhit),'old_hits_retained':len(oldhit&newhit),'old_hits_lost':len(oldhit-newhit),'old_misses_rescued':len(newhit-oldhit)}
 out['v288_overlap']=int(evaldf.race_code.astype(str).isin(ex).sum()); out['september_forbidden']=True
 if out['v288_overlap']: raise RuntimeError('v288 overlap')
 # shadow diagnostic only
 sh=d[(d.month.isin(['2026-07','2026-08']))&(d.p3>=CUT)].copy(); out['jul_aug_nonpristine']={'rank':rank_metrics(sh,col),'money':money(sh,col)}
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
