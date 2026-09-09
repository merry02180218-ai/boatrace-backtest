#!/usr/bin/env python3
"""v240: frozen restored-Waku10 3-head TopN Dutch comparison.
TopN = 2,5,7,10,15. No tuning/model selection. Jul/Aug NON-PRISTINE.
Each settled race stakes exactly 10,000 yen across the selected TopN using canonical v205.round_dutch.
"""
import numpy as np
import pandas as pd
import analyze_v234_3head_waku10_restored_replay as v234

TOPS=[2,5,7,10,15]
BANK=10000
OUT='analysis_v240_3head_topn_dutch_compare.csv'
SUM='summary_v240_3head_topn_dutch_compare.md'

def settle_n(ts,od,actual,n):
 vals=[]
 for q in ts[:n]:
  try: v=float(od[q])
  except Exception:return None
  if not np.isfinite(v) or v<=0:return None
  vals.append(v)
 if not vals:return None
 stakes=np.asarray(v234.v205.round_dutch(vals,BANK),int)
 if stakes.sum()!=BANK:return None
 ret=0.; hit=0
 if actual in ts[:n]:
  j=ts[:n].index(actual)
  if stakes[j]>0:
   hit=1; ret=float(stakes[j])*vals[j]
 comp=1.0/sum(1.0/v for v in vals)
 return hit,ret,ret-BANK,comp,int((stakes>0).sum())

def main():
 cov=v234.reconstruct(); common=v234.validate_parser()
 if (cov.source=='missing').any():raise RuntimeError('missing Waku10; no imputation')
 d,dc,vc,basefs=v234.build_restored(); fs=v234.full_features(d,basefs);fs=[x for x in fs if x in d.columns]
 odds=v234.v205.load_odds(); oi=odds.set_index('race_code',drop=False)
 rows=[]
 for mon in v234.MONTHS:
  first=pd.Timestamp(mon+'-01'); nextm=first+pd.offsets.MonthBegin(1); tr=d[d._date<first]
  pair=v234.v222.fit_pair(tr,'V221')
  base_te,_=v234.v223.fit_head(d,list(basefs),vc,first,nextm); k=max(1,int((base_te._p>=.30).sum()))
  te,_=v234.v223.fit_head(d,fs,vc,first,nextm); sel=te.nlargest(k,'_p').copy()
  races=[]
  for _,r in sel.iterrows():
   if v234.v223.ii(r.get('valid_result'))!=1 or v234.v223.ii(r.get('course3'),3)!=3:continue
   act=v234.v222.v166.combo(r.get('actual_combo')); actual='-'.join(map(str,act)) if len(act)==3 else ''
   if not actual:continue
   code=str(r.get('race_code','')).zfill(12); ts=v234.v222.order(r,pair,'V221')
   races.append((code,actual,int(r._y),ts))
  for n in TOPS:
   settled=hits=0; ret=0.; comps=[]; bought=[]
   for code,actual,y3,ts in races:
    if code not in oi.index:continue
    od=oi.loc[code]; od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
    s=settle_n(ts,od,actual,n)
    if s is None:continue
    settled+=1; hits+=s[0]; ret+=s[1]; comps.append(s[3]); bought.append(s[4])
   rows.append({'month':mon,'top_n':n,'R':len(races),'settled_R':settled,'head_hit_pct':100*np.mean([x[2] for x in races]) if races else np.nan,'trifecta_hits':hits,'trifecta_hit_pct':100*hits/len(races) if races else np.nan,'avg_composite_odds':np.mean(comps) if comps else np.nan,'avg_positive_stake_tickets':np.mean(bought) if bought else np.nan,'new_roi_pct':100*ret/(settled*BANK) if settled else np.nan,'non_pristine':int(mon in ('2026-07','2026-08'))})
 q=pd.DataFrame(rows);q.to_csv(OUT,index=False)
 L=['# v240 TopN Dutch comparison','', '- Frozen restored-Waku10 head selector and frozen V221 ordered-pair ranker; no tuning.', '- TopN: 2 / 5 / 7 / 10 / 15.', '- Exactly 10,000 yen per settled race; inverse-odds Dutch with canonical 100-yen Hamilton rounding.', '- Trifecta hit requires the actual ticket to be within TopN and receive positive stake.', '- Jul/Aug are NON-PRISTINE descriptive only; Dec-Jun are research/contaminated.', f'- Waku10 validation: {common} races, 0 mismatches.','', '|month|TopN|R|settled|head hit|3-ren-tan hit|avg comp odds|avg bought pts|new ROI|status|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
 for _,r in q.iterrows():
  st='NON-PRISTINE' if r.non_pristine else 'research/contaminated'
  L.append(f"|{r.month}|Top{int(r.top_n)}|{int(r.R)}|{int(r.settled_R)}|{r.head_hit_pct:.2f}%|{r.trifecta_hit_pct:.2f}%|{r.avg_composite_odds:.3f}|{r.avg_positive_stake_tickets:.2f}|{r.new_roi_pct:.2f}%|{st}|")
 L += ['', '## Weighted aggregates']
 for label,months in [('Dec-Jun',q.month<='2026-06'),('Jul-Aug',q.month>='2026-07'),('All',q.month.notna())]:
  L += ['',f'### {label}','|TopN|R|settled|3-ren-tan hits|3-ren-tan hit|new ROI|','|---|---:|---:|---:|---:|---:|']
  for n in TOPS:
   g=q[months & (q.top_n==n)]; R=int(g.R.sum()); S=int(g.settled_R.sum()); H=int(g.trifecta_hits.sum())
   # Recover total return from each row's settled denominator and ROI.
   total_ret=float(((g.new_roi_pct/100)*g.settled_R*BANK).sum())
   L.append(f'|Top{n}|{R}|{S}|{H}|{100*H/R if R else float("nan"):.2f}%|{100*total_ret/(S*BANK) if S else float("nan"):.2f}%|')
 with open(SUM,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
 print('\n'.join(L))
if __name__=='__main__':main()
