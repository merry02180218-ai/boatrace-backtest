#!/usr/bin/env python3
"""4号艇: 4-6月→7-8月の市場/構造シフトを結果前変数で分解。9月禁止。"""
from pathlib import Path
import numpy as np, pandas as pd
import audit_4head_julaug_roi_collapse_attribution as src

OUT=Path('/tmp/head4_market_regime_shift'); OUT.mkdir(parents=True,exist_ok=True)

def desc(q,label):
 return {'group':label,'R':len(q),'head_prob_mean':q.head_prob.mean(),'head_prob_med':q.head_prob.median(),
 'opp_mass_mean':q.opponent_mass.mean(),'opp_mass_med':q.opponent_mass.median(),
 'orig_adv_mean':q.last_orig.mean(),'orig_adv_med':q.last_orig.median(),
 'comp_mean':q.composite_odds.mean(),'comp_med':q.composite_odds.median(),
 'tickets_mean':q.tickets.mean(),'head4_rate':100*q.head4.mean(),'hit_rate':100*q.raw_hit.mean(),
 'ROI':100*q.payout_if_bet.sum()/(10000*len(q)) if len(q) else np.nan}

def main():
 rd=src.rebuild()
 if len(rd)!=164 or int(rd.head4.sum())!=70 or int(rd.raw_hit.sum())!=35: raise RuntimeError('再現失敗')
 rd['period']=np.where(rd.month.le('2026-06'),'Apr-Jun','Jul-Aug')
 rows=[]
 for per in ['Apr-Jun','Jul-Aug']:
  q=rd[rd.period.eq(per)]
  rows += [desc(q,per+' ALL'),desc(q[q.composite_odds.lt(7)],per+' comp<7'),desc(q[q.composite_odds.ge(7)],per+' comp>=7')]
 for mo in sorted(rd.month.unique()):
  q=rd[rd.month.eq(mo)]
  rows += [desc(q,mo+' ALL'),desc(q[q.composite_odds.lt(7)],mo+' comp<7'),desc(q[q.composite_odds.ge(7)],mo+' comp>=7')]
 sm=pd.DataFrame(rows); sm.to_csv(OUT/'structure_summary.csv',index=False)
 # Fine comp bands and monotonic cumulative upper/lower selections.
 edges=[0,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,9,10,12,15,20,999]
 rd['band']=pd.cut(rd.composite_odds,edges,right=False)
 band=rd.groupby(['period','band'],observed=True).agg(R=('raw_hit','size'),head4=('head4','sum'),hits=('raw_hit','sum'),
  payout=('payout_if_bet','sum'),head_prob=('head_prob','mean'),opp_mass=('opponent_mass','mean'),orig_adv=('last_orig','mean')).reset_index()
 band['head4_rate']=100*band.head4/band.R; band['hit_rate']=100*band.hits/band.R; band['ROI']=100*band.payout/(band.R*10000)
 band.to_csv(OUT/'fine_comp_bands.csv',index=False)
 sweeps=[]
 cuts=np.arange(3.0,10.01,.25)
 for per,q in [('Apr-Jun',rd[rd.period.eq('Apr-Jun')]),('Jul',rd[rd.month.eq('2026-07')]),('Aug',rd[rd.month.eq('2026-08')]),('Jul-Aug',rd[rd.period.eq('Jul-Aug')])]:
  for cut in cuts:
   for direction,m in [('LOW',q.composite_odds.lt(cut)),('HIGH',q.composite_odds.ge(cut))]:
    z=q[m]; st=10000*len(z); pay=z.payout_if_bet.sum()
    sweeps.append({'period':per,'direction':direction,'cut':cut,'R':len(z),'head4':int(z.head4.sum()),'hits':int(z.raw_hit.sum()),
      'ROI':100*pay/st if st else np.nan,'head_prob_mean':z.head_prob.mean(),'opp_mass_mean':z.opponent_mass.mean(),'orig_adv_mean':z.last_orig.mean()})
 pd.DataFrame(sweeps).to_csv(OUT/'monotonic_comp_sweep.csv',index=False)
 # Correlations among pre-result observables; no rule selection.
 corr=rd[['head_prob','opponent_mass','last_orig','composite_odds','tickets']].corr()
 corr.to_csv(OUT/'observable_correlations.csv')
 rd.to_csv(OUT/'race_detail.csv',index=False)
 print('4号艇_市場構造シフト分解_OK')
 print(sm[sm['group'].isin(['Apr-Jun comp<7','Apr-Jun comp>=7','Jul-Aug comp<7','Jul-Aug comp>=7','2026-07 comp<7','2026-07 comp>=7','2026-08 comp<7','2026-08 comp>=7'])].to_string(index=False))
 print('9月_UNREAD'); print('本番変更なし')
if __name__=='__main__': main()
