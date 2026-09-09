#!/usr/bin/env python3
"""v229 Jul/Aug shadow. NON-PRISTINE descriptive check only."""
from pathlib import Path
from datetime import date
import numpy as np,pandas as pd
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v205_3head_operational_replay as v205
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v224_3head_national_form_decompose as v224
ROOT=Path(__file__).resolve().parent; SRC=ROOT/'analysis_v108_1head_feasibility.csv'; OUT=ROOT/'analysis_v229_3head_jul_aug_shadow.csv'; MISS=ROOT/'analysis_v229_missing_pair_rows.csv'; SUM=ROOT/'summary_v229_3head_jul_aug_shadow.md'; BANK=10000
MONTHS=['2026-07','2026-08']; ENDTS=pd.Timestamp('2026-09-01')
def uniq(x):return list(dict.fromkeys([c for c in x if c]))
def maxdd(a):
 c=np.cumsum(np.asarray(a,float));pk=np.maximum.accumulate(np.r_[0.,c]);return float((pk[1:]-c).max()) if len(c) else 0.
def safe_order(r,pair):
 try:return v222.order(r,pair,'V221')
 except ValueError as e:
  if 'NaN' in str(e) or 'missing values' in str(e):return None
  raise
def fit_pair_audit(tr,month,miss):
 X=[];y=[];n=0
 for _,r in tr.iterrows():
  if v222.ii(r.get('valid_result'))!=1:continue
  a=v222.v166.combo(r.get('actual_combo'))
  if len(a)!=3 or a[0]!=3 or a[1] not in v222.OPP or a[2] not in v222.OPP or a[1]==a[2]:continue
  vecs=[];bad=False
  for s in v222.OPP:
   for t in v222.OPP:
    if s==t:continue
    z=np.asarray(v222.pairvec(r,s,t,'V221'),float)
    if not np.isfinite(z).all():bad=True
    vecs.append((z,int(s==a[1] and t==a[2])))
  if bad:
   miss.append({'month':month,'scope':'pair_train','date':str(r.get('_date',''))[:10],'race_code':str(r.get('race_code','')).zfill(12),'actual_combo':str(r.get('actual_combo','')),'note':'non-finite V221 pair vector'})
   continue
  n+=1
  for z,yy in vecs:X.append(z);y.append(yy)
 if n<100:raise RuntimeError(f'small finite pair train {month}: {n}')
 m=v222.Pipeline([('s',v222.StandardScaler()),('m',v222.LogisticRegression(C=.35,max_iter=1800,solver='lbfgs'))]);m.fit(np.asarray(X,float),np.asarray(y,int));return m,n
def main():
 v223.CONTAM=ENDTS;v223.END=date(2026,8,31);v224.CONTAM=ENDTS
 raw=pd.read_csv(SRC,dtype={'race_code':str});dc=v165.pc(raw,['date','race_date','ymd']);vc=v165.pc(raw,['venue','jcd','stadium','place']);y,_=v165.target(raw);base=v165.feats(raw);raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce');raw['_y']=y;raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<ENDTS)].copy()
 d=v221.build(raw,dc);d=v222.build_current(d,dc);d=v223.build_unused(d,dc);d=v224.add_decomp(d,dc)
 hist=v222.cols(d,'b3_vh_');rel=[c for c in d if c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))];cur=[c for c in v222.cols(d,'c_b3_') if not c.startswith(('c_b3_minus_','c_b3_inside_','c_b3_outside_'))]+[c for c in d if c.startswith(('c_wall','c_attack3','c_outer','c_ex_spread','c_st_spread','c_turn_spread','c_straight_spread'))];form=[c for c in d if c.startswith(('f_b3_m1_','f_b3_m12_','f_b3_m35_','f_b3_trend_','f_rel_'))]+[c for c in ['f_b3_layoff','f_b3_grade','f_b3_m1_grade'] if c in d];fs=uniq(list(base)+hist+cur+rel+form)
 odds=v205.load_odds();oi=odds.set_index('race_code',drop=False);race=[];skip=[];miss=[]
 for mon in MONTHS:
  first=pd.Timestamp(mon+'-01');nxt=first+pd.offsets.MonthBegin(1);pair,ntrain=fit_pair_audit(d[d._date<first],mon,miss);bte,_=v223.fit_head(d,list(base),vc,first,nxt);k=max(1,int((bte._p>=.30).sum()));te,_=v223.fit_head(d,fs,vc,first,nxt);sel=te.nlargest(k,'_p')
  vals=[];prior_missing=0
  for _,r in d[(d._date<first)&(d._y==1)].iterrows():
   ts=safe_order(r,pair)
   if ts is None:
    prior_missing+=1;miss.append({'month':mon,'scope':'prior_coverage','date':str(r.get('_date',''))[:10],'race_code':str(r.get('race_code','')).zfill(12),'actual_combo':str(r.get('actual_combo','')),'note':'non-finite V221 pair vector'});continue
   act=v222.v166.combo(r.get('actual_combo'));a='-'.join(map(str,act)) if len(act)==3 else '';vals.append(int(a in ts[:10]))
  cov=float(np.mean(vals)) if vals else np.nan;selected_missing=0
  for _,r in sel.iterrows():
   code=str(r.get('race_code','')).zfill(12);act=v222.v166.combo(r.get('actual_combo'));actual='-'.join(map(str,act)) if len(act)==3 else ''
   if not actual or code not in oi.index:continue
   ts=safe_order(r,pair)
   if ts is None:
    selected_missing+=1;miss.append({'month':mon,'scope':'selected','date':str(r.get('_date',''))[:10],'race_code':code,'actual_combo':actual,'note':'non-finite V221 pair vector'});continue
   o=oi.loc[code];o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o;tickets=ts[:10]
   try:od=[float(o[t]) for t in tickets]
   except:continue
   if len(od)!=10 or any(not np.isfinite(x) or x<=0 for x in od):continue
   st=v205.round_dutch(od,BANK)
   if not bool((st>=100).all()):continue
   comp=1/sum(1/x for x in od);hit=int(actual in tickets and st[tickets.index(actual)]>0) if actual in tickets else 0;ret=float(st[tickets.index(actual)]*od[tickets.index(actual)]) if hit else 0.;p3=float(r._p);est=p3*cov;ev=est*comp
   race.append({'month':mon,'date':r._date.strftime('%Y-%m-%d'),'race_code':code,'p3':p3,'prior_cov':cov,'est_hit':est,'comp':comp,'ev':ev,'hit':hit,'ret':ret,'profit':ret-BANK})
  skip.append((mon,ntrain,prior_missing,selected_missing,len(vals),k))
 pd.DataFrame(miss).drop_duplicates().to_csv(MISS,index=False);z=pd.DataFrame(race);z.to_csv(OUT,index=False)
 if z.empty:raise RuntimeError('no settled Jul/Aug rows after eligibility filters')
 rules=[('ALL',lambda x:np.ones(len(x),bool)),('comp>=2.5',lambda x:x.comp>=2.5),('comp>=2.75',lambda x:x.comp>=2.75),('comp>=3.0',lambda x:x.comp>=3.0),('comp[3.0,3.25)',lambda x:(x.comp>=3)&(x.comp<3.25)),('EV>=1.20',lambda x:x.ev>=1.20)]
 L=['# v229 Jul/Aug non-pristine shadow check','','**NON-PRISTINE / SANITY CHECK ONLY.**','- Top10 fixed; exact 10,000-yen Dutch; losing race = -10,000 yen.','- Missing V221 pair rows are audited in analysis_v229_missing_pair_rows.csv and not imputed.','','## Missing audit','|month|finite pair-train races|prior winners skipped|selected skipped|prior coverage N|head K|','|---|---:|---:|---:|---:|---:|']
 for m,nt,pm,sm,n,k in skip:L.append(f'|{m}|{nt}|{pm}|{sm}|{n}|{k}|')
 L+=['','## Shadow results','|rule|period|R|hit|ROI|profit|maxDD|','|---|---|---:|---:|---:|---:|---:|']
 for name,fn in rules:
  for period,g0 in [('Jul+Aug',z),*[(m,z[z.month==m]) for m in MONTHS]]:
   g=g0[fn(g0)].copy()
   if g.empty:L.append(f'|{name}|{period}|0|-|-|0|0|');continue
   roi=100*g.ret.sum()/(len(g)*BANK);prof=g.profit.sum();dd=maxdd(g.sort_values(['date','race_code']).profit);L.append(f'|{name}|{period}|{len(g)}|{100*g.hit.mean():.2f}%|{roi:.2f}%|{prof:.0f}|{dd:.0f}|')
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L));print('missing rows',len(pd.DataFrame(miss).drop_duplicates()))
if __name__=='__main__':main()
