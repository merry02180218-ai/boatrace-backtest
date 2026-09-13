from pathlib import Path
import json, numpy as np, pandas as pd
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36_lda_stable_gate as w36
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); BC=Path('v288_operational_pre_replay_94_baseline_codes.csv'); CUT=.365448; K=5

def main():
 d=pd.read_csv(SRC,dtype=str).fillna(''); ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str)); d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
 X=base.build_static(d); y=d.settle__actual_combo.astype(str); d['actual']=y; d['actual3']=y.str.startswith('3-').astype(int); p=np.full(len(d),np.nan); score=np.full((len(d),len(base.COMBOS)),np.nan)
 specs=[('2026-03',d.month=='2026-02'),('2026-04',d.month<'2026-04'),('2026-05',d.month<'2026-05'),('2026-06',d.month<'2026-06'),('2026-07',d.month<='2026-06'),('2026-08',d.month<='2026-06')]
 for mo,trm in specs:
  tem=d.month==mo; tr=np.flatnonzero(trm.to_numpy()); te=np.flatnonzero(tem.to_numpy()); a,s=w36.fit_predict(X.iloc[tr],y.iloc[tr],X.iloc[te]); p[te]=a; score[te]=s
 d['p3']=p; tops=[]
 for i in range(len(d)):
  if not np.isfinite(score[i]).any(): tops.append(''); continue
  idx=np.argsort(-np.nan_to_num(score[i],nan=-1))[:K]; tops.append(';'.join(base.COMBOS[j] for j in idx))
 d['top5']=tops; d=d[d.p3>=CUT].copy(); out={}
 for mo in ['2026-04','2026-05','2026-06','2026-07','2026-08']:
  z=d[d.month==mo].sort_values(['date','race_code']); h=len(z)//2; out[mo]={}
  for tag,q in [('all',z),('early',z.iloc[:h]),('late',z.iloc[h:])]:
   q=q.copy(); q['ret']=[base.dutch_return(r,str(r.top5).split(';') if r.top5 else []) for _,r in q.iterrows()]; ticket=np.array([str(a) in str(t).split(';') for a,t in zip(q.actual,q.top5)]); wins=sorted(q.loc[q.ret>0,'ret'].astype(int).tolist(),reverse=True); total=sum(wins); stake=len(q)*10000; payout=int(q.ret.sum())
   out[mo][tag]={'races':len(q),'head_hits':int(q.actual3.sum()),'head_rate':float(q.actual3.mean()) if len(q) else 0.0,'ticket_hits':int(ticket.sum()),'ticket_rate':float(ticket.mean()) if len(q) else 0.0,'head_correct_order_miss':int(((q.actual3==1)&(~ticket)).sum()),'roi_pct':100*payout/stake if stake else 0.0,'profit_yen':payout-stake,'top1_share':wins[0]/total if total else 0.0,'top3_share':sum(wins[:3])/total if total else 0.0,'roi_no_top1':100*(total-sum(wins[:1]))/stake if stake else 0.0,'roi_no_top3':100*(total-sum(wins[:3]))/stake if stake else 0.0,'roi_no_top5':100*(total-sum(wins[:5]))/stake if stake else 0.0}
 Path('research_v289_3head_wave36r_robustness.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
