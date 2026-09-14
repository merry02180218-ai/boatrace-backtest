from pathlib import Path
import json
import numpy as np,pandas as pd
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36_lda_stable_gate as w36

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('research_v289_3head_wave45_adaptive_topk.json')
CUT=.365448
QS=[.20,.30,.40,.50,.60,.70,.80]
BASE={'races':94,'hits':52,'stake_yen':940000,'payout_yen':1622070}

def ranked(score,k):
 idx=np.argsort(-np.nan_to_num(score,nan=-1))[:k]
 return [base.COMBOS[j] for j in idx]
def top5mass(score):
 s=np.nan_to_num(score,nan=0.0); idx=np.argsort(-s)[:5]; return float(s[idx].sum())
def decorate(q,scores):
 x=q.copy(); x['top5']=[';'.join(ranked(r,5)) for r in scores]; x['top8']=[';'.join(ranked(r,8)) for r in scores]; x['top5_mass']=[top5mass(r) for r in scores]; return x
def hitstats(q,tickets_col):
 hh=int(q.actual3.sum()); hits=int(sum(a in str(t).split(';') for a,t in zip(q.actual,q[tickets_col])))
 return {'races':len(q),'head_hits':hh,'ticket_hits':hits,'conversion':hits/hh if hh else 0.}
def apply_adaptive(q,thr):
 x=q.copy(); x['tickets']=[t8 if float(m)<=thr else t5 for m,t5,t8 in zip(x.top5_mass,x.top5,x.top8)]; x['ticket_count']=x.tickets.str.split(';').map(len); return x
def money(q):
 x=q.copy(); x['variant_return']=[base.dutch_return(r,str(r.tickets).split(';')) for _,r in x.iterrows()]; m=base.block(x); mm={mo:base.block(g) for mo,g in x.groupby('month')}; m.update({'monthly':mm,'min_month_roi_pct':min((z['roi_pct'] for z in mm.values()),default=None),'red_months':sum(z['roi_pct']<100 for z in mm.values()),'max_drawdown_yen':base.maxdd(x.sort_values(['date','race_code'])),'avg_ticket_count':float(x.ticket_count.mean()) if len(x) else 0.}); return m

def main():
 d=pd.read_csv(SRC,dtype=str).fillna('')
 if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
 ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str));
 if len(ex)!=94: raise RuntimeError('exact v288 94 required')
 d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]; d['actual']=d.settle__actual_combo.astype(str); d['actual3']=d.actual.str.startswith('3-').astype(int)
 X=base.build_static(d)
 if X.shape[1]!=63: raise RuntimeError('feature guard')
 y=d.actual
 def predict(train_mask,test_mask):
  ti=np.flatnonzero(train_mask.to_numpy()); ei=np.flatnonzero(test_mask.to_numpy()); p,s=w36.fit_predict(X.iloc[ti],y.iloc[ti],X.iloc[ei]); q=d.iloc[ei].copy(); q['p3']=p; q=decorate(q,s); return q
 mar=predict(d.month=='2026-02',d.month=='2026-03'); sel=mar[mar.p3>=CUT].sort_values(['date','race_code']).reset_index(drop=True)
 old=sel.copy(); old['tickets']=old.top5; old['ticket_count']=5; old_full=hitstats(old,'tickets'); mid=len(sel)//2; old_e=hitstats(old.iloc[:mid],'tickets'); old_l=hitstats(old.iloc[mid:],'tickets')
 cands=[]
 for qv in QS:
  thr=float(sel.top5_mass.quantile(qv)); z=apply_adaptive(sel,thr); e=z.iloc[:mid]; l=z.iloc[mid:]; fs=hitstats(z,'tickets'); es=hitstats(e,'tickets'); ls=hitstats(l,'tickets'); avg=float(z.ticket_count.mean())
  cands.append({'q':qv,'mass_threshold':thr,'full':fs,'early':es,'late':ls,'net':fs['ticket_hits']-old_full['ticket_hits'],'avg_ticket_count':avg})
 eligible=[c for c in cands if c['net']>=1 and c['early']['ticket_hits']>=old_e['ticket_hits'] and c['late']['ticket_hits']>=old_l['ticket_hits'] and c['avg_ticket_count']<=6.5]
 out={'wave':'45-adaptive-topk','feature_count':63,'cut':CUT,'march_old':old_full,'march_old_early':old_e,'march_old_late':old_l,'march_candidates':cands,'v288_overlap':0,'september_forbidden':True}
 if not eligible:
  out['march_gate_pass']=False; out['decision']='NO_ADOPTION_MARCH_GATE'; OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2)); return
 chosen=max(eligible,key=lambda c:(c['full']['ticket_hits'],-c['avg_ticket_count'],-c['q'])); out['chosen']=chosen; out['march_gate_pass']=True
 frames=[]
 for mo in ['2026-04','2026-05','2026-06']:
  q=predict(d.month<mo,d.month==mo); frames.append(q[q.p3>=CUT])
 frozen=d.month<='2026-06'
 for mo in ['2026-07','2026-08']:
  q=predict(frozen,d.month==mo); frames.append(q[q.p3>=CUT])
 ev=pd.concat(frames,ignore_index=True); ev=apply_adaptive(ev,chosen['mass_threshold']); pristine=ev[ev.month.isin(['2026-04','2026-05','2026-06'])].copy(); shadow=ev[ev.month.isin(['2026-07','2026-08'])].copy()
 pm=money(pristine); sm=money(shadow); oldp=pristine.copy(); oldp['tickets']=oldp.top5; oldp['ticket_count']=5; om=money(oldp)
 ov=int(ev.race_code.astype(str).isin(ex).sum());
 if ov: raise RuntimeError(f'v288 overlap {ov}')
 cmb={'races':94+pm['races'],'hits':52+pm['hits'],'stake_yen':940000+pm['stake_yen'],'payout_yen':1622070+pm['payout_yen']}; cmb['profit_yen']=cmb['payout_yen']-cmb['stake_yen']; cmb['roi_pct']=100*cmb['payout_yen']/cmb['stake_yen']
 out.update({'apr_jun_old_top5':om,'apr_jun_adaptive':pm,'jul_aug_nonpristine':sm,'combined_baseline_plus_addon':cmb,'v288_overlap':ov,'decision':'RESEARCH_CANDIDATE' if pm['roi_pct']>om['roi_pct'] and pm['red_months']<=1 else 'NO_ADOPTION'})
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
