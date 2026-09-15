#!/usr/bin/env python3
"""Independent audit of the 86R/40.70% HEAD4 research candidate."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import analyze_4head_headrate_3ren_player_st as base
import analyze_4head_exhibition_original_trainonly as ex
from analyze_v205_3head_operational_replay import load_odds, round_dutch
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
OUT=Path('/tmp/head4_86r_audit'); OUT.mkdir(parents=True,exist_ok=True)
WIN=-0.0299361318939513; REN2=-7.080000000000001; PLAYER=.215605; ST=-0.6000000000000001; ORIG=-0.057777777777777706
BANK=10000; BOATS=(1,2,3,5,6)
def ii(x,d=0):
 try:return int(float(x))
 except:return d
def rebuild():
 z=base.settle_all().merge(base.build_motor_features(),on=['date','month','race_code'],how='left').merge(base.build_prior_features(),on=['date','month','race_code'],how='left')
 z['race_code']=z.race_code.astype(str).str.zfill(12); z['head4']=pd.to_numeric(z.actual_head4,errors='coerce').fillna(0).astype(int)
 e=ex.build_ex(set(z.race_code)); x=z.merge(e,on='race_code',how='left')
 x=x[(x.motor_win_diff_4v3>=WIN)&(x.motor_2ren_diff_4v3>=REN2)&(x.player4_all_win>=PLAYER)&(x.basic_complete==1)&(x.st4_adv_inside>=ST)&(x.orig_avg_available==1)&(x.orig4_adv_inside>=ORIG)].copy()
 x['date']=x.date.astype(str); x['month']=x.date.str[:7]; x=x[(x.date>='2026-04-01')&(x.date<='2026-08-31')].copy()
 tr=x[x.month.isin(['2026-04','2026-05','2026-06'])]; ho=x[x.month.isin(['2026-07','2026-08'])]
 assert (len(tr),int(tr.head4.sum()))==(86,35),(len(tr),int(tr.head4.sum()))
 assert (len(ho),int(ho.head4.sum()))==(78,35),(len(ho),int(ho.head4.sum()))
 print('HEAD4_86R_INDEPENDENT_REPLAY_OK'); return x
def pair_orders(rs):
 out={}
 for mon in [f'2026-{m:02d}' for m in range(4,9)]:
  tr=c4.headrows_before(rs,mon)
  if len(tr)<40: continue
  mu,sd=c4.scalers(tr); w2=c4.fit(tr,'second',mu,sd); w3=c4.fit(tr,'third',mu,sd)
  for r in rs:
   if r.get('date','')[:7]!=mon: continue
   s2,s3=c4.role_scores(r,w2,w3,mu,sd); ps=[(a,b) for a in BOATS for b in BOATS if a!=b]; ps.sort(key=lambda p:s2[p[0]]+s3[p[1]],reverse=True); out[str(r.get('race_code','')).zfill(12)]=ps[:4]
 return out
def actual_map(rs): return {str(r.get('race_code','')).zfill(12):(ii(r.get('winner')),ii(r.get('second')),ii(r.get('third')),ii(r.get('valid_result'))) for r in rs}
def settle(tickets,odrow,actual):
 odds=[]
 for t in tickets:
  try:o=float(odrow[t])
  except:return None
  if not np.isfinite(o) or o<=1:return None
  odds.append(o)
 stakes=round_dutch(odds,BANK); combo=f'{actual[0]}-{actual[1]}-{actual[2]}'; ret=0.;hit=0
 if combo in tickets:
  j=tickets.index(combo)
  if stakes[j]>0: hit=1;ret=float(stakes[j])*odds[j]
 return hit,ret
def summarize_head(x):
 rows=[]
 for mon,g in x.groupby('month'): rows.append({'period':mon,'R':len(g),'head4':int(g.head4.sum()),'head4_rate_pct':100*g.head4.mean()})
 for name,mons in [('Apr-Jun',['2026-04','2026-05','2026-06']),('Jul-Aug',['2026-07','2026-08'])]:
  g=x[x.month.isin(mons)];rows.append({'period':name,'R':len(g),'head4':int(g.head4.sum()),'head4_rate_pct':100*g.head4.mean()})
 return pd.DataFrame(rows)
def main():
 x=rebuild(); hs=summarize_head(x); hs.to_csv(OUT/'head_monthly.csv',index=False)
 rs=c4.read(); orders=pair_orders(rs); am=actual_map(rs); od=load_odds(); oi=od.set_index('race_code',drop=False) if not od.empty else pd.DataFrame(); rr=[]
 for _,r in x.iterrows():
  code=r.race_code; rec={'date':r.date,'month':r.month,'race_code':code,'head4':int(r.head4),'roi_covered':0,'hit':np.nan,'payout':np.nan}; ps=orders.get(code); a=am.get(code)
  if ps and a and a[3]==1 and not oi.empty and code in oi.index:
   o=oi.loc[code]; o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o; st=settle([f'4-{s}-{t}' for s,t in ps],o,a)
   if st is not None: rec.update(roi_covered=1,hit=st[0],payout=st[1])
  rr.append(rec)
 rd=pd.DataFrame(rr);rd.to_csv(OUT/'roi_detail.csv',index=False); sm=[]
 periods=[(m,[m]) for m in sorted(x.month.unique())]+[('Apr-Jun',['2026-04','2026-05','2026-06']),('Jul-Aug',['2026-07','2026-08'])]
 for name,mons in periods:
  allg=rd[rd.month.isin(mons)]; g=allg[allg.roi_covered==1]; stake=len(g)*BANK;payout=float(g.payout.sum()) if len(g) else 0
  sm.append({'period':name,'head_population_R':len(allg),'roi_covered_R':len(g),'coverage_pct':100*len(g)/len(allg) if len(allg) else np.nan,'trifecta_hits':int(g.hit.sum()) if len(g) else 0,'trifecta_hit_rate_pct':100*g.hit.mean() if len(g) else np.nan,'stake_yen':stake,'payout_yen':payout,'profit_yen':payout-stake,'roi_pct':100*payout/stake if stake else np.nan})
 roi=pd.DataFrame(sm);roi.to_csv(OUT/'roi_summary.csv',index=False)
 meta={'candidate':'HEAD4_86R_ORIGAVG_RESEARCH','head_replay_assert':'86/35 Apr-Jun; 78/35 Jul-Aug','roi_note':'retrospective archived-odds audit; separate coverage; not prospective pre-deadline evidence','production_v283_contract':'TOP2XTOP2 alpha2=.60; production unchanged','september':'UNREAD'}; (OUT/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
 print('\nHEAD MONTHLY\n',hs.to_string(index=False));print('\nROI SUMMARY\n',roi.to_string(index=False));print('SEPTEMBER_UNREAD');print('PRODUCTION_UNCHANGED')
if __name__=='__main__':main()
