#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,time
from datetime import date,timedelta
from pathlib import Path
import numpy as np,pandas as pd
from scipy.special import logsumexp
from backtest import rows as source_rows
import run_v323_1head_frozen_live_adapter as v323
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v310_1head_opponent_headrisk_second as v310
import run_v311_1head_opponent_second_family_autoresearch as v311
import run_v317_1head_opponent_error_features as v317
import run_v318_1head_opponent_third_rebuild as v318
import run_v299_1head_trifecta3_policy_search as v299
import run_v312_1head_opponent_outer_gate as v312
import run_v321_1head_julaug_nonpristine_validation as v321
import onehead_production_profile as prod

def resolve_ticket_strategy(policy):
 p=str(policy)
 if p=='v320_HYBRID':return 'HYBRID'
 if p in v299.STRATEGIES:return p
 raise RuntimeError(f'unsupported production ticket policy: {p}')

def sep_features(labels,target):
 out=[]
 for ds in sorted(labels.date.astype(str).unique()):
  d=date.fromisoformat(ds)
  if d>=target:continue
  # Historical September cards are canonical BoatraceCSV inputs and are not
  # materialized in this repository. Use the same remote loader as the
  # verified September source builder instead of Path.exists().
  cards=source_rows(f'data/programs/race_cards/{d:%Y/%m/%d}.csv')
  if not cards:continue
  cur=v323.current_static(cards,d);feat,_,_=v323.build_current_features(cur);out.append(feat)
 if not out:raise RuntimeError('no September reconstructed features')
 z=pd.concat(out,ignore_index=True);lab=labels[['race_code','head_hit','actual_combo']].copy();lab.race_code=lab.race_code.astype(str).str.zfill(12);z.race_code=z.race_code.astype(str).str.zfill(12);z=z.merge(lab,on='race_code',how='inner',validate='one_to_one');return z

def align_append(base,extra):
 for c in base.columns:
  if c not in extra:extra[c]=np.nan
 return pd.concat([base,extra[list(base.columns)]],ignore_index=True)
def p2_fit(sl,target_date):
 tr=sl[pd.to_datetime(sl.date).dt.date<target_date].copy();te=sl[pd.to_datetime(sl.date).dt.date==target_date].copy();fs=v311.audited_features(tr);fs=[c for c in fs if v311.family(c)!='START'];m=v300.fastbase.FastSecond(1.).fit(tr,fs,'y2');te=te.copy();te['score']=m.score(te);return {str(c).zfill(12):v298.v279.probs_within_race(g,'score') for c,g in te.groupby('race_code')},len(fs)
def pc_fit(cl,target_date,l2=.1,drop_start=True):
 tr=cl[(pd.to_datetime(cl.date).dt.date<target_date)&(cl.train_group==1)].copy();te=cl[pd.to_datetime(cl.date).dt.date==target_date].copy();meta={'date','month','race_code','group_id','second_boat','third_boat','train_group','ycond','actual2','actual3'};fs=v300.good(tr,[c for c in tr.columns if c not in meta]);fs=[c for c in fs if 'meet_' not in str(c)]
 if drop_start:fs=[c for c in fs if 'nst_strength' not in str(c)]
 m=v318.fastbase.FastConditional(l2).fit(tr,fs);te=te.copy();te['score']=m.score(te);out={}
 for code,g in te.groupby('race_code'):
  pc={}
  for s,gs in g.groupby('second_boat'):
   aa=gs.score.to_numpy(float);pp=np.exp(aa-logsumexp(aa))
   for t,p in zip(gs.third_boat.astype(int),pp):pc[(int(s),int(t))]=float(p)
  out[str(code).zfill(12)]=pc
 return out,len(fs)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--target-date',default='2026-09-15');ap.add_argument('--sep-source',type=Path,required=True);ap.add_argument('--cards',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);a=ap.parse_args();t0=time.perf_counter();target=date.fromisoformat(a.target_date);labels=pd.read_csv(a.sep_source,dtype={'race_code':str});labels=labels[pd.to_datetime(labels.date).dt.date<target].copy()
 if labels.empty or max(pd.to_datetime(labels.date).dt.date)>=target:raise RuntimeError('chronology failure')
 sep=sep_features(labels,target);head0=pd.read_csv(v323.PREP_HEAD,dtype={'race_code':str});slim0=pd.read_csv(v323.PREP_SLIM,dtype={'race_code':str});headhist=align_append(head0,sep.copy());slimhist=align_append(slim0,sep.copy());a.out_dir.mkdir(parents=True,exist_ok=True);hp=a.out_dir/'rolling_head.csv.gz';sp=a.out_dir/'rolling_slim.csv.gz';headhist.to_csv(hp,index=False,compression='gzip');slimhist.to_csv(sp,index=False,compression='gzip')
 cur0=v323.current_static(v323.load_cards(a.cards),target);cur,_,_=v323.build_current_features(cur0);head=v323.head_score(cur,prod.HEAD_CUTOFF,history_path=hp,allow_rolling_history=True)
 v300.setup_v298();sufs=v298.suffixes(slimhist);curx=cur.copy();curx['head_hit']=0;curx['actual_combo']=''
 for c in slimhist.columns:
  if c not in curx:curx[c]=np.nan
 full=pd.concat([slimhist,curx[list(slimhist.columns)]],ignore_index=True);sl=v300.augment_second(v298.second_long(full,sufs));_,p3,p4=v312.load_cache();sx,_=v317.add_engineered(v310.add_headrisk(sl,p3,p4),'OUTER');p2,n2=p2_fit(sx,target);cl=v300.augment_third(v321._third_fold_long(full,sufs,target.strftime('%Y-%m')));pc,n3=pc_fit(cl,target);base2,_=p2_fit(sl,target);basepc,_=pc_fit(cl,target,l2=.3,drop_start=False);strategy=resolve_ticket_strategy(prod.TICKET_POLICY);fn=v299.STRATEGIES[strategy];outrows=[]
 for _,r in head.iterrows():
  code=str(r.race_code).zfill(12);mass=v300.base5(base2[code],basepc[code])[1];pair=v299.pair_prob(p2[code],pc[code],prod.TICKET_ALPHA);top=fn(p2[code],pc[code],pair)[:3];outrows.append({'race_code':code,'final_head_p':float(r.p_head),'opp_mass':float(mass),'p2':{str(k):float(v) for k,v in p2[code].items()},'pc':{f'{s}-{t}':float(v) for (s,t),v in pc[code].items()},'base_tickets':';'.join(f'1-{s}-{t}' for s,t in top)})
 meta={'production_profile':prod.PROFILE_NAME,'target_date':str(target),'training_cutoff':str(target-timedelta(days=1)),'september_rows':len(sep),'head_history_rows':len(headhist),'opponent_history_rows':len(slimhist),'second_features':n2,'third_features':n3,'ticket_policy':prod.TICKET_POLICY,'ticket_strategy':strategy,'same_day_outcomes_read':False,'target_or_future_rows':0,'chronology_guard':True,'build_sec':time.perf_counter()-t0};(a.out_dir/'rolling_models.json').write_text(json.dumps({'meta':meta,'races':outrows},ensure_ascii=False,indent=2));print(json.dumps(meta,ensure_ascii=False))
if __name__=='__main__':main()
