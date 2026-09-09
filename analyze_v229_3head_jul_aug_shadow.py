#!/usr/bin/env python3
"""v229: apply the already-discovered Top10 composite-odds rules to Jul/Aug 2026.
IMPORTANT: Jul/Aug are NON-PRISTINE / previously contaminated and are used only as descriptive shadow/sanity evidence.
No tuning or adoption decision may be based on this run.
"""
from pathlib import Path
from datetime import date
import numpy as np,pandas as pd
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v205_3head_operational_replay as v205
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v224_3head_national_form_decompose as v224
ROOT=Path(__file__).resolve().parent; SRC=ROOT/'analysis_v108_1head_feasibility.csv'; OUT=ROOT/'analysis_v229_3head_jul_aug_shadow.csv'; SUM=ROOT/'summary_v229_3head_jul_aug_shadow.md'; BANK=10000
MONTHS=['2026-07','2026-08']; ENDTS=pd.Timestamp('2026-09-01')
def uniq(x):return list(dict.fromkeys([c for c in x if c]))
def maxdd(a):
 c=np.cumsum(np.asarray(a,float));pk=np.maximum.accumulate(np.r_[0.,c]);return float((pk[1:]-c).max()) if len(c) else 0.
def safe_order(r,pair):
 """Return V221 order or None when serving pair features are missing.
 Missing feature races are skipped rather than imputed, preserving model semantics.
 """
 try:
  ts=v222.order(r,pair,'V221')
  return ts if len(ts)>=10 else None
 except ValueError as e:
  s=str(e)
  if 'NaN' in s or 'missing values' in s:return None
  raise
def main():
 # Extend existing pre-race builders ONLY so they can materialize Jul/Aug rows. This does not make Jul/Aug pristine.
 v223.CONTAM=ENDTS;v223.END=date(2026,8,31);v224.CONTAM=ENDTS
 raw=pd.read_csv(SRC,dtype={'race_code':str});dc=v165.pc(raw,['date','race_date','ymd']);vc=v165.pc(raw,['venue','jcd','stadium','place']);y,_=v165.target(raw);base=v165.feats(raw);raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce');raw['_y']=y;raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<ENDTS)].copy()
 d=v221.build(raw,dc);d=v222.build_current(d,dc);d=v223.build_unused(d,dc);d=v224.add_decomp(d,dc)
 hist=v222.cols(d,'b3_vh_');rel=[c for c in d if c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))];cur=[c for c in v222.cols(d,'c_b3_') if not c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]+[c for c in d if c.startswith(('c_wall','c_attack3','c_outer','c_ex_spread','c_st_spread','c_turn_spread','c_straight_spread'))];form=[c for c in d if c.startswith(('f_b3_m1_','f_b3_m12_','f_b3_m35_','f_b3_trend_','f_rel_'))]+[c for c in ['f_b3_layoff','f_b3_grade','f_b3_m1_grade'] if c in d];fs=uniq(list(base)+hist+cur+rel+form)
 odds=v205.load_odds();oi=odds.set_index('race_code',drop=False);race=[];skip=[]
 for mon in MONTHS:
  first=pd.Timestamp(mon+'-01');nxt=first+pd.offsets.MonthBegin(1);pair=v222.fit_pair(d[d._date<first],'V221');bte,_=v223.fit_head(d,list(base),vc,first,nxt);k=max(1,int((bte._p>=.30).sum()));te,_=v223.fit_head(d,fs,vc,first,nxt);sel=te.nlargest(k,'_p')
  # Prior-only conditional Top10 coverage; includes earlier historical months, and for Aug also prior Jul because this is shadow replay.
  vals=[];prior_missing=0
  for _,r in d[(d._date<first)&(d._y==1)].iterrows():
   ts=safe_order(r,pair)
   if ts is None:prior_missing+=1;continue
   act=v222.v166.combo(r.get('actual_combo'));a='-'.join(map(str,act)) if len(act)==3 else '';vals.append(int(a in ts[:10]))
  cov=float(np.mean(vals)) if vals else np.nan;selected_missing=0
  for _,r in sel.iterrows():
   code=str(r.get('race_code','')).zfill(12);act=v222.v166.combo(r.get('actual_combo'));actual='-'.join(map(str,act)) if len(act)==3 else ''
   if not actual or code not in oi.index:continue
   ts=safe_order(r,pair)
   if ts is None:selected_missing+=1;continue
   o=oi.loc[code];o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o;tickets=ts[:10]
   try: od=[float(o[t]) for t in tickets]
   except: continue
   if len(od)!=10 or any(not np.isfinite(x) or x<=0 for x in od):continue
   st=v205.round_dutch(od,BANK)
   if not bool((st>=100).all()):continue
   comp=1/sum(1/x for x in od);hit=int(actual in tickets and st[tickets.index(actual)]>0) if actual in tickets else 0;ret=float(st[tickets.index(actual)]*od[tickets.index(actual)]) if hit else 0.;p3=float(r._p);est=p3*cov;ev=est*comp
   race.append({'month':mon,'date':r._date.strftime('%Y-%m-%d'),'race_code':code,'p3':p3,'prior_cov':cov,'est_hit':est,'comp':comp,'ev':ev,'hit':hit,'ret':ret,'profit':ret-BANK})
  skip.append((mon,prior_missing,selected_missing,len(vals),k))
 z=pd.DataFrame(race);z.to_csv(OUT,index=False)
 rules=[('ALL',lambda x:np.ones(len(x),bool)),('comp>=2.5',lambda x:x.comp>=2.5),('comp>=2.75',lambda x:x.comp>=2.75),('comp>=3.0',lambda x:x.comp>=3.0),('comp[3.0,3.25)',lambda x:(x.comp>=3)&(x.comp<3.25)),('EV>=1.20',lambda x:x.ev>=1.20)]
 L=['# v229 Jul/Aug non-pristine shadow check','', '**NON-PRISTINE / SANITY CHECK ONLY:** Jul/Aug were previously exposed/contaminated. These results cannot validate, tune, or justify adoption of a rule.','- Rules are frozen from the prior Dec-Jun closing-odds exploration.','- Top10 fixed; exact 10,000-yen Dutch; losing race = -10,000 yen.','- Races with missing V221 pair-serving features are skipped, never imputed.','', '## Missing pair-feature audit','', '|month|prior winners skipped|selected skipped|prior coverage N|head selection K|','|---|---:|---:|---:|---:|']
 for m,pm,sm,n,k in skip:L.append(f'|{m}|{pm}|{sm}|{n}|{k}|')
 L+=['','## Shadow results','', '|rule|period|R|hit|ROI|profit|maxDD|','|---|---|---:|---:|---:|---:|---:|']
 if z.empty:
  raise RuntimeError('no settled Jul/Aug rows after eligibility filters')
 for name,fn in rules:
  for period,g0 in [('Jul+Aug',z),*[(m,z[z.month==m]) for m in MONTHS]]:
   g=g0[fn(g0)].copy()
   if g.empty:L.append(f'|{name}|{period}|0|-|-|0|0|');continue
   roi=100*g.ret.sum()/(len(g)*BANK);prof=g.profit.sum();dd=maxdd(g.sort_values(['date','race_code']).profit);L.append(f'|{name}|{period}|{len(g)}|{100*g.hit.mean():.2f}%|{roi:.2f}%|{prof:.0f}|{dd:.0f}|')
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
