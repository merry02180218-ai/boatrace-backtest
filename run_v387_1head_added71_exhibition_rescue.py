#!/usr/bin/env python3
from __future__ import annotations
"""v387: 4HEAD-style rescue research for the 1HEAD H078_M375 added71 band.

LIVE165 stays frozen. Only races in H078_M375 but not LIVE165 are eligible for
rescue. Rescue scores use pre-race p_head/mass plus already-causal exhibition
features from the frozen v360 prepared artifact. Outcomes/payouts are used only
for historical evaluation, never as score inputs. September is forbidden.
"""
from pathlib import Path
import argparse,json,math,pickle
import numpy as np
import pandas as pd

import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365

OUT=Path('/tmp/v387-added71-exhibition-rescue'); OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
QS=(.25,.35,.45,.55,.65,.75)
FAMILIES={
  'HEAD_ONLY': {'p_head':1.0},
  'EX_ONLY': {'v332_score':1.0},
  'HEAD_EX': {'p_head':1.0,'v332_score':1.0},
  'HEAD_EX_ATTACK': {'p_head':1.0,'v332_score':1.0,'attack_core':0.5},
  'HEAD_EX_MASS': {'p_head':1.0,'v332_score':1.0,'opp_mass':0.5},
}

def ticket_string(r):
    p2,pc=v365.formal_post_five6(r)
    pr=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    top=v299.STRATEGIES['HYBRID'](p2,pc,pr)[:3]
    out=';'.join(f'1-{s}-{t}' for s,t in top)
    if len(out.split(';'))!=3 or len(set(out.split(';')))!=3:
        raise RuntimeError('invalid formal ticket set')
    return out

def build(rows,payouts):
    rec=[]
    for r in rows:
        code=str(r['race_code']).zfill(12)
        if code[:8]>='20260901': raise RuntimeError(f'September entered {code}')
        ts=ticket_string(r); actual=str(r['actual_combo']); hit=int(actual in ts.split(';'))
        rec.append({
          'race_code':code,'month':str(r['month']),'head_hit':int(r['head_hit']),
          'actual_combo':actual,'tickets':ts,'hit':hit,'payout100':int(payouts[code]),
          'p_head':float(r['p_head']),'opp_mass':float(r['opp_mass']),
          'v332_score':float(r['v332_score']),'attack_core':float(r['attack_core']),
        })
    return pd.DataFrame(rec)

def metric(z):
    if len(z)==0:
        return {'R':0,'head':0,'head_rate':0.0,'hits':0,'exact3_rate':0.0,'stake':0,'return':0,'profit':0,'roi':0.0}
    ret=int(z.loc[z.hit.eq(1),'payout100'].sum()); stake=len(z)*300
    return {'R':int(len(z)),'head':int(z.head_hit.sum()),'head_rate':float(z.head_hit.mean()),
            'hits':int(z.hit.sum()),'exact3_rate':float(z.hit.mean()),'stake':int(stake),
            'return':ret,'profit':int(ret-stake),'roi':float(ret/stake)}

def combine(a,b):
    return pd.concat([a,b],ignore_index=True)

def fit_transform(train, test, weights):
    cols=list(weights)
    mu={c:float(train[c].mean()) for c in cols}
    sd={c:float(train[c].std(ddof=0)) for c in cols}
    for c in cols:
        if not math.isfinite(sd[c]) or sd[c]<1e-9: sd[c]=1.0
    def score(df):
        s=np.zeros(len(df),dtype=float)
        denom=sum(abs(float(w)) for w in weights.values())
        for c,w in weights.items():
            s += float(w)*((df[c].astype(float).to_numpy()-mu[c])/sd[c])
        return s/denom
    return score(train),score(test),{'mean':mu,'sd':sd}

def grid_eval(add,live):
    dev=add[add.month.isin(DEV)].copy(); sup=add[add.month.isin(SUP)].copy()
    live_dev=live[live.month.isin(DEV)].copy(); live_sup=live[live.month.isin(SUP)].copy()
    rows=[]; score_cache={}
    for fam,w in FAMILIES.items():
        trscore,allscore,pars=fit_transform(dev,add,w)
        score_cache[fam]=(trscore,allscore,pars)
        for q in QS:
            th=float(np.quantile(trscore,q))
            sel=add[allscore>=th-1e-12].copy()
            sdev=sel[sel.month.isin(DEV)]; ssup=sel[sel.month.isin(SUP)]
            madd=metric(sel); md=metric(sdev); ms=metric(ssup)
            cd=metric(combine(live_dev,sdev)); cs=metric(combine(live_sup,ssup)); ca=metric(combine(live,sel))
            rows.append({
              'family':fam,'q':q,'threshold':th,
              'selected_R':madd['R'],'selected_head_rate':madd['head_rate'],'selected_roi':madd['roi'],
              'dev_R':md['R'],'dev_head_rate':md['head_rate'],'dev_hits':md['hits'],'dev_roi':md['roi'],'dev_profit':md['profit'],
              'support_R':ms['R'],'support_head_rate':ms['head_rate'],'support_hits':ms['hits'],'support_roi':ms['roi'],'support_profit':ms['profit'],
              'combined_R':ca['R'],'combined_roi':ca['roi'],'combined_profit':ca['profit'],
              'combined_dev_R':cd['R'],'combined_dev_roi':cd['roi'],'combined_dev_profit':cd['profit'],
              'combined_support_R':cs['R'],'combined_support_roi':cs['roi'],'combined_support_profit':cs['profit'],
            })
    return pd.DataFrame(rows),score_cache

def choose_dev_only(grid,add_dev_base,live_dev_base):
    # Volume-first, but refuse obvious DEV deterioration. Support fields never participate.
    strict=grid[
      grid.dev_R.between(15,35) &
      grid.dev_roi.ge(1.0) &
      grid.dev_head_rate.ge(float(add_dev_base['head_rate'])-1e-12) &
      grid.combined_dev_roi.ge(float(live_dev_base['roi'])-0.03)
    ].copy()
    if len(strict):
        z=strict.sort_values(['dev_R','combined_dev_roi','dev_roi'],ascending=[False,False,False])
        return 'STRICT_VOLUME_FIRST',z.iloc[0]
    fallback=grid[grid.dev_R.ge(15)].copy()
    if len(fallback)==0: return 'NO_CANDIDATE',None
    z=fallback.sort_values(['combined_dev_roi','dev_roi','dev_R'],ascending=[False,False,False])
    return 'FALLBACK_DIAGNOSTIC',z.iloc[0]

def lomo(add,family,q):
    out=[]
    w=FAMILIES[family]
    for hold in DEV:
        tr=add[add.month.isin([m for m in DEV if m!=hold])].copy()
        te=add[add.month.eq(hold)].copy()
        if len(tr)==0 or len(te)==0:
            out.append({'holdout':hold,'R':len(te),'selected_R':0,'roi':0.0,'head_rate':0.0}); continue
        trscore,tescore,_=fit_transform(tr,te,w)
        th=float(np.quantile(trscore,q))
        sel=te[tescore>=th-1e-12].copy(); m=metric(sel)
        out.append({'holdout':hold,'threshold':th,'R':len(te),'selected_R':m['R'],
                    'head_rate':m['head_rate'],'hits':m['hits'],'roi':m['roi'],'profit':m['profit']})
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--prepared',required=True,type=Path); args=ap.parse_args()
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD: raise RuntimeError('September guard disabled')
    x=pickle.load(args.prepared.open('rb')); rows=x['rows']
    for name,n in [('LIVE165',165),('H078_M375',236)]:
        if name not in rows or len(rows[name])!=n: raise RuntimeError(f'{name} drift')
    live_ids={str(r['race_code']).zfill(12) for r in rows['LIVE165']}
    broad={str(r['race_code']).zfill(12):r for r in rows['H078_M375']}
    added_rows=[r for c,r in broad.items() if c not in live_ids]
    if len(added_rows)!=71: raise RuntimeError(f'added band drift {len(added_rows)} != 71')
    union=list({str(r['race_code']).zfill(12):r for r in list(rows['LIVE165'])+added_rows}.values())
    v365.install_payout_cache(union); payouts=v365.payouts_for(union)
    live=build(rows['LIVE165'],payouts); add=build(added_rows,payouts)
    if len(live)!=165 or len(add)!=71: raise RuntimeError('build count drift')
    needed=['p_head','opp_mass','v332_score','attack_core']
    if add[needed].isna().any().any(): raise RuntimeError('missing rescue feature')
    if not (add.p_head>=.78-1e-12).all():
        raise RuntimeError(f'added p_head floor drift {add.p_head.min()} {add.p_head.max()}')
    added_below079=int((add.p_head<.79-1e-12).sum())
    added_ge079=int((add.p_head>=.79-1e-12).sum())

    live_base=metric(live); add_base=metric(add)
    live_dev=metric(live[live.month.isin(DEV)]); live_sup=metric(live[live.month.isin(SUP)])
    add_dev=metric(add[add.month.isin(DEV)]); add_sup=metric(add[add.month.isin(SUP)])
    grid,score_cache=grid_eval(add,live)
    mode,pick=choose_dev_only(grid,add_dev,live_dev)
    picked=None; lomo_rows=[]
    if pick is not None:
        fam=str(pick.family); q=float(pick.q); trscore,allscore,pars=score_cache[fam]
        th=float(pick.threshold); sel=add[allscore>=th-1e-12].copy()
        picked={'selection_mode':mode,'family':fam,'q':q,'threshold':th,
                'standardization':pars,'metrics':pick.to_dict(),
                'selected_codes':sel.race_code.tolist()}
        lomo_rows=lomo(add,fam,q)
        sel.to_csv(OUT/'selected_added.csv',index=False)

    grid.to_csv(OUT/'grid.csv',index=False)
    add.to_csv(OUT/'added71_rows.csv',index=False)
    live.to_csv(OUT/'live165_rows.csv',index=False)
    pd.DataFrame(lomo_rows).to_csv(OUT/'lomo.csv',index=False)

    # Useful volume frontier, still DEV-derived only in its ordering/filter.
    frontier=grid[grid.dev_R.ge(10)].sort_values(['dev_R','combined_dev_roi'],ascending=[False,False]).copy()
    frontier.to_csv(OUT/'volume_frontier.csv',index=False)
    result={
      'prepared_source':'v360 Artifact 10539401122',
      'band':'H078_M375 minus LIVE165',
      'band_R':len(add),
      'p_head_range':[float(add.p_head.min()),float(add.p_head.max())],
      'added_below_079_R':added_below079,'added_ge_079_R':added_ge079,
      'band_note':'set difference of H078_M375 and LIVE165; not a pure p_head interval because exhibition gate is refit on each PRE universe',
      'live165_baseline':live_base,'added71_baseline':add_base,
      'live165_dev':live_dev,'live165_support':live_sup,
      'added71_dev':add_dev,'added71_support':add_sup,
      'families':FAMILIES,'quantiles':QS,'grid_cells':len(grid),
      'dev_only_pick':picked,'dev_lomo':lomo_rows,
      'SELECTION_USED_SUPPORT_OUTCOMES':False,
      'RESULT_OR_PAYOUT_USED_AS_SCORE_INPUT':False,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True,
    }
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str),flush=True)
    print('\nTOP DEV VOLUME/QUALITY',flush=True)
    cols=['family','q','selected_R','dev_R','dev_head_rate','dev_roi','combined_dev_R','combined_dev_roi','support_R','support_head_rate','support_roi','combined_R','combined_roi']
    print(grid.sort_values(['dev_R','combined_dev_roi'],ascending=[False,False])[cols].head(30).to_string(index=False),flush=True)

if __name__=='__main__': main()
