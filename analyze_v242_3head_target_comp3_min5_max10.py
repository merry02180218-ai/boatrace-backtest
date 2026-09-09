#!/usr/bin/env python3
"""v242: variable TopN targeting composite odds 3.0 with min5 / max10 rules.
Frozen restored-Waku10 3-head model; no tuning/model selection. Jul/Aug NON-PRISTINE.
Rule:
1) Evaluate TopN N=2..20 and find the N whose composite odds is closest to 3.00.
2) If that unconstrained chosen N is below Top5, skip the race (no bet).
3) If that unconstrained chosen N is above Top10, cap at Top10 even if Top10 composite odds remains >= 3.00.
4) Otherwise use the unconstrained chosen N (Top5..Top10).
5) Stake exactly 10,000 yen with canonical inverse-odds Dutch / 100-yen Hamilton rounding.
6) If frozen V221 pair-ranking inputs contain non-finite values, mark the race pair-rank-invalid and do not impute or bet.
"""
import numpy as np
import pandas as pd
import analyze_v234_3head_waku10_restored_replay as v234

BANK=10000
TARGET=3.0
MIN_N=5
MAX_N=10
OUT='analysis_v242_3head_target_comp3_min5_max10.csv'
SUM='summary_v242_3head_target_comp3_min5_max10.md'

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

def choose_unconstrained(ts,od):
 cand=[]
 for n in range(2,21):
  vals=odds_for(ts,od,n)
  if vals is None:continue
  c=comp(vals)
  cand.append((abs(c-TARGET),n,c))
 if not cand:return None
 cand.sort(key=lambda x:(x[0],x[1]))
 return cand[0][1],cand[0][2]

def choose_n(ts,od):
 raw=choose_unconstrained(ts,od)
 if raw is None:return {'action':'invalid'}
 raw_n,raw_c=raw
 if raw_n<MIN_N:
  return {'action':'skip','raw_n':raw_n,'raw_comp':raw_c,'reason':'below_top5'}
 n=min(raw_n,MAX_N)
 vals=odds_for(ts,od,n)
 if vals is None:return {'action':'invalid'}
 c=comp(vals)
 return {'action':'bet','raw_n':raw_n,'raw_comp':raw_c,'top_n':n,'comp_odds':c,'vals':vals,'capped_at_10':int(raw_n>MAX_N)}

def settle(ts,od,actual):
 ch=choose_n(ts,od)
 if ch.get('action')!='bet':return ch
 n=ch['top_n'];vals=ch['vals'];c=ch['comp_odds']
 stakes=np.asarray(v234.v205.round_dutch(vals,BANK),int)
 if stakes.sum()!=BANK:return {'action':'invalid'}
 hit=0;ret=0.
 if actual in ts[:n]:
  j=ts[:n].index(actual)
  if stakes[j]>0:
   hit=1;ret=float(stakes[j])*vals[j]
 ch.update({'hit':hit,'ret':ret,'profit':ret-BANK,'positive_tickets':int((stakes>0).sum())})
 return ch

def safe_order(r,pair):
 """Preserve frozen V221: reject non-finite inference rows instead of imputing them."""
 for s in v234.v222.OPP:
  for t in v234.v222.OPP:
   if s==t:continue
   try:vec=np.asarray(v234.v222.pairvec(r,s,t,'V221'),dtype=float)
   except Exception:return None
   if not np.isfinite(vec).all():return None
 try:return v234.v222.order(r,pair,'V221')
 except ValueError:return None

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
   code=str(r.get('race_code','')).zfill(12)
   z={'month':mon,'date':r._date.strftime('%Y-%m-%d'),'race_code':code,'p3':float(r._p),'y3':int(r._y),'pair_rank_invalid':0,'odds_available':0,'bet':0,'skip_below_top5':0,'invalid':0,'raw_top_n':np.nan,'raw_comp_odds':np.nan,'top_n':np.nan,'comp_odds':np.nan,'capped_at_10':0,'positive_tickets':np.nan,'trifecta_hit':0,'ret':np.nan,'profit':np.nan,'non_pristine':int(mon in ('2026-07','2026-08'))}
   ts=safe_order(r,pair)
   if ts is None:
    z['pair_rank_invalid']=1;rec.append(z);continue
   if code in oi.index:
    z['odds_available']=1
    od=oi.loc[code];od=od.iloc[-1] if isinstance(od,pd.DataFrame) else od
    s=settle(ts,od,actual)
    if s is not None:
     if s.get('raw_n') is not None:
      z['raw_top_n']=s['raw_n'];z['raw_comp_odds']=s['raw_comp']
     if s.get('action')=='skip':
      z['skip_below_top5']=1
     elif s.get('action')=='invalid':
      z['invalid']=1
     elif s.get('action')=='bet':
      z.update({'bet':1,'top_n':s['top_n'],'comp_odds':s['comp_odds'],'capped_at_10':s['capped_at_10'],'positive_tickets':s['positive_tickets'],'trifecta_hit':s['hit'],'ret':s['ret'],'profit':s['profit']})
   rec.append(z)
 q=pd.DataFrame(rec);q.to_csv(OUT,index=False)
 L=['# v242 variable TopN target composite odds 3.0: min Top5 / max Top10','', '- Frozen restored-Waku10 head selector + frozen V221 ordered-pair ranker; no tuning.', '- First find the unconstrained Top2..Top20 N closest to composite odds 3.00.', '- If unconstrained N < 5: NO BET.', '- If unconstrained N > 10: cap at Top10, even when Top10 composite odds is still >= 3.00.', '- Otherwise use Top5..Top10 as selected.', '- Exactly 10,000 yen per bet race with canonical inverse-odds Dutch / 100-yen Hamilton rounding.', '- Non-finite V221 inference rows are marked pair-rank-invalid and skipped; no imputation.', '- Jul/Aug are NON-PRISTINE descriptive only; Dec-Jun are research/contaminated.', f'- Waku10 validation: {common} races, 0 mismatches.','', '|period|R|bets|pair-invalid|skip<5|cap10|head hit|3-ren-tan hit/bet|avg TopN|avg comp odds|new ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for label,mask in [('Dec-Jun',q.month<='2026-06'),('Jul-Aug',q.month>='2026-07'),('All',q.month.notna())]:
  g=q[mask];s=g[g.bet==1];R=len(g);B=len(s);bad=int(g.pair_rank_invalid.sum());skip=int(g.skip_below_top5.sum());cap=int(s.capped_at_10.sum());H=int(s.trifecta_hit.sum());head=100*g.y3.mean() if R else np.nan;roi=100*s.ret.sum()/(B*BANK) if B else np.nan
  L.append(f'|{label}|{R}|{B}|{bad}|{skip}|{cap}|{head:.2f}%|{100*H/B if B else float("nan"):.2f}%|{s.top_n.mean():.2f}|{s.comp_odds.mean():.3f}|{roi:.2f}%|')
 L += ['', '## Monthly','|month|R|bets|pair-invalid|skip<5|cap10|3-ren-tan hit/bet|avg TopN|avg comp odds|new ROI|status|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
 for mon,g in q.groupby('month',sort=True):
  s=g[g.bet==1];R=len(g);B=len(s);bad=int(g.pair_rank_invalid.sum());skip=int(g.skip_below_top5.sum());cap=int(s.capped_at_10.sum());H=int(s.trifecta_hit.sum());roi=100*s.ret.sum()/(B*BANK) if B else np.nan;st='NON-PRISTINE' if mon in ('2026-07','2026-08') else 'research/contaminated'
  L.append(f'|{mon}|{R}|{B}|{bad}|{skip}|{cap}|{100*H/B if B else float("nan"):.2f}%|{s.top_n.mean():.2f}|{s.comp_odds.mean():.3f}|{roi:.2f}%|{st}|')
 L += ['', '## Bet TopN distribution','|TopN|count|share|','|---|---:|---:|']
 s=q[q.bet==1];dist=s.top_n.value_counts().sort_index()
 for n,cnt in dist.items():L.append(f'|Top{int(n)}|{int(cnt)}|{100*cnt/len(s):.2f}%|')
 with open(SUM,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
 print('\n'.join(L))
if __name__=='__main__':main()
