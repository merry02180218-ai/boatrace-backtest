#!/usr/bin/env python3
from __future__ import annotations
"""v355: keep all BASIC races, apply wall3 ticket rerank only to WATCH subset."""
from pathlib import Path
import argparse, json, hashlib
import numpy as np
import pandas as pd
import run_v351_1head_third_close_margin_audit as pay

OUT=Path('/tmp/v355-watch-wall3-overlay'); OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
CFG={'risk_kind':'SCORE','attack4_min':.6,'g2':3.0,'g3':.5}

def sha(lines): return hashlib.sha256('\n'.join(lines).encode()).hexdigest()

def met(z,cache):
    ret=0
    for _,r in z.iterrows():
        code=str(r.race_code).zfill(12)
        if code[:8]>='20260901': raise RuntimeError(f'September entered v355: {code}')
        _,p=pay._payout(code,str(r.actual_combo),cache)
        if int(r.hit): ret+=p
    stake=len(z)*300
    return {'R':len(z),'head':int(z.head_hit.sum()),'exact3':int(z.hit.sum()),
            'stake_yen':stake,'return_yen':ret,'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--race-predictions',required=True); args=ap.parse_args()
    d=pd.read_csv(args.race_predictions,dtype={'race_code':str})
    d.race_code=d.race_code.astype(str).str.zfill(12)
    if any(d.month.astype(str).str.startswith('2026-09')): raise RuntimeError('September outcomes present')
    basic=d[(d.universe=='BASIC')&(d.risk_kind=='BASE')].copy()
    watch=d[(d.universe=='WATCH')&(d.risk_kind==CFG['risk_kind'])&
            np.isclose(d.attack4_min,CFG['attack4_min'])&np.isclose(d.g2,CFG['g2'])&np.isclose(d.g3,CFG['g3'])].copy()
    if (len(basic),int(basic.hit.sum()))!=(165,80): raise RuntimeError('BASIC baseline drift')
    if (len(watch),int(watch.hit.sum()))!=(77,47): raise RuntimeError('WATCH candidate drift')
    if not set(watch.race_code).issubset(set(basic.race_code)): raise RuntimeError('WATCH not subset of BASIC')
    w=watch[['race_code','tickets','hit','changed','risk']].rename(columns={'tickets':'overlay_tickets','hit':'overlay_hit'})
    z=basic.merge(w,on='race_code',how='left',validate='one_to_one')
    z['final_tickets']=z.overlay_tickets.where(z.overlay_tickets.notna(),z.tickets)
    z['final_hit']=z.overlay_hit.where(z.overlay_hit.notna(),z.hit).astype(int)
    z['watch_overlay']=z.overlay_tickets.notna().astype(int)
    z['ticket_changed']=(z.final_tickets!=z.tickets).astype(int)
    base=basic.copy(); final=z[['month','race_code','head_hit','actual_combo','final_tickets','final_hit']].rename(columns={'final_tickets':'tickets','final_hit':'hit'})
    cache={}
    rows=[]; monthly=[]
    for name,df in [('BASE',base),('WATCH_WALL3_OVERLAY',final)]:
        a=met(df,cache); dv=met(df[df.month.isin(DEV)],cache); sp=met(df[df.month.isin(SUP)],cache)
        rows.append({'policy':name,**{f'all_{k}':v for k,v in a.items()},**{f'dev_{k}':v for k,v in dv.items()},**{f'support_{k}':v for k,v in sp.items()}})
        for mon,g in df.groupby('month'):
            monthly.append({'policy':name,'month':mon,**met(g,cache)})
    sm=pd.DataFrame(rows); mo=pd.DataFrame(monthly)
    comp=basic[['race_code','month','actual_combo','tickets','hit']].rename(columns={'tickets':'base_tickets','hit':'base_hit'}).merge(
        z[['race_code','final_tickets','final_hit','watch_overlay','ticket_changed']],on='race_code',validate='one_to_one')
    comp['delta']=comp.final_hit-comp.base_hit
    result={'config':CFG,'baseline':rows[0],'overlay':rows[1],
            'race_sha':sha(sorted(final.race_code.tolist())),
            'changed_R':int(comp.ticket_changed.sum()),'gain_R':int((comp.delta==1).sum()),'loss_R':int((comp.delta==-1).sum()),
            'watch_overlay_R':int(comp.watch_overlay.sum()),'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    sm.to_csv(OUT/'summary.csv',index=False);mo.to_csv(OUT/'monthly.csv',index=False);comp.to_csv(OUT/'paired.csv',index=False)
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
