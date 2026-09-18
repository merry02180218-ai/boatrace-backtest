#!/usr/bin/env python3
from __future__ import annotations
"""v368: robustness audit around v367 joint exact3 hit-push core."""
from pathlib import Path
import argparse,json,pickle
import numpy as np
import pandas as pd

import run_v365_1head_exact3_hit_push as v365
import run_v367_1head_joint_rerank_fourth as v367

OUT=Path('/tmp/v368-joint-robustness');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')

C_SCORE=(.35,.40,.45,.50)
C_RISK=(.15,.20,.25)
C_MASS=(.375,.40,.425)
C_G2=(.125,.25,.375)
C_G3=(.125,.25,.375)
F_GAP=(.075,.09,.10,.11,.125)
F_PAIR=(.07,.075,.08)
F_P2=(.30,.35,.40)

CORE_C23={'basis':'SCORE','score_min':.40,'risk_min':.20,'mass_min':.40,'g2':.25,'g3':.25}
CORE_F4={'gap_max':.10,'pair_min':.075,'p2_min':.35}

def formal_frame(rows,payouts):
    rec=[]
    for r in rows:
        p2,pc=v365.formal_post_five6(r)
        top=v367.tickets(p2,pc)
        ts=['1-%d-%d'%x for x in top]
        actual=str(r['actual_combo'])
        rec.append({'race_code':str(r['race_code']).zfill(12),'month':str(r['month']),
                    'formal_hit':int(actual in ts),'payout100':int(payouts[str(r['race_code']).zfill(12)])})
    return pd.DataFrame(rec)

def metrics(df,final_hit,expanded):
    final_hit=np.asarray(final_hit,dtype=bool);expanded=np.asarray(expanded,dtype=bool)
    stake=len(df)*300+int(expanded.sum())*100
    ret=int(df.loc[final_hit,'payout100'].sum())
    fh=df.formal_hit.to_numpy()
    delta=final_hit.astype(int)-fh
    return {
      'R':len(df),'hits':int(final_hit.sum()),'hit_rate':float(final_hit.mean()),
      'gain_R':int((delta==1).sum()),'loss_R':int((delta==-1).sum()),
      'expanded_R':int(expanded.sum()),'stake_yen':stake,'return_yen':ret,
      'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0,
    }

def eval_cfg(rows,payouts,c23,f4):
    base=pd.DataFrame([v367.row_after_c23(r,c23) for r in rows])
    ff=formal_frame(rows,payouts)
    d=base.merge(ff,on=['race_code','month'],validate='one_to_one')
    m=v367.fourth_mask(base,f4)
    hit=base.base_hit.astype(bool).to_numpy()|(m&base.extra_hit.astype(bool).to_numpy())
    return d,metrics(d,hit,m)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);args=ap.parse_args()
    x=pickle.load(args.prepared.open('rb'));rows=x['rows']['LIVE165']
    v367.install_payout_cache(rows);payouts=v367.payouts_for(rows)
    formal=formal_frame(rows,payouts)
    fm=metrics(formal,formal.formal_hit.astype(bool).to_numpy(),np.zeros(len(formal),dtype=bool))
    if (fm['R'],fm['hits'],fm['return_yen'])!=(165,87,63700):raise RuntimeError(f'formal drift {fm}')

    core_df,core=eval_cfg(rows,payouts,CORE_C23,CORE_F4)
    if (core['hits'],core['return_yen'],core['stake_yen'])!=(94,70700,57400):
        raise RuntimeError(f'v367 core drift {core}')

    devrows=[r for r in rows if str(r['month']) in DEV]
    suprows=[r for r in rows if str(r['month']) in SUP]
    _,core_dev=eval_cfg(devrows,payouts,CORE_C23,CORE_F4)
    _,core_sup=eval_cfg(suprows,payouts,CORE_C23,CORE_F4)

    # Joint neighborhood on DEV only.
    rec=[]
    for smin in C_SCORE:
      for rmin in C_RISK:
       for mmin in C_MASS:
        for g2 in C_G2:
         for g3 in C_G3:
          c23={'basis':'SCORE','score_min':smin,'risk_min':rmin,'mass_min':mmin,'g2':g2,'g3':g3}
          base=pd.DataFrame([v367.row_after_c23(r,c23) for r in devrows])
          ff=formal_frame(devrows,payouts)
          d=base.merge(ff,on=['race_code','month'],validate='one_to_one')
          for gap in F_GAP:
           for pm in F_PAIR:
            for p2m in F_P2:
             f4={'gap_max':gap,'pair_min':pm,'p2_min':p2m}
             mask=v367.fourth_mask(base,f4)
             hit=base.base_hit.astype(bool).to_numpy()|(mask&base.extra_hit.astype(bool).to_numpy())
             mm=metrics(d,hit,mask)
             rec.append({**{f'c23_{k}':v for k,v in c23.items()},**{f'f4_{k}':v for k,v in f4.items()},**mm})
    ng=pd.DataFrame(rec)
    plateau=ng[(ng.hits.ge(core_dev['hits']-1))&(ng.roi.ge(1.20))&(ng.loss_R.eq(0))].copy()

    # Fixed-core LOMO/holdout-by-month, no reselection.
    lomo=[]
    for mon in DEV:
        rr=[r for r in rows if str(r['month'])==mon]
        _,mm=eval_cfg(rr,payouts,CORE_C23,CORE_F4)
        ff=formal_frame(rr,payouts)
        bm=metrics(ff,ff.formal_hit.astype(bool).to_numpy(),np.zeros(len(ff),dtype=bool))
        lomo.append({'month':mon,'formal_hits':bm['hits'],'core_hits':mm['hits'],
                     'delta_hits':mm['hits']-bm['hits'],'formal_roi':bm['roi'],'core_roi':mm['roi'],
                     'delta_roi_pp':100*(mm['roi']-bm['roi']),'gain_R':mm['gain_R'],'loss_R':mm['loss_R'],
                     'expanded_R':mm['expanded_R']})

    # Support monthly too.
    support_monthly=[]
    for mon in SUP:
        rr=[r for r in rows if str(r['month'])==mon]
        _,mm=eval_cfg(rr,payouts,CORE_C23,CORE_F4)
        ff=formal_frame(rr,payouts);bm=metrics(ff,ff.formal_hit.astype(bool).to_numpy(),np.zeros(len(ff),dtype=bool))
        support_monthly.append({'month':mon,'formal_hits':bm['hits'],'core_hits':mm['hits'],
                                'delta_hits':mm['hits']-bm['hits'],'formal_roi':bm['roi'],'core_roi':mm['roi'],
                                'gain_R':mm['gain_R'],'loss_R':mm['loss_R'],'expanded_R':mm['expanded_R']})

    result={
      'formal_live165':fm,'v367_core':core,'core_dev':core_dev,'core_support':core_sup,
      'neighborhood_cells':len(ng),'plateau_cells':len(plateau),
      'plateau_ranges':({k:[float(plateau[k].min()),float(plateau[k].max())] for k in
          ['c23_score_min','c23_risk_min','c23_mass_min','c23_g2','c23_g3','f4_gap_max','f4_pair_min','f4_p2_min']}
          if len(plateau) else {}),
      'neighborhood_nonnegative_hit_share':float((ng.hits>=87).mean()),
      'neighborhood_zero_loss_share':float((ng.loss_R==0).mean()),
      'lomo_fixed_core':lomo,'support_monthly':support_monthly,
      'lomo_all_nonnegative_hits':bool(all(x['delta_hits']>=0 for x in lomo)),
      'lomo_total_delta_hits':int(sum(x['delta_hits'] for x in lomo)),
      'support_all_nonnegative_hits':bool(all(x['delta_hits']>=0 for x in support_monthly)),
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    ng.to_csv(OUT/'neighborhood.csv',index=False);plateau.to_csv(OUT/'plateau.csv',index=False)
    pd.DataFrame(lomo).to_csv(OUT/'lomo.csv',index=False);pd.DataFrame(support_monthly).to_csv(OUT/'support_monthly.csv',index=False)
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
