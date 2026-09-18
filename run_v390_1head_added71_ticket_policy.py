#!/usr/bin/env python3
from __future__ import annotations
"""v390: expansion-specific 3-ticket policy for the frozen 1HEAD added71 lane.

Race selection is frozen. LIVE165 tickets are untouched. Only the added71
opponent ordering is varied after the already-formal wall3+5>6 p2/pc reranks.
Policy selection uses Feb-Jun DEV only; Jul-Aug SUPPORT is evaluated after
freeze. September outcomes are forbidden.
"""
from pathlib import Path
import argparse,json,pickle
import pandas as pd

import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365

OUT=Path('/tmp/v390-added71-ticket-policy'); OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
ALPHAS=(.40,.50,.60,.70,.80,.90)
STRATEGIES=('HYBRID','JOINT','TOP2XTOP2','SECOND1X3','SECOND3X1')

def ticket_set(r,strategy,alpha):
    p2,pc=v365.formal_post_five6(r)
    pr=v299.pair_prob(p2,pc,float(alpha))
    order=v299.STRATEGIES[strategy](p2,pc,pr)
    top=order[:3]
    if len(top)!=3 or len(set(top))!=3: raise RuntimeError('invalid 3-ticket set')
    return ';'.join(f'1-{s}-{t}' for s,t in top)

def base_row(r,payout):
    return {'race_code':str(r['race_code']).zfill(12),'month':str(r['month']),
            'head_hit':int(r['head_hit']),'actual_combo':str(r['actual_combo']),
            'payout100':int(payout)}

def metric(z,hitcol='hit'):
    if len(z)==0:
        return {'R':0,'head':0,'head_rate':0.0,'hits':0,'exact3_rate':0.0,'stake':0,'return':0,'profit':0,'roi':0.0}
    ret=int(z.loc[z[hitcol].eq(1),'payout100'].sum()); st=len(z)*300
    return {'R':int(len(z)),'head':int(z.head_hit.sum()),'head_rate':float(z.head_hit.mean()),
            'hits':int(z[hitcol].sum()),'exact3_rate':float(z[hitcol].mean()),
            'stake':int(st),'return':ret,'profit':int(ret-st),'roi':float(ret/st)}

def add_policy_cols(df,rowmap,strategy,alpha):
    key=f'{strategy}_a{int(round(alpha*100)):02d}'
    tickets=[]
    for code in df.race_code:
        tickets.append(ticket_set(rowmap[code],strategy,alpha))
    df=df.copy()
    df['tickets']=tickets
    df['hit']=[int(a in t.split(';')) for a,t in zip(df.actual_combo,df.tickets)]
    return key,df

def monthly_metrics(df):
    out=[]
    for mo in DEV:
        m=metric(df[df.month.eq(mo)])
        out.append({'month':mo,**m})
    return out

def combine_metrics(live_base, extra):
    st=int(live_base['stake'])+int(extra['stake'])
    ret=int(live_base['return'])+int(extra['return'])
    return {'R':int(live_base['R'])+int(extra['R']),'stake':st,'return':ret,
            'profit':ret-st,'roi':ret/st if st else 0.0}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--prepared',required=True,type=Path)
    ap.add_argument('--v389-selected',required=False,type=Path,default=None)
    a=ap.parse_args()
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD: raise RuntimeError('September guard disabled')
    x=pickle.load(a.prepared.open('rb')); rr=x['rows']
    if len(rr['LIVE165'])!=165 or len(rr['H078_M375'])!=236: raise RuntimeError('universe drift')
    live_map={str(r['race_code']).zfill(12):r for r in rr['LIVE165']}
    broad={str(r['race_code']).zfill(12):r for r in rr['H078_M375']}
    added_map={c:r for c,r in broad.items() if c not in live_map}
    if len(added_map)!=71: raise RuntimeError(f'added band drift {len(added_map)}')
    union=list({**live_map,**added_map}.values())
    v365.install_payout_cache(union); payouts=v365.payouts_for(union)
    live=pd.DataFrame([base_row(r,payouts[c]) for c,r in live_map.items()])
    add=pd.DataFrame([base_row(r,payouts[c]) for c,r in added_map.items()])
    if any(add.race_code.str[:8].ge('20260901')): raise RuntimeError('September entered')

    # Frozen current formal baseline for LIVE165 and added71.
    _,live_formal=add_policy_cols(live,live_map,'HYBRID',prod.TICKET_ALPHA)
    _,add_formal=add_policy_cols(add,added_map,'HYBRID',prod.TICKET_ALPHA)
    live_base=metric(live_formal); add_base=metric(add_formal)
    if (live_base['R'],live_base['hits'],live_base['return'])!=(165,87,63700):
        raise RuntimeError(f'LIVE formal sentinel drift {live_base}')
    if (add_base['R'],add_base['hits'],add_base['return'])!=(71,33,21360):
        raise RuntimeError(f'added formal sentinel drift {add_base}')

    selected42=set()
    if a.v389_selected and a.v389_selected.exists():
        q=pd.read_csv(a.v389_selected,dtype={'race_code':str})
        selected42=set(q.race_code.str.zfill(12))
        if len(selected42)!=42: raise RuntimeError(f'v389 selected count drift {len(selected42)}')

    rows=[]; monthly=[]
    policy_frames={}
    for strategy in STRATEGIES:
        for alpha in ALPHAS:
            key,z=add_policy_cols(add,added_map,strategy,alpha)
            policy_frames[key]=z
            dev=z[z.month.isin(DEV)]; sup=z[z.month.isin(SUP)]
            ma,md,ms=metric(z),metric(dev),metric(sup)
            mm=monthly_metrics(dev)
            nonneg=sum(int(m['roi']>=1.0-1e-12) for m in mm if m['R']>0)
            active=sum(int(m['R']>0) for m in mm)
            worst=min((m['roi'] for m in mm if m['R']>0),default=0.0)
            for m in mm: monthly.append({'policy':key,**m})
            r={'policy':key,'strategy':strategy,'alpha':alpha,
               'all_R':ma['R'],'all_hits':ma['hits'],'all_exact3_rate':ma['exact3_rate'],'all_roi':ma['roi'],'all_profit':ma['profit'],
               'dev_R':md['R'],'dev_hits':md['hits'],'dev_exact3_rate':md['exact3_rate'],'dev_roi':md['roi'],'dev_profit':md['profit'],
               'dev_nonnegative_months':nonneg,'dev_active_months':active,'dev_worst_month_roi':worst,
               'support_R':ms['R'],'support_hits':ms['hits'],'support_exact3_rate':ms['exact3_rate'],'support_roi':ms['roi'],'support_profit':ms['profit'],
               **{f'combined_all_{k}':v for k,v in combine_metrics(live_base,ma).items()},
               **{f'combined_support_{k}':v for k,v in combine_metrics(metric(live_formal[live_formal.month.isin(SUP)]),ms).items()}}
            if selected42:
                sm=metric(z[z.race_code.isin(selected42)])
                r.update({f'v38942_{k}':v for k,v in sm.items()})
                r.update({f'combined_v38942_{k}':v for k,v in combine_metrics(live_base,sm).items()})
            rows.append(r)
    g=pd.DataFrame(rows)
    base_dev=metric(add_formal[add_formal.month.isin(DEV)])
    # DEV-only selection. Require no aggregate degradation vs current expansion formal.
    eligible=g[
      g.dev_exact3_rate.ge(base_dev['exact3_rate']-1e-12) &
      g.dev_roi.ge(base_dev['roi']-1e-12) &
      g.dev_nonnegative_months.ge(3)
    ].copy()
    if len(eligible):
        pick=eligible.sort_values(['dev_nonnegative_months','dev_worst_month_roi','dev_exact3_rate','dev_roi'],
                                  ascending=[False,False,False,False]).iloc[0]
        mode='DEV_ROBUST'
    else:
        pick=g.sort_values(['dev_nonnegative_months','dev_exact3_rate','dev_roi'],
                           ascending=[False,False,False]).iloc[0]
        mode='FALLBACK_DIAGNOSTIC'
    chosen=pick.to_dict()
    chosen['selection_mode']=mode
    chosen_key=str(pick.policy)
    policy_frames[chosen_key].to_csv(OUT/'chosen_added71_rows.csv',index=False)
    g.to_csv(OUT/'policy_grid.csv',index=False)
    pd.DataFrame(monthly).to_csv(OUT/'dev_monthly.csv',index=False)

    result={'prepared_source':'v360 Artifact 10539401122',
            'v389_selected_source':str(a.v389_selected) if a.v389_selected else None,
            'formal_baseline':{'live165':live_base,'added71':add_base,'added71_dev':base_dev,
                               'added71_support':metric(add_formal[add_formal.month.isin(SUP)])},
            'alphas':ALPHAS,'strategies':STRATEGIES,'grid_cells':len(g),
            'eligible_dev_robust_cells':int(len(eligible)),'dev_only_pick':chosen,
            'SELECTION_USED_SUPPORT_OUTCOMES':False,'RESULT_OR_PAYOUT_USED_AS_POLICY_INPUT':False,
            'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str),flush=True)
    cols=['policy','dev_hits','dev_exact3_rate','dev_roi','dev_nonnegative_months','dev_worst_month_roi',
          'support_hits','support_exact3_rate','support_roi','all_hits','all_roi','combined_all_R','combined_all_roi']
    if selected42: cols += ['v38942_hits','v38942_roi','combined_v38942_R','combined_v38942_roi']
    print('\nPOLICIES',flush=True)
    print(g.sort_values(['dev_nonnegative_months','dev_worst_month_roi','dev_exact3_rate','dev_roi'],
                        ascending=[False,False,False,False])[cols].to_string(index=False),flush=True)

if __name__=='__main__': main()
