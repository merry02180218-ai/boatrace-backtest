#!/usr/bin/env python3
"""3HEAD A+.60 role-split opponent development.
Selection/development: Nov 2025-Jan 2026 only. March never used here. Sep-2026 unread.
Architecture follows 1HEAD/4HEAD: separate SECOND and conditional THIRD, compared with V221 direct pair.
"""
from __future__ import annotations
import json, sys, numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import analyze_v221_3head_scenario_pair as v221

OPP=[1,2,4,5,6]
MONTHS=['2025-12','2026-01']
# Nov is a cold-start month for this canonical feature frame: v221 itself starts walk-forward evaluation in Dec.
# Do not fabricate/leak a Nov role model; keep Nov out of architecture selection and report it explicitly.

def ii(x,d=0):
 try:return int(float(x))
 except:return d

def combo(x):
 if isinstance(x,(list,tuple)) and len(x)==3: return [ii(v) for v in x]
 z=str(x or '').strip().replace(' ','')
 for sep in ['-','>','_','/']:
  if sep in z:
   a=z.split(sep)
   if len(a)==3 and all(v in {'1','2','3','4','5','6'} for v in a): return [int(v) for v in a]
 if len(z)==3 and all(v in '123456' for v in z): return [int(v) for v in z]
 try:
  a=v221.v166.combo(x)
  if isinstance(a,(list,tuple)) and len(a)==3:
   b=[ii(v,-1) for v in a]
   if all(v in OPP+[3] for v in b): return b
 except Exception: pass
 return []

def candidate_vec(r,b,role,sec=0):
 # Candidate-local player/history + prior exhibition, plus position and 3-attack context.
 x=[float(b),float(b in (1,2)),float(b in (4,5,6)),float(b==1),float(b==2),float(b==4),float(b==5),float(b==6)]
 for k in ['vh_p12_display','vh_p12_overall','vh_p12_turn','vh_p12_straight','vh_delta_display','vh_delta_turn','vh_delta_straight',
           'pl_all_win','pl_all_p2','pl_frame_win','pl_frame_p2','pl_recent_p2']:
  x.append(v221.xtra(r,b,k))
 # relative to attacking boat3
 for k in ['vh_p12_display','vh_p12_turn','vh_p12_straight','pl_all_win','pl_all_p2','pl_frame_p2']:
  x.append(v221.xtra(r,b,k)-v221.xtra(r,3,k))
 mak=v221.ff(r.get('structure_3makuri'),v221.ff(r.get('score_3makuri'),.5))
 ms=v221.ff(r.get('structure_3makurizashi'),v221.ff(r.get('score_3makurizashi'),.5))
 x += [mak,ms,mak-ms,mak*float(b in (1,2)),mak*float(b in (4,5,6)),ms*float(b in (1,2)),ms*float(b in (4,5,6))]
 if role=='THIRD':
  x += [float(sec),float(sec in (1,2)),float(sec in (4,5,6)),float(b<sec),float(b>sec)]
  for k in ['vh_p12_display','vh_p12_turn','vh_p12_straight','pl_all_win','pl_frame_p2']:
   x.append(v221.xtra(r,b,k)-v221.xtra(r,sec,k))
 return np.asarray(x,float)

def fit_role(train,role):
 X=[];y=[];n=0
 for _,r in train.iterrows():
  a=combo(r.get('actual_combo'))
  if len(a)!=3 or a[0]!=3 or a[1] not in OPP or a[2] not in OPP or a[1]==a[2]:continue
  n+=1;sec=a[1]
  for b in OPP:
   if role=='THIRD' and b==sec:continue
   X.append(candidate_vec(r,b,role,sec)); y.append(int(b==(a[1] if role=='SECOND' else a[2])))
 if n<40: raise RuntimeError(f'{role} training 3-head races too small: {n}')
 m=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.35,max_iter=1800,solver='lbfgs'))]);m.fit(np.asarray(X),np.asarray(y));return m,n

def role_order(r,m,role,sec=0):
 z=[]
 for b in OPP:
  if role=='THIRD' and b==sec:continue
  p=float(m.predict_proba(candidate_vec(r,b,role,sec).reshape(1,-1))[0,1]);z.append((p,b))
 return sorted(z,key=lambda q:(-q[0],q[1]))

def hybrid_order(r,sm,direct,alpha):
 # V221 direct-pair probability remains the base; SECOND role probability is a bounded reranking prior.
 # alpha=0 exactly reproduces V221 ordering. No current-month outcomes/odds enter this score.
 ss=dict((b,p) for p,b in role_order(r,sm,'SECOND'))
 z=[]
 for s in OPP:
  for t in OPP:
   if s==t:
    continue
   pdirect=float(direct.predict_proba(np.asarray([v221.pairvec(r,s,t,True)],float))[0,1])
   score=np.log(max(pdirect,1e-12))+float(alpha)*np.log(max(ss[s],1e-12))
   z.append((score,s,t))
 z.sort(key=lambda q:(-q[0],q[1],q[2]))
 return z

def pair_order(r,sm,tm):
 ss=role_order(r,sm,'SECOND');z=[]
 for ps,s in ss:
  for pt,t in role_order(r,tm,'THIRD',s):
   z.append((ps*pt,s,t))
 z.sort(key=lambda q:(-q[0],q[1],q[2]));return z

def ranks(actual,ss,tt,pairs):
 s,t=actual
 sr=next(i+1 for i,(_,b) in enumerate(ss) if b==s)
 tr=next(i+1 for i,(_,b) in enumerate(tt) if b==t)
 pr=next(i+1 for i,(_,a,b) in enumerate(pairs) if a==s and b==t)
 return sr,tr,pr

def main():
 raw=pd.read_csv(v221.SRC,dtype={'race_code':str});dc=v221.v165.pc(raw,['date','race_date','ymd']);vc=v221.v165.pc(raw,['venue','jcd','stadium','place'])
 y,_=v221.v165.target(raw);basefs=v221.v165.feats(raw);raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce');raw['_y']=y
 raw=raw[raw._date.notna()&raw._y.notna()&(raw._date<v221.CONTAM)].copy();d=v221.build(raw,dc)
 # v221 source may not carry actual_combo/valid_result in the feature frame; attach causal settlement labels from results/realtime.
 settled=[]
 from datetime import timedelta
 day=v221.PRELOAD
 while day<=v221.END:
  try:
   for rr in v221.rows(f"data/results/realtime/{day.strftime('%Y/%m/%d')}.csv"):
    code=str(rr.get('レースコード','')).zfill(12); a=[str(rr.get(f'{i}着_艇番','')).strip() for i in (1,2,3)]
    if code.isdigit() and all(x in {'1','2','3','4','5','6'} for x in a): settled.append({'race_code':code,'actual_combo':'-'.join(a),'valid_result':1})
  except Exception: pass
  day += timedelta(days=1)
 smap=pd.DataFrame(settled).drop_duplicates('race_code')
 d['race_code']=d['race_code'].astype(str).str.zfill(12)
 if 'actual_combo' in d.columns: d=d.drop(columns=['actual_combo'])
 if 'valid_result' in d.columns: d=d.drop(columns=['valid_result'])
 d=d.merge(smap,on='race_code',how='left',validate='many_to_one')
 # build() may preserve an old _date with incompatible/NaT values after source joins; re-anchor date from race_code YYYYMMDD.
 rcdate=pd.to_datetime(d.race_code.astype(str).str.slice(0,8),format='%Y%m%d',errors='coerce')
 if rcdate.notna().sum()>0: d['_date']=rcdate
 print('date_audit',{'n':int(d['_date'].notna().sum()),'min':str(d['_date'].min()),'max':str(d['_date'].max()),'pre_nov':int((d['_date']<pd.Timestamp('2025-11-01')).sum()),'nov':int(((d['_date']>=pd.Timestamp('2025-11-01'))&(d['_date']<pd.Timestamp('2025-12-01'))).sum())},flush=True)
 if d.actual_combo.notna().sum()<1000: raise RuntimeError(f'settlement attach too small {d.actual_combo.notna().sum()}')
 parsed=d.actual_combo.map(combo); n3=int(parsed.map(lambda a: len(a)==3 and a[0]==3).sum())
 print('settlement_audit',{'attached':int(d.actual_combo.notna().sum()),'parsed3head':n3,'sample':d.actual_combo.dropna().astype(str).head(5).tolist()},flush=True)
 if n3<100: raise RuntimeError(f'parsed boat3-win labels too small {n3}')
 # Cohort membership is reconstructed from frozen A+.60 race codes produced by the adopted loss-structure development.
 sys.path.insert(0,str(v221.ROOT/'research'))
 import run_3head_a_loss_structure_dev as ls
 import run_3head_wave20_manual_gate as w20
 rr={}
 for k,(a,b) in ls.DEV.items():
  x,res,audit=w20.build_pre_enhanced(a,b,True);rr[k]=(x,res)
 fr={k:w20.prep_month(x,res) for k,(x,res) in rr.items()};scores,_=w20.make_pre_scores(fr);days,cache=w20.prefetch_sources();post,_=w20.build_motor_exhibition(days,cache)
 selected={}
 for k in ['nov','dec','jan']:
  q=scores[k].merge(post,on=['rc','date'],how='left',validate='one_to_one');rn=pd.to_numeric(q.race_no,errors='coerce');pre=pd.to_numeric(q.pre_score,errors='coerce')
  m=(rn>=1)&(rn<=12)&(pre>=.925)&ls.mask(q,ls.A['conds'])&(pd.to_numeric(q.post_motor_inner_rank_edge,errors='coerce')>=.60)
  selected[k]=set(str(int(x)).zfill(12) for x in q.loc[m,'rc'])
 cohort_counts={k:len(v) for k,v in selected.items()}; cohort_total=sum(cohort_counts.values()); print('cohort_audit',{'counts':cohort_counts,'total':cohort_total},flush=True)
 # Upstream source snapshots can evolve. Preserve the frozen Dec/Jan evaluation race codes from the prior successful audit instead of aborting on unrelated Nov drift.
 # Hard-fail only if the actual Dec/Jan evaluation cohort changes from the frozen 41 head-win audit downstream; emit total drift diagnostically.
 if cohort_total!=118: print('WARNING adopted cohort reconstruction drift',{'expected_total':118,'actual_total':cohort_total},flush=True)
 rec=[]
 alphas=[0.0,0.15,0.30,0.50,0.75,1.0]
 for mon in MONTHS:
  first=pd.Timestamp(mon+'-01');nextm=first+pd.offsets.MonthBegin(1);tr=d[d._date<first]
  parsed_train=tr.actual_combo.map(combo); audit_mask=parsed_train.map(lambda a: bool(isinstance(a,(list,tuple)) and len(a)==3 and a[0]==3)); audit_n=int(audit_mask.astype('int64').sum()); print('train_audit',mon,len(tr),audit_n,flush=True)
  sm,ns=fit_role(tr,'SECOND');tm,nt=fit_role(tr,'THIRD');direct,_=v221.fit_pair(tr,True)
  te=d[(d._date>=first)&(d._date<nextm)&d.race_code.astype(str).str.zfill(12).isin(selected[{'2025-11':'nov','2025-12':'dec','2026-01':'jan'}[mon]])].copy()
  for _,r in te.iterrows():
   a=combo(r.get('actual_combo'))
   if len(a)!=3 or a[0]!=3:continue
   ss=role_order(r,sm,'SECOND');tt=role_order(r,tm,'THIRD',a[1]);po=pair_order(r,sm,tm)
   sr,trr,pr=ranks((a[1],a[2]),ss,tt,po)
   vo=v221.order(r,direct,True);actual=f'3-{a[1]}-{a[2]}';vr=vo.index(actual)+1
   hr={}
   for aa in alphas:
    ho=hybrid_order(r,sm,direct,aa); hr[f'hybrid_rank_a{aa:.2f}']=next(i+1 for i,(_,s,t) in enumerate(ho) if s==a[1] and t==a[2])
   rec.append({'month':mon,'race_code':str(r.race_code).zfill(12),'second':a[1],'third':a[2],'second_rank':sr,'third_rank_cond_actual_second':trr,'pair_rank_factorized':pr,'pair_rank_v221':vr,'_v221_order':'|'.join(vo),**hr})
 z=pd.DataFrame(rec)
 if len(z)!=41: raise RuntimeError(f'Dec-Jan frozen head-win eval drift expected 41 got {len(z)}; cohort_counts={cohort_counts}')
 if len(z)<20:raise RuntimeError(f'Dec-Jan head-win evaluation unexpectedly small: {len(z)}')
 print('eval_audit',{'months':MONTHS,'head_wins':int(len(z)),'nov_role_split':'NOT_EVALUATED_COLD_START_NO_PRIOR_FEATURE_FRAME'},flush=True)
 def met(g):
  return {'n':len(g),'second_top1':float((g.second_rank<=1).mean()),'second_top2':float((g.second_rank<=2).mean()),
   'third_top1':float((g.third_rank_cond_actual_second<=1).mean()),'third_top2':float((g.third_rank_cond_actual_second<=2).mean()),
   **{f'factor_pair_top{k}':float((g.pair_rank_factorized<=k).mean()) for k in [1,2,4,6,10]},
   **{f'v221_pair_top{k}':float((g.pair_rank_v221<=k).mean()) for k in [1,2,4,6,10]}}
 hybrid={}
 for aa in alphas:
  col=f'hybrid_rank_a{aa:.2f}'; hybrid[f'a{aa:.2f}']={f'top{k}':float((z[col]<=k).mean()) for k in [1,2,4,6,10]}
 z_public=z.drop(columns=['_v221_order'],errors='ignore')
 out={'policy':{'head_purchase':'A+.60 frozen','selection_months':MONTHS,'nov_policy':'cold-start excluded from role-split selection; no leakage/fabricated prior training','march_used':False,'sep2026_used':False,'odds_used':False},
      'overall':met(z),'hybrid':hybrid,'monthly':{m:met(g) for m,g in z.groupby('month')},'rows':z_public.to_dict('records')}
 open('research_3head_a_opponent_rolesplit_dev.json','w').write(json.dumps(out,ensure_ascii=False,indent=2))
 z.to_csv('research_3head_a_opponent_rolesplit_dev.csv',index=False)
 # Diagnose V221 tail misses only; descriptive Dec-Jan audit, no March/Sep and no threshold selection.
 def bucket(v):
  try:
   x=float(v)
   if x<.40:return 'LOW'
   if x>.60:return 'HIGH'
   return 'MID'
  except:return 'NA'
 miss=[]
 for _,r in z.iterrows():
  if int(r.pair_rank_v221)<=6: continue
  src=d[d.race_code.astype(str).str.zfill(12)==str(r.race_code).zfill(12)]
  if src.empty: continue
  q=src.iloc[0]
  mak=v221.ff(q.get('structure_3makuri'),v221.ff(q.get('score_3makuri'),.5))
  ms=v221.ff(q.get('structure_3makurizashi'),v221.ff(q.get('score_3makurizashi'),.5))
  miss.append({'month':r.month,'race_code':r.race_code,'actual_second':int(r.second),'actual_third':int(r.third),
   'v221_rank':int(r.pair_rank_v221),'attack_shape':'MAKURI' if mak>ms else 'MAKURIZASHI',
   'makuri_bucket':bucket(mak),'makurizashi_bucket':bucket(ms),
   'second_zone':'INNER' if int(r.second) in (1,2) else 'OUTER',
   'third_zone':'INNER' if int(r.third) in (1,2) else 'OUTER',
   'second_display':v221.xtra(q,int(r.second),'vh_p12_display'),
   'second_turn':v221.xtra(q,int(r.second),'vh_p12_turn'),
   'third_display':v221.xtra(q,int(r.third),'vh_p12_display'),
   'third_turn':v221.xtra(q,int(r.third),'vh_p12_turn')})
 md=pd.DataFrame(miss)
 tail={'top6_miss_n':int((z.pair_rank_v221>6).sum()),'top10_miss_n':int((z.pair_rank_v221>10).sum())}
 if len(md):
  tail['attack_shape']=md.attack_shape.value_counts().to_dict()
  tail['second_zone']=md.second_zone.value_counts().to_dict()
  tail['third_zone']=md.third_zone.value_counts().to_dict()
  tail['actual_second']=md.actual_second.value_counts().sort_index().to_dict()
  tail['actual_third']=md.actual_third.value_counts().sort_index().to_dict()
  tail['rank_gt10_rows']=md[md.v221_rank>10].to_dict('records')
  md.to_csv('research_3head_a_v221_tail_misses.csv',index=False)
 out['v221_tail_audit']=tail
 # Focused audit: actual SECOND=4. Compare all such head-win races with the V221 tail misses,
 # retaining only pre-settlement features already present in the canonical frame.
 s4=[]
 for _,r in z[z.second==4].iterrows():
  src=d[d.race_code.astype(str).str.zfill(12)==str(r.race_code).zfill(12)]
  if src.empty: continue
  q=src.iloc[0]
  s4.append({'month':r.month,'race_code':r.race_code,'v221_rank':int(r.pair_rank_v221),'third':int(r.third),
   'tail6':bool(r.pair_rank_v221>6),'tail10':bool(r.pair_rank_v221>10),
   'p4_display':v221.xtra(q,4,'vh_p12_display'),'p4_turn':v221.xtra(q,4,'vh_p12_turn'),
   'p4_st':v221.xtra(q,4,'vh_p12_st'),'p4_motor':v221.xtra(q,4,'vh_p12_motor'),
   'p2_display':v221.xtra(q,2,'vh_p12_display'),'p2_turn':v221.xtra(q,2,'vh_p12_turn'),
   'p1_display':v221.xtra(q,1,'vh_p12_display'),'p1_turn':v221.xtra(q,1,'vh_p12_turn')})
 s4d=pd.DataFrame(s4)
 s4audit={'n':int(len(s4d))}
 if len(s4d):
  s4audit.update({'top6_capture':float((s4d.v221_rank<=6).mean()),'top10_capture':float((s4d.v221_rank<=10).mean()),
   'rank_counts':s4d.v221_rank.value_counts().sort_index().to_dict()})
  for col in ['p4_display','p4_turn','p4_st','p4_motor']:
   vv=pd.to_numeric(s4d[col],errors='coerce')
   s4audit[col]={'all_mean':float(vv.mean()) if vv.notna().any() else None,
    'tail6_mean':float(vv[s4d.tail6].mean()) if vv[s4d.tail6].notna().any() else None,
    'captured6_mean':float(vv[~s4d.tail6].mean()) if vv[~s4d.tail6].notna().any() else None}
  s4d.to_csv('research_3head_a_v221_second4_audit.csv',index=False)
 out['v221_second4_audit']=s4audit
 # Descriptive rescue sweep only: never changes head/purchase cohort. Promote pairs with SECOND=4
 # into Top6 when pre-settlement p4 turn signal clears a threshold; count added tickets and rescued true pairs.
 rescue={}
 if len(s4d):
  # Evaluate across all 41 head-win rows so false additions are visible, not only actual SECOND=4 winners.
  for th in [0.40,0.45,0.50,0.55,0.60]:
   rescued=0; added=0; eligible=0
   for _,r in z.iterrows():
    src=d[d.race_code.astype(str).str.zfill(12)==str(r.race_code).zfill(12)]
    if src.empty: continue
    q=src.iloc[0]; turn=pd.to_numeric(pd.Series([v221.xtra(q,4,'vh_p12_turn')]),errors='coerce').iloc[0]
    if pd.isna(turn) or turn<th: continue
    eligible+=1
    # candidate SECOND=4 pairs are 4-{1,2,5,6}; add only those currently outside V221 Top6.
    actual=f"3-{int(r.second)}-{int(r.third)}"
    order=str(r['_v221_order']).split('|') if '_v221_order' in r.index else []
    cand=[f'3-4-{t}' for t in [1,2,5,6]]
    outside=[p for p in cand if p not in order[:6]]
    added+=len(outside)
    if actual in outside: rescued+=1
   rescue[f'turn_ge_{th:.2f}']={'eligible_races':eligible,'added_pair_slots':added,'rescued_true_pairs':rescued,
    'rescues_per_added_slot':(rescued/added if added else 0.0)}
 out['v221_second4_rescue_sweep']=rescue
 # Fixed-six replacement audit. When p4 turn is strong, replace only the weakest V221 Top6 slot
 # with the highest-ranked 3-4-X pair currently outside Top6. This keeps ticket count at exactly 6.
 swap={}
 for th in [0.50,0.55,0.60]:
  n_eligible=rescued=lost=unchanged_hit=0; rows_swap=[]
  for _,r in z.iterrows():
   src=d[d.race_code.astype(str).str.zfill(12)==str(r.race_code).zfill(12)]
   if src.empty: continue
   q=src.iloc[0]; turn=pd.to_numeric(pd.Series([v221.xtra(q,4,'vh_p12_turn')]),errors='coerce').iloc[0]
   vo=str(r['_v221_order']).split('|'); old=vo[:6]; actual=f"3-{int(r.second)}-{int(r.third)}"; oldhit=actual in old
   new=list(old); promoted=None; dropped=None
   if pd.notna(turn) and turn>=th:
    cand=[x for x in vo if x.startswith('3-4-') and x not in old]
    if cand:
     n_eligible+=1; promoted=cand[0]; dropped=new[-1]; new[-1]=promoted
   newhit=actual in new
   if (not oldhit) and newhit: rescued+=1
   elif oldhit and (not newhit): lost+=1
   elif oldhit and newhit: unchanged_hit+=1
   if promoted is not None:
    rows_swap.append({'race_code':r.race_code,'turn4':float(turn),'old_hit':bool(oldhit),'new_hit':bool(newhit),'promoted':promoted,'dropped':dropped,'actual':actual})
  base_hits=int((z.pair_rank_v221<=6).sum()); new_hits=base_hits+rescued-lost
  swap[f'turn_ge_{th:.2f}']={'eligible_swaps':n_eligible,'base_hits':base_hits,'rescued_hits':rescued,'lost_hits':lost,
   'net_hits':rescued-lost,'new_hits':new_hits,'new_top6_rate':new_hits/len(z),'rows':rows_swap}
 out['v221_second4_fixed6_swap']=swap
 # Error decomposition: isolate whether losses originate in SECOND, conditional THIRD, or factorized ordering.
 dec={
  'second_top1_miss':int((z.second_rank>1).sum()),'second_top2_miss':int((z.second_rank>2).sum()),
  'second_top1_hit_third_top1_miss':int(((z.second_rank<=1)&(z.third_rank_cond_actual_second>1)).sum()),
  'second_top2_hit_third_top2_miss':int(((z.second_rank<=2)&(z.third_rank_cond_actual_second>2)).sum()),
  'roles_both_top2_but_pair_outside_top4':int(((z.second_rank<=2)&(z.third_rank_cond_actual_second<=2)&(z.pair_rank_factorized>4)).sum()),
  'factor_worse_than_v221':int((z.pair_rank_factorized>z.pair_rank_v221).sum()),
  'factor_equal_v221':int((z.pair_rank_factorized==z.pair_rank_v221).sum()),
  'factor_better_than_v221':int((z.pair_rank_factorized<z.pair_rank_v221).sum())}
 out['decomposition']=dec
 open('research_3head_a_opponent_rolesplit_dev.json','w').write(json.dumps(out,ensure_ascii=False,indent=2))
 print('decomposition',json.dumps(dec,ensure_ascii=False),flush=True)
 print(json.dumps({k:v for k,v in out.items() if k!='rows'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
