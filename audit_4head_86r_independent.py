#!/usr/bin/env python3
"""Independent audit of the frozen HEAD4 research candidate. September blocked."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import analyze_4head_headrate_3ren_player_st as base
import analyze_4head_exhibition_original_trainonly as ex
OUT=Path('/tmp/head4_86r_audit'); OUT.mkdir(parents=True,exist_ok=True)
WIN=-0.0299361318939513; REN2=-7.080000000000001; PLAYER=.215605; ST=-0.6000000000000001; ORIG=-0.057777777777777706

def rebuild(start='2026-04-01',end='2026-08-31'):
 if str(end)>='2026-09-01': raise RuntimeError('September outcome access blocked')
 months=pd.period_range(start=start,end=end,freq='M').strftime('%Y-%m').tolist()
 z=base.settle_all(months=months).merge(base.build_motor_features(),on=['date','month','race_code'],how='left').merge(base.build_prior_features(),on=['date','month','race_code'],how='left')
 z['race_code']=z.race_code.astype(str).str.zfill(12); z['head4']=pd.to_numeric(z.actual_head4,errors='coerce').fillna(0).astype(int)
 e=ex.build_ex(set(z.race_code)); x=z.merge(e,on='race_code',how='left')
 x=x[(x.motor_win_diff_4v3>=WIN)&(x.motor_2ren_diff_4v3>=REN2)&(x.player4_all_win>=PLAYER)&(x.basic_complete==1)&(x.st4_adv_inside>=ST)&(x.orig_avg_available==1)&(x.orig4_adv_inside>=ORIG)].copy()
 x['date']=x.date.astype(str); x['month']=x.date.str[:7]; x=x[(x.date>=start)&(x.date<=end)].copy()
 if start=='2026-04-01' and end=='2026-08-31':
  tr=x[x.month.isin(['2026-04','2026-05','2026-06'])]; ho=x[x.month.isin(['2026-07','2026-08'])]
  assert (len(tr),int(tr.head4.sum()))==(86,35),(len(tr),int(tr.head4.sum())); assert (len(ho),int(ho.head4.sum()))==(78,35),(len(ho),int(ho.head4.sum()))
 print('HEAD4_FROZEN_INDEPENDENT_REPLAY_OK',start,end,len(x)); return x

def summarize_head(x):
 rows=[]
 for mon,g in x.groupby('month'): rows.append({'period':mon,'R':len(g),'head4':int(g.head4.sum()),'head4_rate_pct':100*g.head4.mean()})
 return pd.DataFrame(rows)
def main():
 x=rebuild(); hs=summarize_head(x); hs.to_csv(OUT/'head_monthly.csv',index=False); roi=[]
 for name,g in x.groupby('month'):
  roi.append({'period':name,'head_population_R':len(g),'roi_covered_R':0,'coverage_pct':0.0,'trifecta_hits':np.nan,'stake_yen':0,'payout_yen':np.nan,'roi_pct':np.nan,'status':'UNAVAILABLE_NO_VERIFIED_PREDEADLINE_V283_REPLAY_ODDS'})
 pd.DataFrame(roi).to_csv(OUT/'roi_summary.csv',index=False); (OUT/'meta.json').write_text(json.dumps({'candidate':'HEAD4_86R_ORIGAVG_RESEARCH','v96_used':False,'post_deadline_odds_used':False,'september':'UNREAD'},indent=2)+'\n'); print(hs.to_string(index=False)); print('SEPTEMBER_UNREAD')
if __name__=='__main__':main()
