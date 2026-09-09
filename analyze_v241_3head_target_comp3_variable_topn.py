#!/usr/bin/env python3
"""v241: variable TopN targeting composite odds 3.0.
Frozen restored-Waku10 3-head model; no tuning/model selection. Jul/Aug NON-PRISTINE.
For each selected race, evaluate TopN N=2..20 and choose the N whose composite odds is closest to 3.00.
Then stake exactly 10,000 yen across that chosen TopN using canonical v205.round_dutch.
"""
# Trigger note: workflow activation commit only; analysis logic unchanged.
import numpy as np
import pandas as pd
import analyze_v234_3head_waku10_restored_replay as v234

BANK=10000
TARGET=3.0
OUT='analysis_v241_3head_target_comp3_variable_topn.csv'
SUM='summary_v241_3head_target_comp3_variable_topn.md'

def odds_for(ts,od,n):
 vals=[]
 for q in ts[:n]:
  try:v=float(od[q])
  except Exception:return None
  if not np.isfinite(v) or v<=0:return None
  vals.append(v)
 return vals

def comp(vals):
 return 1.0/sum(1.0/v for v in vals)

def choose_n(ts,od):
 cand=[]
 for n in range(2,21):
  vals=odds_for(ts,od,n)
  if vals is None:continue
  c=comp(vals)
  cand.append((abs(c-TARGET),n,c,vals))
 if not cand:return None
 cand.sort(key=lambda x:(x[0],x[1]))
 return cand[0][1],cand[0][2],cand[0][3]

def settle(ts,od,actual):
 ch=choose_n(ts,od)
 if ch is None:return None
 n,c,vals=ch
 stakes=np.asarray(v234.v205.round_dutch(vals,BANK),int)
 if stakes.sum()!=BANK:return None
 hit=0;ret=0.
 if actual in ts[:n]:
  j=ts[:n].index(actual)
  if stakes[j]>0:
   hit=1;ret=float(stakes[j])*vals[j]
 return {'top_n':n,'comp_odds':c,'hit':hit,'ret':ret,'profit':ret-BANK,'positive_tickets':int((stakes>0).sum())}

def main():
 cov=v234.reconstruct();common=v234.validate_parser()
 if (cov.source=='missing').any():raise RuntimeError('missing Waku10; no imputation')
 d,dc,vc,basefs=v234.build_restored();fs=v234.full_features(d,basefs);fs=[x for x in fs if x in d.columns]
 odds=v234.v205.load_odds();oi=odds.set_index('race_code',drop=False)
 rec=[]
 for mon in v234.MONTHS:
  first=pd.Timestamp(mon+'-01');nextm=first+pd.offsets.MonthBegin(1);tr=d[d._date<first]
  pair=v234.v222.fit_pair(tr,'V221')
  base_te,_=v234.v223.fit_head(d,list(basefs),vc,first,nextm);k=max(1,int((base_te._p>=.30).sum()))
  te,_=v234.v223.fit_head(d,fs,vc,first,nextm);sel=te.nlargest(k,'_p').copy()
  for _,r in sel.iterrows():
   if v234.v223.ii(r.get('valid_result'))!=1 or v234.v223.ii(r.get('course3'),3)!=3:continue
   act=v234.v222.v166.combo(r.get('actual_combo'));actual='-'.join(map(str,act)) if len(act)==3 else ''
   if not actual:continue
   code=str(r.get('race_code','')).zfill(12);ts=v234.v222.order(r,pair,'V221')
   z={'month':mon,'date':r._date.strftime('%Y-%m-%d'),'race_code':code,'p3':float(r._p),'y3':int(r._y),'settled':0,'top_n':np.nan,'comp_odds':np.nan,'positive_tickets':np.nan,'trifecta_hit':0,'ret':np.nan,'profit':np.nan,'non_pristine':int(mon in ('2026-07','2026-08'))}
   if code in oi.index:
    od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
    s=settle(ts,od,actual)
    if s is not None:
     z.update({'settled':1,'top_n':s['top_n'],'comp_odds':s['comp_odds'],'positive_tickets':s['positive_tickets'],'trifecta_hit':s['hit'],'ret':s['ret'],'profit':s['profit']})
   rec.append(z)
 q=pd.DataFrame(rec);q.to_csv(OUT,index=False)
 L=['# v241 variable TopN target composite odds 3.0','', '- Frozen restored-Waku10 head selector + frozen V221 ordered-pair ranker; no tuning.', '- For each race, evaluate Top2..Top20 and choose the TopN whose composite odds is closest to 3.00.', '- Tie-break: fewer tickets.', '- Exactly 10,000 yen per settled race with canonical inverse-odds Dutch / 100-yen Hamilton rounding.', '- Jul/Aug are NON-PRISTINE descriptive only; Dec-Jun are research/contaminated.', f'- Waku10 validation: {common} races, 0 mismatches.','', '|period|R|settled|head hit|3-ren-tan hit|avg TopN|median TopN|avg comp odds|new ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
 for label,mask in [('Dec-Jun',q.month<='2026-06'),('Jul-Aug',q.month>='2026-07'),('All',q.month.notna())]:
  g=q[mask];s=g[g.settled==1];R=len(g);S=len(s);H=int(g.trifecta_hit.sum());head=100*g.y3.mean() if R else np.nan;roi=100*s.ret.sum()/(S*BANK) if S else np.nan
  L.append(f'|{label}|{R}|{S}|{head:.2f}%|{100*H/R if R else float("nan"):.2f}%|{s.top_n.mean():.2f}|{s.top_n.median():.1f}|{s.comp_odds.mean():.3f}|{roi:.2f}%|')
 L += ['', '## Monthly','|month|R|settled|3-ren-tan hit|avg TopN|avg comp odds|new ROI|status|','|---|---:|---:|---:|---:|---:|---:|---|']
 for mon,g in q.groupby('month',sort=True):
  s=g[g.settled==1];R=len(g);S=len(s);H=int(g.trifecta_hit.sum());roi=100*s.ret.sum()/(S*BANK) if S else np.nan;st='NON-PRISTINE' if mon in ('2026-07','2026-08') else 'research/contaminated'
  L.append(f'|{mon}|{R}|{S}|{100*H/R if R else float("nan"):.2f}%|{s.top_n.mean():.2f}|{s.comp_odds.mean():.3f}|{roi:.2f}%|{st}|')
 L += ['', '## Chosen TopN distribution','|TopN|count|share|','|---|---:|---:|']
 s=q[q.settled==1]
 vc=s.top_n.value_counts().sort_index()
 for n,cnt in vc.items():L.append(f'|Top{int(n)}|{int(cnt)}|{100*cnt/len(s):.2f}%|')
 with open(SUM,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
 print('\n'.join(L))
if __name__=='__main__':main()
