#!/usr/bin/env python3
from __future__ import annotations
"""v351 HEAD x opponent-mass x exhibition joint ROI audit; research only."""
from pathlib import Path
import json,pandas as pd
import run_v337_1head_head_cutoff_volume as v337
import run_v346_1head_v345_production_regression as v346
import run_v347_1head_opponent_attackcore as v347
import run_v351_1head_production_regression as base
import run_v351_1head_third_close_margin_audit as pay
import onehead_production_profile as prod
import run_v332_1head_attack_first_redesign as v332
OUT=Path('/tmp/v351-joint-roi-grid');OUT.mkdir(parents=True,exist_ok=True)
HEAD=(.775,.7775,.780,.7825,.785,.7875,.790);MASS=(.350,.3625,.375,.3875,.400,.4125,.425);ENV_W=(.05,.10,.15);ENV_Q=(.60,.65,.70);MONTHS=tuple(v337.MONTHS)
def universe():
 oldo,oldc=v337.OPP,list(v337.CUTS)
 try:v337.OPP=min(MASS);v337.CUTS=[min(HEAD)];b=v337.load_candidate_base();y,_,_=v337.build_exhibition(b)
 finally:v337.OPP=oldo;v337.CUTS=oldc
 y.race_code=y.race_code.astype(str).str.zfill(12)
 if any(y.race_code.str.startswith('20260917')):raise RuntimeError('forbidden 20260917 race')
 return y
def select(y,h,m,w,q):
 z=y[pd.to_numeric(y.p_head,errors='coerce').ge(h)&pd.to_numeric(y.opp_mass,errors='coerce').ge(m)].copy();cfg={'family':'ATTACK_ENV_SOFT','env_w':w,'q':q};out=[]
 for mon in MONTHS:
  tr=z[z.month.isin(MONTHS[:-1])].copy() if mon=='2026-08' else z[z.month.isin([x for x in MONTHS[:-1] if x!=mon])].copy();te=z[z.month.eq(mon)].copy();p,_=v332.fit_apply(tr,te,cfg);out.append(p)
 return v346.apply_v345_attack_core(pd.concat(out,ignore_index=True))
def tickets(s,maps,cores):
 p2d,pcd,p2j,pcj=maps;rec=[]
 for _,r in s.iterrows():
  c=str(r.race_code).zfill(12);p2,pc=v347.get_dist(str(r.month),c,p2d,pcd,p2j,pcj);core=cores.get(c)
  if core is not None:p2=base._second_adjust(p2,core);pc=base._third_adjust(pc,core)
  ts=v347.tickets(p2,pc);a=str(r.actual_combo);rec.append({'month':str(r.month),'race_code':c,'head_hit':int(a.startswith('1-')),'actual_combo':a,'tickets':ts,'hit':int(a in ts.split(';'))})
 return pd.DataFrame(rec)
def met(z,cache):
 ret=0
 for _,r in z.iterrows():
  if str(r.race_code)[:8]>='20260917':raise RuntimeError('forbidden payout date')
  _,p=pay._payout(str(r.race_code),str(r.actual_combo),cache)
  if int(r.hit):ret+=p
 stake=len(z)*300;return {'R':len(z),'head':int(z.head_hit.sum()),'exact3':int(z.hit.sum()),'stake_yen':stake,'return_yen':ret,'profit_yen':ret-stake,'roi':ret/stake if stake else 0}
def main():
 if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:raise RuntimeError('September guard disabled')
 y=universe();maps=v347.opponent_maps();cores=v347.build_opponent_attackcore(set(y.race_code));cache={};rows=[];mons=[]
 for h in HEAD:
  for m in MASS:
   for w in ENV_W:
    for q in ENV_Q:
     z=tickets(select(y,h,m,w,q),maps,cores);rows.append({'head_cutoff':h,'opponent_mass_min':m,'env_w':w,'env_q':q,**met(z,cache)})
     for mon,g in z.groupby('month'):mons.append({'head_cutoff':h,'opponent_mass_min':m,'env_w':w,'env_q':q,'month':mon,**met(g,cache)})
 sm=pd.DataFrame(rows);mo=pd.DataFrame(mons);pr=sm[(sm.head_cutoff.eq(.78))&(sm.opponent_mass_min.eq(.375))&(sm.env_w.eq(.1))&(sm.env_q.eq(.65))]
 if len(pr)!=1:raise RuntimeError('production cell missing')
 p=pr.iloc[0]
 if (int(p.R),int(p.head),int(p.exact3))!=(276,241,131):raise RuntimeError(f'PRODUCTION_SENTINEL_DRIFT {p.to_dict()}')
 sm['head_rate']=sm.head/sm.R;sm['exact3_rate']=sm.exact3/sm.R;sm=sm.sort_values(['roi','profit_yen','R'],ascending=False);sm.to_csv(OUT/'summary.csv',index=False);mo.to_csv(OUT/'monthly.csv',index=False)
 result={'grid_cells':len(sm),'production_cell':pr.iloc[0].to_dict(),'best_raw_roi':sm.iloc[0].to_dict(),'official_fallback_codes':sorted(pay.OFFICIAL_FALLBACK_CODES),'TODAY_20260917_RESULT_OR_PAYOUT_USED':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True};(OUT/'result.json').write_text(json.dumps(result,indent=2,default=str));print(json.dumps(result,indent=2,default=str))
if __name__=='__main__':main()
