#!/usr/bin/env python3
"""4号艇 7-8月ROI低下の要因分解。4-8月だけ。9月禁止。"""
from pathlib import Path
import numpy as np, pandas as pd
import audit_4head_joint_grid_ablation as ab
import audit_4head_joint_headprob_opponentmass_lastminute as jg

OUT=Path('/tmp/head4_julaug_roi_attribution'); OUT.mkdir(parents=True,exist_ok=True)

def rebuild():
 scores=jg.base.headprob_scores(); df,_=jg.src.build(jg.START,jg.END); df['race_code']=df.race_code.astype(str).str.zfill(12)
 cx=jg.cand.rebuild(jg.START,jg.END)[['race_code','orig4_adv_inside']].copy(); cx['race_code']=cx.race_code.astype(str).str.zfill(12)
 df=df.merge(scores,on='race_code',validate='one_to_one').merge(cx,on='race_code',validate='one_to_one')
 cache={}; rr=[]
 for _,r in df.iterrows():
  pairs=jg.src.pairs(r,None,jg.live.THIRD_GAP); ts=[f'4-{s}-{t}' for s,t in pairs]
  actual=f"4-{int(r.actual_second)}-{int(r.actual_third)}" if r.head4 else ''; hit=bool(actual and actual in ts)
  oq=cache.setdefault(r.date,jg.oddsmod.odds_for_date(r.date)); oo=oq[oq.race_code.astype(str)==str(r.race_code)]
  ovs=[float(pd.to_numeric(oo.iloc[0].get(t),errors='raise')) for t in ts]; comp=jg.live.composite_odds(ovs)
  stakes={x['combo']:x['stake'] for x in jg.live.dutch(ts,ovs)}
  hit_odds=float(oo.iloc[0].get(actual,0)) if hit else np.nan
  hit_stake=float(stakes.get(actual,0)) if hit else 0
  payout=hit_stake*hit_odds if hit else 0
  rr.append({'race_code':r.race_code,'date':r.date,'month':r.month,'head4':int(r.head4),'raw_hit':int(hit),
             'composite_odds':comp,'current_bet':int(comp>=7),'hit_ticket':actual,'hit_ticket_odds':hit_odds,
             'hit_ticket_stake':hit_stake,'payout_if_bet':payout,'tickets':len(ts),'head_prob':float(r.head_prob),
             'opponent_mass':jg.pair_mass(r.p2,r.pc,pairs),'last_orig':float(r.orig4_adv_inside)})
 return pd.DataFrame(rr)

def summary(q,label):
 stake=10000*len(q); pay=float(q.payout_if_bet.sum())
 return {'period':label,'R':len(q),'head4':int(q.head4.sum()),'head4_rate':100*q.head4.mean(),'raw_hits':int(q.raw_hit.sum()),
         'raw_hit_rate':100*q.raw_hit.mean(),'stake':stake,'payout':pay,'ROI':100*pay/stake if stake else np.nan}

def main():
 if jg.END>='2026-09-01': raise RuntimeError('9月結果アクセス禁止')
 rd=rebuild()
 if len(rd)!=164 or int(rd.head4.sum())!=70 or int(rd.tickets.sum())!=817 or int(rd.raw_hit.sum())!=35: raise RuntimeError('再現失敗')
 rd.to_csv(OUT/'race_detail.csv',index=False)
 rows=[]
 for label,q in [('Apr-Jun',rd[rd.month<='2026-06']),('Jul-Aug',rd[rd.month>='2026-07'])]:
  rows += [summary(q,label+' ALL'),summary(q[q.current_bet.eq(1)],label+' comp>=7'),summary(q[q.current_bet.eq(0)],label+' comp<7')]
 pd.DataFrame(rows).to_csv(OUT/'funnel_roi.csv',index=False)
 bands=[0,4,5,5.5,6,6.25,6.5,6.75,7,8,10,15,999]
 rd['comp_band']=pd.cut(rd.composite_odds,bands,right=False)
 bd=rd.groupby(['month','comp_band'],observed=True).agg(R=('race_code','size'),head4=('head4','sum'),hits=('raw_hit','sum'),payout=('payout_if_bet','sum'),avg_comp=('composite_odds','mean')).reset_index()
 bd['ROI']=100*bd.payout/(bd.R*10000); bd.to_csv(OUT/'monthly_comp_bands.csv',index=False)
 win=rd[rd.raw_hit.eq(1)].copy()
 win['rejected_by_comp7']=win.composite_odds.lt(7)
 win.to_csv(OUT/'winning_races.csv',index=False)
 dist=[]
 for label,q in [('Apr-Jun',rd[rd.month<='2026-06']),('Jul-Aug',rd[rd.month>='2026-07'])]:
  for kind,z in [('hit',q[q.raw_hit.eq(1)]),('miss',q[q.raw_hit.eq(0)])]:
   dist.append({'period':label,'kind':kind,'R':len(z),'comp_mean':z.composite_odds.mean(),'comp_median':z.composite_odds.median(),
                'comp_q25':z.composite_odds.quantile(.25),'comp_q75':z.composite_odds.quantile(.75),
                'comp_ge7':int(z.composite_odds.ge(7).sum()),'avg_hit_ticket_odds':z.hit_ticket_odds.mean(),
                'avg_payout_if_bet':z.payout_if_bet.mean()})
 pd.DataFrame(dist).to_csv(OUT/'hit_miss_comp_distribution.csv',index=False)
 print('4号艇_7-8月ROI低下_要因分解_OK')
 print(pd.DataFrame(rows).to_string(index=False))
 print('\n的中/外れの合成オッズ分布')
 print(pd.DataFrame(dist).to_string(index=False))
 for label,q in [('Apr-Jun',win[win.month<='2026-06']),('Jul-Aug',win[win.month>='2026-07'])]:
  print(label,'買い目的中',len(q),'comp>=7採用',int(q.composite_odds.ge(7).sum()),'comp<7除外',int(q.composite_odds.lt(7).sum()),
        '的中comp中央値',round(q.composite_odds.median(),4),'的中券平均オッズ',round(q.hit_ticket_odds.mean(),2))
 print('9月_UNREAD'); print('本番変更なし')
if __name__=='__main__': main()
