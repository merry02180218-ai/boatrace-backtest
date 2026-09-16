#!/usr/bin/env python3
"""Validate SECOND Top3 rescue without July/Aug threshold tuning. September never read."""
from pathlib import Path
import json, numpy as np, pandas as pd
import audit_4head_86r_independent as cand
import audit_4head_86r_v283_closing_odds as audit
from head4_v291_downstream_inference import load_artifact, score_second, score_conditional_third, v283_top4, BOATS
OUT=Path('/tmp/head4_v283_second_margin'); OUT.mkdir(parents=True,exist_ok=True)
GAPS=[.01,.02,.03,.04,.05,.075,.10,.15,.20]; THIRD_GAP=.10; STAKE=100

def build():
 cx=cand.rebuild(); cx=cx[(cx.date>='2026-04-01')&(cx.date<='2026-08-31')].copy(); assert len(cx)==164
 codes=set(cx.race_code.astype(str).str.zfill(12)); d=audit.source_rows(codes); long=audit.build_long_all(d); art=load_artifact(); sf=list(art['v283_SECOND']['features']); cf=list(art['v283_COND_THIRD']['features'])
 truth={str(r.race_code).zfill(12):(int(float(r.winner)),int(float(r.second)),int(float(r.third))) for _,r in d.iterrows() if str(r.get('valid_result','0')) in ('1','1.0')}; rows=[]
 for code,g in long.groupby('race_code'):
  sr=[]
  for _,r in g.iterrows(): x={'boat':int(r.boat)}; x.update({f:r[f] for f in sf}); sr.append(x)
  p2=score_second(sr,art); pc=score_conditional_third(audit.conditional_rows(g,sf,cf),art); so=sorted(BOATS,key=lambda s:(-float(p2[s]),s)); actual=truth.get(str(code)); ar=so.index(actual[1])+1 if actual and actual[0]==4 else np.nan
  rows.append({'date':str(g.date.iloc[0]),'month':str(g.date.iloc[0])[:7],'race_code':str(code),'head4':int(actual is not None and actual[0]==4),'actual_second':actual[1] if actual and actual[0]==4 else np.nan,'actual_third':actual[2] if actual and actual[0]==4 else np.nan,'second_rank':ar,'second_order':'-'.join(map(str,so)),'second_gap23':float(p2[so[1]]-p2[so[2]]),'p2':p2,'pc':pc})
 return pd.DataFrame(rows),art

def pairs(row,sgap=None,tgap=None):
 p2=row.p2; pc=row.pc; so=sorted(BOATS,key=lambda s:(-float(p2[s]),s)); seconds=so[:3] if sgap is not None and float(p2[so[1]]-p2[so[2]])<=sgap else so[:2]; out=[]
 for s in seconds:
  ts=sorted((t for t in BOATS if t!=s),key=lambda t:(-float(pc[(s,t)]),t)); use=ts[:3] if tgap is not None and float(pc[(s,ts[1])]-pc[(s,ts[2])])<=tgap else ts[:2]; out += [(s,t) for t in use]
 base=v283_top4(p2,pc); return list(dict.fromkeys(base+[x for x in out if x not in base]))

def capture(df,sgap):
 q=df[df.head4.eq(1)]; return sum((int(r.actual_second),int(r.actual_third)) in pairs(r,sgap,None) for _,r in q.iterrows())

def main():
 df,art=build(); dev=df[df.month.isin(['2026-04','2026-05','2026-06'])]; scan=[]
 for g in GAPS:
  pp=dev.apply(lambda r:pairs(r,g,None),axis=1); scan.append({'gap':g,'dev_capture':capture(dev,g),'dev_added_tickets':int(sum(len(x)-4 for x in pp))})
 sc=pd.DataFrame(scan); basecap=capture(dev,None); sc['incremental_capture']=sc.dev_capture-basecap; sc['efficiency']=sc.incremental_capture/sc.dev_added_tickets.replace(0,np.nan)
 eligible=sc[sc.incremental_capture>0]; chosen=float((eligible.sort_values(['efficiency','incremental_capture','gap'],ascending=[False,False,True]).iloc[0] if len(eligible) else sc.iloc[0]).gap)
 odds_cache={}; rec=[]
 for _,r in df.iterrows():
  modes={'base':pairs(r,None,None),'second_margin':pairs(r,chosen,None),'third_margin':pairs(r,None,THIRD_GAP),'combined':pairs(r,chosen,THIRD_GAP)}; ds=r.date; oq=odds_cache.setdefault(ds,audit.odds_for_date(ds)); oo=oq[oq.race_code.astype(str)==str(r.race_code)] if len(oq) else oq; covered=len(oo)==1; hp=(int(r.actual_second),int(r.actual_third)) if r.head4 else None
  for mode,ps in modes.items():
   hit=covered and hp in ps; odd=pd.to_numeric(oo.iloc[0].get(f'4-{hp[0]}-{hp[1]}'),errors='coerce') if hit else np.nan; hit=bool(hit and pd.notna(odd)); pay=float(odd*STAKE) if hit else 0
   rec.append({'date':ds,'month':r.month,'race_code':r.race_code,'mode':mode,'head4':r.head4,'second_rank':r.second_rank,'second_gap23':r.second_gap23,'tickets':len(ps),'stake':len(ps)*STAKE if covered else 0,'hit':int(hit),'payout':pay,'profit':pay-(len(ps)*STAKE if covered else 0),'actual_pair':f"4-{int(r.actual_second)}-{int(r.actual_third)}" if r.head4 else ''})
 rd=pd.DataFrame(rec); out=[]
 periods={'Apr-Jun':['2026-04','2026-05','2026-06'],'Jul-Aug':['2026-07','2026-08'],'July':['2026-07'],'August':['2026-08'],'Apr-Aug':['2026-04','2026-05','2026-06','2026-07','2026-08']}
 for pn,mons in periods.items():
  for mode in ['base','second_margin','third_margin','combined']:
   q=rd[(rd.month.isin(mons))&(rd['mode'].eq(mode))]; st=q.stake.sum(); pay=q.payout.sum(); out.append({'period':pn,'mode':mode,'R':len(q),'tickets':q.tickets.sum(),'hits':q.hit.sum(),'stake':st,'payout':pay,'profit':pay-st,'roi_pct':100*pay/st if st else np.nan})
 summary=pd.DataFrame(out); misses=df[(df.head4.eq(1))&(df.second_rank>2)][['date','race_code','actual_second','actual_third','second_rank','second_order','second_gap23']]
 sc.to_csv(OUT/'dev_gap_scan.csv',index=False); misses.to_csv(OUT/'second_misses.csv',index=False); rd.to_csv(OUT/'race_mode_detail.csv',index=False); summary.to_csv(OUT/'summary.csv',index=False); (OUT/'meta.json').write_text(json.dumps({'chosen_second_gap':chosen,'third_gap':THIRD_GAP,'formal_prospective_roi':'NOT_COMPUTABLE','september':'UNREAD','production':'HEAD4_V291_COMP7 unchanged'},indent=2)+'\n')
 print('HEAD4_V283_SECOND_MARGIN_VALIDATION_OK'); print('CHOSEN_SECOND_GAP',chosen); print('\nDEV_SCAN\n',sc.to_string(index=False)); print('\nSECOND_MISSES\n',misses.to_string(index=False)); print('\nSUMMARY\n',summary.to_string(index=False)); print('SEPTEMBER_UNREAD'); print('PRODUCTION_UNCHANGED')
if __name__=='__main__': main()
