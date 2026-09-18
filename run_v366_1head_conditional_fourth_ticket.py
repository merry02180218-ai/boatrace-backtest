#!/usr/bin/env python3
from __future__ import annotations
"""v366: conditional 4th ticket after formal wall3 + 5->6, targeting higher exact3 hit rate.

Research only. Selection is Feb-Jun DEV. Jul-Aug SUPPORT is evaluation only.
Each base race always stakes 3x100 yen. A selected expansion adds exactly one
100-yen fourth ticket.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse, json, pickle, urllib.request
import numpy as np
import pandas as pd

import backtest
import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v351_1head_third_close_margin_audit as pay
import run_v365_1head_exact3_hit_push as v365

OUT=Path('/tmp/v366-conditional-fourth');OUT.mkdir(parents=True,exist_ok=True)
BOATS=(2,3,4,5,6)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
GAP=(.005,.01,.015,.02,.03,.05,.075,.10,.125,.15,.175,.20,.21,.25,.30)
PAIR_MIN=(0.,.06,.07,.075,.08,.085,.09,.095,.10,.105,.11)
PC_MIN=(0.,.10,.15,.18,.20,.22,.24)
P2_MIN=(0.,.30,.35,.40,.45,.50)

def install_payout_cache(rows):
    days=sorted({str(r['race_code'])[:8] for r in rows})
    paths=[f"data/results/payouts/{d[:4]}/{d[4:6]}/{d[6:8]}.csv" for d in days]
    original=backtest.fetch
    def one(path):
        try:
            with urllib.request.urlopen(backtest.BASE+path,timeout=30) as resp:
                return path,resp.read().decode('utf-8-sig')
        except Exception:
            return path,''
    cache={}
    with ThreadPoolExecutor(max_workers=24) as ex:
        for path,txt in ex.map(one,paths): cache[path]=txt
    def cached(path):
        if path in cache:return cache[path]
        return original(path)
    backtest.fetch=cached
    return {'days':len(days),'nonempty':sum(bool(v) for v in cache.values())}

def payouts_for(rows):
    cache={};out={}
    for r in rows:
        code=str(r['race_code']).zfill(12)
        if code[:8]>='20260901': raise RuntimeError(f'September entered {code}')
        _,p=pay._payout(code,str(r['actual_combo']),cache);out[code]=int(p)
    return out

def build_frame(rows,payouts):
    rec=[]
    for r in rows:
        code=str(r['race_code']).zfill(12);actual=str(r['actual_combo'])
        p2,pc=v365.formal_post_five6(r)
        pair=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
        top=v299.STRATEGIES['HYBRID'](p2,pc,pair)[:3]
        if len(top)!=3 or len(set(top))!=3: raise RuntimeError(f'invalid formal top3 {code}')
        formal=[f'1-{s}-{t}' for s,t in top]
        s=top[0][0]
        thirds=sorted([t for t in BOATS if t!=s],key=lambda t:(-float(pc[(s,t)]),t))
        if top[0]!=(s,thirds[0]) or top[1]!=(s,thirds[1]):
            raise RuntimeError(f'HYBRID conditional THIRD semantics drift {code}: top={top} thirds={thirds}')
        extra=(s,thirds[2])
        if extra in top: raise RuntimeError(f'extra duplicate {code}: {extra} in {top}')
        extra_ticket=f'1-{extra[0]}-{extra[1]}'
        gap=float(pc[(s,thirds[1])])-float(pc[(s,thirds[2])])
        rec.append({
          'race_code':code,'month':str(r['month']),'actual_combo':actual,
          'formal_tickets':';'.join(formal),'formal_hit':int(actual in formal),
          'extra_ticket':extra_ticket,'extra_hit':int(actual==extra_ticket),
          'gap23':gap,'extra_pair_prob':float(pair[extra]),'pc_extra':float(pc[extra]),
          'p2_dom':float(p2[s]),'second_boat':int(s),'extra_third':int(extra[1]),
          'payout100':int(payouts[code]),
        })
    return pd.DataFrame(rec)

def metrics(df,mask):
    mask=np.asarray(mask,dtype=bool)
    hit=df.formal_hit.astype(bool).to_numpy() | (mask & df.extra_hit.astype(bool).to_numpy())
    expanded=int(mask.sum())
    stake=int(len(df)*300 + expanded*100)
    ret=int(df.loc[hit,'payout100'].sum())
    return {
      'R':len(df),'expanded_R':expanded,'tickets_total':len(df)*3+expanded,
      'hits':int(hit.sum()),'hit_rate':float(hit.mean()),'gain_hits':int(hit.sum()-df.formal_hit.sum()),
      'stake_yen':stake,'return_yen':ret,'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0,
    }

def active(df,c):
    return (
      df.gap23.le(c['gap_max']+1e-12)&
      df.extra_pair_prob.ge(c['pair_min']-1e-12)&
      df.pc_extra.ge(c['pc_min']-1e-12)&
      df.p2_dom.ge(c['p2_min']-1e-12)
    ).to_numpy()

def cfg(g,p,pc,p2):
    return {'gap_max':float(g),'pair_min':float(p),'pc_min':float(pc),'p2_min':float(p2)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);args=ap.parse_args()
    x=pickle.load(args.prepared.open('rb'));rows=x['rows']['LIVE165']
    if len(rows)!=165: raise RuntimeError(f'LIVE165 drift {len(rows)}')
    prefetch=install_payout_cache(rows);payouts=payouts_for(rows)
    z=build_frame(rows,payouts)
    base=metrics(z,np.zeros(len(z),dtype=bool))
    if (base['R'],base['hits'],base['return_yen'])!=(165,87,63700):
        raise RuntimeError(f'formal baseline drift {base}')
    dev=z[z.month.isin(DEV)].copy();sup=z[z.month.isin(SUP)].copy()
    bdev=metrics(dev,np.zeros(len(dev),dtype=bool));bsup=metrics(sup,np.zeros(len(sup),dtype=bool))

    grid=[];configs=[]
    for g in GAP:
      for p in PAIR_MIN:
       for pcv in PC_MIN:
        for p2 in P2_MIN:
         c=cfg(g,p,pcv,p2);configs.append(c)
         m=metrics(dev,active(dev,c))
         grid.append({**c,**{f'dev_{k}':v for k,v in m.items()},
                      'dev_delta_hits':m['hits']-bdev['hits'],'dev_delta_roi_pp':100*(m['roi']-bdev['roi'])})
    gr=pd.DataFrame(grid)
    # DEV-only selection: exact3 first, require ROI>=115%; prefer higher ROI then fewer expansions.
    elig=gr[gr.dev_roi.ge(1.15)].copy()
    if len(elig)==0: raise RuntimeError('no DEV candidate above ROI floor')
    maxhits=int(elig.dev_hits.max())
    cand=elig[elig.dev_hits.eq(maxhits)].copy()
    best=cand.sort_values(['dev_roi','dev_expanded_R','gap_max','pair_min'],
                          ascending=[False,True,True,False]).iloc[0]
    keys=['gap_max','pair_min','pc_min','p2_min']
    chosen={k:float(best[k]) for k in keys}

    sm=metrics(sup,active(sup,chosen));am=metrics(z,active(z,chosen))
    # Frozen DEV top candidates evaluated on support for diagnostics, not selection.
    top=elig.sort_values(['dev_hits','dev_roi','dev_expanded_R'],ascending=[False,False,True]).head(50).copy()
    srows=[]
    for _,r in top.iterrows():
        c={k:float(r[k]) for k in keys}
        mm=metrics(sup,active(sup,c));aa=metrics(z,active(z,c))
        srows.append({**c,**{f'support_{k}':v for k,v in mm.items()},
                      **{f'all_{k}':v for k,v in aa.items()}})
    top=top.merge(pd.DataFrame(srows),on=keys)

    # Simple gap-only benchmark, plus always-fourth.
    bench=[]
    for g in GAP:
        c=cfg(g,0,0,0);m=metrics(z,active(z,c));bench.append({'name':f'GAP_{g:.3f}',**m})
    always=metrics(z,np.ones(len(z),dtype=bool));bench.append({'name':'ALWAYS4',**always})
    bench=pd.DataFrame(bench)

    # LOMO: select on 4 DEV months using same ROI floor, evaluate held month.
    lomo=[]
    for hold in DEV:
        train=z[z.month.isin([m for m in DEV if m!=hold])].copy()
        test=z[z.month.eq(hold)].copy()
        rec=[]
        for c in configs:
            m=metrics(train,active(train,c))
            if m['roi']>=1.15: rec.append((c,m))
        if not rec: raise RuntimeError(f'no LOMO candidate {hold}')
        mh=max(m['hits'] for _,m in rec)
        cc=[(c,m) for c,m in rec if m['hits']==mh]
        csel,msel=max(cc,key=lambda cm:(cm[1]['roi'],-cm[1]['expanded_R'],-cm[0]['gap_max']))
        hm=metrics(test,active(test,csel));hb=metrics(test,np.zeros(len(test),dtype=bool))
        lomo.append({'holdout_month':hold,**csel,
                     'formal_hits':hb['hits'],'cfg_hits':hm['hits'],'delta_hits':hm['hits']-hb['hits'],
                     'formal_roi':hb['roi'],'cfg_roi':hm['roi'],'delta_roi_pp':100*(hm['roi']-hb['roi']),
                     'expanded_R':hm['expanded_R']})

    # Rows for chosen configuration.
    mask=active(z,chosen)
    rz=z.copy();rz['expanded']=mask.astype(int)
    rz['final_hit']=(rz.formal_hit.astype(bool)|(mask&rz.extra_hit.astype(bool))).astype(int)
    rz['delta_hit']=rz.final_hit-rz.formal_hit
    rz.to_csv(OUT/'rows_chosen.csv',index=False)
    gr.to_csv(OUT/'dev_grid.csv',index=False);top.to_csv(OUT/'top50_support.csv',index=False)
    bench.to_csv(OUT/'benchmarks.csv',index=False);pd.DataFrame(lomo).to_csv(OUT/'lomo.csv',index=False)

    result={
      'formal_live165':base,'formal_dev':bdev,'formal_support':bsup,
      'grid_cells':len(gr),'dev_roi_floor':1.15,'max_dev_hits_under_floor':maxhits,
      'dev_selected':chosen,'selected_dev':{k:v for k,v in best.to_dict().items() if k.startswith('dev_')},
      'selected_support':sm,'selected_all165':am,
      'target_55pct_reached':bool(am['hit_rate']>=.55),
      'always_fourth':always,'gap_only_benchmarks':bench.to_dict('records'),
      'lomo':lomo,'payout_prefetch':prefetch,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
