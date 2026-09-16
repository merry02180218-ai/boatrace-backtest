#!/usr/bin/env python3
"""Fixed gap24=.05/.06 monthly audit, Apr-Aug only. September never read."""
from pathlib import Path
import json, pandas as pd
import audit_4head_v283_adaptive_second_depth as a
OUT=Path('/tmp/head4_v283_fixed_gap005_006_monthly'); OUT.mkdir(parents=True,exist_ok=True)
THIRD=.10
GAPS=[.05,.06]
MONTHS=['2026-04','2026-05','2026-06','2026-07','2026-08']

def gap24(r):
 s=a.ranked(r); return float(r.p2[s[1]]-r.p2[s[3]])

def sparse(r,g,tgap=None):
 d=4 if gap24(r)<=g else 2
 return a.pairs_depth(r,d,tgap)

def main():
 df,_=a.prev.build()
 assert len(df)==164
 assert df.date.min()>='2026-04-01' and df.date.max()<='2026-08-31'
 modes={'base4':lambda r:a.pairs_depth(r,2,None),'third_margin':lambda r:a.pairs_depth(r,2,THIRD)}
 for g in GAPS:
  modes[f'gap24_{g:.2f}']=lambda r,g=g:sparse(r,g,None)
  modes[f'gap24_{g:.2f}_third']=lambda r,g=g:sparse(r,g,THIRD)
 rec=[]
 for n,f in modes.items():
  q=a.settle(df,f); q['mode']=n; q['gap24']=df.apply(gap24,axis=1).values
  q['fire']=(q.gap24<=float(n.split('_')[1]) if n.startswith('gap24_') else False)
  rec.append(q)
 rd=pd.concat(rec,ignore_index=True)
 base=rd[rd['mode'].eq('base4')][['race_code','month','tickets','hit']].rename(columns={'tickets':'base_tickets','hit':'base_hit'})
 sm=[]
 for m in MONTHS:
  for n in modes:
   q=rd[(rd.month.eq(m))&(rd['mode'].eq(n))].copy(); met=a.metric(q)
   z=q.merge(base,on=['race_code','month'],how='left')
   sm.append({'month':m,'mode':n,**met,'fire_races':int(q['fire'].sum()) if n.startswith('gap24_') else 0,'added_tickets_vs_base':int((z.tickets-z.base_tickets).sum()),'added_hits_vs_base':int((z.hit-z.base_hit).sum())})
 summary=pd.DataFrame(sm)
 # transparent actual SECOND rank4 misses and whether each fixed threshold fires
 miss=df[(df.head4.eq(1))&(df.second_rank.eq(4))].copy(); miss['gap24']=miss.apply(gap24,axis=1)
 for g in GAPS: miss[f'fire_{g:.2f}']=miss.gap24<=g
 miss=miss[['date','month','race_code','actual_second','actual_third','second_rank','gap24','fire_0.05','fire_0.06']]
 rescue=[]
 for m in MONTHS:
  mm=miss[miss.month.eq(m)]
  rescue.append({'month':m,'rank4_misses':len(mm),'fire_0.05':int(mm['fire_0.05'].sum()),'fire_0.06':int(mm['fire_0.06'].sum())})
 pd.DataFrame(rescue).to_csv(OUT/'rank4_monthly_rescue.csv',index=False)
 summary.to_csv(OUT/'monthly_summary.csv',index=False); rd.to_csv(OUT/'race_detail.csv',index=False); miss.to_csv(OUT/'rank4_misses.csv',index=False)
 meta={'fixed_gap24':[.05,.06],'months':MONTHS,'third_gap':THIRD,'formal_prospective_roi':'NOT_COMPUTABLE','september':'UNREAD','production':'HEAD4_V291_COMP7 unchanged'}
 (OUT/'meta.json').write_text(json.dumps(meta,indent=2)+'\n')
 print('HEAD4_V283_FIXED_GAP005_006_MONTHLY_OK'); print('\nMONTHLY SUMMARY\n',summary.to_string(index=False)); print('\nRANK4 MISSES\n',miss.to_string(index=False)); print('SEPTEMBER_UNREAD'); print('PRODUCTION_UNCHANGED')
if __name__=='__main__': main()
