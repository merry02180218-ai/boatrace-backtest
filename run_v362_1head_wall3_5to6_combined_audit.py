#!/usr/bin/env python3
from __future__ import annotations
"""v362: combine promoted wall3 LIVE tickets with expanded 5->6 ST rerank.

Research/audit only. Current production is not mutated here.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse, json, math, pickle, urllib.request
import pandas as pd

import backtest
import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v351_1head_third_close_margin_audit as pay

OUT=Path('/tmp/v362-wall3-5to6-combined');OUT.mkdir(parents=True,exist_ok=True)
BOATS=(2,3,4,5,6)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
CANDIDATES={
 'STRICT': {'attack_min':.60,'risk_min':.50,'mass_min':.375,'g2':0.0,'g3':.75},
 'BROAD50': {'attack_min':.60,'risk_min':.50,'mass_min':0.0,'g2':0.0,'g3':.75},
 'BROAD40': {'attack_min':.60,'risk_min':.40,'mass_min':0.0,'g2':0.0,'g3':.75},
}

def norm(q):
    s=sum(max(float(v),0.0) for v in q.values())
    if s<=0: raise RuntimeError('invalid probability mass')
    return {k:max(float(v),0.0)/s for k,v in q.items()}

def tickets(p2,pc):
    pr=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    top=v299.STRATEGIES['HYBRID'](p2,pc,pr)[:3]
    out=';'.join(f'1-{s}-{t}' for s,t in top)
    if len(out.split(';'))!=3 or len(set(out.split(';')))!=3: raise RuntimeError('invalid tickets')
    return out

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
        for path,txt in ex.map(one,paths):cache[path]=txt
    def cached(path):
        if path in cache:return cache[path]
        return original(path)
    backtest.fetch=cached
    return {'days':len(days),'nonempty':sum(bool(v) for v in cache.values())}

def payout_values(rows):
    cache={};vals={}
    for r in rows:
        code=str(r['race_code']).zfill(12)
        if code[:8]>='20260901':raise RuntimeError(f'September entered {code}')
        _,p=pay._payout(code,str(r['actual_combo']),cache);vals[code]=int(p)
    return vals

def wall3(p2,pc,r):
    watch=float(r['opp_mass'])>=prod.WATCH_OPPONENT_MASS_MIN
    if not watch or not bool(r.get('ex_ready',False)):
        return p2,pc,False,0.0
    wall=float(r['score3'])-float(r['score4'])
    risk=max(0.0,-wall) if float(r['score4'])>=prod.WALL3_SHADOW_ATTACK4_MIN else 0.0
    if risk<=0:return p2,pc,False,risk
    q2,q3=apply_pair(p2,pc,3,4,risk,prod.WALL3_SHADOW_SECOND_G2,prod.WALL3_SHADOW_THIRD_G3)
    return q2,q3,True,risk

def five6(p2,pc,r,cfg):
    if not bool(r.get('ex_ready',False)) or float(r['opp_mass'])<cfg['mass_min'] or float(r['score6'])<cfg['attack_min']:
        return p2,pc,False,0.0
    risk=float(r['st6'])-float(r['st5'])
    if risk<cfg['risk_min'] or risk<=0:return p2,pc,False,risk
    q2,q3=apply_pair(p2,pc,5,6,risk,cfg['g2'],cfg['g3'])
    return q2,q3,True,risk

def build_policy(rows,cfg=None):
    rec=[]
    for r in rows:
        p2={int(k):float(v) for k,v in r['_p2'].items()}
        pc={(int(s),int(t)):float(v) for (s,t),v in r['_pc'].items()}
        pre=tickets(p2,pc)
        p2,pc,wapp,wrisk=wall3(p2,pc,r)
        wall_t=tickets(p2,pc)
        fapp=False;frisk=0.0
        if cfg is not None:
            p2,pc,fapp,frisk=five6(p2,pc,r,cfg)
        final=tickets(p2,pc)
        actual=str(r['actual_combo'])
        rec.append({'race_code':str(r['race_code']).zfill(12),'month':str(r['month']),'actual_combo':actual,
                    'opp_mass':float(r['opp_mass']),'base_tickets':pre,'wall3_tickets':wall_t,'tickets':final,
                    'base_hit':int(actual in pre.split(';')),'wall3_hit':int(actual in wall_t.split(';')),
                    'hit':int(actual in final.split(';')),'wall3_applied':int(wapp),'wall3_risk':wrisk,
                    'five6_applied':int(fapp),'five6_risk':frisk})
    return pd.DataFrame(rec)

def met(z,payouts,hitcol='hit'):
    ret=sum(payouts[str(r.race_code).zfill(12)] for _,r in z.iterrows() if int(r[hitcol]))
    stake=len(z)*300
    return {'R':len(z),'hits':int(z[hitcol].sum()),'return_yen':ret,'stake_yen':stake,
            'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0}

def split_metrics(z,payouts,hitcol='hit'):
    return {'all':met(z,payouts,hitcol),'dev':met(z[z.month.isin(DEV)],payouts,hitcol),
            'support':met(z[z.month.isin(SUP)],payouts,hitcol)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);args=ap.parse_args()
    x=pickle.load(args.prepared.open('rb'));rows=x['rows']['LIVE165']
    if len(rows)!=165:raise RuntimeError(f'LIVE165 drift {len(rows)}')
    prefetch=install_payout_cache(rows);payouts=payout_values(rows)
    wall=build_policy(rows,None)
    wm=split_metrics(wall,payouts,'wall3_hit')
    expected=(165,83,58650)
    got=(wm['all']['R'],wm['all']['hits'],wm['all']['return_yen'])
    if got!=expected:raise RuntimeError(f'official wall3 baseline drift got={got} expected={expected}')

    summaries=[];monthly=[];details=[]
    for name,cfg in CANDIDATES.items():
        z=build_policy(rows,cfg);m=split_metrics(z,payouts,'hit')
        summary={'candidate':name,**cfg,
                 **{f'all_{k}':v for k,v in m['all'].items()},
                 **{f'dev_{k}':v for k,v in m['dev'].items()},
                 **{f'support_{k}':v for k,v in m['support'].items()},
                 'delta_hits_vs_wall3':m['all']['hits']-wm['all']['hits'],
                 'delta_roi_pp_vs_wall3':100*(m['all']['roi']-wm['all']['roi']),
                 'gain_vs_wall3':int(((z.hit-z.wall3_hit)==1).sum()),
                 'loss_vs_wall3':int(((z.hit-z.wall3_hit)==-1).sum()),
                 'five6_applied_R':int(z.five6_applied.sum()),
                 'final_changed_vs_wall3_R':int((z.tickets!=z.wall3_tickets).sum())}
        summaries.append(summary)
        for mon,g in z.groupby('month'):
            mm=met(g,payouts,'hit');bm=met(wall[wall.month.eq(mon)],payouts,'wall3_hit')
            monthly.append({'candidate':name,'month':mon,**mm,'wall3_hits':bm['hits'],'wall3_roi':bm['roi'],
                            'delta_hits':mm['hits']-bm['hits'],'delta_roi_pp':100*(mm['roi']-bm['roi'])})
        q=z[(z.tickets!=z.wall3_tickets)|((z.hit-z.wall3_hit)!=0)].copy()
        q['candidate']=name;q['delta_vs_wall3']=q.hit-q.wall3_hit;details.append(q)

    sm=pd.DataFrame(summaries);mo=pd.DataFrame(monthly);dt=pd.concat(details,ignore_index=True)
    sm.to_csv(OUT/'summary.csv',index=False);mo.to_csv(OUT/'monthly.csv',index=False);dt.to_csv(OUT/'changed_races.csv',index=False)
    result={'wall3_baseline':wm,'candidates':summaries,'payout_prefetch':prefetch,
            'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)
    print('\nSUMMARY',flush=True);print(sm.to_string(index=False),flush=True)
    print('\nMONTHLY',flush=True);print(mo.to_string(index=False),flush=True)

if __name__=='__main__':main()
