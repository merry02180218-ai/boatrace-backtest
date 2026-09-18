#!/usr/bin/env python3
from __future__ import annotations
"""v373: translate closing-odds value gate to current/pre-close odds with market-only safety margins.

No parameter is selected from payout/return. Safety margin d is selected only from
pre-close -> closing odds transition behavior on v372 covered races.
"""
from pathlib import Path
import argparse,json,math
import numpy as np
import pandas as pd

OUT=Path('/tmp/v373-current-odds-safety');OUT.mkdir(parents=True,exist_ok=True)
CLOSE_C=2.25
CLOSE_E=1.10
EXTRA=3
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')

def comb(od):
    return 1.0/sum(1.0/float(x) for x in od)

def vals(r,cols):
    return [float(r.p1)*float(r[cols[0]]),float(r.p2)*float(r[cols[1]]),float(r.p3)*float(r[cols[2]])]

def gate(r,cols,c,e):
    od=[float(r[x]) for x in cols]
    return comb(od)>=c and max(vals(r,cols))>=e

def alloc(r,cols,extra=EXTRA):
    v=np.array(vals(r,cols),float)
    u=np.ones(3,dtype=int)
    if not np.isfinite(v).all() or v.sum()<=0:v=np.ones(3)
    target=extra*v/v.sum(); fl=np.floor(target).astype(int);u+=fl
    left=extra-int(fl.sum())
    for i in np.argsort(-(target-fl))[:left]:u[int(i)]+=1
    return tuple(int(x) for x in u)

def baseline(z):
    stake=len(z)*300
    ret=int(sum(int(r.payout100) for _,r in z.iterrows() if int(r.hit_rank)>0))
    return {'R':len(z),'stake_yen':stake,'return_yen':ret,'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0}

def evaluate(z,cols,c,e,extra=EXTRA):
    stake=ret=trig=0;rows=[]
    for _,r in z.iterrows():
        active=gate(r,cols,c,e)
        u=alloc(r,cols,extra) if active else (1,1,1)
        hr=int(r.hit_rank); rr=int(r.payout100)*u[hr-1] if hr>0 else 0
        stake+=sum(u)*100;ret+=rr;trig+=int(active)
        rows.append({'race_code':r.race_code,'active':int(active),'u1':u[0],'u2':u[1],'u3':u[2],
                     'hit_rank':hr,'return_yen':rr})
    return {'R':len(z),'trigger_R':trig,'stake_yen':stake,'return_yen':ret,
            'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0},pd.DataFrame(rows)

def safety_threshold(d):
    return CLOSE_C/(1.0-d),CLOSE_E/(1.0-d)

def ceil_step(x,step):
    return math.ceil((x-1e-12)/step)*step

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--joined',required=True,type=Path);a=ap.parse_args()
    z=pd.read_csv(a.joined,dtype={'race_code':str});z.race_code=z.race_code.str.zfill(12)
    if len(z)!=165:raise RuntimeError(f'R drift {len(z)}')
    if any(z.race_code.str[:8].ge('20260901')):raise RuntimeError('September entered')
    pc=z[z.pre_odds1.notna()].copy()
    if len(pc)!=21:raise RuntimeError(f'covered R drift {len(pc)}')
    close_cols=('odds1','odds2','odds3'); pre_cols=('pre_odds1','pre_odds2','pre_odds3')

    # Market-only transition table.
    trans=[]
    for _,r in pc.iterrows():
        co0=comb([r.pre_odds1,r.pre_odds2,r.pre_odds3]);co1=comb([r.odds1,r.odds2,r.odds3])
        cg=gate(r,close_cols,CLOSE_C,CLOSE_E)
        trans.append({'race_code':r.race_code,'month':r.month,'combined_pre':co0,'combined_close':co1,
                      'combined_rel_drift':co1/co0-1.0,'closing_trigger':int(cg),
                      'close_u':'-'.join(map(str,alloc(r,close_cols))) if cg else '1-1-1'})
    t=pd.DataFrame(trans)
    abs95=float(t.combined_rel_drift.abs().quantile(.95))
    p95_d=min(.90,ceil_step(abs95,.05))

    grid=[]
    for n in range(0,41):
        d=n/100.0;c,e=safety_threshold(d)
        pre_active=[];close_active=[];exact=[]
        for _,r in pc.iterrows():
            pa=gate(r,pre_cols,c,e);ca=gate(r,close_cols,CLOSE_C,CLOSE_E)
            pre_active.append(pa);close_active.append(ca)
            if pa:
                exact.append(bool(ca and alloc(r,pre_cols)==alloc(r,close_cols)))
        fp=sum(p and not c0 for p,c0 in zip(pre_active,close_active))
        tp=sum(p and c0 for p,c0 in zip(pre_active,close_active))
        fn=sum((not p) and c0 for p,c0 in zip(pre_active,close_active))
        exact_bad=sum(not x for x in exact)
        # payout evaluation is diagnostic only and is not used in selection.
        m,_=evaluate(pc,pre_cols,c,e)
        grid.append({'d':d,'combined_min':c,'value_min':e,'pre_trigger_R':sum(pre_active),
                     'closing_trigger_R':sum(close_active),'true_positive_R':tp,
                     'false_positive_R':fp,'false_negative_R':fn,'triggered_allocation_mismatch_R':exact_bad,
                     **{f'diag_{k}':v for k,v in m.items()}})
    g=pd.DataFrame(grid)
    elig=g[(g.pre_trigger_R.gt(0))&(g.false_positive_R.eq(0))&(g.triggered_allocation_mismatch_R.eq(0))]
    if len(elig)==0:raise RuntimeError('no market-only alignment margin')
    align_d=float(elig.sort_values('d').iloc[0].d)
    operational_d=ceil_step(align_d,.05)
    if abs(operational_d-.20)>1e-9:
        raise RuntimeError(f'expected rounded alignment margin .20, got {operational_d}')
    candidates={'ALIGN_MIN':align_d,'ALIGN_ROUND5':operational_d,'P95_ROUND5':p95_d}

    cand=[]
    for name,d in candidates.items():
        c,e=safety_threshold(d)
        pre_m,_=evaluate(pc,pre_cols,c,e)
        close_same,_=evaluate(pc,close_cols,c,e)
        full,_=evaluate(z,close_cols,c,e)
        dev,_=evaluate(z[z.month.isin(DEV)],close_cols,c,e)
        sup,_=evaluate(z[z.month.isin(SUP)],close_cols,c,e)
        cand.append({'name':name,'d':d,'combined_min':c,'value_min':e,
                     **{f'pre21_{k}':v for k,v in pre_m.items()},
                     **{f'close21_tight_{k}':v for k,v in close_same.items()},
                     **{f'full165_close_tight_{k}':v for k,v in full.items()},
                     'dev_close_tight_roi':dev['roi'],'support_close_tight_roi':sup['roi']})
    cand=pd.DataFrame(cand)

    # Same-21 reference comparisons.
    b21=baseline(pc)
    raw_pre,_=evaluate(pc,pre_cols,CLOSE_C,CLOSE_E)
    raw_close,_=evaluate(pc,close_cols,CLOSE_C,CLOSE_E)

    g.to_csv(OUT/'safety_margin_grid.csv',index=False)
    cand.to_csv(OUT/'market_only_candidates.csv',index=False)
    t.to_csv(OUT/'market_transition.csv',index=False)
    result={
      'covered_R':len(pc),
      'selection_uses_payout':False,
      'closing_gate':{'combined_min':CLOSE_C,'value_min':CLOSE_E,'extra_units':EXTRA},
      'combined_abs_rel_drift_p95':abs95,
      'market_only_align_min_d':align_d,
      'market_only_align_round5_d':operational_d,
      'market_only_p95_round5_d':p95_d,
      'same21_equal_baseline':b21,
      'same21_raw_closing_core':raw_close,
      'same21_raw_preclose_core':raw_pre,
      'candidates':cand.to_dict('records'),
      'recommended_research_shadow_d':operational_d,
      'recommended_research_shadow_combined_min':safety_threshold(operational_d)[0],
      'recommended_research_shadow_value_min':safety_threshold(operational_d)[1],
      'reason':'smallest market-only d with zero preclose false-positive closing triggers and exact triggered allocation, rounded upward to 5pct',
      'FORMAL_CHANGED':False,'SEPTEMBER_OUTCOMES_READ':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
