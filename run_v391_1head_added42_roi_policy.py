#!/usr/bin/env python3
from __future__ import annotations
"""v391: ROI-first 3-ticket policy inside frozen v389 added42 rescue lane.

Race selection is frozen to v389 CONSENSUS_MASS q=.35. No fourth ticket.
Policy selection uses only Feb-Jun DEV. Jul-Aug SUPPORT is untouched holdout.
"""
from pathlib import Path
import argparse,json,pickle
import pandas as pd

import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365

OUT=Path('/tmp/v391-added42-roi-policy'); OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
ALPHAS=(.40,.50,.60,.70,.80,.90)
STRATEGIES=('HYBRID','JOINT','TOP2XTOP2','SECOND1X3','SECOND3X1')

def tickets(r,strategy,alpha):
    p2,pc=v365.formal_post_five6(r)
    pr=v299.pair_prob(p2,pc,float(alpha))
    top=v299.STRATEGIES[strategy](p2,pc,pr)[:3]
    if len(top)!=3 or len(set(top))!=3: raise RuntimeError('bad tickets')
    return ';'.join(f'1-{s}-{t}' for s,t in top)

def metric(z):
    if len(z)==0:return {'R':0,'hits':0,'hit_rate':0.0,'stake':0,'return':0,'profit':0,'roi':0.0}
    ret=int(z.loc[z.hit.eq(1),'payout100'].sum()); st=len(z)*300
    return {'R':int(len(z)),'hits':int(z.hit.sum()),'hit_rate':float(z.hit.mean()),
            'stake':st,'return':ret,'profit':ret-st,'roi':ret/st}

def combine(a,b):
    st=a['stake']+b['stake']; ret=a['return']+b['return']
    return {'R':a['R']+b['R'],'stake':st,'return':ret,'profit':ret-st,'roi':ret/st if st else 0.0}

def frame(codes,rowmap,payouts,strategy,alpha):
    rec=[]
    for code in codes:
        r=rowmap[code]; ts=tickets(r,strategy,alpha); actual=str(r['actual_combo'])
        rec.append({'race_code':code,'month':str(r['month']),'actual_combo':actual,
                    'tickets':ts,'hit':int(actual in ts.split(';')),'payout100':int(payouts[code])})
    return pd.DataFrame(rec)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--prepared',required=True,type=Path)
    ap.add_argument('--selected',required=True,type=Path)
    a=ap.parse_args()
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD: raise RuntimeError('September guard disabled')
    x=pickle.load(a.prepared.open('rb')); rr=x['rows']
    live_map={str(r['race_code']).zfill(12):r for r in rr['LIVE165']}
    broad={str(r['race_code']).zfill(12):r for r in rr['H078_M375']}
    add_map={c:r for c,r in broad.items() if c not in live_map}
    sel=pd.read_csv(a.selected,dtype={'race_code':str}); codes=sel.race_code.str.zfill(12).tolist()
    if len(codes)!=42 or len(set(codes))!=42: raise RuntimeError(f'selected42 drift {len(codes)}')
    if not set(codes)<=set(add_map): raise RuntimeError('selected codes outside added71')
    union=list({**live_map,**add_map}.values())
    v365.install_payout_cache(union); payouts=v365.payouts_for(union)

    live=frame(list(live_map),live_map,payouts,'HYBRID',prod.TICKET_ALPHA)
    live_base=metric(live)
    if (live_base['R'],live_base['hits'],live_base['return'])!=(165,87,63700):
        raise RuntimeError(f'LIVE sentinel drift {live_base}')
    formal=frame(codes,add_map,payouts,'HYBRID',prod.TICKET_ALPHA)
    fb=metric(formal); fd=metric(formal[formal.month.isin(DEV)]); fs=metric(formal[formal.month.isin(SUP)])
    if (fb['R'],fb['hits'],fb['return'])!=(42,21,12850): raise RuntimeError(f'added42 sentinel drift {fb}')
    live_sup=metric(live[live.month.isin(SUP)])

    rows=[]; frames={}
    for strategy in STRATEGIES:
      for alpha in ALPHAS:
        key=f'{strategy}_a{int(round(alpha*100)):02d}'
        z=frame(codes,add_map,payouts,strategy,alpha); frames[key]=z
        d=z[z.month.isin(DEV)]; s=z[z.month.isin(SUP)]
        ma,md,ms=metric(z),metric(d),metric(s)
        month=[]
        for mo in DEV:
            mm=metric(d[d.month.eq(mo)]); month.append(mm)
        nonneg=sum(int(m['roi']>=1-1e-12) for m in month if m['R'])
        active=sum(int(m['R']>0) for m in month)
        worst=min((m['roi'] for m in month if m['R']),default=0.0)
        rows.append({'policy':key,'strategy':strategy,'alpha':alpha,
                     'all_hits':ma['hits'],'all_hit_rate':ma['hit_rate'],'all_roi':ma['roi'],'all_profit':ma['profit'],
                     'dev_hits':md['hits'],'dev_hit_rate':md['hit_rate'],'dev_roi':md['roi'],'dev_profit':md['profit'],
                     'dev_nonnegative_months':nonneg,'dev_active_months':active,'dev_worst_month_roi':worst,
                     'support_hits':ms['hits'],'support_hit_rate':ms['hit_rate'],'support_roi':ms['roi'],'support_profit':ms['profit'],
                     **{f'combined_{k}':v for k,v in combine(live_base,ma).items()},
                     **{f'combined_support_{k}':v for k,v in combine(live_sup,ms).items()}})
    g=pd.DataFrame(rows)

    # ROI-first but protect against a major exact3 collapse on only 34 DEV races.
    eligible=g[
      g.dev_hits.ge(fd['hits']-2) &
      g.dev_nonnegative_months.ge(3) &
      g.dev_roi.ge(fd['roi']-1e-12)
    ].copy()
    if len(eligible):
        pick=eligible.sort_values(['dev_nonnegative_months','dev_worst_month_roi','dev_roi','dev_hits'],
                                  ascending=[False,False,False,False]).iloc[0]
        mode='DEV_ROI_ROBUST'
    else:
        pick=g[g.dev_hits.ge(fd['hits']-2)].sort_values(
            ['dev_nonnegative_months','dev_roi','dev_hits'],ascending=[False,False,False]).iloc[0]
        mode='FALLBACK_DIAGNOSTIC'
    chosen=pick.to_dict(); chosen['selection_mode']=mode
    frames[str(pick.policy)].to_csv(OUT/'chosen_rows.csv',index=False)
    g.to_csv(OUT/'policy_grid.csv',index=False)

    result={'source_v389':'Artifact 10562248620 CONSENSUS_MASS q=.35',
            'selected42_formal':{'all':fb,'dev':fd,'support':fs},
            'live165_formal':live_base,'grid_cells':len(g),'eligible_cells':int(len(eligible)),
            'dev_only_pick':chosen,
            'SELECTION_USED_SUPPORT_OUTCOMES':False,'RESULT_OR_PAYOUT_USED_AS_POLICY_INPUT':False,
            'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str),flush=True)
    cols=['policy','dev_hits','dev_roi','dev_nonnegative_months','dev_worst_month_roi',
          'support_hits','support_roi','all_hits','all_roi','combined_R','combined_roi','combined_support_roi']
    print(g.sort_values(['dev_nonnegative_months','dev_worst_month_roi','dev_roi'],ascending=[False,False,False])[cols].to_string(index=False),flush=True)

if __name__=='__main__': main()
