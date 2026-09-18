#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
import onehead_production_profile as prod
import run_v323_1head_frozen_live_adapter as live
import run_v300_1head_trifecta3_feature_upgrade as v300
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v310_1head_opponent_headrisk_second as v310
import run_v311_1head_opponent_second_family_autoresearch as v311
import run_v312_1head_opponent_outer_gate as v312
import run_v317_1head_opponent_error_features as v317
import run_v318_1head_opponent_third_rebuild as v318
import run_v321_1head_julaug_nonpristine_validation as v321
import run_v332_1head_attack_first_redesign as v332
import run_v299_1head_trifecta3_policy_search as v299

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--date',required=True);ap.add_argument('--cards',type=Path,required=True);ap.add_argument('--pre',type=Path);ap.add_argument('--race-code',default='');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();target=pd.Timestamp(a.date).date();wanted=str(a.race_code).zfill(12) if a.race_code else ''
 cur0=live.current_static(live.load_cards(a.cards),target);cur,_,_=live.build_current_features(cur0);head=live.head_score(cur,prod.LIVE_HEAD_CUTOFF)
 slim=pd.read_csv(live.PREP_SLIM,dtype={'race_code':str});slim.race_code=slim.race_code.astype(str).str.zfill(12);v300.setup_v298();sufs=v298.suffixes(slim);cc=cur.copy();cc['head_hit']=0;cc['actual_combo']=''
 for c in slim.columns:
  if c not in cc: cc[c]=float('nan')
 full=pd.concat([slim,cc[list(slim.columns)]],ignore_index=True);full.race_code=full.race_code.astype(str).str.zfill(12)
 sl=v300.augment_second(v298.second_long(full,sufs));base_p2,_=v300.p2_predict(sl,live.TARGET_MONTH,10.0,False);_,p3,p4=v312.load_cache();sx,_=v317.add_engineered(v310.add_headrisk(sl,p3,p4),'OUTER');p2,_=v311.p2_predict_explicit(sx,live.TARGET_MONTH,1.0,None,{'START'})
 cl=v300.augment_third(v321._third_fold_long(full,sufs,live.TARGET_MONTH));base_pc,_=v300.pc_predict(cl,live.TARGET_MONTH,.3,False);pc,_=v318.pc_predict(cl,live.TARGET_MONTH,.1,'DROP_START')
 # Daily mode must cache every current race, not only PRE candidates. PRE rows are
 # metadata overlays; this keeps arbitrary LIVE requests fast without changing
 # production HEAD/opponent calculations.
 pm={str(c).zfill(12):{} for c in head.race_code.astype(str)}
 if a.pre:
  pre=pd.read_csv(a.pre,dtype={'race_code':str});pre.race_code=pre.race_code.astype(str).str.zfill(12)
  for code,m in pre.set_index('race_code').to_dict('index').items(): pm.setdefault(code,{}).update(m)
 if wanted: pm={wanted:pm.get(wanted,{})}
 hm=head.set_index('race_code');a.out.mkdir(parents=True,exist_ok=True)
 train=v332.load_all();train['date']=[f'{c[:4]}-{c[4:6]}-{c[6:8]}' for c in train.race_code.astype(str).str.zfill(12)];train.to_csv(a.out/'v351_exhibition_train.csv',index=False);n=0
 for code,m in pm.items():
  if code not in hm.index or code not in p2 or code not in pc or code not in base_p2 or code not in base_pc: continue
  mass=v300.base5(base_p2[code],base_pc[code])[1];probs=v299.pair_prob(p2[code],pc[code],prod.TICKET_ALPHA);top=v299.STRATEGIES['HYBRID'](p2[code],pc[code],probs)[:3];hp=float(hm.loc[code,'p_head'])
  operating_pre_class='WATCH_PRE' if hp>=prod.WATCH_HEAD_CUTOFF and float(mass)>=prod.WATCH_OPPONENT_MASS_MIN else ('BASIC_PRE' if hp>=prod.LIVE_HEAD_CUTOFF and float(mass)>=prod.LIVE_OPPONENT_MASS_MIN else 'NON_CANDIDATE')
  obj={'race_code':code,'pre_class':m.get('pre_class','NON_CANDIDATE'),'operating_pre_class':operating_pre_class,'legacy_pre_p':float(m['legacy_pre_p']) if m.get('legacy_pre_p') not in (None,'') else hp,'final_head_p':hp,'opp_mass':float(mass),'p2':{str(k):float(v) for k,v in p2[code].items()},'pc':{f'{s}-{t}':float(v) for (s,t),v in pc[code].items()},'base_tickets':';'.join(f'1-{s}-{t}' for s,t in top),'production_profile':prod.PROFILE_NAME,'live_operation_profile':prod.LIVE_OPERATION_PROFILE_NAME,'training_cutoff':(target-pd.Timedelta(days=1)).isoformat(),'result_or_payout_used':False,'chronology_guard':True,'base_source':'ON_DEMAND_CAUSAL' if wanted else 'DAILY_ALL_RACE_CACHE'};(a.out/f'{code}.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2));n+=1
 if wanted and n!=1: raise RuntimeError(f'on-demand causal base could not be generated for {wanted}')
 meta={'date':a.date,'all_race_cache_R':n,'requested_race_code':wanted or None,'training_cutoff':(target-pd.Timedelta(days=1)).isoformat(),'production_profile':prod.PROFILE_NAME,'live_operation_profile':prod.LIVE_OPERATION_PROFILE_NAME,'result_or_payout_used':False,'chronology_guard':True};(a.out/'meta.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta))
if __name__=='__main__':main()
