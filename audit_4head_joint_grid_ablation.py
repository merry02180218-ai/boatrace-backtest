#!/usr/bin/env python3
"""既存joint_gridを再計算し、各判定を外したアブレーションとnear-missを出す。9月禁止。"""
from pathlib import Path
import numpy as np, pandas as pd
import audit_4head_joint_headprob_opponentmass_lastminute as jg

OUT=Path('/tmp/head4_joint_ablation'); OUT.mkdir(parents=True,exist_ok=True)

def stats(q,m):
 b=q[m]; st=10000*len(b); py=float(b.payout_if_bet.sum())
 return len(b),int((b.current_bet.eq(0)&m).sum()),int(b.raw_hit.sum()),py,100*py/st if st else np.nan

def main():
 if jg.END>='2026-09-01': raise RuntimeError('9月結果アクセス禁止')
 # race_detail生成部を同じ意味で再構築するため、joint scriptの出力ロジックを最小限複製
 scores=jg.base.headprob_scores(); df,_=jg.src.build(jg.START,jg.END); df['race_code']=df.race_code.astype(str).str.zfill(12)
 cx=jg.cand.rebuild(jg.START,jg.END)[['race_code','orig4_adv_inside']].copy(); cx['race_code']=cx.race_code.astype(str).str.zfill(12)
 df=df.merge(scores,on='race_code',validate='one_to_one').merge(cx,on='race_code',validate='one_to_one')
 cache={}; rr=[]
 for _,r in df.iterrows():
  pairs=jg.src.pairs(r,None,jg.live.THIRD_GAP); ts=[f'4-{s}-{t}' for s,t in pairs]; mass=jg.pair_mass(r.p2,r.pc,pairs)
  actual=f"4-{int(r.actual_second)}-{int(r.actual_third)}" if r.head4 else ''; hit=bool(actual and actual in ts)
  oq=cache.setdefault(r.date,jg.oddsmod.odds_for_date(r.date)); oo=oq[oq.race_code.astype(str)==str(r.race_code)]
  ovs=[float(pd.to_numeric(oo.iloc[0].get(t),errors='raise')) for t in ts]; comp=jg.live.composite_odds(ovs)
  stakes={x['combo']:x['stake'] for x in jg.live.dutch(ts,ovs)}
  pay=float(stakes.get(actual,0))*float(oo.iloc[0].get(actual,0)) if hit else 0.0
  rr.append({'month':r.month,'head_prob':float(r.head_prob),'opponent_mass':mass,'last_orig':float(r.orig4_adv_inside),
             'raw_hit':int(hit),'composite_odds':comp,'current_bet':int(comp>=7),'payout_if_bet':pay})
 rd=pd.DataFrame(rr)
 rows=[]
 configs=[('HEAD',True,False,False),('MASS',False,True,False),('LAST',False,False,True),
          ('HEAD+MASS',True,True,False),('HEAD+LAST',True,False,True),('MASS+LAST',False,True,True),('ALL',True,True,True)]
 for period,q in [('4-6',rd[rd.month<='2026-06']),('7-8',rd[rd.month>='2026-07'])]:
  for name,uh,um,ul in configs:
   for hc in (jg.HEAD_CUTS if uh else [None]):
    for mc in (jg.MASS_CUTS if um else [None]):
     for lc in (jg.LAST_CUTS if ul else [None]):
      for lo in jg.COMP_LOWER:
       rescue=q.current_bet.eq(0)
       if uh: rescue &= q.head_prob.ge(hc)
       if um: rescue &= q.opponent_mass.ge(mc)
       if ul: rescue &= q.last_orig.ge(lc)
       if lo>0: rescue &= q.composite_odds.ge(lo)
       m=q.current_bet.eq(1)|rescue; n,add,hits,pay,roi=stats(q,m)
       rows.append({'period':period,'config':name,'head':hc,'mass':mc,'last':lc,'comp_lower':lo,'betR':n,'addedR':add,'hits':hits,'payout':pay,'roi':roi})
 out=pd.DataFrame(rows); out.to_csv(OUT/'ablation_all.csv',index=False)
 keys=['config','head','mass','last','comp_lower']
 # NaN keys are awkward to join, replace with sentinel text for paired comparison.
 z=out.copy()
 for k in ['head','mass','last']: z[k]=z[k].fillna('OFF').astype(str)
 dev=z[z.period=='4-6'].set_index(keys); val=z[z.period=='7-8'].set_index(keys)
 p=dev[['betR','addedR','hits','roi']].add_prefix('dev_').join(val[['betR','addedR','hits','roi']].add_prefix('val_')).reset_index()
 p=p[p.val_addedR>=1].copy(); p['min_roi']=np.minimum(p.dev_roi,p.val_roi)
 p=p.sort_values(['min_roi','val_roi','val_addedR'],ascending=[False,False,False])
 p.head(200).to_csv(OUT/'near_miss_top200.csv',index=False)
 best=[]
 for cfg,g in p.groupby('config'):
  x=g.iloc[0].to_dict(); best.append(x)
 pd.DataFrame(best).sort_values('min_roi',ascending=False).to_csv(OUT/'best_by_ablation.csv',index=False)
 print('4号艇_判定別アブレーション_OK')
 print(pd.DataFrame(best).sort_values('min_roi',ascending=False).to_string(index=False))
 print('9月_UNREAD'); print('本番変更なし')
if __name__=='__main__': main()
