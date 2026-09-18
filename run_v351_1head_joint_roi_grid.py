#!/usr/bin/env python3
from __future__ import annotations
"""v351 HEAD x opponent-mass x exhibition joint ROI audit; research only."""
from pathlib import Path
import hashlib,json
import pandas as pd
import run_v337_1head_head_cutoff_volume as v337
import run_v346_1head_v345_production_regression as v346
import run_v347_1head_opponent_attackcore as v347
import run_v351_1head_production_regression as base
import run_v351_1head_third_close_margin_audit as pay
import onehead_production_profile as prod
import run_v332_1head_attack_first_redesign as v332

OUT=Path('/tmp/v351-joint-roi-grid');OUT.mkdir(parents=True,exist_ok=True)
HEAD=(.775,.7775,.780,.7825,.785,.7875,.790)
MASS=(.350,.3625,.375,.3875,.400,.4125,.425)
ENV_W=(.05,.10,.15);ENV_Q=(.60,.65,.70);MONTHS=tuple(v337.MONTHS)

def sha(lines):
 return hashlib.sha256('\n'.join(lines).encode()).hexdigest()

def universe():
 # Widen only opponent mass. Keep the frozen v337 .75 head floor so the
 # production cell has exactly the same training universe as formal v351.
 oldo=v337.OPP
 try:
  v337.OPP=min(MASS);b=v337.load_candidate_base();y,_,_=v337.build_exhibition(b)
 finally:v337.OPP=oldo
 y.race_code=y.race_code.astype(str).str.zfill(12)
 if any(y.race_code.str[:8].ge('20260901')):raise RuntimeError('September entered joint grid')
 return y

def eval_cfg(y,h,w,q):
 # Exact v337.eval_cut chronology, with only the requested exhibition CFG varied.
 z=y[pd.to_numeric(y.p_head,errors='coerce').ge(h)].copy()
 cfg={'family':'ATTACK_ENV_SOFT','env_w':w,'q':q};out=[]
 for mon in MONTHS:
  tr=z[z.month.isin(MONTHS[:-1])].copy() if mon=='2026-08' else z[z.month.isin([x for x in MONTHS[:-1] if x!=mon])].copy()
  te=z[z.month.eq(mon)].copy();p,_=v332.fit_apply(tr,te,cfg);out.append(p)
 return pd.concat(out,ignore_index=True) if out else z.iloc[0:0].copy()

def tickets(s,maps,cores):
 p2d,pcd,p2j,pcj=maps;rec=[]
 for _,r in s.sort_values('race_code').iterrows():
  c=str(r.race_code).zfill(12);p2,pc=v347.get_dist(str(r.month),c,p2d,pcd,p2j,pcj);core=cores.get(c)
  if core is not None:p2=base._second_adjust(p2,core);pc=base._third_adjust(pc,core)
  ts=base._tickets(p2,pc);a=str(r.actual_combo);parts=a.split('-')
  rec.append({'month':str(r.month),'race_code':c,'head_hit':int(len(parts)==3 and parts[0]=='1'),'actual_combo':a,'tickets':ts,'hit':int(a in ts.split(';'))})
 return pd.DataFrame(rec)

def met(z,cache):
 ret=0
 for _,r in z.iterrows():
  if str(r.race_code)[:8]>='20260917':raise RuntimeError('forbidden payout date')
  _,p=pay._payout(str(r.race_code),str(r.actual_combo),cache)
  if int(r.hit):ret+=p
 stake=len(z)*300
 return {'R':len(z),'head':int(z.head_hit.sum()),'exact3':int(z.hit.sum()),'stake_yen':stake,'return_yen':ret,'profit_yen':ret-stake,'roi':ret/stake if stake else 0}

def main():
 if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:raise RuntimeError('September guard disabled')
 y=universe();maps=v347.opponent_maps();cores=v347.build_opponent_attackcore(set(y.race_code));cache={};rows=[];mons=[]
 # Formal order: mass universe -> v345 attackCore -> HEAD/env v332 filter -> v351 tickets.
 for m in MASS:
  ym=y[pd.to_numeric(y.opp_mass,errors='coerce').ge(m)].copy()
  ym=v346.apply_v345_attack_core(ym)
  for h in HEAD:
   for w in ENV_W:
    for q in ENV_Q:
     z=tickets(eval_cfg(ym,h,w,q),maps,cores);row={'head_cutoff':h,'opponent_mass_min':m,'env_w':w,'env_q':q,**met(z,cache)}
     if h==.78 and m==.375 and w==.10 and q==.65:
      row['race_sha']=sha(sorted(z.race_code.tolist()))
      row['ticket_sha']=sha((z.sort_values('race_code').race_code+':'+z.sort_values('race_code').tickets).tolist())
     rows.append(row)
     for mon,g in z.groupby('month'):mons.append({'head_cutoff':h,'opponent_mass_min':m,'env_w':w,'env_q':q,'month':mon,**met(g,cache)})
 sm=pd.DataFrame(rows);mo=pd.DataFrame(mons);pr=sm[(sm.head_cutoff.eq(.78))&(sm.opponent_mass_min.eq(.375))&(sm.env_w.eq(.1))&(sm.env_q.eq(.65))]
 if len(pr)!=1:raise RuntimeError('production cell missing')
 p=pr.iloc[0]
 got=(int(p['R']),int(p['head']),int(p['exact3']),str(p['race_sha']),str(p['ticket_sha']))
 exp=(prod.PRODUCTION_EXPECTED_PASS_R,prod.PRODUCTION_EXPECTED_HEAD,prod.PRODUCTION_EXPECTED_EXACT3,prod.PRODUCTION_EXPECTED_PASS_ID_SHA256,prod.PRODUCTION_EXPECTED_TICKET_ID_SHA256)
 if got!=exp:raise RuntimeError(f'PRODUCTION_SENTINEL_DRIFT got={got} expected={exp}')
 sm['head_rate']=sm['head']/sm['R'];sm['exact3_rate']=sm['exact3']/sm['R'];sm=sm.sort_values(['roi','profit_yen','R'],ascending=False)
 sm.to_csv(OUT/'summary.csv',index=False);mo.to_csv(OUT/'monthly.csv',index=False)
 result={'grid_cells':len(sm),'production_cell':pr.iloc[0].to_dict(),'best_raw_roi':sm.iloc[0].to_dict(),'official_fallback_codes':sorted(pay.OFFICIAL_FALLBACK_CODES),'TODAY_20260917_RESULT_OR_PAYOUT_USED':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
 (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str));print(json.dumps(result,indent=2,default=str))
if __name__=='__main__':main()
