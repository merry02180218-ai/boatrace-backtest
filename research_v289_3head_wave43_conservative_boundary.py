from pathlib import Path
import json, numpy as np, pandas as pd
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36_lda_stable_gate as w36

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); BC=Path('v288_operational_pre_replay_94_baseline_codes.csv'); OUT=Path('research_v289_3head_wave43_conservative_boundary.json')
CUT=.365448
# conservative, score-only correction: promote one rank6-10 candidate only if its Wave36 probability is close to rank5.
RANKS=[6,7,8,9,10]; RATIOS=[.70,.75,.80,.85,.90,.95]

def rankstr(row): return ';'.join(base.COMBOS[j] for j in np.argsort(-row))
def corrected(scores, rank, ratio):
    order=np.argsort(-scores).tolist(); j=rank-1
    if len(order)<=j or scores[order[4]]<=0: return ';'.join(base.COMBOS[k] for k in order)
    if scores[order[j]]/scores[order[4]] >= ratio:
        x=order.pop(j); order.insert(4,x)
    return ';'.join(base.COMBOS[k] for k in order)
def metrics(q,col):
    h=q[q.actual3==1]; ranks=[]
    for _,r in h.iterrows(): ranks.append(str(r[col]).split(';').index(r.actual)+1)
    a=np.array(ranks) if ranks else np.array([])
    return {'heads':len(h),'top1':int((a<=1).sum()),'top3':int((a<=3).sum()),'top5':int((a<=5).sum()),'top8':int((a<=8).sum()),'top10':int((a<=10).sum()),'mrr':float(np.mean(1/a)) if len(a) else 0.,'mean_rank':float(a.mean()) if len(a) else 0.}
def money(q,col):
    z=q.copy(); z['variant_return']=[base.dutch_return(r,str(r[col]).split(';')[:5]) for _,r in z.iterrows()]; m=base.block(z); m['max_drawdown_yen']=base.maxdd(z.sort_values(['date','race_code'])); return m

def main():
    d=pd.read_csv(SRC,dtype=str).fillna('');
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str)); d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
    X=base.build_static(d); y=d.settle__actual_combo.astype(str); d['actual']=y; d['actual3']=y.str.startswith('3-').astype(int)
    n=len(d); p3=np.full(n,np.nan); sc=np.full((n,len(base.COMBOS)),np.nan)
    specs=[('2026-03',d.month=='2026-02'),('2026-04',d.month<'2026-04'),('2026-05',d.month<'2026-05'),('2026-06',d.month<'2026-06'),('2026-07',d.month<='2026-06'),('2026-08',d.month<='2026-06')]
    for mo,trm in specs:
        te=d.month==mo; ti=np.flatnonzero(trm.to_numpy()); ei=np.flatnonzero(te.to_numpy()); hp,cs=w36.fit_predict(X.iloc[ti],y.iloc[ti],X.iloc[ei]); p3[ei]=hp; sc[ei]=cs
    d['p3']=p3; d['old_rank']=[rankstr(x) if np.isfinite(x).any() else '' for x in sc]
    march=d[(d.month=='2026-03')&(d.p3>=CUT)].sort_values(['date','race_code']).reset_index(drop=True); mid=len(march)//2
    cand=[]
    for rank in RANKS:
      for ratio in RATIOS:
        col=f'c_{rank}_{ratio}'; d[col]=[corrected(sc[i],rank,ratio) if np.isfinite(sc[i]).any() else '' for i in range(n)]
        qm=d[(d.month=='2026-03')&(d.p3>=CUT)].sort_values(['date','race_code']).reset_index(drop=True)
        oldhit={(r.race_code,r.actual) for _,r in qm.iterrows() if r.actual3==1 and r.actual in r.old_rank.split(';')[:5]}; newhit={(r.race_code,r.actual) for _,r in qm.iterrows() if r.actual3==1 and r.actual in r[col].split(';')[:5]}
        full=metrics(qm,col); early=metrics(qm.iloc[:mid],col); late=metrics(qm.iloc[mid:],col)
        cand.append({'rank':rank,'ratio':ratio,'col':col,'full':full,'early':early,'late':late,'lost':len(oldhit-newhit),'rescued':len(newhit-oldhit),'net':len(newhit)-len(oldhit),'worst_half_top5':min(early['top5'],late['top5'])})
    # explicit preservation penalty: zero-loss candidates dominate; then net rescue, stability, full Top5, MRR.
    chosen=max(cand,key=lambda z:(z['lost']==0,z['net'],z['worst_half_top5'],z['full']['top5'],z['full']['mrr'],-z['rank'],z['ratio']))
    col=chosen['col']; ev=d[(d.month.isin(['2026-04','2026-05','2026-06']))&(d.p3>=CUT)].copy(); old=metrics(ev,'old_rank'); new=metrics(ev,col)
    oh={(r.race_code,r.actual) for _,r in ev.iterrows() if r.actual3==1 and r.actual in r.old_rank.split(';')[:5]}; nh={(r.race_code,r.actual) for _,r in ev.iterrows() if r.actual3==1 and r.actual in r[col].split(';')[:5]}
    months={mo:{'rank':metrics(ev[ev.month==mo],col),'money':money(ev[ev.month==mo],col)} for mo in ['2026-04','2026-05','2026-06']}
    out={'wave':'43-conservative-boundary','protocol':'Feb train; March OOS correction selection; Apr-Jun frozen one-shot','head_cut':CUT,'march_candidates':cand,'chosen':chosen,'apr_jun_old_rank':old,'apr_jun_new_rank':new,'old_vs_new':{'old_hits':len(oh),'new_hits':len(nh),'retained':len(oh&nh),'lost':len(oh-nh),'rescued':len(nh-oh)},'apr_jun_money':money(ev,col),'months':months,'v288_overlap':int(ev.race_code.astype(str).isin(ex).sum()),'september_forbidden':True}
    sh=d[(d.month.isin(['2026-07','2026-08']))&(d.p3>=CUT)].copy(); out['jul_aug_nonpristine']={'rank':metrics(sh,col),'money':money(sh,col)}
    out['decision']='RESEARCH_CANDIDATE' if len(nh)>len(oh) and out['apr_jun_money']['roi_pct']>=114.913 else 'NO_ADOPTION'
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
