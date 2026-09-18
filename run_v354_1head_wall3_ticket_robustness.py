#!/usr/bin/env python3
from __future__ import annotations
"""v354: robustness audit for WATCH wall3-aware 3-ticket rerank.

Consumes v353 race_predictions.csv only.  No model retraining.  Historical
payouts are joined only for 2026-02..08; >=2026-09 is hard-rejected.
"""
from pathlib import Path
import argparse, json, math
import numpy as np
import pandas as pd
import run_v351_1head_third_close_margin_audit as pay

OUT=Path('/tmp/v354-wall3-ticket-robustness'); OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
G2=(1.5,2.0,3.0); G3=(0.0,.5,1.0)
A4=.60; KIND='SCORE'


def metric(z, cache):
    ret=0
    for _,r in z.iterrows():
        code=str(r.race_code).zfill(12)
        if code[:8]>='20260901': raise RuntimeError(f'September entered v354: {code}')
        _,p=pay._payout(code,str(r.actual_combo),cache)
        if int(r.hit): ret+=p
    stake=len(z)*300
    return {'R':len(z),'hits':int(z.hit.sum()),'stake_yen':stake,'return_yen':ret,
            'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0}


def key_row(r):
    return f"{r.risk_kind}|a4={float(r.attack4_min):.1f}|g2={float(r.g2):.1f}|g3={float(r.g3):.1f}"


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--race-predictions',required=True); args=ap.parse_args()
    d=pd.read_csv(args.race_predictions,dtype={'race_code':str})
    d.race_code=d.race_code.astype(str).str.zfill(12)
    if any(d.month.astype(str).str.startswith('2026-09')): raise RuntimeError('September outcomes present')
    d=d[d.universe.eq('WATCH')].copy()
    base=d[d.risk_kind.eq('BASE')].copy()
    if len(base)!=77 or int(base.hit.sum())!=44: raise RuntimeError(f'WATCH base drift R={len(base)} hits={int(base.hit.sum())}')
    cand=d[(d.risk_kind.eq(KIND))&np.isclose(d.attack4_min,A4)&d.g2.isin(G2)&d.g3.isin(G3)].copy()
    configs=cand[['risk_kind','attack4_min','g2','g3']].drop_duplicates().sort_values(['g2','g3'])
    if len(configs)!=9: raise RuntimeError(f'expected 9 configs got {len(configs)}')
    cache={}; summaries=[]; monthly=[]; paired=[]
    bmap=base[['race_code','month','actual_combo','tickets','hit']].rename(columns={'tickets':'base_tickets','hit':'base_hit'})
    for _,cfg in configs.iterrows():
        z=cand[np.isclose(cand.g2,float(cfg.g2))&np.isclose(cand.g3,float(cfg.g3))].copy()
        name=key_row(cfg)
        mm=bmap.merge(z[['race_code','tickets','hit','changed','risk']].rename(columns={'tickets':'wall_tickets','hit':'wall_hit'}),on='race_code',validate='one_to_one')
        mm['delta']=mm.wall_hit-mm.base_hit
        mm['config']=name
        paired.append(mm)
        allm=metric(z,cache); dev=metric(z[z.month.isin(DEV)],cache); sup=metric(z[z.month.isin(SUP)],cache)
        rows={'config':name,'g2':float(cfg.g2),'g3':float(cfg.g3),
              **{f'all_{k}':v for k,v in allm.items()},**{f'dev_{k}':v for k,v in dev.items()},**{f'support_{k}':v for k,v in sup.items()},
              'changed_R':int(mm.changed.sum()),'gain_R':int((mm.delta==1).sum()),'loss_R':int((mm.delta==-1).sum())}
        dev_rois=[]; dev_dhits=[]; sup_rois=[]; sup_dhits=[]
        for mon in DEV+SUP:
            cm=metric(z[z.month.eq(mon)],cache); bm=metric(base[base.month.eq(mon)],cache)
            monthly.append({'config':name,'g2':float(cfg.g2),'g3':float(cfg.g3),'month':mon,**cm,
                            'base_hits':bm['hits'],'base_roi':bm['roi'],'delta_hits':cm['hits']-bm['hits'],'delta_roi_pp':100*(cm['roi']-bm['roi'])})
            if mon in DEV: dev_rois.append(cm['roi']); dev_dhits.append(cm['hits']-bm['hits'])
            else: sup_rois.append(cm['roi']); sup_dhits.append(cm['hits']-bm['hits'])
        rows['dev_min_month_roi']=min(dev_rois); rows['dev_nonnegative_hit_months']=sum(x>=0 for x in dev_dhits)
        rows['support_min_month_roi']=min(sup_rois); rows['support_nonnegative_hit_months']=sum(x>=0 for x in sup_dhits)
        summaries.append(rows)
    sm=pd.DataFrame(summaries); mo=pd.DataFrame(monthly); pp=pd.concat(paired,ignore_index=True)
    # Baseline monthly table.
    bmonthly=[]
    for mon in DEV+SUP:
        bm=metric(base[base.month.eq(mon)],cache); bmonthly.append({'month':mon,**bm})
    bmonthly=pd.DataFrame(bmonthly)
    # Fixed candidate chosen on all development only; Jul-Aug never participates in choice.
    pick=sm.sort_values(['dev_hits','dev_roi','dev_min_month_roi','changed_R'],ascending=[False,False,False,True]).iloc[0]
    # Leave-one-dev-month-out selection using the other 4 dev months.
    nested=[]
    for hold in DEV:
        train=[m for m in DEV if m!=hold]; scored=[]
        for _,cfg in configs.iterrows():
            name=key_row(cfg)
            z=cand[np.isclose(cand.g2,float(cfg.g2))&np.isclose(cand.g3,float(cfg.g3))].copy()
            tr=metric(z[z.month.isin(train)],cache); scored.append((tr['hits'],tr['roi'],-int(z.changed.sum()),name,float(cfg.g2),float(cfg.g3)))
        _,_,_,name,g2,g3=max(scored)
        z=cand[np.isclose(cand.g2,g2)&np.isclose(cand.g3,g3)].copy()
        hm=metric(z[z.month.eq(hold)],cache); hb=metric(base[base.month.eq(hold)],cache)
        nested.append({'holdout_month':hold,'selected_config':name,'g2':g2,'g3':g3,
                       **hm,'base_hits':hb['hits'],'base_roi':hb['roi'],'delta_hits':hm['hits']-hb['hits'],'delta_roi_pp':100*(hm['roi']-hb['roi'])})
    nested=pd.DataFrame(nested)
    sm.to_csv(OUT/'summary.csv',index=False); mo.to_csv(OUT/'monthly.csv',index=False)
    pp.to_csv(OUT/'paired.csv',index=False); bmonthly.to_csv(OUT/'baseline_monthly.csv',index=False); nested.to_csv(OUT/'nested_lomo.csv',index=False)
    pz=paired[int(np.where(np.isclose(configs.g2,float(pick.g2))&np.isclose(configs.g3,float(pick.g3)))[0][0])]
    gain=pz[pz.delta.ne(0)].copy(); gain.to_csv(OUT/'picked_gain_loss.csv',index=False)
    result={'watch_base_all':metric(base,cache),'watch_base_dev':metric(base[base.month.isin(DEV)],cache),'watch_base_support':metric(base[base.month.isin(SUP)],cache),
            'fixed_dev_selected':pick.to_dict(),'nested_lomo_delta_hits_total':int(nested.delta_hits.sum()),
            'nested_lomo_nonnegative_months':int((nested.delta_hits>=0).sum()),'nested_lomo':nested.to_dict('records'),
            'official_fallback_codes':sorted(pay.OFFICIAL_FALLBACK_CODES),'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
