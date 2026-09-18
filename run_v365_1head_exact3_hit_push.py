#!/usr/bin/env python3
from __future__ import annotations
"""v365: push exact3 hit-rate with 3 tickets after formal wall3 + 5->6 ST.

Uses v360 prepared rows only. Selection is Feb-Jun DEV only.
Jul-Aug SUPPORT is evaluation only. September outcomes are forbidden.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse, json, math, pickle, urllib.request
import numpy as np
import pandas as pd

import backtest
import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v351_1head_third_close_margin_audit as pay

OUT=Path('/tmp/v365-exact3-hit-push');OUT.mkdir(parents=True,exist_ok=True)
BOATS=(2,3,4,5,6)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')

FAMILIES=('2>3','4>5','2>3+4>5')
BASES=('SCORE','ST','COMBO')
OUTER_SCORE_MIN=(.40,.50,.60,.70)
RISK_MIN=(0.,.10,.20,.30,.40)
MASS_MIN=(.375,.400,.425)
G2=(0.,.25,.50,1.0)
G3=(.25,.50,.75,1.0,1.5)

def norm(q):
    s=sum(max(float(v),0.0) for v in q.values())
    if not math.isfinite(s) or s<=0: raise RuntimeError('invalid probability mass')
    return {k:max(float(v),0.0)/s for k,v in q.items()}

def tickets(p2,pc):
    pr=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    top=v299.STRATEGIES['HYBRID'](p2,pc,pr)[:3]
    if len(top)!=3 or len(set(top))!=3: raise RuntimeError('invalid tickets')
    return ';'.join(f'1-{s}-{t}' for s,t in top)

def apply_pair(p2,pc,inner,outer,risk,g2,g3):
    q2={b:float(p2[b]) for b in BOATS}
    if g2>0:
        q2[outer]*=math.exp(g2*risk);q2[inner]*=math.exp(-g2*risk);q2=norm(q2)
    q3={}
    for s in BOATS:
        q={t:float(pc[(s,t)]) for t in BOATS if t!=s}
        if g3>0:
            if outer in q:q[outer]*=math.exp(g3*risk)
            if inner in q:q[inner]*=math.exp(-g3*risk)
        q=norm(q)
        for t,v in q.items():q3[(s,t)]=v
    return q2,q3

def formal_post_five6(r):
    p2={int(k):float(v) for k,v in r['_p2'].items()}
    pc={(int(s),int(t)):float(v) for (s,t),v in r['_pc'].items()}
    # formal wall3
    if float(r['opp_mass'])>=prod.WATCH_OPPONENT_MASS_MIN and bool(r.get('ex_ready',False)):
        wrisk=max(0.0,float(r['score4'])-float(r['score3'])) if float(r['score4'])>=prod.WALL3_SHADOW_ATTACK4_MIN else 0.0
        if wrisk>0:
            p2,pc=apply_pair(p2,pc,3,4,wrisk,prod.WALL3_SHADOW_SECOND_G2,prod.WALL3_SHADOW_THIRD_G3)
    # formal five6
    if bool(r.get('ex_ready',False)) and float(r['score6'])>=prod.FIVE6_SHADOW_SCORE6_MIN:
        gap=float(r['st6'])-float(r['st5'])
        if gap>=prod.FIVE6_SHADOW_ST_GAP_MIN:
            p2,pc=apply_pair(p2,pc,5,6,gap,prod.FIVE6_SHADOW_SECOND_G2,prod.FIVE6_SHADOW_THIRD_G3)
    return p2,pc

def risk_for(r,inner,outer,basis):
    sg=float(r[f'score{outer}'])-float(r[f'score{inner}'])
    st=float(r[f'st{outer}'])-float(r[f'st{inner}'])
    if basis=='SCORE': return sg
    if basis=='ST': return st
    return .65*st+.35*sg

def family_pairs(family):
    if family=='2>3': return ((2,3),)
    if family=='4>5': return ((4,5),)
    return ((2,3),(4,5))

def apply_extra(r,p2,pc,cfg):
    if not bool(r.get('ex_ready',False)) or float(r['opp_mass'])<cfg['mass_min']:
        return p2,pc,[],{}
    triggers=[];risks={}
    for inner,outer in family_pairs(cfg['family']):
        if float(r[f'score{outer}'])<cfg['outer_score_min']: continue
        rv=risk_for(r,inner,outer,cfg['basis'])
        risks[f'{inner}>{outer}']=rv
        if rv>=cfg['risk_min'] and rv>0:
            p2,pc=apply_pair(p2,pc,inner,outer,rv,cfg['g2'],cfg['g3'])
            triggers.append(f'{inner}>{outer}')
    return p2,pc,triggers,risks

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
    cache={};vals={}
    for r in rows:
        code=str(r['race_code']).zfill(12)
        if code[:8]>='20260901': raise RuntimeError(f'September entered {code}')
        _,p=pay._payout(code,str(r['actual_combo']),cache);vals[code]=int(p)
    return vals

def formal_rows(rows):
    out=[]
    for r in rows:
        p2,pc=formal_post_five6(r);ts=tickets(p2,pc);actual=str(r['actual_combo'])
        out.append({'race_code':str(r['race_code']).zfill(12),'month':str(r['month']),
                    'actual_combo':actual,'tickets':ts,'hit':int(actual in ts.split(';'))})
    return pd.DataFrame(out)

def metric_df(z,payouts,hit='hit'):
    ret=sum(payouts[str(r.race_code).zfill(12)] for _,r in z.iterrows() if int(r[hit]))
    stake=len(z)*300
    return {'R':len(z),'hits':int(z[hit].sum()),'stake':stake,'return':ret,
            'profit':ret-stake,'roi':ret/stake if stake else 0.0}

def evaluate(rows,cfg,payouts,need_detail=False):
    rec=[];details=[];trig23=trig45=0
    for r in rows:
        code=str(r['race_code']).zfill(12);actual=str(r['actual_combo'])
        p2,pc=formal_post_five6(r);base=tickets(p2,pc);bh=int(actual in base.split(';'))
        p2,pc,triggers,risks=apply_extra(r,p2,pc,cfg)
        ts=tickets(p2,pc);h=int(actual in ts.split(';'));d=h-bh
        trig23+=int('2>3' in triggers);trig45+=int('4>5' in triggers)
        rec.append({'race_code':code,'month':str(r['month']),'actual_combo':actual,
                    'tickets':ts,'hit':h,'formal_tickets':base,'formal_hit':bh,
                    'changed':int(ts!=base),'delta':d,'opp_mass':float(r['opp_mass'])})
        if need_detail and (ts!=base or d):
            details.append({'race_code':code,'month':str(r['month']),'actual_combo':actual,
                            'opp_mass':float(r['opp_mass']),'formal_tickets':base,'tickets':ts,
                            'formal_hit':bh,'hit':h,'delta':d,'triggers':';'.join(triggers),
                            'risk_2>3':risks.get('2>3'),'risk_4>5':risks.get('4>5')})
    z=pd.DataFrame(rec);m=metric_df(z,payouts)
    m.update({'changed_R':int(z.changed.sum()),'gain_R':int((z.delta==1).sum()),
              'loss_R':int((z.delta==-1).sum()),'trigger23_R':trig23,'trigger45_R':trig45})
    return z,m,details

def cfgdict(family,basis,omin,rmin,mass,g2,g3):
    return {'family':family,'basis':basis,'outer_score_min':float(omin),'risk_min':float(rmin),
            'mass_min':float(mass),'g2':float(g2),'g3':float(g3)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);args=ap.parse_args()
    x=pickle.load(args.prepared.open('rb'));allrows=x['rows']
    rows165=allrows['LIVE165'];rows313=allrows['H0775_M350']
    union_by={}
    for name in ('LIVE165','H078_M375','H0775_M375','H0775_M350','PROD276'):
        for r in allrows[name]: union_by[str(r['race_code']).zfill(12)]=r
    union=list(union_by.values())
    prefetch=install_payout_cache(union);payouts=payouts_for(union)

    formal165=formal_rows(rows165);fm165=metric_df(formal165,payouts)
    if (fm165['R'],fm165['hits'],fm165['return'])!=(165,87,63700):
        raise RuntimeError(f'formal baseline drift {fm165}')
    dev165=[r for r in rows165 if str(r['month']) in DEV]
    sup165=[r for r in rows165 if str(r['month']) in SUP]
    formal_dev=formal_rows(dev165);formal_sup=formal_rows(sup165)
    fdev=metric_df(formal_dev,payouts);fsup=metric_df(formal_sup,payouts)

    grid=[]
    for fam in FAMILIES:
      for basis in BASES:
       for omin in OUTER_SCORE_MIN:
        for rmin in RISK_MIN:
         for mass in MASS_MIN:
          for g2 in G2:
           for g3 in G3:
            cfg=cfgdict(fam,basis,omin,rmin,mass,g2,g3)
            _,m,_=evaluate(dev165,cfg,payouts)
            grid.append({**cfg,**{f'dev_{k}':v for k,v in m.items()},
                         'dev_delta_hits':m['hits']-fdev['hits'],'dev_delta_roi_pp':100*(m['roi']-fdev['roi'])})
    g=pd.DataFrame(grid)

    # DEV-only shortlist: maximize exact3, require no more than one lost baseline hit.
    max_hits=int(g.dev_hits.max())
    short=g[g.dev_hits.eq(max_hits)].copy()
    # ROI floor is applied on DEV as a guard, but exact3 remains primary objective.
    roi_floor=1.20
    guarded=short[short.dev_roi.ge(roi_floor)].copy()
    if len(guarded): short=guarded
    # prefer fewer losses, then higher ROI, fewer changes, simpler g2.
    best=short.sort_values(['dev_loss_R','dev_roi','dev_changed_R','g2','risk_min'],
                           ascending=[True,False,True,True,False]).iloc[0]
    keys=['family','basis','outer_score_min','risk_min','mass_min','g2','g3']
    chosen={k:(str(best[k]) if k in ('family','basis') else float(best[k])) for k in keys}

    # Evaluate chosen on SUPPORT, ALL165, 313 and other universes.
    supz,supm,_=evaluate(sup165,chosen,payouts)
    allz,allm,detail165=evaluate(rows165,chosen,payouts,True)
    rows313z,m313,detail313=evaluate(rows313,chosen,payouts,True)

    universes=[]
    for name,rr in allrows.items():
        if name not in ('LIVE165','H078_M375','H0775_M375','H0775_M350','PROD276'):continue
        bz=formal_rows(rr);bm=metric_df(bz,payouts)
        _,cm,_=evaluate(rr,chosen,payouts)
        universes.append({'universe':name,'formal_hits':bm['hits'],'formal_roi':bm['roi'],
                          'cfg_hits':cm['hits'],'cfg_roi':cm['roi'],'delta_hits':cm['hits']-bm['hits'],
                          'delta_roi_pp':100*(cm['roi']-bm['roi']),'gain_R':cm['gain_R'],'loss_R':cm['loss_R']})

    # Monthly on chosen LIVE165.
    monthly=[]
    for mon in sorted(set(allz.month)):
        cz=allz[allz.month.eq(mon)];bz=formal165[formal165.month.eq(mon)]
        cm=metric_df(cz,payouts);bm=metric_df(bz,payouts)
        monthly.append({'month':mon,'formal_hits':bm['hits'],'formal_roi':bm['roi'],
                        'cfg_hits':cm['hits'],'cfg_roi':cm['roi'],'delta_hits':cm['hits']-bm['hits'],
                        'delta_roi_pp':100*(cm['roi']-bm['roi'])})

    # Near-best DEV plateau: within one hit of max, ROI >=120%, loss<=1.
    plateau=g[(g.dev_hits.ge(max_hits-1))&(g.dev_roi.ge(roi_floor))&(g.dev_loss_R.le(1))].copy()

    # LOMO: reselect from full grid using other 4 DEV months and evaluate holdout.
    lomo=[]
    for hold in DEV:
        train=[r for r in dev165 if str(r['month'])!=hold]
        test=[r for r in dev165 if str(r['month'])==hold]
        ftrain=metric_df(formal_rows(train),payouts)
        rec=[]
        for _,row in g.iterrows():
            cfg={k:(str(row[k]) if k in ('family','basis') else float(row[k])) for k in keys}
            _,m,_=evaluate(train,cfg,payouts)
            rec.append((cfg,m))
        mx=max(m['hits'] for _,m in rec)
        cand=[(c,m) for c,m in rec if m['hits']==mx and m['roi']>=1.20]
        if not cand:cand=[(c,m) for c,m in rec if m['hits']==mx]
        csel,msel=min(cand,key=lambda cm:(cm[1]['loss_R'],-cm[1]['roi'],cm[1]['changed_R'],cm[0]['g2']))
        tz,tm,_=evaluate(test,csel,payouts);fb=metric_df(formal_rows(test),payouts)
        lomo.append({'holdout_month':hold,**csel,'formal_hits':fb['hits'],'cfg_hits':tm['hits'],
                     'delta_hits':tm['hits']-fb['hits'],'formal_roi':fb['roi'],'cfg_roi':tm['roi'],
                     'delta_roi_pp':100*(tm['roi']-fb['roi']),'gain_R':tm['gain_R'],'loss_R':tm['loss_R']})

    # Optional 4th-ticket benchmark for comparison only, not a production candidate here.
    # Take highest remaining pair probability after the formal 3 tickets.
    fourth=[]
    for r in rows165:
        p2,pc=formal_post_five6(r);formal=tickets(p2,pc).split(';')
        pair=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
        ordered=[f'1-{s}-{t}' for (s,t),_ in sorted(pair.items(),key=lambda kv:(-kv[1],kv[0]))]
        extra=next(t for t in ordered if t not in formal)
        actual=str(r['actual_combo']);base_hit=int(actual in formal);hit4=int(actual in formal or actual==extra)
        fourth.append({'race_code':str(r['race_code']).zfill(12),'month':str(r['month']),
                       'base_hit':base_hit,'hit4':hit4,'extra_hit':int(actual==extra),'extra_ticket':extra})
    f4=pd.DataFrame(fourth)
    ret4=sum(payouts[str(r.race_code).zfill(12)] for _,r in f4.iterrows() if int(r.hit4))
    stake4=len(f4)*400
    fourth_summary={'R':len(f4),'hits':int(f4.hit4.sum()),'gain_hits':int(f4.hit4.sum()-f4.base_hit.sum()),
                    'stake':stake4,'return':ret4,'roi':ret4/stake4 if stake4 else 0.0}

    g.to_csv(OUT/'dev_grid.csv',index=False);plateau.to_csv(OUT/'dev_plateau.csv',index=False)
    pd.DataFrame(universes).to_csv(OUT/'universes.csv',index=False)
    pd.DataFrame(monthly).to_csv(OUT/'monthly_live165.csv',index=False)
    pd.DataFrame(lomo).to_csv(OUT/'lomo.csv',index=False)
    pd.DataFrame(detail165).to_csv(OUT/'chosen_changed_live165.csv',index=False)
    pd.DataFrame(detail313).to_csv(OUT/'chosen_changed_313.csv',index=False)
    f4.to_csv(OUT/'fourth_ticket_rows.csv',index=False)

    result={
      'formal_live165':fm165,'formal_dev':fdev,'formal_support':fsup,
      'grid_cells':len(g),'max_dev_hits':max_hits,'dev_plateau_size':len(plateau),
      'dev_selected':chosen,
      'selected_dev':{k:v for k,v in best.to_dict().items() if k.startswith('dev_')},
      'selected_support':supm,'selected_all165':allm,'selected_313':m313,
      'selected_live165_hit_rate':allm['hits']/allm['R'],
      'target_55pct_reached':bool(allm['hits']/allm['R']>=.55),
      'universes':universes,'lomo':lomo,'fourth_ticket_benchmark':fourth_summary,
      'payout_prefetch':prefetch,'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
