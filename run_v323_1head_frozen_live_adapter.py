#!/usr/bin/env python3
"""v323: result-blind LIVE adapter for the frozen 1-head stack.

Frozen semantics
----------------
HEAD   : v308 absolute development q=.98 p_head cutoff + opponent mass >= .375.
SECOND : v317 OUTER_L2_1 with START family dropped.
THIRD  : v318 DROPSTART_T0.1.
TICKETS: v320 HYBRID alpha=.70, exactly three 1-x-y tickets.
ODDS   : official BOAT RACE odds3t only; 120-combination snapshot required.

Default behavior remains the historical frozen adapter.  LIVE rolling callers may
explicitly provide chronology-audited September history through allow_rolling_history;
the target row itself remains inference-only and meet_* stays forbidden.
"""
from __future__ import annotations
import argparse,csv,math
from datetime import date
from pathlib import Path
import numpy as np,pandas as pd
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v303_1head_headmodel_transfer_ablation as v303
import run_v305_1head_leakage_audit as v305
import run_v307_1head_causal_turn_form as v307
import run_v310_1head_opponent_headrisk_second as v310
import run_v311_1head_opponent_second_family_autoresearch as v311
import run_v312_1head_opponent_outer_gate as v312
import run_v317_1head_opponent_error_features as v317
import run_v318_1head_opponent_third_rebuild as v318
import run_v299_1head_trifecta3_policy_search as v299
import run_v321_1head_julaug_nonpristine_validation as v321
import fetch_live_trifecta_odds as liveodds
ROOT=Path(__file__).resolve().parent;DEV_PRED=ROOT/'analysis_v308_1head_volume_opponent_joint_pred.csv';FROZEN_V320=ROOT/'analysis_v320_1head_exact3_ticket_policy_best_race.csv';PREP_HEAD=ROOT/'cache_v321_julaug_nonpristine_head_full.csv.gz';PREP_SLIM=ROOT/'cache_v321_julaug_nonpristine_slim.csv.gz';Q=.98;OPP_MASS_CUT=.375;POLICY='HYBRID';ALPHA=.70;TARGET_MONTH='2026-09';META_HEAD={'date','month','race_code','venue','race','head_hit','actual_combo'}
def norm_code(x):
 s=str(x or '').strip();s=s[:-2] if s.endswith('.0') and s[:-2].isdigit() else s;return s.zfill(12) if s.isdigit() else ''
def load_cards(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def assert_frozen_regression():
 d=pd.read_csv(FROZEN_V320,dtype={'race_code':str});hh=int(pd.to_numeric(d.head_hit,errors='coerce').sum());hit=int(pd.to_numeric(d.hit,errors='coerce').sum())
 if len(d)!=345 or hh!=290 or hit!=139:raise RuntimeError(f'v323 regression drift {len(d)}/{hh}/{hit}')
 if set(d.strategy.astype(str))!={POLICY} or not np.allclose(pd.to_numeric(d.alpha,errors='coerce'),ALPHA):raise RuntimeError('v323 policy drift')
 return {'R':len(d),'head_hits':hh,'exact3_hits':hit}
def frozen_hcut():
 d=pd.read_csv(DEV_PRED,dtype={'race_code':str});bad=[m for m in d.test_month.astype(str).unique() if str(m).startswith(('2026-07','2026-08','2026-09'))]
 if bad:raise RuntimeError(f'forbidden DEV months {bad}')
 return float(pd.to_numeric(d.p_head,errors='coerce').dropna().quantile(Q))
def current_static(cards,target):
 out=[]
 for card in cards:
  code=norm_code(card.get('レースコード',''))
  if not code:continue
  if code[:8]!=target.strftime('%Y%m%d'):raise RuntimeError('current card date mismatch')
  q={'date':target.isoformat(),'month':target.strftime('%Y-%m'),'race_code':code,'venue':str(card.get('レース場コード','') or code[8:10]).zfill(2),'race':int(code[10:12])}
  for b in range(1,7):
   for k,v in v298.v294.raw_parts(card,b).items():q[f'b{b}_{k}']=v
  out.append(q)
 if not out:raise RuntimeError('no usable current cards')
 return pd.DataFrame(out).drop_duplicates('race_code')
def build_current_features(cur0):
 d=v298.v294.add_rel(cur0.copy());d,threat=v298.add_threat(d);d,tf=v303.add_transfer_features(d);d,causal=v307.add_causal(d);safe=list(dict.fromkeys(v305.safe_transfer(tf['TURN_FORM'])+v305.safe_transfer(tf['STMOTOR'])+causal))
 if any('meet_' in str(c).lower() for c in safe):raise RuntimeError('unsafe meet current feature')
 return d,threat,safe
def _audit_history(hd,target_month,allow):
 mons=hd.month.astype(str);bad=mons[mons>=target_month].unique().tolist()
 if bad:raise RuntimeError(f'target/future history leak {bad}')
 if not allow and any(str(m).startswith('2026-09') for m in mons.unique()):raise RuntimeError('September history requires explicit rolling audit')
def head_score(cur_feat,hcut,history_path=None,allow_rolling_history=False):
 hd=pd.read_csv(history_path or PREP_HEAD,dtype={'race_code':str});hd.race_code=hd.race_code.astype(str).str.zfill(12);target_month=str(cur_feat.month.iloc[0]);_audit_history(hd,target_month,allow_rolling_history)
 safe_static=set(v298.v296.SAFE);core=[]
 for c in hd.columns:
  s=str(c)
  if s in META_HEAD:continue
  if s.startswith('v298_') or '_pl_' in s or s.startswith('rel_pl_') or any(s.startswith(f'b{b}_{k}') for b in range(1,7) for k in safe_static) or any(s.startswith(f'rel_{k}_') for k in safe_static) or any(s==f'attack23_{k}' for k in safe_static):core.append(c)
 core=list(dict.fromkeys(core));extras=[c for c in hd.columns if c not in META_HEAD and c not in core and 'meet_' not in str(c).lower()];guard=[c for c in core if str(c).startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]
 cur=cur_feat.copy()
 for c in hd.columns:
  if c not in cur:cur[c]=np.nan
 cur['head_hit']=0;cur['actual_combo']='';tr=hd.copy();te=cur.copy();bc=v298.v293.available(tr,core,.55);bg=v298.v293.available(tr,guard,.55);ex=v303.available(tr,extras);ph,*_=v298.head_fold(tr,te,list(dict.fromkeys(bc+ex)),bg);z=te[['date','month','race_code','venue','race']].copy();z['p_head']=ph;z['hcut']=hcut;return z
def opponent_score(cur_feat,head,history_path=None,allow_rolling_history=False):
 slim=pd.read_csv(history_path or PREP_SLIM,dtype={'race_code':str});slim.race_code=slim.race_code.astype(str).str.zfill(12);target_month=str(cur_feat.month.iloc[0]);_audit_history(slim,target_month,allow_rolling_history);v300.setup_v298();sufs=v298.suffixes(slim)
 if any('meet_' in str(x).lower() for x in sufs):raise RuntimeError('forbidden meet suffix')
 cur=cur_feat.copy();cur['head_hit']=0;cur['actual_combo']=''
 for c in slim.columns:
  if c not in cur:cur[c]=np.nan
 cur=cur[list(slim.columns)];full=pd.concat([slim,cur],ignore_index=True);sl=v300.augment_second(v298.second_long(full,sufs));base_p2,_=v300.p2_predict(sl,target_month,10.,False);_,p3,p4=v312.load_cache();sl_hr=v310.add_headrisk(sl,p3,p4);sx,_=v317.add_engineered(sl_hr,'OUTER');p2,_=v311.p2_predict_explicit(sx,target_month,1.,None,{'START'});cl=v300.augment_third(v321._third_fold_long(full,sufs,target_month));base_pc,_=v300.pc_predict(cl,target_month,.3,False);pc,_=v318.pc_predict(cl,target_month,.1,'DROP_START');masses={c:v300.base5(base_p2[c],base_pc[c])[1] for c in cur.race_code.astype(str)};out=head.copy();out['opp_mass']=[masses.get(str(x).zfill(12),np.nan) for x in out.race_code];out['selected']=((out.p_head>=out.hcut)&(out.opp_mass>=OPP_MASS_CUT)).astype(int);fn=v299.STRATEGIES[POLICY];ticket_map={}
 for code in out.loc[out.selected==1,'race_code'].astype(str):
  probs=v299.pair_prob(p2[code],pc[code],ALPHA);top3=fn(p2[code],pc[code],probs)[:3];ticket_map[code]=[f'1-{s}-{t}' for s,t in top3]
 out['tickets']=[';'.join(ticket_map.get(str(c),[])) for c in out.race_code];return out,ticket_map
def composite(vals):return 1./sum(1./x for x in vals)
def attach_live_odds(out,ticket_map,target):
 z=out.copy();z['bet_status']='SKIP_NOT_SELECTED';return z
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--date',required=True);ap.add_argument('--cards',required=True,type=Path);ap.add_argument('--out',default='v323_live',type=Path);ap.add_argument('--skip-odds',action='store_true');args=ap.parse_args();target=date.fromisoformat(args.date)
 if target.strftime('%Y-%m')!=TARGET_MONTH:raise RuntimeError('v323 target month mismatch')
 reg=assert_frozen_regression();hcut=frozen_hcut();cur0=current_static(load_cards(args.cards),target);cur_feat,_,_=build_current_features(cur0);head=head_score(cur_feat,hcut);scored,ticket_map=opponent_score(cur_feat,head);scored['policy']=POLICY;scored['alpha']=ALPHA;scored['opp_mass_cut']=OPP_MASS_CUT;args.out.mkdir(parents=True,exist_ok=True);p=args.out/f'v323_1head_live_{target:%Y%m%d}.csv';scored.to_csv(p,index=False);print(f'v323 regression={reg} wrote {p}');return 0
if __name__=='__main__':raise SystemExit(main())
